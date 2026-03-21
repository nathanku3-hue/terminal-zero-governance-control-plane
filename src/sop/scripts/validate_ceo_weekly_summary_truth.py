from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from sop.scripts.ceo_go_signal_contract import (
        AUTOMATED_CRITERIA_KEYS,
        CRITERIA_ORDER,
        criterion_met,
        criterion_status_display,
        extract_infra_failures,
    )
except ModuleNotFoundError:
    # Fallback for direct script execution (development mode)
    try:
        from scripts.ceo_go_signal_contract import (
            AUTOMATED_CRITERIA_KEYS,
            CRITERIA_ORDER,
            criterion_met,
            criterion_status_display,
            extract_infra_failures,
        )
    except Exception:
        from ceo_go_signal_contract import (  # type: ignore[no-redef]
            AUTOMATED_CRITERIA_KEYS,
            CRITERIA_ORDER,
            criterion_met,
            criterion_status_display,
            extract_infra_failures,
        )


KNOWN_CRITERIA_CODES = tuple(short_code for short_code, _ in CRITERIA_ORDER)
CRITERION_CODE_PATTERN = "|".join(re.escape(code) for code in KNOWN_CRITERIA_CODES)
CRITERION_CODE_REGEX = re.compile(
    rf"\b(?P<code>{CRITERION_CODE_PATTERN})\b", re.IGNORECASE
)
CRITERION_PAIR_PATTERN = re.compile(
    rf"\b(?P<code>{CRITERION_CODE_PATTERN})\s*[:=]\s*(?P<status>MANUAL_CHECK|PASS|FAIL|TRUE|FALSE|✅|❌|⚠️?|⚠)\b",
    re.IGNORECASE,
)
CRITERION_LINE_PATTERN = re.compile(
    rf"^\s*(?:[-*]\s*)?(?:\*\*)?(?P<code>{CRITERION_CODE_PATTERN})(?:\*\*)?\s*(?:[:=\-]\s*|\s+)(?P<rest>.+?)\s*$",
    re.IGNORECASE,
)
STATUS_AT_START_PATTERN = re.compile(
    r"^\s*(?P<status>MANUAL_CHECK|PASS|FAIL|TRUE|FALSE|✅|❌|⚠️?|⚠)\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
ACTION_LINE_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?(?:Recommended Action|Recommendation|Program Status|RECOMMENDATION)\s*:\s*(?P<action>GO|HOLD|REFRAME)\s*$",
    re.IGNORECASE,
)
INTEGER_PATTERN = re.compile(r"-?\d+")
PERCENT_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")
VERSION_PATTERN = re.compile(r"\b\d+\.\d+\.\d+\b")

CRITERION_KEY_BY_CODE = dict(CRITERIA_ORDER)
CRITERION_CODE_BY_UPPER = {code.upper(): code for code in KNOWN_CRITERIA_CODES}


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
    criteria = payload.get("promotion_criteria")
    if isinstance(criteria, dict):
        return criteria
    return {}


def _strip_markdown(text: str) -> str:
    cleaned = text.replace("\\|", "|")
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"[*_~]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _canonical_code(raw: str) -> str | None:
    cleaned = _strip_markdown(raw)
    if not cleaned:
        return None
    upper = cleaned.upper()
    return CRITERION_CODE_BY_UPPER.get(upper)


def _normalize_status_token(raw: str) -> str | None:
    cleaned = _strip_markdown(raw)
    if not cleaned:
        return None

    upper = cleaned.upper()

    if "/" in upper and any(token in upper for token in ("PASS", "FAIL", "MANUAL_CHECK")):
        return None

    if "❌" in cleaned:
        return "FAIL"
    if "✅" in cleaned:
        return "PASS"
    if "⚠" in cleaned:
        return "MANUAL_CHECK"

    if re.search(r"\bMANUAL[\s_]?CHECK\b", upper):
        return "MANUAL_CHECK"

    if re.fullmatch(r"TRUE", upper):
        return "PASS"
    if re.fullmatch(r"FALSE", upper):
        return "FAIL"

    has_pass = bool(re.search(r"\bPASS\b", upper))
    has_fail = bool(re.search(r"\bFAIL\b", upper))
    if has_pass and not has_fail:
        return "PASS"
    if has_fail and not has_pass:
        return "FAIL"

    return None


def _split_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if not cells:
        return None
    if all(re.fullmatch(r"[-:\s]+", cell or "") for cell in cells):
        return None
    return cells


