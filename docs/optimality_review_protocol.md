# Optimality Review Protocol (Advisory)

Status: Active  
Scope: PM/operator decision-support (docs-only)  
Authority: Advisory only; does not add decision/control-plane authority.

## Core Principle

- `PASS`/merge-complete is not automatically optimal.
- Optimal means the best tradeoff under current constraints, not theoretical perfection.

## What to Review (top-level only)

- Extract semantic tradeoffs, not code trivia.
- Keep `TOP_LEVEL_TRADEOFFS` to at most 2-3 items.
- Focus on decision-shaping tradeoffs (impact/risk/reversibility/scope pressure).

## Required Brief Fields

- `PRIMARY_OBJECTIVE`
- `TOP_LEVEL_TRADEOFFS`
- `OPTION_SET` (`OPTION_A`, `OPTION_B`, optional `OPTION_C`)
- `RECOMMENDED_OPTION`
- `RECOMMENDED_BALANCE`
- `WHAT_WOULD_FLIP_DECISION`

## R1 Advisory Multi-Option Comparison

- Use the same brief in compare mode when the decision could reasonably go more than one way.
- Compare at most `2-3` real options.
- Keep each option at the semantic/top-level only; do not drift into code trivia.
- For each option, capture:
  - `TOP_LEVEL_EFFECT`
  - `WHY_NOW`
  - `COST_IF_WRONG`
  - `EVIDENCE_PATHS`
- If an honest comparison is not yet possible, explicitly state `I don't know yet` and name the missing evidence or expert lane required.
- This is advisory only: no new gate, no new authority path, no control-plane change.

## R2 Advisory Milestone-Level Review

- Reuse the same brief at milestone close to review whether the system shape actually improved.
- Use milestone review once per milestone close, not every round.
- Keep the milestone addendum short and top-level only.
- Milestone-close addendum fields:
  - `MILESTONE_ID`
  - `SHAPE_DELTA` (`SIMPLER|UNCHANGED|MORE_COMPLEX`)
  - `KEEP_THIS_SHAPE_TODAY` (`YES|NO|I don't know yet`)
  - `TOP_2_REGRETS_IF_WRONG`
  - `WHAT_TO_REMOVE_NEXT`
  - `EVIDENCE_PATHS`
- If the milestone is too fresh to judge honestly, explicitly state `I don't know yet`.
- This is advisory only: no new gate, no new authority path, no control-plane change.

## R4 Advisory Elegance / Entropy Snapshot

- Reuse the same brief; do not create a separate subsystem, scorer, or gate.
- Use this snapshot when the question is whether the system got simpler or more tangled after a milestone or shape-changing patch.
- Keep it proxy-based and top-level only; do not pretend to precision that the artifacts cannot support.
- Capture only the leanest fields:
  - `CONCEPT_SURFACE_DELTA`
  - `INTERFACE_SURFACE_DELTA`
  - `BOUNDARY_CROSSINGS_DELTA`
  - `FUTURE_EDIT_SURFACE`
  - `BIGGEST_SIMPLIFIER`
  - `BIGGEST_ENTROPY_RISK`
  - `ENTROPY_VERDICT`
- `I don't know yet` is the correct answer when:
  - integration is too fresh to judge honestly
  - concurrent in-flight changes make the surface unstable
  - future edit surface will only become visible after one more real change or shipped use
- This is advisory only: no new gate, no new authority path, no control-plane change.

## Trigger Cases (use when any apply)

- high-impact decision
- one-way/low-reversibility decision
- cross-module or architecture-affecting change
- semantic-heavy/domain-interpretation-heavy decision
- milestone close for a major architecture or workflow wave

## Working Artifact

- Template: `docs/templates/optimality_review_brief.md`
- Suggested live file: `docs/context/optimality_review_brief_latest.md`
- Suggested milestone-close file: `docs/context/milestone_optimality_review_latest.md`
- R4 elegance / entropy snapshot lives inside the same brief; do not create a separate template.

## Authority Boundary

- Worker/Auditor/PM/CEO ownership remains unchanged.
- This protocol improves recommendation quality only; it is not a new gate.
