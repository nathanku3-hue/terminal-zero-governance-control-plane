from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from uuid import UUID

QUEUE_SCHEMA_VERSION = "1.0.0"
ALERT_SCHEMA_VERSION = "1.0.0"
STATE_SCHEMA_VERSION = "1.0.0"
REGISTRY_SCHEMA_VERSION = "1.0.0"
VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

DEFAULT_WARN_MINUTES = 15
DEFAULT_BLOCK_MINUTES = 30
DEFAULT_INTERVAL_SECONDS = 10
DEFAULT_MIN_IMAGE_BYTES = 1024

MISSING_CAPTURE_TOKEN = "REAL_CAPTURE_MISSING"

# Terminal polling: lines in terminal .txt files that match this pattern are
# treated as evidence signals.  Two syntaxes are recognised:
#   EVIDENCE:<path>          explicit signal written to terminal by operator
#   Any bare/quoted path ending with a recognised image extension
TERMINAL_EVIDENCE_SIGNAL_RE = re.compile(
    r"(?:EVIDENCE:\s*(?P<signal>[^\s]+))"
    r"|(?:(?P<path>(?:[A-Za-z]:[/\\]|[/\\]|\.)[^\s'\"]*\.(?:png|jpg|jpeg|webp)))",
    re.IGNORECASE,
)


class ManualCaptureError(RuntimeError):
    pass


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        raw = value.replace("Z", "+00:00")
        return datetime.fromisoformat(raw).astimezone(timezone.utc)
    except Exception:
        return None


def _windows_desktop_path() -> Path | None:
    if os.name != "nt":
        return None
    # FOLDERID_Desktop = {B4BFCC3A-DB2C-424C-B029-7FE99A87C641}
    folder_id = UUID("{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}").bytes_le

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    guid = GUID.from_buffer_copy(folder_id)
    path_ptr = ctypes.c_wchar_p()
    shell32 = ctypes.windll.shell32
    ole32 = ctypes.windll.ole32
    result = shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(path_ptr))
    if result != 0 or not path_ptr.value:
        return None
    try:
        return Path(path_ptr.value)
    finally:
        ole32.CoTaskMemFree(path_ptr)


