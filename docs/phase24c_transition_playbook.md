# Phase 24C Transition Playbook v1.0

**Owner:** PM
**Status:** ACTIVE
**Last Updated:** 2026-03-04

---

## Purpose

Provide step-by-step checklists and pass/fail thresholds for transitioning from C3 closure through C1 verification, canary enforce, and full rollout.

Use this playbook for:
- Validating entry criteria before each phase transition
- Verifying that C1 signoff remains evidenced by `D-174`
- Executing canary enforce with clear success criteria
- Making stop/go decisions for full enforce rollout

---

## Phase Transition Overview

```
Current State: W11 Execution (C3 Closure)
    ↓
Phase 1: C3 Closure Complete (March 14-15, 2026)
    ↓
Phase 2: C1 Manual Signoff (March 15-16, 2026)
    ↓
Phase 3: Canary Enforce (3-5 runs, March 16-18, 2026)
    ↓
Phase 4: Full Enforce Rollout (March 18+, 2026)
```

**Critical Path:** Each phase must complete successfully before proceeding to next phase. No skipping allowed.

---

## Phase 1: C3 Closure Complete

**Objective:** Achieve 2 consecutive qualifying weeks (W10 + W11) with 10+ items each

**Entry Criteria:**
- [ ] W10 has 10+ items (currently: 30 items ✅)
- [ ] W11 has 10+ items (target: 12+ by March 15)
- [ ] Both weeks are consecutive (ISO week numbers differ by 1)
- [ ] All items are annotated (100% coverage)
- [ ] FP rate <5% (target: 0%)

**Validation Steps:**

### Step 1: Verify W11 Item Count
```bash
# After final W11 cycle (March 15)
python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_calibration_report.json --output-md docs/context/auditor_calibration_report.md --mode weekly --from-utc 2026-03-03T00:00:00Z

# Check W11 item count
cat docs/context/auditor_calibration_report.json | grep "w11_items"
# Must be >= 10 (target: >= 12)
```

### Step 2: Verify Consecutive Weeks
```bash
# Check ISO week numbers
cat docs/context/auditor_calibration_report.json | grep "iso_week"
# W10 should be week 10, W11 should be week 11 (consecutive)
```

### Step 3: Verify Annotation Coverage
```bash
# Check annotation coverage
cat docs/context/auditor_promotion_dossier.json | grep "annotation_coverage"
# Must be 1.0 (100%)
```

### Step 4: Verify FP Rate
```bash
# Check FP rate
cat docs/context/auditor_promotion_dossier.json | grep "fp_rate"
# Must be < 0.05 (5%)
```

### Step 5: Run Final Dossier
```bash
python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_promotion_dossier.json --output-md docs/context/auditor_promotion_dossier.md --mode dossier --min-items 30 --min-items-per-week 10 --min-weeks 2 --max-fp-rate 0.05 --from-utc 2026-03-03T00:00:00Z --to-utc 2026-03-17T00:00:00Z

# Check C3 status
cat docs/context/auditor_promotion_dossier.json | grep "c3_min_weeks"
# Must show: "met": true, "value": "2 consecutive weeks >= 10"
```

**Pass Criteria:**
- W11 items >= 10 (target: >= 12)
- W10 and W11 are consecutive ISO weeks
- Annotation coverage = 100%
- FP rate < 5%
- Dossier C3 criterion: `"met": true`

**Fail Criteria:**
- W11 items < 10 → Extend W11 window or start W12
- Annotation coverage < 100% → Repair annotations before proceeding
- FP rate >= 5% → Rollback to shadow, fix FP issues
- W10 and W11 not consecutive → Restart consecutive week count

**Decision Point:**
- If PASS: Proceed to Phase 2 (C1 Manual Signoff)
- If FAIL: Address gaps and retry validation

