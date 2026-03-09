from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_ceo_go_signal.py"
)


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_ceo_go_signal_under_test", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec for {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding=encoding)


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
    dossier_payload: dict | None,
    calibration_payload: dict | None,
    context_payload: dict | None = None,
    dossier_encoding: str = "utf-8",
    calibration_encoding: str = "utf-8",
) -> tuple[subprocess.CompletedProcess[str], str, Path]:
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    context_path = tmp_path / "current_context.json"
    output_path = tmp_path / "ceo_go_signal.md"

    if dossier_payload is not None:
        _write_json(dossier_path, dossier_payload, encoding=dossier_encoding)
    if calibration_payload is not None:
        _write_json(calibration_path, calibration_payload, encoding=calibration_encoding)
    if context_payload is not None:
        _write_json(context_path, context_payload)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
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

    content = ""
    if output_path.exists():
        content = output_path.read_text(encoding="utf-8")
    return result, content, output_path


def test_generate_ceo_go_signal_go_when_all_automated_criteria_met(tmp_path: Path) -> None:
    dossier = {
        "phase": "Phase 24C",
        "promotion_criteria": _criteria(),
    }
    calibration = {"infra_failures": 0}

    result, content, output_path = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
        dossier_encoding="utf-8-sig",
        calibration_encoding="utf-8-sig",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_path.exists()
    assert "- Recommended Action: GO" in content
    assert "- Phase: Phase 24C" in content
    assert "| C0 | PASS | 0 failures |" in content
    assert "| C1 | MANUAL_CHECK | MANUAL_CHECK |" in content


def test_generate_ceo_go_signal_hold_when_automated_criteria_not_met(tmp_path: Path) -> None:
    dossier = {
        "promotion_criteria": _criteria(c2=False),
    }
    calibration = {"infra_failures": 0}

    result, content, _ = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "- Recommended Action: HOLD" in content
    assert "- C2 not met (30 >= 30)." in content


def test_generate_ceo_go_signal_reframe_on_infra_failure_signal(tmp_path: Path) -> None:
    dossier = {
        "promotion_criteria": _criteria(),
    }
    calibration = {"infra_failures": 2}

    result, content, _ = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "- Recommended Action: REFRAME" in content
    assert "Infra failure signal detected" in content
    assert "calibration infra_failures=2" in content


def test_generate_ceo_go_signal_reframe_when_c0_not_met(tmp_path: Path) -> None:
    dossier = {
        "promotion_criteria": _criteria(c0=False),
    }
    calibration = {"infra_failures": 0}

    result, content, _ = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "- Recommended Action: REFRAME" in content
    assert "C0 marked not met in dossier" in content


def test_generate_ceo_go_signal_creates_markdown_when_inputs_missing(tmp_path: Path) -> None:
    result, content, output_path = _run_generator(
        tmp_path,
        dossier_payload=None,
        calibration_payload=None,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_path.exists()
    assert "- Recommended Action: HOLD" in content
    assert "Missing input file" in content
    assert "WARNING: Missing input file" in result.stderr


def test_generate_ceo_go_signal_phase_falls_back_to_current_context(tmp_path: Path) -> None:
    dossier = {
        "promotion_criteria": _criteria(),
    }
    calibration = {"infra_failures": 0}
    context = {"active_phase": 24}

    result, content, _ = _run_generator(
        tmp_path,
        dossier_payload=dossier,
        calibration_payload=calibration,
        context_payload=context,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "- Phase: Phase 24" in content


def test_generate_ceo_go_signal_write_failure_returns_infra_error(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = _load_generator_module()
    dossier_path = tmp_path / "auditor_promotion_dossier.json"
    calibration_path = tmp_path / "auditor_calibration_report.json"
    context_path = tmp_path / "current_context.json"
    output_path = tmp_path / "ceo_go_signal.md"

    _write_json(dossier_path, {"promotion_criteria": _criteria()})
    _write_json(calibration_path, {"infra_failures": 0})
    _write_json(context_path, {"active_phase": 24})

    def _raise_permission_error(path: Path, content: str) -> None:
        raise PermissionError(f"simulated permission denied: {path}")

    monkeypatch.setattr(module, "_atomic_write_text", _raise_permission_error)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT_PATH),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--context-json",
            str(context_path),
            "--output",
            str(output_path),
        ],
    )

    exit_code = module.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert output_path.exists() is False
    assert captured.out == ""
    assert "WARNING: failed to write output markdown" in captured.err
