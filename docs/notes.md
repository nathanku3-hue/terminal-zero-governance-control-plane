# Phase 16.13 Formula Notes (Proxy Gate)

Date: 2026-02-17

## 1) Derived Quarterly Metrics
- `sales_growth_q = pct_change(total_revenue_q, 1)`
- `sales_accel_q = delta(sales_growth_q)`
- `op_margin_accel_q = delta(operating_margin_delta_q)`
- `bloat_q = delta(ln(total_assets_q - inventory_q)) - delta(ln(total_revenue_q))`
- `net_investment_q = (abs(capex_q) - depreciation_q) / lag(total_assets_q, 1)`

## 2) Inventory Quality Proxy
- `z_inventory_quality_proxy = z(sales_accel_q) + z(op_margin_accel_q) - z(bloat_q) - 0.5*z(net_investment_q)`

## 3) Discipline Conditional Gate
- Base penalty: `penalty = asset_growth_yoy * (1 - sigmoid(operating_margin_delta_q / smooth_factor))`
- Proxy gate waiver: if `z_inventory_quality_proxy > 0`, then `penalty = 0`
- Output term: `z_discipline_cond = z(-penalty)` (cross-sectional per date)

## 4) Capital Cycle Score
- `capital_cycle_score = 0.4*z_moat + 0.4*z_discipline_cond + 0.2*z_demand`

## 5) Implementation Files
- `data/fundamentals_updater.py` (raw + derived quarterly fields)
- `data/fundamentals_compustat_loader.py` (Compustat parity for derived fields)
- `data/fundamentals.py` (snapshot/daily broadcast propagation)
- `data/fundamentals_panel.py` (daily panel schema + SQL projection)
- `data/feature_specs.py` (proxy score + discipline waiver logic)
- `data/feature_store.py` (feature context + output wiring)

---

# Phase 17.1 Formula Notes (Cross-Sectional Backtester)

Date: 2026-02-19

## 1) Forward Return
- `fwd_return_{t,h} = adj_close_{t+h} / adj_close_t - 1`
- Implementation:
  - `scripts/evaluate_cross_section.py` (`load_eval_frame`, DuckDB `LEAD(adj_close, h)` window).

## 2) Double Sort
- Sort 1 (high growth bucket, by date/industry):
  - `High_Asset_Growth = top 30% of asset_growth_yoy within (date, industry)`
- Sort 2 (inside Sort 1 bucket):
  - assign proxy deciles from ordered `z_inventory_quality_proxy` within `(date, industry)`:
    - `decile = floor((rank_position * 9) / (n-1)) + 1`, clipped to `[1, 10]`
- Spread:
  - `spread_t = mean(fwd_return_t | decile=10) - mean(fwd_return_t | decile=1)`
- Implementation:
  - `scripts/evaluate_cross_section.py` (`compute_double_sort`).

## 3) Inference Metrics
- Period mean:
  - `mean = E[spread_t]`
- Period volatility:
  - `vol = std(spread_t)`
- Sharpe:
  - `period_sharpe = mean / vol`
  - `annualized_sharpe = period_sharpe * sqrt(252 / horizon_days)`
- Newey-West lag (auto):
  - `lag = floor(4 * (T/100)^(2/9))`
- Newey-West t-stat for spread mean:
  - OLS on constant with HAC covariance.
- Implementation:
  - `scripts/evaluate_cross_section.py` (`auto_newey_west_lags`, `newey_west_mean_test`, `summarize_spread`).

## 4) Fama-MacBeth Specification
- Cross-sectional regression per date:
  - `fwd_return_{i,t+h} = alpha_t + beta1_t*asset_growth_{i,t} + beta2_t*z_proxy_{i,t} + beta3_t*(asset_growth_{i,t}*z_proxy_{i,t}) + eps_{i,t}`
- Time-series stage:
  - report mean beta and Newey-West t-stat for each beta series (`beta1_t`, `beta2_t`, `beta3_t`).
- Interaction acceptance diagnostic:
  - `beta3_mean > 0` and statistically significant (`p < 0.05`).
- Implementation:
  - `scripts/evaluate_cross_section.py` (`run_fama_macbeth`).

---

# Phase 17.2 Formula Notes (Parameter Sweep, CSCV, DSR)

Date: 2026-02-19

## 1) Correlation-Adjusted Effective Trials
- Let `N` be the number of tested variants and `rho_avg` the average off-diagonal correlation of variant return streams.
- Effective trial count:
  - `N_eff ~= N * (1 - rho_avg) + 1`
  - bounded in implementation to `[1, N]`.
- Implementation:
  - `utils/statistics.py` (`average_pairwise_correlation`, `effective_number_of_trials`).
  - Used by `scripts/parameter_sweep.py`.

## 2) CSCV Split Geometry and PBO
- Split time index into `S` contiguous even blocks (`S in {6, 8, 10}`).
- Enumerate all train/test splits:
  - `splits = C(S, S/2)` where train uses `S/2` blocks and test is the complement.
- Per split:
  - pick train-best variant by Sharpe.
  - evaluate that variant rank in test cross-section.
  - transform relative rank `r` to:
    - `lambda = log(r / (1 - r))`.
- Probability of Backtest Overfitting:
  - `PBO = mean(lambda <= 0)`.
- Implementation:
  - `utils/statistics.py` (`build_cscv_splits`, `build_cscv_block_series`, `cscv_analysis`).
  - Called in `scripts/parameter_sweep.py`.

## 3) Deflated Sharpe Ratio (Bailey & Lopez de Prado Convention)
- Estimated Sharpe of each variant stream:
  - `SR_hat = mean(R) / std(R) * sqrt(periods_per_year)`.
- Expected max Sharpe benchmark under multiple testing:
  - `SR* = E[max(SR)]` approximation from estimated Sharpe distribution and `N_eff`.
- Non-normality-adjusted probabilistic Sharpe:
  - `PSR = Phi( (SR_hat - SR*) * sqrt(n-1) / sqrt(1 - skew*SR_hat + ((kurt-1)/4)*SR_hat^2) )`
  - where `Phi` is the standard normal CDF.
- Deflated Sharpe Ratio:
  - `DSR = PSR`.
- Implementation:
  - `utils/statistics.py` (`safe_sharpe`, `expected_max_sharpe`, `probabilistic_sharpe_ratio`, `deflated_sharpe_ratio`).
  - Applied per variant in `scripts/parameter_sweep.py`.

## 4) Coarse-to-Fine Sweep Topology
- Stage 1 (coarse):
  - evaluate bounded coarse grid (local cap <= 200 combos).
- Stage 2 (fine):
  - center around coarse winner and test neighborhood steps.
- Ranking contract:
  - sort by `DSR` first, then `t_stat_nw`, then spread mean.
- Implementation:
  - `scripts/parameter_sweep.py` (`_build_coarse_grid`, `_build_fine_grid`, `_evaluate_grid`, ranking block in `main`).

---

# Phase 17.3 Prep Notes (Execution Hardening)

Date: 2026-02-19

## 1) Deterministic Variant Identity
- Variant key generation:
  - `variant_id = md5(json(sorted(params)))`