def _extract_status_and_value_from_text(text: str) -> tuple[str | None, str | None]:
    cleaned = _strip_markdown(text)
    match = STATUS_AT_START_PATTERN.match(cleaned)
    if not match:
        return None, None

    status = _normalize_status_token(match.group("status"))
    if status is None:
        return None, None

    remainder = match.group("rest").strip()
    remainder = re.sub(r"^[\s:|=\-]+", "", remainder)
    if remainder.startswith("(") and remainder.endswith(")"):
        remainder = remainder[1:-1].strip()
    value = remainder or None
    return status, value


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        match = INTEGER_PATTERN.search(value)
        if match:
            try:
                return int(match.group(0))
            except ValueError:
                return None
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _extract_first_int(text: str) -> int | None:
    match = INTEGER_PATTERN.search(text)
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None


def _extract_percent(text: str) -> float | None:
    match = PERCENT_PATTERN.search(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _extract_versions(text: str) -> set[str]:
    return set(VERSION_PATTERN.findall(text))


def _validate_dossier_structure(dossier: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    criteria = dossier.get("promotion_criteria")
    if not isinstance(criteria, dict):
        errors.append("Invalid dossier JSON: missing object field 'promotion_criteria'")
        return errors

    missing = [
        key for _, key in CRITERIA_ORDER if key not in criteria
    ]
    if missing:
        joined = ", ".join(missing)
        errors.append(
            "Invalid dossier JSON: promotion_criteria missing required keys: "
            f"{joined}"
        )
    return errors


def _parse_weekly_markdown(
    markdown: str,
) -> tuple[str | None, dict[str, str], dict[str, str], list[str], list[str]]:
    parse_errors: list[str] = []
    consistency_errors: list[str] = []

    observed_statuses: dict[str, set[str]] = {}
    observed_values: dict[str, list[str]] = {}
    observed_actions: set[str] = set()

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        action_match = ACTION_LINE_PATTERN.match(_strip_markdown(line))
        if action_match:
            observed_actions.add(action_match.group("action").upper())

        table_cells = _split_table_row(line)
        if table_cells is not None:
            code_match = CRITERION_CODE_REGEX.search(_strip_markdown(table_cells[0]))
            if code_match:
                code = _canonical_code(code_match.group("code"))
                if code is None:
                    continue

                status: str | None = None
                status_index: int | None = None
                for index, cell in enumerate(table_cells[1:], start=1):
                    candidate = _normalize_status_token(cell)
                    if candidate is None:
                        continue
                    status = candidate
                    status_index = index
                    break

                if status is not None:
                    observed_statuses.setdefault(code, set()).add(status)
                    if status_index is not None and status_index + 1 < len(table_cells):
                        value = _strip_markdown(table_cells[status_index + 1])
                        if value:
                            observed_values.setdefault(code, []).append(value)
                continue

        criterion_pairs = list(CRITERION_PAIR_PATTERN.finditer(line))
        if criterion_pairs:
            for pair in criterion_pairs:
                code = _canonical_code(pair.group("code"))
                status = _normalize_status_token(pair.group("status"))
                if code is None or status is None:
                    continue
                observed_statuses.setdefault(code, set()).add(status)
            continue

        criterion_line = CRITERION_LINE_PATTERN.match(line)
        if criterion_line:
            code = _canonical_code(criterion_line.group("code"))
            if code is None:
                continue
            status, value = _extract_status_and_value_from_text(criterion_line.group("rest"))
            if status is None:
                continue
            observed_statuses.setdefault(code, set()).add(status)
            if value:
                observed_values.setdefault(code, []).append(value)

    parsed_statuses: dict[str, str] = {}
    for code in KNOWN_CRITERIA_CODES:
        seen = sorted(observed_statuses.get(code, set()))
        if not seen:
            continue
        if len(seen) > 1:
            joined = ", ".join(seen)
            consistency_errors.append(
                f"Conflicting criterion {code} statuses found in markdown: {joined}"
            )
        parsed_statuses[code] = seen[0]

    missing_codes = [code for code in KNOWN_CRITERIA_CODES if code not in observed_statuses]
    if missing_codes:
        joined = ", ".join(missing_codes)
        parse_errors.append(
            "Invalid weekly summary markdown: missing criterion status entries for: "
            f"{joined}"
        )

    parsed_values: dict[str, str] = {}
    for code, values in observed_values.items():
        for value in values:
            if value:
                parsed_values[code] = value
                break

    action: str | None = None
    if len(observed_actions) == 1:
        action = next(iter(observed_actions))
    elif len(observed_actions) > 1:
        joined = ", ".join(sorted(observed_actions))
        consistency_errors.append(
            f"Conflicting recommended actions found in markdown: {joined}"
        )

    return action, parsed_statuses, parsed_values, parse_errors, consistency_errors


def _expected_action(dossier: dict[str, Any], calibration: dict[str, Any]) -> str:
    criteria = _promotion_criteria(dossier)
    calibration_criteria = _promotion_criteria(calibration)

    dossier_infra_failures = extract_infra_failures(dossier)
    calibration_infra_failures = extract_infra_failures(calibration)
    dossier_c0_met = criterion_met(criteria, "c0_infra_health")
    calibration_c0_met = criterion_met(calibration_criteria, "c0_infra_health")

    infra_signal = False
    if dossier_infra_failures is not None and dossier_infra_failures > 0:
        infra_signal = True
    if calibration_infra_failures is not None and calibration_infra_failures > 0:
        infra_signal = True
    if dossier_c0_met is False or calibration_c0_met is False:
        infra_signal = True

    automated_all_met = all(
        criterion_met(criteria, key) is True
        for key in AUTOMATED_CRITERIA_KEYS
    )

    if infra_signal:
        return "REFRAME"
    if automated_all_met:
        return "GO"
    return "HOLD"


def _expected_criterion_statuses(dossier: dict[str, Any]) -> dict[str, str]:
    criteria = _promotion_criteria(dossier)
    expected: dict[str, str] = {}
    for short_code, key in CRITERIA_ORDER:
        met_value = criterion_met(criteria, key)
        display = criterion_status_display(key, met_value)
        normalized = _normalize_status_token(str(display))
        expected[short_code] = normalized or str(display).strip().upper()
    return expected


def _value_truth_errors(
    dossier: dict[str, Any],
    calibration: dict[str, Any],
    actual_values: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    criteria = _promotion_criteria(dossier)

    totals = calibration.get("totals")
    if not isinstance(totals, dict):
        totals = {}
    fp_analysis = calibration.get("fp_analysis")
    if not isinstance(fp_analysis, dict):
        fp_analysis = {}

    expected_values: dict[str, str] = {}
    for short_code, key in CRITERIA_ORDER:
        raw = criteria.get(key)
        value = raw.get("value") if isinstance(raw, dict) else "N/A"
        expected_values[short_code] = str(value) if value is not None else "N/A"

    c0_actual = actual_values.get("C0")
    if c0_actual is not None:
        actual_failures = _extract_first_int(c0_actual)
        expected_failures = extract_infra_failures(calibration)
        if expected_failures is None:
            expected_failures = _extract_first_int(expected_values["C0"])
        if (
            expected_failures is not None
            and actual_failures is not None
            and actual_failures != expected_failures
        ):
            errors.append(
                "Criterion C0 value mismatch: "
                f"markdown={c0_actual}, expected failures={expected_failures}"
            )

    c1_actual = actual_values.get("C1")
    if c1_actual is not None:
        expected_c1 = _strip_markdown(expected_values["C1"]).upper()
        actual_c1 = _strip_markdown(c1_actual).upper()
        if actual_c1 != expected_c1:
            errors.append(
                "Criterion C1 value mismatch: "
                f"markdown={c1_actual}, expected={expected_values['C1']}"
            )

    c2_actual = actual_values.get("C2")
    if c2_actual is not None:
        expected_items = _to_int(totals.get("items_reviewed"))
        if expected_items is None:
            expected_items = _extract_first_int(expected_values["C2"])
        actual_items = _extract_first_int(c2_actual)
        if expected_items is not None and actual_items is not None and actual_items != expected_items:
            errors.append(
                "Criterion C2 value mismatch: "
                f"markdown={c2_actual}, expected items_reviewed={expected_items}"
            )

    c3_actual = actual_values.get("C3")
    if c3_actual is not None:
        expected_weeks = _extract_first_int(expected_values["C3"])
        actual_weeks = _extract_first_int(c3_actual)
        if expected_weeks is not None and actual_weeks is not None and actual_weeks != expected_weeks:
            errors.append(
                "Criterion C3 value mismatch: "
                f"markdown={c3_actual}, expected consecutive_weeks={expected_weeks}"
            )

    c4_actual = actual_values.get("C4")
    if c4_actual is not None:
        expected_fp_rate = _to_float(fp_analysis.get("fp_rate"))
        expected_pct = None if expected_fp_rate is None else expected_fp_rate * 100.0
        if expected_pct is None:
            expected_pct = _extract_percent(expected_values["C4"])
        actual_pct = _extract_percent(c4_actual)
        if (
            expected_pct is not None
            and actual_pct is not None
            and abs(actual_pct - expected_pct) > 0.05
        ):
            errors.append(
                "Criterion C4 value mismatch: "
                f"markdown={c4_actual}, expected fp_rate={expected_pct:.2f}%"
            )

    c4b_actual = actual_values.get("C4b")
    if c4b_actual is not None:
        expected_coverage = _to_float(fp_analysis.get("annotation_coverage_ch"))
        expected_pct = None if expected_coverage is None else expected_coverage * 100.0
        if expected_pct is None:
            expected_pct = _extract_percent(expected_values["C4b"])
        actual_pct = _extract_percent(c4b_actual)
        if (
            expected_pct is not None
            and actual_pct is not None
            and abs(actual_pct - expected_pct) > 0.05
        ):
            errors.append(
                "Criterion C4b value mismatch: "
                f"markdown={c4b_actual}, expected annotation_coverage={expected_pct:.2f}%"
            )

    c5_actual = actual_values.get("C5")
    if c5_actual is not None:
        expected_versions = _extract_versions(expected_values["C5"])
        actual_versions = _extract_versions(c5_actual)
        if expected_versions and actual_versions and actual_versions != expected_versions:
            errors.append(
                "Criterion C5 value mismatch: "
                f"markdown versions={sorted(actual_versions)}, "
                f"expected versions={sorted(expected_versions)}"
            )

    return errors


def _validate_truth(
    dossier: dict[str, Any],
    calibration: dict[str, Any],
    actual_action: str | None,
    actual_statuses: dict[str, str],
    actual_values: dict[str, str],
    consistency_errors: list[str],
) -> list[str]:
    errors = list(consistency_errors)

    expected_action = _expected_action(dossier, calibration)
    if actual_action is None:
        errors.append(
            "Missing Recommended Action line in weekly summary markdown: "
            "expected one of GO, HOLD, or REFRAME."
        )
    elif actual_action != expected_action:
        errors.append(
            "Recommended Action mismatch: "
            f"markdown={actual_action}, expected={expected_action}"
        )

    expected_statuses = _expected_criterion_statuses(dossier)
    for code in KNOWN_CRITERIA_CODES:
        expected_status = expected_statuses.get(code)
        actual_status = actual_statuses.get(code)
        if expected_status is None:
            errors.append(f"Dossier missing expected status for criterion: {code}")
            continue
        if actual_status is None:
            errors.append(f"Missing criterion status in markdown: {code}")
            continue
        if actual_status != expected_status:
            errors.append(
                f"Criterion {code} status mismatch: "
                f"markdown={actual_status}, expected={expected_status}"
            )

    errors.extend(_value_truth_errors(dossier, calibration, actual_values))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that ceo_weekly_summary markdown truthfully reflects "
            "dossier/calibration facts. Exit 0=pass, 1=truth mismatch, 2=input/format error."
        )
    )
    parser.add_argument("--weekly-md", required=True, help="Path to CEO weekly summary markdown")
    parser.add_argument("--dossier-json", required=True, help="Path to promotion dossier JSON")
    parser.add_argument(
        "--calibration-json",
        required=True,
        help="Path to auditor calibration report JSON",
    )
    args = parser.parse_args()

    weekly_path = Path(args.weekly_md)
    dossier_path = Path(args.dossier_json)
    calibration_path = Path(args.calibration_json)

    infra_errors: list[str] = []

    dossier, dossier_error = _read_json_object(dossier_path)
    if dossier_error:
        infra_errors.append(dossier_error)

    calibration, calibration_error = _read_json_object(calibration_path)
    if calibration_error:
        infra_errors.append(calibration_error)

    markdown, markdown_error = _read_markdown(weekly_path)
    if markdown_error:
        infra_errors.append(markdown_error)

    if dossier is not None:
        infra_errors.extend(_validate_dossier_structure(dossier))

    parsed_action: str | None = None
    parsed_statuses: dict[str, str] = {}
    parsed_values: dict[str, str] = {}
    consistency_errors: list[str] = []

    if markdown is not None:
        (
            parsed_action,
            parsed_statuses,
            parsed_values,
            markdown_parse_errors,
            markdown_consistency_errors,
        ) = _parse_weekly_markdown(markdown)
        infra_errors.extend(markdown_parse_errors)
        consistency_errors.extend(markdown_consistency_errors)

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
        actual_values=parsed_values,
        consistency_errors=consistency_errors,
    )
    if truth_errors:
        for error in truth_errors:
            print(f"[ERROR] {error}")
        return 1

    print("[OK] CEO weekly-summary truth-check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
