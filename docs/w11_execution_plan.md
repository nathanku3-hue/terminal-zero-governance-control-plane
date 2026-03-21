# W11 Execution Plan: C3 Closure (March 9-15, 2026)

**Objective:** Collect 12+ items in W11 to close C3 criterion (2 consecutive qualifying weeks)

**Current State:**
- W10: 30 items (qualifying week ✅)
- W11: 0 items (need 10+ to qualify, target 12+ for buffer)
- C3 status: 1/2 consecutive weeks

**Architecture Freeze:** No new gates/scripts/major prompt redesign until promotion decision

**Operations Active:** W11 execution, annotation, reporting, dossier refresh, GO signal refresh

---

## Reference Documents (One-Click Navigation)

**Governance and Process:**
- [Decision Authority Matrix](decision_authority_matrix.md) - Role boundaries, SLAs, override rules
- [Disagreement Runbook](disagreement_runbook.md) - Step-by-step D01-D10 resolution flows
- [Rollback Protocol](rollback_protocol.md) - Trigger matrix, immediate actions, recovery criteria
- [Phase 24C Transition Playbook](phase24c_transition_playbook.md) - C3 → C1 → Canary → Rollout checklists
- [W11 Communication Protocol](w11_comms_protocol.md) - Daily status, checkpoints, escalation templates

**Supporting Documents:**
- [Expert Invocation Policy](expert_invocation_policy.md) - Expert caps, triggers, anti-overengineering
- [Round Contract Template](round_contract_template.md) - ORIGINAL_INTENT, DELIVERABLE, NON_GOALS, DONE_WHEN
- [Disagreement Taxonomy](disagreement_taxonomy.md) - D01-D10 codes, severity, escalation matrix
- [Prompt Quality Rubric](prompt_quality_rubric.md) - 8-dimension scoring, pass bands
- [CEO Weekly Summary Template](templates/ceo_weekly_summary.md) - Executive snapshot format

---

## W11 Day-by-Day Run Card

**Window:** March 9, 2026 to March 15, 2026 (Asia/Macau local dates)

| Date | W11 Cumulative Target | Action |
|---|---:|---|
| March 9 (Mon) | >=2 | Start first shadow cycle and refresh all artifacts |
| March 10 (Tue) | >=4 | Checkpoint 1 (must hit) |
| March 11 (Wed) | >=6 | Maintain cadence; keep annotation 100% |
| March 12 (Thu) | >=8 | Checkpoint 2 (must hit) |
| March 13 (Fri) | >=9 | Buffer day; add extra run if behind |
| March 14 (Sat) | >=10 | Checkpoint 3; C3 likely closes |
| March 15 (Sun) | >=12 | Stretch target and finalize W11 evidence |

---

## Per-Cycle Command Card

**Run every cycle (in order):**

### 1. Enforce Phase-End (Default)
```bash
# Enforce mode is now default (D-184, 2026-03-22)
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot .
```

**For rollback only:** Add `-AuditMode shadow` to revert temporarily.

### 2. Check for C/H Findings
```bash
# Read latest auditor findings
cat docs/context/phase_end_logs/auditor_findings_<run_id>.json
```

### 3. Annotate All C/H Findings (if any)
```bash
# Edit FP ledger to add annotations for each C/H finding
# Maintain 100% coverage (no unannotated C/H findings)
```

### 4. Refresh Weekly Report
```bash
python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_calibration_report.json --output-md docs/context/auditor_calibration_report.md --mode weekly --from-utc 2026-03-03T00:00:00Z
```

### 5. Refresh Dossier
```bash
python scripts/auditor_calibration_report.py --logs-dir docs/context/phase_end_logs --repo-id quant_current_scope --ledger docs/context/auditor_fp_ledger.json --output-json docs/context/auditor_promotion_dossier.json --output-md docs/context/auditor_promotion_dossier.md --mode dossier --min-items 30 --min-items-per-week 10 --min-weeks 2 --max-fp-rate 0.05 --from-utc 2026-03-03T00:00:00Z --to-utc 2026-03-17T00:00:00Z
```

### 6. Refresh GO Signal
```bash
python scripts/generate_ceo_go_signal.py --dossier-json docs/context/auditor_promotion_dossier.json --calibration-json docs/context/auditor_calibration_report.json --context-json docs/context/current_context.json --output docs/context/ceo_go_signal.md
```

### 7. Report Status
```text
=== W11 CYCLE STATUS ===
Date: <YYYY-MM-DD>
Run ID: <run_id>
W11 Items (cumulative): <count>
W11 Target: <checkpoint_target>
C3 Status: <PASS/FAIL>
Annotation Coverage: <XXX%>
FP Rate: <X.XX%>
Next Checkpoint: <date and target>
========================
```

---

## Escalation Triggers (Enforce Strictly)