- Contract:
  - stable under key-order changes and robust to grid-order reshuffles.
  - hash payload is restricted to canonical sweep parameter keys (non-parameter metadata ignored).
- Implementation:
  - `scripts/parameter_sweep.py` (`_variant_id_from_params`).

## 2) Fine-Grid Anchor Rule
- Coarse winner selection for fine search:
  - primary: `DSR`
  - tie-break 1: `t_stat_nw`
  - tie-break 2: `period_mean`
  - tie-break 3: deterministic `variant_id` lexical order (stable sort).
- Rationale:
  - refines around the most robust candidate instead of highest raw in-sample signal.
- Implementation:
  - `scripts/parameter_sweep.py` (`_best_row(..., primary_metric='dsr')` in `main`).

## 3) Checkpoint / Resume Policy
- Checkpoint artifacts:
  - `.checkpoint_<prefix>.json`
  - `.checkpoint_<prefix>_results.csv`
  - `.checkpoint_<prefix>_streams.csv`
- Auto checkpoint cadence (`--checkpoint-every=0`):
  - `<=80 variants -> 10`
  - `<=250 variants -> 20`
  - `>250 variants -> 50`
- Resume behavior:
  - default ON, disable with `--no-resume`
  - stage skips use completed `(result + stream)` variant IDs.
- Implementation:
  - `scripts/parameter_sweep.py` (`_checkpoint_paths`, `_save_checkpoint`, `_load_checkpoint`, `_resolve_checkpoint_every`, `_evaluate_grid`).

## 4) Partition-Read Batching for Feature Upsert
- Upsert read optimization:
  - load all touched `(year, month)` partitions in one DuckDB query.
  - reuse one DuckDB connection per `_atomic_upsert_features` execution.
- Implementation:
  - `data/feature_store.py` (`_load_feature_partition_slices`, `_atomic_upsert_features`).

---

# Phase 17 Closeout Notes (Windows Lock Safety)

Date: 2026-02-19

## 1) Windows PID Liveness Contract
- Windows path avoids `os.kill(pid, 0)` and uses WinAPI:
  - `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, ...)`
  - `GetExitCodeProcess(handle, ...)`
  - liveness condition: `exit_code == STILL_ACTIVE (259)`.
- Non-Windows path keeps:
  - `os.kill(pid, 0)` probe semantics.
- Implementation:
  - `scripts/parameter_sweep.py` (`_pid_is_running`).

## 2) Corrupt Lock TTL Recovery Fallback
- Primary lock age:
  - `age_seconds = now_utc - created_at_utc` (from lock payload).
- Fallback lock age when payload is unreadable/missing:
  - `age_seconds = now_utc - file_mtime(lock_path)`.
- Recovery rule:
  - if `age_seconds >= stale_lock_seconds`, attempt stale-lock removal with bounded retries.
- Implementation:
  - `scripts/parameter_sweep.py` (`_lock_age_seconds`, `_lock_file_age_seconds`, `_acquire_sweep_lock`, `_recover_stale_lock`).

## 3) Regression Coverage
- Lock regression tests:
  - `tests/test_parameter_sweep.py::test_sweep_lock_rejects_live_pid`
  - `tests/test_parameter_sweep.py::test_sweep_lock_recovers_dead_pid`
  - `tests/test_parameter_sweep.py::test_sweep_lock_ttl_fallback_recovers_invalid_pid_lock`
  - `tests/test_parameter_sweep.py::test_sweep_lock_ttl_fallback_recovers_corrupt_lock_by_file_mtime`
  - `tests/test_parameter_sweep.py::test_sweep_lock_recovery_is_bounded_when_remove_fails`
  - `tests/test_parameter_sweep.py::test_evaluate_grid_resume_only_path_keeps_existing_state_and_triggers_checkpoint`

---

# Phase 18 Day 1 Formula Notes (Baseline Benchmarking)

Date: 2026-02-19

## 1) SPY Return and Cash Return
- SPY daily return:
  - `spy_ret_t = spy_close_t / spy_close_{t-1} - 1`
- Cash daily return hierarchy:
  - `cash_ret_t = bil_ret_t` when available
  - else `cash_ret_t = effr_rate_t / 100 / 252`
  - else `cash_ret_t = 0.02 / 252`
- Implementation:
  - `scripts/baseline_report.py` (`load_market_inputs`)
  - FR-050 helper: `backtests/verify_phase13_walkforward.py` (`build_cash_return`)

## 2) Baseline Target Weights
- Buy & Hold:
  - `w_target_t = 1.0`
- Static 50/50:
  - `w_target_t = 0.5`
- Trend SMA200:
  - `sma200_t = mean(spy_close_{t-199..t})`
  - `w_target_t = 1.0 if spy_close_t > sma200_t else w_risk_off`
  - default `w_risk_off = 0.5` (CLI override via `--trend-risk-off-weight`)
- Implementation:
  - `scripts/baseline_report.py` (`build_trend_target_weight`, `run_baselines`)

## 3) Engine-Parity Execution and Costs
- Executed weight (D-04):
  - `w_exec_t = w_target_{t-1}`
- Excess-return sleeve passed to engine:
  - `r_excess_t = spy_ret_t - cash_ret_t`
- Engine net excess return:
  - `r_net_excess_t = w_exec_t * r_excess_t - cost_t`