**Evidence to Preserve:**
- `docs/context/auditor_promotion_dossier.json` (final W11 dossier)
- `docs/context/auditor_calibration_report.json` (final W11 weekly report)
- `docs/context/auditor_fp_ledger.json` (all annotations)
- `docs/context/ceo_go_signal.md` (final GO signal)

---

## Phase 2: C1 Manual Signoff

**Objective:** Validate operational readiness and obtain PM signoff for enforce mode

**Entry Criteria:**
- [ ] C3 closure complete (Phase 1 PASS)
- [ ] All automated criteria met (C0, C2, C3, C4, C4b, C5)
- [ ] Bootstrap worker packet replaced (already done ✅)
- [ ] Cross-repo readiness validated
- [ ] One successful enforce-mode dry-run

**Validation Steps:**

### Step 1: Verify Automated Criteria
```bash
# Check dossier for all automated criteria
cat docs/context/auditor_promotion_dossier.json | grep '"met"'
# C0, C2, C3, C4, C4b, C5 must all show "met": true
```

### Step 2: Validate Cross-Repo Readiness
```bash
# Run cross-repo readiness check
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode shadow -CrossRepoRoots "E:\Code\Quant,E:\Code\Film"

# Check for any HIGH findings across repos
cat docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md | grep "HIGH"
# Should be 0 HIGH findings (or all annotated as TP with mitigation)
```

**Cross-Repo Readiness Checklist:**
- [ ] Quant repo: Shadow run PASS, no HIGH findings
- [ ] Film repo: Shadow run PASS, no HIGH findings (or excluded from enforce)
- [ ] SOP repo: Shadow run PASS, no HIGH findings (or excluded from enforce)
- [ ] All repos use same auditor version (v2.0.0)
- [ ] All repos have FP ledger initialized

### Step 3: Execute Enforce-Mode Dry-Run
```bash
# Run single-repo enforce dry-run (limited scope)
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode enforce -EnforceScoreThresholds

# Check outcome
cat docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md | grep "gate_verdict"
# Should be PASS (no false blocks)
```

**Dry-Run Success Criteria:**
- Enforce run completes without infra errors (exit code 0 or 1, not 2)
- If BLOCK: All findings are true positives (no false blocks)
- If PASS: All gates green, no unexpected findings
- Worker packet validates successfully
- Dossier criteria remain met after enforce run

### Step 4: Collect C1 Evidence
**Required Evidence Links:**
- Dossier JSON: `docs/context/auditor_promotion_dossier.json` (generated <timestamp>)
- Dry-run ID: `<run_id>`
- Dry-run summary: `docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md`
- Cross-repo summary: `docs/context/phase_end_logs/phase_end_handover_summary_<cross_repo_run_id>.md`
- FP ledger: `docs/context/auditor_fp_ledger.json`
- Weekly report: `docs/context/auditor_calibration_report.json`

### Step 5: PM Signoff Entry
**Create entry in `docs/decision log.md`:**

```markdown
### Phase 24C: C1 Manual Signoff
**Date:** <YYYY-MM-DD>
**Status:** APPROVED

**Criteria Validated:**
- Bootstrap worker packet replaced: ✅ (docs/context/worker_reply_packet.json v2.0.0)
- Cross-repo readiness: ✅ (Quant ready, Film/SOP status: <READY|EXCLUDED>)
- Enforce dry-run: ✅ (PASS, no false blocks)
- All automated criteria (C0, C2-C5): ✅

**Evidence:**
- Dossier JSON: `docs/context/auditor_promotion_dossier.json` (generated <timestamp>)
- Dry-run ID: `<run_id>`
- Dry-run summary: `docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md`
- Cross-repo summary: `docs/context/phase_end_logs/phase_end_handover_summary_<cross_repo_run_id>.md`
- FP ledger: `docs/context/auditor_fp_ledger.json` (<count> annotations, 100% coverage)
- Weekly report: `docs/context/auditor_calibration_report.json` (FP rate: <X.XX%>)

**Risk Assessment:**
- FP rate: <X.XX%> (target: <5%)
- Annotation coverage: 100%
- Infra stability: <count> runs, 0 exit 2 errors
- Cross-repo readiness: <READY|PARTIAL>

**PM Signoff:** <name>
**Date:** <YYYY-MM-DD>
**Signature:** <signature>

**Next Phase:** Canary Enforce (3-5 runs, limited blast radius)
```

