# Phase 24C: Auditor Calibration & Shadow-to-Enforce Promotion

**Phase ID**: phase-24c
**Phase Name**: Auditor Calibration & Shadow-to-Enforce Promotion
**Status**: in_progress
**Owner**: PM
**Start Date**: 2026-03-03
**Target End**: 2026-03-17

---

## Scope

Implement independent auditor review system with false-positive calibration and promotion dossier to validate shadow-to-enforce transition.

**Core Components**:
- Auditor rules engine (AUD-R000 through AUD-R009)
- False-positive ledger and annotation workflow
- Calibration reporting (weekly and dossier modes)
- Shadow-to-enforce promotion criteria (C0-C5)

---

## Workflow Profile

**Workflow Weight**:
- Frontend: 0%
- Backend: 30%
- Governance: 60%
- Data: 10%
- Research: 0%

**Total: 100%**

**Rationale**: Governance-heavy phase focused on auditor calibration, FP annotation workflow, and promotion criteria validation with backend support for rules engine and data processing for calibration metrics.

---

## Objectives

1. Implement 7 auditor rules for worker reply packet quality review
2. Establish FP ledger schema and 100% annotation workflow for C/H findings
3. Execute 2-week shadow calibration window (2026-03-03 to 2026-03-17)
4. Validate promotion criteria through automated dossier reporting
5. Transition to enforce mode after dossier approval and manual signoff

---

## Deliverables

| ID | Name | Workflow Type | Status | Owner | Evidence Path | Evidence Type |
|---|---|---|---|---|---|---|
| D1 | Auditor Rules Engine | backend | complete | worker | scripts/auditor.py | code |
| D2 | FP Ledger Schema | governance | complete | auditor | docs/context/auditor_fp_ledger.json | artifact |
| D3 | Calibration Reporting | backend | complete | worker | scripts/calibration_report.py | code |
| D4 | Promotion Dossier | governance | in_progress | auditor | docs/context/auditor_promotion_dossier.md | artifact |
| D5 | Test Suite | backend | complete | worker | tests/ | code |
| D6 | Shadow Run Evidence | data | in_progress | worker | docs/context/shadow_runs/ | data |

---

## Success Criteria

| ID | Name | Workflow Type | Threshold | Status | Measured Value | Evidence Path |
|---|---|---|---|---|---|---|
| C0 | Infrastructure Health | backend | 0 failures | pass | 0 | docs/context/auditor_promotion_dossier.md |
| C1 | Phase 24B Operational Close | governance | PM signoff | pending | — | docs/decision_log.md |
| C2 | Minimum Items Reviewed | data | >=30 items | pending | 15 | docs/context/auditor_calibration_report.md |
| C3 | Consecutive Weeks | data | >=2 weeks | pending | 1 | docs/context/auditor_calibration_report.md |
| C4 | False-Positive Rate | governance | <5% | pending | — | docs/context/auditor_fp_ledger.json |
| C4b | Annotation Coverage | governance | 100% | pass | 100% | docs/context/auditor_fp_ledger.json |
| C5 | Schema Version | backend | v2.0.0 | pass | v2.0.0 | docs/context/shadow_runs/ |

---

## Realm-Specific Criteria

### Software Engineering

| ID | Name | Check | Validator | Status |
|---|---|---|---|---|
| SE-01 | Test Coverage | all rules tested | scripts/validate_test_coverage.py | pass |
| SE-02 | Exit Code Discipline | exit 2 always blocks | scripts/validate_exit_codes.py | pass |
| SE-03 | Schema Validation | all packets v2.0.0 | scripts/validate_schema_version.py | pass |

---

## Evidence Requirements

**Operational Artifacts**:
- `docs/context/auditor_fp_ledger.json` - FP annotations with 100% C/H coverage
- `docs/context/auditor_calibration_report.md` - Weekly calibration report
- `docs/context/auditor_promotion_dossier.md` - Dossier validation report

**Test Evidence**:
- 51 tests passing (23 auditor + 28 calibration)
- Zero regressions in existing test suite

**Traceability**:
- PM-24C-001 through PM-24C-007 mapped in `pm_to_code_traceability.yaml`
- Decision log entries D-117 through D-126

---

## Acceptance Criteria

### C0: Infrastructure Health
- **Threshold**: 0 infra failures
- **Definition**: Zero exit code 2 failures (script crashes, invalid JSON, missing files)
- **Rationale**: Infra errors block regardless of mode; broken tooling must never hide behind shadow mode

### C1: Phase 24B Operational Close (MANUAL)
- **Threshold**: PM signoff required
- **Requirements**:
  - Bootstrap worker packet replaced with real execution evidence
  - Cross-repo readiness validated (Quant, Film, SOP)
  - One successful enforce-mode dry-run completed without false blocks
- **Rationale**: Manual gate ensures operational readiness beyond automated metrics

### C2: Minimum Items Reviewed
- **Threshold**: ≥30 items total across shadow window
- **Definition**: Sum of `items_reviewed` from all shadow run summaries
- **Rationale**: Statistical significance for FP rate measurement

### C3: Consecutive Weeks
- **Threshold**: ≥2 consecutive ISO weeks with ≥10 items each
- **Definition**: Longest consecutive run of qualifying weeks (not total qualifying weeks)
- **Rationale**: Sustained operational cadence, not sporadic bursts

### C4: False-Positive Rate
- **Threshold**: <5%
- **Definition**: (FP count / C+H total) among annotated findings
- **Rationale**: Acceptable false-block rate for enforce mode

### C4b: Annotation Coverage
- **Threshold**: 100% (strict)
- **Definition**: All C/H findings must have TP or FP verdict in ledger
- **Rationale**: Cannot measure FP rate without complete annotation

### C5: Schema Version
- **Threshold**: All packets v2.0.0
- **Definition**: All reviewed packets use `schema_version: "2.0.0"`
- **Rationale**: v1 packets lack v2 fields required for auditor checks

---

## Dependencies

**Blocks**: Phase 25 (Enforce Mode Rollout)
**Blocked By**: Phase 24B (Worker Reply Packet v2)
**External Dependencies**: PM signoff for C1 manual gate

---

## Risks

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Insufficient shadow run volume | HIGH | Extend shadow window if needed | PM |
| High FP rate (>5%) | HIGH | Refine auditor rules, re-calibrate | Worker |
| Annotation workflow bottleneck | MEDIUM | Automate TP/FP classification where possible | Worker |

---

## Rollback Plan

**If this phase fails or must be reverted**:
1. Revert to Phase 24B baseline (worker packets without auditor)
2. Archive FP ledger and calibration reports
3. Document lessons learned in decision log

**Rollback Evidence**: Git tag `phase-24b-baseline` exists and is deployable

---

## Next Phase

**Phase ID**: phase-25
**Phase Name**: Enforce Mode Rollout
**Trigger**: C0-C5 all pass AND C1 manual signoff complete

---

## Notes

- Shadow window: 2026-03-03 to 2026-03-17 (2 weeks)
- Canary enforce cycles (3-5 runs) required before full rollout
- FP ledger uses composite key (repo_id, run_id, finding_id)

---

**Template Version**: 2.0.0
**Last Updated**: 2026-03-16
