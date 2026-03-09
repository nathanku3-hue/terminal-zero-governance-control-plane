# Phase C Next Work

**Status:** Phase C fail-closed enforcement is live on main (commit 939c4d8)

**Completed this stream:**
- ✅ Phase C implementation with requirement derivation
- ✅ Test coverage (14/14 Phase C tests, 322/322 full suite)
- ✅ Merged to main with safe stash/restore workflow
- ✅ Measurement framework established (baseline + tracking schema)
- ✅ Dead code cleanup (Phase B warning helper removed)

---

## Immediate Next Work

### 1. Task 9b: Live-Round Data Collection (Priority: HIGH)

**Goal:** Measure Phase C operational impact on real rounds

**Process:**
1. After each of the next 10 rounds completes, run:
   ```bash
   python scripts/validate_round_contract_checks.py \
     --round-contract-md docs/context/round_contract_latest.md
   ```

2. Record outcome in `phase_c_measurement/live_rounds.csv`:
   - Extract fields from round contract (risk_tier, decision_class, workflow_lane)
   - Record validator exit code (0=pass, 1=fail, 2=error)
   - If exit 1: capture error messages and time to fix
   - Note whether exception path was used

3. After 10 rounds, generate aggregate report:
   - Calculate 6 target metrics (failure rate, QA/Socratic requirement rate, exception usage, time to fix, false positive rate)
   - Compare against Phase B synthetic baseline (20% warning rate, 0% failure rate)
   - Document operational friction and recommendations
   - Create `phase_c_measurement/MEASUREMENT_REPORT.md`

**Success criteria:**
- 10+ rounds measured
- All 6 metrics calculated
- Comparison vs Phase B baseline documented
- Operational recommendations provided (keep/iterate/rollback)

**Estimated timeline:** 1-2 weeks (depends on round execution cadence)

---

### 2. Wave 2 P2: Packaging & Reproducibility Hardening (Priority: MEDIUM)

**Goal:** Make SOP workflow reproducible and portable for OSS release

**Deferred until:** Task 9b data collection complete

**Scope:**
- Package management hardening (requirements.txt pinning, dependency audit)
- Environment reproducibility (Python version constraints, platform compatibility)
- Installation documentation (setup.py or pyproject.toml, installation guide)
- CI/CD integration (GitHub Actions for test automation)
- Release artifacts (versioning, changelog, distribution)

**Rationale for deferral:**
- Phase C operational evidence needed before adding more release surface
- Measurement data may inform packaging priorities
- Avoid premature optimization before validating Phase C impact

---

## Future Work (Not Immediate)

### Phase D: Measurement & Iteration (Week 4+)

After Task 9b complete:
- Review aggregate metrics
- CEO decision: GO (keep enforcement) / ITERATE (adjust thresholds) / HOLD (rollback)
- If GO: document Phase C as stable, archive measurement artifacts
- If ITERATE: adjust requirement derivation logic based on false positive rate
- If HOLD: revert to Phase B warning mode, analyze root causes

### Workflow Edge KPI Dashboard (Optional)

If Phase C proves valuable:
- Automate measurement collection (scripts/measure_phase_c_round.py)
- Create weekly KPI report generation
- Track long-term trends (QA catch rate, Socratic challenge rate, cycle time impact)
- Integrate into loop_operating_contract.md as first-class metric

### Additional Workflow Lanes (Optional)

If WORKFLOW_LANE adoption is high:
- Add EXPERIMENTAL lane (even more relaxed than PROTOTYPE)
- Add SECURITY_CRITICAL lane tricter than HIGH_RISK)
- Document lane selection decision tree

---

## Handoff Notes

**Current repo state:**
- Branch: main (commit 939c4d8)
- Phase C enforcement: active
- Tests: 322/322 passing
- Measurement framework: ready for data collection

**Untracked local artifacts (not committed):**
- .gitignore (modified)
- docs/context/auditor_calibration_report.* (generated)
- docs/context/auditor_promotion_dossier.* (generated)
- docs/context/ceo_go_signal.md (generated)

These are operational artifacts from previous rounds, not part of Phase C work.

**Key files for next operator:**
- `phase_c_measurement/README.md` - Measurement process
- `phase_c_measurement/live_rounds.csv` - Data collection schema
- `scripts/validate_round_contract_checks.py` - Phase C validator (lines 197-282)
- `tests/test_validate_round_contract_checks.py` - Phase C test coverage

**Critical path:**
1. Collect 10 live rounds → Task 9b complete
2. Generate aggregate report → CEO decision on Phase C
3. If GO → proceed to Wave 2 P2 packaging work
4. If ITERATE/HOLD → adjust Phase C logic or revert

---

## Questions for Next Operator

1. **Measurement cadence:** How frequently are rounds executing? (Affects Task 9b timeline)
2. **Exception path usage:** Are PM/CEO approving QA/Socratic exceptionsk in CSV notes)
3. **False positive rate:** Do HIGH/ONE_WAY rounds feel over-gated? (Subjective but important)
4. **Cycle time impact:** Is +1.5-3 hours for QA/Socratic acceptable? (Compare against baseline)

**Contact:** Review phase_c_measurement/baseline_analysis.md for current round compliance check.