def _detect_default_drop_dir() -> Path:
    explicit = os.environ.get("MANUAL_CAPTURE_DROP_DIR", "").strip()
    if explicit:
        return Path(explicit).expanduser()

    desktop_known = _windows_desktop_path()
    userprofile = Path(os.environ.get("USERPROFILE", "~")).expanduser()
    candidates = [
        desktop_known / "Evidence_Drop" if desktop_known is not None else None,
        userprofile / "Desktop" / "Evidence_Drop",
        userprofile / "OneDrive" / "Desktop" / "Evidence_Drop",
        userprofile / "OneDrive" / "桌面" / "Evidence_Drop",
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        parent = candidate.parent
        if parent.exists():
            return candidate
    return candidates[0]


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def _quarantine_corrupt_json(path: Path) -> Path:
    timestamp = _iso_utc(_now_utc()).replace(":", "").replace("-", "")
    candidate = path.with_name(f"{path.stem}.corrupt.{timestamp}{path.suffix}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(
            f"{path.stem}.corrupt.{timestamp}.{counter}{path.suffix}"
        )
        counter += 1
    os.replace(path, candidate)
    return candidate


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManualCaptureError(f"Failed to read JSON state file {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except Exception as exc:
        quarantined = _quarantine_corrupt_json(path)
        raise ManualCaptureError(
            f"Malformed JSON in {path}; quarantined to {quarantined}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        quarantined = _quarantine_corrupt_json(path)
        raise ManualCaptureError(
            f"JSON root must be an object in {path}; quarantined to {quarantined}"
        )
    return data


def _sha256_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _validate_image_file(path: Path, min_bytes: int) -> tuple[bool, str]:
    if not path.exists() or not path.is_file():
        return False, "missing_file"
    ext = path.suffix.lower()
    if ext not in VALID_IMAGE_EXTENSIONS:
        return False, f"unsupported_extension:{ext}"
    size = path.stat().st_size
    if size < min_bytes:
        return False, f"file_too_small:{size}"

    with open(path, "rb") as handle:
        head = handle.read(16)

    if ext == ".png" and not head.startswith(b"\x89PNG\r\n\x1a\n"):
        return False, "invalid_png_header"
    if ext in {".jpg", ".jpeg"} and not head.startswith(b"\xff\xd8\xff"):
        return False, "invalid_jpeg_header"
    if ext == ".webp" and not (head.startswith(b"RIFF") and head[8:12] == b"WEBP"):
        return False, "invalid_webp_header"
    return True, "ok"


def _split_markdown_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = [cell.strip() for cell in stripped[1:-1].split("|")]
    if len(cells) < 5:
        return None
    return cells


def _extract_img_target(evidence_cell: str) -> str | None:
    match = re.search(r"\[Img\]\(([^)]+)\)", evidence_cell, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _extract_criteria(evidence_cell: str) -> str:
    marker = "Criteria:"
    if marker not in evidence_cell:
        return ""
    tail = evidence_cell.split(marker, 1)[1]
    cleaned = tail.replace("*", "").replace("<br>", " ").strip()
    return cleaned.rstrip(". ").strip()


def _format_evidence_cell(*, evidence_target: str, criteria: str) -> str:
    base = f"[Img]({evidence_target})"
    if not criteria:
        return base
    safe_criteria = criteria.rstrip(". ").strip()
    return f"{base} <br> *Criteria: {safe_criteria}.*"


def load_index_rows(index_path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    if not index_path.exists():
        raise ManualCaptureError(f"Missing index markdown: {index_path}")
    lines = index_path.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        cells = _split_markdown_row(line)
        if cells is None:
            continue
        row_id = cells[0]
        if not row_id.lower().startswith("manual"):
            continue
        rows.append(
            {
                "line_index": idx,
                "id": row_id,
                "name": cells[1],
                "result": cells[2],
                "date": cells[3],
                "evidence_cell": cells[4],
                "img_target": _extract_img_target(cells[4]),
                "criteria": _extract_criteria(cells[4]),
            }
        )
    return lines, rows


def infer_task_id(lines: list[str]) -> str:
    gate_regex = re.compile(r"\((T\d+)_gate\d+_\d{8}\.log\)", flags=re.IGNORECASE)
    manual_regex = re.compile(r"\((T\d+)_manual\d+_[^)]+\)", flags=re.IGNORECASE)
    for line in lines:
        match = gate_regex.search(line)
        if match:
            return match.group(1).upper()
    for line in lines:
        match = manual_regex.search(line)
        if match:
            return match.group(1).upper()
    return "T00"


def _default_file_pattern(task_id: str, row_id: str) -> str:
    escaped_task = re.escape(task_id)
    escaped_id = re.escape(row_id)
    return rf"^{escaped_task}_{escaped_id}_[A-Za-z0-9._-]+_\d{{8}}\.(png|jpg|jpeg|webp)$"


def _build_item_from_row(row: dict[str, Any], task_id: str, now_iso: str) -> dict[str, Any]:
    target = row.get("img_target") or MISSING_CAPTURE_TOKEN
    result_upper = str(row.get("result", "")).upper()
    status = "PENDING"
    evidence_file = None
    if target != MISSING_CAPTURE_TOKEN:
        status = "RECEIVED"
        evidence_file = Path(target).name
    elif "BLOCK" in result_upper:
        status = "BLOCKED"

    return {
        "id": row["id"],
        "name": row["name"],
        "task_id": task_id,
        "criteria": row.get("criteria", ""),
        "file_pattern": _default_file_pattern(task_id, row["id"]),
        "status": status,
        "created_at_utc": now_iso,
        "warned_at_utc": None,
        "blocked_at_utc": None,
        "received_at_utc": now_iso if status == "RECEIVED" else None,
        "evidence_file": evidence_file,
        "evidence_sha256": None,
    }


def ensure_queue_payload(
    *,
    queue_path: Path,
    rows: list[dict[str, Any]],
    task_id: str,
    drop_dir: Path,
    evidence_dir: Path,
    now: datetime,
) -> dict[str, Any]:
    now_iso = _iso_utc(now)
    existing = _safe_read_json(queue_path)
    if existing is None or existing.get("schema_version") != QUEUE_SCHEMA_VERSION:
        existing = {
            "schema_version": QUEUE_SCHEMA_VERSION,
            "generated_at_utc": now_iso,
            "task_id": task_id,
            "drop_dir": str(drop_dir),
            "evidence_dir": str(evidence_dir),
            "items": [],
        }

    existing_items = existing.get("items", [])
    if not isinstance(existing_items, list):
        existing_items = []
    item_by_id = {
        str(item.get("id")): item
        for item in existing_items
        if isinstance(item, dict) and str(item.get("id", "")).startswith("manual")
    }

    reconciled_items: list[dict[str, Any]] = []
    for row in rows:
        row_id = row["id"]
        candidate = item_by_id.get(row_id)
        if candidate is None:
            candidate = _build_item_from_row(row=row, task_id=task_id, now_iso=now_iso)
        else:
            candidate.setdefault("created_at_utc", now_iso)
            candidate["name"] = row["name"]
            candidate["task_id"] = candidate.get("task_id") or task_id
            candidate["criteria"] = row.get("criteria", candidate.get("criteria", ""))
            candidate["file_pattern"] = candidate.get("file_pattern") or _default_file_pattern(
                candidate["task_id"], row_id
            )
            target = row.get("img_target") or MISSING_CAPTURE_TOKEN
            if target != MISSING_CAPTURE_TOKEN and candidate.get("status") != "RECEIVED":
                candidate["status"] = "RECEIVED"
                candidate["evidence_file"] = Path(target).name
                candidate["received_at_utc"] = candidate.get("received_at_utc") or now_iso
        reconciled_items.append(candidate)

    existing["generated_at_utc"] = now_iso
    existing["task_id"] = task_id
    existing["drop_dir"] = str(drop_dir)
    existing["evidence_dir"] = str(evidence_dir)
    existing["items"] = reconciled_items
    return existing


def _load_or_init_alerts(alerts_path: Path, now_iso: str) -> dict[str, Any]:
    data = _safe_read_json(alerts_path)
    if data is None or data.get("schema_version") != ALERT_SCHEMA_VERSION:
        data = {
            "schema_version": ALERT_SCHEMA_VERSION,
            "generated_at_utc": now_iso,
            "events": [],
        }
    events = data.get("events")
    if not isinstance(events, list):
        data["events"] = []
    data["generated_at_utc"] = now_iso
    return data


def _load_or_init_state(state_path: Path, now_iso: str) -> dict[str, Any]:
    data = _safe_read_json(state_path)
    if data is None or data.get("schema_version") != STATE_SCHEMA_VERSION:
        data = {
            "schema_version": STATE_SCHEMA_VERSION,
            "generated_at_utc": now_iso,
            "active_owner_id": "",
            "updated_at_utc": now_iso,
        }
    data["generated_at_utc"] = now_iso
    if "active_owner_id" not in data:
        data["active_owner_id"] = ""
    if "updated_at_utc" not in data:
        data["updated_at_utc"] = now_iso
    return data


def _load_or_init_registry(registry_path: Path, now_iso: str) -> dict[str, Any]:
    data = _safe_read_json(registry_path)
    if data is None or data.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        data = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "generated_at_utc": now_iso,
            "entries": {},
        }
    entries = data.get("entries")
    if not isinstance(entries, dict):
        data["entries"] = {}
    data["generated_at_utc"] = now_iso
    return data


def _resolve_occupancy(
    *,
    single_occupancy: bool,
    state: dict[str, Any],
    owner_id: str,
    now_iso: str,
    auto_claim_empty: bool,
) -> tuple[bool, dict[str, Any], str]:
    if not single_occupancy:
        return True, state, owner_id

    active_owner = str(state.get("active_owner_id", "")).strip()
    if not active_owner and auto_claim_empty:
        active_owner = owner_id
        state["active_owner_id"] = owner_id
        state["updated_at_utc"] = now_iso

    is_active = active_owner == owner_id
    return is_active, state, active_owner


def _upsert_registry_entry(
    *,
    registry: dict[str, Any],
    owner_id: str,
    repo_key: str,
    repo_root: str,
    now_iso: str,
    status: str,
    active_owner_id: str,
    summary: dict[str, int],
) -> dict[str, Any]:
    entries = registry.setdefault("entries", {})
    entries[owner_id] = {
        "owner_id": owner_id,
        "repo_key": repo_key,
        "repo_root": repo_root,
        "status": status,
        "active_owner_id": active_owner_id,
        "last_seen_utc": now_iso,
        "summary": summary,
    }
    registry["generated_at_utc"] = now_iso
    return registry


def _append_alert(
    alerts: dict[str, Any],
    *,
    now_iso: str,
    level: str,
    item_id: str,
    message: str,
    evidence_file: str | None = None,
) -> None:
    alerts.setdefault("events", [])
    alerts["events"].append(
        {
            "timestamp_utc": now_iso,
            "level": level,
            "item_id": item_id,
            "message": message,
            "evidence_file": evidence_file,
        }
    )


def _find_matching_capture(drop_dir: Path, pattern: str) -> Path | None:
    if not drop_dir.exists():
        return None
    regex = re.compile(pattern, flags=re.IGNORECASE)
    matches = [path for path in drop_dir.iterdir() if path.is_file() and regex.match(path.name)]
    if not matches:
        return None
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0]


def _list_drop_images(drop_dir: Path) -> list[Path]:
    if not drop_dir.exists():
        return []
    files = [
        path
        for path in drop_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VALID_IMAGE_EXTENSIONS
    ]
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def _default_terminal_dir() -> Path | None:
    """Return the Cursor terminals folder for this project, or None if not detectable."""
    userprofile = Path(os.environ.get("USERPROFILE", "~")).expanduser()
    cursor_projects = userprofile / ".cursor" / "projects"
    if not cursor_projects.exists():
        return None
    # Map the workspace root to the slug Cursor uses (drive colon → hyphen, backslashes → hyphens)
    # e.g.  E:\Code\SOP  →  e-Code-SOP
    try:
        workspace = Path(__file__).resolve().parents[3]
        slug = workspace.as_posix().replace(":", "").replace("/", "-").lstrip("-")
        candidate = cursor_projects / slug / "terminals"
        if candidate.exists():
            return candidate
        # Fallback: search for any terminals folder whose slug contains the repo name
        repo_name = workspace.name
        for entry in cursor_projects.iterdir():
            if repo_name.lower() in entry.name.lower():
                t = entry / "terminals"
                if t.exists():
                    return t
    except Exception:
        pass
    return None


def _scan_terminal_files(terminal_dir: Path) -> list[Path]:
    """Scan all .txt files in *terminal_dir* and return image paths found in them.

    Two signal syntaxes are accepted (case-insensitive):
      EVIDENCE:<path>          explicit operator signal
      Any bare filesystem path ending in .png/.jpg/.jpeg/.webp
    Returned paths are deduplicated and ordered by first appearance.
    """
    if not terminal_dir.exists():
        return []
    found: list[Path] = []
    seen: set[str] = set()
    for txt_file in sorted(terminal_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime):
        try:
            # Read last 8 KB only — terminals can be huge
            size = txt_file.stat().st_size
            offset = max(0, size - 8192)
            with open(txt_file, "r", encoding="utf-8", errors="replace") as fh:
                if offset:
                    fh.seek(offset)
                tail = fh.read()
        except OSError:
            continue
        for line in tail.splitlines():
            m = TERMINAL_EVIDENCE_SIGNAL_RE.search(line)
            if not m:
                continue
            raw = m.group("signal") or m.group("path")
            if not raw:
                continue
            raw = raw.strip("'\"")
            key = raw.lower()
            if key not in seen:
                seen.add(key)
                found.append(Path(raw))
    return found


def _safe_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    if not token:
        return "capture"
    return token[:24]


def _build_auto_filename(item: dict[str, Any], now: datetime, extension: str) -> str:
    task_id = str(item.get("task_id", "T00")).upper()
    item_id = str(item.get("id", "manual"))
    context = _safe_token(str(item.get("name", "capture")))
    date_token = now.strftime("%Y%m%d")
    ext = extension.lower()
    return f"{task_id}_{item_id}_{context}_{date_token}{ext}"


def _dedupe_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 2
    while True:
        candidate = parent / f"{stem}_v{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _copy_capture_file(*, source: Path, destination: Path, move_file: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() == destination.resolve():
        return
    if move_file:
        shutil.move(str(source), str(destination))
    else:
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=f"{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        os.close(tmp_fd)
        try:
            shutil.copy2(str(source), tmp_path)
            os.replace(tmp_path, destination)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


def _update_index_lines(
    *,
    lines: list[str],
    rows: list[dict[str, Any]],
    queue: dict[str, Any],
    now: datetime,
) -> list[str]:
    date_token = now.strftime("%Y-%m-%d")
    item_by_id = {
        str(item.get("id")): item for item in queue.get("items", []) if isinstance(item, dict)
    }
    updated = list(lines)
    for row in rows:
        item = item_by_id.get(row["id"])
        if item is None:
            continue
        status = str(item.get("status", "PENDING")).upper()
        criteria = str(item.get("criteria", row.get("criteria", ""))).strip()
        evidence_target = MISSING_CAPTURE_TOKEN
        result = "Machine PASS + Manual Pending"

        if status == "RECEIVED" and item.get("evidence_file"):
            evidence_target = str(item["evidence_file"])
            result = "PASS"
        elif status == "BLOCKED":
            result = "BLOCK"
        elif status == "WARNED":
            result = "Machine PASS + Manual Pending"

        evidence_cell = _format_evidence_cell(
            evidence_target=evidence_target,
            criteria=criteria,
        )
        updated[row["line_index"]] = (
            f"| {row['id']} | {row['name']} | {result} | {date_token} | {evidence_cell} |"
        )
    return updated


def process_cycle(
    *,
    queue: dict[str, Any],
    drop_dir: Path,
    evidence_dir: Path,
    warn_minutes: int,
    block_minutes: int,
    min_image_bytes: int,
    move_from_drop: bool,
    accept_any_filename: bool,
    now: datetime,
    alerts: dict[str, Any],
    terminal_poll: bool = False,
    terminal_dir: Path | None = None,
) -> dict[str, Any]:
    now_iso = _iso_utc(now)
    items = queue.get("items", [])
    if not isinstance(items, list):
        raise ManualCaptureError("Queue payload 'items' must be a list")

    # When terminal_poll is active, harvest image paths from Cursor terminal files
    # instead of scanning the Evidence_Drop folder.
    if terminal_poll:
        terminal_images = _scan_terminal_files(terminal_dir) if terminal_dir else []
        fallback_images: list[Path] = terminal_images  # treat as accept_any_filename pool
        _accept_any = True
        _move = True  # terminal paths are the source; always move/copy into evidence_dir
    else:
        fallback_images = _list_drop_images(drop_dir) if accept_any_filename else []
        _accept_any = accept_any_filename
        _move = move_from_drop
    consumed_fallback: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id", "manual_unknown"))
        status = str(item.get("status", "PENDING")).upper()

        if status == "RECEIVED":
            continue

        file_pattern = str(item.get("file_pattern") or "")
        if not file_pattern:
            item["file_pattern"] = _default_file_pattern(
                str(item.get("task_id", "T00")),
                item_id,
            )
            file_pattern = str(item["file_pattern"])

        # Drop-dir pattern match is skipped in terminal_poll mode (no drop folder).
        matched: Path | None = None
        matched_via_fallback = False
        if not terminal_poll:
            matched = _find_matching_capture(drop_dir=drop_dir, pattern=file_pattern)
        if matched is None and _accept_any:
            for candidate in fallback_images:
                key = str(candidate.resolve()) if candidate.is_absolute() else str(candidate)
                if key in consumed_fallback:
                    continue
                consumed_fallback.add(key)
                matched = candidate
                matched_via_fallback = True
                break
        if matched is not None:
            is_valid, reason = _validate_image_file(matched, min_bytes=min_image_bytes)
            if not is_valid:
                _append_alert(
                    alerts,
                    now_iso=now_iso,
                    level="WARN",
                    item_id=item_id,
                    message=f"Rejected capture '{matched.name}' ({reason})",
                    evidence_file=matched.name,
                )
                continue

            if matched_via_fallback or terminal_poll:
                destination = _dedupe_destination(
                    evidence_dir / _build_auto_filename(item=item, now=now, extension=matched.suffix)
                )
            else:
                destination = _dedupe_destination(evidence_dir / matched.name)
            effective_move = _move or matched_via_fallback
            _copy_capture_file(source=matched, destination=destination, move_file=effective_move)
            digest = _sha256_of_file(destination)
            item["status"] = "RECEIVED"
            item["received_at_utc"] = now_iso
            item["evidence_file"] = destination.name
            item["evidence_sha256"] = digest
            _append_alert(
                alerts,
                now_iso=now_iso,
                level="INFO",
                item_id=item_id,
                message=f"Accepted capture '{destination.name}'",
                evidence_file=destination.name,
            )
            continue

        created_at = _parse_iso_utc(str(item.get("created_at_utc")))
        if created_at is None:
            created_at = now
            item["created_at_utc"] = now_iso

        elapsed_minutes = max(0.0, (now - created_at).total_seconds() / 60.0)

        if elapsed_minutes >= float(block_minutes) and status != "BLOCKED":
            item["status"] = "BLOCKED"
            item["blocked_at_utc"] = now_iso
            _append_alert(
                alerts,
                now_iso=now_iso,
                level="BLOCK",
                item_id=item_id,
                message=(
                    f"Manual evidence missing for {elapsed_minutes:.1f} minutes "
                    f"(threshold={block_minutes}m)"
                ),
            )
            continue

        warned_at = _parse_iso_utc(str(item.get("warned_at_utc")))
        if elapsed_minutes >= float(warn_minutes) and warned_at is None:
            item["status"] = "WARNED"
            item["warned_at_utc"] = now_iso
            _append_alert(
                alerts,
                now_iso=now_iso,
                level="WARN",
                item_id=item_id,
                message=(
                    f"Manual evidence still missing at {elapsed_minutes:.1f} minutes "
                    f"(threshold={warn_minutes}m)"
                ),
            )
        elif status not in {"WARNED", "BLOCKED"}:
            item["status"] = "PENDING"

    queue["generated_at_utc"] = now_iso
    return queue


def summarize_queue(queue: dict[str, Any]) -> dict[str, int]:
    counts = {"pending": 0, "warned": 0, "blocked": 0, "received": 0}
    for item in queue.get("items", []):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "PENDING")).upper()
        if status == "RECEIVED":
            counts["received"] += 1
        elif status == "BLOCKED":
            counts["blocked"] += 1
        elif status == "WARNED":
            counts["warned"] += 1
        else:
            counts["pending"] += 1
    return counts


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_index = repo_root / "e2e_test" / "docs" / "context" / "e2e_evidence" / "index.md"
    default_evidence_dir = default_index.parent
    default_queue = default_evidence_dir / "manual_capture_queue.json"
    default_alerts = default_evidence_dir / "manual_capture_alerts.json"
    default_drop_dir = _detect_default_drop_dir()

    parser = argparse.ArgumentParser(
        description="Poll a drop zone for real manual captures and close Manual Pending evidence loops."
    )
    parser.add_argument("--index", type=Path, default=default_index, help="Path to evidence index.md")
    parser.add_argument("--queue", type=Path, default=default_queue, help="Queue state JSON path")
    parser.add_argument("--alerts", type=Path, default=default_alerts, help="Alert events JSON path")
    parser.add_argument("--drop-dir", type=Path, default=default_drop_dir, help="Drop zone directory")
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=default_evidence_dir,
        help="Final evidence directory where accepted captures are stored",
    )
    parser.add_argument("--warn-minutes", type=int, default=DEFAULT_WARN_MINUTES)
    parser.add_argument("--block-minutes", type=int, default=DEFAULT_BLOCK_MINUTES)
    parser.add_argument("--interval-seconds", type=int, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--min-image-bytes", type=int, default=DEFAULT_MIN_IMAGE_BYTES)
    parser.add_argument("--watch", action="store_true", help="Run continuously and poll on interval")
    parser.add_argument(
        "--max-watch-minutes",
        type=int,
        default=0,
        help="Optional wall-time cap for watch mode (0 means unlimited)",
    )
    parser.add_argument(
        "--move-from-drop",
        action="store_true",
        help="Move files from drop dir into evidence dir instead of copy",
    )
    parser.add_argument(
        "--fail-on-block",
        action="store_true",
        help="Exit code 2 when any item is BLOCKED after cycle",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print updates only; no writes",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print queue summary as JSON for automation hooks",
    )
    parser.add_argument(
        "--accept-any-filename",
        action="store_true",
        help=(
            "Accept any image filename from drop dir and auto-assign FIFO to pending manual slots. "
            "Use when user workflow is drop-and-go without naming."
        ),
    )
    parser.add_argument(
        "--single-occupancy",
        action="store_true",
        help=(
            "Enable single-owner mode on a shared drop folder. "
            "Only the active owner processes incoming files; others register as STANDBY."
        ),
    )
    parser.add_argument(
        "--owner-id",
        type=str,
        default="",
        help="Stable owner identity (recommended: scheduler task name).",
    )
    parser.add_argument(
        "--repo-key",
        type=str,
        default="",
        help="Short repo identifier used in occupancy registry (example: Quant, Film).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional absolute repo root used for registry metadata.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Optional shared occupancy state file. Defaults to <drop-dir>/repo_capture_state.json.",
    )
    parser.add_argument(
        "--registry-file",
        type=Path,
        default=None,
        help="Optional shared repo status registry file. Defaults to <drop-dir>/repo_capture_registry.json.",
    )
    parser.add_argument(
        "--disable-auto-claim",
        action="store_true",
        help="In single-occupancy mode, do not auto-claim active owner when state has no owner.",
    )
    parser.add_argument(
        "--terminal-poll",
        action="store_true",
        help=(
            "Disable Evidence_Drop folder scanning entirely and instead poll Cursor IDE "
            "terminal files for evidence image paths. "
            "Signals recognised: 'EVIDENCE:<path>' or any bare path ending in .png/.jpg/.jpeg/.webp."
        ),
    )
    parser.add_argument(
        "--terminal-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing Cursor terminal .txt files to poll. "
            "Defaults to auto-detected ~/.cursor/projects/<slug>/terminals/."
        ),
    )
    return parser.parse_args()


