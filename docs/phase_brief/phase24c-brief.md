# Phase 24C: Auditor Calibration & Shadow-to-Enforce Promotion

## Scope

Implement independent auditor review system with false-positive calibration and promotion dossier to validate shadow-to-enforce transition.

**Core Components:**
- Auditor rules engine (AUD-R000 through AUD-R009)
- False-positive ledger and annotation workflow
- Calibration reporting (weekly and dossier modes)
- Shadow-to-enforce promotion criteria (C0-C5)

## Objectives

1. Implement 7 auditor rules for worker reply packet quality review
2. Establish FP ledger schema and 100% annotation workflow for C/H findings
3. Execute 2-week shadow calibration window (2026-03-03 to 2026-03-17)
4. Validate promotion criteria through automated dossier reporting
5. Transition to enforce mode after dossier approval and manual signoff

## Acceptance Criteria

### C0: Infrastructure Health
- **Threshold:** 0 infra failures
- **Definition:** Zero exit code 2 failures (script crashes, invalid JSON, missing files)
- **Rationale:** Infra errors block regardless of mode; broken tooling must never hide behind shadow mode

### C1: Phase 24B Operational Close (MANUAL)
- **Threshold:** PM signoff required
- **Requirements:**
  - Bootstrap worker packet replaced with real execution evidence
  - Cross-repo readiness validated (Quant, Film, SOP)
  - One successful enforce-mode dry-run completed without false blocks
- **Rationale:** Manual gate ensures operational readiness beyond automated metrics

### C2: Minimum Items Reviewed
- **Threshold:** ≥30 items total across shadow window
- **Definition:** Sum of `items_reviewed` from all shadow run summaries
- **Rationale:** Statistical significance for FP rate measurement

### C3: Consecutive Weeks
- **Threshold:** ≥2 consecutive ISO weeks with ≥10 items each
- **Definition:** Longest consecutive run of qualifying weeks (not total qualifying weeks)
- **Rationale:** Sustained operational cadence, not sporadic bursts

### C4: False-Positive Rate
- **Threshold:** <5%
- **Definition:** (FP count / C+H total) among annotated findings
- **Rationale:** Acceptable false-block rate for enforce mode

### C4b: Annotation Coverage
- **Threshold:** 100% (strict)
- **Definition:** All C/H findings must have TP or FP verdict in ledger
- **Rationale:** Cannot measure FP rate without complete annotation

### C5: Schema Version
- **Threshold:** All packets v2.0.0
- **Definition:** All reviewed packets use `schema_version: "2.0.0"`
- **Rationale:** v1 packets lack v2 fields required for auditor checks

## Evidence Requirements

**Operational Artifacts:**
- `docs/context/auditor_fp_ledger.json` - FP annotations with 100% C/H coverage
- `docs/context/auditor_calibration_report.md` - Weekly calibration report
- `docs/context/auditor_promotion_dossier.md` - Dossier validation report

**Test Evidence:**
- 51 tests passing (23 auditor + 28 calibration)
- Zero regressions in existing test suite

**Traceability:**
- PM-24C-001 through PM-24C-007 mapped in `pm_to_code_traceability.yaml`
- Decision log entries D-117 through D-126

## Deliverables

1. **Auditor Rules Implementation** (7 rules)
   - AUD-R000: v1 packet detection (HIGH severity)
   - AUD-R001: Low confidence detection (CRITICAL if <0.70)
   - AUD-R002: Problem-solving alignment (CRITICAL if <0.75)
   - AUD-R003: Expertise coverage validation
   - AUD-R004: Citation quality checks
   - AUD-R008: DoD result reporting (MEDIUM for FAIL)
   - AUD-R009: Open risks validation

2. **Calibration Reporting Scripts**
   - `scripts/auditor_calibration_report.py` (weekly/dossier modes)
   - `scripts/run_auditor_review.py` (shadow/enforce modes)

