from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from datetime import timezone
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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _load_json_fail_open(path: Path) -> tuple[dict[str, Any], list[str]]:
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


def _extract_infra_failures(report: dict[str, Any]) -> int | None:
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


def _criterion_met(criteria: dict[str, Any], key: str) -> Any:
    item = criteria.get(key)
    if isinstance(item, dict):
        return item.get("met")
    return None


def _criterion_value(criteria: dict[str, Any], key: str) -> str:
    item = criteria.get(key)
    if isinstance(item, dict):
        value = item.get("value")
        if value is None:
            return "N/A"
        return str(value)
    return "N/A"


def _criterion_status_display(key: str, met_value: Any) -> str:
    if key == "c1_24b_close":
        return "MANUAL_CHECK"
    if met_value is True:
        return "PASS"
    if met_value is False:
        return "FAIL"
    if isinstance(met_value, str):
        return met_value
    return "N/A"


def _detect_phase(
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


def _build_markdown(
    phase: str,
    generated_at: str,
    action: str,
    criteria: dict[str, Any],
    blocking_reasons: list[str],
    next_steps: list[str],
    calibration_path: Path,
    dossier_path: Path,
    output_path: Path,
) -> str:
    lines = [
        "# CEO GO Signal",
        "",
        f"- Phase: {phase}",
        f"- Generated: {generated_at}",
        f"- Recommended Action: {action}",
        "",
        "## Dossier Criteria",
        "",
        "| Criterion | Status | Value |",
        "|---|---|---|",
    ]

    for short_code, key in CRITERIA_ORDER:
        if key not in criteria:
            continue
        met_value = _criterion_met(criteria, key)
        status = _criterion_status_display(key, met_value)
        value = _criterion_value(criteria, key).replace("|", "\\|")
        lines.append(f"| {short_code} | {status} | {value} |")

    if len(lines) > 0 and lines[-1] == "|---|---|---|":
        lines.append("| (no criteria found) | N/A | Dossier missing `promotion_criteria` |")

    lines.extend(
        [
            "",
            "## Blocking Reasons",
            "",
        ]
    )
    if blocking_reasons:
        for reason in blocking_reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Next Steps",
            "",
        ]
    )
    for index, step in enumerate(next_steps, start=1):
        lines.append(f"{index}. {step}")

    lines.extend(
        [
            "",
            "## Artifact Links",
            "",
            f"- Dossier JSON: `{dossier_path}`",
            f"- Calibration JSON: `{calibration_path}`",
            f"- Signal Markdown: `{output_path}`",
        ]
    )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate concise CEO GO/HOLD/REFRAME signal from calibration artifacts."
    )
    parser.add_argument(
        "--calibration-json",
        default="docs/context/auditor_calibration_report.json",
        help="Path to auditor calibration report JSON.",
    )
    parser.add_argument(
        "--dossier-json",
        default="docs/context/auditor_promotion_dossier.json",
        help="Path to auditor promotion dossier JSON.",
    )
    parser.add_argument(
        "--output",
        default="docs/context/ceo_go_signal.md",
        help="Output markdown path.",
    )
    parser.add_argument(
        "--context-json",
        default="docs/context/current_context.json",
        help="Optional context artifact path used for phase fallback.",
    )
    parser.add_argument(
        "--phase",
        default="",
        help="Optional phase label override for output header.",
    )
    args = parser.parse_args()

    calibration_path = Path(args.calibration_json)
    dossier_path = Path(args.dossier_json)
    context_path = Path(args.context_json)
    output_path = Path(args.output)

    calibration, calibration_warnings = _load_json_fail_open(calibration_path)
    dossier, dossier_warnings = _load_json_fail_open(dossier_path)
    context, _ = _load_json_fail_open(context_path)
    warnings = calibration_warnings + dossier_warnings

    dossier_criteria_obj = dossier.get("promotion_criteria")
    criteria: dict[str, Any] = (
        dossier_criteria_obj if isinstance(dossier_criteria_obj, dict) else {}
    )
    calibration_criteria_obj = calibration.get("promotion_criteria")
    calibration_criteria: dict[str, Any] = (
        calibration_criteria_obj if isinstance(calibration_criteria_obj, dict) else {}
    )

    dossier_infra_failures = _extract_infra_failures(dossier)
    calibration_infra_failures = _extract_infra_failures(calibration)
    dossier_c0_met = _criterion_met(criteria, "c0_infra_health")
    calibration_c0_met = _criterion_met(calibration_criteria, "c0_infra_health")

    infra_signal = False
    if dossier_infra_failures is not None and dossier_infra_failures > 0:
        infra_signal = True
    if calibration_infra_failures is not None and calibration_infra_failures > 0:
        infra_signal = True
    if dossier_c0_met is False or calibration_c0_met is False:
        infra_signal = True

    automated_all_met = all(
        _criterion_met(criteria, key) is True for key in AUTOMATED_CRITERIA_KEYS
    )

    if infra_signal:
        action = "REFRAME"
    elif automated_all_met:
        action = "GO"
    else:
        action = "HOLD"

    blocking_reasons: list[str] = []
    blocking_reasons.extend(warnings)

    if infra_signal:
        reasons: list[str] = []
        if dossier_infra_failures is not None:
            reasons.append(f"dossier infra_failures={dossier_infra_failures}")
        if calibration_infra_failures is not None:
            reasons.append(f"calibration infra_failures={calibration_infra_failures}")
        if dossier_c0_met is False:
            reasons.append("C0 marked not met in dossier")
        if calibration_c0_met is False:
            reasons.append("C0 marked not met in calibration")
        detail = "; ".join(reasons) if reasons else "infra failure signal detected"
        blocking_reasons.append(f"Infra failure signal detected: {detail}.")

    unmet_automated: list[str] = []
    for short_code, key in CRITERIA_ORDER:
        if key not in AUTOMATED_CRITERIA_KEYS:
            continue
        met_value = _criterion_met(criteria, key)
        if met_value is not True:
            if key in criteria:
                value = _criterion_value(criteria, key)
                unmet_automated.append(f"{short_code} not met ({value}).")
            else:
                unmet_automated.append(f"{short_code} missing in dossier criteria.")

    if action in ("HOLD", "REFRAME"):
        blocking_reasons.extend(unmet_automated)

    phase = _detect_phase(
        dossier=dossier,
        calibration=calibration,
        context=context,
        phase_arg=args.phase,
    )
    generated_at = _utc_now_iso()

    if action == "GO":
        next_steps = [
            "Complete C1 manual signoff (MANUAL_CHECK) in decision log.",
            "Proceed with enforce-mode canary and rollout using phase-end handover.",
        ]
    elif action == "REFRAME":
        next_steps = [
            "Resolve infra failures in audit/calibration pipeline first.",
            "Regenerate dossier and calibration artifacts.",
            "Re-run phase-end handover to refresh this signal.",
        ]
    else:
        next_steps = [
            "Satisfy remaining automated dossier criteria (C0, C2, C3, C4, C4b, C5).",
            "Regenerate dossier and calibration artifacts.",
            "Re-run phase-end handover to refresh this signal.",
        ]

    markdown = _build_markdown(
        phase=phase,
        generated_at=generated_at,
        action=action,
        criteria=criteria,
        blocking_reasons=blocking_reasons,
        next_steps=next_steps,
        calibration_path=calibration_path,
        dossier_path=dossier_path,
        output_path=output_path,
    )

    try:
        _atomic_write_text(output_path, markdown)
    except Exception as exc:
        print(f"WARNING: failed to write output markdown {output_path}: {exc}", file=sys.stderr)
        return 2

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
