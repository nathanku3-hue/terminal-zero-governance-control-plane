# Phase 20 Handover (PM-Friendly)

Date: 2026-02-22
Phase Window: 2020-01-01 to 2024-12-31
Status: BLOCK
Owner: Codex

## 1) Executive Summary
- Objective completed: Phase 20 strategy evolution was wrapped into a single locked operating narrative with evidence ledger and handoff package.
- Business/user impact: We now have an auditable Golden Master thesis, explicit structural boundary, and a clean runway definition for Phase 24 data pods.
- Current readiness: Documentation/handover is complete, but phase-end governance remains BLOCKED until full regression failures are cleared.

## 2) Delivered Scope vs Deferred Scope
- Delivered:
  - Golden Master formula lock, entry/exit gate lock, and concentrated portfolio defaults codified.
  - Full experiment ledger stitched to concrete `phase20_5y_*` artifacts.
  - MU reverse-engineer diagnostics integrated into closure rationale.
  - SAW closeout report + closure packet + validators.
- Deferred:
  - Full green regression gate for phase-end closure (Owner: Engineering, Target: Phase 20 closeout patch).
  - Phase 24 Supercycle and sentiment/flow pods (Owner: PM/Research, Target: Phase 24).

## 3) Derivation and Formula Register
| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-01 | `cluster_score = (CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot` | `CycleSetup` cycle interaction, `op_lev` operating leverage, `rev_accel` revenue accel, `inv_vel_traj` inventory velocity trajectory, `q_tot` valuation/supply proxy | Encodes capital-cycle trough thesis with value discipline | `strategies/ticker_pool.py` (`_conviction_cluster_score`) |
| F-02 | `entry_gate = score_valid & (conviction_score >= 7.0) & pool_long_candidate & mom_ok & support_proximity` | score validity, conviction threshold, pool candidacy, momentum and support gates | Prevents falling-knife entries | `strategies/company_scorecard.py` (`build_phase20_conviction_frame`) |
| F-03 | `selected = entry_gate & (rank <= n_target)` | rank and hard gate | Hard exit; no hysteresis carry in lock state | `scripts/phase20_full_backtest.py` (`_build_phase20_plan`) |
| F-04 | `cash_pct_GREEN = 0.20`, `gross_cap_GREEN = 0.80` | regime map, gross cap clamp | Maintains structural cash buffer in GREEN | `scripts/phase20_full_backtest.py` (`_build_phase20_plan`) |
| F-05 | grouped `ffill(limit=120)` -> sector median -> market median -> `0.0` | sparse SDM fundamentals | Avoids NaN-driven universe collapse | `strategies/company_scorecard.py` (`build_phase20_conviction_frame`) |

## 4) Logic Chain
| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-01 | `features.parquet` + `features_sdm.parquet` + prices + macro/liquidity | dual-read merge, PIT lag features, pool ranking, hard gates | only `entry_gate` and rank-qualified names are selected | daily portfolio plan + backtest artifacts |
| L-02 | sparse quarterly/annual SDM fields | ticker ffill(120) + cross-sectional fallback | keep rows tradable despite sparse fundamentals | preserved cross-section for ranking |
| L-03 | backtest outputs and diagnostics | compare experiment metrics and MU boundary stats | lock known-good rules; defer data-ontology gaps | Phase 20 closure packet and Phase 24 runway |

