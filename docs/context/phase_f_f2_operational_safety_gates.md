# Phase F F2 Operational Safety Gate Set

**Date:** 2026-04-01  
**Phase:** Phase F (`phase6`)  
**Status:** Implemented and frozen

---

## Guardrail Preconditions (required)

Required boolean preconditions:

- `dry_run_passed`
- `rollback_plan_ready`
- `observability_ready`
- `deployment_window_open`

Required string preconditions:

- `change_ticket_id`
- `owner_ack`
- `escalation_contact`

Additional evaluated keys:

- `approval_status`
- `dependency_health`
- `security_exception_open`
- `policy_blocker_present`

Missing or invalid required precondition data triggers fail-safe `BLOCK`.

---

## Decision Logic (deterministic)

1. **BLOCK** on payload/precondition schema invalidity.
2. **BLOCK** when `security_exception_open` is true.
3. **BLOCK** when `policy_blocker_present` is true.
4. **HOLD** when `approval_status != approved`.
5. **HOLD** when `dependency_health` is not green/healthy.
6. **HOLD** when required readiness booleans include any false value.
7. **ALLOW** only when all guardrails are satisfied.

Terminal adverse precedence: `BLOCK` > `HOLD` > `ALLOW`.

---

## Operator Disposition Requirements

- `HOLD` requires explicit disposition before continuation.
- `BLOCK` requires corrective action + re-validation evidence before retry.
- unresolved disposition items are closure blockers for Phase F.

---

## Observability Hooks

Implemented in:

- `evaluate_rollout_guardrails(...)` in `src/sop/_rollout_guardrails.py`
- `build_guardrail_observability_record(...)` in `src/sop/_rollout_guardrails.py`

Observability record includes:

- actor (`guardrail:phase-f-rollout`)
- trace_id
- gate
- decision
- reason
- ordered guardrail checks with status/detail
- metadata

---

## Focused Validation

Command:

```bash
python -m pytest tests/test_phase_f_rollout_guardrails.py -q
```

Result: **9 passed**
