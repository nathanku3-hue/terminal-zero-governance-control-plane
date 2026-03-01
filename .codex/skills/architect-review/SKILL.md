---
name: architect-review
description: Trigger-based architecture review skill for boundaries, coupling, scaling, and security tradeoffs before high-impact implementation.
---

# Architect Review Skill

This skill is available by trigger and is not mandatory by default.

## 1. Trigger Conditions
Use this skill when one or more are true:
1. Architecture-impacting design change.
2. New dependency or boundary-crossing integration.
3. Performance/scaling uncertainty.
4. Security/data-access boundary concerns.

## 2. Review Contract
1. Confirm active project hierarchy context (`L1`, active `L2` stream, active stage).
2. Review and rate:
   - component boundaries,
   - dependency coupling,
   - data-flow bottlenecks,
   - scaling/SPOF risks,
   - security boundaries (`auth`, data access, API edges).
3. For each finding:
   - include file reference when applicable,
   - provide 2-3 options (including `do nothing` when reasonable),
   - select risk profile and weights:
     - `balanced`: `w_impact=1.0`, `w_maintainability=1.0`, `w_risk=1.0`, `w_effort=1.0`
     - `reliability_first`: `w_impact=1.0`, `w_maintainability=1.2`, `w_risk=1.5`, `w_effort=0.8`
     - `security_first`: `w_impact=1.0`, `w_maintainability=1.0`, `w_risk=1.7`, `w_effort=0.8`
     - `performance_first`: `w_impact=1.3`, `w_maintainability=0.9`, `w_risk=1.2`, `w_effort=0.9`
   - score each option with normalized components (`impact`, `risk`, `effort`, `maintainability`; 1-5 scale),
   - compute weighted `OptionScore = (impact*w_impact) + (maintainability*w_maintainability) - (risk*w_risk) - (effort*w_effort)`,
   - recommend one option with one-line reason.
4. Request confirmation before locking direction.

## 3. Output Schema
1. Findings table (`severity`, `impact`, `options`, `recommendation`, `status`).
2. Decision note (`chosen option`, `why`, `owner`).
3. Risk register (`open risk`, `mitigation`, `rollback`, `owner`, `target_milestone`).
4. Risk profile line (`profile`, `w_impact`, `w_maintainability`, `w_risk`, `w_effort`).
5. Option scoring table (`option`, `impact`, `risk`, `effort`, `maintainability`, `OptionScore`).
6. Calibration line:
   - append outcome rows to `docs/architect/profile_outcomes.csv` (`profile`, `outcome` in [0,1]).
   - run `python .codex/skills/_shared/scripts/validate_architect_calibration.py --history-csv "docs/architect/profile_outcomes.csv" --active-profile "<profile>"`.
   - emit `CalibrationValidation: PASS/DRIFT/INSUFFICIENT`.
7. Closure packet (machine-check format):
   - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
8. Closure validation:
   - run `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
   - emit `ClosureValidation: PASS/BLOCK`

## 4. Loop-Close and Edge-Case Rules
1. Severity gate:
   - unresolved in-scope `Critical/High` findings => `BLOCK` unless user explicitly accepts risk.
2. No-findings path:
   - if no material findings exist, emit `PASS` plus residual-risk note (one line).
3. Close-score tie-break:
   - if top two options are close (`recommendation_certainty < 75` and `option_score_diff <= 1`), keep recommended option first and force explicit user direction before lock-in.
4. Incomplete context:
   - if key architecture inputs are missing, mark finding `Needs Data`, add required inputs, and set `BLOCK` for closure decisions.
5. Hard close gate:
   - `PASS` only if:
     - no unresolved in-scope `Critical/High`,
     - no unresolved `Needs Data` blockers for decision-critical items,
     - risk profile is declared with complete weight set,
     - all options include complete normalized score components and computed weighted `OptionScore`,
     - calibration validation is `PASS` or `INSUFFICIENT` (with balanced fallback documented),
     - closure packet fields are complete (`RoundID`, `ScopeID`, `Checks*`),
     - closure validation is `PASS`.
   - `CalibrationValidation=DRIFT` => `BLOCK` unless user explicitly accepts risk.
   - otherwise `BLOCK` with required inputs in `Open Risks` and explicit next action.
6. Closure count rule:
   - `ChecksTotal` = number of decision-critical checks evaluated in this round.
   - `ChecksPassed` = checks satisfied; `ChecksFailed` = checks failed or not evaluable.

## 5. Escalation Rule
If the same architecture-risk trigger recurs for `>= 2` rounds in the same milestone/session, recommend upgrading this skill to mandatory for that milestone and request explicit user approval before enforcing.
