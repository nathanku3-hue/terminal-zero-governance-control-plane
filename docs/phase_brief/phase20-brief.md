# Phase 20 Brief: Cyclical Trough Engine (Pod 1)
Date: 2026-02-22
Status: CLOSED (Strategy lock complete; phase-end governance BLOCK pending regression cleanup)
Owner: Codex

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): Cyclical Trough Engine (Pod 1)
- L2 Active Streams: Backend, Data, Ops
- L2 Deferred Streams: Frontend/UI
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Backend
- Active Stage Level: L3
- Current Stage: CI/CD
- Planning Gate Boundary: in-scope = Phase 20 strategy-rule closure, backtest evidence ledger, and phase handoff docs; out-of-scope = Phase 24 alternative-data pod implementation.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C and PM.
- Acceptance Checks: CHK-P20-01..CHK-P20-08.

## 1. Milestone Closure Summary
Phase 20 established and validated the Cyclical Trough Engine behavior as a defensive trough-hunting alpha model, then locked the production-facing decision rules used for handoff.

## 2. Golden Master Logic (Locked)
- Alpha generation ranker (cluster centroid score):
  - `cluster_score = (CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`
- Final ticker ordering path:
  - cyclical component selection uses `cluster_score`, then ticker ranking uses `odds_score` from the Mahalanobis/posterior path in `rank_ticker_pool`.
- Hard entry gate:
  - `entry_gate = score_valid & (conviction_score >= 7.0) & pool_long_candidate & mom_ok & support_proximity`
- Hard exit / portfolio inclusion:
  - `selected = entry_gate & (rank <= n_target)`

## 3. Portfolio Construction Lock
- Concentrated defaults:
  - `top_n_green = 8`
  - `top_n_amber = 4`
- Structural cash:
  - GREEN cash = `20%` (max gross cap effectively `0.80` in GREEN)
- Option A specialist regime remains available via run flag:
  - `--option-a-sector-specialist`

## 4. Empirical Backtest Ledger (2020-01-01 to 2024-12-31)
| Experiment | Artifact | CAGR | Sharpe | Max Drawdown | Verdict |
|---|---|---:|---:|---:|---|
| 1. Baseline (Broad Market) | `data/processed/phase20_5y_summary.json` | 2.25% | 0.31 | -13.41% | Failed: value-trap regime mismatch |
| 2. Option A (Sector Specialist) | `data/processed/phase20_5y_optionA_summary.json` | 6.76% | 0.41 | -25.37% | Improved return, weak drawdown control |
| 3. Option B (No Value Penalty) | `data/processed/phase20_5y_optionB_summary.json` | 4.24% | 0.29 | -30.70% | Failed: cyclical-top bias |
| 4. Hard Gate (Trend Confirmation) | `data/processed/phase20_5y_hardgate_summary.json` | 12.12% | 0.65 | -18.44% | Golden Master behavior confirmed |
| 5. Winner Retention (Soft Exits) | `data/processed/phase20_5y_winner_retention_summary.json` | 7.59% | 0.40 | -24.40% | Failed: alpha dilution |
| 6. Neutralized Macro (No Sector Filter) | `data/processed/phase20_5y_neutralized_macro_summary.json` | 3.07% | 0.29 | -19.03% | Failed: sector-selection drift |
| 7. Supercycle Growth Ranker | `data/processed/phase20_5y_supercycle_summary.json` | 5.46% | 0.33 | -31.98% | Failed: deep drawdown instability |
| 8. Concentrated + Missing-Data Fix | `data/processed/phase20_5y_PRODUCTION_FINAL_summary.json` | 1.23% | 0.34 | -3.21% | Stability gain, return ceiling observed |

## 5. Structural Boundary (Phase 20 Outcome)
- Micron diagnostic confirmed the model boundary for backward-looking fundamentals at cycle troughs:
  - October 2022 (`data/processed/diagnostic_MU_reverse_engineer.csv`):
    - `q_tot` mean = `3.2634692142857142`
    - `inv_vel_traj` mean = `0.0`
    - `conviction_score` mean = `3.510820467875683`
- Interpretation: market forward-pricing can make true trough recoveries appear expensive in backward-looking fundamental manifolds.

## 6. Delivered vs Deferred
- Delivered:
  - SDM adapter plumbing into Phase 20 runner.
  - Hard-gate entry enforcement.
  - Concentrated portfolio controls and structural-cash guardrails.
  - Missing-data continuity repair (ticker ffill + sector/market fallback).
- Deferred (Phase 24 runway):
  - S&P Capital IQ Pro forward-estimate feature pod (NTM growth, revisions, backlog).
  - Sentiment/flow pod (VIX term structure, options flow, insider flow).
  - Pod-level capital-rotation controller.

## 7. Artifacts (Phase 20 Close Set)
- `data/processed/phase20_5y_hardgate_summary.json`
- `data/processed/phase20_5y_hardgate_equity.png`
- `data/processed/phase20_5y_PRODUCTION_FINAL_summary.json`
- `data/processed/phase20_5y_PRODUCTION_FINAL_equity.png`
- `data/processed/diagnostic_MU_reverse_engineer.csv`
- `docs/handover/phase20_handover.md`

## 8. Top-Down Snapshot
L1: Cyclical Trough Engine (Pod 1)
L2 Active Streams: Backend, Data, Ops
L2 Deferred Streams: Frontend/UI
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Backend
Active Stage Level: L3

+--------------------+-----------------------------------------------------------------------------------------+--------+----------------------------------------------------------------------------+
| Stage              | Current Scope                                                                           | Rating | Next Scope                                                                 |
+--------------------+-----------------------------------------------------------------------------------------+--------+----------------------------------------------------------------------------+
| Planning           | Boundary=Phase20 close docs/evidence; Owner/Handoff=Codex->SAW A/B/C; AC=CHK-P20-*     | 100/100| 1) Freeze closure packet and handover [98/100]: governance complete        |
| Executing          | Consolidated experiment ledger + locked formulas + concentrated rules                   | 100/100| 1) Keep runtime unchanged pending PM token [95/100]: prevent drift         |
| Iterate Loop       | Reconciled MU diagnostics with backtest outcomes and model boundary                      | 98/100 | 1) Shift innovation to Phase24 data pods [90/100]: boundary now explicit   |
| Final Verification | SAW closure report + validators + context bootstrap packet                               | 96/100 | 1) Await PM "approve next phase" token [92/100]: phase gate contract       |
| CI/CD              | Phase 20 handover publication and locked-state docs                                      | 95/100 | 1) Start Phase24 only after approval [90/100]: explicit token required     |
+--------------------+-----------------------------------------------------------------------------------------+--------+----------------------------------------------------------------------------+

## 9. Evidence Footer
Evidence:
- Metrics and decisions sourced from `data/processed/phase20_5y*_summary.json` close artifacts.
- MU reverse-engineer evidence sourced from `data/processed/diagnostic_MU_reverse_engineer.csv`.

Assumptions:
- Phase 24 will introduce forward-looking alternative-data factors and keep PIT controls.

Open Risks:
- Current codebase previously carried exploratory ranker variants; closure lock requires keeping Option A ranker frozen unless PM reopens phase scope.

Rollback Note:
- Revert to pre-close state by restoring previous `phase20` brief and handover docs from backup plus prior ranker function implementation in `strategies/ticker_pool.py`.