- Turnover/cost (D-05):
  - `turnover_t = |w_exec_t - w_exec_{t-1}|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Portfolio net return:
  - `r_port_t = cash_ret_t + r_net_excess_t`
- Implementation:
  - `scripts/baseline_report.py` (`simulate_single_baseline`)
  - `engine.py` (`run_simulation`)

## 4) Report Metrics
- Equity curve:
  - `equity_t = Π(1 + r_port_i), i=1..t`
- Annualized volatility:
  - `ann_vol = std(r_port) * sqrt(252)`
- Annualized turnover:
  - `turnover_annualized = mean(turnover_t) * 252`
- Total turnover:
  - `turnover_total = Σ turnover_t`
- CAGR / Sharpe / MaxDD / Ulcer:
  - FR-050 helpers reused directly from `backtests/verify_phase13_walkforward.py`
- Implementation:
  - `scripts/baseline_report.py` (`simulate_single_baseline`, `run_baselines`)

---

# Phase 18 Day 1 Addendum (SSOT Metrics + Final Artifact Contract)

Date: 2026-02-19

## 1) Metric SSOT Consolidation
- Metric functions extracted to:
  - `utils/metrics.py`
- Canonical formulas used by code:
  - `CAGR = (equity_T / equity_0)^(1/years) - 1`
  - `Sharpe = mean(excess_ret) / std(excess_ret) * sqrt(periods_per_year)`
  - `MaxDD = min((equity / cummax(equity)) - 1)`
  - `Ulcer = sqrt(mean((100 * drawdown)^2))`
  - `Turnover_t = sum(abs(weights_t - weights_{t-1}))`
- Delegation compatibility:
  - `backtests/verify_phase13_walkforward.py` keeps existing helper names but delegates to `utils/metrics.py`.

## 2) Day 1 Output Contract (Final)
- CSV output (single summary table):
  - `data/processed/phase18_day1_baselines.csv`
- CSV columns:
  - `baseline,cagr,sharpe,max_dd,ulcer,turnover_annual,turnover_total,start_date,end_date,n_days`
- Plot output:
  - `data/processed/phase18_day1_equity_curves.png`
  - log-scale y-axis
  - matplotlib primary path, Pillow fallback when matplotlib is unavailable.

## 3) Baseline Return Equation (Implemented)
- `w_exec_t = shift(w_target_t, 1)` (D-04)
- `r_excess_t = spy_ret_t - cash_ret_t`
- `cost_t = turnover_t * (cost_bps / 10000)` where `turnover_t = |w_exec_t - w_exec_{t-1}|` (D-05)
- `r_port_t = cash_ret_t + w_exec_t * r_excess_t - cost_t`
- File reference:
  - `scripts/baseline_report.py` (`simulate_single_baseline`)

---

# Phase 18 Day 2 Formula Notes (TRI Migration)

Date: 2026-02-19

## 1) Per-Asset TRI Construction
- Core factor:
  - `factor_t = 1 + total_ret_t`
- Guardrail handling:
  - if `total_ret_t` is missing -> `factor_t = 1`
  - if `total_ret_t <= -1` -> `factor_t = 0` (terminal/invalid loss cap)
- TRI path:
  - `TRI_t = base_value * cumprod(factor_t)`
- File reference:
  - `data/build_tri.py` (`build_prices_tri`)

## 2) Schema Guardrail (Split Trap Barrier)
- Legacy signal source renamed:
  - `adj_close -> legacy_adj_close`
- Day 2 contract:
  - signal/indicator layer uses `tri`
  - execution layer keeps `total_ret`
- File references:
  - `data/build_tri.py` (artifact schema projection)
  - `data/feature_store.py` (TRI-first source selection + compatibility output)

## 3) Split Continuity Validation
- For known split dates:
  - `tri_pct_t = TRI_t / TRI_{t-1} - 1`
  - `expected_pct_t = total_ret_t`
  - pass when `abs(tri_pct_t - expected_pct_t) <= tolerance`
- This checks continuity against causal return input (avoids false failure from genuine split-day market moves).
- File reference:
  - `data/build_tri.py` (`build_validation_report`)

## 4) Dividend Capture Sanity Check
- Trailing 1-year delta:
  - `delta_dividend_effect = tri_return_1y - legacy_adj_close_return_1y`
- Expected sign:
  - `delta_dividend_effect >= 0` for high-yield validation tickers.
- File reference:
  - `data/build_tri.py` (`build_validation_report`)

## 5) Macro TRI Extension
- Added TRI columns:
  - `spy_tri`, `vix_tri`, `mtum_tri`, `dxy_tri`
- Recomputed derived fields:
  - `vix_proxy = rolling_std(pct_change(spy_tri), 20) * sqrt(252) * 100`
  - `mtum_spy_corr_60d = rolling_corr(pct_change(mtum_tri), pct_change(spy_tri), 60)`
  - `dxy_spx_corr_20d = rolling_corr(pct_change(dxy_tri), pct_change(spy_tri), 20)`
- File reference:
  - `data/build_macro_tri.py`

## 6) Runtime Integration Notes
- `app.py` prefers `prices_tri.parquet` and `macro_features_tri.parquet` when present.
- `strategies/investor_cockpit.py` carries `tri` in feature history and uses it when available for price-side checks.
- `data/feature_store.py` persists both `adj_close` (compatibility) and `tri` (signal-safe column).

---

# Phase 18 Day 3 Formula Notes (Cash Overlay)

Date: 2026-02-20

## 1) Scenario Set (6 total)
- `Buy & Hold`: `w_target_t = 1.0`
- `Trend SMA200`: `w_target_t = 1.0 if TRI_t > SMA200_t else 0.5`
- `Vol Target 15% (20/60/120d)`: three lookback variants
- `Trend Multi-Horizon`: weighted MA score (`50/100/200`, weights `0.5/0.3/0.2`)
- File reference:
  - `scripts/cash_overlay_report.py` (`run_scenarios`)

## 2) Volatility-Target Overlay Formula
- Realized volatility (lag-safe):
  - `sigma_t = std(spy_ret_{t-lookback..t-1}) * sqrt(252)`
- Target exposure:
  - `w_target_t = clip(0.15 / sigma_t, 0, 1)`
- Warm-up handling:
  - before valid window, fill `w_target_t = 1.0`
- File reference:
  - `strategies/cash_overlay.py` (`VolatilityTargetOverlay.compute_exposure`)

## 3) Trend Multi-Horizon Overlay Formula
- Lagged price:
  - `p_lag_t = TRI_{t-1}`
- For each MA window `i`:
  - `MA_i,t = mean(p_lag_{t-i+1..t})`
  - `signal_i,t = +1 if p_lag_t > MA_i,t else -1`
- Weighted score:
  - `score_t = sum_i(weight_i * signal_i,t)`
- Exposure mapping:
  - `w_target_t = clip(0.5 + 0.5 * score_t, 0, 1)`
- File reference:
  - `strategies/cash_overlay.py` (`TrendFollowingOverlay.compute_exposure`)

## 4) Portfolio Return, Lag, and Cost Path
- Executed exposure (D-04):
  - `w_exec_t = shift(w_target_t, 1)`
- Excess-return sleeve sent to engine:
  - `r_excess_t = spy_ret_t - cash_ret_t`
- Engine net excess:
  - `r_net_excess_t = w_exec_t * r_excess_t - cost_t`
- Turnover/cost (D-05):
  - `turnover_t = |w_exec_t - w_exec_{t-1}|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Portfolio net return (FR-050 cash hierarchy applied):
  - `r_port_t = cash_ret_t + r_net_excess_t`
- File references:
  - `scripts/cash_overlay_report.py` (`simulate_overlay_strategy`)
  - `engine.py` (`run_simulation`)

## 5) Stress and Correlation Diagnostics
- Stress-window exposure summary:
  - `exposure_min`, `exposure_mean`, `exposure_max` per scenario/window
  - windows: `covid_crash`, `inflation_shock`, `low_vol_meltup`, `rate_hikes_q4`
- Exposure orthogonality:
  - Pearson correlation matrix on executed exposure series.
- File references:
  - `scripts/cash_overlay_report.py` (`build_stress_checks`, `build_exposure_corr`)

## 6) Day 3 Regression Fix Note
- `_load_inputs` now passes datetime-indexed macro context into FR-050 `_build_context`.
- Prevents mixed-index sort error (`Timestamp` vs `int`) when liquidity context is present.
- File references:
  - `scripts/cash_overlay_report.py` (`_load_inputs`)
  - `tests/test_cash_overlay.py` (`test_load_inputs_uses_datetime_index_for_fr050_context`)

---

# Phase 18 Day 4 Formula Notes (Company Scorecard)

Date: 2026-02-20

