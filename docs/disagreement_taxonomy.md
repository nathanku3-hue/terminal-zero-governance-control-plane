# Worker-Auditor Disagreement Taxonomy v1.0

Owner: PM  
Status: ACTIVE  
Last Updated: 2026-03-04

## Purpose
Standardize why Worker and Auditor disagree so decisions are faster, repeatable, and measurable.

Use this taxonomy for:
- Round-level dispute logging.
- Escalation routing (PM vs CEO).
- Weekly trend review (top disagreement causes).

## Scope
In scope:
- Worker <-> Auditor disagreements on scope, risk, evidence, and delivery readiness.

Out of scope:
- Business priority disagreements already owned by CEO/PM strategy.
- Runtime production incidents (track separately).

---

## Severity Levels

| Severity | Meaning | Default SLA |
|---|---|---|
| LOW | Preference mismatch; no delivery risk | Resolve in next round |
| MEDIUM | Could delay completion or cause rework | Resolve within 1 business day |
| HIGH | Could create false GO/HOLD, policy breach, or quality failure | Resolve same day; escalate if unresolved |

---

## Reason Codes

| Code | Category | Description | Default Severity | Typical Owner |
|---|---|---|---|---|
| D01 | Scope | Deliverable exceeds original intent | HIGH | Worker to cut scope |
| D02 | Scope | Deliverable incomplete vs DONE_WHEN criteria | MEDIUM | Worker to close gaps |
| D03 | Evidence | Missing/weak evidence for claims (tests/logs/artifacts) | HIGH | Worker to provide evidence |
| D04 | Risk | Infra/safety risk not adequately addressed | HIGH | Worker + RiskOps |
| D05 | Policy | Expert invocation cap/trigger policy violation | MEDIUM | Worker, PM override if needed |
| D06 | Policy | Anti-overengineering contract fields missing/inconsistent | MEDIUM | Worker |
| D07 | Quality | Test coverage insufficient for change risk | MEDIUM | Worker + QA |
| D08 | Interpretation | Different reading of criteria/thresholds (C0-C5, score gates) | MEDIUM | Auditor + PM clarification |
| D09 | Timing | Attempted promotion/decision before evidence maturity | HIGH | PM/CEO hold |
| D10 | Ownership | Decision authority crossed (worker vs auditor vs CEO) | MEDIUM | PM |

---

## Required Log Fields (Per Disagreement)

| Field | Required | Example |
|---|---|---|
| round_id | YES | `20260304_140348` |
| task_id | YES | `PM-24C-006` |
| code | YES | `D03` |
| severity | YES | `HIGH` |
| worker_position | YES | `Claims complete based on local test pass` |
| auditor_position | YES | `Missing production-log evidence` |
| evidence_refs | YES | `tests/..., docs/context/...` |
| decision | YES | `WORKER_FIX` / `AUDITOR_OVERRIDE` / `PM_OVERRIDE` / `CEO_DECISION` |
| owner | YES | `<name/role>` |
| due_utc | YES | `<ISO8601>` |
| resolved | YES | `true/false` |
| resolution_note | YES | `<one-line outcome>` |

---

## Resolution Rules

1. Worker must classify disagreement with one primary code (`D01..D10`).
2. Auditor confirms or reclassifies code with rationale.
3. If unresolved:
   - LOW/MEDIUM -> PM decides.
   - HIGH -> PM same-day; CEO if PM cannot resolve.
4. Close only when:
   - Resolution note is explicit.
   - Evidence references are attached.
   - Next action owner is named.

---

## Escalation Matrix

| Trigger | Escalate To | Deadline |
|---|---|---|
| Same code repeats 3+ times in 7 days | PM | Same day |
| Any HIGH unresolved > 24h | CEO | Immediate |
| D09 (timing/premature promotion) occurs | CEO | Immediate |
| D04 + D03 together (risk + weak evidence) | PM and CEO | Immediate |

---

## Weekly Reporting (Minimum)

Report these 5 numbers in weekly ops notes:
1. Total disagreements.
2. Disagreements by code (`D01..D10`).
3. HIGH disagreements count.
4. Median time-to-resolution.
5. Repeat-rate (same code recurring within 7 days).

Target bands:
- Total disagreements trending down week-over-week.
- HIGH disagreements <= 1 per week.
- Median resolution < 1 business day.

---

## Paste-Ready Round Blocks

### Worker Block
```text
DISAGREEMENT_LOG
ROUND: <round_id>
TASK: <task_id>
CODE: D0X
SEVERITY: LOW|MEDIUM|HIGH
WORKER_POSITION: <one line>
EVIDENCE_REFS: <paths>
PROPOSED_DECISION: WORKER_FIX|PM_OVERRIDE_REQUEST|CEO_ESCALATION
DUE_UTC: <timestamp>
```

### Auditor Block
```text
DISAGREEMENT_REVIEW
ROUND: <round_id>
TASK: <task_id>
CODE: D0X (confirmed|reclassified to D0Y)
AUDITOR_POSITION: <one line>
RISK_STATEMENT: <one line>
REQUIRED_ACTION: <one line>
ESCALATION: NONE|PM|CEO
```

### PM/CEO Resolution Block
```text
DISAGREEMENT_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
FINAL_DECISION: WORKER_FIX|AUDITOR_OVERRIDE|PM_OVERRIDE|CEO_DECISION
OWNER: <role/name>
DUE_UTC: <timestamp>
RESOLVED: true|false
RESOLUTION_NOTE: <one line>
```

---

## Examples

### Example A: Scope Creep
- Code: `D01`
- Pattern: Worker adds extra refactor not requested.
- Decision: `WORKER_FIX` (cut extras, keep scoped deliverable).

### Example B: Weak Evidence
- Code: `D03`
- Pattern: Worker claims pass but no run artifact attached.
- Decision: `WORKER_FIX` with mandatory artifact links.

### Example C: Premature Promotion Push
- Code: `D09`
- Pattern: Attempt to move to enforce before C3 closes.
- Decision: `CEO_DECISION` -> HOLD.

---

## Governance Notes

- This taxonomy is procedural; it does not change gate authority.
- Gate authority remains:
  - Worker: implementation decisions
  - Auditor: scope/risk compliance verdict
  - CEO: GO/HOLD/REFRAME and final strategic decisions

