# Phase End Handover Template

## Executive Summary (PM-friendly)

**Phase**: [Phase Number/Name]
**Duration**: [Start Date] → [End Date]
**Status**: [COMPLETE | PARTIAL | BLOCKED]
**Key Outcome**: [One-sentence summary of what was delivered]

## Delivered Scope vs Deferred Scope

### Delivered
- [Item 1]: [Brief description + evidence pointer]
- [Item 2]: [Brief description + evidence pointer]

### Deferred
- [Item 1]: [Reason for deferral + target phase]
- [Item 2]: [Reason for deferral + target phase]

## Derivation and Formula Register

| Formula ID | Formula | Variables | Source Path |
|------------|---------|-----------|-------------|
| F-001 | [formula] | [var definitions] | [file:line] |
| F-002 | [formula] | [var definitions] | [file:line] |

## Logic Chain

```
Input → Transform → Decision → Output
[source] → [operation] → [condition] → [artifact]
```

**Example**:
```
raw_data.csv → filter(valid_rows) → if count > threshold → processed_data.csv
```

## Evidence Matrix

| Command | Result | Artifact |
|---------|--------|----------|
| `python script.py` | exit_code=0 | `output/result.csv` |
| `pytest tests/` | 15 passed | `.pytest_cache/` |

## Open Risks / Assumptions / Rollback

### Open Risks
- **R-001**: [Risk description] | Impact: [H/M/L] | Mitigation: [action] | Owner: [name]

### Assumptions
- **A-001**: [Assumption description] | Validation: [how to verify]

### Rollback Plan
- **Step 1**: [Rollback action]
- **Step 2**: [Verification step]

## Next Phase Roadmap

1. [Action 1] | Acceptance: [verification criteria]
2. [Action 2] | Acceptance: [verification criteria]
3. [Action 3] | Acceptance: [verification criteria]

**Blockers for Next Phase**:
- [Blocker 1]
- [Blocker 2]

---

## NewContextPacket

**What was done**:
- [Key deliverable 1]
- [Key deliverable 2]

**What is locked**:
- [Immutable decision 1]
- [Immutable decision 2]

**What remains**:
- [Open work item 1]
- [Open work item 2]

**Next-phase roadmap**:
1. [First action] | Acceptance: [criteria]
2. [Second action] | Acceptance: [criteria]
3. [Third action] | Acceptance: [criteria]

**Immediate first step**:
[Concrete next action for fresh worker]

**ConfirmationRequired**: YES
