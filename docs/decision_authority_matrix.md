# Decision Authority Matrix v1.1

**Owner:** PM
**Status:** ACTIVE
**Last Updated:** 2026-03-07

---

## Purpose

Define clear decision boundaries, response-time SLAs, and override rules to prevent authority conflicts and reduce decision latency.

Use this matrix for:
- Routing decisions to the correct owner
- Setting response-time expectations
- Preventing authority boundary violations
- Resolving escalations with clear paths

---

## Decision Authority by Type

| Decision Type | Owner | Authority Scope | Cannot Be Overridden By | Can Be Overridden By |
|---------------|-------|-----------------|-------------------------|----------------------|
| **Implementation** | Worker | How to solve, which code to write, which tools to use, technical approach | Auditor (can only flag risks) | PM (with rationale), CEO (strategic override) |
| **Scope/Risk Verdict** | Auditor | PASS/BLOCK verdict on scope creep, missing experts, risk gaps, policy violations | Worker (cannot self-override HIGH findings) | PM (with evidence), CEO (final authority) |
| **Dual-Judge Escalation Readiness** | Auditor | Confirm dual-judge evidence before escalation when `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY` | Worker | PM (process override with evidence), CEO (final authority) |
| **Parallel Shard Ownership/Fan-In** | PM | Approve shard plan, enforce non-overlap of `OWNED_FILES`, approve overlap override when justified | Worker, Auditor | CEO (strategic override) |
| **Exception Approval** | PM | Expert cap exceptions, policy overrides, prioritization, resource allocation | Worker, Auditor | CEO (strategic override) |
| **Milestone Expert Lineup** | PM/CEO | Approve milestone domain roster, reentry triggers, and additions when `ROSTER_MISSING` / `UNKNOWN_EXPERT_DOMAIN` is emitted | Worker, Auditor | CEO (final authority) |
| **Strategic Direction** | CEO | GO/HOLD/REFRAME decisions, promotion approval, unresolved escalations, policy changes | Worker, Auditor, PM | None (final authority) |
| **QA Pre-Escalation Verdict** | QA (advisory) | Test coverage analysis, edge case validation, quality findings before CEO escalation | Worker (cannot self-override QA BLOCK without exception) | PM (can approve QA_EXCEPTION_APPROVED with rationale), CEO (final authority) |
| **Socratic Challenge Resolution** | Socratic Investigator (advisory) | Assumption challenges, false confidence detection, pre-execution risk probing | Worker (cannot proceed with 2+ unresolved challenges without exception) | Auditor (escalates if 2+ unresolved), PM (can approve SOCRATIC_EXCEPTION_APPROVED or scope clarification), CEO (final authority) |

**Authority Clarification for QA and Socratic Investigator:**
- Both roles are **advisory** and gate readiness **operationally** but do not have veto authority in the decision authority hierarchy.
- QA findings and Socratic challenges create operational gates (QA_VERDICT=PASS, SOCRATIC_CHALLENGE_RESOLVED=YES) that must be satisfied before CEO escalation.
- PM/CEO can approve exceptions via `QA_EXCEPTION_APPROVED=YES` or `SOCRATIC_EXCEPTION_APPROVED=YES` with explicit rationale to bypass the operational gate while maintaining the advisory authority structure.
- Worker cannot self-override QA BLOCK or proceed with 2+ unresolved Socratic challenges without PM/CEO exception approval.

---

## Advisory Decision-Support Note

- `docs/context/board_decision_brief_latest.*` is a decision-support artifact, not a new authority type.
- PM may use it to frame top-level options, tradeoffs, and a recommended path for CEO review.
- Any CTO/COO/expert content inside the brief is analytic input only and cannot approve, veto, or overrule.
- CEO remains the final authority for strategic direction and all GO/HOLD/REFRAME outcomes.
- `BOARD_LINEUP_REVIEW_REQUIRED` indicates board reentry timing for lineup quality only; it does not grant new veto authority to advisory artifacts.

---

## Response-Time SLAs

| Severity | Meaning | Worker Response | Auditor Response | PM Response | CEO Response |
|----------|---------|-----------------|------------------|-------------|--------------|
| **HIGH** | Could create false GO/HOLD, policy breach, quality failure, or infra risk | Same day (within 8 hours) | Same day (within 4 hours) | Same day (within 8 hours) | Within 24 hours |
| **MEDIUM** | Could delay completion or cause rework | 1 business day | 1 business day | 1 business day | Within 2 business days |
| **LOW** | Preference mismatch; no delivery risk | Next round | Next round | Next round | Next weekly review |

