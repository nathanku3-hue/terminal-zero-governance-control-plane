# Terminal Zero In-Loop Operations Runbook (Reference)

> Non-runtime operator reference material. Active in-loop guidance lives in
> `docs/runbook_ops_active.md`.
> This file is NOT loaded by `execution_deputy` — it is reference-only.

## Scope

This file contains operator reference material not needed inside the execution loop:
- Subagent review choreography
- Detailed choreography invariants and failure handling

For the active loop command and in-loop truth surfaces, see `docs/runbook_ops_active.md`.
For startup, closure, takeover, and supervision reference, see `docs/operator_reference.md`.

## Subagent Review Choreography

When executing bounded work with subagent delegation, follow this review sequence:

```
Implementer → Spec Compliance Review → Code Quality Review → Continue/Close
```

### Sequence Steps

1. **Implementer**: Executes the bounded scope against the round contract.
2. **Spec Compliance Review**: Verifies the implementation matches the agreed specification in
   `planner_packet_current.md` and `bridge_contract_current.md`.
3. **Code Quality Review**: Checks code quality, test coverage, and lint/typecheck status.
4. **Continue/Close**: If both reviews pass, continue to next bounded piece or close the round.
   If either review fails, return to Implementer with explicit remediation notes.

### Invariants

| Invariant | Meaning |
|-----------|----------|
| No new authority | Review sequence does not override PM/CEO approval gates |
| No runtime hooks | This is a choreography pattern, not automated enforcement |
| No Phase 5C execution semantics | Execution semantics remain blocked until Phase 5C |
| Re-review required | If spec or quality review fails, the work must return to Implementer |

### Failure Handling

- **Spec compliance fails**: Return to Implementer with specific spec drift notes. Do not proceed
  to code quality review until spec compliance passes.
- **Code quality fails**: Return to Implementer with specific quality issues. Spec compliance
  remains valid; only fix quality issues.

This choreography is advisory-only. It does not create a new gate or authority path.