**Pass Criteria:**
- All automated criteria met (C0, C2, C3, C4, C4b, C5)
- Cross-repo readiness validated (or scope reduced to single repo)
- Enforce dry-run PASS (no false blocks)
- PM reviews evidence and approves

**Fail Criteria:**
- Any automated criterion fails → Return to shadow, address gaps
- Cross-repo readiness fails → Reduce scope or fix failing repos
- Enforce dry-run false block → Tune rules, retry dry-run
- PM denies signoff → Address PM concerns, retry validation

**Decision Point:**
- If PASS: Proceed to Phase 3 (Canary Enforce)
- If FAIL: Address gaps and retry C1 validation

---

## Phase 3: Canary Enforce (3-5 Runs)

**Objective:** Validate enforce mode with limited blast radius before full rollout

**Entry Criteria:**
- [x] C1 manual signoff complete (`D-174` recorded 2026-03-16)
- [ ] PM approval to begin canary enforce
- [ ] Rollback protocol ready (docs/rollback_protocol.md)
- [ ] Escalation paths clear (docs/decision_authority_matrix.md)

**Canary Scope:**
- Single repo only (quant_current_scope)
- 3-5 enforce runs minimum
- Monitor for false blocks and FP rate
- Maintain full refresh discipline (weekly/dossier/GO signal)

**Per Canary Run Checklist:**

### Run N (N = 1 to 5)

#### Step 1: Execute Enforce Run
```bash
# Run enforce phase-end
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode enforce -EnforceScoreThresholds

# Capture run ID
RUN_ID=<run_id>
```

#### Step 2: Monitor Outcome
```bash
# Check gate verdict
cat docs/context/phase_end_logs/phase_end_handover_summary_$RUN_ID.md | grep "gate_verdict"
# PASS or BLOCK
```

**If PASS:**
- No findings or all findings are LOW/MEDIUM (shadowed)
- Worker packet validates successfully
- All gates green
- Continue to Step 3

**If BLOCK:**
- Review all HIGH findings
- Classify each finding as TP (true positive) or FP (false positive)
- If any FP: Annotate in ledger, increment FP count
- If all TP: Worker addresses findings, re-run
- If FP rate >=5%: ROLLBACK to shadow (see rollback_protocol.md)

#### Step 3: Annotate Findings (if any C/H)
```bash
# Edit FP ledger to add annotations for each C/H finding
# Maintain 100% coverage
```

#### Step 4: Refresh Artifacts
```bash
# Refresh weekly report
python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_calibration_report.json --output-md docs/context/auditor_calibration_report.md --mode weekly --from-utc 2026-03-03T00:00:00Z

# Refresh dossier
python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_promotion_dossier.json --output-md docs/context/auditor_promotion_dossier.md --mode dossier --min-items 30 --min-items-per-week 10 --min-weeks 2 --max-fp-rate 0.05 --from-utc 2026-03-03T00:00:00Z --to-utc 2026-03-17T00:00:00Z

# Refresh GO signal
python scripts/generate_ceo_go_signal.py --dossier-json docs/context/auditor_promotion_dossier.json --calibration-json docs/context/auditor_calibration_report.json --context-json docs/context/current_context.json --output docs/context/ceo_go_signal.md
```

#### Step 5: Report Status
```text
=== CANARY RUN N STATUS ===
Date: <YYYY-MM-DD>
Run ID: <run_id>
Outcome: PASS|BLOCK
Findings: <count> (HIGH: <count>, MEDIUM: <count>, LOW: <count>)
FP Count: <count>
FP Rate: <X.XX%>
Annotation Coverage: <XXX%>
Infra Errors: <count>
Next Run: <date>
===========================
```