**SLA Breach Escalation:**
- If Worker/Auditor misses SLA: Escalate to PM
- If PM misses SLA: Escalate to CEO
- If CEO misses SLA: Log in decision log, continue with best available information

---

## Explicit "Cannot Override" Lines

### 1. Worker Cannot Self-Override Auditor HIGH Findings

**Rule:** Worker cannot mark HIGH findings as resolved without PM/CEO approval.

**Rationale:** HIGH findings indicate policy breach, quality failure, or infra risk. Self-override would bypass quality gates.

**Process:**
1. Auditor flags HIGH finding
2. Worker provides evidence or fixes issue
3. Auditor re-reviews and updates verdict
4. If still HIGH and Worker disagrees: Escalate to PM
5. PM reviews evidence and makes final call (or escalates to CEO)

**Example:**
- Auditor: "Missing devsecops expert for auth change (HIGH)"
- Worker: "I believe auth change is minor, no expert needed"
- **BLOCKED:** Worker cannot self-override
- **REQUIRED:** Escalate to PM with evidence (code diff, risk assessment)
- PM decides: Add devsecops or downgrade finding to MEDIUM with rationale

### 2. CEO/PM Strategic Override Requires Evidence References

**Rule:** CEO/PM cannot override Auditor verdict without citing specific evidence.

**Rationale:** Prevents arbitrary overrides that bypass quality gates. Maintains audit trail.

**Required Evidence:**
- Code diffs showing risk is mitigated
- Test results showing coverage is adequate
- Expert review confirming approach is sound
- Risk assessment showing impact is acceptable

**Process:**
1. Auditor blocks with HIGH finding
2. Worker provides counter-evidence
3. PM/CEO reviews both positions
4. If overriding Auditor: Must cite specific evidence in decision log
5. Log entry must include: finding_id, override_rationale, evidence_refs, owner, timestamp

**Example:**
- Auditor: "Test coverage insufficient (HIGH)"
- Worker: "Coverage is 85%, meets project standard"
- PM override: "Approved based on: (1) 85% coverage exceeds 80% threshold, (2) critical paths tested, (3) QA expert reviewed. Evidence: tests/test_*.py, docs/qa_review.md"

### 3. Auditor Cannot Change Implementation Decisions

**Rule:** Auditor can flag risks but cannot dictate technical approach.

**Rationale:** Worker owns implementation. Auditor validates scope/risk, not technical choices.

**Auditor CAN:**
- Flag missing experts (e.g., "Missing riskops for fail-closed logic")
- Flag scope creep (e.g., "Deliverable exceeds ORIGINAL_INTENT")
- Flag risk gaps (e.g., "No error handling for infra failure")
- Flag policy violations (e.g., "Expert cap exceeded without rationale")

**Auditor CANNOT:**
- Dictate which library to use
- Require specific code patterns
- Mandate refactoring approach
- Override Worker's technical judgment on "how"

**Example:**
- Worker: "Using JSON for config storage"
- Auditor: "Must use YAML instead" ❌ **OUT OF SCOPE**
- Auditor: "Missing validation for malformed JSON (risk gap)" ✅ **IN SCOPE**

### 4. PM Cannot Override CEO Strategic Decisions

**Rule:** PM can recommend, but CEO has final authority on GO/HOLD/REFRAME.

**Rationale:** CEO owns strategic direction and promotion decisions.

**PM Authority:**
- Approve expert cap exceptions
- Resolve Worker-Auditor disputes
- Prioritize work
- Approve policy changes (subject to CEO review)

**CEO Authority:**
- Final GO/HOLD/REFRAME decision
- Promotion approval (shadow → enforce)
- Unresolved escalations
- Strategic direction changes

**Process:**
1. PM reviews dossier and makes recommendation
2. CEO reviews PM recommendation and artifacts
3. CEO makes final decision
4. If PM disagrees: Can log dissent in decision log, but CEO decision stands

### 5. No Shard File Overlap Without PM Override

**Rule:** Active shards cannot overlap `OWNED_FILES` unless PM records explicit override.

**Rationale:** Overlapping ownership introduces merge risk and invalidates independent shard evidence.

