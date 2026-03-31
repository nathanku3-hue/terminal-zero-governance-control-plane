from __future__ import annotations

from pathlib import Path

import pytest

from sop.phase8_ga_readiness import (
    EXPECTED_FINAL_RESULTS,
    SCENARIO_FIXTURE_MAP,
    VALID_GA_VERDICTS,
    calculate_unexpected_failure_rate,
    is_unexpected_failure,
    validate_ga_verdict,
)


EXPECTED_SCENARIOS = {
    "healthy-pass-path",
    "policy-shadow-block-path",
    "gate-hold-path",
    "plugin-warn-path",
    "failure-artifact-path",
}


def test_scenario_fixture_mapping_is_explicit_and_pinned() -> None:
    assert set(SCENARIO_FIXTURE_MAP.keys()) == EXPECTED_SCENARIOS

    for scenario_id, fixture_path in SCENARIO_FIXTURE_MAP.items():
        assert isinstance(fixture_path, Path)
        # Pinned mapping must be concrete fixture paths in-repo, not runtime tokens.
        assert "{" not in str(fixture_path)
        assert "}" not in str(fixture_path)
        assert "$" not in str(fixture_path)
        assert "*" not in str(fixture_path)
        assert str(fixture_path).strip() != ""
        # Must resolve under tests/fixtures/repos for reproducibility.
        parts = fixture_path.parts
        assert "tests" in parts
        assert "fixtures" in parts
        assert "repos" in parts


def test_expected_results_are_pinned_for_all_scenarios() -> None:
    assert set(EXPECTED_FINAL_RESULTS.keys()) == EXPECTED_SCENARIOS
    assert EXPECTED_FINAL_RESULTS["healthy-pass-path"] == "PASS"
    assert EXPECTED_FINAL_RESULTS["policy-shadow-block-path"] == "PASS"
    assert EXPECTED_FINAL_RESULTS["gate-hold-path"] == "HOLD"
    assert EXPECTED_FINAL_RESULTS["plugin-warn-path"] == "PASS"
    assert EXPECTED_FINAL_RESULTS["failure-artifact-path"] == "FAIL"


def test_unexpected_failure_when_final_result_mismatch() -> None:
    assert is_unexpected_failure(
        expected_final_result="PASS",
        actual_final_result="FAIL",
        exit_code=0,
        expects_normal_completion=True,
        has_loop_summary=True,
        has_closure_or_status_artifact=True,
        has_terminal_decision_artifact=True,
    ) is True


def test_unexpected_failure_when_nonzero_exit_for_normal_contract() -> None:
    assert is_unexpected_failure(
        expected_final_result="PASS",
        actual_final_result="PASS",
        exit_code=1,
        expects_normal_completion=True,
        has_loop_summary=True,
        has_closure_or_status_artifact=True,
        has_terminal_decision_artifact=True,
    ) is True


def test_unexpected_failure_when_required_artifacts_missing() -> None:
    assert is_unexpected_failure(
        expected_final_result="HOLD",
        actual_final_result="HOLD",
        exit_code=0,
        expects_normal_completion=False,
        has_loop_summary=False,
        has_closure_or_status_artifact=True,
        has_terminal_decision_artifact=True,
    ) is True

    assert is_unexpected_failure(
        expected_final_result="HOLD",
        actual_final_result="HOLD",
        exit_code=0,
        expects_normal_completion=False,
        has_loop_summary=True,
        has_closure_or_status_artifact=False,
        has_terminal_decision_artifact=True,
    ) is True


def test_unexpected_failure_when_terminal_decision_artifact_missing() -> None:
    assert is_unexpected_failure(
        expected_final_result="FAIL",
        actual_final_result="FAIL",
        exit_code=1,
        expects_normal_completion=False,
        has_loop_summary=True,
        has_closure_or_status_artifact=True,
        has_terminal_decision_artifact=False,
    ) is True


def test_unexpected_failure_false_when_all_contract_conditions_met() -> None:
    assert is_unexpected_failure(
        expected_final_result="HOLD",
        actual_final_result="HOLD",
        exit_code=1,
        expects_normal_completion=False,
        has_loop_summary=True,
        has_closure_or_status_artifact=True,
        has_terminal_decision_artifact=True,
    ) is False


def test_unexpected_failure_rate_calculation() -> None:
    records = [
        {
            "expected_final_result": "PASS",
            "actual_final_result": "PASS",
            "exit_code": 0,
            "expects_normal_completion": True,
            "has_loop_summary": True,
            "has_closure_or_status_artifact": True,
            "has_terminal_decision_artifact": True,
        },
        {
            "expected_final_result": "PASS",
            "actual_final_result": "FAIL",
            "exit_code": 1,
            "expects_normal_completion": True,
            "has_loop_summary": True,
            "has_closure_or_status_artifact": True,
            "has_terminal_decision_artifact": True,
        },
        {
            "expected_final_result": "HOLD",
            "actual_final_result": "HOLD",
            "exit_code": 0,
            "expects_normal_completion": False,
            "has_loop_summary": False,
            "has_closure_or_status_artifact": True,
            "has_terminal_decision_artifact": True,
        },
    ]

    summary = calculate_unexpected_failure_rate(records)

    assert summary["total_runs"] == 3
    assert summary["unexpected_failures"] == 2
    assert summary["unexpected_failure_rate"] == pytest.approx(2 / 3)


def test_ga_verdict_enum_is_pass_or_fail_only() -> None:
    assert VALID_GA_VERDICTS == {"PASS", "FAIL"}
    assert validate_ga_verdict("PASS") == "PASS"
    assert validate_ga_verdict("FAIL") == "FAIL"

    with pytest.raises(ValueError):
        validate_ga_verdict("HOLD")

    with pytest.raises(ValueError):
        validate_ga_verdict("CONDITIONAL")
