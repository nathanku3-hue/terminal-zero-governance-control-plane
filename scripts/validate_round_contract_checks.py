from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


KEY_VALUE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")


def _read_text(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, f"Missing input file: {path}"
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except Exception as exc:
        return None, f"Failed to read file {path}: {exc}"


def _read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    raw, read_error = _read_text(path)
    if read_error:
        return None, read_error
    try:
        payload = json.loads(raw or "")
    except Exception as exc:
        return None, f"Invalid JSON in {path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"JSON root must be an object: {path}"
    return payload, None


def _parse_markdown_fields(markdown: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in markdown.splitlines():
        match = KEY_VALUE_PATTERN.match(line)
        if match is None:
            continue
        key = match.group(1).strip().upper()
        value = match.group(2).strip()
        if key:
            fields[key] = value
    return fields


def _parse_checks(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _is_meaningful_value(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    lowered = text.lower()
    if lowered in {"n/a", "na", "none", "null", "todo", "tbd"}:
        return False
    if lowered.startswith("todo(") or lowered.startswith("todo:"):
        return False
    return True


def _extract_int_from_change_budget(raw_budget: str, pattern: str) -> int | None:
    match = re.search(pattern, raw_budget)
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _is_large_change_scope(fields: dict[str, str]) -> bool:
    decision_class = fields.get("DECISION_CLASS", "").strip().upper()
    if decision_class == "ONE_WAY":
        return True

    risk_tier = fields.get("RISK_TIER", "").strip().upper()
    if risk_tier == "HIGH":
        return True

    raw_budget = fields.get("CHANGE_BUDGET", "").strip().lower()
    if not raw_budget:
        return False

    architecture_changes = _extract_int_from_change_budget(
        raw_budget,
        r"(\d+)\s+architecture\s+changes?",
    )
    if architecture_changes is not None and architecture_changes > 0:
        return True

    file_count = _extract_int_from_change_budget(raw_budget, r"(\d+)\s+files?")
    if file_count is not None and file_count > 2:
        return True

    if any(keyword in raw_budget for keyword in ("large", "major", "cross-module")):
        return True

    return False


def _validate_large_change_boundary_fields(fields: dict[str, str]) -> list[str]:
    if not _is_large_change_scope(fields):
        return []

    required_fields = (
        "LOGIC_SPINE_INDEX_ARTIFACT",
        "CHANGE_MANIFEST_ARTIFACT",
        "ALLOWED_BOUNDARY_REFS",
        "NON_GOAL_REFS",
    )
    errors: list[str] = []
    for field_name in required_fields:
        value = fields.get(field_name)
        if not _is_meaningful_value(value):
            errors.append(
                (
                    "Large-change scope requires "
                    f"{field_name} to be present and non-placeholder."
                )
            )
    return errors


def _collect_available_checks(
    loop_summary: dict[str, Any],
    closure: dict[str, Any],
) -> tuple[set[str], str | None]:
    available: set[str] = set()

    steps = loop_summary.get("steps")
    if not isinstance(steps, list):
        return set(), "Invalid loop summary JSON: 'steps' must be a list"
    for step in steps:
        if not isinstance(step, dict):
            continue
        name = step.get("name")
        if isinstance(name, str) and name.strip():
            available.add(name.strip())

    checks = closure.get("checks")
    if not isinstance(checks, list):
        return set(), "Invalid closure JSON: 'checks' must be a list"
    for check in checks:
        if not isinstance(check, dict):
            continue
        name = check.get("name")
        if isinstance(name, str) and name.strip():
            available.add(name.strip())

    return available, None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate DONE_WHEN_CHECKS in round contract against loop and closure check IDs. "
            "Exit 0=pass, 1=validation fail, 2=infra/input error."
        )
    )
    parser.add_argument(
        "--round-contract-md",
        default="docs/context/round_contract_latest.md",
        help="Round contract markdown path.",
    )
    parser.add_argument(
        "--loop-summary-json",
        default="docs/context/loop_cycle_summary_latest.json",
        help="Loop cycle summary JSON path.",
    )
    parser.add_argument(
        "--closure-json",
        default="docs/context/loop_closure_status_latest.json",
        help="Loop closure status JSON path.",
    )
    args = parser.parse_args()

    round_contract_path = Path(args.round_contract_md)
    loop_summary_path = Path(args.loop_summary_json)
    closure_path = Path(args.closure_json)

    markdown, markdown_error = _read_text(round_contract_path)
    if markdown_error:
        print(f"[ERROR] {markdown_error}")
        return 2

    loop_summary, loop_error = _read_json_object(loop_summary_path)
    if loop_error:
        print(f"[ERROR] {loop_error}")
        return 2

    closure, closure_error = _read_json_object(closure_path)
    if closure_error:
        print(f"[ERROR] {closure_error}")
        return 2

    fields = _parse_markdown_fields(markdown or "")
    raw_checks = fields.get("DONE_WHEN_CHECKS", "")
    check_ids = _parse_checks(raw_checks)
    if not check_ids:
        print("[ERROR] DONE_WHEN_CHECKS must declare a non-empty check list.")
        return 1

    large_change_errors = _validate_large_change_boundary_fields(fields)
    if large_change_errors:
        for error in large_change_errors:
            print(f"[ERROR] {error}")
        return 1

    available_ids, availability_error = _collect_available_checks(loop_summary or {}, closure or {})
    if availability_error:
        print(f"[ERROR] {availability_error}")
        return 2

    unknown_ids: list[str] = []
    seen: set[str] = set()
    for check_id in check_ids:
        if check_id in available_ids:
            continue
        if check_id in seen:
            continue
        seen.add(check_id)
        unknown_ids.append(check_id)

    if unknown_ids:
        print(f"[ERROR] Unknown DONE_WHEN_CHECKS ids: {', '.join(unknown_ids)}")
        return 1

    print("[OK] DONE_WHEN_CHECKS validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
