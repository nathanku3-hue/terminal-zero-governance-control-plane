# Phase E D2 Capability Matrix — Extension Runtime Governance

**Date:** 2026-04-01  
**Phase:** Phase E (`phase5`)  
**Status:** Frozen (D2)

---

## Global Contract

- Capability model is **deny-by-default**.
- Only capabilities declared in the D1 allowlist are valid in Phase E.
- Plugin `capabilities` field is mandatory for v2 (`api_version: "2.0"`).
- Unknown capability keys are rejected at load/validation stage.
- Capability declarations must match plugin `kind` constraints.

Allowed capability set:

- `policy.read_context`
- `policy.emit_decision`
- `decision_store.read`
- `decision_store.write`
- `iam_siem.emit_event`

Any other capability identifier is invalid for Phase E.

---

## Capability Matrix

| Capability | Allowed plugin kinds | Allowed operations | Forbidden operations | Validation-time checks | Runtime enforcement expectations | Violation outcome |
|---|---|---|---|---|---|---|
| `policy.read_context` | `policy_evaluator` | read action/context payload for policy evaluation | mutating core governance state; invoking external unapproved channels | reject if declared by non-`policy_evaluator` kind | plugin can read provided context only; no authority escalation | invalid declaration -> `BLOCK` at validation/load |
| `policy.emit_decision` | `policy_evaluator` | emit `ALLOW/BLOCK/WARN` decision payloads via contract | overriding terminal core authority; bypassing policy chain order | reject if declared by non-`policy_evaluator` kind; decision shape must match contract | decision participates in normal chain semantics; first `BLOCK` short-circuits | invalid declaration/shape -> `BLOCK`; runtime contract breach -> `WARN` + audit error marker |
| `decision_store.read` | `decision_store` | read decision records through approved connector path | arbitrary filesystem/network read outside approved adapter scope | reject if non-`decision_store` kind declares it | reads must occur through approved connector boundary and be auditable | invalid declaration -> `BLOCK`; unapproved access attempt -> `BLOCK` |
| `decision_store.write` | `decision_store` | write decision records through approved connector path | destructive overwrite semantics outside contract; bypassing audit trail | reject if non-`decision_store` kind declares it | writes must emit auditable metadata and preserve traceability | invalid declaration -> `BLOCK`; unauditable write attempt -> `BLOCK` |
| `iam_siem.emit_event` | `iam_siem_connector` | emit governance/security events to approved IAM/SIEM channel | arbitrary outbound traffic or non-governance event payload injection | reject if non-`iam_siem_connector` kind declares it | outbound event emission restricted to approved integration adapter | invalid declaration -> `BLOCK`; out-of-policy emit attempt -> `BLOCK` |

---

## Enforcement Stage Mapping

### Load-time / validation-time (hard-fail)

Fail and block plugin activation when any is true:

- `capabilities` missing for v2 plugin
- unknown capability key present
- declared capability not permitted for plugin `kind`
- malformed capability list/type

### Runtime (guarded execution)

- Runtime preserves deterministic plugin order and chain semantics from v1.
- If plugin violates capability contract during execution, outcome is recorded and enforced per matrix violation outcome.
- Boundary violations must be visible in audit artifacts and cannot silently downgrade.

---

## v1/v2 Coexistence Note

- v1 plugins remain operational under existing v1 contract during coexistence window.
- v2 capability model applies only to plugins declaring `api_version: "2.0"`.
- Mixed v1/v2 execution remains deterministic lexical order among compatible plugins.
