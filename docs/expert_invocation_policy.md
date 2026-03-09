# Expert Invocation Policy v1.2

**Owner:** PM (Product Management)
**Review Cadence:** Weekly during shadow window, monthly post-promotion
**Last Updated:** 2026-03-05
**Status:** ACTIVE

**Version History:**
- v1.2 (2026-03-05): Added decision class + fast-lane gating, delete-before-add and pre-execution disagreement fields, cross-judge metadata hook
- v1.1 (2026-03-04): Fixed cap/exception contradiction, unsafe override authority, missing per-task limit, KPI reporting claim
- v1.0 (2026-03-04): Initial policy

---

## 1. Authority Split

| Role | Authority | Scope |
|------|-----------|-------|
| **Worker** | Implementation decisions | How to solve, which code to write, which tools to use |
| **Auditor** | Scope/risk enforcement | Flags overengineering, missing experts, expert sprawl, risk gaps |
| **CEO** | GO/HOLD/REFRAME decisions | Approves/blocks promotion, sets strategic direction, resolves escalations |

**Principle:** Worker proposes, Auditor validates, CEO decides.

---

## 2. Expert Roles and Scope

| Expert | Scope | NOT in Scope |
|--------|-------|--------------|
| **principal** | Architecture decisions, design patterns, system-level trade-offs | Implementation details, routine fixes |
| **system_eng** | Integration, gate orchestration, workflow design | Single-script changes, business logic |
| **riskops** | Infra health, fail-closed validation, FP rate tracking | Business logic, UI, general code quality |
| **qa** | Test coverage, edge cases, validation scenarios | Implementation code, architecture |
| **devsecops** | Security vulnerabilities, access control, audit trails | General code quality, performance |
| **architect** | Component design, module boundaries, API contracts | Implementation details, system-level decisions |

---

## 3. Deterministic Invocation Algorithm

**Sequence (execute in order):**

```
0. VALIDATE lane/class gate:
   REQUIRE DECISION_CLASS in {ONE_WAY, TWO_WAY}
   REQUIRE EXECUTION_LANE in {STANDARD, FAST}
   IF EXECUTION_LANE == FAST:
       REQUIRE all FAST_LANE_ELIGIBILITY_* == YES
       REQUIRE DECISION_CLASS == TWO_WAY
       SET invocation_list = none
       IF security/risk trigger appears:
           SWITCH lane to STANDARD (FAST not allowed)
       ELSE:
           OUTPUT invocation_list (none) and STOP

1. START with core reviewers (always invoked):
   - None (all experts are optional by default)

2. APPLY triggers (check conditions, add experts):
   IF new_system_component OR major_refactor:
       ADD principal
   IF gate_integration OR workflow_change:
       ADD system_eng
   IF fail_closed_logic OR fp_tracking OR infra_error_handling:
       ADD riskops
   IF new_test_file OR edge_case_validation OR coverage_gap:
       ADD qa
   IF auth_change OR sensitive_data OR security_vuln:
       ADD devsecops
   IF module_boundary OR api_contract OR component_interface:
       ADD architect

3. APPLY caps:
   IF expert_count > 3:
       GOTO overflow_rule

4. RESOLVE conflicts by priority:
   Priority order: devsecops > riskops > principal > system_eng > architect > qa
   (Security and risk take precedence)

5. OUTPUT invocation list
```

---

## 4. Overflow Rule

**When triggers exceed 3-expert cap:**

1. **Keep top 3 by priority** (see priority order in algorithm)
2. **Defer remaining experts** to next round
3. **Require explicit rationale** in worker packet:
   - Why all triggered experts are needed
   - Why cap should be exceeded (exception request)
4. **Escalate to PM** if rationale insufficient

**Exception Approval:**
- Security or infra critical issues: Auto-approve 4th expert (exceeds normal 3-expert cap)
- All other cases: PM approval required

**Per-Task Hard Limit:**
- Maximum 5 total expert invocations across all rounds for a single task
- If limit reached: Escalate to PM for scope review
- Reset: Limit resets when task completes or is closed

---

## 5. Anti-Overengineering Contract

**Mandatory fields per round (in worker packet):**

```json
{
  "ORIGINAL_INTENT": "One-sentence problem statement from user",
  "DELIVERABLE_THIS_SCOPE": "Concrete output for this round only",
  "DECISION_CLASS": "ONE_WAY or TWO_WAY",
  "EXECUTION_LANE": "STANDARD or FAST",
  "FAST_LANE_REQUEST": "YES or NO",
  "NON_GOALS": "What is explicitly out of scope this round",
  "DONE_WHEN": "Objective completion criteria (tests pass, gate passes, etc.)",
  "DELETE_BEFORE_ADD_TARGETS": "Paths to delete/deprecate first, or none",
  "ADDITIONS_AFTER_DELETE": "Planned additions after deletion step, or none",
  "PRE_EXEC_DISAGREEMENT_CAPTURE": "none or list: D-code|risk|owner|due_utc"
}
```

