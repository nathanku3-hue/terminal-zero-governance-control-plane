# Rollback Protocol v1.0

**Owner:** PM
**Status:** ACTIVE
**Last Updated:** 2026-03-04

---

## Purpose

Define clear triggers, immediate actions, and recovery criteria for reverting to shadow mode when quality or infra risks are detected.

Use this protocol for:
- Detecting rollback triggers during W11 execution or canary enforce
- Taking immediate safety actions by role
- Reverting to shadow mode with minimal disruption
- Re-entering normal flow after recovery

---

## Rollback Trigger Matrix

| Trigger | Severity | Immediate Action | Owner | Rollback Required |
|---------|----------|------------------|-------|-------------------|
| **Infra error (exit 2)** | CRITICAL | Stop execution, log error, revert to shadow | Worker → PM | YES (immediate) |
| **FP rate >=5%** | CRITICAL | Stop execution, review findings, revert to shadow | Worker → PM → CEO | YES (immediate) |
| **Annotation coverage <100%** | HIGH | Stop cycle, repair annotations, do not report | Worker | NO (repair in place) |
| **Data-volume checkpoint miss** | MEDIUM | Increase run frequency, escalate if pattern | Worker → PM | NO (adjust cadence) |
| **Repeated HIGH findings (3+ same code)** | MEDIUM | Review root cause, escalate to PM | Worker → PM | NO (fix root cause) |
| **Dossier validation failure** | HIGH | Stop reporting, fix validation, re-run dossier | Worker → PM | NO (fix validation) |
| **Cross-repo enforce failure** | HIGH | Revert to single-repo enforce, escalate | Worker → PM → CEO | YES (scope reduction) |

---

## Trigger 1: Infra Error (Exit 2)

**Definition:** Phase-end handover script exits with code 2 (infrastructure failure, not policy violation)

**Severity:** CRITICAL

**Detection:**
```bash
# After running phase-end handover
echo $?
# If exit code is 2: INFRA ERROR
```

**Immediate Actions (within 1 hour):**

### Worker Actions
1. **Stop execution immediately** - Do not run additional cycles
2. **Capture error context:**
   ```bash
   # Read latest phase-end summary
   cat docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md

   # Check for exit code 2 indicators
   grep "exit_code: 2" docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md
   ```
3. **Log error in decision log:**
   ```markdown
   ### Rollback: Infra Error (Exit 2)
   **Date:** <YYYY-MM-DD HH:MM UTC>
   **Run ID:** <run_id>
   **Error:** <one-line description>
   **Evidence:** docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md
   **Action:** Reverted to shadow mode, escalated to PM
   ```
4. **Escalate to PM** with error context

### PM Actions (within 2 hours)
1. **Review error context** - Determine if infra issue or script bug
2. **Assess blast radius** - Check if other repos affected
3. **Decide recovery path:**
   - Option A: Fix infra issue (e.g., missing file, permission error) and resume
   - Option B: Fix script bug and resume
   - Option C: Escalate to CEO if systemic issue
4. **Communicate decision** to Worker and CEO

### CEO Actions (if escalated)
1. **Review PM assessment**
2. **Approve recovery plan or HOLD promotion**
3. **If HOLD:** Set recovery criteria and timeline

**Rollback Command:**
```bash
# No explicit rollback needed - shadow mode is default
# Simply do not run enforce mode until issue is resolved
```

**Recovery Criteria:**
- Infra issue fixed and verified
- Script bug fixed and tested
- One successful shadow run completes without exit 2
- PM approves resumption

---

## Trigger 2: FP Rate >=5%

**Definition:** False positive rate (FP findings / total C/H findings) reaches or exceeds 5%

**Severity:** CRITICAL

**Detection:**
```bash
# After refreshing dossier
cat docs/context/auditor_promotion_dossier.json | grep "fp_rate"
# If fp_rate >= 0.05: ROLLBACK TRIGGER
```

**Immediate Actions (within 4 hours):**

### Worker Actions
1. **Stop execution immediately** - Do not run additional cycles
2. **Review all FP annotations:**
   ```bash
   # Check FP ledger for recent FP verdicts
   cat docs/context/auditor_fp_ledger.json | grep '"verdict": "FP"'
   ```
3. **Identify FP pattern:**
   - Which auditor rule is triggering FPs? (AUD-R000 through AUD-R009)
   - Is it a rule bug or annotation error?
   - Are FPs concentrated in one run or spread across multiple runs?
4. **Log rollback in decision log:**
   ```markdown
   ### Rollback: FP Rate >=5%
   **Date:** <YYYY-MM-DD HH:MM UTC>
   **FP Rate:** <X.XX%>
   **FP Count:** <count>
   **Total C/H:** <count>
   **Pattern:** <rule_id or description>
   **Evidence:** docs/context/auditor_fp_ledger.json, docs/context/auditor_promotion_dossier.json
   **Action:** Reverted to shadow mode, escalated to PM
   ```
