# Legacy Quant and Benchmark Runbook Archive

> Historical commands preserved for reference only.
> These procedures are not part of the active governance control-plane operator flow described in `README.md`, `OPERATOR_LOOP_GUIDE.md`, or `docs/runbook_ops.md`.

## Data Management

- **Legacy price refresh note**: The data updater entrypoint no longer exists in this repo. Data-pipeline refresh commands are not currently part of the active control-plane workflow.
- **Legacy universe hydration note**: Broad market-data hydration is not currently present in this repo surface.
- **Update Fundamentals**: `python data/fundamentals_updater.py --scope "Top 500"`
- **Build Feature Store (Incremental default)**: `python data/feature_store.py --start-year 2000 --universe-mode yearly_union --yearly-top-n 100`
- **Build Feature Store (Forced full rebuild)**: `python data/feature_store.py --start-year 2000 --full-rebuild`
- **Rebuild Sector Map**: `python data/build_sector_map.py`

## Testing

- **Run All Tests**: `pytest`
- **Run Data Layer Tests**: `pytest tests/test_updater_parallel.py tests/test_feature_store.py tests/test_parallel_utils.py`
- **Run Data Validation Gate**: `python scripts/validate_data_layer.py`

## Baseline Benchmarking (Phase 18 Day 1)

- **Run Baseline Report**: `.venv\Scripts\python scripts/baseline_report.py --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --trend-risk-off-weight 0.5`
- **Output CSV (default)**: `data/processed/phase18_day1_baselines.csv`
- **Output Plot (default)**: `data/processed/phase18_day1_equity_curves.png`
- **Path Resolution Note**: relative CLI paths in `scripts/baseline_report.py` are resolved against repo root (`E:\Code\Quant`), not the caller working directory. Use absolute paths if external schedulers need other destinations.

## TRI Migration (Phase 18 Day 2)

- **Build TRI prices artifact**: `.venv\Scripts\python data/build_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --output data/processed/prices_tri.parquet --validation-csv data/processed/phase18_day2_tri_validation.csv --split-plot data/processed/phase18_day2_split_events.png`
- **Build macro TRI artifact**: `.venv\Scripts\python data/build_macro_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --input data/processed/macro_features.parquet --output data/processed/macro_features_tri.parquet`
- **Primary Day 2 outputs**:
  - `data/processed/prices_tri.parquet`
  - `data/processed/macro_features_tri.parquet`
  - `data/processed/phase18_day2_tri_validation.csv`
  - `data/processed/phase18_day2_split_events.png`

## Cash Overlay Benchmarking (Phase 18 Day 3)

- **Prerequisites**:
  - `data/processed/prices_tri.parquet` must exist (built in Day 2 via `data/build_tri.py`).
  - `data/processed/macro_features_tri.parquet` recommended (fallback: `macro_features.parquet`).
  - `data/processed/liquidity_features.parquet` recommended for EFFR context.
- **Run overlay comparison (6 scenarios)**: `.venv\Scripts\python scripts/cash_overlay_report.py --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --target-vol 0.15 --vol-lookbacks 20,60,120 --output-csv data/processed/phase18_day3_overlay_metrics.csv --output-plot data/processed/phase18_day3_overlay_3panel.png --output-stress-csv data/processed/phase18_day3_overlay_stress_checks.csv --output-corr-csv data/processed/phase18_day3_overlay_exposure_corr.csv`
- **Primary Day 3 outputs**:
  - `data/processed/phase18_day3_overlay_metrics.csv`
  - `data/processed/phase18_day3_overlay_stress_checks.csv`
  - `data/processed/phase18_day3_overlay_exposure_corr.csv`
  - `data/processed/phase18_day3_overlay_3panel.png`
- **Expected scenarios in metrics CSV**:
  - `Buy & Hold`
  - `Trend SMA200`
  - `Vol Target 15% (20d)`
  - `Vol Target 15% (60d)`
  - `Vol Target 15% (120d)`
  - `Trend Multi-Horizon`
- **Operational note**:
  - Script reuses FR-050 cash hierarchy from Phase 13 helpers and routes returns through `engine.run_simulation`; keep `--cost-bps` aligned with baseline comparables unless intentionally testing sensitivity.

## Company Scorecard Validation (Phase 18 Day 4)

- **Run scorecard validation**: `.venv\Scripts\python scripts/scorecard_validation.py --input-features data/processed/features.parquet --scoring-method complete_case --start-date 2015-01-01 --end-date 2024-12-31 --output-validation-csv data/processed/phase18_day4_scorecard_validation.csv --output-scores-csv data/processed/phase18_day4_company_scores.csv`
- **POSIX equivalent**: `.venv/bin/python scripts/scorecard_validation.py --input-features data/processed/features.parquet --scoring-method complete_case --start-date 2015-01-01 --end-date 2024-12-31 --output-validation-csv data/processed/phase18_day4_scorecard_validation.csv --output-scores-csv data/processed/phase18_day4_company_scores.csv`
- **Primary Day 4 outputs**:
  - `data/processed/phase18_day4_company_scores.csv`
  - `data/processed/phase18_day4_scorecard_validation.csv`
- **Expected validation checks**:
  - `score_coverage`
  - `factor_balance_max_share`
  - `adjacent_rank_correlation`
  - `quartile_spread_sigma`
- **Schema alignment note**:
  - `data/feature_store.py` now emits scorecard aliases:
    - `quality_composite`
    - `realized_vol_21d`
    - `illiq_21d`

## Day 5 Ablation Matrix (Phase 18 Day 5)