**Auditor enforcement:**
- Missing any field → MEDIUM finding
- Scope creep detected (deliverable != original intent) → HIGH finding
- Non-goals violated (work done outside scope) → HIGH finding
- `EXECUTION_LANE=FAST` with any `FAST_LANE_ELIGIBILITY_* = NO` → HIGH finding
- Additive changes without valid `DELETE_BEFORE_ADD_TARGETS` entry → HIGH finding
- Missing `PRE_EXEC_DISAGREEMENT_CAPTURE` before execution start → MEDIUM finding

---

## 6. Measurable KPIs

**Tracked per round:**

| KPI | Target | Threshold |
|-----|--------|-----------|
| `experts_per_round` | ≤2 | WARN if >3, BLOCK if >4 without exception |
| `experts_per_task` | ≤5 | WARN if >5, escalate to PM if >7 |
| `rounds_to_decision` | ≤3 | WARN if >5, escalate if >7 |
| `HOLD_rate` | <20% | Review policy if >30% for 2+ weeks |
| `REFRAME_rate` | <5% | Escalate if >10% for 2+ weeks |
| `auditor_ch_findings_per_round` | <3 | Review worker quality if >5 sustained |

**Reporting:**
- Manual tracking in weekly ops notes (until calibration script integration)
- Weekly during shadow window
- Monthly post-promotion
- Implementation task: Add expert KPI tracking to auditor_calibration_report.py (deferred to post-promotion)

---

## 7. Exception and Escalation Path

**Policy Violation Handling:**

| Violation | Who Blocks | Who Can Override | How Recorded |
|-----------|------------|------------------|--------------|
| Expert sprawl (>3 without exception) | Auditor | PM | Auditor finding (MEDIUM) |
| Missing critical expert (security issue without devsecops) | Auditor | PM (or CEO if unresolved) | Auditor finding (HIGH) |
| Scope creep (deliverable != intent) | Auditor | CEO | Auditor finding (HIGH) + HOLD |
| Cap exceeded without rationale | Auditor | PM | Auditor finding (MEDIUM) + HOLD |
| KPI threshold breach | Auditor | CEO | Weekly report + escalation |

**Escalation Flow:**
1. Auditor flags violation in findings
2. Worker provides rationale or fixes issue
3. If unresolved: PM reviews and decides
4. If PM cannot resolve: CEO makes final call

**Recording:**
- All violations logged in `auditor_findings.json`
- Escalations logged in `escalation_events.json`
- Overrides logged in `decision log.md`

---

## 8. Paste-Ready Invocation Output Format

### Generated Advisory Acceleration Artifacts

- `docs/context/expert_request_latest.json` / `docs/context/expert_request_latest.md`
  - Generated from current loop evidence when the worker is blocked by low confidence, ambiguity, or expert-dependent uncertainty.
  - Purpose: accelerate a bounded specialist ask.
  - Authority: advisory only; Worker still owns the implementation ask, Auditor still flags missing/incorrect expert use, and PM approves exceptions.
- `docs/context/pm_ceo_research_brief_latest.json` / `docs/context/pm_ceo_research_brief_latest.md`
  - Generated from current loop evidence when PM/CEO needs focused tradeoff research delegated to subagents/engineers.
  - Purpose: accelerate research delegation and structured option gathering.
  - Authority: advisory only; PM/CEO remains the synthesizer and final decision owner.
- Split-style delivery convention for generated advisory artifacts:
  - JSON file = machine-canonical payload for downstream automation.
  - Markdown file = concise human/operator summary.
  - `paste_ready_block` = copy/paste delegation lane.
- Milestone roster integration (advisory-only):
  - If `docs/context/milestone_expert_roster_latest.json` is present, expert domain assignment should prefer approved `mandatory_domains` + `optional_domains`.
  - If roster is missing or requested domain is outside approved lineup, emit explicit fail-closed status (`ROSTER_MISSING` or `UNKNOWN_EXPERT_DOMAIN`) and set `BOARD_LINEUP_REVIEW_REQUIRED`.
  - These statuses do not create new control-plane authority; they are advisory signals for PM/CEO board reentry timing.
- If generated expert/research artifacts conflict with the active round contract or startup intake, the active authoritative artifacts win.

**Worker Output (per round):**

- Authoritative structured lanes remain `machine_optimized` and `pm_first_principles`.
- Optional additive `response_views` may be emitted with:
  - `machine_view`
  - `human_brief`
  - `paste_ready_block`
- `response_views` improves transport/readability only; it does not replace the authoritative worker contract.

