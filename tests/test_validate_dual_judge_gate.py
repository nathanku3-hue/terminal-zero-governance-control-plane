from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "validate_dual_judge_gate.py"
)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(contract_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--round-contract-md", str(contract_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_passes_low_medium_two_way_without_dual_judge(tmp_path: Path) -> None:
    contract = tmp_path / "round_contract_latest.md"
    _write_text(
        contract,
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DECISION_CLASS: TWO_WAY",
                "- RISK_TIER: MEDIUM",
                "",
            ]
        ),
    )

    result = _run(contract)

    assert result.returncode == 0
    assert "not required" in (result.stdout + result.stderr).lower()


def test_fails_high_risk_when_required_dual_fields_missing(tmp_path: Path) -> None:
    contract = tmp_path / "round_contract_latest.md"
    _write_text(
        contract,
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DECISION_CLASS: ONE_WAY",
                "- RISK_TIER: LOW",
                "- DUAL_JUDGE_REQUIRED: NO",
                "",
            ]
        ),
    )

    result = _run(contract)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "DUAL_JUDGE_REQUIRED must be YES" in combined
    assert "DUAL_JUDGE_AUDITOR_1_VERDICT" in combined
    assert "DUAL_JUDGE_AUDITOR_2_VERDICT" in combined


def test_fails_when_verdicts_diverge_without_resolution(tmp_path: Path) -> None:
    contract = tmp_path / "round_contract_latest.md"
    _write_text(
        contract,
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DECISION_CLASS: TWO_WAY",
                "- RISK_TIER: HIGH",
                "- DUAL_JUDGE_REQUIRED: YES",
                "- DUAL_JUDGE_AUDITOR_1_VERDICT: PASS",
                "- DUAL_JUDGE_AUDITOR_2_VERDICT: FAIL",
                "",
            ]
        ),
    )

    result = _run(contract)

    assert result.returncode == 1
    assert "DUAL_JUDGE_RESOLUTION is required" in (result.stdout + result.stderr)


def test_returns_exit_1_for_missing_classifier(tmp_path: Path) -> None:
    contract = tmp_path / "round_contract_latest.md"
    _write_text(
        contract,
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DECISION_CLASS: TWO_WAY",
                "",
            ]
        ),
    )

    result = _run(contract)

    assert result.returncode == 1
    assert "Missing required classifier: RISK_TIER" in (result.stdout + result.stderr)
