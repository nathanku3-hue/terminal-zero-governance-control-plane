from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


GENERATOR_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_ceo_go_signal.py"
)
VALIDATOR_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_ceo_go_signal_truth.py"
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


def _run_generator(
    *,
    dossier_path: Path,
    calibration_path: Path,
    context_path: Path,
    output_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(GENERATOR_SCRIPT_PATH),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--context-json",
            str(context_path),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_truth_check(
    *,
    dossier_path: Path,
    calibration_path: Path,
    go_signal_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_SCRIPT_PATH),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--go-signal-md",
            str(go_signal_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_truth_check_passes_for_generator_markdown(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    context_path = tmp_path / "current_context.json"
    go_signal_path = tmp_path / "ceo_go_signal.md"

    _write_json(
        dossier_path,
        {"phase": "Phase 24C", "promotion_criteria": _criteria()},
    )
    _write_json(calibration_path, {"infra_failures": 0})
    _write_json(context_path, {"active_phase": 24})

    generate_result = _run_generator(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        context_path=context_path,
        output_path=go_signal_path,
    )
    assert generate_result.returncode == 0, generate_result.stdout + generate_result.stderr

    truth_result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        go_signal_path=go_signal_path,
    )

    assert truth_result.returncode == 0, truth_result.stdout + truth_result.stderr
    assert "[OK] CEO go-signal truth-check passed." in truth_result.stdout


def test_truth_check_fails_when_action_drifts(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    context_path = tmp_path / "current_context.json"
    go_signal_path = tmp_path / "ceo_go_signal.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, {"infra_failures": 0})
    _write_json(context_path, {})

    generate_result = _run_generator(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        context_path=context_path,
        output_path=go_signal_path,
    )
    assert generate_result.returncode == 0, generate_result.stdout + generate_result.stderr

    original = go_signal_path.read_text(encoding="utf-8")
    drifted = re.sub(
        r"^\s*-\s*Recommended Action:\s*[A-Za-z_]+\s*$",
        "- Recommended Action: HOLD",
        original,
        count=1,
        flags=re.MULTILINE,
    )
    assert drifted != original
    go_signal_path.write_text(drifted, encoding="utf-8")

    truth_result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        go_signal_path=go_signal_path,
    )

    assert truth_result.returncode == 1
    combined = truth_result.stdout + truth_result.stderr
    assert "Recommended Action mismatch" in combined


def test_truth_check_fails_when_criterion_status_drifts(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    context_path = tmp_path / "current_context.json"
    go_signal_path = tmp_path / "ceo_go_signal.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, {"infra_failures": 0})
    _write_json(context_path, {})

    generate_result = _run_generator(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        context_path=context_path,
        output_path=go_signal_path,
    )
    assert generate_result.returncode == 0, generate_result.stdout + generate_result.stderr

    original = go_signal_path.read_text(encoding="utf-8")
    drifted = re.sub(
        r"^(\|\s*C2\s*\|\s*)PASS(\s*\|.*)$",
        r"\1FAIL\2",
        original,
        count=1,
        flags=re.MULTILINE,
    )
    assert drifted != original
    go_signal_path.write_text(drifted, encoding="utf-8")

    truth_result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        go_signal_path=go_signal_path,
    )

    assert truth_result.returncode == 1
    combined = truth_result.stdout + truth_result.stderr
    assert "Criterion C2 status mismatch" in combined


def test_truth_check_returns_exit_2_when_input_missing(tmp_path: Path) -> None:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    missing_signal_path = tmp_path / "missing_ceo_go_signal.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, {"infra_failures": 0})

    truth_result = _run_truth_check(
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        go_signal_path=missing_signal_path,
    )

    assert truth_result.returncode == 2
    combined = truth_result.stdout + truth_result.stderr
    assert "Missing input file" in combined