**Process:**
1. Worker declares `OWNED_FILES` and `PARALLEL_SHARD_ID`
2. Auditor checks overlap against active shards
3. If overlap found: block fan-in unless PM override is logged with rationale and evidence
4. If PM override granted: continue with heightened review and explicit fan-in checkpoint

---

## Decision Routing Matrix

| Scenario | First Owner | Escalation Path | Final Authority |
|----------|-------------|-----------------|-----------------|
| Implementation approach dispute | Worker | PM (if Auditor flags risk) | CEO (if unresolved) |
| Auditor HIGH finding | Auditor | PM (if Worker disputes) | CEO (if PM cannot resolve) |
| Expert cap exception request | Worker | PM (approval required) | CEO (if PM denies and Worker escalates) |
| Scope creep detected | Auditor | Worker (to fix) → PM (if unresolved) | CEO (if PM cannot resolve) |
| FP rate >5% | Auditor | PM (immediate) | CEO (strategic decision) |
| Infra error (exit 2) | Worker | PM (immediate) | CEO (if rollback needed) |
| Annotation coverage <100% | Worker | PM (if not fixed same day) | CEO (if pattern repeats) |
| `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY` and no dual-judge evidence | Auditor | PM (process override review) | CEO (if escalation disputed) |
| Parallel shard overlap in `OWNED_FILES` | Auditor | PM (override or re-shard) | CEO (if PM/Worker deadlock) |
| Fan-in requested with shard evidence gap | Auditor | Worker (close gap) → PM (if blocked) | CEO (if unresolved) |
| Premature promotion attempt | Auditor | CEO (immediate) | CEO (final authority) |
| Policy violation | Auditor | PM (exception approval) | CEO (if PM cannot resolve) |
| Cross-role authority conflict | PM | CEO (immediate) | CEO (final authority) |
| Top-level tradeoff framing via `board_decision_brief_latest.*` | PM | CEO review | CEO (final authority) |

---

## Override Documentation Requirements

**All overrides must be logged in `docs/decision log.md` with:**

```markdown
### Override: <Decision Type>
**Date:** <YYYY-MM-DD>
**Override By:** <Role/Name>
**Original Decision:** <Worker/Auditor/PM position>
**Override Rationale:** <One-sentence reason>
**Evidence References:**
- <path/to/evidence1>
- <path/to/evidence2>
**Risk Assessment:** <One-sentence impact statement>
**Approval:** <CEO/PM signature if required>
```

**Required Approvals:**
- Worker override of MEDIUM finding: PM approval
- Worker override of HIGH finding: PM approval with evidence; CEO approval required when escalation changes strategic GO/HOLD/REFRAME path
- PM override of Auditor verdict: Evidence references required
- CEO override of any decision: No approval required, but rationale must be logged

---

## Paste-Ready Decision Routing Block

```text
=== DECISION ROUTING ===
Scenario: <description>
Severity: HIGH|MEDIUM|LOW
First Owner: Worker|Auditor|PM|CEO
SLA: <timeframe>
Escalation Path: <role1> → <role2> → <role3>
Final Authority: <role>
Required Evidence: <list>
Override Allowed: YES|NO
Override Requires: <PM_APPROVAL|CEO_APPROVAL|EVIDENCE_REFS>
========================
```

---

## Authority Conflict Resolution

**If two roles claim authority over the same decision:**

1. **Check this matrix first** - Most conflicts are already defined
2. **If not in matrix:** Escalate to PM for clarification
3. **If PM cannot resolve:** Escalate to CEO for final ruling
4. **Log resolution:** Add to this matrix for future reference
5. **Update matrix:** PM updates matrix with CEO-approved ruling

**Conflict Resolution SLA:** Same day for HIGH severity, 1 business day for MEDIUM/LOW

---

## Weekly Review

**PM reviews weekly:**
1. Override count by type (target: <5 per week)
2. SLA breach count (target: 0)
3. Authority conflicts (target: 0)
4. Escalation patterns (identify recurring issues)

**Triggers for matrix update:**
- 3+ authority conflicts on same decision type
- 5+ overrides in same category in 7 days
- SLA breach rate >10%
- CEO requests clarification

---

## Governance Notes

- This matrix is authoritative for decision routing
- Conflicts between this matrix and other docs: This matrix wins
- Updates require PM proposal + CEO approval
- Version incremented on each update
- Changes communicated to all roles within 24 hours
