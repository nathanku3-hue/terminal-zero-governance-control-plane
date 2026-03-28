from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.1.0"
DEFAULT_LOOP_CLOSURE_PATH = Path("docs/context/loop_closure_status_latest.json")
DEFAULT_STARTUP_INTAKE_PATH = Path("docs/context/startup_intake_latest.json")
DEFAULT_ROUND_CONTRACT_PATH = Path("docs/context/round_contract_latest.md")
DEFAULT_GO_SIGNAL_PATH = Path("docs/context/ceo_go_signal.md")
DEFAULT_CORPUS_DIR = Path("docs/context/profile_outcomes_corpus")


def _parse_iso_utc(value: str | None) -> str:
    if value is None or not value.strip():
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = value.strip()
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_bool_text(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean value '{value}'. Use true/false.")


def _normalize_rollback_status(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"no", "none", "false", "n", "0"}:
        return "NO"
    if normalized in {"partial", "part", "some"}:
        return "PARTIAL"
    if normalized in {"full", "yes", "true", "y", "1"}:
        return "FULL"
    raise ValueError(
        f"Invalid rollback status '{value}'. Use NO, PARTIAL, or FULL."
    )


def _normalize_semantic_issue_status(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"none", "no", "false", "n", "0"}:
        return "NONE"
    if normalized in {"present", "yes", "true", "y", "1"}:
        return "PRESENT"
    if normalized in {"unknown", "i don't know yet", "i dont know yet", "not_sure"}:
        return "I don't know yet"
    raise ValueError(
        "Invalid semantic issue status "
        f"'{value}'. Use NONE, PRESENT, or 'I don't know yet'."
    )


def _parse_non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise ValueError("Expected a non-negative integer.")
    return parsed


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "go", "ready"}:
            return True
        if text in {"0", "false", "no", "n", "hold", "not_ready"}:
            return False
    return None


