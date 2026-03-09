from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_counterexample_gate.py"
)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(round_md: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--round-contract-md",
            str(round_md),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_counterexample_gate_passes_when_required_mode_has_real_values(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- TDD_MODE: REQUIRED",
                "- COUNTEREXAMPLE_TEST_COMMAND: python -m pytest tests/test_failure_case.py -q",
                "- COUNTEREXAMPLE_TEST_RESULT: FAIL (as expected before fix)",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] Counterexample gate passed." in result.stdout


def test_counterexample_gate_fails_when_required_mode_uses_placeholder(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- TDD_MODE: REQUIRED",
                "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
                "- COUNTEREXAMPLE_TEST_RESULT: TODO",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "COUNTEREXAMPLE_TEST_COMMAND cannot be N/A or TODO when TDD_MODE=REQUIRED." in combined
    assert "COUNTEREXAMPLE_TEST_RESULT cannot be N/A or TODO when TDD_MODE=REQUIRED." in combined


def test_counterexample_gate_passes_when_not_applicable_mode_has_fields(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- TDD_MODE: NOT_APPLICABLE",
                "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
                "- COUNTEREXAMPLE_TEST_RESULT: N/A",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] Counterexample gate passed." in result.stdout


def test_counterexample_gate_fails_when_not_applicable_missing_field(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- TDD_MODE: NOT_APPLICABLE",
                "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 1
    assert "Missing COUNTEREXAMPLE_TEST_RESULT field." in (result.stdout + result.stderr)


def test_counterexample_gate_returns_exit_2_when_round_contract_missing(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    result = _run(round_md)
    assert result.returncode == 2
    assert "Missing input file" in (result.stdout + result.stderr)

