# First-Principles Prompt Quality Rubric v1.0

Owner: PM  
Status: ACTIVE  
Last Updated: 2026-03-04

## Purpose
Provide a measurable, repeatable way to evaluate worker/auditor prompt quality before making prompt edits.

This rubric is used to:
- Decide whether a prompt is acceptable as-is.
- Identify exactly what to improve.
- Prevent subjective prompt churn and overengineering.

## Scope
In scope:
- Worker and auditor prompt quality for planning/review rounds.
- Prompt-driven output quality for first-principles reasoning and decision readiness.

Out of scope:
- Model capability limits unrelated to prompt text.
- Infrastructure/runtime failures.

---

## Scoring Model

- 8 dimensions, each scored `0`, `1`, or `2`.
- Maximum score = `16`.
- Evaluate using the latest completed round artifacts.

### Dimension Definitions

| ID | Dimension | Score 0 | Score 1 | Score 2 |
|---|---|---|---|---|
| R1 | Intent Precision | Intent missing/ambiguous | Intent present but broad | Single-sentence intent is specific and testable |
| R2 | Scope Discipline | Scope drift present | Partial scope control | Clear non-goals + no out-of-scope execution |
| R3 | Deliverable Clarity | Deliverable undefined | Deliverable partially concrete | Deliverable explicit, bounded, and verifiable |
| R4 | Evidence Contract | No required evidence listed | Evidence listed but incomplete | Required evidence + verification commands clearly defined |
| R5 | Risk Coverage | Key risks omitted | Risks noted but weak actions | Risks mapped to actions/escalation triggers |
| R6 | Decision Readiness | Output not decision-usable | Decision signal present but vague | Clear GO/HOLD/REFRAME path with blockers |
| R7 | Concision/Signal | Verbose or under-specified | Mixed signal/noise | High signal density, minimal fluff, paste-ready |
| R8 | Round Closure Quality | No explicit done condition | Done condition partial | DONE_WHEN + STOP_CONDITION explicit and enforced |

---

## Pass/Fail Thresholds

| Total Score | Verdict | Action |
|---:|---|---|
| 14-16 | PASS | Keep prompt; no edit required |
| 11-13 | ADVISORY_PASS | Small targeted edits allowed (max 2 changes) |
| 8-10 | HOLD | Prompt revision required before next major scope |
| 0-7 | REFRAME | Prompt redesign required; escalate to PM |

### Hard-Fail Rules (Override Total Score)
If any of these are true, verdict cannot be PASS:
1. `R1 = 0` (Intent not precise)
2. `R2 = 0` (Scope discipline broken)
3. `R4 = 0` (Evidence contract missing)
4. `R8 = 0` (No clear closure condition)

---

## Review Procedure (Per Prompt Revision Cycle)

1. Collect latest round artifacts:
   - `docs/round_contract_template.md` outputs (worker + auditor blocks)
   - `docs/context/ceo_go_signal.md`
   - latest phase-end summary in `docs/context/phase_end_logs/`
2. Score all 8 dimensions (`R1..R8`).
3. Record scorecard in weekly ops notes.
4. If verdict is `ADVISORY_PASS` or lower, propose only targeted edits linked to low-scoring dimensions.
5. Re-run one round, then rescore. Do not stack multiple prompt rewrites without rescoring.

---

## Edit Budget Rules

To keep prompt tuning lean:
- `PASS`: 0 edits.
- `ADVISORY_PASS`: up to 2 line-level edits.
- `HOLD`: up to 5 focused edits in one revision.
- `REFRAME`: redesign allowed, but requires PM approval before use.

Never combine prompt redesign with architecture changes in the same round.

---

## KPI Linkage (Weekly)

Track these with rubric score:
1. Rubric total score (`0..16`)
2. `HOLD` and `REFRAME` rate
3. Auditor Critical/High findings per round
4. Rounds-to-decision median

Expected direction after prompt improvements:
- Rubric score up
- HOLD/REFRAME down
- C/H findings down
- rounds-to-decision down

---

## Paste-Ready Scoring Block

```text
PROMPT_RUBRIC_SCORE
ROUND: <round_id>
PROMPT_TARGET: worker|auditor

R1 Intent Precision: 0|1|2
R2 Scope Discipline: 0|1|2
R3 Deliverable Clarity: 0|1|2
R4 Evidence Contract: 0|1|2
R5 Risk Coverage: 0|1|2
R6 Decision Readiness: 0|1|2
R7 Concision/Signal: 0|1|2
R8 Round Closure Quality: 0|1|2

TOTAL: <0-16>
VERDICT: PASS|ADVISORY_PASS|HOLD|REFRAME
HARD_FAIL: YES|NO

LOWEST_DIMENSIONS: <list>
EDIT_BUDGET: <0|2|5|PM_APPROVAL>
NEXT_ACTION: <one line>
```

---

## Example (Current 24C State)

Context: C2 closed, C3 pending; operational loop stable.

Sample score:
- R1: 2
- R2: 2
- R3: 2
- R4: 2
- R5: 2
- R6: 2
- R7: 1
- R8: 2

Total: `15/16` -> `PASS`

Interpretation:
- Prompt quality is strong enough for current scope.
- No redesign needed.
- Optional micro-improvement: tighten concise output style (`R7`) with at most 1-2 line edits.

---

## Governance Notes

- This rubric evaluates prompt quality, not implementation correctness.
- Auditor and PM should both be able to reproduce scores from artifacts.
- Any score dispute uses `docs/disagreement_taxonomy.md` (code `D08`).

