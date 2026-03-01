## What Was Done
- Phase 20 closure docs/logs were consolidated and lock formulas were codified with artifact-backed evidence.
- Option A cyclical-trough ranker was restored in code to match lock narrative.
- Independent replay evidence (implementer + Reviewer B) was produced with matching outputs.

## What Is Locked
- Cluster ranker: `(CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`.
- Hard entry gate requires both `mom_ok` and `support_proximity`.
- Hard exit/selection is rank-threshold + entry-gate bound.

## What Is Next
- Phase 24 Pod A (Supercycle) feature ingestion is not started.
- Phase 24 Pod B (Sentiment and Flow) feature ingestion is not started.
- Pod-level capital rotation and PM dashboard are not started.
- Build Supercycle Pod with forward features (NTM growth, EPS revisions, capex-to-sales, backlog mapping).
- Build Sentiment and Flow Pod (VIX term structure, put/call, IV spikes, max pain, insider-flow signals).
- Define pod-rotation capital allocator and publish PM monitor dashboard contract.

## First Command
```text
Draft `docs/phase_brief/phase24-brief.md` with Pod A/B acceptance checks and PIT-safe schema contracts.
```
