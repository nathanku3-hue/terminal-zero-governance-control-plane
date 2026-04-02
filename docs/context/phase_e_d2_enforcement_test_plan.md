# Phase E D2 Enforcement Contract Test Plan

**Date:** 2026-04-01  
**Phase:** Phase E (`phase5`)  
**Status:** Planned and frozen for D2 validation

---

## Scope

Define machine-checkable tests that prove the D2 capability boundary is enforceable and not documentation-only.

---

## Test Groups

### Group A — Valid declaration paths

1. `test_v2_policy_evaluator_accepts_policy_capabilities`
   - plugin kind: `policy_evaluator`
   - capabilities: `policy.read_context`, `policy.emit_decision`
   - expected: load PASS

2. `test_v2_decision_store_accepts_decision_store_capabilities`
   - plugin kind: `decision_store`
   - capabilities: `decision_store.read`, `decision_store.write`
   - expected: load PASS

3. `test_v2_iam_siem_accepts_emit_event_capability`
   - plugin kind: `iam_siem_connector`
   - capability: `iam_siem.emit_event`
   - expected: load PASS

### Group B — Declaration rejection paths (negative)

4. `test_v2_unknown_capability_rejected`
   - capability: `foo.bar`
   - expected: validation/load BLOCK

5. `test_v2_missing_capabilities_rejected`
   - no `capabilities` field
   - expected: validation/load BLOCK

6. `test_v2_cross_kind_capability_rejected`
   - plugin kind `policy_evaluator` declares `decision_store.write`
   - expected: validation/load BLOCK

7. `test_v2_malformed_capability_list_rejected`
   - `capabilities` not list[str]
   - expected: validation/load BLOCK

### Group C — Runtime boundary behavior

8. `test_runtime_forbidden_operation_produces_block`
   - simulate operation outside declared/allowed capability set
   - expected: BLOCK outcome and audit marker

9. `test_runtime_contract_breach_is_auditable`
   - simulate v2 plugin decision/metadata contract breach
   - expected: auditable WARN/ERROR marker per contract; run does not silently pass

10. `test_deterministic_order_preserved_with_v2_plugins`
    - mixed compatible plugins in lexical filename order
    - expected: deterministic order unchanged

### Group D — v1/v2 coexistence

11. `test_v1_plugins_load_without_v2_capability_field`
    - v1 plugin baseline behavior
    - expected: PASS under v1 semantics

12. `test_mixed_v1_v2_chain_semantics_preserved`
    - mixed plugin set with BLOCK short-circuit rule
    - expected: first BLOCK wins and behavior remains deterministic

---

## Evidence Expectations

For D2 PASS recommendation, evidence must include:

- fresh test run with pass/fail counts
- explicit confirmation of unknown/missing/cross-kind rejection behavior
- explicit confirmation of deterministic order + chain semantics preservation
- audit artifact snippet proving boundary violation is visible

---

## Proposed Test Surface

- `tests/test_plugin_api_v1.py` (existing baseline compatibility checks)
- `tests/test_plugin_api_v2_capabilities.py` (new D2 test suite)

Naming and file location can be adjusted, but the above test groups are mandatory for D2 closure confidence.
