from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
PACKET_KEYS = (
    "schema_version",
    "generated_at_utc",
    "source_files",
    "active_phase",
    "what_was_done",
    "what_is_locked",
    "what_is_next",
    "first_command",
    "next_todos",
)
REQUIRED_SECTION_KEYS = (
    "what_was_done",
    "what_is_locked",
    "what_is_next",
    "first_command",
)
REQUIRED_MD_HEADERS = (
    "## What Was Done",
    "## What Is Locked",
    "## What Is Next",
    "## First Command",
)
MAX_CONTEXT_AGE_HOURS = 24.0
DEFAULT_GEMINI_OUT_DIR = Path("docs/handover/gemini")
DEFAULT_TOP_LEVEL_PM_PATH = Path("top_level_PM.md")
DEFAULT_PHILOSOPHY_LOG_PATH = Path("docs/context/philosophy_migration_log.json")

_PHASE_RE = re.compile(r"phase(\d+)", re.IGNORECASE)
_LABEL_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\d+[.)]\s*)?(?P<label>[A-Za-z][A-Za-z0-9 \-_/()]+?)\s*:\s*(?P<value>.*)\s*$"
)
_HEADING_RE = re.compile(r"^\s*#{1,6}\s*(?P<label>.+?)\s*$")

_LABEL_ALIASES = {
    "what was done": "what_was_done",
    "what is locked": "what_is_locked",
    "what is next": "what_is_next",
    "what remains": "what_is_next",
    "first command": "first_command",
    "immediate first step": "first_command",
    "proposed full historical run command": "first_command",
    "next todos": "next_todos",
    "next todo": "next_todos",
    "nextphase roadmap": "next_todos",
    "next phase roadmap": "next_todos",
    "nextphase roadmap summary": "next_todos",
    "next phase roadmap summary": "next_todos",
}


class ContextPacketError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceDocs:
    phase_briefs: list[Path]
    phase_handovers: list[Path]
    decision_log: Path
    lessons: Path


def _normalize_label(raw: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", raw.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _canonical_label(raw: str) -> str | None:
    return _LABEL_ALIASES.get(_normalize_label(raw))


def _clean_content_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"^\d+[.)]\s+", "", cleaned)
    return cleaned.strip()