## 1) Linear Factor Score
- Core equation:
  - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t))`
- where:
  - `w_k`: factor weight
  - `sign_k`: `+1` for positive factors, `-1` for negative factors
  - `N_k(i,t)`: normalized factor value for stock `i` on date `t`
- File references:
  - `strategies/company_scorecard.py` (`compute_scores`)
  - `strategies/factor_specs.py` (`build_default_factor_specs`)

## 2) Cross-Sectional Normalization
- Z-score normalization (default):
  - `N_k(i,t) = (x_k(i,t) - μ_k,t) / σ_k,t`
- Rank normalization:
  - `N_k(i,t) = rank_pct(x_k(i,t))`
- Raw normalization:
  - `N_k(i,t) = x_k(i,t)`
- File reference:
  - `strategies/company_scorecard.py` (`_normalize`)

## 3) Day 4 Default Factor Set (Equal Weights)
- Momentum (`+`): `resid_mom_60d`
- Quality (`+`): `quality_composite` (fallback `capital_cycle_score`)
- Volatility (`-`): `realized_vol_21d` (fallback `yz_vol_20d`)
- Illiquidity (`-`): `illiq_21d` (fallback `amihud_20d`)
- Weight vector:
  - `[0.25, 0.25, 0.25, 0.25]`
- File references:
  - `strategies/factor_specs.py`
  - `data/feature_store.py` (Day 4 alias columns)

## 4) Control-Theory Upgrade Toggles (Default OFF)
- Sigmoid blender:
  - `sigmoid(x) = 2 / (1 + exp(-k*x)) - 1`
- Dirty derivative:
  - `x'_t = x_t - x_{t-1}`
- Leaky integrator:
  - `x~_t = EWMA_alpha(x_t)`
- Day 4 baseline policy:
  - all toggles `False`; wiring only, no ablation activation
- File references:
  - `strategies/factor_specs.py` (`FactorSpec` toggles)
  - `strategies/company_scorecard.py` (`_apply_control_toggles`)

## 5) Validation Metrics
- Score coverage:
  - `coverage = non_null(score) / total_rows`
- Factor dominance:
  - per-row share `= |contrib_k| / Σ_j |contrib_j|`
  - evaluate max mean share across factors
- Stability:
  - Spearman rank correlation between adjacent dates
- Quartile separation:
  - `spread_sigma = (mean(Q1) - mean(Q4)) / std(score)`
- File reference:
  - `scripts/scorecard_validation.py` (`build_validation_table`)

---

# Phase 18 Day 5 Formula Notes (Ablation Matrix)

Date: 2026-02-20

## 1) Score Validity Modes
- Complete-case:
  - `valid_i,t = AND_k isfinite(N_k(i,t))`
  - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t))` only when `valid_i,t = True`
- Partial:
  - `valid_i,t = OR_k isfinite(N_k(i,t))`
  - `Score_i,t = [Σ_k (w_k * sign_k * N_k(i,t))] / [Σ_k (w_k * 1_{k available})]`
- Impute-neutral:
  - `valid_i,t = OR_k isfinite(N_k(i,t))`
  - missing factor contribution treated as `0`:
    - `Score_i,t = Σ_k (w_k * sign_k * N_k(i,t, missing->0))`
- File reference:
  - `strategies/company_scorecard.py` (`compute_scores`)

## 2) Top-Quantile Portfolio Construction
- Per-date descending rank:
  - `rank_desc(i,t) = rank(score_i,t, descending, method=first)`
- Selected names:
  - `n_select_t = ceil(top_quantile * n_valid_t)`
  - `selected_i,t = 1 if rank_desc(i,t) <= n_select_t else 0`
- Target weight:
  - `w_target(i,t) = selected_i,t / n_select_t`
- File reference:
  - `scripts/day5_ablation_report.py` (`_build_target_weights`)

## 3) Backtest Path (D-04/D-05)
- Engine input:
  - target matrix `W_target(t,i)` from Day 5 scores
  - return matrix `R(t,i)` from `prices_tri.total_ret`
- Execution lag:
  - `W_exec(t,i) = W_target(t-1,i)` (inside `engine.run_simulation`)
- Turnover/cost:
  - `turnover_t = Σ_i |W_exec(t,i) - W_exec(t-1,i)|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
- Net return:
  - `r_net_t = Σ_i (W_exec(t,i) * R(t,i)) - cost_t`
- Equity:
  - `equity_t = Π(1 + r_net_j), j=1..t`
- File references:
  - `scripts/day5_ablation_report.py` (`_simulate_scores_strategy`)
  - `engine.py` (`run_simulation`)

## 4) Day 5 Delta Metrics
- Baseline anchor: `BASELINE_DAY4`
- For each metric `m`:
  - `delta_m(config) = m(config) - m(baseline)`
- Turnover reduction:
  - `turnover_reduction = 1 - turnover_annual(config) / turnover_annual(baseline)`
- Optimal selection gates:
  - `coverage >= target_coverage`
  - `quartile_spread_sigma >= target_spread`
  - `turnover_reduction >= target_turnover_reduction`
  - `sharpe >= sharpe_baseline`
- File references:
  - `scripts/day5_ablation_report.py` (`_build_deltas`, `_select_optimal`)

## 5) Runtime Guardrails Added
- Dense matrix cap:
  - fail if `n_dates * max(1, n_permnos) > max_matrix_cells`
- Missing active returns:
  - default fail-fast on active-position missing cells
  - optional override: `--allow-missing-returns` => warn + zero-impute
- Empty input window:
  - writes empty artifacts with `status=no_data` and exits non-zero.
- File reference:
  - `scripts/day5_ablation_report.py` (`main`, `_simulate_scores_strategy`)

---

# Phase 18 Day 6 Formula Notes (Walk-Forward Validation)

Date: 2026-02-20

## 1) Leaky Integrator Parameterization
- Day 6 C3 setting:
  - `decay = 0.95`
  - `alpha = 1 - decay = 0.05`
- Integrator recurrence (per factor series per permno):
  - `I_t = (1 - alpha) * I_{t-1} + alpha * x_t`
  - implemented as EWMA with `alpha=0.05`, `adjust=False`.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`_build_c3_specs`)
  - `strategies/company_scorecard.py` (`_apply_control_toggles`)

## 2) Walk-Forward Window Mechanics
- Train/test windows (`W1..W4`) are evaluated as:
  - train metrics on `[train_start, train_end]`
  - test metrics on `[test_start, test_end]`
- Temporal isolation:
  - scores are generated on chronologically ordered history only,
  - no future rows are used in score computation,
  - execution remains `shift(1)` through engine path.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`run_walk_forward_validation`)

## 3) Portfolio Simulation Path
- Selection:
  - `n_select_t = ceil(top_quantile * n_valid_t)`
  - top-ranked names get equal target weights.
- Execution/cost:
  - `w_exec_t = w_target_{t-1}`
  - `turnover_t = sum_i |w_exec_t(i) - w_exec_{t-1}(i)|`
  - `cost_t = turnover_t * (cost_bps / 10000)`
  - `net_ret_t = sum_i(w_exec_t(i) * ret_t(i)) - cost_t`
- File references:
  - `scripts/day6_walkforward_validation.py` (`_simulate_from_scores`)
  - `engine.py` (`run_simulation`)

## 4) Day 6 Check Computations
- Drawdown duration:
  - longest consecutive run where `equity_t < rolling_peak_t`.
