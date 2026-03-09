from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_refactor_mock_policy.py"
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


def test_refactor_mock_policy_passes_for_strict_mode_with_budget_and_integration_coverage(
    tmp_path: Path,
) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- REFACTOR_BUDGET_MINUTES: 30",
                "- REFACTOR_SPEND_MINUTES: 20",
                "- MOCK_POLICY_MODE: STRICT",
                "- MOCKED_DEPENDENCIES: payment_api,auth_service",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: YES",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] Refactor/mock policy gate passed." in result.stdout


def test_refactor_mock_policy_parses_key_values_with_extra_spacing(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "  -   REFACTOR_BUDGET_MINUTES   :  15  ",
                " - REFACTOR_SPEND_MINUTES: 15",
                " - MOCK_POLICY_MODE : NOT_APPLICABLE",
                " - MOCKED_DEPENDENCIES : N/A",
                " - INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 0, result.stdout + result.stderr


def test_refactor_mock_policy_fails_when_spend_exceeds_budget_without_reason(
    tmp_path: Path,
) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- REFACTOR_BUDGET_MINUTES: 10",
                "- REFACTOR_SPEND_MINUTES: 12",
                "- MOCK_POLICY_MODE: NOT_APPLICABLE",
                "- MOCKED_DEPENDENCIES: N/A",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 1
    assert "REFACTOR_SPEND_MINUTES exceeds REFACTOR_BUDGET_MINUTES" in (
        result.stdout + result.stderr
    )


def test_refactor_mock_policy_passes_when_budget_exceeded_with_reason(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- REFACTOR_BUDGET_MINUTES: 10",
                "- REFACTOR_SPEND_MINUTES: 12",
                "- REFACTOR_BUDGET_EXCEEDED_REASON: urgent safety refactor before release",
                "- MOCK_POLICY_MODE: NOT_APPLICABLE",
                "- MOCKED_DEPENDENCIES: N/A",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[NOTE] Refactor spend exceeds budget with explicit reason" in result.stdout


def test_refactor_mock_policy_fails_when_strict_has_empty_mock_dependencies(
    tmp_path: Path,
) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- REFACTOR_BUDGET_MINUTES: 5",
                "- REFACTOR_SPEND_MINUTES: 5",
                "- MOCK_POLICY_MODE: STRICT",
                "- MOCKED_DEPENDENCIES: N/A",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: YES",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 1
    assert "MOCKED_DEPENDENCIES must be non-empty" in (result.stdout + result.stderr)


def test_refactor_mock_policy_fails_when_strict_has_no_integration_coverage_yes(
    tmp_path: Path,
) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- REFACTOR_BUDGET_MINUTES: 5",
                "- REFACTOR_SPEND_MINUTES: 4",
                "- MOCK_POLICY_MODE: STRICT",
                "- MOCKED_DEPENDENCIES: billing_client",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: NO",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 1
    assert "must be YES when MOCK_POLICY_MODE=STRICT" in (result.stdout + result.stderr)


def test_refactor_mock_policy_fails_when_not_applicable_has_non_na_coverage(
    tmp_path: Path,
) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    _write_text(
        round_md,
        "\n".join(
            [
                "- REFACTOR_BUDGET_MINUTES: 5",
                "- REFACTOR_SPEND_MINUTES: 1",
                "- MOCK_POLICY_MODE: NOT_APPLICABLE",
                "- MOCKED_DEPENDENCIES: N/A",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: YES",
            ]
        )
        + "\n",
    )

    result = _run(round_md)
    assert result.returncode == 1
    assert "must be N/A when MOCK_POLICY_MODE=NOT_APPLICABLE" in (
        result.stdout + result.stderr
    )


def test_refactor_mock_policy_returns_exit_2_when_round_contract_missing(
    tmp_path: Path,
) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    result = _run(round_md)
    assert result.returncode == 2
    assert "Missing input file" in (result.stdout + result.stderr)