def _dedupe_keep_order(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _phase_number(path: Path) -> int:
    match = _PHASE_RE.search(path.name)
    if not match:
        return -1
    return int(match.group(1))


def _discover_sources(repo_root: Path) -> SourceDocs:
    docs_root = repo_root / "docs"
    phase_briefs = sorted(
        (docs_root / "phase_brief").glob("phase*-brief.md"),
        key=lambda p: (_phase_number(p), p.as_posix()),
    )
    phase_handovers = sorted(
        (docs_root / "handover").glob("phase*_handover.md"),
        key=lambda p: (_phase_number(p), p.as_posix()),
    )
    decision_log = docs_root / "decision log.md"
    lessons = docs_root / "lessonss.md"

    missing: list[str] = []
    if not phase_briefs:
        missing.append("docs/phase_brief/phase*-brief.md")
    if not phase_handovers:
        missing.append("docs/handover/phase*_handover.md")
    if not decision_log.exists():
        missing.append("docs/decision log.md")
    if not lessons.exists():
        missing.append("docs/lessonss.md")
    if missing:
        joined = ", ".join(missing)
        raise ContextPacketError(f"Missing required source files: {joined}")

    return SourceDocs(
        phase_briefs=phase_briefs,
        phase_handovers=phase_handovers,
        decision_log=decision_log,
        lessons=lessons,
    )


def _extract_context_block(text: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if _normalize_label(line).find("new context packet") >= 0:
            start = idx + 1
            break
    if start is None:
        return lines

    allowed_heading_sections = {
        key for key in REQUIRED_SECTION_KEYS
    }.union({"next_todos"})
    end = len(lines)
    for idx in range(start, len(lines)):
        heading_match = _HEADING_RE.match(lines[idx])
        if heading_match:
            heading_label = _canonical_label(heading_match.group("label"))
            if heading_label in allowed_heading_sections:
                continue
            end = idx
            break
    return lines[start:end]


def _parse_context_sections(text: str) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {
        "what_was_done": [],
        "what_is_locked": [],
        "what_is_next": [],
        "first_command": [],
        "next_todos": [],
    }
    in_code_fence = False
    current_section: str | None = None

    for raw_line in _extract_context_block(text):
        stripped = raw_line.strip()
        if not stripped:
            continue

        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence and current_section == "first_command":
            command_line = stripped
            if command_line:
                parsed["first_command"].append(command_line)
            continue

        label_match = _LABEL_LINE_RE.match(raw_line)
        if label_match:
            label = _canonical_label(label_match.group("label"))
            if label is not None:
                current_section = label
                inline_value = _clean_content_line(label_match.group("value"))
                if inline_value:
                    parsed[label].append(inline_value)
                continue

        heading_match = _HEADING_RE.match(raw_line)
        if heading_match:
            heading_label = _canonical_label(heading_match.group("label"))
            current_section = heading_label
            continue

        if current_section is None:
            continue
        value = _clean_content_line(raw_line)
        if value:
            parsed[current_section].append(value)

    for key in parsed:
        parsed[key] = _dedupe_keep_order(parsed[key])
    return parsed


def _select_context_source(
    phase_briefs: list[Path], phase_handovers: list[Path]
) -> tuple[Path, dict[str, list[str]]]:
    candidates: list[tuple[int, int, Path]] = []
    for path in phase_handovers:
        candidates.append((_phase_number(path), 0, path))
    for path in phase_briefs:
        candidates.append((_phase_number(path), 1, path))
    candidates.sort(key=lambda item: (-item[0], item[1], item[2].as_posix()))

    errors: list[str] = []
    for _, _, path in candidates:
        sections = _parse_context_sections(path.read_text(encoding="utf-8"))
        first_command = sections["first_command"][0] if sections["first_command"] else ""
        missing: list[str] = []
        if not sections["what_was_done"]:
            missing.append("what_was_done")
        if not sections["what_is_locked"]:
            missing.append("what_is_locked")
        if not sections["what_is_next"]:
            missing.append("what_is_next")
        if not first_command:
            missing.append("first_command")
        if not missing:
            return path, sections
        errors.append(f"{path.as_posix()}: {', '.join(missing)}")

    details = "; ".join(errors)
    raise ContextPacketError(
        "Missing required sections in all candidate phase docs. "
        f"Required: {', '.join(REQUIRED_SECTION_KEYS)}. Details: {details}"
    )


def _active_phase(phase_briefs: list[Path], selected_source: Path) -> int:
    selected_phase = _phase_number(selected_source)
    if selected_phase >= 0:
        return selected_phase
    return max(_phase_number(path) for path in phase_briefs)


def _generated_at_utc(explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")


def _parse_generated_at_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        raise ValueError("generated_at_utc must include UTC offset or Z suffix")
    return parsed.astimezone(timezone.utc)


def _packet_without_timestamp(packet: dict[str, object]) -> dict[str, object]:
    out = dict(packet)
    out.pop("generated_at_utc", None)
    return out


def _validate_packet_schema(packet: dict[str, Any]) -> None:
    if tuple(packet.keys()) != PACKET_KEYS:
        raise ContextPacketError("JSON schema key set drifted from PACKET_KEYS")
    if str(packet.get("schema_version", "")).strip() != SCHEMA_VERSION:
        raise ContextPacketError("schema_version mismatch")
    if not str(packet.get("first_command", "")).strip():
        raise ContextPacketError("first_command must be non-empty")
    for key in ("what_was_done", "what_is_locked", "what_is_next", "next_todos"):
        values = packet.get(key)
        if not isinstance(values, list) or not values:
            raise ContextPacketError(f"{key} must be a non-empty list")
    try:
        generated_at = _parse_generated_at_utc(str(packet.get("generated_at_utc", "")))
    except Exception as exc:
        raise ContextPacketError(f"Invalid generated_at_utc: {exc}") from exc
    age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600.0
    if age_hours > MAX_CONTEXT_AGE_HOURS:
        raise ContextPacketError(
            f"Context artifact too old ({age_hours:.2f}h > {MAX_CONTEXT_AGE_HOURS:.0f}h)"
        )


def _validate_markdown_contract(markdown_text: str) -> None:
    headers = [line.strip() for line in markdown_text.splitlines() if line.startswith("## ")]
    if headers != list(REQUIRED_MD_HEADERS):
        raise ContextPacketError(
            "Markdown section contract mismatch. "
            f"Expected headers={list(REQUIRED_MD_HEADERS)}, got={headers}"
        )
    if "## First Command" not in markdown_text:
        raise ContextPacketError("Markdown missing First Command section")


def build_context_packet(
    repo_root: Path, generated_at_utc: str | None = None
) -> dict[str, object]:
    sources = _discover_sources(repo_root=repo_root)
    source_doc, sections = _select_context_source(
        phase_briefs=sources.phase_briefs, phase_handovers=sources.phase_handovers
    )

    first_command = sections["first_command"][0].strip()
    if not first_command:
        raise ContextPacketError("Missing required sections: first_command")

    what_is_next = sections["what_is_next"]
    next_todos = sections["next_todos"] if sections["next_todos"] else what_is_next
    next_todos = _dedupe_keep_order(next_todos)

    source_files = sorted(
        {
            path.relative_to(repo_root).as_posix()
            for path in (
                [*sources.phase_briefs]
                + [*sources.phase_handovers]
                + [sources.decision_log, sources.lessons]
            )
        }
    )

    packet: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _generated_at_utc(generated_at_utc),
        "source_files": source_files,
        "active_phase": _active_phase(sources.phase_briefs, source_doc),
        "what_was_done": sections["what_was_done"],
        "what_is_locked": sections["what_is_locked"],
        "what_is_next": what_is_next,
        "first_command": first_command,
        "next_todos": next_todos,
    }

    _validate_packet_schema(packet)
    return packet


def _render_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render_context_markdown(packet: dict[str, object]) -> str:
    _validate_packet_schema(packet)

    what_was_done = [str(item) for item in packet["what_was_done"]]
    what_is_locked = [str(item) for item in packet["what_is_locked"]]
    what_is_next = [str(item) for item in packet["what_is_next"]]
    next_todos = [str(item) for item in packet["next_todos"]]
    merged_next = _dedupe_keep_order([*what_is_next, *next_todos])
    first_command = str(packet["first_command"]).strip()

    if not merged_next or not first_command:
        raise ContextPacketError("Missing required content to render markdown")

    if "`" in first_command or "\n" in first_command:
        first_command_block = "```text\n" + first_command + "\n```"
    else:
        first_command_block = f"`{first_command}`"

    parts = [
        "## What Was Done",
        _render_bullets(what_was_done),
        "",
        "## What Is Locked",
        _render_bullets(what_is_locked),
        "",
        "## What Is Next",
        _render_bullets(merged_next),
        "",
        "## First Command",
        first_command_block,
        "",
    ]
    markdown = "\n".join(parts)
    _validate_markdown_contract(markdown)
    return markdown


def _fenced_block(text: str, language: str = "text") -> str:
    body = text.rstrip("\n")
    return f"~~~{language}\n{body}\n~~~"


def _read_required_text(path: Path, description: str) -> str:
    if not path.exists():
        raise ContextPacketError(f"Missing required {description}: {path}")
    return path.read_text(encoding="utf-8")


def _read_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _relative_display(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_gemini_handover_path(
    *, repo_root: Path, packet: dict[str, object], gemini_out_dir: Path
) -> Path:
    phase = int(packet["active_phase"])
    return gemini_out_dir / f"phase{phase}_gemini_handover.md"


def render_gemini_handover(
    *,
    repo_root: Path,
    packet: dict[str, object],
    context_json_text: str,
    context_md_text: str,
    top_level_pm_path: Path,
    philosophy_log_path: Path,
) -> str:
    _validate_packet_schema(packet)
    top_level_text = _read_required_text(top_level_pm_path, "top level PM file")
    source_files = [Path(str(item)) for item in packet["source_files"]]

    lines = [
        f"# Gemini Handover - Phase {int(packet['active_phase'])}",
        "",
        f"- GeneratedAtUTC: {packet['generated_at_utc']}",
        f"- SchemaVersion: {packet['schema_version']}",
        f"- SourceTopLevelPM: `{_relative_display(top_level_pm_path, repo_root)}`",
        "- SourceContextJSON: `docs/context/current_context.json`",
        "- SourceContextMD: `docs/context/current_context.md`",
        "",
        "## Top Level PM",
        _fenced_block(top_level_text, "markdown"),
        "",
        "## Context Packet (Markdown)",
        _fenced_block(context_md_text, "markdown"),
        "",
        "## Context Packet (JSON)",
        _fenced_block(context_json_text, "json"),
        "",
        "## Source Context Files",
    ]

    for rel_path in source_files:
        abs_path = repo_root / rel_path
        text = _read_required_text(abs_path, f"source context file `{rel_path.as_posix()}`")
        lines.extend(
            [
                "",
                f"### {rel_path.as_posix()}",
                _fenced_block(text, "markdown" if abs_path.suffix.lower() in {'.md', '.txt'} else "text"),
            ]
        )

    philosophy_log_text = _read_optional_text(philosophy_log_path)
    lines.extend(["", "## Philosophy Migration Log"])
    if philosophy_log_text is None:
        lines.append("- Status: NOT_FOUND")
        lines.append(
            f"- ExpectedPath: `{_relative_display(philosophy_log_path, repo_root)}`"
        )
    else:
        lines.extend(
            [
                f"- Source: `{_relative_display(philosophy_log_path, repo_root)}`",
                _fenced_block(philosophy_log_text, "json"),
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def write_context_outputs(
    packet: dict[str, object],
    json_path: Path,
    md_path: Path,
    *,
    repo_root: Path,
    gemini_out_dir: Path,
    top_level_pm_path: Path,
    philosophy_log_path: Path,
) -> None:
    _validate_packet_schema(packet)

    json_text = json.dumps(packet, indent=2, ensure_ascii=True) + "\n"
    md_text = render_context_markdown(packet)
    gemini_text = render_gemini_handover(
        repo_root=repo_root,
        packet=packet,
        context_json_text=json_text,
        context_md_text=md_text,
        top_level_pm_path=top_level_pm_path,
        philosophy_log_path=philosophy_log_path,
    )
    gemini_path = _resolve_gemini_handover_path(
        repo_root=repo_root,
        packet=packet,
        gemini_out_dir=gemini_out_dir,
    )
    _atomic_write_text(json_path, json_text)
    _atomic_write_text(md_path, md_text)
    _atomic_write_text(gemini_path, gemini_text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic context packet outputs.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root used for source discovery and relative defaults.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("docs/context/current_context.json"),
        help="JSON output path, relative to --repo-root when not absolute.",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/context/current_context.md"),
        help="Markdown output path, relative to --repo-root when not absolute.",
    )
    parser.add_argument(
        "--gemini-out-dir",
        type=Path,
        default=DEFAULT_GEMINI_OUT_DIR,
        help="Gemini handover output directory. File name is phase<NN>_gemini_handover.md.",
    )
    parser.add_argument(
        "--top-level-pm",
        type=Path,
        default=DEFAULT_TOP_LEVEL_PM_PATH,
        help="Top-level PM markdown file path used in Gemini handover.",
    )
    parser.add_argument(
        "--philosophy-log",
        type=Path,
        default=DEFAULT_PHILOSOPHY_LOG_PATH,
        help="Optional philosophy migration log included in Gemini handover when present.",
    )
    parser.add_argument(
        "--generated-at-utc",
        type=str,
        default=None,
        help="Optional explicit generated_at_utc value for deterministic runs.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing context artifacts against current sources and schema.",
    )
    return parser.parse_args()


def _resolve_output_path(repo_root: Path, output_path: Path) -> Path:
    if output_path.is_absolute():
        return output_path
    return repo_root / output_path


def validate_existing_outputs(
    *,
    repo_root: Path,
    json_path: Path,
    md_path: Path,
    gemini_out_dir: Path,
    top_level_pm_path: Path,
    philosophy_log_path: Path,
    generated_at_utc: str | None = None,
) -> None:
    if not json_path.exists():
        raise ContextPacketError(f"Missing context JSON artifact: {json_path}")
    if not md_path.exists():
        raise ContextPacketError(f"Missing context Markdown artifact: {md_path}")

    expected_packet = build_context_packet(
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
    try:
        existing_packet = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContextPacketError(f"Context JSON decode failure: {exc}") from exc
    if not isinstance(existing_packet, dict):
        raise ContextPacketError("Context JSON payload must be an object")
    _validate_packet_schema(existing_packet)
    if _packet_without_timestamp(existing_packet) != _packet_without_timestamp(expected_packet):
        raise ContextPacketError(
            "Context artifacts are stale relative to current source docs. "
            "Run build_context_packet.py to refresh."
        )
    markdown_text = md_path.read_text(encoding="utf-8")
    _validate_markdown_contract(markdown_text)
    expected_markdown = render_context_markdown(existing_packet).rstrip() + "\n"
    existing_markdown = markdown_text.rstrip() + "\n"
    if existing_markdown != expected_markdown:
        raise ContextPacketError(
            "Context Markdown artifact drifted from JSON payload. "
            "Run build_context_packet.py to refresh."
        )

    gemini_path = _resolve_gemini_handover_path(
        repo_root=repo_root,
        packet=existing_packet,
        gemini_out_dir=gemini_out_dir,
    )
    if not gemini_path.exists():
        raise ContextPacketError(f"Missing Gemini handover artifact: {gemini_path}")
    canonical_json_text = json.dumps(existing_packet, indent=2, ensure_ascii=True) + "\n"
    expected_gemini = (
        render_gemini_handover(
            repo_root=repo_root,
            packet=existing_packet,
            context_json_text=canonical_json_text,
            context_md_text=existing_markdown,
            top_level_pm_path=top_level_pm_path,
            philosophy_log_path=philosophy_log_path,
        ).rstrip()
        + "\n"
    )
    existing_gemini = gemini_path.read_text(encoding="utf-8").rstrip() + "\n"
    if existing_gemini != expected_gemini:
        raise ContextPacketError(
            "Gemini handover artifact drifted from context payload/top-level sources. "
            "Run build_context_packet.py to refresh."
        )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    try:
        json_out = _resolve_output_path(repo_root=repo_root, output_path=args.json_out)
        md_out = _resolve_output_path(repo_root=repo_root, output_path=args.md_out)
        gemini_out_dir = _resolve_output_path(
            repo_root=repo_root, output_path=args.gemini_out_dir
        )
        top_level_pm_path = _resolve_output_path(
            repo_root=repo_root, output_path=args.top_level_pm
        )
        philosophy_log_path = _resolve_output_path(
            repo_root=repo_root, output_path=args.philosophy_log
        )
        if args.validate:
            validate_existing_outputs(
                repo_root=repo_root,
                json_path=json_out,
                md_path=md_out,
                gemini_out_dir=gemini_out_dir,
                top_level_pm_path=top_level_pm_path,
                philosophy_log_path=philosophy_log_path,
                generated_at_utc=args.generated_at_utc,
            )
        else:
            packet = build_context_packet(
                repo_root=repo_root, generated_at_utc=args.generated_at_utc
            )
            write_context_outputs(
                packet=packet,
                json_path=json_out,
                md_path=md_out,
                repo_root=repo_root,
                gemini_out_dir=gemini_out_dir,
                top_level_pm_path=top_level_pm_path,
                philosophy_log_path=philosophy_log_path,
            )
    except ContextPacketError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"I/O failure while writing context packet: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