def _resolve_path(repo_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _load_json_safe(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _load_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def _extract_go_action(go_signal_text: str) -> str:
    for raw_line in go_signal_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if "recommended action" not in lower:
            continue
        if ":" in line:
            return line.split(":", 1)[1].strip().upper() or "UNKNOWN"
    return "UNKNOWN"


def _parse_contract_fields(round_contract_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in round_contract_text.splitlines():
        match = re.match(r"^\s*-\s*([A-Z0-9_]+):\s*(.*)$", raw_line)
        if not match:
            continue
        fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def _infer_project_profile(
    *,
    startup_intake: dict[str, Any] | None,
    contract_fields: dict[str, str],
    explicit_project_profile: str | None,
) -> str:
    if explicit_project_profile and explicit_project_profile.strip():
        return explicit_project_profile.strip()

    if isinstance(startup_intake, dict):
        domain_bootstrap = startup_intake.get("domain_bucket_bootstrap")
        if isinstance(domain_bootstrap, dict):
            profile = str(domain_bootstrap.get("project_profile", "")).strip()
            if profile:
                return profile
        interrogation = startup_intake.get("interrogation")
        if isinstance(interrogation, dict):
            profile = str(interrogation.get("project_profile", "")).strip()
            if profile:
                return profile
    contract_profile = contract_fields.get("PROJECT_PROFILE", "").strip()
    if contract_profile:
        return contract_profile
    return "unknown"


def _infer_loop_closure_result(loop_closure: dict[str, Any] | None) -> str:
    if not isinstance(loop_closure, dict):
        return "UNKNOWN"
    for key in ("result", "overall_status", "status"):
        value = str(loop_closure.get(key, "")).strip()
        if value:
            return value.upper()
    return "UNKNOWN"


def _infer_board_reentry_required(contract_fields: dict[str, str]) -> bool:
    raw = contract_fields.get("BOARD_REENTRY_REQUIRED", "")
    parsed = _coerce_bool(raw)
    return bool(parsed) if parsed is not None else False


def _infer_unknown_domain_triggered(contract_fields: dict[str, str]) -> bool:
    for key in ("BOARD_REENTRY_REASON", "TRIGGERED_EXPERTS", "PRE_EXEC_DISAGREEMENT_CAPTURE"):
        value = contract_fields.get(key, "").upper()
        if "UNKNOWN_EXPERT_DOMAIN" in value or "UNKNOWN_DOMAIN" in value:
            return True
    return False


def _infer_ready_flag(loop_closure_result: str, go_action: str) -> bool:
    normalized_closure = loop_closure_result.strip().upper()
    normalized_action = go_action.strip().upper()
    if normalized_closure and normalized_closure != "UNKNOWN":
        return normalized_closure == "READY_TO_ESCALATE"
    return normalized_action == "GO"


def _sanitize_slug(value: str) -> str:
    collapsed = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
    return collapsed.lower() or "unknown"


def _build_record_filename(captured_at_utc: str, project_profile: str) -> str:
    stamp = captured_at_utc.replace("-", "").replace(":", "").replace(".", "")
    stamp = stamp.replace("+0000", "Z").replace("+00:00", "Z")
    stamp = stamp.replace("T", "T").replace("Z", "Z")
    return f"profile_outcome_{stamp}_{_sanitize_slug(project_profile)}.json"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture an additive advisory-only profile outcome record for offline "
            "profile ranking evidence."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--loop-closure-json", type=Path, default=DEFAULT_LOOP_CLOSURE_PATH)
    parser.add_argument("--startup-intake-json", type=Path, default=DEFAULT_STARTUP_INTAKE_PATH)
    parser.add_argument("--round-contract-md", type=Path, default=DEFAULT_ROUND_CONTRACT_PATH)
    parser.add_argument("--go-signal-md", type=Path, default=DEFAULT_GO_SIGNAL_PATH)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--captured-at-utc", type=str, default=None)
    parser.add_argument("--project-profile", type=str, default=None)
    parser.add_argument("--shipped", type=str, required=True, help="Operator-supplied shipped flag: true/false.")
    parser.add_argument(
        "--rollback-status",
        type=str,
        default="NO",
        help="Operator-supplied rollback status: NO, PARTIAL, or FULL.",
    )
    parser.add_argument(
        "--followup-changes-within-30d",
        type=_parse_non_negative_int,
        default=0,
        help="Number of follow-up changes attributed to this shipped wave within 30 days.",
    )
    parser.add_argument(
        "--semantic-issue-detected-after-merge",
        type=str,
        default="I don't know yet",
        help="Semantic issue status after merge: NONE, PRESENT, or 'I don't know yet'.",
    )
    parser.add_argument("--postmortem-score", type=float, default=None)
    parser.add_argument("--postmortem-note", "--postmortem", dest="postmortem_note", type=str, default="")
    parser.add_argument("--notes", type=str, default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    captured_at_utc = _parse_iso_utc(args.captured_at_utc)
    shipped = _parse_bool_text(args.shipped)
    rollback_status = _normalize_rollback_status(args.rollback_status)
    semantic_issue_detected_after_merge = _normalize_semantic_issue_status(
        args.semantic_issue_detected_after_merge
    )

    loop_closure_path = _resolve_path(repo_root, args.loop_closure_json)
    startup_intake_path = _resolve_path(repo_root, args.startup_intake_json)
    round_contract_path = _resolve_path(repo_root, args.round_contract_md)
    go_signal_path = _resolve_path(repo_root, args.go_signal_md)
    corpus_dir = _resolve_path(repo_root, args.corpus_dir)

    loop_closure = _load_json_safe(loop_closure_path)
    startup_intake = _load_json_safe(startup_intake_path)
    round_contract_text = _load_text_safe(round_contract_path)
    go_signal_text = _load_text_safe(go_signal_path)

    contract_fields = _parse_contract_fields(round_contract_text)
    project_profile = _infer_project_profile(
        startup_intake=startup_intake,
        contract_fields=contract_fields,
        explicit_project_profile=args.project_profile,
    )
    loop_closure_result = _infer_loop_closure_result(loop_closure)
    go_action = _extract_go_action(go_signal_text)
    ready = _infer_ready_flag(loop_closure_result, go_action)
    board_reentry_required = _infer_board_reentry_required(contract_fields)
    unknown_domain_triggered = _infer_unknown_domain_triggered(contract_fields)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "captured_at_utc": captured_at_utc,
        "advisory_only": True,
        "control_plane_impact": "none",
        "project_profile": project_profile,
        "loop_closure_result": loop_closure_result,
        "go_action": go_action,
        "ready": ready,
        "shipped": shipped,
        "rollback_status": rollback_status,
        "followup_changes_within_30d": args.followup_changes_within_30d,
        "semantic_issue_detected_after_merge": semantic_issue_detected_after_merge,
        "postmortem_score": args.postmortem_score,
        "postmortem_note": args.postmortem_note,
        "notes": args.notes,
        "board_reentry_required": board_reentry_required,
        "unknown_domain_triggered": unknown_domain_triggered,
        "artifact_context": {
            "loop_closure_path": str(loop_closure_path),
            "loop_closure_present": loop_closure is not None,
            "startup_intake_path": str(startup_intake_path),
            "startup_intake_present": startup_intake is not None,
            "round_contract_path": str(round_contract_path),
            "round_contract_present": bool(round_contract_text.strip()),
            "go_signal_path": str(go_signal_path),
            "go_signal_present": bool(go_signal_text.strip()),
        },
    }

    if args.output_json is not None:
        output_path = _resolve_path(repo_root, args.output_json)
    else:
        output_path = corpus_dir / _build_record_filename(captured_at_utc, project_profile)

    _atomic_write_json(output_path, payload)

    print("PROFILE_OUTCOME_CAPTURE_STATUS: WRITTEN")
    print(f"OUTPUT_PATH: {output_path}")
    print(f"PROJECT_PROFILE: {project_profile}")
    print(f"LOOP_CLOSURE_RESULT: {loop_closure_result}")
    print(f"GO_ACTION: {go_action}")
    print(f"SHIPPED: {str(shipped).upper()}")
    print(f"ROLLBACK_STATUS: {rollback_status}")
    print(f"FOLLOWUP_CHANGES_WITHIN_30D: {args.followup_changes_within_30d}")
    print(
        "SEMANTIC_ISSUE_DETECTED_AFTER_MERGE: "
        f"{semantic_issue_detected_after_merge}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
