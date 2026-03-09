# Minimal Optimality Roadmap

Status: Active  
Scope: PM/operator planning artifact (advisory)  
Authority: Advisory only; does not change the stable control plane.

## Current Verdict

- Current system is a strong governance/control engine, not yet an optimal engine.
- `PASS` means admissible / merge-ready, not automatically optimal.
- Current maturity snapshot:
  - governance / control engine: `9.1/10`
  - truth-aware delivery engine: `7.8/10`
  - optimality engine maturity: `8.6/10`

## Working Definitions

- `Optimal` = the best tradeoff under current constraints; honest to truth, reversible where possible, low entropy, and high learning value.
- `Semantic top-level tradeoff` = a tension that changes what the system should optimize, what counts as truth, the cost of being wrong, or long-term system direction.

## PM-Style Gap Table

| Capability | Current Engine | Optimal Engine | Minimal Next Patch |
| --- | --- | --- | --- |
| Merge / admissibility | Strong fail-closed merge and escalation discipline | Keep this strength | No patch needed; preserve current gate model |
| Multi-option comparison | Advisory compare mode now exists, but it is still early and not yet outcome-validated at scale | Compares 2-3 real options before one-way or high-impact moves | Use compare mode on real high-impact rounds and feed what actually mattered into shipped-outcome capture |
| Milestone-level optimality review | Advisory milestone-close review now exists, but it is still new and not yet proven across repeated milestones | Reviews whether each milestone improved or worsened the system shape | Use the milestone-close addendum on real milestone closes and carry the main deltas into shipped-outcome feedback |
| Shipped-outcome feedback | Advisory shipped-outcome capture now exists in the corpus, but the learning loop is still young and not yet supported by many shipped waves | Learns from shipped outcomes, rollbacks, and semantic misses | Populate outcome records on real shipped waves and reuse them before adding new scoring or automation |
| Elegance / entropy visibility | Advisory snapshot now exists via the reused optimality brief, but it is still early and not yet proven across repeated milestone closes | Tracks whether the system is getting simpler or more tangled without inventing a new subsystem | Reuse the same brief on real milestone closes and compare lightweight proxies: concepts, interfaces, boundary crossings, future edit surface |
| Token / context discipline | Good local discipline with docs-as-code and indexes | Same, but even leaner with better top-level tradeoff routing | Treat token budget as a secondary constraint, not the primary optimality engine gap |

## Minimal Roadmap Order

| Step | Goal | Completion Signal | Expected Effect |
| --- | --- | --- | --- |
| `R1` | Add multi-option comparison | High-impact rounds show `Option A / Option B / why now / cost if wrong` | Biggest immediate jump in decision quality |
| `R2` | Add milestone-level optimality review | Each major milestone answers `what got simpler / more complex / would we keep this shape today` | Prevents local wins from creating global mess |
| `R3` | Add shipped-outcome feedback | Each shipped wave records rollback/follow-up/semantic issues | Converts post-merge reality into reusable evidence |
| `R4` | Add elegance / entropy snapshot | The reused optimality brief reports simple elegance proxies (`concepts`, `interfaces`, `boundary crossings`, `future edit surface`) | Makes simplicity and maintainability discussable, not just intuitive |

## Recommended Sequence

- `R1` is in place as advisory compare mode.
- `R2` is in place as an advisory milestone-close addendum.
- `R3` is in place as advisory shipped-outcome capture in the corpus.
- `R4` is now in place as a lightweight elegance / entropy snapshot inside the reused optimality brief.
- Next step is operational, not architectural: use `R4` on real milestone closes before inventing any scoring layer.

## Target Trajectory

- After `R1 + R2`: likely `~8.0 - 8.4` on optimality-engine maturity.
- After `R3` patch-only: likely `~8.2 - 8.4`.
- After `R4` patch-only: likely `~8.5 - 8.7`.
- After repeated real shipped waves plus real milestone-close `R4` use: likely `~8.8 - 9.1`.
- After `R4` plus real operating time: possible `~9.3 - 9.5`.

## Operator Note

- This roadmap is intentionally lean.
- It is designed to sharpen decision quality without adding a new authority path, new mandatory runtime gate, or unnecessary process overhead.
