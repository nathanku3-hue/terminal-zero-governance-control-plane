# Phase C Baseline Analysis
**Date:** 2026-03-09
**Measurement Type:** Baseline check of current round + tracking framework setup
**Round Analyzed:** docs/context/round_contract_latest.md (generated 2026-03-05T17:35:00Z)

## Current Round Phase C Compliance Check

**Round Metadata:**
- ORIGINAL_INTENT: tdd smoke
- DELIVERABLE_THIS_SCOPE: seed generation
- DECISION_CLASS: TWO_WAY
- RISK_TIER: MEDIUM
- WORKFLOW_LANE: (not specified, defaults to DEFAULT)

**Phase C Requirement Derivation:**
- RISK_TIER=MEDIUM → QA/Socratic NOT required by derivation
- DECISION_CLASS=TWO_WAY → QA/Socratic NOT required by derivation
- WORKFLOW_LANE=DEFAULT (implicit) → QA/Socratic NOT required by derivation

**Phase C Gates Status:**

| Gate | Required? | Present? | Status | Notes |
|------|-----------|----------|--------|-------|
| QA_PRE_ESCALATION_REQUIRED | NO | NO | ✅ PASS | Not required for MEDIUM+TWO_WAY |
| QA_VERDICT | N/A | NO | ✅ PASS | Not required when QA not triggered |
| SOCRATIC_CHALLENGE_REQUIRED | NO | NO | ✅ PASS | Not required for MEDIUM+TWO_WAY |
| SOCRATIC_CHALLENGE_RESOLVED | N/A | NO | ✅ PASS | Not required when Socratic not triggered |
| WORKFLOW_LANE | Optional | NO | ✅ PASS | Defaults to DEFAULT, no enforcement needed |
| INTUITION_GATE (MILESTONE_REVIEW) | N/A | MACHINE_DEFAULT | ✅ PASS | Not MILESTONE_REVIEW lane |

**Validator Result:** ✅ PASS (exit 0 expected)

**Analysis:**
- Current round would pass Phase C validation
- No QA/Socratic requirements triggered (MEDIUM risk + TWO_WAY decision)
- No exception paths needed
- This represents a "low-friction" round under Phase C rules

**Baseline Conclusion:**
Phase C enforcement does not impact low-risk, two-way decision rounds. This is correct behavior - the workflow edge targets high-risk and one-way decisions, not routine work.

---

## Measurement Framework for Next 10 Rounds

**Tracking Schema:**

```csv
round_id,generated_at_utc,risk_tier,decision_class,workflow_lane,qa_required,qa_verdict,qa_exception_used,socratic_required,socratic_resolved,socratic_exception_used,milestone_review_lane,validator_exit_code,failure_reasons,time_to_fix_minutes,notes
```

**Field Definitions:**
- `round_id`: Sequential ID or round contract filename
- `generated_at_utc`: GENERATED_AT_UTC from round contract
- `risk_tier`: LOW|MEDIUM|HIGH
- `decision_class`: TWO_WAY|ONE_WAY
- `workflow_lane`: DEFAULT|PROTOTYPE|HIGH_RISK|MILESTONE_REVIEW (or blank if not specified)
- `qa_required`: YES|NO (derived or explicit)
- `verdict`: PASS|BLOCK|N/A
- `qa_exception_used`: YES|NO|N/A
- `socratic_required`: YES|NO (derived or explicit)
- `socratic_resolved`: YES|NO|N/A
- `socratic_exception_used`: YES|NO|N/A
- `milestone_review_lane`: YES|NO (WORKFLOW_LANE=MILESTONE_REVIEW)
- `validator_exit_code`: 0|1|2
- `failure_reasons`: Comma-separated list of Phase C errors (or "none")
- `time_to_fix_minutes`: Time spent fixing Phase C validation failures (or 0)
- `notes`: Free-text observations

**Measurement Process:**
1. After each round completes, run validator: `python scripts/validate_round_contract_checks.py`
2. Record exit code and any [ERROR] messages
3. If exit 1, measure time to add missing QA/Socratic fields and re-validate
4. Append row to `phase_c_measurement/live_rounds.csv`
5. After 10 rounds, generate aggregate report

**Target Metrics (to be measured):**
- **Validator failure rate:** % of rounds that initially fail Phase C validation
- **QA requirement rate:** % of rounds where QA is required (HIGH|ONE_WAY|HIGH_RISK)
- **Socratic requirement rate:** % of rounds where Socratic is required
- **Exception usage rate:** % of required rounds that use exception path
- **Time to fix:** Median minutes to resolve Phase C validation failuresalse positive rate:** % of rounds where Phase C requirements felt unnecessary (subjective)

**Success Criteria for Task 9b:**
- 10+ rounds measured
- All 6 target metrics calculated
- Comparison against Phase B synthetic baseline (20% warning rate, 0% failure rate)
- Operational recommendations documented

---

## Initial Data Point (Baseline Round)

```csv
round_id,generated_at_utc,risk_tier,decision_class,workflow_lane,qa_required,qa_verdict,qa_exception_used,socratic_required,socratic_resolved,socratic_exception_used,milestone_review_lane,validator_exit_code,failure_reasons,time_to_fix_minutes,notes
baseline_2026-03-05,2026-03-05T17:35:00Z,MEDIUM,TWO_WAY,DEFAULT,NO,N/A,N/A,NO,N/A,N/A,NO,0,none,0,Pre-Phase-C round; no QA/Socratic required
```

**Next Steps:**
1. Create `phase_c_measurement/live_rounds.csv` with header + baseline row
2. After each new round, append measurement row
3. After 10 rounds, run aggregate analysis and generate MEASUREMENT_REPORT.md
4. Compare against Phase B synthetic baseline to assess operational impact

---

## Tracking Script (Optional Enhancement)

For automated measurement, create `scripts/measure_phase_c_round.py`:

```python
#!/u/env python3
"""Measure Phase Ciance for a round contract and append to tracking CSV."""

import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-contract", required=True)
    parser.add_argument("--output-csv", default="phase_c_measurement/live_rounds.csv")
    args = parser.parse_args()

    # Run validator
    result = subprocess.run(
        ["python", "scripts/validate_round_contract_checks.py",
         "--round-contract-md", args.round_contract],
        capture_output=True,
        text=True,
    )

    # Parse round contract fields (simplified - would need full parser)
    # Extract: risk_tier, decision_class, workflow_lane, qa_*, socratic_*

    # Append row to CSV
    # (Implementation details omitted for brevity)

    print(f"Recorded measurement for {args.round_contract}")
    print(f"Validator exit code: {result.returncode}")


if __name__ == "__main__":
    sys.exit(main())
```

**Decision:** Defer automated script until manual tracking proves valuable. Start with manual CSV updates for first 10 rounds.