3. **FP Ledger Schema and Workflow**
   - Composite key: (repo_id, run_id, finding_id)
   - Verdicts: TP (true positive) or FP (false positive)
   - Provenance: annotated_by, annotated_at_utc

4. **2-Week Shadow Window Execution**
   - Weekly shadow cycles on active repos
   - 100% C/H annotation after each run
   - Weekly report regeneration

5. **Promotion Dossier Validation**
   - Automated C0, C2-C5 validation
   - Manual C1 signoff in decision log
   - Exit 0 = ready for enforce, Exit 1 = criteria not met

6. **Canary Enforce Cycles** (3-5 runs)
   - Limited scope enforce runs before full rollout
   - Validate no false blocks in production

7. **Full Enforce Rollout**
   - Enable enforce mode in phase-end handover
   - Monitor FP rate <5% sustained

## Dependencies

**Phase 24B Operational Close:**
- Real worker packet (not bootstrap placeholder)
- Cross-repo validation complete
- Enforce dry-run successful

**Worker Reply Packet v2.0.0:**
- Schema includes machine_optimized block
- Schema includes pm_first_principles block
- All packets migrated from v1

**Phase-End Handover Gates:**
- G00-G11 operational
- G11 auditor gate integrated
- G09b/G10b finalize path working

## Risks and Mitigations

**Risk:** Insufficient shadow data (C2/C3 not met)
- **Mitigation:** 2-week window with weekly cadence ensures 30+ items across 2+ weeks

**Risk:** High FP rate (C4 >=5%)
- **Mitigation:** Rule tuning during shadow window; can extend window if needed

**Risk:** Infra failures (C0 violations)
- **Mitigation:** Fail-closed validation (exit 2 always blocks); comprehensive test coverage

**Risk:** Annotation burden (C4b 100% requirement)
- **Mitigation:** Composite key ledger makes annotation workflow efficient; small C/H volume expected

## Success Metrics

**Automated Criteria:**
- C0: 0 infra failures ✅
- C2: ≥30 items ✅
- C3: ≥2 consecutive weeks ✅
- C4: <5% FP rate ✅
- C4b: 100% annotation coverage ✅
- C5: All v2.0.0 ✅

**Manual Criteria:**
- C1: PM signoff recorded in decision log ✅

**Operational Metrics:**
- Dossier exits 0 (all criteria met)
- Canary enforce runs complete without false blocks
- Full enforce rollout with <5% FP rate sustained over 4+ weeks

## Rollback Plan

If enforce mode causes operational issues:

1. Revert `phase_end_handover.ps1` to `-AuditMode shadow`
2. Investigate false-block root cause
3. Tune rules or extend shadow window
4. Re-run dossier validation
5. Repeat canary enforce cycles

**Rollback trigger:** FP rate >=5% in enforce mode; revert to shadow immediately per `docs/rollback_protocol.md` and resume promotion only after the recovery criteria are met

---

## What Was Done

- Implemented Phase 24C auditor calibration system (auditor + calibration reporting + FP ledger)
- Completed first shadow cycle and annotation workflow
- Fixed 9 critical gaps in calibration script (status schema, BOM encoding, consecutive weeks logic, items counting, timestamp validation, ledger validation, output paths)
- Created 51 tests (23 auditor + 28 calibration) with zero regressions

## What Is Locked

- Auditor criteria C0/C2/C3/C4/C4b/C5 logic is implemented and tested
- Shadow mode + dossier reporting workflow is operational
- Fail-closed validation architecture (exit 2 always blocks)
- FP ledger schema with composite key (repo_id, run_id, finding_id)

## What Is Next

- Continue shadow runs to reach C2/C3 evidence thresholds (30+ items, 2+ consecutive weeks)
- Maintain 100% C/H annotation coverage after each run
- Regenerate weekly calibration reports
- Run dossier at window end (2026-03-17) and complete C1 manual signoff if eligible
- Execute canary enforce cycles (3-5 runs) before full rollout

## First Command

```bash
powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot . -AuditMode shadow
```