#### Step 6: Decide Next Action
- If PASS and FP rate <5%: Continue to next canary run
- If BLOCK with TP findings: Worker fixes, re-run same canary number
- If BLOCK with FP findings: Annotate, check FP rate, continue if <5%
- If FP rate >=5%: ROLLBACK to shadow (see rollback_protocol.md)
- If infra error (exit 2): ROLLBACK to shadow (see rollback_protocol.md)

**Canary Success Criteria (After 3-5 Runs):**
- [ ] 3-5 enforce runs complete
- [ ] FP rate <5% across all canary runs
- [ ] No infra failures (exit 2)
- [ ] At least 1 PASS run (no HIGH findings)
- [ ] Annotation coverage maintained at 100%
- [ ] PM reviews canary results and approves rollout

**Canary Fail Criteria:**
- FP rate >=5% → ROLLBACK to shadow, tune rules, retry canary
- Infra error (exit 2) → ROLLBACK to shadow, fix infra, retry canary
- 3+ consecutive BLOCK runs with TP findings → Escalate to PM (quality issue)
- PM denies rollout approval → Address PM concerns, extend canary

**Rollback Trigger:**
```bash
# If FP rate >=5% or infra error:
# 1. Stop canary immediately
# 2. Revert to shadow mode
# 3. Log rollback in decision log
# 4. Tune rules or fix infra
# 5. Retry canary after fixes validated
```

**Decision Point:**
- If PASS: Proceed to Phase 4 (Full Enforce Rollout)
- If FAIL: Rollback to shadow, address issues, retry canary

**Evidence to Preserve:**
- All canary run summaries: `docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md`
- Final dossier after canary: `docs/context/auditor_promotion_dossier.json`
- FP ledger with all canary annotations: `docs/context/auditor_fp_ledger.json`
- Canary summary report (create manually or via script)

---

## Phase 4: Full Enforce Rollout

**Objective:** Enable enforce mode as default and monitor post-rollout stability

**Entry Criteria:**
- [ ] Canary enforce complete (Phase 3 PASS)
- [ ] FP rate <5% sustained across canary runs
- [ ] PM approval for full rollout
- [ ] CEO approval for full rollout (if required)

**Rollout Steps:**

### Step 1: Update Default Audit Mode
**Option A: Update phase-end handover script default**
```powershell
# Edit scripts/phase_end_handover.ps1
# Change default AuditMode from "shadow" to "enforce"
```

**Option B: Update runbook/documentation**
```markdown
# Update docs/w11_execution_plan.md or equivalent
# Change default command from:
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode shadow

# To:
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode enforce -EnforceScoreThresholds
```

### Step 2: Communicate Rollout
**Create rollout announcement in `docs/decision log.md`:**

```markdown
### Phase 24C: Full Enforce Rollout
**Date:** <YYYY-MM-DD>
**Status:** COMPLETE

**Rollout Summary:**
- Canary runs: <count> (all PASS, FP rate <5%)
- Default audit mode: enforce
- Scope: quant_current_scope (single repo)
- Cross-repo: <READY|DEFERRED>

**Evidence:**
- Canary summary: <path>
- Final dossier: `docs/context/auditor_promotion_dossier.json`
- FP rate: <X.XX%> (target: <5%)
- Annotation coverage: 100%

**Monitoring Plan:**
- Duration: 2 weeks (March 18 - April 1, 2026)
- Frequency: Daily FP rate check
- Escalation: If FP rate >=5%, rollback to shadow immediately

**PM Approval:** <name>
**CEO Approval:** <name> (if required)
**Date:** <YYYY-MM-DD>
```