def _run_once(args: argparse.Namespace) -> tuple[dict[str, int], int]:
    now = _now_utc()
    now_iso = _iso_utc(now)
    lines, rows = load_index_rows(args.index)
    task_id = infer_task_id(lines)
    owner_id = args.owner_id.strip() if args.owner_id else ""
    if not owner_id:
        owner_id = f"owner-{os.getpid()}"

    repo_root = args.repo_root.resolve() if args.repo_root else args.index.resolve().parents[3]
    repo_key = args.repo_key.strip() if args.repo_key else repo_root.name
    state_path = args.state_file.resolve() if args.state_file else args.drop_dir / "repo_capture_state.json"
    registry_path = (
        args.registry_file.resolve() if args.registry_file else args.drop_dir / "repo_capture_registry.json"
    )

    state_payload = _load_or_init_state(state_path=state_path, now_iso=now_iso)
    is_active, state_payload, active_owner_id = _resolve_occupancy(
        single_occupancy=args.single_occupancy,
        state=state_payload,
        owner_id=owner_id,
        now_iso=now_iso,
        auto_claim_empty=not args.disable_auto_claim,
    )

    if not is_active:
        existing_queue = _safe_read_json(args.queue)
        summary = summarize_queue(existing_queue if isinstance(existing_queue, dict) else {"items": []})
        registry = _load_or_init_registry(registry_path=registry_path, now_iso=now_iso)
        registry = _upsert_registry_entry(
            registry=registry,
            owner_id=owner_id,
            repo_key=repo_key,
            repo_root=str(repo_root),
            now_iso=now_iso,
            status="STANDBY",
            active_owner_id=active_owner_id,
            summary=summary,
        )
        if args.dry_run:
            print(f"[DRY-RUN] Occupancy status: STANDBY (active_owner={active_owner_id or 'NONE'})")
            print("[DRY-RUN] Queue summary:")
            print(json.dumps(summary, indent=2, ensure_ascii=True))
            if args.print_json:
                print(
                    json.dumps(
                        {
                            "summary": summary,
                            "occupancy": {
                                "status": "STANDBY",
                                "active_owner_id": active_owner_id,
                                "owner_id": owner_id,
                                "repo_key": repo_key,
                            },
                        },
                        ensure_ascii=True,
                    )
                )
            return summary, 0

        args.drop_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(registry_path, registry)
        if args.single_occupancy:
            _atomic_write_json(state_path, state_payload)
        if args.print_json:
            print(
                json.dumps(
                    {
                        "summary": summary,
                        "occupancy": {
                            "status": "STANDBY",
                            "active_owner_id": active_owner_id,
                            "owner_id": owner_id,
                            "repo_key": repo_key,
                        },
                    },
                    ensure_ascii=True,
                )
            )
        else:
            print(
                (
                    "manual-capture standby: "
                    f"owner={owner_id} active_owner={active_owner_id or 'NONE'} "
                    f"pending={summary['pending']} warned={summary['warned']} "
                    f"blocked={summary['blocked']} received={summary['received']}"
                )
            )
        return summary, 0

    queue = ensure_queue_payload(
        queue_path=args.queue,
        rows=rows,
        task_id=task_id,
        drop_dir=args.drop_dir,
        evidence_dir=args.evidence_dir,
        now=now,
    )
    alerts = _load_or_init_alerts(args.alerts, _iso_utc(now))

    # Resolve terminal directory when terminal_poll is requested
    terminal_dir: Path | None = None
    if args.terminal_poll:
        if args.terminal_dir is not None:
            terminal_dir = args.terminal_dir.resolve()
        else:
            terminal_dir = _default_terminal_dir()

    queue = process_cycle(
        queue=queue,
        drop_dir=args.drop_dir,
        evidence_dir=args.evidence_dir,
        warn_minutes=args.warn_minutes,
        block_minutes=args.block_minutes,
        min_image_bytes=args.min_image_bytes,
        move_from_drop=args.move_from_drop,
        accept_any_filename=args.accept_any_filename,
        now=now,
        alerts=alerts,
        terminal_poll=args.terminal_poll,
        terminal_dir=terminal_dir,
    )
    updated_lines = _update_index_lines(lines=lines, rows=rows, queue=queue, now=now)
    summary = summarize_queue(queue)
    registry = _load_or_init_registry(registry_path=registry_path, now_iso=now_iso)
    registry = _upsert_registry_entry(
        registry=registry,
        owner_id=owner_id,
        repo_key=repo_key,
        repo_root=str(repo_root),
        now_iso=now_iso,
        status="ACTIVE",
        active_owner_id=active_owner_id or owner_id,
        summary=summary,
    )

    if args.dry_run:
        print(f"[DRY-RUN] Occupancy status: ACTIVE (owner={owner_id})")
        print("[DRY-RUN] Queue summary:")
        print(json.dumps(summary, indent=2, ensure_ascii=True))
        if args.print_json:
            print(
                json.dumps(
                    {
                        "summary": summary,
                        "queue": queue,
                        "occupancy": {
                            "status": "ACTIVE",
                            "active_owner_id": active_owner_id or owner_id,
                            "owner_id": owner_id,
                            "repo_key": repo_key,
                        },
                    },
                    ensure_ascii=True,
                )
            )
        return summary, 0

    args.drop_dir.mkdir(parents=True, exist_ok=True)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(args.queue, queue)
    _atomic_write_json(args.alerts, alerts)
    _atomic_write_text(args.index, "\n".join(updated_lines).rstrip() + "\n")
    _atomic_write_json(registry_path, registry)
    if args.single_occupancy:
        state_payload["active_owner_id"] = owner_id
        state_payload["updated_at_utc"] = now_iso
        _atomic_write_json(state_path, state_payload)

    if args.print_json:
        print(
            json.dumps(
                {
                    "summary": summary,
                    "occupancy": {
                        "status": "ACTIVE",
                        "active_owner_id": active_owner_id or owner_id,
                        "owner_id": owner_id,
                        "repo_key": repo_key,
                    },
                },
                ensure_ascii=True,
            )
        )
    else:
        print(
            (
                "manual-capture summary: "
                f"pending={summary['pending']} warned={summary['warned']} "
                f"blocked={summary['blocked']} received={summary['received']}"
            )
        )

    if args.fail_on_block and summary["blocked"] > 0:
        return summary, 2
    return summary, 0


def main() -> int:
    args = parse_args()
    try:
        if args.watch:
            started = time.monotonic()
            while True:
                summary, code = _run_once(args)
                if code != 0:
                    return code
                if summary["received"] > 0 and (summary["pending"] + summary["warned"] + summary["blocked"]) == 0:
                    return 0
                if args.max_watch_minutes > 0:
                    elapsed_minutes = (time.monotonic() - started) / 60.0
                    if elapsed_minutes >= float(args.max_watch_minutes):
                        return 0
                time.sleep(max(1, args.interval_seconds))
        else:
            _, code = _run_once(args)
            return code
    except ManualCaptureError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"I/O failure: {exc}", file=sys.stderr)
        return 2
    except re.error as exc:
        print(f"Invalid regex pattern in queue payload: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