- Recovery speed:
  - index distance from `recovery_start` to first date where equity regains pre-start peak.
- Beta:
  - `beta = cov(port_ret, spy_ret) / var(spy_ret)`.
- Rank stability:
  - mean adjacent-date Spearman rank correlation on cross-sectional scores.
- File references:
  - `scripts/day6_walkforward_validation.py` (`_compute_drawdown_duration`, `_days_to_new_high`, `_compute_beta`, `_adjacent_rank_corr`)

## 5) Decay Plateau Diagnostics (CHK-51..53)
- Gradient smoothness:
  - `max(abs(gradient(sharpe(decay_grid)))) < 0.05`.
- Peak-width:
  - at least 3 decay points within `0.03` Sharpe of the best decay.
- Symmetry:
  - `abs((S_0.95 - S_0.90) - (S_0.95 - S_0.98)) < 0.05`.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`analyze_decay_sensitivity`, `evaluate_checks`)

## 6) Crisis Turnover Gate (CHK-54)
- For each crisis window:
  - `reduction_pct = 100 * (turnover_base - turnover_c3) / turnover_base`
  - pass condition: `reduction_pct >= 15` and `turnover_c3 < turnover_base`
- Global CHK-54 pass:
  - all crisis windows pass simultaneously.
- File reference:
  - `scripts/day6_walkforward_validation.py` (`validate_crisis_turnover`)

---

# Phase 21 Day 1 Formula Notes (Stop-Loss & Drawdown Control)

Date: 2026-02-20

## 1) ATR Proxy (Close-Only, SMA)
- Mode:
  - `atr_mode = proxy_close_only`
- Daily range proxy:
  - `range_t = |close_t - close_{t-1}|`
- ATR:
  - `ATR_t = SMA(range_t, window=20)`
- File reference:
  - `strategies/stop_loss.py` (`ATRCalculator.compute_atr`)

## 2) Initial and Trailing Stop Formulas
- Initial stop at entry:
  - `stop_initial = entry_price - (K_initial * ATR_entry)`
  - `K_initial = 2.0`
- Trailing candidate:
  - `stop_trailing_candidate_t = price_t - (K_trailing * ATR_t)`
  - `K_trailing = 1.5`
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.enter_position`, `StopLossManager.update_stop`)

## 3) D-57 Ratchet Invariant
- Non-decreasing stop:
  - `stop_t = max(stop_{t-1}, stop_candidate_t)`
- Invariant:
  - `stop_t >= stop_{t-1}` for every update step.
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.update_stop`)

## 4) Time-Based Underwater Exit
- Underwater condition:
  - `price_t <= entry_price`
- Exit rule:
  - force exit when `days_held > max_underwater_days` while underwater.
