from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


VALIDATOR_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_ceo_weekly_summary_truth.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _criteria(
    *,
    c0: bool = True,
    c2: bool = True,
    c3: bool = True,
    c4: bool = True,
    c4b: bool = True,
    c5: bool = True,
) -> dict:
    return {
        "c0_infra_health": {"met": c0, "value": "0 failures"},
        "c1_24b_close": {"met": True, "value": "APPROVED"},
        "c2_min_items": {"met": c2, "value": "30 >= 30"},
        "c3_min_weeks": {"met": c3, "value": "2 consecutive weeks >= 2"},
        "c4_fp_rate": {"met": c4, "value": "0.00%"},
        "c4b_annotation_coverage": {"met": c4b, "value": "100.00%"},
        "c5_all_v2": {"met": c5, "value": "1 versions: ['2.0.0']"},
    }


def _weekly_markdown(*, c2_status: str = "PASS", recommendation: str | None = "GO") -> str:
    recommendation_line = ""
    if recommendation is not None:
        recommendation_line = f"**Recommendation:** {recommendation}\n"

    return (
        "# CEO Weekly Summary\n"
        "\n"
        "## Promotion Readiness (C0-C5 Criteria)\n"
        "\n"
        "| Criterion | Business Meaning | Status | Progress | Target |\n"
        "|---|---|---|---|---|\n"
        "| **C0: System Health** | No infrastructure failures | [OK] | 0 failures | 0 failures |\n"
        "| **C1: Operational Readiness** | PM signoff recorded in decision log | PASS | APPROVED | D-174 |\n"
        f"| **C2: Evidence Volume** | Enough data to measure quality | {c2_status} | 30/30 items | 30+ items |\n"
        "| **C3: Consistency** | Sustained quality over time | PASS | 2/2 weeks | 2+ consecutive weeks |\n"
        "| **C4: Quality Rate** | Low false-alarm rate | PASS | 0.00% | <5% false alarms |\n"
        "| **C4b: Review Coverage** | All issues reviewed | PASS | 100% | 100% coverage |\n"
        "| **C5: Standards Compliance** | Using latest standards | PASS | All v2.0.0 | All v2.0.0 |\n"
        "\n"
        f"{recommendation_line}"
    )


def _run_truth_check(
    *,
    dossier_path: Path,
    calibration_path: Path,
    weekly_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_SCRIPT_PATH),
            "--weekly-md",
            str(weekly_path),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _calibration_payload() -> dict:
    return {
        "infra_failures": 0,
        "totals": {
            "items_reviewed": 30,
        },
        "fp_analysis": {
            "fp_rate": 0.0,
            "annotation_coverage_ch": 1.0,
        },
    }


def test_weekly_truth_check_passes_for_aligned_markdown(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    weekly_path = tmp_path / "ceo_weekly_summary.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, _calibration_payload())
    weekly_path.write_text(_weekly_markdown(), encoding="utf-8")

    result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        weekly_path=weekly_path,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] CEO weekly-summary truth-check passed." in result.stdout


def test_weekly_truth_check_fails_for_status_drift(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    weekly_path = tmp_path / "ceo_weekly_summary.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria(c2=False)})
    _write_json(calibration_path, _calibration_payload())
    weekly_path.write_text(_weekly_markdown(c2_status="PASS", recommendation="HOLD"), encoding="utf-8")

    result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        weekly_path=weekly_path,
    )

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Criterion C2 status mismatch" in combined


def test_weekly_truth_check_fails_for_recommended_action_drift(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    weekly_path = tmp_path / "ceo_weekly_summary.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, _calibration_payload())
    weekly_path.write_text(_weekly_markdown(recommendation="HOLD"), encoding="utf-8")

    result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        weekly_path=weekly_path,
    )

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Recommended Action mismatch" in combined


def test_weekly_truth_check_fails_when_recommended_action_line_missing(
    tmp_path: Path,
) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    weekly_path = tmp_path / "ceo_weekly_summary.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, _calibration_payload())
    weekly_path.write_text(_weekly_markdown(recommendation=None), encoding="utf-8")

    result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        weekly_path=weekly_path,
    )

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Missing Recommended Action line" in combined


def test_weekly_truth_check_returns_exit_2_on_parse_error(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    weekly_path = tmp_path / "ceo_weekly_summary.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, _calibration_payload())
    weekly_path.write_text(
        "# CEO Weekly Summary\n\nNo criteria snapshot included in this file.\n",
        encoding="utf-8",
    )

    result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        weekly_path=weekly_path,
    )

    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "Invalid weekly summary markdown" in combined
