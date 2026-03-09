from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


NEXT_ROUND_HANDOFF_PATH = "docs/context/next_round_handoff_latest.md"
EXPERT_REQUEST_PATH = "docs/context/expert_request_latest.md"
PM_CEO_RESEARCH_BRIEF_PATH = "docs/context/pm_ceo_research_brief_latest.md"
BOARD_DECISION_BRIEF_PATH = "docs/context/board_decision_brief_latest.md"

ROOT_CONVENIENCE_MIRRORS = [
    "NEXT_ROUND_HANDOFF_LATEST.md",
    "EXPERT_REQUEST_LATEST.md",
    "PM_CEO_RESEARCH_BRIEF_LATEST.md",
    "BOARD_DECISION_BRIEF_LATEST.md",
]

ARTIFACT_PATHS = [
    "docs/context/ceo_weekly_summary_latest.md",
    "docs/context/ceo_go_signal.md",
    "docs/context/exec_memory_packet_latest.json",
    "docs/context/loop_cycle_summary_latest.json",
    "docs/context/loop_closure_status_latest.json",
    EXPERT_REQUEST_PATH,
    PM_CEO_RESEARCH_BRIEF_PATH,
    BOARD_DECISION_BRIEF_PATH,
]

ADVISORY_HANDOFFS: list[tuple[str, str]] = [
    ("advisory_next_round_handoff", NEXT_ROUND_HANDOFF_PATH),
    ("advisory_expert_request", EXPERT_REQUEST_PATH),
    ("advisory_pm_ceo_research_brief", PM_CEO_RESEARCH_BRIEF_PATH),
    ("advisory_board_decision_brief", BOARD_DECISION_BRIEF_PATH),
]

MACHINE_VIEW_MARKERS: dict[str, tuple[str, ...]] = {
    "advisory_expert_request": (
        "REQUESTED_DOMAIN",
        "ROSTER_FIT",
        "MILESTONE_ID",
        "BOARD_REENTRY_REQUIRED",
        "BOARD_REENTRY_REASON_CODES",
        "EXPERT_MEMORY_STATUS",
        "BOARD_MEMORY_STATUS",
        "MEMORY_REASON_CODES",
    ),
    "advisory_board_decision_brief": (
        "LINEUP_DECISION_NEEDED",
        "LINEUP_GAP_DOMAINS",
        "APPROVED_ROSTER_SNAPSHOT",
        "REINTRODUCE_BOARD_WHEN",
        "BOARD_REENTRY_REQUIRED",
        "BOARD_REENTRY_REASON_CODES",
        "EXPERT_MEMORY_STATUS",
        "BOARD_MEMORY_STATUS",
        "MEMORY_REASON_CODES",
    ),
}

SECTION_MARKER_FALLBACKS: dict[str, dict[str, dict[str, str]]] = {
    "advisory_expert_request": {
        "## Lineup": {
            "RequestedDomain": "REQUESTED_DOMAIN",
            "RosterFit": "ROSTER_FIT",
            "MilestoneId": "MILESTONE_ID",
            "BoardReentryRequired": "BOARD_REENTRY_REQUIRED",
            "BoardReentryReasonCodes": "BOARD_REENTRY_REASON_CODES",
        },
        "## Memory": {
            "ExpertMemoryStatus": "EXPERT_MEMORY_STATUS",
            "BoardMemoryStatus": "BOARD_MEMORY_STATUS",
            "MemoryReasonCodes": "MEMORY_REASON_CODES",
        },
    },
    "advisory_board_decision_brief": {
        "## Lineup": {
            "LineupDecisionNeeded": "LINEUP_DECISION_NEEDED",
            "LineupGapDomains": "LINEUP_GAP_DOMAINS",
            "ApprovedRosterSnapshot": "APPROVED_ROSTER_SNAPSHOT",
            "ReintroduceBoardWhen": "REINTRODUCE_BOARD_WHEN",
            "BoardReentryRequired": "BOARD_REENTRY_REQUIRED",
            "BoardReentryReasonCodes": "BOARD_REENTRY_REASON_CODES",
        },
        "## Memory": {
            "ExpertMemoryStatus": "EXPERT_MEMORY_STATUS",
            "BoardMemoryStatus": "BOARD_MEMORY_STATUS",
            "MemoryReasonCodes": "MEMORY_REASON_CODES",
        },
    },
}


def _load_closure_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing closure status file: {path}")
    raw = path.read_text(encoding="utf-8-sig")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Closure status JSON root must be an object.")
    return payload


def _extract_startup_gate_status(payload: dict[str, Any]) -> str | None:
    checks = payload.get("checks")
    if not isinstance(checks, list):
        return None
    for check in checks:
        if not isinstance(check, dict):
            continue
        if check.get("name") != "startup_gate_status":
            continue
        status = check.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip()
        return None
    return None


def _result_to_exit_code(result: str) -> int:
    normalized = result.strip().upper()
    if normalized == "READY_TO_ESCALATE":
        return 0
    if normalized == "NOT_READY":
        return 1
    return 2


