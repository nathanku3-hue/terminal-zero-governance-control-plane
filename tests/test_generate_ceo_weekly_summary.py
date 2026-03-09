from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


WEEKLY_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_ceo_weekly_summary.py"
)
TRUTH_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_ceo_weekly_summary_truth.py"
)
GO_SIGNAL_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "ceo_go_signal_contract.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "generate_ceo_weekly_summary_under_test",
        WEEKLY_SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {WEEKLY_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_go_signal_module():
    spec = importlib.util.spec_from_file_location(
        "ceo_go_signal_contract_under_test",
        GO_SIGNAL_SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {GO_SIGNAL_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        "c1_24b_close": {"met": "MANUAL_CHECK", "value": "MANUAL_CHECK"},
        "c2_min_items": {"met": c2, "value": "30 >= 30"},
        "c3_min_weeks": {"met": c3, "value": "2 consecutive weeks >= 2"},
        "c4_fp_rate": {"met": c4, "value": "0.00%"},
        "c4b_annotation_coverage": {"met": c4b, "value": "100.00%"},
        "c5_all_v2": {"met": c5, "value": "1 versions: ['2.0.0']"},
    }


def _run_generator(
    tmp_path: Path,
    *,
    dossier_payload: dict,
    calibration_payload: dict,
) -> tuple[subprocess.CompletedProcess[str], str, Path, Path, Path]:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    go_signal_path = tmp_path / "ceo_go_signal.md"
    output_path = tmp_path / "ceo_weekly_summary_latest.md"

    _write_json(dossier_path, dossier_payload)
    _write_json(calibration_path, calibration_payload)
    go_signal_path.write_text("# CEO GO Signal\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(WEEKLY_SCRIPT_PATH),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--go-signal-md",
            str(go_signal_path),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    content = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    return result, content, output_path, dossier_path, calibration_path


def test_weekly_summary_action_go_when_automated_criteria_met(tmp_path: Path) -> None:
    dossier = {
        "phase": "Phase 24C",
        "promotion_criteria": _criteria(),
    }
    calibration = {
        "totals": {"items_reviewed": 48},
        "fp_analysis": {"fp_rate": 0.0, "annotation_coverage_ch": 1.0},
        "infra_failures": 0,
    }

    result, content, output_path, _, _ = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_path.exists()
    assert "Recommended Action: GO" in content
    assert "| C2 | PASS | 48 items |" in content
    assert "| C4 | PASS | 0.00% |" in content
    assert "| C4b | PASS | 100.00% |" in content


def test_weekly_summary_action_hold_when_criteria_not_met(tmp_path: Path) -> None:
    dossier = {
        "promotion_criteria": _criteria(c2=False),
    }
    calibration = {
        "totals": {"items_reviewed": 12},
        "fp_analysis": {"fp_rate": 0.0, "annotation_coverage_ch": 1.0},
        "infra_failures": 0,
    }

    result, content, _, _, _ = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Recommended Action: HOLD" in content
    assert "| C2 | FAIL | 12 items |" in content


def test_weekly_summary_truth_checker_passes_on_generated_markdown(tmp_path: Path) -> None:
    dossier = {
        "promotion_criteria": _criteria(c3=False, c4b=False),
    }
    calibration = {
        "totals": {"items_reviewed": 48},
        "fp_analysis": {"fp_rate": 0.0, "annotation_coverage_ch": 0.6053},
        "infra_failures": 0,
    }

    result, _, output_path, dossier_path, calibration_path = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    truth_result = subprocess.run(
        [
            sys.executable,
            str(TRUTH_SCRIPT_PATH),
            "--weekly-md",
            str(output_path),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert truth_result.returncode == 0, truth_result.stdout + truth_result.stderr


def test_go_signal_public_contract_exposes_shared_helpers() -> None:
    module = _load_go_signal_module()

    assert module.to_int("48 items") == 48
    assert module.extract_infra_failures({"infra_failures": 2}) == 2
    assert module.criterion_met({"c2_min_items": {"met": True}}, "c2_min_items") is True
    assert module.detect_phase({"phase": "Phase 24C"}, {}, {}, "") == "Phase 24C"
    assert module.determine_recommended_action(
        {"promotion_criteria": _criteria()},
        {"infra_failures": 0},
    ) == "GO"


def test_weekly_summary_write_failure_returns_infra_error(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = _load_module()
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    output_path = tmp_path / "ceo_weekly_summary_latest.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(
        calibration_path,
        {
            "totals": {"items_reviewed": 30},
            "fp_analysis": {"fp_rate": 0.0, "annotation_coverage_ch": 1.0},
            "infra_failures": 0,
        },
    )

    def _raise_permission_error(path: Path, content: str) -> None:
        raise PermissionError(f"simulated permission denied: {path}")

    monkeypatch.setattr(module, "_atomic_write_text", _raise_permission_error)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(WEEKLY_SCRIPT_PATH),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--output",
            str(output_path),
        ],
    )

    exit_code = module.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert not output_path.exists()
    assert "WARNING: failed to write weekly summary markdown" in captured.err
