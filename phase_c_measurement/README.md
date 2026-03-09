# Phase C Live-Round Measurement Framework

**Purpose:** Track Phase C fail-closed enforcement impact on real rounds over time.

**Status:** Active measurement (0/10 rounds collected)

**Baseline:** 1 pre-Phase-C round analyzed (MEDIUM+TWO_WAY, passed validation)

---

## Measurement Process

After each round completes:

1. **Run validator:**
   ```bash
   python scripts/validate_round_contract_checks.py \
     --round-contract-md docs/context/round_contract_latest.md
   ```

2. **Record exit code:**
   - 0 = pass
   - 1 = Phase C validation failure
   - 2 = infrastructure error

3. **If exit 1, capture:**
   - Error messages from validator output
   - Time spent adding missing QA/Socratic fields
   - Whether exception path was used

4. **Append row to `live_rounds.csv`:**
   - Extract fields from round contract
   - Record validator outcome
   - Add notes on operational friction

5. **After 10 rounds:**
   - Generate aggregate metrics
   - Compare against Phase B synthetic baseline
   - Create MEASUREMENT_REPORT.md with recommendations

---

## Target Metrics

| Metric | Definition | Phase B Baseline | Phase C Target |
|--------|------------|------------------|----------------|
| **Validator failure rate** | % rounds that initially fail Phase C validation | 0% (warning-only) | TBD (expect >0%) |
| **QA requirement rate** | % rounds where QA required (HIGH\|ONE_WAY\|HIGH_RISK) | 20% (synthetic) | TBD |
| **Socratic requirement rate** | % rounds where Socratic required | 20% (synthetic) | TBD |
| **Exception usage rate** | % required rounds using exception path | 20% (synthetic) | TBD (expect <10%) |
| **Time to fix** | Median minutes to resolve Phase C failures | 0 (no failures) | TBD |
| **False positive rate** | % rounds where requirements felt unnecessary | 0% (subjective) | TBD |

---

## Data Collection

**Location:** `phase_c_measurement/live_rounds.csv`

**Schema:**
```
round_id, generated_at_utc, risk_tier, decision_class, workflow_lane,
qa_required, qa_verdict, qa_exception_used,
socratic_required, socratic_resolved, socratic_exception_used,
milestone_review_lane, validator_exit_code, failure_reasons,
time_to_fix_minutes, notes
```

**Current data:** 1 baseline row (pre-Phase-C round)

---

## Success Criteria

Task 9b complete when:
- ✅ Baseline analysis done (current round evaluated)
- ✅ Tracking framework established (CSV + process documented)
- ⏳ 10+ rounds measured (0/10 complete)
- ⏳ Aggregate metrics calculated
- ⏳ Comparison vs Phase B baseline documented
- ⏳ Operational recommendations provided

**Next action:** Collect data from next 10 real rounds as they execute.

---

## Notes

- Baseline round (2026-03-05): MEDIUM+TWO_WAY, no QA/Socratic required, passed validation
- Phase C enforcement does not impact low-risk routine work (correct behavior)
- Measurement will show impact on HIGH risk, ONE_WAY decisions, and HIGH_RISK lane usage
- Manual CSV updates for now; automated script deferred until value proven