5. **Escalate to PM** with FP analysis

### PM Actions (within 4 hours)
1. **Review FP pattern** - Determine root cause
2. **Assess options:**
   - Option A: Annotation error (Worker misclassified TP as FP) → Fix annotations, re-run dossier
   - Option B: Rule bug (Auditor rule is too strict) → Tune rule, re-run calibration
   - Option C: Systemic issue (Auditor design flaw) → Escalate to CEO, may require REFRAME
3. **Decide recovery path:**
   - If annotation error: Worker fixes, PM approves, resume shadow
   - If rule bug: PM tunes rule, tests on historical data, resume shadow
   - If systemic: Escalate to CEO for strategic decision
4. **Communicate decision** to Worker and CEO

### CEO Actions (if escalated)
1. **Review PM assessment and FP analysis**
2. **Decide strategic path:**
   - GO: Approve PM recovery plan and resume shadow
   - HOLD: Pause promotion until FP rate <5% sustained for 2+ weeks
   - REFRAME: Redesign auditor rules (requires architecture change, breaks freeze)
3. **If REFRAME:** Set new timeline and criteria

**Rollback Command:**
```bash
# No explicit rollback needed - shadow mode is default
# Do not proceed to enforce mode until FP rate <5%
```

**Recovery Criteria:**
- FP rate <5% after fixes
- At least 10 new items reviewed post-fix with FP rate <5%
- PM approves resumption
- If rule was tuned: All historical data re-validated with new rule

---

## Trigger 3: Annotation Coverage <100%

**Definition:** Not all C/H findings have annotations in FP ledger

**Severity:** HIGH (not CRITICAL - can be repaired in place)

**Detection:**
```bash
# After refreshing dossier
cat docs/context/auditor_promotion_dossier.json | grep "annotation_coverage"
# If annotation_coverage < 1.0: REPAIR REQUIRED
```

**Immediate Actions (within 2 hours):**

### Worker Actions
1. **Stop cycle** - Do not report status or refresh artifacts until fixed
2. **Identify unannotated findings:**
   ```bash
   # Compare C/H findings to FP ledger annotations
   # Find findings without matching annotations
   ```
3. **Annotate all missing findings:**
   - Review each C/H finding
   - Classify as TP or FP with rationale
   - Add annotation to FP ledger
4. **Re-run dossier:**
   ```bash
   python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_promotion_dossier.json --output-md docs/context/auditor_promotion_dossier.md --mode dossier --min-items 30 --min-items-per-week 10 --min-weeks 2 --max-fp-rate 0.05 --from-utc 2026-03-03T00:00:00Z --to-utc 2026-03-17T00:00:00Z
   ```
5. **Verify coverage is 100%:**
   ```bash
   cat docs/context/auditor_promotion_dossier.json | grep "annotation_coverage"
   # Must be 1.0 (100%)
   ```
6. **Resume cycle** - Refresh artifacts and report status

**No Rollback Required** - This is a repair-in-place issue, not a quality failure

**Escalation Trigger:**
- If coverage <100% repeats 3+ times: Escalate to PM (Worker discipline issue)
- If Worker cannot identify unannotated findings: Escalate to PM (tooling issue)

**Recovery Criteria:**
- Annotation coverage = 100%
- All C/H findings have TP/FP verdict in ledger
- Dossier validates successfully

---

## Trigger 4: Data-Volume Checkpoint Miss

**Definition:** W11 cumulative items fall below checkpoint target (e.g., <4 by March 10, <8 by March 12)

**Severity:** MEDIUM

**Detection:**
```bash
# After each cycle, check W11 cumulative items
cat docs/context/auditor_calibration_report.json | grep "w11_items"
# Compare to checkpoint target from W11 execution plan
```

**Immediate Actions (same day):**

### Worker Actions
1. **Assess gap:**
   - Current W11 items: <count>
   - Checkpoint target: <count>
   - Gap: <count>
   - Days remaining to checkpoint: <count>
2. **Increase run frequency:**
   - If gap <=2 items: Add 1 extra cycle same day
   - If gap >2 items: Add 2 extra cycles same day
   - If gap >4 items: Escalate to PM (may need to extend window)
3. **Log checkpoint miss in decision log:**
   ```markdown
   ### Checkpoint Miss: W11 Volume
   **Date:** <YYYY-MM-DD>
   **Checkpoint:** <March 10/12/14>
   **Target:** <count> items
   **Actual:** <count> items
   **Gap:** <count> items
   **Action:** Increased run frequency to <count> cycles/day
   **Next Checkpoint:** <date and target>
   ```
4. **Execute extra cycles** and report status

**No Rollback Required** - This is a cadence adjustment, not a quality failure

