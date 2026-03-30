# Phase Brief Template

> **Canonical source:** src/sop/templates/phase_brief_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

**Phase ID**: [phase-XX]
**Phase Name**: [Human-readable phase name]
**Status**: [not_started | in_progress | blocked | complete]
**Owner**: [PM | CEO | Worker | Auditor]
**Start Date**: [YYYY-MM-DD or TBD]
**Target End**: [YYYY-MM-DD or TBD]

---

## Scope

[One paragraph describing what this phase accomplishes]

**Core Components**:
- [Component 1]
- [Component 2]
- [Component 3]

## Product Direction

- **PRODUCT_STAGE_NOW**: [current product/maturity stage]
- **PRODUCT_STAGE_INTENT**: [target stage this phase is serving]
- **PRODUCT_STAGE_OUT_OF_SCOPE**: [stage change or ambition explicitly out of scope]
- **PRODUCT_PROBLEM_THIS_ROUND**: [product/user/system problem this phase addresses]
- **WHY_NOW**: [why this phase matters now]
- **IF_WE_SKIP_THIS**: [cost of skipping this phase]

---

## Workflow Profile

**Workflow Weight**:
- Frontend: [0-100]%
- Backend: [0-100]%
- Governance: [0-100]%
- Data: [0-100]%
- Research: [0-100]%

**Total must equal 100%**

**Rationale**: [One line explaining why this weight distribution]

---

## Objectives

1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

## Planned Surface Strategy

- **PLANNED_SURFACE_NAME**: [primary surface/artifact/component this phase shapes]
- **PLANNED_SURFACE_TYPE**: [core | temporary | replacement]
- **REPLACES_OR_MERGES_WITH**: [existing surface replaced/merged, or none]
- **RETIRE_TRIGGER**: [condition that retires the temporary/replacement surface]
- **MVP_NEXT_STAGE_GATE**: [what proves this slice is sufficient to advance the MVP]
- **NEXT_SIMPLIFICATION_STEP**: [how this phase reduces complexity later]

---

## Deliverables

| ID | Name | Workflow Type | Status | Owner | Evidence Path | Evidence Type |
|---|---|---|---|---|---|---|
| D1 | [Deliverable name] | backend | not_started | worker | scripts/... | code |
| D2 | [Deliverable name] | governance | not_started | auditor | docs/context/... | artifact |
| D3 | [Deliverable name] | data | not_started | worker | data/processed/... | data |

**Workflow Types**: `frontend | backend | governance | data | research`
**Status Values**: `not_started | in_progress | blocked | complete`
**Owner Values**: `worker | auditor | pm | ceo | qa | external`
**Evidence Types**: `code | artifact | report | data | manual`

---

## Success Criteria

| ID | Name | Workflow Type | Threshold | Status | Measured Value | Evidence Path |
|---|---|---|---|---|---|---|
| C0 | [Criterion name] | backend | 0 failures | pending | — | docs/context/... |
| C1 | [Criterion name] | governance | PM signoff | pending | — | docs/decision log.md |
| C2 | [Criterion name] | data | >=30 items | pending | — | docs/context/... |

**Workflow Types**: `frontend | backend | governance | data | research`
**Status Values**: `pass | fail | pending | manual_check`

---

## Realm-Specific Criteria

### [Finance | Law | Medical | Scientific | Software Engineering]

| ID | Name | Check | Validator | Status |
|---|---|---|---|---|
| FIN-01 | PIT Discipline | no future data leakage | scripts/validate_pit_discipline.py | pending |
| FIN-02 | Audit Trail | all decisions logged | scripts/validate_audit_trail.py | pending |
| FIN-03 | Regulatory Compliance | rules documented | manual | pending |

**Validator Types**:
- Script path: `scripts/validate_*.py` (automated check)
- `manual`: requires human review
- `$skill-name`: requires skill invocation (e.g., `$research-analysis`)

**Status Values**: `pass | fail | pending | manual_check | n/a`

---

## Evidence Requirements

**Operational Artifacts**:
- [Artifact 1]: [path]
- [Artifact 2]: [path]

**Test Evidence**:
- [N] tests passing
- Zero regressions in existing test suite

**Traceability**:
- PM-XX-001 through PM-XX-NNN mapped in `pm_to_code_traceability.yaml`
- Decision log entries D-XXX through D-YYY

---

## Acceptance Criteria

### [Criterion Name]
- **Threshold**: [specific measurable threshold]
- **Definition**: [precise definition of what is measured]
- **Rationale**: [why this threshold matters]

[Repeat for each success criterion]

---

## Dependencies

**Blocks**: [List of phases/tasks that cannot start until this completes]
**Blocked By**: [List of phases/tasks that must complete before this starts]
**External Dependencies**: [Any external factors or approvals needed]

---

## Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| [Risk description] | HIGH/MEDIUM/LOW | [Mitigation strategy] | [owner] |

---

## Rollback Plan

**If this phase fails or must be reverted**:
1. [Rollback step 1]
2. [Rollback step 2]
3. [Rollback step 3]

**Rollback Evidence**: [How to verify rollback succeeded]

---

## Next Phase

**Phase ID**: [phase-YY]
**Phase Name**: [Next phase name]
**Trigger**: [What must happen to start next phase]

---

## Notes

[Any additional context, assumptions, or clarifications]

---

**Template Version**: 2.1.0
**Last Updated**: 2026-03-19