## 5) Validation Evidence Matrix
| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-PH-01 | `.venv\Scripts\python -m pytest -q` | BLOCK (6 failing tests) | console output | failing modules: `tests/test_assemble_sdm_features.py`, `tests/test_company_scorecard.py`, `tests/test_phase20_full_backtest_loader.py`, `tests/test_ticker_pool.py` |
| CHK-PH-02 | `.venv\Scripts\python launch.py --help` | PASS | console output | app boot CLI help returned with exit code `0` |
| CHK-PH-03 | Implementer replay: `.venv\Scripts\python scripts/phase20_full_backtest.py --start-date 2024-01-01 --end-date 2024-03-31 --allow-missing-returns --option-a-sector-specialist ...phase20_closeout_impl_*` | PASS (reproducible ABORT_PIVOT) | `data/processed/phase20_closeout_impl_summary.json` + CSV/PNG set | exit code `1`, decision `ABORT_PIVOT`, `3/6` gates |
| CHK-PH-03-B | Reviewer B independent replay: same command with `...phase20_closeout_revB_*` outputs | PASS (matches implementer) | `data/processed/phase20_closeout_revB_summary.json` + CSV/PNG set | same exit code `1`, same decision/gates, same row counts |
| CHK-PH-04 | Atomic write inspection + artifact sanity | PASS | `scripts/day5_ablation_report.py`, `data/processed/phase20_closeout_*` | atomic `tmp -> os.replace`; row counts match implementer/reviewer sets |
| CHK-PH-05 | Docs-as-code updates | PASS | docs files listed below | brief + handover + notes + lessons + decision log updated |

## 6) Open Risks / Assumptions / Rollback
- Open Risks:
  - Full regression gate is red (`6` failing tests), so phase-end governance cannot be marked PASS yet.
  - Existing backtest ledger includes multiple exploratory branches; production lock depends on not re-opening ranker drift without PM approval.
- Assumptions:
  - Phase 24 introduces forward-looking/alternative data and does not relax PIT safety controls.
- Rollback Note:
  - Revert lock change in `strategies/ticker_pool.py` and restore pre-close docs if PM rejects the Golden Master closure framing.

## 6.1) Data Integrity Evidence (Required)
- Atomic write path proof:
  - `scripts/day5_ablation_report.py` uses temp file suffix + `os.replace` for `_atomic_csv_write` and `_atomic_json_write`.
- Row-count sanity:
  - Implementer outputs: delta `1`, cash `61`, top20 `61`, sample `40`, crisis `4`.
  - Reviewer B outputs: delta `1`, cash `61`, top20 `61`, sample `40`, crisis `4`.
- Runtime/performance sanity:
  - Replay memory peak: `263.27 MB` (`tracemalloc`) for 2024-01-01..2024-03-31 replay.

## 7) Next Phase Roadmap
| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | Clear full regression failures and close CHK-PH-01 | `.venv\Scripts\python -m pytest -q` all green | Engineering |
| 2 | Freeze Phase 20 production config snapshot | no drift in ranker/gate equations vs notes/handover | Engineering + PM |
| 3 | Build Phase 24 Pod A feature ingestion contract | documented schema + PIT rules + tests | Data |
| 4 | Build Phase 24 Pod B sentiment/flow contract | documented signal definitions + source availability check | Research |
| 5 | Define Pod-rotation capital allocator | acceptance test for regime-switch behavior | Strategy |

## 8) New Context Packet (for /new)
- What was done:
  - Phase 20 closure docs/logs were consolidated and lock formulas were codified with artifact-backed evidence.
  - Option A cyclical-trough ranker was restored in code to match lock narrative.
  - Independent replay evidence (implementer + Reviewer B) was produced with matching outputs.
- What is locked:
  - Cluster ranker: `(CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`.
  - Hard entry gate requires both `mom_ok` and `support_proximity`.
  - Hard exit/selection is rank-threshold + entry-gate bound.
- What remains:
  - Phase 24 Pod A (Supercycle) feature ingestion is not started.
  - Phase 24 Pod B (Sentiment and Flow) feature ingestion is not started.
  - Pod-level capital rotation and PM dashboard are not started.
- Next-phase roadmap summary:
  - Build Supercycle Pod with forward features (NTM growth, EPS revisions, capex-to-sales, backlog mapping).
  - Build Sentiment and Flow Pod (VIX term structure, put/call, IV spikes, max pain, insider-flow signals).
  - Define pod-rotation capital allocator and publish PM monitor dashboard contract.
- Immediate first step:
  - Draft `docs/phase_brief/phase24-brief.md` with Pod A/B acceptance checks and PIT-safe schema contracts.

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve next phase" to start execution.