- Day 1 default:
  - `max_underwater_days = 60`
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager.update_stop`)

## 5) Drawdown Circuit Breakers
- Drawdown:
  - `dd_t = (equity_t - peak_equity_t) / peak_equity_t`
- Tiers:
  - if `dd_t <= -0.15` => scale `0.00`
  - else if `dd_t <= -0.12` => scale `0.50`
  - else if `dd_t <= -0.08` => scale `0.75`
  - else scale `1.00`
- Recovery:
  - if currently in tier mode and `dd_t > -0.04`, reset to scale `1.00`.
- File reference:
  - `strategies/stop_loss.py` (`PortfolioDrawdownMonitor.update_equity`)

## 6) Zero-Volatility Safety Switch
- Optional microscopic floor:
  - `stop <= reference_price - min_stop_distance_abs`
- Default Day 1 setting:
  - `min_stop_distance_abs = 0.0` (disabled by default)
- Intended use:
  - avoid zero-distance stop placement when ATR is exactly zero.
- File reference:
  - `strategies/stop_loss.py` (`StopLossManager._enforce_min_stop_distance`)

---

# Phase 21.1 Formula Notes (Anchor-Injected Cyclical Centroid)

Date: 2026-02-21

## 1) Anchor-Injected Cyclical Centroid in z-Space
- Anchor set:
  - `A = {MU, LRCX, AMAT, KLAC, STX, WDC}`
- Daily available anchors:
  - `A_t = {i in slice_t | ticker_i in A}`
- Centroid (primary path):
  - `mu_cyc_t = mean_{i in A_t}(z_i_t)`
- File reference:
  - `strategies/ticker_pool.py` (`_compute_cyc_centroid_anchor_injected`)

## 2) No-Anchor Fallback Centroid (Legacy Top-k)
- Trigger:
  - `|A_t| = 0`
- Fallback index set:
  - `K_t = TopK(score_col_prepool, k=centroid_top_k)`
- Fallback centroid:
  - `mu_cyc_t = mean_{i in K_t}(z_i_t)`
- Empty fallback safety:
  - if `K_t` is empty after NaN filtering, return zero vector.
- File reference:
  - `strategies/ticker_pool.py` (`_compute_cyc_centroid_anchor_injected`)

## 3) Pre-Pool Score Guard (Chicken-and-Egg Prevention)
- Rule:
  - `score_col` must not be pool-derived (`mahalanobis_*`, `posterior_*`, `odds_*`, `pool_*`, `compounder_prob`).
- Behavior:
  - raise `ValueError` if forbidden score column is passed.
- File reference:
  - `strategies/ticker_pool.py` (`_assert_pre_pool_score_col`)

## 4) Anchor-Priority Long Ranking Boost
- Base eligibility:
  - `valid_i = (MahDist_k_cyc_i <= 5.0) and (odds_ratio_i > 0.5)`
- Anchor bonus level:
  - `B_t = max_{j notin A}(odds_ratio_j) + 1`, fallback `B_t = 10` when non-anchor set is empty.
- Final score:
  - `odds_score_i = odds_ratio_i + B_t * 1_{i in A}` if `valid_i`, else `-9999`.
- File reference:
  - `strategies/ticker_pool.py` (inside `rank_ticker_pool`)

## 5) Path1 Runtime Gates and Deterministic Resample Rule
- Sector-balanced resample depth is computed on known sector labels only:
  - `counts_known = counts(sector != 'UNKNOWN')`
  - `per_sector = min(counts_known)`
  - if `per_sector < 2`, fallback mode is used.
- Non-finite sector projection residualization is hard-fail for that date slice:
  - `if residual_mode == 'projection_nonfinite_fallback': skip date slice + CRITICAL log`
- Slice runner exposes explicit mode toggle:
  - `--dictatorship-mode on|off`
  - `on -> DICTATORSHIP_MODE='PATH1_STRICT'`
  - `off -> DICTATORSHIP_MODE='PATH1_DEPRECATED'`
- File reference:
  - `strategies/ticker_pool.py` (`_deterministic_sector_balanced_resample`, `rank_ticker_pool`)
  - `scripts/phase21_1_ticker_pool_slice.py` (`parse_args`, `main`)

---

# Phase 21.1 Path1 Formula Notes (Sector Context + Dictatorship Telemetry)

Date: 2026-02-21

## 1) Deterministic Sector/Industry Attach (Before Pool Ranking)
- Source:
  - `data/static/sector_map.parquet`
- Priority order:
  - `context_permno = latest(sector, industry by permno)`
  - `context_ticker = latest(sector, industry by ticker)`
  - `context = coalesce(context_permno, context_ticker, 'Unknown')`
- Deterministic selection:
  - sort rows by `updated_at DESC`, then stable tie-breakers, then keep first key row.
- File reference:
  - `strategies/company_scorecard.py` (`_load_sector_context_maps`, `_attach_sector_industry_context`)

## 2) Path1 Context Attachment Flag
- Source label:
  - `sector_context_source_i = 'permno' if permno-map hit else 'ticker' if ticker-map hit else 'unknown'`
- Attachment flag:
  - `path1_sector_context_attached_i = 1{sector_context_source_i != 'unknown'}`
- File reference:
  - `strategies/company_scorecard.py` (`_attach_sector_industry_context`)

## 3) Path1 Directive and DICTATORSHIP_MODE Output Fields
- Constant fields:
  - `DICTATORSHIP_MODE = 'PATH1_STRICT'`
  - `path1_directive_id = 'PATH1_SECTOR_CONTEXT_PRE_RANK'`
- Emitted to:
  - sample CSV rows and summary JSON telemetry.
- File reference:
  - `scripts/phase21_1_ticker_pool_slice.py` (`main`)

## 4) Path1 Summary Telemetry Formulas
- Block-level attachment coverage:
  - `context_attached_ratio_in_block = context_attached_rows_in_block / max(1, block_rows)`
- Sector/industry known counts:
  - `known_sector_rows_in_block = sum(1{sector not in ['', 'Unknown', NaN]})`
  - `known_industry_rows_in_block = sum(1{industry not in ['', 'Unknown', NaN]})`
- Source mix:
  - `context_source_counts_in_block = frequency(sector_context_source)`
- Sample composition:
  - `sample_sector_counts = frequency(sample.sector)`
  - `sample_industry_counts = frequency(sample.industry)`
- File reference:
  - `scripts/phase21_1_ticker_pool_slice.py` (`main`, `_known_context_mask`)

---

# Phase 22 Formula Notes (Separability Harness)

Date: 2026-02-21

## 1) Cluster Stability (Jaccard Overlap)
- Ranking basis:
  - `odds_score` descending.
- Sets:
  - `S_decile_t = top ceil(0.10 * N_t) tickers by odds_score`
  - `S_30_t = top min(30, N_t) tickers by odds_score`
- Daily stability:
  - `J(S_t, S_{t-1}) = |S_t ∩ S_{t-1}| / |S_t ∪ S_{t-1}|`
- Emitted metrics:
  - `jaccard_top_decile`
  - `jaccard_top_30`
- File reference:
  - `scripts/phase22_separability_harness.py` (`_jaccard_index`, `_build_daily_metrics`)

## 2) Manifold Separation (Silhouette in Path1 Geometry)
- Feature space:
  - post-MAD robust z-scored features
  - then sector-projection residualized geometry (`z_geom_resid`).
- Labels:
  - `label_i = argmax(posterior_cyclical_i, posterior_defensive_i, posterior_junk_i)`.
- Score:
  - silhouette score on `(z_geom_resid, label)` rows.
- One-class policy:
  - if only one effective class on a day, emit `silhouette_score = NaN` with class coverage counters.
- Runtime fallback:
  - when `sklearn.metrics` is unavailable, use deterministic manual Euclidean silhouette implementation.
- File reference:
  - `scripts/phase22_separability_harness.py` (`_build_geometry_residuals`, `_compute_silhouette_metrics`, `_manual_silhouette_score`)

## 3) Invariant Truth Checks (Archetype Recall)
- Archetype set:
  - `{MU, LRCX, AMAT, KLAC}`
- Daily rank:
  - `rank_i_t = 1-based rank of ticker i by odds_score on day t`
- Daily hits:
  - `hit_decile_i_t = 1{rank_i_t <= top_decile_n_t}`
  - `hit_top30_i_t = 1{rank_i_t <= top_30_n_t}`
- Aggregate rates:
  - mean of daily hit indicators across the evaluation window.
- File reference:
  - `scripts/phase22_separability_harness.py` (`_archetype_rank_metrics`, `_build_summary`)

---

# Phase 23 Formula Notes (FMP PIT Estimates Ingestion - Step 1)

Date: 2026-02-22

## 1) Internal Schema Contract
- Cleaned output schema:
  - `permno, ticker, published_at, horizon, metric, value`
- Metric names ingested from FMP:
  - `estimatedRevenueAvg`
  - `estimatedEpsAvg`
- Horizon:
  - normalized to `NTM`.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_build_processed_estimates`)

## 2) PIT Publication-Time Rule
- Publication timestamp:
  - `published_at = coalesce(date, publishedDate, published_at, acceptedDate, updatedAt, fetched_at_utc)`
- PIT firewall for NTM aggregation:
  - include forecast periods only when `period_end > published_at`.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_derive_period_fields`, `_normalize_ntm_for_metric`)

## 3) NTM Normalization Rule (Quarterly/Annual)
- For each `(permno, ticker, published_at, metric)` group:
  - if at least 4 future quarterly rows exist:
    - `NTM = sum(first 4 future quarters by period_end ascending)`
  - else if 2-3 future quarterly rows exist:
    - `NTM = sum(quarters) * (4 / n_quarters)` (annualized partial forward set)
  - else if annual (`FY`) row exists:
    - `NTM = FY value`
  - else if exactly 1 future quarter exists:
    - `NTM = quarter_value * 4`
  - else:
    - fallback to first finite metric value.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_normalize_ntm_for_metric`)

## 4) Identifier Integrity Rule
- Mapping source:
  - `data/static/sector_map.parquet`
- Join key:
  - uppercased cleaned ticker (`ticker_u`)
- Integrity behavior:
  - drop unmapped ticker rows from processed output.
  - log unmapped ticker sample for audit.
  - if processed output is empty after mapping/normalization, abort write (preserve existing outputs).
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_load_ticker_permno_crosswalk`, `_build_processed_estimates`, `main`)

## 5) Rate-Aware Cache-First Ingestion Rules
- Per-ticker cache path:
  - `cache_path(ticker) = data/raw/fmp_cache/{ticker}.json`
- Cache priority:
  - if cache exists and `--refresh-cache` is not set:
    - use cache rowset, skip network request.
- 429 handling:
  - exponential backoff:
    - `wait_k = min(backoff_initial_sec * 2^k, 300)` for retry `k`.
  - after retry budget is exhausted:
    - set rate-limited mode,
    - stop new network requests,
    - continue cache-only for remaining scoped tickers,
    - exit cleanly (`code 0`) if no fresh rows can be fetched.
- Scoped universe:
  - target list resolved from `--tickers` and/or `--tickers-file`,
  - capped by `--max-tickers` (default `500`),
  - pre-filtered to tickers with known `permno` in crosswalk before API calls.
- Merge policy:
  - if `--merge-existing` and prior `data/processed/estimates.parquet` exists:
    - `final = dedup(existing ∪ new)` on key
      - `(permno, ticker, published_at, horizon, metric)`
    - source rank enforces **new rows win** on key collisions.
- File reference:
  - `scripts/ingest_fmp_estimates.py` (`_resolve_target_tickers`, `_load_cached_rows`, `_fetch_with_backoff`, `_merge_existing_processed`, `main`)

---

# Phase 23 Formula Notes (3-Pillar SDM Ingest + Assembler Round 3)

Date: 2026-02-22

## 1) merge_asof Sorting Contract (Pillar 1 + 2)
- Required global order before `merge_asof(..., by='gvkey')`:
  - `left sort = sort_values(['published_at_dt', 'gvkey'])`
  - `right sort = sort_values(['pit_date', 'gvkey'])`
- Hard assertions:
  - `published_at_dt` monotonic increasing globally.
  - `pit_date` monotonic increasing globally.
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_assert_merge_asof_sorted`, `_join_totalq`)

