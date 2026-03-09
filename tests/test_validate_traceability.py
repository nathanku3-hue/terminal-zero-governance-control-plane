from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_traceability.py"
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _run_validator(
    traceability_path: Path,
    *,
    strict: bool = False,
    require_test: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--input",
        str(traceability_path),
    ]
    if strict:
        command.append("--strict")
    if require_test:
        command.append("--require-test")
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_validate_traceability_passes_with_strict_and_require_test(tmp_path: Path) -> None:
    payload = {
        "directives": [
            {
                "directive_id": "D-100",
                "status": "MAPPED",
                "traceability": {
                    "code_diffs": [{"file": "scripts/example.py"}],
                    "validators": [{"name": "tests/test_example.py::test_ok"}],
                },
            }
        ]
    }
    traceability_path = tmp_path / "pm_to_code_traceability.yaml"
    _write_yaml(traceability_path, payload)

    result = _run_validator(traceability_path, strict=True, require_test=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_traceability_strict_fails_for_unmapped_directive(tmp_path: Path) -> None:
    payload = {
        "directives": [
            {
                "directive_id": "D-UNMAPPED",
                "status": "UNMAPPED",
                "traceability": {"code_diffs": [], "validators": []},
            }
        ]
    }
    traceability_path = tmp_path / "pm_to_code_traceability.yaml"
    _write_yaml(traceability_path, payload)

    result = _run_validator(traceability_path, strict=True)
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "UNMAPPED directives found" in combined
    assert "D-UNMAPPED" in combined


def test_validate_traceability_require_test_fails_when_diffs_have_no_validators(
    tmp_path: Path,
) -> None:
    payload = {
        "directives": [
            {
                "directive_id": "D-NO-VALIDATOR",
                "status": "MAPPED",
                "traceability": {
                    "code_diffs": [{"file": "scripts/example.py"}],
                    "validators": [],
                },
            }
        ]
    }
    traceability_path = tmp_path / "pm_to_code_traceability.yaml"
    _write_yaml(traceability_path, payload)

    result = _run_validator(traceability_path, require_test=True)
    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "code diffs but no validators" in combined
    assert "D-NO-VALIDATOR" in combined