```
=== EXPERT INVOCATION ===
Round: <round_number>
Task: <task_id>

Triggered Experts:
- principal: <trigger_reason>
- riskops: <trigger_reason>
- qa: <trigger_reason>

Decision Class: ONE_WAY|TWO_WAY
Execution Lane: STANDARD|FAST
Fast Lane Accepted: YES|NO

Applied Cap: 3/3 experts
Deferred: architect (module_boundary trigger, lower priority)

Rationale: <why_these_experts_needed>

Anti-Overengineering Contract:
- ORIGINAL_INTENT: <one_sentence>
- DELIVERABLE_THIS_SCOPE: <concrete_output>
- NON_GOALS: <explicitly_out_of_scope>
- DONE_WHEN: <objective_criteria>
- DELETE_BEFORE_ADD_TARGETS: <paths_or_none>
- ADDITIONS_AFTER_DELETE: <paths_or_none>
- PRE_EXEC_DISAGREEMENT_CAPTURE: <none_or_list>
=========================
```

**Recommended generated worker-to-expert wrapper (when present):**

```
=== GENERATED EXPERT REQUEST ===
Round: <round_number>
Task: <task_id>

Target Expert:
- <expert_name>

Trigger:
- low_confidence|ambiguity|blocked_by_expert|tradeoff_unclear

Question:
- <single bounded expert question>

Why This Blocks Progress:
- <what cannot proceed without the answer>

Required Output:
- <expected answer shape / tradeoff dimensions / evidence format>

Source Artifacts:
- <artifact_paths>

Non-Goals:
- <out of scope>
================================
```

**Auditor Output (per round):**

```
=== EXPERT INVOCATION AUDIT ===
Round: <round_number>
Task: <task_id>

Invocation Check:
- Expert count: 3/3 ✓
- Triggers valid: ✓
- Cap respected: ✓
- Rationale provided: ✓
- Fast lane gate valid (if requested): ✓

Contract Check:
- ORIGINAL_INTENT: ✓
- DELIVERABLE_THIS_SCOPE: ✓
- DECISION_CLASS: ✓
- EXECUTION_LANE: ✓
- NON_GOALS: ✓
- DONE_WHEN: ✓
- DELETE_BEFORE_ADD_TARGETS: ✓
- PRE_EXEC_DISAGREEMENT_CAPTURE: ✓

Sampling Hook:
- CROSS_JUDGE_SAMPLED: YES|NO
- CROSS_JUDGE_RESULT: CONCUR|DIVERGE|N/A

Findings:
- None

Verdict: PASS
================================
```

---

## 9. Invocation Triggers (Detailed)

### Principal
**Trigger conditions:**
- New system component (>500 LOC)
- Major refactor (>30% of file changed)
- Cross-cutting architectural decision
- Performance/scalability concerns

**NOT triggered by:**
- Routine bug fixes (<50 LOC)
- Minor edits (<10% of file)
- Single-function changes

### System_Eng
**Trigger conditions:**
- Gate integration or modification
- Phase-end handover workflow changes
- Multi-gate orchestration
- New gate creation

**NOT triggered by:**
- Single-script changes
- Business logic updates
- UI changes

### RiskOps
**Trigger conditions:**
- Fail-closed validation logic
- FP rate tracking or dossier criteria
- Infra error handling (exit code 2)
- Promotion criteria changes

**NOT triggered by:**
- Business logic
- UI changes
- General code quality

### QA
**Trigger conditions:**
- New test file creation
- Edge case validation needed
- Test coverage gaps identified
- Complex validation scenarios

**NOT triggered by:**
- Implementation code
- Architecture decisions
- Minor test updates

### DevSecOps
**Trigger conditions:**
- Authentication/authorization changes
- Sensitive data handling (PII, credentials)
- Security vulnerability fixes
- Access control modifications

**NOT triggered by:**
- General code quality
- Performance optimization
- Business logic

### Architect
**Trigger conditions:**
- Module boundary design
- API contract definition
- Component interface design
- Dependency injection patterns

**NOT triggered by:**
- Implementation details
- System-level decisions
- Single-function changes

---

## 10. Anti-Patterns (What NOT to Do)

| Anti-Pattern | Description | Consequence |
|--------------|-------------|-------------|
| **Expert Sprawl** | Calling all 6 experts for simple bug fix | Auditor MEDIUM finding |
| **Duplicate Reviews** | Multiple experts reviewing same code aspect | Auditor MEDIUM finding |
| **Premature Invocation** | Calling experts before problem well-defined | Auditor HIGH finding |
| **Scope Creep** | Expert suggests unrelated improvements | Auditor HIGH finding + HOLD |
| **Analysis Paralysis** | Waiting for expert consensus on trivial decisions | Auditor MEDIUM finding |
| **Missing Critical Expert** | Security issue without devsecops | Auditor HIGH finding |
| **Cap Bypass** | Exceeding 3-expert limit without rationale | Auditor MEDIUM finding + HOLD |
| **Fast Lane Abuse** | Marking non-trivial work as FAST to skip review | Auditor HIGH finding + BLOCK |
| **Add-Before-Delete** | Adding superseding artifacts without delete/deprecate step | Auditor HIGH finding |

