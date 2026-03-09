# Disagreement Runbook v1.1

**Owner:** PM
**Status:** ACTIVE
**Last Updated:** 2026-03-05

---

## Purpose

Provide step-by-step operational procedures for resolving Worker-Auditor disagreements using the taxonomy codes (D01-D10).

Use this runbook for:
- Executing disagreement resolution flows
- Determining who acts first, who resolves, by when
- Collecting required artifacts per escalation
- Closing disagreements with proper logging

**Companion Document:** `docs/disagreement_taxonomy.md` (defines codes, severity, reason categories)

---

## Quick Reference: D01-D10 Resolution Owners

| Code | Category | First Responder | Resolver | Escalation Path |
|------|----------|-----------------|----------|-----------------|
| D01 | Scope creep | Worker (cut scope) | Auditor (re-review) | PM → CEO |
| D02 | Incomplete deliverable | Worker (close gaps) | Auditor (re-review) | PM → CEO |
| D03 | Weak evidence | Worker (provide evidence) | Auditor (re-review) | PM → CEO |
| D04 | Risk not addressed | Worker + RiskOps | PM (risk assessment) | CEO |
| D05 | Expert policy violation | Worker (fix or request exception) | PM (approve exception) | CEO |
| D06 | Contract fields missing | Worker (fill fields) | Auditor (re-review) | PM |
| D07 | Test coverage insufficient | Worker + QA | Auditor (re-review) | PM → CEO |
| D08 | Criteria interpretation | Auditor + PM | PM (clarify criteria) | CEO |
| D09 | Premature promotion | PM (hold decision) | CEO (final call) | CEO (immediate) |
| D10 | Authority boundary crossed | PM (clarify authority) | PM (enforce matrix) | CEO |

---

## General Resolution Flow (All Codes)

```
0. PRE-CAPTURE: Record pre-execution disagreement risks before first execution command
1. DETECT: Auditor flags finding with disagreement code (D01-D10)
2. CLASSIFY: Worker confirms or disputes code assignment
3. RESPOND: First responder takes action (see code-specific flows below)
4. RE-REVIEW: Auditor validates resolution
5. CLOSE: Log resolution with evidence references
6. ESCALATE: If unresolved within SLA, escalate per matrix
```

**SLA Reminders:**
- HIGH: Same day (within 8 hours)
- MEDIUM: 1 business day
- LOW: Next round

---

## Pre-Execution Disagreement Capture (Mandatory)

Complete this before any execution command:
- `PRE_EXEC_DISAGREEMENT_CAPTURE` (`none` or D-code risk list)
- `PRE_EXEC_CAPTURED_AT_UTC`
- `PRE_EXEC_ALIGNMENT_ACK` (`WORKER_ACK` + `AUDITOR_ACK`)

Acceptance checks:
- Missing any field => open `D06` and set round `NOT_READY`.
- Timestamp later than first execution command => `D06` (late capture) and re-run planning step.
- If risk is identified, include `owner` and `due_utc` in capture row before execution continues.

Paste-ready block:
```text
PRE_EXEC_CAPTURE
ROUND: <round_id>
TASK: <task_id>
PRE_EXEC_DISAGREEMENT_CAPTURE: <none or Dxx|risk|owner|due_utc>
PRE_EXEC_CAPTURED_AT_UTC: <timestamp>
PRE_EXEC_ALIGNMENT_ACK: WORKER_ACK|AUDITOR_ACK
STATUS: READY|NOT_READY
```

---

## D01: Scope Creep (Deliverable Exceeds Intent)

**Severity:** HIGH
**First Responder:** Worker
**Resolver:** Auditor (after Worker fixes)
**SLA:** Same day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Deliverable exceeds ORIGINAL_INTENT"
   - Code: D01
   - Evidence: List out-of-scope work items
   - Required action: "Cut extras, keep only scoped deliverable"

2. **Worker Action (within 8 hours):**
   - Review ORIGINAL_INTENT from round contract
   - Identify out-of-scope work
   - Remove or defer out-of-scope items
   - Update deliverable to match intent
   - Provide evidence: Updated file list, diff showing removals

3. **Auditor Re-Review:**
   - Verify deliverable matches ORIGINAL_INTENT
   - Check NON_GOALS are respected
   - Update finding: RESOLVED or escalate to PM

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: round contract, updated deliverable, diff

