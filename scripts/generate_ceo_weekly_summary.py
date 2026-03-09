from __future__ import annotations

import argparse
import os
import sys
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

try:
    from scripts import ceo_go_signal_contract as go_signal_contract
except Exception:
    import ceo_go_signal_contract as go_signal_contract  # type: ignore[no-redef]


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


def _fmt_percent(value: Any) -> str:
    number = _to_float(value)
    if number is None:
        return "N/A"
    return f"{number * 100.0:.2f}%"


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


def _resolved_action(dossier: dict[str, Any], calibration: dict[str, Any]) -> str:
    return go_signal_contract.determine_recommended_action(dossier=dossier, calibration=calibration)


def _criterion_value(
    short_code: str,
    key: str,
    criteria: dict[str, Any],
    calibration: dict[str, Any],
) -> str:
    totals_obj = calibration.get("totals")
    totals: dict[str, Any] = totals_obj if isinstance(totals_obj, dict) else {}
    fp_obj = calibration.get("fp_analysis")
    fp_analysis: dict[str, Any] = fp_obj if isinstance(fp_obj, dict) else {}

    if short_code == "C0":
        infra_failures = go_signal_contract.extract_infra_failures(calibration)
        if infra_failures is not None:
            return f"{infra_failures} failures"
    if short_code == "C2":
        items_reviewed = go_signal_contract.to_int(totals.get("items_reviewed"))
        if items_reviewed is not None:
            return f"{items_reviewed} items"
    if short_code == "C4":
        return _fmt_percent(fp_analysis.get("fp_rate"))
    if short_code == "C4b":
        return _fmt_percent(fp_analysis.get("annotation_coverage_ch"))

    return go_signal_contract.criterion_value(criteria, key)


def _build_markdown(
    *,
    phase: str,
    generated_at: str,
    action: str,
    criteria: dict[str, Any],
    calibration: dict[str, Any],
) -> str:
    lines: list[str] = [
        "# CEO Weekly Summary",
        "",
        f"- Generated: {generated_at}",
        f"- Phase: {phase}",
        f"Recommended Action: {action}",
        "",
        "## Promotion Criteria",
        "",
        "| Criterion | Status | Value |",
        "|---|---|---|",
    ]

    for short_code, key in go_signal_contract.CRITERIA_ORDER:
        met_value = go_signal_contract.criterion_met(criteria, key)
        status = go_signal_contract.criterion_status_display(key, met_value)
        value = _criterion_value(short_code, key, criteria, calibration).replace("|", "\\|")
        lines.append(f"| {short_code} | {status} | {value} |")

    lines.extend(
        [
            "",
            "## Snapshot",
            "",
            "This report is auto-generated from dossier/calibration artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate CEO weekly summary markdown from dossier/calibration artifacts."
    )
    parser.add_argument(
        "--dossier-json",
        default="docs/context/auditor_promotion_dossier.json",
        help="Path to auditor promotion dossier JSON.",
    )
    parser.add_argument(
        "--calibration-json",
        default="docs/context/auditor_calibration_report.json",
        help="Path to auditor calibration report JSON.",
    )
    parser.add_argument(
        "--go-signal-md",
        default="docs/context/ceo_go_signal.md",
        help="Optional go-signal markdown path (kept for symmetry and provenance).",
    )
    parser.add_argument(
        "--output",
        default="docs/context/ceo_weekly_summary_latest.md",
        help="Output markdown path.",
    )
    parser.add_argument(
        "--phase",
        default="",
        help="Optional phase label override.",
    )
    args = parser.parse_args()

    dossier_path = Path(args.dossier_json)
    calibration_path = Path(args.calibration_json)
    output_path = Path(args.output)

    dossier, dossier_warnings = go_signal_contract.load_json_fail_open(dossier_path)
    calibration, calibration_warnings = go_signal_contract.load_json_fail_open(calibration_path)

    for warning in dossier_warnings + calibration_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    criteria = go_signal_contract.promotion_criteria(dossier)

    action = _resolved_action(dossier=dossier, calibration=calibration)
    phase = go_signal_contract.detect_phase(
        dossier=dossier,
        calibration=calibration,
        context={},
        phase_arg=args.phase,
    )
    generated_at = _utc_now_iso()
    markdown = _build_markdown(
        phase=phase,
        generated_at=generated_at,
        action=action,
        criteria=criteria,
        calibration=calibration,
    )

    try:
        _atomic_write_text(output_path, markdown)
    except OSError as exc:
        print(f"WARNING: failed to write weekly summary markdown: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