---

## 11. Examples

### Example 1: Simple Bug Fix
**Task:** Fix BOM encoding crash in JSON loader
**Experts needed:** 0
**Rationale:** Straightforward fix (<10 LOC), no architectural or risk implications
**Contract:**
- ORIGINAL_INTENT: Fix UTF-8 BOM crash
- DELIVERABLE_THIS_SCOPE: Change encoding="utf-8" to encoding="utf-8-sig"
- NON_GOALS: Refactor JSON loader, add new features
- DONE_WHEN: Tests pass, no BOM crash on real files

### Example 2: New Gate Integration
**Task:** Add G11 auditor gate to phase-end handover
**Experts needed:** 2 (system_eng, riskops)
**Rationale:** Workflow change + fail-closed validation
**Triggers:**
- system_eng: gate_integration
- riskops: fail_closed_logic
**Contract:**
- ORIGINAL_INTENT: Integrate auditor review into phase-end workflow
- DELIVERABLE_THIS_SCOPE: G11 gate in handover script, finalize path for digest
- NON_GOALS: Rewrite entire handover script, add new auditor rules
- DONE_WHEN: G11 gate runs, digest reflects auditor state, tests pass

### Example 3: New Calibration System
**Task:** Implement auditor calibration reporting
**Experts needed:** 3 (principal, riskops, qa)
**Rationale:** New system component with risk and quality implications
**Triggers:**
- principal: new_system_component
- riskops: fp_tracking
- qa: new_test_file
**Contract:**
- ORIGINAL_INTENT: Track FP rate and promotion criteria for auditor
- DELIVERABLE_THIS_SCOPE: Calibration script with weekly/dossier modes, test suite
- NON_GOALS: Rewrite auditor rules, add new gates, redesign FP ledger
- DONE_WHEN: Script runs on real data, 28 tests pass, dossier validates criteria

### Example 4: Security Vulnerability (Exception)
**Task:** Fix SQL injection in query builder
**Experts needed:** 4 (devsecops, qa, architect, riskops) - EXCEPTION APPROVED
**Rationale:** Security critical + API contract change + risk validation
**Triggers:**
- devsecops: security_vuln (priority 1)
- riskops: fail_closed_logic (priority 2)
- architect: api_contract (priority 5)
- qa: edge_case_validation (priority 6)
**Exception:** 4th expert auto-approved (devsecops security critical trigger)
**Applied Cap:** Keep top 4 by priority (devsecops, riskops, architect, qa)
**Contract:**
- ORIGINAL_INTENT: Fix SQL injection vulnerability
- DELIVERABLE_THIS_SCOPE: Parameterized queries, API contract update, validation tests
- NON_GOALS: Rewrite entire query builder, add ORM, migrate database
- DONE_WHEN: Vulnerability fixed, tests pass, security scan clean

---

## 12. Ownership and Review

**Policy Owner:** PM (Product Management)

**Review Triggers:**
- Weekly during shadow window (March 3-17, 2026)
- Monthly post-promotion
- After any KPI threshold breach
- After 3+ escalations in same category

**Update Process:**
1. PM reviews KPI data and escalations
2. PM proposes policy changes in decision log
3. CEO approves changes
4. Policy version incremented
5. Changes communicated to worker and auditor

**Version History:**
- v1.2 (2026-03-05): Added decision class + fast-lane gating, delete-before-add and pre-execution disagreement fields, cross-judge metadata hook
- v1.1 (2026-03-04): Fixed cap/exception contradiction, unsafe override authority, missing per-task limit, KPI reporting claim
- v1.0 (2026-03-04): Initial policy

---

## 13. Enforcement

**Worker Responsibility:**
- Follow invocation algorithm
- Provide paste-ready invocation output
- Fill anti-overengineering contract
- Stay within 3-expert cap or request exception

**Auditor Responsibility:**
- Validate invocation against algorithm
- Check anti-overengineering contract
- Flag violations as findings (MEDIUM or HIGH)
- Track KPIs manually in weekly ops notes (until calibration integration)

**PM Responsibility:**
- Review escalations
- Approve cap exceptions
- Update policy based on KPI data
- Resolve worker-auditor conflicts

**CEO Responsibility:**
- Make final GO/HOLD/REFRAME decisions
- Approve policy changes
- Resolve PM-level escalations
