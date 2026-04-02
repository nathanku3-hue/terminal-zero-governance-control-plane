# Phase F F3 Conformance + Negative-Path Validation Gates

**Date:** 2026-04-01  
**Phase:** Phase F (`phase6`)  
**Status:** PASS

---

## Gate Coverage Map

### F3-G1 Conformance stability
- ALLOW path remains stable under complete valid preconditions.
- HOLD path reasons are stable (`approval pending`, `dependency health not ready`, readiness incomplete).
- BLOCK path reasons are stable for hard blockers and schema failures.

### F3-G2 Negative-path / abuse-case
- malformed payload shape -> fail-safe BLOCK
- missing required fields -> fail-safe BLOCK
- invalid schema types -> fail-safe BLOCK
- conflicting blocker/hold signals -> BLOCK precedence verified
- incomplete required strings -> fail-safe BLOCK

### F3-G3 Determinism and observability
- repeated guardrail evaluation produces identical outcomes
- observability record structure is present and deterministic

---

## Focused Command

```bash
python -m pytest tests/test_phase_f_rollout_guardrails.py -q
```

Result: **14 passed**

---

## Pass Criteria

F3 is PASS only when:

1. Conformance and negative-path scenarios pass in focused run.
2. Deterministic behavior checks pass.
3. Observability record structure checks pass.

Any failure keeps F3 in BLOCK.
