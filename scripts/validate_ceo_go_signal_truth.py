from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from scripts import ceo_go_signal_contract as go_signal_contract
except Exception:
    import ceo_go_signal_contract as go_signal_contract  # type: ignore[no-redef]


KNOWN_CRITERIA_CODES = tuple(
    short_code for short_code, _ in go_signal_contract.CRITERIA_ORDER
)
CRITERION_CODE_PATTERN = "|".join(re.escape(code) for code in KNOWN_CRITERIA_CODES)
RECOMMENDED_ACTION_PATTERN = re.compile(
    r"^\s*-\s*Recommended Action:\s*(?P<action>[A-Za-z_]+)\s*$",
    re.MULTILINE,
)
CRITERION_ROW_PATTERN = re.compile(
    rf"^\|\s*(?P<code>{CRITERION_CODE_PATTERN})\s*\|\s*(?P<status>[^|]+?)\s*\|"
)


def _read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, f"Missing input file: {path}"
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"Failed to read JSON file {path}: {exc}"

    try:
        data = json.loads(raw)
    except Exception as exc:
        return None, f"Invalid JSON in {path}: {exc}"

    if not isinstance(data, dict):
        return None, f"JSON root must be an object: {path}"
    return data, None


def _read_markdown(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, f"Missing input file: {path}"
    try:
        content = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"Failed to read markdown file {path}: {exc}"
    return content, None


def _promotion_criteria(payload: dict[str, Any]) -> dict[str, Any]:
    return go_signal_contract.promotion_criteria(payload)


def _extract_dossier_criteria_section(markdown: str) -> list[str] | None:
    lines = markdown.splitlines()
    start_index: int | None = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Dossier Criteria":
            start_index = idx + 1
            break

    if start_index is None:
        return None

    section_lines: list[str] = []
    for line in lines[start_index:]:
        if line.strip().startswith("## "):
            break
        section_lines.append(line)
    return section_lines


def _parse_go_signal_markdown(markdown: str) -> tuple[str | None, dict[str, str], list[str]]:
    errors: list[str] = []

    action_match = RECOMMENDED_ACTION_PATTERN.search(markdown)
    action = action_match.group("action").strip().upper() if action_match else None
    if action is None:
        errors.append("Invalid go-signal markdown: missing '- Recommended Action:' line")

    section = _extract_dossier_criteria_section(markdown)
    statuses: dict[str, str] = {}
    duplicates: set[str] = set()
    if section is None:
        errors.append("Invalid go-signal markdown: missing '## Dossier Criteria' section")
        return action, statuses, errors

    for raw_line in section:
        line = raw_line.strip()
        match = CRITERION_ROW_PATTERN.match(line)
        if not match:
            continue
        code = match.group("code").strip()
        status = match.group("status").strip()
        if code in statuses:
            duplicates.add(code)
        statuses[code] = status

    if duplicates:
        joined = ", ".join(sorted(duplicates))
        errors.append(f"Invalid go-signal markdown: duplicate criterion rows ({joined})")

    return action, statuses, errors


def _expected_action(dossier: dict[str, Any], calibration: dict[str, Any]) -> str:
    return go_signal_contract.determine_recommended_action(dossier=dossier, calibration=calibration)


def _expected_criterion_statuses(dossier: dict[str, Any]) -> dict[str, str]:
    criteria = _promotion_criteria(dossier)
    expected: dict[str, str] = {}
    for short_code, key in go_signal_contract.CRITERIA_ORDER:
        if key not in criteria:
            continue
        met_value = go_signal_contract.criterion_met(criteria, key)
        expected[short_code] = go_signal_contract.criterion_status_display(key, met_value)
    return expected


def _validate_truth(
    dossier: dict[str, Any],
    calibration: dict[str, Any],
    actual_action: str | None,
    actual_statuses: dict[str, str],
) -> list[str]:
    errors: list[str] = []

    expected_action = _expected_action(dossier, calibration)
    if actual_action != expected_action:
        errors.append(
            "Recommended Action mismatch: "
            f"markdown={actual_action or 'N/A'}, expected={expected_action}"
        )

    expected_statuses = _expected_criterion_statuses(dossier)

    for code, expected_status in expected_statuses.items():
        actual_status = actual_statuses.get(code)
        if actual_status is None:
            errors.append(f"Missing criterion row in markdown table: {code}")
            continue
        if actual_status != expected_status:
            errors.append(
                f"Criterion {code} status mismatch: "
                f"markdown={actual_status}, expected={expected_status}"
            )

    unexpected_codes = sorted(set(actual_statuses) - set(expected_statuses))
    for code in unexpected_codes:
        errors.append(
            "Unexpected criterion row in markdown table not present in dossier criteria: "
            f"{code}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that ceo_go_signal.md truthfully reflects dossier/calibration facts. "
            "Exit 0=pass, 1=truth mismatch, 2=input/format error."
        )
    )
    parser.add_argument("--dossier-json", required=True, help="Path to promotion dossier JSON")
    parser.add_argument(
        "--calibration-json",
        required=True,
        help="Path to auditor calibration report JSON",
    )
    parser.add_argument("--go-signal-md", required=True, help="Path to CEO go-signal markdown")
    args = parser.parse_args()

    dossier_path = Path(args.dossier_json)
    calibration_path = Path(args.calibration_json)
    go_signal_path = Path(args.go_signal_md)

    infra_errors: list[str] = []

    dossier, dossier_error = _read_json_object(dossier_path)
    if dossier_error:
        infra_errors.append(dossier_error)

    calibration, calibration_error = _read_json_object(calibration_path)
    if calibration_error:
        infra_errors.append(calibration_error)

    markdown, markdown_error = _read_markdown(go_signal_path)
    if markdown_error:
        infra_errors.append(markdown_error)

    parsed_action: str | None = None
    parsed_statuses: dict[str, str] = {}
    if markdown is not None:
        parsed_action, parsed_statuses, markdown_parse_errors = _parse_go_signal_markdown(
            markdown
        )
        infra_errors.extend(markdown_parse_errors)

    if infra_errors:
        for error in infra_errors:
            print(f"[ERROR] {error}")
        return 2

    if dossier is None or calibration is None:
        print("[ERROR] Internal validation failure while loading inputs.")
        return 2

    truth_errors = _validate_truth(
        dossier=dossier,
        calibration=calibration,
        actual_action=parsed_action,
        actual_statuses=parsed_statuses,
    )
    if truth_errors:
        for error in truth_errors:
            print(f"[ERROR] {error}")
        return 1

    print("[OK] CEO go-signal truth-check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
