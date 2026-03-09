from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CRITERIA_ORDER = [
    ("C0", "c0_infra_health"),
    ("C1", "c1_24b_close"),
    ("C2", "c2_min_items"),
    ("C3", "c3_min_weeks"),
    ("C4", "c4_fp_rate"),
    ("C4b", "c4b_annotation_coverage"),
    ("C5", "c5_all_v2"),
]

AUTOMATED_CRITERIA_KEYS = (
    "c0_infra_health",
    "c2_min_items",
    "c3_min_weeks",
    "c4_fp_rate",
    "c4b_annotation_coverage",
    "c5_all_v2",
)

__all__ = [
    "AUTOMATED_CRITERIA_KEYS",
    "CRITERIA_ORDER",
    "criterion_met",
    "criterion_status_display",
    "criterion_value",
    "detect_phase",
    "extract_infra_failures",
    "load_json_fail_open",
    "promotion_criteria",
    "determine_recommended_action",
    "to_int",
]


def load_json_fail_open(path: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if not path.exists():
        warnings.append(f"Missing input file: {path}")
        return {}, warnings
    try:
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
        if not isinstance(data, dict):
            warnings.append(f"Input is not a JSON object: {path}")
            return {}, warnings
        return data, warnings
    except Exception as exc:
        warnings.append(f"Failed to parse JSON {path}: {exc}")
        return {}, warnings


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+", value)
        if match:
            try:
                return int(match.group(0))
            except ValueError:
                return None
    return None


def to_int(value: Any) -> int | None:
    return _to_int(value)


def extract_infra_failures(report: dict[str, Any]) -> int | None:
    direct = _to_int(report.get("infra_failures"))
    if direct is not None:
        return direct

    criteria = report.get("promotion_criteria")
    if isinstance(criteria, dict):
        c0 = criteria.get("c0_infra_health")
        if isinstance(c0, dict):
            value = _to_int(c0.get("value"))
            if value is not None:
                return value
    return None


def criterion_met(criteria: dict[str, Any], key: str) -> Any:
    item = criteria.get(key)
    if isinstance(item, dict):
        return item.get("met")
    return None


def criterion_value(criteria: dict[str, Any], key: str) -> str:
    item = criteria.get(key)
    if isinstance(item, dict):
        value = item.get("value")
        if value is None:
            return "N/A"
        return str(value)
    return "N/A"


def criterion_status_display(key: str, met_value: Any) -> str:
    if key == "c1_24b_close":
        return "MANUAL_CHECK"
    if met_value is True:
        return "PASS"
    if met_value is False:
        return "FAIL"
    if isinstance(met_value, str):
        return met_value
    return "N/A"


def detect_phase(
    dossier: dict[str, Any],
    calibration: dict[str, Any],
    context: dict[str, Any],
    phase_arg: str,
) -> str:
    candidates: list[Any] = [
        phase_arg,
        dossier.get("phase"),
        dossier.get("phase_id"),
        dossier.get("phase_name"),
        calibration.get("phase"),
        calibration.get("phase_id"),
        calibration.get("phase_name"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    active_phase = context.get("active_phase")
    if isinstance(active_phase, int):
        return f"Phase {active_phase}"
    if isinstance(active_phase, str) and active_phase.strip():
        return f"Phase {active_phase.strip()}"
    return "UNKNOWN"


def promotion_criteria(payload: dict[str, Any]) -> dict[str, Any]:
    criteria = payload.get("promotion_criteria")
    if isinstance(criteria, dict):
        return criteria
    return {}


def determine_recommended_action(dossier: dict[str, Any], calibration: dict[str, Any]) -> str:
    criteria = promotion_criteria(dossier)
    calibration_criteria = promotion_criteria(calibration)

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
        criterion_met(criteria, key) is True for key in AUTOMATED_CRITERIA_KEYS
    )

    if infra_signal:
        return "REFRAME"
    if automated_all_met:
        return "GO"
    return "HOLD"