### Escalation Trigger
- If Worker refuses to cut scope: Escalate to PM
- If PM cannot resolve: Escalate to CEO (strategic decision)

### Paste-Ready Block
```text
D01_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
ORIGINAL_INTENT: <one line>
OUT_OF_SCOPE_ITEMS: <list>
WORKER_ACTION: Cut <items>, deferred to <future_task>
AUDITOR_VERDICT: RESOLVED|ESCALATE_PM
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D02: Incomplete Deliverable (vs DONE_WHEN)

**Severity:** MEDIUM
**First Responder:** Worker
**Resolver:** Auditor (after Worker closes gaps)
**SLA:** 1 business day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Deliverable incomplete vs DONE_WHEN criteria"
   - Code: D02
   - Evidence: List missing items from DONE_WHEN
   - Required action: "Close gaps to meet DONE_WHEN"

2. **Worker Action (within 1 business day):**
   - Review DONE_WHEN criteria from round contract
   - Identify missing items
   - Complete missing work
   - Provide evidence: Tests pass, artifacts generated, criteria met

3. **Auditor Re-Review:**
   - Verify all DONE_WHEN criteria are met
   - Check evidence is sufficient
   - Update finding: RESOLVED or escalate to PM

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Test results, artifacts, DONE_WHEN checklist

### Escalation Trigger
- If Worker cannot close gaps within SLA: Escalate to PM (scope may need adjustment)
- If gaps require significant rework: PM may REFRAME task

### Paste-Ready Block
```text
D02_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
DONE_WHEN: <criteria>
MISSING_ITEMS: <list>
WORKER_ACTION: Completed <items>
AUDITOR_VERDICT: RESOLVED|ESCALATE_PM
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D03: Weak Evidence (Missing Artifacts)

**Severity:** HIGH
**First Responder:** Worker
**Resolver:** Auditor (after Worker provides evidence)
**SLA:** Same day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Missing/weak evidence for claims"
   - Code: D03
   - Evidence: List claims without supporting artifacts
   - Required action: "Provide test results, logs, or artifacts"