## 2) Peters & Taylor PIT Join + Dynamic Schema
- Filing lag:
  - `pit_date = datadate + 90 days`
- Dynamic probe:
  - `available_cols = information_schema.columns(totalq.total_q)`
  - `selected_cols = required + stable + optional_intersection`
- Required:
  - `gvkey`, `datadate`
- Stable:
  - `k_int`, `k_int_know`, `k_int_org`, `q_tot`
- Optional enrichment:
  - `k_phy`, `invest_int`, `invest_phy`, `ik_tot`
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_probe_totalq_columns`, `_select_totalq_columns`, `_query_totalq`)

## 3) Pillar 2 Derived Features
- Intangible intensity:
  - `intang_intensity = k_int / (k_int + ppentq)` when denominator `> 0`
- Investment discipline:
  - preferred: `invest_disc = ik_tot - lag4(ik_tot)` when `ik_tot` exists
  - fallback: `invest_disc = (k_int - lag4(k_int)) / lag4(k_int)` when `lag4(k_int) > 0`
- Regime flag:
  - `q_regime = 1(q_tot > 1.0)` (NaN-preserving when `q_tot` unavailable)
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_join_totalq`)

## 4) Allow + Audit Identifier Policy
- Mapping:
  - `permno = map(ticker -> permno from sector_map.parquet)`
- Policy:
  - never drop unmapped rows.
  - emit audit CSV for unmapped rows:
    - `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`
- File reference:
  - `scripts/ingest_compustat_sdm.py` (`_crosswalk_permno`, `_atomic_write_csv`)

## 5) Assembler PIT Join Rules
- Inputs:
  - `fundamentals_sdm.parquet`
  - `macro_rates.parquet`
  - `ff_factors.parquet`
- Key normalization:
  - `published_at_dt = to_datetime(published_at, utc=True).tz_convert(None)`
  - `macro_at = to_datetime(date, utc=True).tz_convert(None)`
  - `ff_at = to_datetime(date, utc=True).tz_convert(None)`
- Asof joins:
  - `fundamentals ⟵ macro` by backward join on `published_at_dt` to `macro_at`
  - `fundamentals ⟵ ff` by backward join on `published_at_dt` to `ff_at`
  - strict staleness cap: `tolerance = Timedelta('14d')`
- Tolerance-null audit:
  - `baseline_match = merge_asof(..., tolerance=None)`
  - `strict_match = merge_asof(..., tolerance='14d')`
  - `nulled_by_tolerance = count(baseline_match exists AND strict_match is null)`
  - emit warning counts for macro and factor joins.
- Sector attach:
  - `permno` map first, then ticker fallback.
- File reference:
  - `scripts/assemble_sdm_features.py` (`assemble_features`, `_count_rows_nulled_by_tolerance`, `_attach_sector_context`)

---

# Phase 23 Formula Notes (Action 2: BGM Manifold Swap)

Date: 2026-02-22

## 1) Daily SDM Broadcast (Method A)
- Entity-wise daily forward fill from quarterly release timeline:
  - `date = normalize(published_at)`
  - For each `gvkey`: reindex to daily calendar and `ffill` latest released snapshot.
- Calendar:
  - `calendar = date_range(min(fundamentals, macro, ff), max(fundamentals, macro, ff), 'D')`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_build_daily_calendar`, `_expand_fundamentals_daily`, `assemble_features`)

## 2) Industry Median Precompute (Method B)
- Daily industry medians:
  - `ind_rev_accel = median(rev_accel | date, industry)`
  - `ind_inv_vel_traj = median(inv_vel_traj | date, industry)`
  - `ind_gm_traj = median(gm_traj | date, industry)`
  - `ind_op_lev = median(op_lev | date, industry)`
  - `ind_intang_intensity = median(intang_intensity | date, industry)`
  - `ind_q_tot = median(q_tot | date, industry)`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_add_industry_medians`)

## 3) Macro-Cycle Interaction (Method B)
- Cycle setup interaction:
  - `CycleSetup = yield_slope_10y2y * rmw * cma`
  - alias: `cycle_setup = CycleSetup`
- File reference:
  - `scripts/assemble_sdm_features.py` (`_add_cycle_setup`)

## 4) Dual-Read Migration Adapter
- Data loader merge contract:
  - `features_window = left_join(features.parquet, features_sdm.parquet, on=[date, permno])`
  - Date normalization before merge:
    - `date = to_datetime(date, utc=True).tz_convert(None)`
  - Overlap policy:
    - for duplicate column name `x`, use `combine_first(x_left, x_sdm)`.
- File reference:
  - `scripts/phase20_full_backtest.py` (`_read_feature_window`, `_load_features_window`)

## 5) BGM Geometry Isolation Contract (Superseded by Phase 20 Lock on 2026-02-22)
- Current locked Phase 20 geometry set must include only:
  - `rev_accel, inv_vel_traj, op_lev, q_tot, CycleSetup`
- Historical note:
  - prior Phase 23 experimentation used a broader 10-feature geometry set;
    this is retained as historical context only and is not the current lock state.
- Explicit risk exclusion asserts:
  - reject exact risk columns:
    - `realized_vol_lag, yz_vol_20d, atr_14d, sigma_continuous, asset_beta_lag, portfolio_beta, rolling_beta_63d`
  - reject any geometry column containing token:
    - `beta` or `vol`
- File reference:
  - `strategies/ticker_pool.py` (`TickerPoolConfig`, `_assert_geometry_excludes_risk`, `rank_ticker_pool`)

## 6) Risk Routing Separation
- Risk features kept for sizing/governor only:
  - volatility path: `sigma_continuous`, `realized_vol_lag`, `atr_14d`, `yz_vol_20d`
  - beta path: `asset_beta_lag`, `portfolio_beta`, `beta_scale_pre`, `beta_scale_post`
- Geometry path uses lagged SDM/macro fields only.
- File reference:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 7) Hierarchical Imputation for SDM Geometry (Universe Preservation)
- Scope:
  - Applied in ticker-pool geometry build before robust MAD scaling.
- Level 1 (Industry Fill, PIT cross-section):
  - For each date and feature:
    - `x_i = median(feature | date, industry)` when firm value is NaN
  - Fallback grouping key:
    - `industry` else `sector` else `UNKNOWN`.