### Step 3: Monitor Post-Rollout (2 Weeks)
**Daily Monitoring Checklist:**
- [ ] Run enforce phase-end
- [ ] Check FP rate (must be <5%)
- [ ] Check annotation coverage (must be 100%)
- [ ] Check infra stability (no exit 2 errors)
- [ ] Report status to PM

**Weekly Monitoring Report:**
```text
=== POST-ROLLOUT WEEK N ===
Week: <YYYY-MM-DD to YYYY-MM-DD>
Enforce Runs: <count>
PASS Runs: <count>
BLOCK Runs: <count>
FP Rate: <X.XX%>
Annotation Coverage: <XXX%>
Infra Errors: <count>
Rollback Events: <count>
Status: STABLE|AT_RISK|ROLLBACK_REQUIRED
===========================
```

### Step 4: Declare Phase 24C Complete
**After 2 weeks of stable enforce mode:**

```markdown
### Phase 24C: Completion Declaration
**Date:** <YYYY-MM-DD>
**Status:** COMPLETE

**Final Metrics:**
- Total enforce runs: <count>
- FP rate: <X.XX%> (target: <5%)
- Annotation coverage: 100%
- Infra stability: <count> runs, 0 exit 2 errors
- Rollback events: <count>

**Achievements:**
- ✅ C0: Infra health (0 exit 2 errors)
- ✅ C1: Manual signoff (PM approved)
- ✅ C2: Evidence volume (30+ items)
- ✅ C3: Consistency (2+ consecutive weeks)
- ✅ C4: Quality rate (FP rate <5%)
- ✅ C4b: Review coverage (100%)
- ✅ C5: Standards compliance (v2.0.0)
- ✅ Canary enforce (3-5 runs, FP rate <5%)
- ✅ Full rollout (2 weeks stable)

**Next Phase:** Phase 25 (TBD) or operational maintenance

**PM Signoff:** <name>
**CEO Signoff:** <name>
**Date:** <YYYY-MM-DD>
```

**Completion Criteria:**
- 2 weeks of enforce mode with FP rate <5%
- No rollback events during monitoring period
- Annotation coverage maintained at 100%
- PM and CEO approve completion

**Fail Criteria:**
- FP rate >=5% during monitoring → Rollback to shadow, extend monitoring
- Infra error (exit 2) → Rollback to shadow, fix infra, extend monitoring
- Rollback event occurs → Restart 2-week monitoring after recovery

---

## Stop/Go Decision Matrix

| Phase | Stop Criteria | Go Criteria | Decision Owner |
|-------|---------------|-------------|----------------|
| **C3 Closure** | W11 <10 items, FP rate >=5%, annotation <100% | W11 >=10 items, FP rate <5%, annotation 100% | Worker → PM |
| **C1 Signoff** | Any automated criterion fails, enforce dry-run false block | All criteria met, dry-run PASS, PM approves | PM |
| **Canary Enforce** | FP rate >=5%, infra error, 3+ consecutive BLOCK | 3-5 runs complete, FP rate <5%, >=1 PASS | PM → CEO |
| **Full Rollout** | FP rate >=5% during monitoring, rollback event | 2 weeks stable, FP rate <5%, PM/CEO approve | CEO |

---

## Paste-Ready Transition Block

```text
=== PHASE TRANSITION ===
From: <C3 Closure|C1 Signoff|Canary Enforce|Full Rollout>
To: <C1 Signoff|Canary Enforce|Full Rollout|Complete>
Date: <YYYY-MM-DD>

Entry Criteria: PASS|FAIL
Evidence: <paths>
Decision: GO|STOP
Owner: <Worker|PM|CEO>
Next Phase: <phase_name>
Expected Completion: <YYYY-MM-DD>
========================
```

---

## Governance Notes

- This playbook is authoritative for phase transitions
- No phase can be skipped (must complete in order: C3 → C1 → Canary → Rollout)
- All evidence must be preserved for audit trail
- PM approval required for C1 signoff and canary start
- CEO approval required for full rollout (or PM with delegation)
- Updates require PM proposal + CEO approval