**Escalation Trigger:**
- If gap >4 items: Escalate to PM (may need to extend W11 window)
- If checkpoint miss repeats at next checkpoint: Escalate to PM (systemic issue)

**Recovery Criteria:**
- W11 items back on track for next checkpoint
- Increased cadence sustained until checkpoint met

---

## Trigger 5: Repeated HIGH Findings (Same Code)

**Definition:** Same HIGH finding code (e.g., AUD-R003) appears 3+ times in 7 days

**Severity:** MEDIUM

**Detection:**
```bash
# Review recent auditor findings
cat docs/context/phase_end_logs/auditor_findings_*.json | grep '"severity": "HIGH"'
# Count occurrences of same rule_id
```

**Immediate Actions (within 1 business day):**

### Worker Actions
1. **Identify pattern:**
   - Which rule is triggering repeatedly? (AUD-R000 through AUD-R009)
   - What is the root cause? (Worker error, rule too strict, systemic issue)
2. **Review root cause:**
   - If Worker error: Fix process to prevent recurrence
   - If rule too strict: Escalate to PM for rule tuning
   - If systemic: Escalate to PM for strategic review
3. **Log pattern in decision log:**
   ```markdown
   ### Repeated HIGH Findings
   **Date:** <YYYY-MM-DD>
   **Rule:** <AUD-R00X>
   **Occurrences:** <count> in 7 days
   **Root Cause:** <Worker error|Rule too strict|Systemic>
   **Action:** <Fixed process|Escalated to PM>
   ```
4. **Escalate to PM** with root cause analysis

### PM Actions (within 1 business day)
1. **Review pattern and root cause**
2. **Decide action:**
   - If Worker error: Coach Worker, monitor for improvement
   - If rule too strict: Tune rule (requires testing on historical data)
   - If systemic: Escalate to CEO for strategic decision
3. **Communicate decision** to Worker and CEO

**No Rollback Required** - This is a quality improvement issue, not a safety failure

**Recovery Criteria:**
- Root cause addressed
- No recurrence of same HIGH finding for 7 days
- PM approves resumption of normal cadence

---

## Trigger 6: Dossier Validation Failure

**Definition:** Dossier script exits with error (not criteria failure, but validation error)

**Severity:** HIGH

**Detection:**
```bash
# After running dossier script
echo $?
# If exit code != 0 and not criteria failure: VALIDATION ERROR
```

**Immediate Actions (within 2 hours):**

### Worker Actions
1. **Stop reporting** - Do not refresh GO signal or report status until fixed
2. **Capture validation error:**
   ```bash
   # Read dossier script output
   python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_promotion_dossier.json --output-md docs/context/auditor_promotion_dossier.md --mode dossier --min-items 30 --min-items-per-week 10 --min-weeks 2 --max-fp-rate 0.05 --from-utc 2026-03-03T00:00:00Z --to-utc 2026-03-17T00:00:00Z 2>&1 | tee dossier_error.log
   ```
3. **Identify root cause:**
   - Schema error (FP ledger, findings JSON)
   - Data error (missing run, corrupt file)
   - Script bug (logic error, edge case)
4. **Fix validation error:**
   - If schema error: Fix FP ledger or findings JSON
   - If data error: Regenerate missing data
   - If script bug: Escalate to PM (may require code fix)
5. **Re-run dossier** and verify success
6. **Resume reporting** after validation passes

**No Rollback Required** - This is a data quality issue, not a safety failure

**Escalation Trigger:**
- If validation error is script bug: Escalate to PM (code fix required)
- If validation error repeats: Escalate to PM (systemic data quality issue)

**Recovery Criteria:**
- Dossier script exits 0 (success)
- Dossier JSON is valid and complete
- All criteria are evaluated (may still fail, but validation passes)

---

## Trigger 7: Cross-Repo Enforce Failure

**Definition:** Enforce mode fails on cross-repo validation (Quant, Film, SOP)

**Severity:** HIGH

**Detection:**
```bash
# After running cross-repo enforce dry-run
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode enforce -EnforceScoreThresholds -CrossRepoRoots "E:\Code\Quant,E:\Code\Film"
# If any repo fails with HIGH findings: CROSS-REPO FAILURE
```

**Immediate Actions (within 4 hours):**

### Worker Actions
1. **Stop cross-repo enforce** - Revert to single-repo enforce
2. **Identify failing repo:**
   - Which repo failed? (Quant, Film, SOP)
   - What was the failure? (HIGH finding, infra error, validation error)
3. **Log failure in decision log:**
   ```markdown
   ### Rollback: Cross-Repo Enforce Failure
   **Date:** <YYYY-MM-DD HH:MM UTC>
   **Failing Repo:** <Quant|Film|SOP>
   **Failure Type:** <HIGH finding|Infra error|Validation error>
   **Evidence:** docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md
   **Action:** Reverted to single-repo enforce, escalated to PM
   ```