- **Run 9-config ablation matrix**: `.venv\Scripts\python scripts/day5_ablation_report.py --input-features data/processed/features.parquet --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --top-quantile 0.10 --allow-missing-returns --output-metrics-csv data/processed/phase18_day5_ablation_metrics.csv --output-deltas-csv data/processed/phase18_day5_ablation_deltas.csv --output-summary-json data/processed/phase18_day5_ablation_summary.json`
- **Strict mode (fail on missing active returns)**: remove `--allow-missing-returns`.
- **Matrix safety control**:
  - default `--max-matrix-cells 25000000`
  - increase only with explicit memory headroom.
- **Primary Day 5 outputs**:
  - `data/processed/phase18_day5_ablation_metrics.csv`
  - `data/processed/phase18_day5_ablation_deltas.csv`
  - `data/processed/phase18_day5_ablation_summary.json`
- **Expected summary fields**:
  - `baseline_id`
  - `optimal_id`
  - `acceptance.coverage_met`
  - `acceptance.spread_met`
  - `acceptance.turnover_reduction_met`
  - `acceptance.sharpe_preservation_met`

## Day 6 Walk-Forward Validation (Phase 18 Day 6)

- **Run Day 6 validator**: `.venv\Scripts\python scripts/day6_walkforward_validation.py --input-features data/processed/features.parquet --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --top-quantile 0.10 --c3-decay 0.95 --allow-missing-returns --output-dir data/processed`
- **Strict missing-return mode**: remove `--allow-missing-returns` to fail-fast when active-position return cells are missing.
- **Primary Day 6 outputs**:
  - `data/processed/phase18_day6_walkforward.csv`
  - `data/processed/phase18_day6_decay_sensitivity.csv`
  - `data/processed/phase18_day6_crisis_turnover.csv`
  - `data/processed/phase18_day6_checks.csv`
  - `data/processed/phase18_day6_summary.json`
- **Critical gate check**:
  - `CHK-54` from `phase18_day6_checks.csv` must be `pass=True`.
- **Mandatory missing-data check (when using `--allow-missing-returns`)**:
  - open `phase18_day6_summary.json`
  - inspect:
    - `missing_active_return_cells.baseline`
    - `missing_active_return_cells.c3`
  - if either value is `> 0`, treat run as a data-quality warning and do not promote as hard-pass without explicit acknowledgment.
- **Matrix safety control**:
  - default `--max-matrix-cells 25000000`
  - if raised, confirm memory headroom and record override in run notes.

## Stop-Loss Module Validation (Phase 21 Day 1)

- **Compile gate**: `.venv\Scripts\python -m py_compile strategies/stop_loss.py tests/test_stop_loss.py`
- **Unit gate**: `.venv\Scripts\python -m pytest tests/test_stop_loss.py -q`
- **Compatibility smoke**: `.venv\Scripts\python -m pytest tests/test_phase15_integration.py -q`
- **Behavioral contract**:
  - ATR mode must stay `proxy_close_only`.
  - ATR method must remain SMA over `abs(diff(close))`.
  - D-57 ratchet must keep stop non-decreasing (`stop_t >= stop_{t-1}`).
  - Drawdown tiers remain `-8%/-12%/-15%` with scales `0.75/0.50/0.00`.
- **Integration activation gate (Phase 21 Day 2+)**:
  - Do **not** enable stop-loss execution in live runtime until integration PR passes:
    - integration tests for stop-trigger exits and drawdown scaling,
    - telemetry emission checks for stop/drawdown state,
    - SAW round sign-off for wiring changes.
  - Owner/Handoff:
    - Owner: Strategy Engineering
    - Handoff: Quant Ops + Risk review
- **Runtime observability checks after activation**:
  - verify `atr_mode` logged as `proxy_close_only` in runtime context.
  - verify stop ratchet invariant on sampled positions (`stop_t >= stop_{t-1}`).
  - monitor stop-hit counts, underwater timeout exits, and drawdown tier transitions.
  - alert when:
    - tier-3 (`scale=0.0`) persists unexpectedly,
    - stop levels become non-finite/NaN,
    - ATR series becomes unavailable for active symbols.
- **Rollback if post-activation behavior deviates**:
  1. disable stop-loss wiring feature flag / integration path.
  2. revert to prior strategy execution path (pre-Phase 21 stop module usage).
  3. rerun compatibility smoke:
     - `.venv\Scripts\python -m pytest tests/test_phase15_integration.py -q`
  4. record incident and rollback details in `docs/decision log.md`.

## SDM 3-Pillar Ingestion + Assembly (Phase 23)

- **Fundamentals SDM dry-run (scoped)**:
  - `.venv\Scripts\python scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31 --dry-run`
- **Fundamentals SDM write (scoped)**:
  - `.venv\Scripts\python scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31`
- **Macro rates dry-run/write**:
  - `.venv\Scripts\python scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run`
  - `.venv\Scripts\python scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31`
- **FF five-factor dry-run/write**:
  - `.venv\Scripts\python scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run`
  - `.venv\Scripts\python scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31`
- **Final SDM assembler dry-run/write**:
  - `.venv\Scripts\python scripts/assemble_sdm_features.py --dry-run`
  - `.venv\Scripts\python scripts/assemble_sdm_features.py`
- **Outputs**:
  - `data/processed/fundamentals_sdm.parquet`
  - `data/processed/macro_rates.parquet`
  - `data/processed/ff_factors.parquet`
  - `data/processed/features_sdm.parquet`
  - `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`

## Emergency / Troubleshooting

- **Clear Cache**: Delete `data/processed/*.parquet` (safe, will trigger redownload).
- **Force Rebuild**: Delete `data/processed/fundamentals_snapshot.parquet` to force a clean snapshot generation.
