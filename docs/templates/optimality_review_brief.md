# Optimality Review Brief (Template)

> **Canonical source:** src/sop/templates/optimality_review_brief.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Use this for high-impact semantic tradeoff decisions. Keep it short.

## Header
- BriefID: `<YYYYMMDD-short-id>`
- Owner: `<name>`
- DateUTC: `<ISO8601>`
- Scope: `<decision/change scope>`

## PRIMARY_OBJECTIVE
- `<one sentence>`

## TOP_LEVEL_TRADEOFFS
- `1) <tradeoff>`
- `2) <tradeoff>`
- `3) <tradeoff|optional>`

## OPTION_SET

### OPTION_A
- `TOP_LEVEL_EFFECT`: `<how this changes the system at the semantic/top level>`
- `WHY_NOW`: `<why choose this option under current constraints>`
- `COST_IF_WRONG`: `<main downside if this choice is wrong>`
- `EVIDENCE_PATHS`: `<artifact paths supporting this option>`

### OPTION_B
- `TOP_LEVEL_EFFECT`: `<...>`
- `WHY_NOW`: `<...>`
- `COST_IF_WRONG`: `<...>`
- `EVIDENCE_PATHS`: `<artifact paths supporting this option>`

### OPTION_C (Optional)
- `TOP_LEVEL_EFFECT`: `<...>`
- `WHY_NOW`: `<...>`
- `COST_IF_WRONG`: `<...>`
- `EVIDENCE_PATHS`: `<artifact paths supporting this option>`

## RECOMMENDED_OPTION
- `<OPTION_A|OPTION_B|OPTION_C|I don't know yet>`

## RECOMMENDED_BALANCE
- `<recommended tradeoff balance under current constraints>`

## WHAT_WOULD_FLIP_DECISION
- `<specific condition/evidence that would change the recommendation>`

## IF_NOT_READY_TO_COMPARE
- `<if needed, say "I don't know yet" and name the missing evidence or expert lane>`

## MILESTONE_CLOSE_ADDENDUM (Optional)
- `MILESTONE_ID`: `<milestone identifier>`
- `SHAPE_DELTA`: `<SIMPLER|UNCHANGED|MORE_COMPLEX>`
- `KEEP_THIS_SHAPE_TODAY`: `<YES|NO|I don't know yet>`
- `TOP_2_REGRETS_IF_WRONG`:
  - `1) <regret or risk>`
  - `2) <regret or risk>`
- `WHAT_TO_REMOVE_NEXT`: `<the next concept, interface, step, or surface to remove/simplify>`
- `EVIDENCE_PATHS`: `<artifact paths supporting the milestone review>`

## ELEGANCE_ENTROPY_SNAPSHOT (Optional)
- `CONCEPT_SURFACE_DELTA`: `<LOWER|UNCHANGED|HIGHER|I don't know yet>`
- `INTERFACE_SURFACE_DELTA`: `<LOWER|UNCHANGED|HIGHER|I don't know yet>`
- `BOUNDARY_CROSSINGS_DELTA`: `<LOWER|UNCHANGED|HIGHER|I don't know yet>`
- `FUTURE_EDIT_SURFACE`: `<SMALLER|UNCHANGED|LARGER|I don't know yet>`
- `BIGGEST_SIMPLIFIER`: `<what most reduced system entropy>`
- `BIGGEST_ENTROPY_RISK`: `<what most increased future maintenance or coordination cost>`
- `ENTROPY_VERDICT`: `<LOWER|UNCHANGED|HIGHER|I don't know yet>`
- `IF_NOT_READY_TO_JUDGE`: `<say "I don't know yet" when integration is too fresh, concurrent edits make the surface unstable, or future edit surface is not yet observable from one real change>`

## Note
- Advisory only; does not change control-plane authority.
- No new gate and no new authority path.