def _load_optional_handoff(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8-sig")
    stripped = raw.strip()
    if not stripped:
        return None
    return stripped


def _extract_markdown_section(markdown: str, heading: str) -> str | None:
    lines = markdown.splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            collecting = True
            continue
        if collecting and stripped.startswith("#"):
            break
        if collecting:
            collected.append(line)
    section = "\n".join(collected).strip()
    return section or None


def _extract_fenced_block(markdown: str, *headings: str) -> str | None:
    section: str | None = None
    for heading in headings:
        section = _extract_markdown_section(markdown, heading)
        if section is not None:
            break
    if section is None:
        return None

    lines = section.splitlines()
    in_fence = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```"):
                in_fence = True
            continue
        if stripped == "```":
            break
        collected.append(line)

    fenced_block = "\n".join(collected).strip()
    return fenced_block or None


def _extract_paste_ready_block(markdown: str) -> str | None:
    return _extract_fenced_block(markdown, "### Paste-Ready Block", "## Paste-Ready Block")


def _extract_machine_view_block(markdown: str) -> str | None:
    return _extract_fenced_block(markdown, "### Machine View", "## Machine View")


def _extract_human_brief(markdown: str) -> str | None:
    section = _extract_markdown_section(markdown, "### Human Brief")
    if section is None:
        section = _extract_markdown_section(markdown, "## Human Brief")
    if section is None:
        return None
    return " ".join(section.split()) or None


def _normalize_marker_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _extract_section_markers(markdown: str, heading: str, key_map: dict[str, str]) -> dict[str, str]:
    section = _extract_markdown_section(markdown, heading)
    if section is None:
        return {}

    normalized_key_map = {
        _normalize_marker_key(source_key): marker_name
        for source_key, marker_name in key_map.items()
    }
    markers: dict[str, str] = {}
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        item = stripped[1:].strip()
        key, separator, value = item.partition(":")
        if not separator:
            continue
        marker_name = normalized_key_map.get(_normalize_marker_key(key))
        marker_value = value.strip()
        if marker_name and marker_value:
            markers[marker_name] = marker_value
    return markers


def _extract_machine_view_markers(markdown: str, label: str) -> dict[str, str]:
    machine_view = _extract_machine_view_block(markdown)
    markers: dict[str, str] = {}
    if machine_view is not None:
        for line in machine_view.splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                continue
            normalized_key = key.strip().upper()
            normalized_value = value.strip()
            if normalized_key and normalized_value:
                markers[normalized_key] = normalized_value

    for heading, key_map in SECTION_MARKER_FALLBACKS.get(label, {}).items():
        fallback_markers = _extract_section_markers(markdown, heading, key_map)
        for marker_name, marker_value in fallback_markers.items():
            markers.setdefault(marker_name, marker_value)
    return markers


def _print_optional_advisory(repo_root: Path, label: str, relative_path: str) -> None:
    advisory_path = repo_root / Path(relative_path)
    try:
        advisory_text = _load_optional_handoff(advisory_path)
    except OSError as exc:
        print(f"WARNING: Unable to read {relative_path}: {exc}", file=sys.stderr)
        return
    if advisory_text is None:
        return
    print(f"{label}: present")
    print(f"{label}_path: {relative_path}")
    human_brief = _extract_human_brief(advisory_text)
    if human_brief is not None:
        print(f"{label}_summary: {human_brief}")
    machine_view_markers = _extract_machine_view_markers(advisory_text, label)
    for marker_name in MACHINE_VIEW_MARKERS.get(label, ()):
        marker_value = machine_view_markers.get(marker_name)
        if marker_value is not None:
            print(f"{label}_{marker_name.lower()}: {marker_value}")
    paste_ready_block = _extract_paste_ready_block(advisory_text)
    if paste_ready_block is not None:
        print(f"{label}_paste_ready_begin")
        print(paste_ready_block)
        print(f"{label}_paste_ready_end")
    print(f"{label}_begin")
    print(advisory_text)
    print(f"{label}_end")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print deterministic PM/CEO takeover entrypoint artifacts from loop closure status."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    closure_path = repo_root / "docs" / "context" / "loop_closure_status_latest.json"

    try:
        payload = _load_closure_payload(closure_path)
    except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result_raw = payload.get("result")
    if not isinstance(result_raw, str) or not result_raw.strip():
        print("ERROR: Missing or invalid closure result.", file=sys.stderr)
        return 2
    result = result_raw.strip()

    print(f"closure_result: {result}")
    startup_gate_status = _extract_startup_gate_status(payload)
    if startup_gate_status is not None:
        print(f"startup_gate_status: {startup_gate_status}")

    for label, relative_path in ADVISORY_HANDOFFS:
        _print_optional_advisory(repo_root, label, relative_path)

    print("root_convenience_mirrors:")
    for mirror in ROOT_CONVENIENCE_MIRRORS:
        print(f"- {mirror}")

    print("artifacts:")
    for artifact in ARTIFACT_PATHS:
        print(f"- {artifact}")

    return _result_to_exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
