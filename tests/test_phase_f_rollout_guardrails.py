from __future__ import annotations

from sop._rollout_guardrails import (
    build_guardrail_observability_record,
    evaluate_rollout_guardrails,
)


def _baseline_preconditions() -> dict:
    return {
        "dry_run_passed": True,
        "rollback_plan_ready": True,
        "observability_ready": True,
        "deployment_window_open": True,
        "change_ticket_id": "CHG-001",
        "owner_ack": "ack",
        "escalation_contact": "oncall@example.com",
        "approval_status": "approved",
        "dependency_health": "green",
        "security_exception_open": False,
        "policy_blocker_present": False,
    }


def test_guardrails_allow_when_all_preconditions_satisfied() -> None:
    outcome = evaluate_rollout_guardrails(
        preconditions=_baseline_preconditions(),
        context={"trace_id": "t-1", "gate": "rollout"},
    )
    assert outcome.decision == "ALLOW"
    assert outcome.reason == "operational rollout guardrails satisfied"
    assert outcome.checks[-1].name == "boolean-readiness"


def test_guardrails_block_on_non_dict_payload_shape() -> None:
    outcome = evaluate_rollout_guardrails(preconditions=[], context={})  # type: ignore[arg-type]
    assert outcome.decision == "BLOCK"
    assert "payload" in outcome.reason


def test_guardrails_block_on_missing_required_precondition() -> None:
    pre = _baseline_preconditions()
    del pre["change_ticket_id"]

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "BLOCK"
    assert "missing" in outcome.reason


def test_guardrails_block_on_invalid_schema() -> None:
    pre = _baseline_preconditions()
    pre["dry_run_passed"] = "yes"

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "BLOCK"
    assert "schema" in outcome.reason


def test_guardrails_block_on_security_exception() -> None:
    pre = _baseline_preconditions()
    pre["security_exception_open"] = True

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "BLOCK"
    assert outcome.reason == "security exception open"


def test_guardrails_block_on_policy_blocker_present() -> None:
    pre = _baseline_preconditions()
    pre["policy_blocker_present"] = True

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "BLOCK"
    assert outcome.reason == "policy blocker present"


def test_guardrails_block_precedence_over_hold_signal() -> None:
    pre = _baseline_preconditions()
    pre["security_exception_open"] = True
    pre["approval_status"] = "pending"

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "BLOCK"
    assert outcome.reason == "security exception open"


def test_guardrails_hold_on_pending_approval() -> None:
    pre = _baseline_preconditions()
    pre["approval_status"] = "pending"

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "HOLD"
    assert outcome.reason == "approval pending"


def test_guardrails_hold_on_dependency_health_not_ready() -> None:
    pre = _baseline_preconditions()
    pre["dependency_health"] = "red"

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "HOLD"
    assert outcome.reason == "dependency health not ready"


def test_guardrails_hold_on_false_readiness_flag() -> None:
    pre = _baseline_preconditions()
    pre["rollback_plan_ready"] = False

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "HOLD"
    assert outcome.reason == "rollout readiness flags incomplete"


def test_guardrails_fail_safe_on_incomplete_inputs() -> None:
    pre = _baseline_preconditions()
    pre["escalation_contact"] = ""

    outcome = evaluate_rollout_guardrails(preconditions=pre, context={})
    assert outcome.decision == "BLOCK"
    assert outcome.metadata.get("fail_safe") is True


def test_guardrails_evaluation_is_deterministic() -> None:
    pre = _baseline_preconditions()

    outcome_one = evaluate_rollout_guardrails(preconditions=pre, context={"trace_id": "t-1", "gate": "g"})
    outcome_two = evaluate_rollout_guardrails(preconditions=pre, context={"trace_id": "t-1", "gate": "g"})

    assert outcome_one == outcome_two


def test_guardrails_observability_record_contains_gate_outcome() -> None:
    outcome = evaluate_rollout_guardrails(
        preconditions=_baseline_preconditions(),
        context={"trace_id": "t-1", "gate": "rollout"},
    )
    record = build_guardrail_observability_record(outcome=outcome, trace_id="t-1", gate="rollout")

    assert record["actor"] == "guardrail:phase-f-rollout"
    assert record["decision"] == "ALLOW"
    assert isinstance(record["checks"], list)
    assert len(record["checks"]) >= 1


def test_guardrails_observability_record_is_deterministic() -> None:
    outcome = evaluate_rollout_guardrails(
        preconditions=_baseline_preconditions(),
        context={"trace_id": "t-1", "gate": "rollout"},
    )

    record_one = build_guardrail_observability_record(outcome=outcome, trace_id="t-1", gate="rollout")
    record_two = build_guardrail_observability_record(outcome=outcome, trace_id="t-1", gate="rollout")

    assert record_one == record_two
