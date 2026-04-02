# Phase E D1 Contract Freeze — Extension API v2

**Date:** 2026-04-01  
**Phase:** Phase E (`phase5`)  
**Status:** Frozen

---

## 1) Approved Integration Classes (in scope)

Phase E v2 scope is frozen to these extension classes:

1. **Policy Evaluator Plugin**
2. **Decision Store Connector Plugin**
3. **IAM/SIEM Connector Plugin**

No other extension class is in Phase E closure scope without explicit audit addendum.

---

## 2) Extension Contract Shape (v2)

Each extension module must export `plugin` with these minimum fields:

- `name: str`
- `version: str` (semver)
- `api_version: "2.0"`
- `kind: "policy_evaluator" | "decision_store" | "iam_siem_connector"`
- `min_sop_version: str` (semver)
- `capabilities: list[str]` (must be allowlisted)
- `evaluate(action: dict, context: dict) -> dict | None`

Result contract (unchanged from v1 for execution decisions):
- `None`, or
- `{ "decision": "ALLOW|BLOCK|WARN", "reason": "non-empty", "metadata"?: <json-serializable> }`

---

## 3) Capability Allowlist Model (deny-by-default)

Allowed capability identifiers in Phase E v2:

- `policy.read_context`
- `policy.emit_decision`
- `decision_store.read`
- `decision_store.write`
- `iam_siem.emit_event`

Rules:

- Any capability outside this set is rejected at load time.
- Missing `capabilities` is treated as invalid contract.
- Runtime behavior for disallowed capability usage is BLOCK at validation gate (not silent downgrade).

---

## 4) v1/v2 Coexistence Rules

- v1 plugins remain supported during Phase E migration window.
- v2 plugins require `api_version: "2.0"` and pass capability validation.
- Mixed v1/v2 plugin sets are allowed.
- Execution order remains deterministic lexical filename order among compatible plugins.
- Existing v1 decision semantics remain unchanged during coexistence window.

---

## 5) Deprecation Timeline & Migration Note

- **T0 (Phase E start):** announce v2 and coexistence policy.
- **T+1 release:** emit deprecation notice for v1-only features lacking v2 contract metadata.
- **T+2 release:** require migration plan for remaining v1-only plugins in governance review.
- **Post-T+2:** retirement decision for v1 support requires separate audit approval (not auto-removed).

Migration documentation must include:

- mapping from v1 fields to v2 fields (`kind`, `api_version`, `capabilities`)
- compatibility expectations during mixed-mode execution
- deprecation notice language and timeline checkpoints

---

## 6) Non-goals / Forbidden Capabilities (Phase E)

The following are explicitly out of scope for Phase E v2:

- arbitrary subprocess execution by plugin contract
- unrestricted filesystem mutation outside governed workspace context
- unrestricted outbound network capability not represented by approved capability keys
- runtime override of core PM/CEO/Auditor governance authority
- hidden bypass of policy gates or closure validation

Any extension design requiring these capabilities must be deferred to a separately approved phase.