4. **Escalate to PM** with failure analysis

### PM Actions (within 4 hours)
1. **Review failure analysis**
2. **Assess options:**
   - Option A: Fix failing repo (Worker addresses HIGH findings)
   - Option B: Exclude failing repo from enforce (reduce scope)
   - Option C: Escalate to CEO (strategic decision on cross-repo readiness)
3. **Decide recovery path:**
   - If fixable: Worker addresses findings, retry cross-repo enforce
   - If not ready: Exclude failing repo, proceed with single-repo enforce
   - If systemic: Escalate to CEO for strategic decision
4. **Communicate decision** to Worker and CEO

### CEO Actions (if escalated)
1. **Review PM assessment and failure analysis**
2. **Decide strategic path:**
   - GO: Approve single-repo enforce, defer cross-repo to future phase
   - HOLD: Pause enforce until all repos ready
   - REFRAME: Redesign cross-repo strategy
3. **Set recovery criteria and timeline**

**Rollback Command:**
```bash
# Revert to single-repo enforce
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode enforce -EnforceScoreThresholds
# Do not use -CrossRepoRoots until failure is resolved
```

**Recovery Criteria:**
- Failing repo addresses HIGH findings
- Cross-repo enforce dry-run passes on all repos
- PM approves cross-repo enforce resumption

---

## Revert to Shadow Command Path

**When rollback is required (Triggers 1, 2, 7):**

### Step 1: Stop Current Mode
```bash
# No explicit stop needed - simply do not run enforce mode
```

### Step 2: Revert to Shadow
```bash
# Run shadow mode (default, no special flags)
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode shadow
```

### Step 3: Log Rollback Decision
```markdown
### Rollback Decision
**Date:** <YYYY-MM-DD HH:MM UTC>
**Trigger:** <Infra error|FP rate >=5%|Cross-repo failure>
**Run ID:** <run_id>
**Evidence:** <paths>
**Decision:** Reverted to shadow mode
**Owner:** <Worker|PM|CEO>
**Recovery Criteria:** <list>
**Expected Recovery Date:** <YYYY-MM-DD>
```

### Step 4: Communicate Rollback
- Worker notifies PM immediately
- PM notifies CEO within 4 hours
- CEO reviews and approves recovery plan

---

## Recovery Criteria (Re-Enter Normal Flow)

**After rollback, to resume normal flow:**

### For Infra Error (Exit 2)
- [ ] Infra issue fixed and verified
- [ ] Script bug fixed and tested (if applicable)
- [ ] One successful shadow run completes without exit 2
- [ ] PM approves resumption

### For FP Rate >=5%
- [ ] FP rate <5% after fixes
- [ ] At least 10 new items reviewed post-fix with FP rate <5%
- [ ] If rule was tuned: All historical data re-validated with new rule
- [ ] PM approves resumption

### For Cross-Repo Enforce Failure
- [ ] Failing repo addresses HIGH findings
- [ ] Cross-repo enforce dry-run passes on all repos
- [ ] PM approves cross-repo enforce resumption

**General Recovery Checklist:**
- [ ] Root cause identified and documented
- [ ] Fix implemented and tested
- [ ] Evidence of fix provided (test results, logs, artifacts)
- [ ] PM reviews and approves recovery plan
- [ ] CEO approves if strategic decision required
- [ ] Rollback decision logged in decision log
- [ ] Recovery criteria met and verified

---

## Paste-Ready Rollback Block

```text
=== ROLLBACK EXECUTED ===
Date: <YYYY-MM-DD HH:MM UTC>
Trigger: <Infra error|FP rate >=5%|Annotation <100%|Checkpoint miss|Repeated HIGH|Dossier validation|Cross-repo failure>
Severity: CRITICAL|HIGH|MEDIUM
Run ID: <run_id>
Evidence: <paths>
Immediate Action: <description>
Owner: <Worker|PM|CEO>
Escalated To: <PM|CEO|None>
Rollback Required: YES|NO
Recovery Criteria: <list>
Expected Recovery: <YYYY-MM-DD>
===========================
```

---

## Weekly Rollback Review

**PM tracks and reports weekly:**
1. Rollback count by trigger (target: 0)
2. Recovery time (trigger to resumption) (target: <24 hours)
3. Rollback patterns (identify systemic issues)
4. False rollbacks (trigger fired but rollback not needed) (target: 0)

**Triggers for protocol update:**
- New rollback trigger identified
- Recovery criteria prove insufficient
- Rollback rate >1 per week

---

## Governance Notes

- This protocol is authoritative for rollback decisions
- Conflicts between this protocol and other docs: This protocol wins for safety decisions
- Updates require PM proposal + CEO approval
- Version incremented on each update