2. **Worker Action (within 8 hours):**
   - Identify missing evidence
   - Run tests, generate logs, or create artifacts
   - Attach evidence to worker packet
   - Provide paths: tests/*, docs/context/*, logs/*

3. **Auditor Re-Review:**
   - Verify evidence supports claims
   - Check artifacts are complete and verifiable
   - Update finding: RESOLVED or escalate to PM

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Test results, logs, artifact paths

### Escalation Trigger
- If Worker cannot provide evidence: Escalate to PM (claim may be invalid)
- If evidence contradicts claim: PM may HOLD or REFRAME

### Paste-Ready Block
```text
D03_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
CLAIMS: <list>
MISSING_EVIDENCE: <list>
WORKER_ACTION: Provided <artifacts>
AUDITOR_VERDICT: RESOLVED|ESCALATE_PM
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D04: Risk Not Addressed (Infra/Safety)

**Severity:** HIGH
**First Responder:** Worker + RiskOps
**Resolver:** PM (risk assessment)
**SLA:** Same day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Infra/safety risk not adequately addressed"
   - Code: D04
   - Evidence: Describe risk (infra failure, data loss, security vuln)
   - Required action: "Mitigate risk or provide risk assessment"

2. **Worker Action (within 8 hours):**
   - Invoke RiskOps expert (if not already invoked)
   - Assess risk impact and likelihood
   - Implement mitigation (fail-closed logic, error handling, validation)
   - Provide evidence: Code changes, test results, risk assessment doc

3. **PM Review:**
   - Validate risk is mitigated or acceptable
   - Check RiskOps expert was consulted
   - Approve mitigation or require additional work
   - If risk is acceptable: Document rationale in decision log

4. **Auditor Re-Review:**
   - Verify mitigation is in place
   - Check PM approval if risk is accepted
   - Update finding: RESOLVED or escalate to CEO

5. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Risk assessment, mitigation code, PM approval

### Escalation Trigger
- If risk cannot be mitigated: Escalate to CEO (strategic decision to accept risk or block)
- If D04 + D03 together (risk + weak evidence): Immediate escalation to PM and CEO

### Paste-Ready Block
```text
D04_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
RISK_DESCRIPTION: <one line>
MITIGATION: <actions taken>
RISKOPS_CONSULTED: YES|NO
PM_APPROVAL: YES|NO (if risk accepted)
AUDITOR_VERDICT: RESOLVED|ESCALATE_CEO
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D05: Expert Policy Violation (Cap/Trigger)

**Severity:** MEDIUM
**First Responder:** Worker
**Resolver:** PM (exception approval)
**SLA:** 1 business day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Expert invocation cap/trigger policy violation"
   - Code: D05
   - Evidence: Expert count >3 without exception, or missing critical expert
   - Required action: "Fix invocation or request PM exception"

2. **Worker Action (within 1 business day):**
   - Review expert_invocation_policy.md
   - Option A: Reduce experts to <=3 by priority
   - Option B: Request PM exception with rationale
   - Provide evidence: Updated expert list or exception request

3. **PM Review (if exception requested):**
   - Check rationale (security critical, infra critical, etc.)
   - Approve or deny exception
   - If approved: Log in decision log with evidence
   - If denied: Worker must reduce experts

4. **Auditor Re-Review:**
   - Verify expert count <=3 or PM exception approved
   - Check rationale is documented
   - Update finding: RESOLVED or escalate to CEO

5. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Expert list, PM exception approval (if applicable)

### Escalation Trigger
- If PM denies exception and Worker disputes: Escalate to CEO
- If same violation repeats 3+ times in 7 days: PM reviews policy

### Paste-Ready Block
```text
D05_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
VIOLATION: <cap_exceeded|missing_critical_expert>
WORKER_ACTION: <reduced_experts|requested_exception>
PM_DECISION: APPROVED|DENIED
RATIONALE: <one line>
AUDITOR_VERDICT: RESOLVED|ESCALATE_CEO
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D06: Contract Fields Missing (Anti-Overengineering)

**Severity:** MEDIUM
**First Responder:** Worker
**Resolver:** Auditor (after Worker fills fields)
**SLA:** 1 business day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Anti-overengineering contract fields missing/inconsistent"
   - Code: D06
   - Evidence: List missing fields (`ORIGINAL_INTENT`, `DELIVERABLE_THIS_SCOPE`, `DECISION_CLASS`, `EXECUTION_LANE`, `NON_GOALS`, `DONE_WHEN`, `DELETE_BEFORE_ADD_TARGETS`, `PRE_EXEC_DISAGREEMENT_CAPTURE`)
   - Required action: "Fill all mandatory contract fields"

2. **Worker Action (within 1 business day):**
   - Review round_contract_template.md
   - Fill missing fields in worker packet
   - Ensure consistency across fields
   - Provide evidence: Updated worker packet

3. **Auditor Re-Review:**
   - Verify all mandatory fields are present
   - Check fields are consistent (DELIVERABLE matches INTENT, NON_GOALS respected, fast lane fields valid if lane=FAST)
   - Update finding: RESOLVED or escalate to PM

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Updated worker packet

### Escalation Trigger
- If Worker refuses to fill fields: Escalate to PM (policy enforcement)
- If fields are inconsistent after fix: PM reviews and clarifies

### Paste-Ready Block
```text
D06_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
MISSING_FIELDS: <list>
WORKER_ACTION: Filled <fields>
AUDITOR_VERDICT: RESOLVED|ESCALATE_PM
EVIDENCE: <worker_packet_path>
CLOSED_UTC: <timestamp>
```

---

## D07: Test Coverage Insufficient

**Severity:** MEDIUM
**First Responder:** Worker + QA
**Resolver:** Auditor (after Worker adds tests)
**SLA:** 1 business day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Test coverage insufficient for change risk"
   - Code: D07
   - Evidence: Coverage percentage, missing test scenarios
   - Required action: "Add tests to meet coverage threshold or QA review"

2. **Worker Action (within 1 business day):**
   - Invoke QA expert (if not already invoked)
   - Add missing tests (unit, integration, edge cases)
   - Run coverage report
   - Provide evidence: Test files, coverage report, QA review

3. **Auditor Re-Review:**
   - Verify coverage meets threshold (typically 80%+)
   - Check critical paths are tested
   - Check QA expert reviewed if coverage is borderline
   - Update finding: RESOLVED or escalate to PM

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Test files, coverage report, QA review

### Escalation Trigger
- If coverage cannot meet threshold: Escalate to PM (may accept lower coverage with rationale)
- If QA expert disagrees with coverage: PM makes final call

### Paste-Ready Block
```text
D07_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
COVERAGE_BEFORE: <percentage>
COVERAGE_AFTER: <percentage>
TESTS_ADDED: <list>
QA_CONSULTED: YES|NO
AUDITOR_VERDICT: RESOLVED|ESCALATE_PM
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D08: Criteria Interpretation Dispute

**Severity:** MEDIUM
**First Responder:** Auditor + PM
**Resolver:** PM (clarify criteria)
**SLA:** 1 business day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Different reading of criteria/thresholds (C0-C5, score gates)"
   - Code: D08
   - Evidence: Describe interpretation difference
   - Required action: "PM clarify criteria definition"

2. **PM Action (within 1 business day):**
   - Review criteria definition (dossier, gates, thresholds)
   - Consult source documents (phase brief, promotion criteria)
   - Clarify interpretation with rationale
   - Update criteria doc if ambiguous
   - Provide evidence: Criteria doc, clarification note

3. **Auditor Re-Review:**
   - Apply PM clarification to finding
   - Update verdict based on clarified criteria
   - Update finding: RESOLVED or escalate to CEO

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Criteria doc, PM clarification note

### Escalation Trigger
- If PM clarification is disputed: Escalate to CEO (final authority on criteria)
- If same criteria ambiguity repeats: PM updates criteria doc permanently

### Paste-Ready Block
```text
D08_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
CRITERIA: <C0|C1|C2|C3|C4|C4b|C5|gate_name>
WORKER_INTERPRETATION: <one line>
AUDITOR_INTERPRETATION: <one line>
PM_CLARIFICATION: <one line>
CRITERIA_DOC_UPDATED: YES|NO
AUDITOR_VERDICT: RESOLVED|ESCALATE_CEO
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D09: Premature Promotion Attempt

**Severity:** HIGH
**First Responder:** PM (hold decision)
**Resolver:** CEO (final call)
**SLA:** Immediate (same day)

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Attempted promotion/decision before evidence maturity"
   - Code: D09
   - Evidence: Describe missing evidence (C3 not closed, FP rate unstable, etc.)
   - Required action: "HOLD promotion until criteria met"

2. **PM Action (immediate):**
   - Review dossier and criteria status
   - Confirm evidence is insufficient
   - Issue HOLD decision
   - Communicate to Worker and CEO
   - Provide evidence: Dossier status, missing criteria

3. **CEO Review (same day):**
   - Validate PM HOLD decision
   - Confirm criteria are not met
   - Approve HOLD or override with strategic rationale
   - If override: Document risk acceptance in decision log

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Dossier, PM HOLD decision, CEO approval

### Escalation Trigger
- D09 always escalates to CEO immediately (no PM-only resolution)
- If D09 repeats: CEO reviews Worker understanding of criteria

### Paste-Ready Block
```text
D09_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
PROMOTION_REQUESTED: <shadow_to_enforce|canary_to_rollout>
MISSING_CRITERIA: <list>
PM_DECISION: HOLD
CEO_DECISION: APPROVED_HOLD|OVERRIDE
OVERRIDE_RATIONALE: <one line if override>
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## D10: Authority Boundary Crossed

**Severity:** MEDIUM
**First Responder:** PM
**Resolver:** PM (enforce matrix)
**SLA:** 1 business day

### Step-by-Step Flow

1. **Auditor Action:**
   - Flag finding: "Decision authority crossed (worker vs auditor vs CEO)"
   - Code: D10
   - Evidence: Describe authority violation (e.g., Worker overrode HIGH finding, Auditor dictated implementation)
   - Required action: "PM clarify authority and enforce matrix"

2. **PM Action (within 1 business day):**
   - Review decision_authority_matrix.md
   - Identify which role has authority for this decision type
   - Clarify authority with rationale
   - Enforce matrix (reverse unauthorized decision if needed)
   - Provide evidence: Authority matrix, clarification note

3. **Auditor Re-Review:**
   - Verify authority matrix is enforced
   - Check unauthorized decision is reversed
   - Update finding: RESOLVED or escalate to CEO

4. **Closure:**
   - Log resolution in disagreement log
   - Attach evidence: Authority matrix, PM clarification, reversed decision (if applicable)

### Escalation Trigger
- If authority conflict is not in matrix: Escalate to CEO for ruling
- If same authority violation repeats: PM updates matrix with CEO approval

### Paste-Ready Block
```text
D10_RESOLUTION
ROUND: <round_id>
TASK: <task_id>
AUTHORITY_VIOLATION: <description>
CORRECT_AUTHORITY: <Worker|Auditor|PM|CEO>
PM_ACTION: <clarified|reversed_decision>
AUDITOR_VERDICT: RESOLVED|ESCALATE_CEO
EVIDENCE: <paths>
CLOSED_UTC: <timestamp>
```

---

## Cross-Judge Lightweight Sampling Policy

Purpose: sample disagreement outcomes for quality calibration with low overhead.

Sampling rules:
- Random sample: minimum 10% of `RESOLVED` disagreements weekly.
- Mandatory sample triggers:
  - `severity=HIGH`
  - Repeated same code on same task within 7 days
  - Primary auditor confidence `<0.70`

Mandatory fields for sampled items:
- `cross_judge_sampled` (`YES/NO`)
- `cross_judge_trigger` (`random_10pct|high_severity|repeat_pattern|low_confidence|none`)
- `cross_judge_id`
- `cross_judge_result` (`CONCUR|DIVERGE|N/A`)

Acceptance checks:
- Trigger present + `cross_judge_sampled=NO` => escalation to PM.
- `cross_judge_result=DIVERGE` => reopen disagreement and classify `D08` unless a different code is clearly correct.

---

## Escalation Matrix (Cross-Reference)

| Trigger | Escalate To | Deadline |
|---------|-------------|----------|
| Same code repeats 3+ times in 7 days | PM | Same day |
| Any HIGH unresolved > 24h | CEO | Immediate |
| D09 (premature promotion) occurs | CEO | Immediate |
| D04 + D03 together (risk + weak evidence) | PM and CEO | Immediate |
| SLA breach by Worker/Auditor | PM | Next business day |
| SLA breach by PM | CEO | Next business day |
| Authority conflict not in matrix | CEO | Same day |

---

## Closure Checklist (All Codes)

Before marking disagreement as RESOLVED, verify:

- [ ] Resolution note is explicit and actionable
- [ ] Evidence references are attached (file paths, run IDs, timestamps)
- [ ] Next action owner is named (if follow-up required)
- [ ] SLA was met (or breach is logged)
- [ ] Auditor re-reviewed and updated verdict
- [ ] Resolution is logged in disagreement log with all required fields
- [ ] Pre-execution capture fields are present and timely
- [ ] Cross-judge fields are complete for sampled/triggered cases

**Required Fields:**
- round_id, task_id, code, severity
- worker_position, auditor_position
- evidence_refs, decision, owner, due_utc
- resolved (true/false), resolution_note
- pre_exec_disagreement_capture, pre_exec_captured_at_utc
- cross_judge_sampled, cross_judge_trigger, cross_judge_result

---

## Weekly Reporting

**PM tracks and reports weekly:**
1. Total disagreements by code (D01-D10)
2. HIGH disagreements count (target: <=1 per week)
3. Median time-to-resolution (target: <1 business day)
4. Repeat-rate (same code recurring within 7 days) (target: 0%)
5. SLA breach count (target: 0)

**Triggers for runbook update:**
- New disagreement pattern not covered by D01-D10
- Resolution flow proves inefficient (>3 escalations on same code)
- SLA breach rate >10%

---

## Governance Notes

- This runbook is operational; it implements the taxonomy (docs/disagreement_taxonomy.md)
- Conflicts between runbook and taxonomy: Taxonomy wins (definitions), runbook wins (procedures)
- Updates require PM proposal + CEO approval
- Version incremented on each update

**Version History:**
- v1.1 (2026-03-05): Added mandatory pre-execution disagreement capture and cross-judge lightweight sampling policy
- v1.0 (2026-03-04): Initial policy