- Level 2 (Neutral Fill):
  - Remaining NaN -> `0.0` in robust-scaled geometry space.
  - Interpretation:
    - `0.0` is neutral market-average exposure on that feature.
- Telemetry:
  - `geometry_universe_before_imputation`
  - `geometry_universe_after_imputation`
  - `geometry_industry_impute_cells`
  - `geometry_zero_impute_cells`
- File reference:
  - `strategies/ticker_pool.py` (`_hierarchical_impute_geometry`, `_build_weighted_zmat_with_imputation`, `rank_ticker_pool`)
  - `scripts/phase22_separability_harness.py` (`_build_geometry_residuals`, `_build_daily_metrics`, `_build_summary`)

---

# Phase 20 Closure Formula Notes (Golden Master Lock)

Date: 2026-02-22

## 1) Cluster Ranker (Option A, Cyclical Trough)
- Formula:
  - `cluster_score = (CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`
- Interpretation:
  - reward cycle inflection + operating leverage + revenue acceleration + inventory clearing,
  - penalize high `q_tot` to avoid buying supply-heavy/capital-loose profiles.
- Source path:
  - `strategies/ticker_pool.py` (`_conviction_cluster_score`)

## 2) Hard Entry Gate (Trend-Confirmed)
- Formula:
  - `entry_gate = score_valid & (conviction_score >= 7.0) & pool_long_candidate & mom_ok & support_proximity`
- Interpretation:
  - no entry without both momentum confirmation and support confirmation.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 3) Hard Exit / Selection Rule
- Formula:
  - `selected = entry_gate & (rank <= n_target)`
- Interpretation:
  - positions must still pass hard gate and rank threshold each day (no winner-retention hysteresis in locked state).
- Source path:
  - `scripts/phase20_full_backtest.py` (`_build_phase20_plan`)

## 4) Concentrated Portfolio and Structural Cash
- Defaults:
  - `top_n_green = 8`
  - `top_n_amber = 4`
  - `cash_pct_GREEN = 0.20`
  - `gross_cap_GREEN = 0.80`
- Source path:
  - `scripts/phase20_full_backtest.py` (`parse_args`, `_build_phase20_plan`)

## 5) Fundamental Continuity Repair (PIT-safe Missing Data)
- Rule:
  - grouped ticker-level `ffill(limit=120)` for `q_tot`, `inv_vel_traj`, `op_lev`, `rev_accel`, `CycleSetup`.
  - remaining NaNs filled by same-date sector median, then same-date market median, then `0.0`.
- Source path:
  - `strategies/company_scorecard.py` (`build_phase20_conviction_frame`)

## 6) MU Reverse-Engineer Diagnostic (Boundary Evidence)
- October 2022 means from `data/processed/diagnostic_MU_reverse_engineer.csv`:
  - `q_tot = 3.2634692142857142`
  - `inv_vel_traj = 0.0`
  - `conviction_score = 3.510820467875683`
- Interpretation:
  - backward-looking fundamentals can lag market forward-pricing at cycle bottoms.

---

# Context Bootstrap Formula/Contract Notes

Date: 2026-02-23

## 1) Context Artifact Schema Contract (`current_context.json`)
- Required top-level fields:
  - `schema_version`
  - `generated_at_utc`
  - `source_files`
  - `active_phase`
  - `what_was_done`
  - `what_is_locked`
  - `what_is_next`
  - `first_command`
  - `next_todos`
- Field constraints:
  - `generated_at_utc`: ISO-8601 UTC timestamp.
  - `what_was_done`, `what_is_locked`, `what_is_next`, `next_todos`: non-empty string arrays.
  - `first_command`: non-empty string.
  - key order is fixed to `PACKET_KEYS` in `scripts/build_context_packet.py`.

## 2) Markdown Packet Section Contract (`current_context.md`)
- Required section order:
  - `## What Was Done`
  - `## What Is Locked`
  - `## What Is Next`
  - `## First Command`

## 3) Refresh/Validation Command Contract
- Build command:
  - `.venv\Scripts\python scripts/build_context_packet.py`
- Validation command:
  - `.venv\Scripts\python scripts/build_context_packet.py --validate`
- Phase-end freshness check formula:
  - `artifact_age_hours = (now_utc - generated_at_utc) / 3600`
  - pass condition: `artifact_age_hours <= 24`

## 4) Source Selection + Active Phase Rule
- Candidate order:
  - inspect phase handovers and phase briefs by descending phase number.
  - select first document that satisfies required sections.
- `active_phase` rule:
  - use phase number parsed from selected source document.
  - fallback to max phase brief number only if selected source has no parseable phase token.
- File reference:
  - `scripts/build_context_packet.py` (`_select_context_source`, `_active_phase`, `build_context_packet`)

## 5) Validate Mode Integrity Rule
- Validation command:
  - `.venv\Scripts\python scripts/build_context_packet.py --validate`
- Pass conditions:
  - JSON schema matches `PACKET_KEYS`.
  - `generated_at_utc` parseable + age <= 24h.
  - existing JSON equals expected packet except timestamp field.
  - markdown headers match required contract.
  - markdown body equals canonical render from JSON payload (parity check).
- File reference:
  - `scripts/build_context_packet.py` (`validate_existing_outputs`, `render_context_markdown`)

---

# Philosophy Sync + Gemini Handover Contracts

Date: 2026-03-01

## 1) Local-First Philosophy Sync Contract
- Command:
  - `.venv\Scripts\python scripts/sync_philosophy_feedback.py --scan-root E:\Code --main-repo E:\Code\SOP\quant_current_scope`
- Required sequence:
  - discover worker repos from `AGENTS.md` under `--scan-root` (excluding ignored paths such as `node_modules`, `.git`, `.venv`).
  - update worker-local loop file first (`docs/lessonss.md` preferred; fallback to `docs/lessons.md`/`LESSONS_LEARNED.md`).
  - migrate summary to main SOP repo only when all worker updates pass (`strict` fail-closed gate).
- Source of philosophy payload:
  - extract sections `6/7/8` from `top_level_PM.md`.
- Source path:
  - `scripts/sync_philosophy_feedback.py` (`discover_worker_repos`, `_extract_sections_6_8`, `run_sync`)

## 2) Main Migration Outputs
- JSON log:
  - `docs/context/philosophy_migration_log.json`
- Markdown report:
  - `docs/context/philosophy_migration_report.md`
- `overall_status` rule:
  - `PASS` only when strict gate sees no worker `BLOCK`.
  - `BLOCK` when any worker local update fails under strict mode.

## 3) Gemini Handover Auto-Generation Contract
- Trigger command:
  - `.venv\Scripts\python scripts/build_context_packet.py`
- Auto-generated output path:
  - `docs/handover/gemini/phase<active_phase>_gemini_handover.md`
- Mandatory content:
  - `top_level_PM.md` full text,
  - `docs/context/current_context.json`,
  - `docs/context/current_context.md`,
  - all files listed in `source_files` from the context packet,
  - `docs/context/philosophy_migration_log.json` (or explicit `NOT_FOUND` marker if absent).
- Source path:
  - `scripts/build_context_packet.py` (`render_gemini_handover`, `write_context_outputs`, `validate_existing_outputs`)