| Trigger | Action | Owner |
|---------|--------|-------|
| **Annotation coverage <100%** | Stop cycle and repair before reporting | Worker (immediate) |
| **FP rate >5%** | Escalate immediately | Worker → PM → CEO |
| **Any infra error (exit 2)** | Revert to shadow-safe handling and escalate | Worker → PM |
| **W11 items <8 by March 12** | Increase run frequency same day | Worker (immediate) |

**Rollback Trigger:**
- If infra error (exit 2) or FP rate >=5%, revert to shadow immediately and log decision in `docs/decision log.md`

---

## Success Criteria

**C3 Closure:**
- W11 has 10+ items by March 14 (12+ by March 15 for buffer)
- Dossier shows: `c3_min_weeks: {met: true, value: "2 consecutive weeks >= 2"}`
- Dossier exits 0 with `c1_24b_close: {met: true, value: "APPROVED"}` sourced from `D-174`

**Quality Maintained:**
- Annotation coverage: 100% (no unannotated C/H findings)
- FP rate: <5% (target 0%)
- Infra failures: 0 (no exit 2 errors)

---

## Post-C3 Closure (Immediate Next Steps)

### Phase 2: C1 Manual Signoff

**C1 Requirements:**
1. ✅ Bootstrap worker packet replaced (already done)
2. Cross-repo readiness validated
3. One successful enforce-mode dry-run

**C1 Validation Command:**
```bash
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode enforce -EnforceScoreThresholds -CrossRepoRoots "E:\Code\Quant,E:\Code\Film"
```

**C1 Signoff Entry (docs/decision log.md):**
```markdown
### Phase 24C: C1 Manual Signoff
**Date:** <YYYY-MM-DD>
**Status:** APPROVED

**Criteria Validated:**
- Bootstrap worker packet replaced: ✅
- Cross-repo readiness: ✅ (Quant ready, Film/SOP status)
- Enforce dry-run: ✅ (PASS, no false blocks)
- All automated criteria (C0, C2-C5): ✅

**Evidence:**
- Dossier JSON: `docs/context/auditor_promotion_dossier.json` (generated <timestamp>)
- Dry-run ID: <run_id>
- Summary: `docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md`

**PM Signoff:** <name>
**Date:** <YYYY-MM-DD>
**Signature:** <signature>
```

### Phase 3: Canary Enforce (3-5 Runs)

**Objective:** Validate enforce mode with limited blast radius

**Per Canary Run:**
1. Run enforce phase-end
2. Monitor outcome (PASS/BLOCK)
3. If BLOCK: Review findings (TP or FP)
4. Refresh weekly/dossier/GO signal
5. Report status

**Canary Success Criteria:**
- 3-5 enforce runs complete
- FP rate <5%
- No infra failures (exit 2)
- At least 1 PASS run

**Rollback Trigger:**
- If FP rate >=5% or infra error: Revert to shadow, tune rules, retry canary

### Phase 4: Full Enforce Rollout

**Trigger:** Canary successful (FP rate <5%, 3-5 runs complete)

**Actions:**
1. Update default audit mode to enforce
2. Communicate rollout completion
3. Monitor post-rollout (2 weeks)
4. Declare Phase 24C complete

---

## Secondary Work Status

**Completed (Items 1-5):**
- ✅ Expert invocation policy v1.1
- ✅ Round contract template v1.0
- ✅ CEO weekly summary template v1.0
- ✅ Disagreement taxonomy v1.0
- ✅ Prompt quality rubric v1.0 (both prompts scored 16/16 PASS)

**Pending Adoption Evidence:**
- Round contract: Use in live rounds (not yet applied)
- Disagreement taxonomy: Log entries when disagreements occur (none yet)

**Intentionally Deferred:**
- Prompt honing: Rubric is PASS (16/16), no edits needed
- C1 signoff: Not executable until C3 closes
- Canary enforce: Starts only after C3 + C1

**No blocking secondary gaps before W11 start.**

---

## Daily Status Template (Copy/Paste Format)

```text
=== W11 DAY <N> STATUS ===
Date: <YYYY-MM-DD>
Day: <Mon/Tue/Wed/Thu/Fri/Sat/Sun>

Cycles Run Today: <count>
W11 Items (cumulative): <count>
W11 Target: <checkpoint_target>
On Track: YES/NO

C3 Status: <PASS/FAIL>
Annotation Coverage: <XXX%>
FP Rate: <X.XX%>
Infra Errors: <count>

Next Checkpoint: <date and target>
Action Required: <none or specific action>
Escalation: <none or trigger>
===========================
```

---

## GO Signal Received

**Authorization:** Begin W11 execution on March 9, 2026
**No additional approval needed:** Continue W11 cadence autonomously
**Next hard gate:** C3 closure → C1 signoff → Canary enforce

**Status:** Standing by for March 9, 2026 to begin W11 shadow runs.
