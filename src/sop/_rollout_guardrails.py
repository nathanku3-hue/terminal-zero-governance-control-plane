from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GuardrailCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class GuardrailOutcome:
    decision: str
    reason: str
    checks: list[GuardrailCheck]
    metadata: dict[str, Any]


_REQUIRED_BOOL_KEYS = (
    "dry_run_passed",
    "rollback_plan_ready",
    "observability_ready",
    "deployment_window_open",
)
_REQUIRED_STR_KEYS = (
    "change_ticket_id",
    "owner_ack",
    "escalation_contact",
)


def _normalize_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evaluate_rollout_guardrails(
    *,
    preconditions: dict[str, Any],
    context: dict[str, Any],
) -> GuardrailOutcome:
    checks: list[GuardrailCheck] = []

    if not isinstance(preconditions, dict) or not isinstance(context, dict):
        return GuardrailOutcome(
            decision="BLOCK",
            reason="guardrail payload must include dict preconditions/context",
            checks=[GuardrailCheck(name="payload-shape", status="BLOCK", detail="invalid payload shape")],
            metadata={"fail_safe": True},
        )

    missing_keys = [
        key for key in (*_REQUIRED_BOOL_KEYS, *_REQUIRED_STR_KEYS) if key not in preconditions
    ]
    if missing_keys:
        checks.append(
            GuardrailCheck(
                name="required-preconditions",
                status="BLOCK",
                detail=f"missing required preconditions: {sorted(missing_keys)}",
            )
        )
        return GuardrailOutcome(
            decision="BLOCK",
            reason="missing required rollout preconditions",
            checks=checks,
            metadata={"missing_keys": sorted(missing_keys), "fail_safe": True},
        )

    invalid_bool_keys = [
        key for key in _REQUIRED_BOOL_KEYS if _normalize_bool(preconditions.get(key)) is None
    ]
    invalid_str_keys = [
        key for key in _REQUIRED_STR_KEYS if not _is_non_empty_string(preconditions.get(key))
    ]
    if invalid_bool_keys or invalid_str_keys:
        checks.append(
            GuardrailCheck(
                name="precondition-schema",
                status="BLOCK",
                detail=(
                    f"invalid bool keys={sorted(invalid_bool_keys)}; "
                    f"invalid string keys={sorted(invalid_str_keys)}"
                ),
            )
        )
        return GuardrailOutcome(
            decision="BLOCK",
            reason="invalid rollout precondition schema",
            checks=checks,
            metadata={
                "invalid_bool_keys": sorted(invalid_bool_keys),
                "invalid_string_keys": sorted(invalid_str_keys),
                "fail_safe": True,
            },
        )

    checks.append(GuardrailCheck(name="required-preconditions", status="PASS", detail="all required keys valid"))

    if preconditions.get("security_exception_open") is True:
        checks.append(
            GuardrailCheck(
                name="security-exception-check",
                status="BLOCK",
                detail="security exception is open",
            )
        )
        return GuardrailOutcome(
            decision="BLOCK",
            reason="security exception open",
            checks=checks,
            metadata={"fail_safe": True},
        )

    if preconditions.get("policy_blocker_present") is True:
        checks.append(
            GuardrailCheck(
                name="policy-blocker-check",
                status="BLOCK",
                detail="policy blocker present",
            )
        )
        return GuardrailOutcome(
            decision="BLOCK",
            reason="policy blocker present",
            checks=checks,
            metadata={"fail_safe": True},
        )

    checks.append(GuardrailCheck(name="hard-blockers", status="PASS", detail="no hard blockers"))

    if str(preconditions.get("approval_status", "")).strip().lower() != "approved":
        checks.append(
            GuardrailCheck(
                name="approval-status",
                status="HOLD",
                detail="approval_status is not approved",
            )
        )
        return GuardrailOutcome(
            decision="HOLD",
            reason="approval pending",
            checks=checks,
            metadata={"approval_status": preconditions.get("approval_status")},
        )

    if str(preconditions.get("dependency_health", "")).strip().lower() not in {"green", "healthy"}:
        checks.append(
            GuardrailCheck(
                name="dependency-health",
                status="HOLD",
                detail="dependency health is not green",
            )
        )
        return GuardrailOutcome(
            decision="HOLD",
            reason="dependency health not ready",
            checks=checks,
            metadata={"dependency_health": preconditions.get("dependency_health")},
        )

    checks.append(GuardrailCheck(name="hold-preconditions", status="PASS", detail="approval and dependency health are ready"))

    false_bools = [key for key in _REQUIRED_BOOL_KEYS if preconditions.get(key) is False]
    if false_bools:
        checks.append(
            GuardrailCheck(
                name="boolean-readiness",
                status="HOLD",
                detail=f"readiness flags not satisfied: {sorted(false_bools)}",
            )
        )
        return GuardrailOutcome(
            decision="HOLD",
            reason="rollout readiness flags incomplete",
            checks=checks,
            metadata={"false_flags": sorted(false_bools)},
        )

    checks.append(GuardrailCheck(name="boolean-readiness", status="PASS", detail="all readiness flags satisfied"))

    return GuardrailOutcome(
        decision="ALLOW",
        reason="operational rollout guardrails satisfied",
        checks=checks,
        metadata={
            "trace_id": str(context.get("trace_id", "")).strip() or None,
            "gate": str(context.get("gate", "")).strip() or None,
        },
    )


def build_guardrail_observability_record(
    *,
    outcome: GuardrailOutcome,
    trace_id: str,
    gate: str,
) -> dict[str, Any]:
    return {
        "actor": "guardrail:phase-f-rollout",
        "trace_id": trace_id,
        "gate": gate,
        "decision": outcome.decision,
        "reason": outcome.reason,
        "checks": [
            {"name": check.name, "status": check.status, "detail": check.detail}
            for check in outcome.checks
        ],
        "metadata": outcome.metadata,
    }
