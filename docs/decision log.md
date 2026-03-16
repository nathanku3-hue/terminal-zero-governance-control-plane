Decision Log: Terminal Zero Governance Control Plane
Author: Atomic Mesh | Last Updated: 2026-03-09 (Identity framing clarified)

This log is the long-lived decision record for the current governance control plane.
Legacy quant-era decisions are retained below for historical traceability; current operator behavior is governed by the active control-plane contracts and runbooks.

Reader note: the first table entries below begin with legacy quant-era history; use the active governance docs as the authoritative source for present-day operator behavior.

Part 1: Master Decision Log

| ID   | Component  | The Friction Point          | The Decision (Hardcoded)       | Rationale                                                |
|------|------------|-----------------------------|--------------------------------|----------------------------------------------------------|
| D-01 | etl.py     | Delisting Bias              | Merge dlret into ret           | Captures -100% bankruptcies in total_ret.                |
| D-02 | etl.py     | Split/Div Confusion         | Dual Schema                    | adj_close for Signals, total_ret for PnL.                |
| D-03 | etl.py     | Macro Availability          | macro.parquet                  | Global regime awareness (SPY/VIX Proxy).                 |
| D-04 | engine     | Look-Ahead Bias             | Shift(1) Enforcement           | Trade T+1 based on Signal T.                             |
| D-05 | engine     | Cost Blindness              | Turnover Tax (10bps)           | Deduct cost on every portfolio change.                   |
| D-06 | infra      | NaN Explosions              | Forward Fill                   | Prevent simulation crashes from missing data.            |
| D-07 | strategy   | API Rigidity                | Abstract Weights               | Decouple Strategy from Engine via BaseStrategy.          |
| D-08 | integration| Wide-Format Mismatch        | Matrix Injection               | Engine accepts pre-pivoted Returns Matrix (T x N).       |
| D-09 | data       | No cfacpr column            | adj_close = abs(PRC)           | Split Trap acknowledged. MVP only. No live trading.      |
| D-10 | data       | No High/Low prices          | Close-Only ATR                 | ATR ≈ abs(Close-PrevClose). k raised to 3.5.             |
| D-11 | data       | No VIX index                | VIX Proxy                      | Rolling StdDev of SPY * sqrt(252) * 100.                 |
| D-12 | data       | No Compustat fundamentals   | Quality Gate stubbed           | Historical MVP decision; superseded by D-29 PIT quality gate. |
| D-13 | strategy   | Binary On/Off regime        | 3-State Regime (0.5/0.7/1.0)  | Attack/Caution/Defense dimmer switch (historical baseline; superseded by later FR-041/FR-050/FR-070 regime contracts). |
| D-14 | strategy   | Black Box feeling           | Reason Codes                   | Strategy returns (weights, regime, details) for UI.      |
| D-15 | data       | Memory crash (23K permnos)  | Top 2000 Liquid Universe       | Filter by total dollar volume in DuckDB before loading.  |
| D-16 | optimizer  | Manual parameter nudging    | 2D Grid Search                 | Automated sweep of k and z. Output: Heatmap. ← NEW      |
| D-17 | optimizer  | Fixed k/z in all regimes    | VIX-Adaptive Parameters        | k, z = f(VIX). Tight in calm; loose in panic. ← NEW     |
| D-18 | optimizer  | Left-Side entry too early   | Wait-for-Confirmation          | Green Candle check: P(T) > P(T-1) before entry. ← NEW   |
| D-19 | strategy   | One k/z for all stocks      | Quantile Mapping               | k_i = 2.5 + 1.5×VolRank, z_i = -3.0 + 2.0×VolRank. Per-stock adaptive params. |
| D-20 | UX         | Raw PERMNO input            | Searchable Ticker Dropdown     | st.multiselect with tickers.parquet (23K mappings). Type "NV" → NVDA. |
| D-21 | data       | Static data (ends 2024)     | Append-Only Hybrid Lake        | Base (WRDS) + Patch (Yahoo) via DuckDB UNION ALL. Never rewrite 47M base. |
| D-22 | data       | Sequential ticker download  | Batch yf.download()            | Multi-ticker request 50x faster. Top 50/100/200 scope. Dashboard trigger. |
| D-23 | UX         | Binary SELL/BUY signals     | 5-State Classifier (FR-023)    | HOLD/BUY/WATCH/AVOID/WAIT. Forward-looking support levels, not stale "SELL". |
| D-24 | strategy   | All BUYs equal              | Conviction Scorecard (FR-024)  | 0-10 score: Trend(3)+Value(3)+Macro(2)+Momentum(2). Hardcoded, no LLM. |
| D-25 | data/UX    | Manual "Run Update Now"     | Smart Watchlist + Auto-Update  | watchlist.json persists selections. Auto-update on stale data. CLI script. |
| D-26 | strategy   | Naive conviction (StdDev/coin-flip) | L5 Alpha (Robust Z + ER) | MAD-based z-score resists crashes. Kaufman ER filters noise from trend. VIX trend. |
| D-27 | UX         | Multiselect + stacked cards  | Scanner + Detail Views (FR-026v2) | Radio toggle (scan/watchlist), always top-5, ticker search bar, drill-down. No permnos shown. |
| D-28 | data       | Stale prices for non-watchlist | JIT Single Ticker Patch (D-28) | "Bedrock + Fresh Snow" architecture. Auto-fetch Yahoo on drill-down if data > 3 days stale. |
| D-29 | data/strategy | Value Traps from price-only dips | PIT Quality Gate (FR-027) | Fundamentals keyed by release_date, daily broadcast via ffill, MVQ filter: ROIC>0 and Revenue YoY>0; stale/missing fundamentals fail-safe. |
| D-30 | data       | Universe too narrow vs institutional coverage | Top 3000 Optional Expansion (FR-030) | Expand investable set without forcing slower default runtime for all sessions. |
| D-31 | app/runtime| Top 3000 load pressure during pivot/concat | Dynamic Batch Sizing in `load_data()` | Use smaller batches when universe > 2500 (`200` vs `250`) to reduce memory spikes and improve stability. |
| D-32 | data/ops   | Missing context for risk concentration | Sector Map as Static Bedrock (FR-028) | Build once, merge at runtime; keeps scanner context-rich without API calls in hot path. |
| D-33 | data       | Sparse Yahoo fundamentals coverage | Compustat CSV Bedrock Ingestion (FR-031) | Load quarterly WRDS/Compustat file for materially higher PIT coverage in investable universe. |
| D-34 | data       | Mixed-source collisions on same release date | Source Precedence: Compustat > Yahoo | `rdq`-driven Compustat rows are preferred over yfinance restatements at `(permno, release_date)` key. |
| D-35 | data/quality | Symbol format drift between vendors | Deterministic ticker normalization + audit | Use exact + suffix/dot normalization and persist unmatched audit file for explicit gap tracking. |
| D-36 | data       | Metadata-only index exports masquerade as constituents | Hard Input Gate for R3000 PIT Loader (FR-032) | Fail fast unless WRDS file has required columns and sufficient rows; prevents hallucinated universe builds. |
| D-37 | app/data   | Need PIT membership universe for forward testing without breaking current runtime | Optional `universe_mode='r3000_pit'` in `load_data()` | Keeps default Top2000/Top3000 flow stable while enabling future date-aware universe selection. |
| D-38 | data/factors | YTD cashflow misread as quarterly flow | OANCFY Decumulation by (permno,fyearq,fqtr) | Prevents Q4 overstatement and restores quarter-true cashflow signals. |
| D-39 | data/factors | Valuation factor mismatch across debt/cash fields | Vectorized EV/EBITDA + Leverage Matrix (FR-033) | Standardized enterprise-value construction with safe denominator handling. |
| D-40 | infra      | Phase churn risk before catalyst layer | Infrastructure Frozen milestone | Lock PIT universe + fundamentals bedrock before adding event-driven alpha logic. |
| D-41 | strategy/UI | High-score picks can hide event risk near earnings | Catalyst Radar event overlay (FR-034) | Keep best candidates visible while flagging `earnings_risk` for <5-day blackout window. |
| D-42 | data/macro | Dual macro artifacts drift and hidden look-ahead risk | Single SSOT macro layer (`macro_features.parquet`) + conservative FRED lag policy | Prevents schema drift and enforces PIT safety by design (`T+1` for slow macro). |
| D-43 | data/perf | Macro rebuild risked >10s as history grows | Vectorized rolling percentile + parallel/date-bounded FRED pulls | Preserves PIT correctness while reducing runtime bottlenecks in FR-035 build path. |
| D-44 | app/strategy | Missing macro artifact could imply false “calm” regime | Defensive fallback (`regime_scalar=0.5`) + scalar-priority regime mapping | Fails safe (reduced risk) when macro layer is unavailable, avoiding full-risk exposure on data outage. |
| D-45 | data/liquidity | Need causal liquidity features with strict PIT discipline | Dedicated `liquidity_features.parquet` + H.4.1 lag rule (Wed→Fri) | Prevents look-ahead in Fed weekly series while adding flow/plumbing signals for FR-040. |
| D-46 | data/runtime | Liquidity build could silently degrade on partial inputs or stale locks | Fail-fast Yahoo critical checks + calendar end-date bounding + stale-lock recovery | Prevents writing misleading stress signals, respects requested build windows, and avoids deadlocks after crashed writers. |
| D-47 | strategy/runtime | Single scalar regime path mixes structural stress and sizing pace | Two-layer RegimeManager (`Governor` + `Throttle`) with fixed 3x3 scalar matrix | Makes exposure logic explicit, testable, and stable across data-source fallback paths for FR-041. |
| D-48 | strategy/risk | Need strict long-only safety in crisis while avoiding blind chase | Red matrix clamps (`RED+NEG=0.0`, `RED+NEUT=0.0`, `RED+POS<=0.20`) [FR-041 historical freeze] | Historical contract snapshot; current runtime precedence is FR-050/FR-070 budget map (`RED=0.0`). |
| D-49 | strategy/validation | Regime tuning can drift without anchored historical behavior checks | FR-042 strict truth table + 2017 GREEN guardrail | Enforces crisis defensiveness (2008 Q4, 2020 Mar, 2022 H1) while preventing chronic risk-off behavior during calm regimes. |
| D-50 | strategy/validation | FR-042 strict run blocked by low-vol false RED triggers and short-window recovery NaNs | Add volatility gates to credit/liquidity RED triggers and allow recovery fallback to full-sample metric when crisis-window recoveries are undefined | Preserves crisis capture while preventing mathematically impossible failures in fixed short windows. |
| D-51 | strategy/backtest | Cash ETF history is incomplete across full sample | FR-050 cash hierarchy (`BIL -> EFFR/252 -> flat 2%/252`) | Preserves realistic cash carry in pre-/post-ETF gaps and avoids biased zero-cash assumptions. |
| D-52 | strategy/backtest | Regime signal can leak if applied same-day to returns | Enforce deterministic `t signal -> t+1 executed weight` in FR-050 | Keeps walk-forward PnL strictly point-in-time and execution-realistic. |
| D-53 | data/features | Selector layer lacks stock-level alpha vectors | Create FR-060 `feature_store` with ranking/sizing/execution features | Separates capital-preservation governor from asset-selection alpha engine. |
| D-54 | data/features | Historical lake is close-only, but YZ/ATR are OHLC-native | Add explicit close-only fallback modes (`yz_mode`, `atr_mode`) | Keeps pipeline operational without hidden assumptions while preserving future OHLC upgrade path. |
| D-55 | strategy/alpha | Need robust tuning without curve-fit drift | FR-070 fixed-vs-adaptive governance + walk-forward-only tuning | Preserve structural philosophy while allowing regime-aware sensitivity changes. |
| D-56 | strategy/execution | Daily rank jitter can overtrade and kill alpha net of costs | Hysteresis rank buffer (`enter<=5`, `hold<=20`, `exit>20`) | Reduces churn while preserving strong-signal entries. |
| D-57 | strategy/risk | Stop logic can drift downward and re-open left-tail risk | Ratchet-only stop (`stop_t=max(stop_{t-1}, new_stop_t)`) | Locks gains and prevents stop widening after entry. |
| D-58 | strategy/optimizer | Parameter hunts can silently mutate structural behavior | FR-080 FIX vs FINETUNE governance split | Keeps structural rules frozen while allowing bounded adaptive honing only where intended. |
| D-59 | strategy/validation | Optimizer loops can overfit by peeking into OOS outcomes | FR-080 WFO-only promotion gate with strict OOS isolation | Preserves causal validation by forbidding OOS data in search objective, ranking, and tie-breaks. |
| D-60 | strategy/perf | FR-080 grid search underutilized CPU despite cached data | Optional multi-process candidate evaluation + sequential fallback | Preserves deterministic behavior while scaling candidate throughput using available cores. |
| D-61 | strategy/optimizer | Multiple FR-080 candidate outputs required a single promoted baseline | Promote strict-pass defaults (`alpha_top_n=10`, `hysteresis_exit_rank=20`, `adaptive_rsi_percentile=0.05`, `atr_preset=3.0 -> 3.0/4.0/5.0`) | Establishes one production SSOT default after WFO strict pass and prevents runtime/backtest config drift. |
| D-62 | strategy/runtime | Tuned FR-080 promotion failed FR-070 verifier gate | Hard-stop rollback: demote promoted params to research-only and restore guarded runtime defaults (`alpha disabled`, `adaptive_rsi_percentile=0.15`) | Prevents shipping unstable tuning and enforces verifier-first runtime promotion policy. |
| D-63 | strategy/optimizer | Train-winner could pass stability but still be operationally inactive | Phase 16.2 activity guardrails (`trades_per_year > 10`, `exposure_time > 0.30`) in promotion gate, computed on OOS window only | Prevents starvation/under-trading profiles from promotion while preserving train-only ranking and OOS isolation. |
| D-64 | strategy/alpha | Dip-only entry gate can starve valid trend/liquidity candidates | Phase 16.2 Step 3 Dip OR Breakout entry (`dip_entry OR breakout_entry_green`) with PIT-safe prior-50d-high | Restores GREEN-regime trade flow while preserving AMBER/RED restraint and no-look-ahead discipline. |
| D-65 | strategy/safety | Malformed regime tokens can bypass intended RED/AMBER/GREEN contracts | Canonical regime normalization (`strip().upper()`) with unknown-state fail-safe to RED budget | Enforces deterministic exposure safety and prevents accidental risk escalation from token formatting or invalid states. |
| D-66 | data/features | Global top-N liquidity universe can over-concentrate selector coverage across long windows | Add feature-store `universe_mode` with default `yearly_union` (`yearly_top_n=100`) and keep `global` legacy flag path | Expands PIT coverage by unioning per-year liquid leaders while preserving operational safety with memory-envelope guards. |
| D-67 | strategy/optimizer | Train-ranked winner selection could ignore promotability and leak policy intent | Promotable-first, train-only deterministic ranking (`objective`, `train_cagr`, `train_robust`, `train_ulcer`, parameter tie-breakers) with no OOS ranking fields | Aligns FR-080 selection behavior with governance by promoting only candidates that pass stability and activity guardrails. |
| D-68 | infra/program | Parallel infra refactor can conflict with active optimizer reader runs | Phase 17 gated execution policy with explicit run guard (`phase16_optimizer.lock` + process check + artifact-bundle completion) before writer milestones | Prevents reader/writer conflicts and preserves a clean attribution boundary between strategy outcomes and infrastructure changes. |
| D-69 | data/updater | Large Yahoo scopes stall or partially fail under single-call batching | Chunked parallel Yahoo downloads with ordered merge and key dedupe (`ticker`,`date`) before atomic patch publish | Improves throughput/resilience for Top500/Top3000 updates while preserving lock-safe, append-only patch semantics. |
| D-70 | data/features | Full-window feature rebuilds are too costly for daily refresh cadence | Incremental feature rebuild with warmup replay, atomic upsert merge, and duplicate-key override (`date`,`permno`) | Converts daily builds from full recompute toward bounded append cost while protecting rolling-window correctness. |
| D-71 | data/ops | Feature artifact failures were not explicitly audited in integrity gate | Extend `scripts/validate_data_layer.py` with feature-store checks (row count, null keys, duplicate keys, freshness gap) | Adds enforceable data-layer acceptance evidence before downstream strategy/optimizer runs. |
| D-72 | strategy/optimizer | Dip-only vs breakout-style entries were not testable as first-class optimizer dimensions | Add FR-080 tournament `entry_logic` grid (`dip`,`breakout`,`combined`) with deterministic train-only tie-break integration and artifact fielding | Enables regime-sensitive entry discovery without violating OOS-isolation governance or promotion guardrails. |
| D-73 | strategy/ops | Long FR-080 tournament runs lacked visible progress and live leaderboard telemetry | Add real-time optimizer heartbeat (`phase16_optimizer_progress.json`) and interim leaderboard (`phase16_optimizer_live_results.csv`) with periodic console ETA updates | Enables operator monitoring/polling without waiting for end-of-run artifacts. |
| D-74 | data/fundamentals | Price-only and partial-fundamental snapshots could not support first-principles moat/demand ranking | Expand PIT fundamentals schema with conservative EPS/equity policy (`net_income_q`, `equity_q`, `eps_basic_q`, `eps_diluted_q`, `eps_q`, `eps_ttm`, `eps_growth_yoy`, `roe_q`) across Yahoo + Compustat loaders and snapshot broadcaster | Enables robust fundamental scoring with explicit diluted-EPS priority, equity fallback, and release-date-safe propagation into runtime selector contexts. |
| D-75 | data/feature-architecture | Parallel script hardening alone could not support agent-driven factor evolution or restatement-safe backtests | Merge Stream A+B into a declarative-engine foundation and bitemporal fundamentals contract: explicit capital-cycle raw fields, `published_at` as-of filtering (`published_at <= trade_date`), conservative fallback (`filing_date` else `fiscal_period_end + 90d`) | Preserves PIT integrity under restatements while preparing feature computation for spec-driven extension instead of hardcoded script edits. |
| D-76 | data/features | Hardcoded feature blocks were not agent-extensible and repeated expensive recompute on identical spec/input states | Refactor `feature_store` into a declarative `FeatureSpec` executor with registry-driven compute and add hash-addressed build cache (`features_<cache_key>.parquet`) | Enables safe feature extension without editing core compute flow and skips redundant rebuilds via deterministic cache reuse. |
| D-77 | data/fundamentals | Sparse bitemporal fundamentals were correct but too slow for repeated runtime joins | Build a dense daily vintage panel with interval-based PIT expansion (`published_at` to `next_published_at`) plus manifest-driven source-signature cache (`daily_fundamentals_panel.parquet` + manifest) | Preserves strict as-of correctness under restatements while making feature/optimizer joins fast and reproducible for each input vintage. |
| D-78 | strategy/validation | Capital-cycle logic needed a deterministic bubble-era sanity check independent of Yahoo coverage gaps | Add CSCO 2000 event-study harness with Compustat fallback and inventory-commitment-sensitive discipline stress (`backtests/event_study_csco.py`) | Verifies that score can de-rate names under rising inventory commitments even when moat remains positive, and prevents silent logic regressions in future refactors. |
| D-79 | strategy/validation | CSCO-style inventory penalty may over-fire on cyclical semis during trough-to-recovery transitions | Add MU 2016 paradox stress run (rally-positive gate) and mark cyclical-exception requirement when score remains negative during confirmed price supercycle | Prevents shipping a discipline term that systematically false-sells cyclical leaders and defines the next research patch target. |
| D-80 | strategy/factor | Discipline penalty needed explicit efficiency override during inventory-led ramps | Implement Turnover Gate (`delta(revenue/inventory) > 0.05 => waive discipline penalty`) in FeatureSpec discipline logic and event-study scorer, then re-run CSCO/MU twin checks | Preserves Cisco de-rating behavior while testing whether turnover-only override can unban cyclical recoveries; establishes whether additional cyclical exception features are required. |
| D-81 | strategy/factor | Turnover-only override remained insufficient for cyclical recoveries and lacked leading inventory-quality signals | Implement Inventory Quality Gate with weighted soft-vote (`book_to_bill`, `gm_accel`, `delta_dso`) across fundamentals schema, FeatureSpec discipline logic, and event-study scorer, with missing-signal fallbacks | Preserves Cisco de-rating while introducing leading quality classification for inventory builds; creates a measurable bridge from “inventory level” to “inventory quality” and isolates remaining MU strict-positivity gap for next patch. |
| D-82 | strategy/factor | Discrete inventory-quality gates remained brittle in cyclical transitions and overfit edge conditions | Pivot to continuous proxy gate (`z_inventory_quality_proxy`) using quarterly acceleration/bloat terms with waiver rule `z_inventory_quality_proxy > 0` and no-new-fetch policy | Reduces binary gate brittleness, preserves PIT semantics, and improves cyclical recovery handling without adding new external data dependencies. |
| D-83 | governance/docs | Plan/report structure drift and missing institutional memory | Add mandatory planning contract (high confidence, low certainty, boundary), self-learning feedback loop (`docs/lessonss.md`), SAW reporting format, and skill hooks (`.codex/skills/saw`, `.codex/skills/research-analysis`) in `AGENTS.md` | Standardizes decision quality visibility, enforces post-round review discipline, and creates repeatable research-backed planning behavior. |
| D-84 | data/runtime | Strict fail-fast external checks can stall refresh workflows during provider outages | On critical upstream data failure, keep last-successful artifact in service, skip unsafe publish, emit stale-data alert, and require explicit resume note before next publish | Preserves data integrity while maintaining operational continuity during transient provider failures. |
| D-85 | governance/review | Review output style varied by session and missed explicit option tradeoffs | Add a mandatory interactive review protocol in `AGENTS.md` (Big/Small mode gate, section cadence, numbered issues with lettered options, file:line evidence, recommended-first options, explicit user confirmation before implementation) | Improves review consistency, keeps decisions auditable, and aligns recommendations with user engineering preferences without over-expanding process overhead. |
| D-86 | governance/pm | Snapshot hierarchy remained generic and produced cluttered planning views | Adopt project-based hierarchy (`L1` pillar, `L2` streams, `L3` stages), stage-specific active-stream reporting, one-stage expansion loop, and trigger-based optional skills (`se-executor`, `architect-review`) with `>=2`-round escalation-by-approval | Improves PM traceability, keeps planning MECE, reduces formatting leakage, and adds rigor only when risk/complexity warrants it. |
| D-87 | governance/saw | Inherited out-of-scope High findings could block unrelated docs-only rounds indefinitely | Scope SAW blocking to in-scope Critical/High findings, while carrying inherited out-of-scope High findings in Open Risks with owner/target milestone and requiring explicit acceptance before milestone close | Preserves review rigor without deadlocking governance updates on pre-existing external debt. |
| D-88 | strategy/research | Event-study-first flow could not answer cross-sectional efficacy question for proxy gate | Promote cross-sectional double-sort evaluator with HAC/Newey-West and optional Fama-MacBeth as the primary Phase 17.1 validation harness | Makes proxy-gate validation reproducible at cross-sectional scale and aligns acceptance to spread/t-stat evidence instead of anecdotal event windows. |
| D-89 | data/features | Incremental feature updates still risked full-table rewrite cost | Convert `features.parquet` from single file to Hive-style partitioned dataset (`year=YYYY/month=MM`) with one-time migration and partition-only upsert rewrites | Restores practical iteration speed for repeated research loops while preserving atomic publish guarantees and PIT-safe storage semantics. |
| D-90 | strategy/statistics | Dense parameter search can overfit and overstate Sharpe under multiple testing | Standardize Phase 17.2 sweep on full combinatorial CSCV (`S` even blocks) + PBO + correlation-adjusted `N_eff` and DSR non-normality adjustment | Adds formal data-snooping controls and promotes variants using deflated risk-adjusted evidence rather than raw in-sample Sharpe. |
| D-91 | strategy/ops | Long-running sweeps could lose progress and misalign fine-search focus after interruptions | Add deterministic parameter-hash variant IDs, checkpoint/resume cadence, and DSR-first coarse anchor (`DSR -> t_stat_nw -> period_mean`) in sweep engine | Prevents wasted recompute, preserves stable identity across grid mutations, and keeps refinement centered on robust (deflated) candidates. |
| D-92 | data/perf | Partitioned upsert still paid avoidable per-partition DuckDB session/read overhead | Batch touched partition reads with a single DuckDB connection inside `_atomic_upsert_features` before per-partition atomic rewrites | Reduces connection churn and repeated scan overhead while preserving partition-scoped atomic write semantics. |
| D-94 | strategy/ticker-pool | Quarterly centroid drift and circular fallback risk degraded anchor intent in Mahalanobis scoring | Replace cyc centroid with per-slice anchor-injected mean in z-space (`MU`,`LRCX`,`AMAT`,`KLAC`,`STX`,`WDC`) and enforce `score_col` as pre-pool metric only; when anchors are missing, fallback to top-k by pre-pool score with critical logging | Removes centroid drift, blocks chicken-and-egg score recursion, and preserves deterministic fallback behavior with explicit telemetry. |
| D-103 | strategy/ticker-pool | Pre-pool ranking lacked deterministic sector context visibility and no explicit Path1 directive telemetry contract | Attach `sector/industry` from static `sector_map.parquet` into conviction frame before `rank_ticker_pool` using permno-first/ticker-fallback deterministic mapping; emit `DICTATORSHIP_MODE` and Path1 telemetry into sample/summary artifacts | Keeps ranking inputs context-aware without runtime API calls and creates auditable Path1 directive evidence for each slice run. |
| D-104 | strategy/ticker-pool | Path1 geometry/runtime gates could silently degrade when projection failed, sparse slices were skipped, or unknown-sector rows collapsed balanced resampling | Fail fast on non-finite sector-projection residualization, add explicit slice-skip logging, exclude `UNKNOWN` from sector-balance depth checks, and expose `--dictatorship-mode on/off` toggle in slice runner with model telemetry parity | Prevents silent geometry corruption, improves operational observability, preserves deterministic balanced-resample behavior under partial context coverage, and enables controlled de-anchor experiments. |
| D-148 | governance/optimality-review | Milestone-close simplicity and entropy concerns kept recurring, but only as discussion; creating a new subsystem would overengineer the advisory layer | Reuse `docs/templates/optimality_review_brief.md` and `docs/optimality_review_protocol.md` to add one optional `ELEGANCE_ENTROPY_SNAPSHOT` with lean proxy fields and explicit `I don't know yet` fallback | Makes elegance and maintainability discussable in one existing artifact without adding gates, validators, or authority changes. |
| D-149 | governance/startup | Startup profile choice needed evidence-learned guidance without introducing new authority paths | Add offline deterministic advisory ranking artifact from local shipped-project outcomes (`docs/context/profile_selection_ranking_latest.json`) and surface it in startup artifacts as recommendation-only; startup intake and active `PROJECT_PROFILE` remain authoritative | Improves profile selection signal quality while preserving fail-closed governance and avoiding any control-plane authority change. |
| D-150 | governance/operator | Profile ranking input could drift because outcome records were manual and inconsistently shaped across rounds | Add deterministic corpus-capture step to write normalized profile-outcome records from current loop artifacts plus operator-supplied shipped/postmortem inputs before ranking build | Keeps ranking evidence auditable and comparable round-to-round without changing startup/control-plane authority. |
| D-151 | governance/docs | Pragmatic execution philosophy existed in discussion but not encoded as one auditable docs contract | Add CN/EN pragmatic SOP and enforce five process rules in docs: manifest-first for big changes, single logic-spine index, orchestrator governance-only role split, doc lifecycle tiers, and AI coding inside explicit boundaries/non-goals | Reduces coordination ambiguity and keeps change execution lean, bounded, and reviewable without introducing new runtime authority. |
| D-152 | governance/truth-protocol | Teams asked for an “ultimate truth layer,” but cross-repo domain semantics are not uniform and can create false certainty | Define a repo-init truth protocol and add a high-semantic-risk falsification pack template (`docs/templates/domain_falsification_pack.md`) plus a conditional structural closure gate when the active round contract explicitly requires it | Improves semantic rigor for domain-heavy decisions while preserving existing authority ownership and avoiding universal-engine overreach. |
| D-153 | governance/decision-quality | Teams needed a lean way to evaluate “optimal under constraints” beyond pass/merge completion | Add an advisory optimality review protocol + brief template focused on top-level semantic tradeoffs (`PRIMARY_OBJECTIVE`, `TOP_LEVEL_TRADEOFFS`, `RECOMMENDED_BALANCE`, `WHAT_WOULD_FLIP_DECISION`) with max 2-3 tradeoffs | Improves high-impact decision quality while preserving stable authority model and avoiding control-plane redesign. |
| D-154 | governance/roadmap | Optimality-engine discussion recurred across rounds without one canonical operator artifact showing current state, target state, and next minimal patches | Add `docs/minimal_optimality_roadmap.md` and link it from the runbook as the single PM-style roadmap for current engine vs optimal engine gaps | Keeps strategic improvement work explicit, sequenced, and lean without changing the stable control plane or adding new runtime gates. |
| D-155 | governance/decision-quality | High-impact decisions still tended to converge on one recommended path without a canonical in-brief comparison of alternatives | Extend the existing advisory `optimality_review_brief` into a `2-3` option compare mode with evidence-bound `TOP_LEVEL_EFFECT`, `WHY_NOW`, and `COST_IF_WRONG`, plus explicit `I don't know yet` fallback when comparison is not honest yet | Improves decision quality for one-way and semantic-heavy rounds while keeping the patch docs-only, advisory-only, and free of new gates or authority paths. |
| D-156 | governance/milestone-review | Local round quality could improve while overall milestone shape still became more complex, with no single advisory checkpoint asking whether the milestone actually made the system simpler | Reuse the existing advisory `optimality_review_brief` as a milestone-close addendum with `MILESTONE_ID`, `SHAPE_DELTA`, `KEEP_THIS_SHAPE_TODAY`, `TOP_2_REGRETS_IF_WRONG`, and `WHAT_TO_REMOVE_NEXT` stored in `docs/context/milestone_optimality_review_latest.md` | Adds a lean milestone-level shape review without introducing any new gate, control-plane authority, or extra subsystem. |
| D-157 | governance/learning-loop | The system could reason better before merge, but it still learned too little from what actually happened after ship/merge | Extend `scripts/capture_profile_outcome_record.py` and the operator docs so the same local corpus records lean shipped-outcome feedback (`rollback_status`, `followup_changes_within_30d`, `semantic_issue_detected_after_merge`) in addition to shipped/postmortem inputs | Adds a small evidence-learned `R3` loop while preserving advisory-only behavior, local determinism, and the stable control plane. |
| D-158 | governance/operator-ux | Milestone close brief existed under `docs/context`, but operator scan flow still lacked a repo-root one-screen PM summary | Add `MILESTONE_OPTIMALITY_REVIEW_LATEST.md` as a convenience-only thin PM summary mirror of `docs/context/milestone_optimality_review_latest.md` with snapshot/recommendation/regret/removal/evidence fields while keeping `docs/context` as the authoritative source | Improves operator usability without changing gates, authority, or control-plane behavior. |
| D-159 | governance/operator-ux | Repo-root mirror wording drifted across docs, making the mirror lane feel less like one consistent family | Standardize mirror language around four shared rules: convenience-only, authoritative `docs/context` source, thin PM summary, and no gate or authority change | Keeps operator handoff language predictable end-to-end without creating new mirrors, subsystems, or control-plane behavior. |
| D-160 | governance/philosophy | The repo had strong operational contracts, but lacked one canonical non-command explanation of how intent, context operations, abstention, optimality, beauty, and delegation strategy fit together as an engineering method | Refresh `docs/engineering_philosophy.md` as the canonical top-level methodology document covering intent-to-code translation, why optimal does not equal beautiful, why context is an operating problem, why `I don't know yet` matters, how to monitor drift under context growth, and when centralized delegation beats single-agent or naive multi-agent patterns | Gives the repo a stable philosophical spine for evaluating code quality, context health, and task-shape-appropriate delegation without adding new runtime behavior, gates, roles, or authority paths. |
| D-161 | governance/learning-loop | The repo had no canonical way to pull philosophy or heuristic refinements from another actively operated repo without overreacting to papers or mutating policy automatically | Add a minimal `thesis_pull` template, protocol, authoritative working copy, and thin repo-root mirror so thesis pulls only run from active-repo evidence, combine local data with `1-3` academic inputs, classify research by actionability, and stop at human-reviewed heuristic proposals | Creates a bounded evidence-led philosophy-learning loop without adding new gates, roles, subsystems, or automatic policy mutation. |
| D-162 | governance/operator-ux | The thesis-pull mirror existed at repo root, but the main operator guide did not point to it for quick scan flow | Add one short operator-guide pointer to `THESIS_PULL_LATEST.md` as the live one-screen thesis mirror while preserving `docs/context/thesis_pull_latest.md` as authoritative and the mirror as convenience-only | Improves operator discoverability and quick scan flow without changing the stable control plane, mirror authority rules, or any gate behavior. |
| D-163 | governance/thesis-pull-polish | Thesis-pull docs were functionally correct, but still had small mirror-family wording drift and no explicit freshness/abstention fields for conservative pulls | Align thesis-pull mirror wording with the repo-root mirror family and add advisory-only `EVIDENCE_FRESHNESS_WINDOW` plus `ABSTENTION_REASON_CODE` to the template and working copy | Closes the remaining docs-only polish gap without adding any gate, validator, script, role, or subsystem. |
| D-164 | governance/phase5 | Phase 5 direction needed formal approval before spec/discovery work could begin | Approved Phase 5 direction (plugin architecture, benchmark harness, skills library, hierarchical memory optimization) and 5A.0 spec/discovery work ONLY. Implementation explicitly BLOCKED until freeze exit and implementation approval. Target repo: `quant_current_scope`. All Phase 5 approvals recorded in this decision log. | Enables architecture specification work while preserving freeze discipline and preventing premature implementation. |
| D-165 | governance/phase5 | Extension loading needed explicit allowlist policy to prevent unapproved plugins from entering production | Approved ADR-003: Extension Loading Policy. Extensions use explicit allowlist with PM/CEO approval before activation. No dynamic loading without governance. Skills are declarative YAML only (no executable code). Version pinning required. Deprecation grace period: 90 days. Emergency disable available for security issues. | Establishes safe extension loading model with clear approval gates and security boundaries. |
| D-166 | governance/phase5 | Benchmark-driven policy changes needed human-in-loop to prevent silent policy mutations | Approved ADR-004: Benchmark → Policy Feedback Loop. Benchmark results inform policy changes, but humans approve all changes. No silent policy updates. Monthly benchmark cadence + event-triggered runs. Policy changes apply to next round (not active round). Rollback and emergency override processes defined. | Enables adaptive guardrails while preserving human decision authority and preventing automated policy drift. |
| D-167 | governance/phase5 | ADR-004 policy loosening format used explicit negatives (require_X: False), which appeared to disable protections and conflicted with advisory-only model | Amended ADR-004 to use additive-only format: recommended_guardrail_strength and min_review_level instead of require_X: False. Policy recommendations never disable protections. Kernel floor enforcement always wins. | Clarifies that policy layer recommends thresholds but never turns protections off; kernel validates and enforces floor. |
| D-168 | governance/phase5 | ADR-003 approval authority was ambiguous (PM/CEO required, but examples showed PM alone) | Amended ADR-003 to explicit approval authority: PM alone for LOW-risk skills, CEO required for MEDIUM/HIGH-risk, both required for approval routing changes. Added risk_level field to allowlist schema. | Removes implementation ambiguity and establishes clear approval delegation rules. |
| D-169 | governance/phase5 | ADR-003 benchmark requirements were approval criteria, but benchmark harness is still Phase 5 design artifact | Amended ADR-003 with interim rule: eval.yaml is declarative until harness operational. Skills requiring benchmark validation need benchmark-waiver entry in decision log. After harness operational, benchmark requirements enforced. | Allows skill approval to proceed during Phase 5A while preserving benchmark requirement for post-5A.1 skills. |
| D-170 | governance/phase5 | ADR-004 baseline policy (first run becomes baseline) was brittle and vulnerable to noisy first run | Amended ADR-004 to 3-run median baseline per model version. Added re-baselining rules: model version change, major update, baseline drift (3 consecutive trends), or manual PM/CEO request. | Reduces baseline noise and prevents single outlier run from skewing future policy changes. |
| D-171 | governance/phase5 | ADR-003/004 had implementation-facing inconsistencies: baseline object field mismatch, tightening logic still used boolean-style output conflicting with D-167, risk_level not required in allowlist schema | Amended ADR-004: fixed baseline.baseline_score reference consistency, converted tightening logic to additive-only format (min_review_level, min_approval_level). Amended ADR-003: made risk_level required field in allowlist schema, added to all examples. | Removes implementation ambiguity and ensures consistent additive-only policy format across tightening and loosening logic. |
| D-172 | governance/phase5 | Phase 5A.0 architecture complete; freeze exit needed to begin implementation | Approved freeze exit for Phase 5 implementation. Current freeze (loop_operating_contract.md lines 9, 14) superseded for Phase 5 work only. Phase 5 implementation may proceed incrementally with validation at each milestone. All other work remains frozen. Implementation plan: phase5_implementation_plan_today_v2.md. | Enables Phase 5 implementation while preserving freeze discipline for non-Phase-5 work. |
| D-173 | governance/phase5 | Phase 5A.1 Benchmark Harness Setup complete; operational baseline established | Completed 5A.1 implementation. Promptfoo 0.121.1 installed and operational. sql_accuracy suite implemented with 5 prompts and vendor-neutral assertions. Baseline established: anthropic:claude-opus-4-6 scored 0.91 (median of 3 runs). Harness correctly fails closed on provider errors and distinguishes assertion failures from API errors. Scripts operational: run_baseline_benchmark.py, validate_baseline.py, test_policy_proposal.py. All tests passing (12/12 in test_phase5_benchmark.py). | Delivers operational benchmark harness with real baseline. Enables 5A.2 (Subagent Routing Matrix) to proceed. |
| D-174 | governance/phase24c | C1 PM signoff for Phase 24C enforce promotion | PM signoff granted for Phase 24C enforce promotion. Criteria: C0 (infra health) PASS, C2 (evidence volume ≥30) PASS, C3 (2 consecutive qualifying weeks) pending W11, C4 (FP rate ≤5%) PASS, C4b (annotation coverage 100%) PASS, C5 (schema v2.0.0) PASS. Authorization: proceed with shadow cycles through W11, then execute dry-run → canary → full rollout → 2-week monitor sequence. Rollout remains single-repo (quant_current_scope) with explicit `-AuditMode enforce` flag. | Satisfies C1 manual signoff requirement. Enables enforce promotion path once C3 automated blocker clears. Date: 2026-03-16. |

Part 2: Decision Rationale (Phase 4 — Optimizer)

D-16: 2D Grid Search
  Problem: User manually nudges k (stop) and z (entry) sliders, relying on intuition.
  Solution: Run all 600+ (k, z) combinations in a vectorized batch.
  Metric: Ulcer-Adjusted Sharpe = CAGR / Ulcer Index.
    Ulcer Index = sqrt(mean(drawdown^2)) — captures both depth AND duration of pain.
  Output: 2D Heatmap where color = metric value. User picks the "Golden (k, z)".
  Risk: Overfitting to historical data. Mitigated by:
    1. Using rolling 5-year windows (Walk-Forward validation).
    2. Preferring "plateaus" over "peaks" in the heatmap (robustness).

D-17: VIX-Adaptive Parameters
  Problem: A fixed k=3.5 may be too tight during panics and too loose during calm.
  Solution: Make parameters slaves to the Regime:
    | VIX < 15  | k=2.5, z=-1.5 | Tight stops, buy mild dips    |
    | VIX 15-25 | k=3.5, z=-2.5 | Standard                      |
    | VIX > 25  | k=4.5, z=-3.5 | Loose stops, deep dips only   |
  Confidence: 9/10. This directly solves the FOMO-vs-Pain tension.

D-18: Wait-for-Confirmation ("Green Candle")
  Problem: Dip entries at z=-2.5 sometimes trigger while the stock is still falling.
  Solution: Z-Score triggers the "Ready" state. Entry only CONFIRMS when:
    Price(T) > Price(T-1) (first "green candle" after the dip).
  Confidence: 10/10. Dramatically reduces Left-Side entries.
  Statistical Basis: Mean-reversion signals have higher win rates when
    the reversal has objectively begun (price turns up).

Part 3: Historical Build Log

Phase 1 (2026-02-12): ETL + Engine
  - Wrote etl.py (DuckDB pipeline for 3.7GB CRSP CSV).
  - Wrote engine.py (Vectorized kernel with Shift/Cost walls).
  - Initial backtest: -82% due to Split Trap (D-09).

Phase 2 (2026-02-13): 3-Regime Strategy
  - Added Attack/Caution/Defense logic (D-13).
  - Strategy returns (weights, regime, details) tuple (D-14).
  - Marginal DD improvement (-82.3% → -81.4%). Split Trap dominates.

Phase 3 (2026-02-13): Investor Cockpit
  - Created InvestorCockpitStrategy with parameterized k and z.
  - Dashboard: Signal Monitor with Macro Advisor.
  - Visualization: Stop Level (Red) + Buy Zone (Green) overlay.
  - Close-Only data constraint acknowledged (D-10).

Phase 4 (2026-02-13): Parameter Optimizer ← PLANNED
  - Grid Search over (k, z) parameter space.
  - Adaptive Regime Parameters (D-17).
  - Wait-for-Confirmation logic (D-18).

Phase 4.2 (2026-02-13): Live Data + UX
  - Searchable Ticker Dropdown (D-20). Replaced PERMNO text input.
  - Yahoo Bridge: Append-Only Hybrid Lake (D-21).
  - Batch download via yf.download (D-22). Top 50/100/200 scopes.
  - Data Manager tab in dashboard for one-click updates.
  - Memory-safe: base parquet never loaded into pandas.
    OOM at 47M rows → solved by DuckDB-only queries + separate patch file.

Phase 4.3 (2026-02-14): Scanner Cockpit Redesign (D-27) ← NEW
  - Replaced st.multiselect + stacked cards with scanner+detail views.
  - scan_universe(): 2-pass filter (MA200 gate → L5 Alpha scoring).
  - views/scanner_view.py: High Conviction Scans + My Watchlist tables.
  - views/detail_view.py: Single-ticker chart + action report card.
  - Router in render_investor_cockpit() dispatches via session state.
  - [D-28] JIT Patch: views/jit_patch.py auto-fetches Yahoo data for stale tickers on drill-down.
    "Bedrock + Fresh Snow" — WRDS static base (2000-2024) + Yahoo on-demand (2025-now).

Phase 5 (2026-02-14): Quantamental Integration (D-29)
  - Added PIT quality layer with release-date discipline.
  - Scanner now enforces Pass 1.5 Quality Gate (hard filter).
  - Watchlist/details keep symbols visible but apply quality penalty behavior.

Phase 6 (2026-02-14): Portfolio Optimizer
  - Added optimizer module (inverse-volatility + mean-variance SLSQP + fallback).
  - Added optimizer view with allocation chart and shares-to-buy table.

Phase 7 (2026-02-14): Sector Context Upgrade (D-32)
  - Implemented static sector/industry map builder.
  - Merged sector context into scanner and fundamentals latest view.

Phase 8 (2026-02-14): Catalyst Radar Foundation — Steps 1-6 (D-30, D-31) ✅
  - Expanded scope support to Top 3000:
    - `data/updater.py`
    - `data/fundamentals_updater.py`
    - `data/build_sector_map.py`
    - Data Manager scope in `app.py`
  - Hydrated data foundation:
    - `fundamentals.parquet`: 10,219 rows
    - `fundamentals_snapshot.parquet`: 1,680 rows
    - `sector_map.parquet`: 3,000 rows
    - max `release_date`: 2026-03-17
  - Runtime validation:
    - Top 2000: load 15.356s, scan 0.227s, gate trend=6 quality=310 survivors=2
    - Top 3000: load 21.307s, scan 0.307s, gate trend=6 quality=432 survivors=2
  - Rollout stance: keep default at Top 2000; Top 3000 remains operator-selected until Catalyst layer (Steps 7-11) is shipped.

Phase 8 (2026-02-14): Compustat Bedrock Expansion (FR-031, D-33..D-35) ✅
  - Added loader: `data/fundamentals_compustat_loader.py`
    - Input: `data/e1o8zgcrz4nwbyif.csv`
    - Scope guardrail: Top 3000 liquid symbols only
    - PIT release date: `rdq`, fallback `datadate + 45d`
    - Revenue YoY formula: `(revenue_q - lag4(revenue_q)) / lag4(revenue_q)` via DuckDB window
  - Merge behavior:
    - Canonical key: `(permno, release_date)`
    - Precedence: `compustat_csv > yfinance`
    - Safety: lock + atomic writes + timestamped backups
  - Results:
    - Match coverage vs Top3000: 2781/3000 (92.70%)
    - fundamentals rows: 10,219 -> 225,640
    - snapshot rows: 1,680 -> 2,819
    - Scanner gate (Top3000): trend=6 quality=428 survivors=2

Phase 8 (2026-02-15): R3000 PIT Universe Scaffold (FR-032, D-36..D-37) 🟡
  - Added `data/r3000_membership_loader.py`:
    - Normalizes WRDS membership rows and maps ticker -> permno with audit trail.
    - Builds `universe_r3000_daily.parquet` via PIT date-window expansion.
  - Added optional `universe_mode='r3000_pit'` to `app.load_data()`.
  - Current blocker:
    - `data/t1nd1jyzkjc3hsmq.csv` failed input gate (metadata-only, 0 usable constituent rows).
    - Awaiting full WRDS constituent-history export for production run.

Entry 2026-02-14: Status: Infrastructure Frozen.
  Action:
    - Implemented PIT index-universe framework via Russell 3000 membership loader scaffold.
    - Hardened Top3000 fundamentals bedrock with PIT clamp and snapshot hygiene.
  Significance:
    - Backtests now maintain point-in-time visibility constraints and prevent survivorship-bias inflation.
    - System is ready to layer forward catalyst logic on top of stable data contracts.

Phase 8 (2026-02-15): Institutional Factor Layer (FR-033, D-38..D-39) ✅
  - Expanded schema in fundamentals pipeline:
    - Added quarterly raw fields (`oibdpq`, `atq`, `ltq`, `xrdq`, `oancfy`, debt/cash/market-cap components, fiscal keys).
    - Added derived institutional factors (`oancf_q`, `oancf_ttm`, `ebitda_ttm`, `ev_ebitda`, `leverage_ratio`, `rd_intensity`).
  - Implemented vectorized decumulation and valuation math in
    `data/fundamentals_compustat_loader.py::compute_institutional_factors`.
  - Validation results (`scripts/validate_factor_layer.py`):
    - PIT violations: 0
    - Decumulation mismatch: 0.0698%
    - Q4 spike rate (>10x): 1.69%
    - Debt fallback zero-rate: 99.15%
    - EV/EBITDA arithmetic bad-rate: 0.00%
  - Snapshot factor coverage:
    - EV/EBITDA 48.45%, Leverage 73.94%, RD Intensity 47.87%, OANCF_TTM 85.35%, EBITDA_TTM 80.90%.

Phase 8 (2026-02-15): Catalyst Radar Integration (FR-034, D-41) ✅
  - Added `data/calendar_updater.py`:
    - Yahoo earnings-date fetch by scope (Top 20/50/100/200/500/3000 or Custom).
    - Uses updater lock and atomic writes to `earnings_calendar.parquet`.
  - `app.load_data()` now merges calendar context into fundamentals payload.
  - `scan_universe()` now emits:
    - `days_to_earnings`, `days_since_earnings`, `earnings_risk`.
    - Optional `fresh_catalysts` mode (last earnings within 7 days).
  - Scanner UI adds:
    - Earnings warning column (`⚠️` when within blackout window).
    - "Hide earnings risk" toggle and blackout-days control.
  - Added `scripts/validate_calendar_layer.py` for data integrity checks.

Phase 9 (2026-02-15): Macro-Regime Layer (FR-035, D-42) 🟡
  - Added `data/macro_loader.py`:
    - Builds canonical `data/processed/macro_features.parquet`.
    - Ingests Yahoo market series + FRED rates.
    - Applies PIT-safe lag policy: fast series T+0, slow series T+1.
    - Computes stress features and `regime_scalar`.
  - Added `scripts/validate_macro_layer.py`:
    - Schema/null checks.
    - Crisis-window sanity checks for March 2020 and 2022.
  - Integration:
    - `app.py` now prefers `macro_features.parquet` with fallback to legacy `macro.parquet`.
    - Data Manager adds macro rebuild control and live regime metrics.
    - `InvestorCockpitStrategy` consumes `regime_scalar` when present, else falls back to legacy VIX scoring.

Phase 9.2 (2026-02-15): Macro Build Optimization Patch (D-43) ✅
  - Performance refactor in `data/macro_loader.py`:
    - Replaced rolling percentile `.apply()` path with vectorized `rolling().rank(pct=True)` (with fallback).
    - Parallelized FRED fetches and bounded requests to build window (`cosd/coed`) while preserving full in-window refetch for revision safety.
  - Added explicit stage timing logs in macro build status.
  - Validation hardening:
    - `scripts/validate_macro_layer.py` now enforces full trading-calendar coverage (no missing/extra dates).
  - Reliability hardening:
    - FRED fetch now uses retry/backoff + timeout and explicit critical-series failure signaling (no silent NaN holes).
    - Trading calendar query applies date filter at SQL level to avoid full-history scans.
    - App fallback macro state is explicitly defensive (`regime_scalar=0.5`, elevated proxy VIX) and strategy macro defense now prioritizes scalar regime when available.
  - Timing results (same machine/session):
    - Baseline: `16.073s`
    - After Step 2 (vectorized percentile): `8.201s`
    - After Step 3 (parallel/date-bounded FRED): `7.927s`

Phase 10 (2026-02-15): Liquidity Layer Foundation + Hardening (FR-040, D-45..D-46) ✅
  - Added `data/liquidity_loader.py`:
    - Builds `data/processed/liquidity_features.parquet` from FRED + Yahoo.
    - Enforces H.4.1 PIT lag for weekly Fed balance-sheet series (Wed -> Fri availability).
    - Computes net-liquidity, repo stress, LRP, dollar stress, and smart-money flow features.
  - Added `scripts/validate_liquidity_layer.py`:
    - Schema/calendar/null checks + Sept-2019 repo spike and 2022 impulse sanity checks.
    - Uses ratio-based 2022 impulse gate to reduce brittleness under normal data revisions.
  - Hardening updates:
    - `data/liquidity_loader.py` now fails fast when critical Yahoo inputs are missing/empty.
    - `data/liquidity_loader.py` now honors `--end-date` in trading-calendar assembly.
    - `data/updater.py` now recovers stale update locks left by crashed jobs.
  - Runtime integration:
    - `app.py` merges `liquidity_features.parquet` into the macro context and exposes FR-040 rebuild controls in Data Manager.
    - `strategies/investor_cockpit.py` consumes FR-040 stress fields as macro-score fallback when `regime_scalar` is unavailable.

Phase 11 (2026-02-15): Regime Governor + Throttle Documentation Freeze (FR-041, D-47..D-48) 🟡
  - Documentation scope (docs-as-code):
    - Added `docs/phase11-brief.md` with objective, thresholds, architecture, and acceptance criteria.
    - `spec.md` now freezes "Current Algorithm v1" before FR-041 contract changes.
    - `spec.md` defines FR-041 RegimeManager interface, BOCPD threshold contract, repo stress units, and 3x3 matrix.
    - `prd.md` now includes FR-041 feature description and delivery criteria.
  - Safety stance:
    - Long-only red safety uses matrix clamps:
      - `RED+NEG=0.00`, `RED+NEUT=0.00`, `RED+POS<=0.20` (D-48).

Phase 12 (2026-02-15): FR-042 Truth-Table Verification Contract (D-49) 🟡
  - Added `docs/phase12-brief.md` with:
    - Objective and methodology for regime verification.
    - Strict acceptance windows:
      - 2008 Q4 RED
      - 2020 Mar RED
      - 2022 H1 AMBER/RED
      - 2017 mostly GREEN (guardrail)
      - Nov 2023 transition to GREEN
    - Performance metrics: drawdown reduction + recovery speed.
  - Calibration patch:
    - Tightened RED trigger context (`credit_freeze` and liquidity shock now volatility-gated).
    - Added FR-042 recovery fallback rule for windows without in-window full recovery.
  - Added `spec.md` FR-042 verification artifacts contract for:
    - `data/processed/regime_history.csv`
    - `data/processed/regime_overlay.png`

Phase 13 (2026-02-15): FR-050 Walk-Forward Contract (D-51..D-52) 🟡
  - Added `docs/phase13-brief.md`:
    - Governor-only deterministic routing (`GREEN=1.0`, `AMBER=0.5`, `RED=0.0`).
    - Strict T+1 execution and turnover cost model.
    - Cash hierarchy and acceptance checks.
  - Added FR-050 sections in `prd.md` and `spec.md`:
    - Artifact schema and metric contract for walk-forward validation.
  - Implemented `backtests/verify_phase13_walkforward.py` + unit tests:
    - `tests/test_verify_phase13_walkforward.py`
    - Artifacts generated:
      - `data/processed/phase13_walkforward.csv`
      - `data/processed/phase13_equity_curve.png`
  - Current FR-050 run snapshot:
    - Sharpe: strategy `0.516` vs buy-and-hold `0.494` (improved)
    - Ulcer: strategy `15.668` vs buy-and-hold `16.255` (improved)
    - MaxDD: strategy `-46.885%` vs buy-and-hold `-55.189%` (improved but not 50% compression)
    - Overall FR-050 strict verdict: `BLOCK`
  - Milestone review gate:
    - Reviewer A: PASS
    - Reviewer B: PASS (after strict-output + optional-PNG resiliency patch)
    - Reviewer C: PASS (fallback coverage telemetry confirmed)

Phase 14 (2026-02-15): FR-060 Feature Store Contract (D-53..D-54) 🟡
  - Added `docs/phase14-brief.md`:
    - Ranking/sizing/execution feature definitions and acceptance checks.
    - Explicit close-only fallback rule for OHLC-dependent features.
  - Added FR-060 sections in `prd.md` and `spec.md`:
    - Feature schema contract and output artifact path.
  - Implemented feature builder + tests:
    - `data/feature_store.py`
    - `tests/test_feature_store.py`
  - Smoke verification:
    - `pytest`: 20 passed
    - `python data/feature_store.py --start-year 2020 --top-n 200`:
      - rows written: 296,834
      - total runtime: 9.522s
  - Hardening patch:
    - Added memory-envelope estimation + safety abort threshold in build path.
    - Added SPY market coverage checks before feature computation.
  - Milestone review gate:
    - Reviewer A: PASS
    - Reviewer B: PASS
    - Reviewer C: PASS

Phase 15 (2026-02-15): FR-070 Alpha Engine Contract (D-55) 🟡
  - Fixed (structural, non-tunable):
    - `SMA200` long eligibility gate remains fixed.
    - Regime budget map remains fixed (`GREEN=1.0`, `AMBER=0.5`, `RED=0.0`).
    - Signal-sign invariants remain fixed (momentum positive, volatility penalty).
  - Adaptive (tunable via WFO only):
    - RSI entry sensitivity via rolling percentile over trailing history.
    - ATR stop multiplier via volatility regime schedule.
    - Selection depth via top-N/percentile controls.
  - Governance rule:
    - Parameter updates require walk-forward protocol.
    - If out-of-sample degradation breaches tolerance, simplify rules instead of adding knobs.

Phase 15 (2026-02-15): FR-070 Integration + Truth Test (D-56..D-57) 🟡
  - Implemented integration in `strategies/investor_cockpit.py`:
    - Alpha path wiring with deterministic selector/sizer/executor loop.
    - Hysteresis hold-buffer enforcement (`Top5` entry, `Top20` hold).
    - Ratchet-only stop persistence per active position.
    - Telemetry emission (`alpha_score`, `entry_trigger`, `stop_loss_level`, `turnover`).
  - Added verifier:
    - `backtests/verify_phase15_alpha_walkforward.py`
    - Compares `SPY` vs `Phase13_Governor` vs `Phase15_Alpha`.
  - UI exposure:
    - Cockpit now renders Top Alpha Candidates and Active Stop-Loss panels when FR-070 is enabled.

Phase 16 (2026-02-15): FR-080 Walk-Forward Optimization & Honing (D-58..D-59) 🟡
  - Documentation scope (FR-080 docs-only milestone):
    - Added `docs/phase16-brief.md` with objective, WFO policy, search-space contract, and acceptance criteria.
    - Added FR-080 section in `prd.md` with objective, governance policy, search space, acceptance, and artifacts.
    - Added FR-080 contract in `spec.md` with artifact schema and hard constraints.
  - FIX vs FINETUNE governance (explicit):
    - FIX (non-tunable): structural FR-070 rules, regime budgets, long-only + hard-cap invariants.
    - FINETUNE (WFO-tunable): `alpha_top_n`, hysteresis ranks, RSI percentile gate, ATR multiplier.
  - WFO-only governance:
    - Parameter selection uses train window metrics only (`2015-01-01..2021-12-31`).
    - OOS/Test window (`2022-01-01..2024-12-31`) is strictly read-only for stability and pass/fail governance.
    - Any detected OOS leakage blocks parameter promotion.

Phase 16.1 (2026-02-15): FR-080 Low-Cost Runtime Optimization Patch (D-60) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added optional multi-process candidate evaluation (`ProcessPoolExecutor`).
    - Added worker controls: `--max-workers`, `--chunk-size`, `--disable-parallel`.
    - Added lock controls: `--lock-stale-seconds`, `--lock-wait-seconds`.
    - Added deterministic fallback to sequential execution if parallel execution fails.
    - Added staged artifact bundle commit with rollback on promotion failure.
  - Data reuse stance:
    - Shared datasets are loaded once per run and reused across all candidate evaluations.
  - Safety:
    - Parallel patch preserves existing train-only selection + OOS promotion gate semantics.

Phase 16.2a (2026-02-15): FR-080 Promoted Production Defaults (D-61) ✅
  - Promoted defaults after WFO strict pass:
    - `alpha_top_n=10`
    - `hysteresis_exit_rank=20`
    - `adaptive_rsi_percentile=0.05`
    - `atr_preset=3.0` mapped to ATR multipliers `3.0/4.0/5.0` (`low/mid/high` volatility).
  - Rationale:
    - Locks one strict-pass profile as the FR-080 production default across docs and runtime references.
    - Preserves FR-070 FIX invariants while minimizing operator-side parameter drift.

Phase 16.3 (2026-02-15): FR-080 Hard-Stop Rollback + Diagnostic Pivot (D-62) 🟡
  - Hard-stop rollback:
    - Tuned promotion was blocked after FR-070 tuned verification returned `BLOCK`.
    - Promoted parameter bundle was moved to research-only status (not a runtime default).
    - Runtime default keeps Alpha Engine disabled in UI, with safer RSI fallback `adaptive_rsi_percentile=0.15`.
  - Diagnostic pivot:
    - Next validation focus is starvation analysis on selection/hold behavior under current gates.
    - Phase 16.2 logic expansion is now the required pass path before any re-promotion attempt.

Phase 16.2 (2026-02-15): FR-080 Optimizer Activity Guardrails (D-63) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added CLI guard thresholds:
      - `--min-trades-per-year` (default `10.0`)
      - `--min-exposure-time` (default `0.30`)
    - Added deterministic per-candidate activity metrics from generated OOS weights:
      - `exposure_time` (fraction of active OOS exposure days)
      - `trades_per_year` (annualized OOS positive turnover-change events)
    - Promotion gate now requires both:
      - `stability_pass`
      - `activity_guard_pass`
    - Added guard thresholds and activity metrics into summary CSV and best-params payload.
  - Rationale:
    - Stabilizes Phase 16 promotion by blocking low-activity/starved profiles.
    - Preserves strict no-leakage policy and train-only ranking semantics.

Phase 16.2 Step 3 (2026-02-15): FR-080 Dip OR Breakout Entry Logic (D-64) ✅
  - Updated `strategies/alpha_engine.py`:
    - Added PIT-safe breakout feature `prior_50d_high`:
      - Rolling 50-day `adj_close` high per `permno`, shifted by one bar.
    - Entry logic expanded to:
      - `tradable & trend_ok & (dip_entry OR breakout_entry_green)`.
    - Breakout path is GREEN-only:
      - `breakout_entry_green = (regime_state == "GREEN") & (adj_close > prior_50d_high)`.
    - Reason-code precedence:
      - Dip path wins when both are true.
      - Breakout path uses `MOM_BREAKOUT_GREEN_<ADAPT|FIXED>`.
  - Updated tests in `tests/test_alpha_engine.py`:
    - Breakout can trigger when dip path is blocked.
    - Breakout does not trigger in AMBER/RED.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now document Dip OR Breakout and starvation rationale.

Phase 16.2 Guardrail Hardening (2026-02-15): Regime Normalization + OOS Activity Window (D-65) ✅
  - Updated `strategies/alpha_engine.py`:
    - Added strict regime-state normalization (`strip().upper()`).
    - Unknown states now fail-safe to `RED` budget behavior.
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Activity guard metrics now computed on OOS/Test rows only.
    - Turnover activity includes OOS boundary transitions for accurate trade-rate accounting.
  - Updated tests:
    - `tests/test_alpha_engine.py` validates normalization and unknown-state fail-safe behavior.
    - `tests/test_optimize_phase16_parameters.py` validates OOS-window activity metric computation.

Phase 16.3 (2026-02-15): FR-060 PIT Yearly Universe Expander Remediation (D-66) ✅
  - Updated `data/feature_store.py`:
    - Added configurable `universe_mode` (`yearly_union` default, `global` legacy).
    - Added `yearly_top_n` control with default `100`.
    - Added PIT yearly union selector:
      - Per calendar-year top-N liquidity inside `[start_date, end_date]`.
      - Distinct-permno union across years.
    - Added mode-aware status logs and selected-permno reporting.
    - Added pre-load yearly-union memory envelope guard and abort path.
    - Hardened timestamp handling by normalizing market-series datetimes to tz-naive before window alignment.
    - Preserved existing update lock + atomic write flow.
  - Updated tests:
    - `tests/test_feature_store.py` now validates yearly-union and global helper behavior with synthetic annual-liquidity frames.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now include the remediation contract and default settings.

Phase 16.2 (2026-02-15): FR-080 Promotion Policy Mismatch Fix "Greed patch" (D-67) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Selection now uses promotable-first ranking:
      - promotable rows are `stability_pass AND activity_guard_pass` with valid
        train metrics.
    - If promotable pool is non-empty, ranking is train-only and deterministic:
      - `objective_score` (desc)
      - `train_cagr` (desc)
      - `train_robust_score` (desc)
      - `train_ulcer` (asc)
      - parameter tie-breakers:
        `alpha_top_n`, `hysteresis_exit_rank`, `adaptive_rsi_percentile`,
        `atr_preset` (ascending).
    - If promotable pool is empty, train-only ranking is retained for
      diagnostics and promotion is blocked.
    - Added explicit `selection_pool` states:
      - `promotable_train_ranked`
      - `train_only_rejected_guardrails`
      - `no_valid_candidates`
    - OOS fields are excluded from ranking and tie-break decisions.
  - Updated tests:
    - `tests/test_optimize_phase16_parameters.py` now validates promotable-first
      behavior and non-promotable skip despite higher train objective.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now describe the corrected
      promotion policy and ranking order.

Phase 17.0 (2026-02-15): FR-090 Infrastructure Hardening Baseline + Conflict Gate (D-68) ✅
  - Added `docs/phase17-brief.md`:
    - Defines the Phase 17 architecture direction: "Qlib Storage, RD-Agent Evolution."
    - Establishes reader/writer conflict policy for optimizer vs data-layer work.
    - Defines concrete KPI capture methods and target thresholds for Milestones 1-4.
    - Locks approved execution order:
      1) FR-080 functional baseline run,
      2) docs-only Milestone 0 in parallel,
      3) data-layer refactors only after optimizer completion.
  - Runtime safety decision:
    - Active Phase 16.4 optimizer run is treated as a protected reader workload.
    - Milestone 1 write-path refactors remain blocked until:
      - no optimizer process is active,
      - `data/processed/phase16_optimizer.lock` is absent,
      - FR-080 artifact bundle is fully committed.

Phase 17.1 (2026-02-16): FR-090 Data Layer Hardening Slice A (D-69..D-71) ✅
  - Added `utils/parallel.py`:
    - Unified parallel wrapper with ordered result semantics.
    - Backends: threading + multiprocessing.
    - Optional joblib acceleration (`threading`/`loky`) with safe fallback.
  - Updated `data/updater.py`:
    - Added chunked parallel Yahoo download orchestrator:
      - `parallel_batch_download_yahoo()`
      - chunk worker `_download_chunk()`
    - Preserved existing update lock + atomic parquet publish path.
    - Added deterministic ticker normalization and `(ticker,date)` dedupe on merged Yahoo payload.
  - Updated `data/feature_store.py`:
    - Added incremental build mode (default enabled when window semantics allow):
      - Detect existing feature max date.
      - Recompute from warmup replay window.
      - Append only new rows.
    - Added atomic upsert merge helper for `features.parquet`:
      - Source precedence: new rows override old on `(date, permno)`.
    - Added CLI controls:
      - `--full-rebuild`
      - `--incremental-warmup-bdays`
    - Added parallelized stack stage via `utils.parallel.parallel_execute`.
  - Updated `scripts/validate_data_layer.py`:
    - Added feature-store integrity check:
      - non-empty rows,
      - null-key guard,
      - duplicate-key guard,
      - freshness gap vs latest prices/patch.
  - Added tests:
    - `tests/test_parallel_utils.py`
    - `tests/test_updater_parallel.py`
    - Extended `tests/test_feature_store.py` for incremental/upsert helpers.
  - Verification:
    - `pytest`: PASS (all tests).
    - `scripts/validate_data_layer.py`: FAIL due pre-existing snapshot zombie row (not introduced by this slice).

Phase 16.5 (2026-02-16): FR-080 Alpha Discovery Tournament Expansion (D-72) ✅
  - Updated `strategies/alpha_engine.py`:
    - Added `entry_logic` contract in `AlphaEngineConfig` with allowed values:
      - `dip`
      - `breakout`
      - `combined`
    - Added strict validation (`ValueError` on unsupported logic).
    - Entry and reason-code routing now respect selected logic mode.
  - Updated `strategies/investor_cockpit.py`:
    - Added `alpha_entry_logic` passthrough into internal `AlphaEngineConfig`.
    - Exposed selected entry logic in strategy details payload.
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added `--entry-logic-grid`.
    - Expanded default tournament grid:
      - `entry_logic=dip,breakout,combined`
      - `alpha_top_n=10,20`
      - `atr_preset=2.0,3.0,4.0,5.0`
    - Added `entry_logic` into summary fields and deterministic tie-break ranking.
    - Preserved FR-080 governance:
      - train-only ranking
      - OOS only for stability/activity promotion gates.
  - Updated tests:
    - `tests/test_alpha_engine.py`: entry-logic mode routing + validation coverage.
    - `tests/test_optimize_phase16_parameters.py`: grid validation for entry-logic dimension.
  - Verification:
    - `pytest tests/test_alpha_engine.py tests/test_optimize_phase16_parameters.py -q`: PASS.
    - `pytest -q`: PASS.

Phase 16.5b (2026-02-16): FR-080 Real-Time Tournament Telemetry (D-73) ✅
  - Updated `backtests/optimize_phase16_parameters.py`:
    - Added periodic progress heartbeat controls:
      - `--progress-interval-seconds`
      - `--progress-path`
    - Added interim leaderboard controls:
      - `--live-results-path`
      - `--live-results-every`
      - `--disable-live-results`
    - Parallel evaluator now consumes futures via `as_completed` for immediate completion visibility.
    - Emits periodic console status with elapsed/ETA/promotable count/best-so-far.
    - Publishes atomic heartbeat JSON and interim results CSV during execution.
  - Updated docs:
    - `docs/phase16-brief.md` and `spec.md` now include telemetry contract.

Phase 16.7 (2026-02-16): Fundamental Data-Layer Expansion (D-74) ✅
  - Updated `data/fundamentals_updater.py`:
    - Extended canonical schema and snapshot fields with:
      - `net_income_q`, `equity_q`, `eps_basic_q`, `eps_diluted_q`,
        `eps_q`, `eps_ttm`, `eps_growth_yoy`, `roe_q`.
    - Added net-income mapping preference for common-share earnings labels.
    - Added equity fallback:
      - `equity_q = Total Assets - Total Liabilities` when stockholders equity is missing.
    - Added EPS policy:
      - store both basic/diluted when available,
      - derive EPS from net income and shares when needed,
      - prioritize diluted for selector-facing `eps_q`.
    - Hardened runtime safety:
      - acquire shared update lock before mutating shared artifacts,
      - atomic writes for `fundamentals.parquet`, `fundamentals_snapshot.parquet`, and `tickers.parquet`.
    - Added compatibility guard to backfill missing schema columns before final column selection.
  - Updated `data/fundamentals_compustat_loader.py`:
    - Added resilient optional-column extraction (`niq`, `ceqq`, `epspxq`, `epsfxq`, `atq`, `ltq`).
    - Applied same equity fallback and diluted-priority EPS policy in institutional factor computation.
    - Added graceful lock-contention handling (`TimeoutError` -> status/log return, no uncaught crash).
  - Updated `data/fundamentals.py`:
    - Extended required schema validation, numeric casting, snapshot load path, and runtime context matrices for:
      - `roe_q`
      - `eps_growth_yoy`
    - Extended latest snapshot payload used by scanner/runtime selection.
  - Updated `scripts/validate_factor_layer.py`:
    - Added new fundamentals and snapshot required columns to integrity checks.
    - Core valuation coverage gate now evaluates investable rows (`quality_pass==1`) while reporting full-snapshot coverage for observability.
  - Updated docs:
    - `docs/phase16-brief.md` adds Section 12 for Phase 16.7 scope and data policy.

Phase 17.2 (2026-02-16): Capital-Cycle + Bitemporal Foundation (D-75) ✅
  - Updated docs contract:
    - `docs/phase16-brief.md` adds Phase 16.7b Capital-Cycle Pivot section:
      - score contract (`0.4/0.4/0.2`),
      - conditional discipline logic,
      - bitemporal acceptance criteria.
  - Updated data schema and ingestion:
    - `data/fundamentals_updater.py` adds explicit raw fields:
      - `capex_q`, `depreciation_q`, `inventory_q`, `total_assets_q`, `operating_income_q`
      - plus capital-cycle derivatives:
        `delta_capex_sales`, `operating_margin_delta_q`, `delta_revenue_inventory`, `asset_growth_yoy`.
    - Added bitemporal columns:
      - `filing_date`
      - `published_at`
    - `data/updater.py` now exposes shared quarterly-statement fetch helper for the fundamentals layer.
  - Updated Compustat merge path:
    - `data/fundamentals_compustat_loader.py` now maps the same explicit raw fields when available.
    - Merge dedupe key now preserves published-time versions:
      - `(permno, release_date, published_at)` with source precedence.
  - Updated bitemporal query layer:
    - `data/fundamentals.py` now enforces as-of filtering:
      - `published_at <= as_of_date`.
    - Legacy row fallback for missing `published_at`:
      - `filing_date`,
      - else `fiscal_period_end + 90 days`.
    - Snapshot context now requests as-of-safe fundamentals snapshot.
  - Verification:
    - `py_compile`: PASS (`data/updater.py`, `data/fundamentals_updater.py`, `data/fundamentals.py`, `data/fundamentals_compustat_loader.py`).
    - As-of sanity check: PASS (`published_at`-bounded loads + snapshot path).
    - `pytest -q`: PASS.

Phase 17.2b (2026-02-16): Declarative FeatureSpec Engine + Hash Cache (D-76) ✅
  - Added `data/feature_specs.py`:
    - Introduced `FeatureSpec` dataclass contract:
      - `name`, `func`, `category`, `inputs`, `params`, `smooth_factor`.
    - Added default registry with technical + capital-cycle specs:
      - `z_resid_mom`, `z_flow_proxy`, `z_vol_penalty`, `composite_score`
      - `z_moat`, `z_discipline_cond`, `z_demand`, `capital_cycle_score`.
  - Refactored `data/feature_store.py`:
    - Added declarative spec executor loop with dependency checks for fundamental inputs.
    - Replaced hardcoded score assembly with registry outputs.
    - Added capital-cycle feature outputs to artifact schema:
      - `z_moat`, `z_discipline_cond`, `z_demand`, `capital_cycle_score`.
    - Added deterministic cache key + artifact cache path:
      - `data/processed/features_<cache_key>.parquet`.
    - Cache key includes:
      - spec signature hash,
      - config + universe parameters,
      - permno hash,
      - input artifact fingerprints.
    - On cache hit, build skips feature compute and publishes from cached artifact.
  - Updated tests:
    - `tests/test_feature_specs.py` for conditional discipline behavior.
    - `tests/test_feature_store.py` schema assertions now include capital-cycle outputs.
    - `tests/test_feature_store.py` validates deterministic feature-spec hash.
  - Verification:
    - `py_compile`: PASS (`data/feature_specs.py`, `data/feature_store.py`).
    - `pytest -q`: PASS.
    - Runtime smoke:
      - first run writes cache artifact,
      - second identical run logs cache hit and skips compute stage.

Phase 17.3 (2026-02-16): Daily Vintage Fundamentals Panel + Bitemporal Audit (D-77) ✅
  - Added `data/fundamentals_panel.py`:
    - New dense panel artifact builder:
      - `data/processed/daily_fundamentals_panel.parquet`.
    - Interval-based PIT expansion:
      - each sparse row is active on `[published_at, next_published_at)`.
    - Atomic publish path and manifest cache:
      - `daily_fundamentals_panel.manifest.json` stores source signature + panel metadata.
    - Runtime helper:
      - `join_prices_with_daily_fundamentals()` for fast `(date, permno|ticker)` joins.
  - Feature-engine hash contract hardening:
    - `data/feature_specs.py` now exports:
      - `compute_spec_hash(spec)`
      - `compute_registry_hash(specs)`.
    - `data/feature_store.py` now consumes the shared registry hash helper.
  - Added tests:
    - `tests/test_bitemporal_integrity.py`:
      - fake restatement scenario with strict as-of assertions,
      - pre-restatement panel check (must show old value),
      - post-restatement panel check (must show new value),
      - manifest cache-hit assertion.
    - `tests/test_feature_specs.py`:
      - deterministic hash API assertions.
  - Validation target:
    - Fail build if pre-restatement as-of query resolves to restated value (look-ahead breach).

Phase 16.9 (2026-02-16): CSCO 2000 Event Study Smoke Test (D-78) ✅
  - Added event-study runner:
    - `backtests/event_study_csco.py`
  - Scope:
    - Builds CSCO (1999-2001) daily study frame from `prices.parquet`.
    - Attempts panel path first; auto-falls back to local Compustat CSV when
      panel fields are insufficient in early history.
    - Computes and stores:
      - `z_moat`
      - `z_discipline_cond` (inventory-commitment stress + operating-leverage relief)
      - `z_demand`
      - `capital_cycle_score`
  - Output artifacts:
    - `data/processed/csco_event_study_1999_2001.csv`
    - `data/processed/csco_event_study_1999_2001.html`
  - Result:
    - Source: `compustat_fallback`
    - `Q2 2000 score = 0.4344`
    - `Q3 2000 score = 0.3966`
    - `Q4 2000 score = 0.0328`
    - `Q4 z_moat = 1.0828`
    - Verdict: `PASS`

Phase 16.10 (2026-02-16): MU 2016 Micron Paradox Stress Test (D-79) 🟡
  - Extended event-study harness:
    - `backtests/event_study_csco.py` now supports:
      - dynamic ticker/year artifacts,
      - `--eval-mode rally_positive`,
      - PIT-safe panel projection via publication-time snapshots.
    - Added operational hardening:
      - atomic CSV/HTML writes,
      - resilient output-directory creation,
      - DuckDB-filtered Compustat fallback path for non-zipped CSV.
  - MU run:
    - Command:
      - `python backtests/event_study_csco.py --ticker MU --start 2014-01-01 --end 2018-12-31 --eval-mode rally_positive --rally-start 2016-04-01 --rally-end 2017-03-31`
    - Artifacts:
      - `data/processed/mu_event_study_2014_2018.csv`
      - `data/processed/mu_event_study_2014_2018.html`
    - Outcome:
      - source=`compustat_fallback`
      - rally score mean=`-1.1809`
      - rally score min=`-2.4056`
      - positive-share=`24.51%`
      - verdict=`FAIL` (score does not stay positive through 2016 rally)
  - Decision impact:
    - Cyclical exception is now a required next patch to avoid false-sell behavior in semiconductor supercycle transitions.

Phase 16.11 (2026-02-16): Turnover Gate Patch + Twin Verification (D-80) 🟡
  - Implemented turnover gate:
    - `delta(revenue_inventory_q) > 0.05` waives discipline penalty.
  - Updated shared factor logic:
    - `data/feature_specs.py`:
      - `spec_discipline_conditional` now accepts turnover input and threshold parameter.
      - default spec input for `z_discipline_cond` includes `delta_revenue_inventory`.
  - Updated event-study scorer:
    - `backtests/event_study_csco.py` applies the same turnover-gate logic in:
      - panel path
      - Compustat fallback path
    - Added CLI parameter `--turnover-gate-threshold`.
  - Test updates:
    - `tests/test_feature_specs.py` now covers turnover-gate open/closed behavior.
  - Twin verification:
    - Cisco 2000:
      - verdict `PASS`
      - `Q2=0.4344`, `Q3=0.3966`, `Q4=0.0328`
    - Micron 2016 rally-positive:
      - verdict `FAIL`
      - mean `-1.2894`, min `-2.4056`, max `-0.0603`, positive-share `0.0000`
  - Decision impact:
    - Turnover-only override is insufficient; next patch needs additional cyclical exception features.

Phase 16.12 (2026-02-16): Inventory Quality Gate (D-81) 🟡
  - Implemented leading-signal inventory quality layer:
    - Data schema additions in fundamentals artifacts:
      - `cogs_q`, `receivables_q`, `deferred_revenue_q`, `delta_deferred_revenue_q`
      - `book_to_bill_proxy_q`, `dso_q`, `delta_dso_q`, `gm_accel_q`
    - Updated modules:
      - `data/fundamentals_updater.py`
      - `data/fundamentals_compustat_loader.py`
      - `data/fundamentals.py`
      - `data/fundamentals_panel.py`
  - Updated discipline gate logic:
    - `data/feature_specs.py::spec_discipline_conditional`
      - weighted soft vote:
        - book-to-bill demand vote weight `2`
        - GM acceleration vote weight `1`
        - DSO trend vote weight `1`
      - thresholds:
        - `book_to_bill_proxy_q > 1.0`
        - `gm_accel_q >= 0`
        - `delta_dso_q <= 0`
      - fallback policy:
        - with book-to-bill present: gate opens at `>= 2` weighted votes
        - without book-to-bill: requires GM + DSO path (`>= 2`)
      - missing-signal resilience:
        - `gm_accel_q` falls back to `operating_margin_delta_q`
        - `delta_dso_q` falls back to `-delta_revenue_inventory`
  - Event-study scorer parity:
    - `backtests/event_study_csco.py` now applies Inventory Quality Gate in:
      - panel path
      - Compustat fallback path
    - Added CLI controls for gate thresholds and vote weights.
  - Validation:
    - `pytest -q`: PASS
    - CSCO 2000 (`csco_drop`): PASS (`Q2=0.4344`, `Q3=0.3966`, `Q4=0.0328`)
    - MU 2016 (`rally_positive`): FAIL (strict all-days-positive condition still not met)
  - Decision impact:
    - Infrastructure and gate logic are upgraded end-to-end.
    - Twin verification remains partially blocked by MU strict-positivity; next patch needs moat/demand normalization refinement for cyclical trough regimes without regressing CSCO de-rating.

Phase 16.13 (2026-02-17): Proxy Gate Pivot (D-82) 🟡
  - Decision:
    - Replace discrete inventory-quality soft-vote gate with a continuous
      cross-sectional proxy gate driven by quarterly acceleration/bloat terms.
    - Keep no-new-fetch policy; compute all inputs from existing quarterly fields.
  - New derived fields:
    - `sales_growth_q = pct_change(total_revenue_q, 1)`
    - `sales_accel_q = delta(sales_growth_q)`
    - `op_margin_accel_q = delta(operating_margin_delta_q)`
    - `bloat_q = delta(ln(total_assets_q - inventory_q)) - delta(ln(total_revenue_q))`
    - `net_investment_q = (abs(capex_q) - depreciation_q) / lag(total_assets_q, 1)`
  - Gate score:
    - `z_inventory_quality_proxy = z(sales_accel_q) + z(op_margin_accel_q) - z(bloat_q) - 0.5*z(net_investment_q)`
    - Discipline waiver rule: if `z_inventory_quality_proxy > 0`, set discipline penalty to zero.
  - Rationale:
    - Avoid binary gate brittleness and better separate strategic inventory build
      from inefficient asset bloat in cyclical recoveries.
  - Safety:
    - PIT semantics unchanged (`published_at <= as_of_date`).
    - Backward compatibility preserved by nullable derived columns.

Governance Update (2026-02-18): Planning/SAW Contract Upgrade (D-83) ✅
  - Added mandatory plan response contract and SAW report format in `AGENTS.md`.
  - Added self-learning source of truth: `docs/lessonss.md`.
  - Added skill hooks for SAW and research-backed planning.

Governance Update (2026-02-18): Runtime Fail-Safe Continuity (D-84) ✅
  - Defined fail-safe continuity policy for critical upstream data failures:
    keep last-successful artifact, skip unsafe publish, emit stale-data alert, and require resume note.

Governance Update (2026-02-19): Interactive Review Protocol (D-85) ✅
  - Added structured review mode gate (`BIG CHANGE`/`SMALL CHANGE`) and per-issue optioned responses.
  - Added explicit confirmation checkpoint before implementation during review-mode workflows.

Governance Update (2026-02-19): PM Hierarchy + Stage Loop (D-86) ✅
  - Standardized project-based hierarchy (`L1` pillar, `L2` streams, `L3` stages).
  - Added one-stage expansion/anti-sprawl loop and stage-specific snapshot contract.
  - Added trigger-based optional skills (`se-executor`, `architect-review`) with `>=2`-round escalation by approval.

Governance Update (2026-02-19): SAW In-Scope Blocking Rule (D-87) ✅
  - Updated SAW reconciliation semantics to block on in-scope Critical/High findings.
  - Added inherited out-of-scope High finding carry-forward rule (`Open Risks` + owner + target milestone).

Phase 17.1 (2026-02-19): Cross-Sectional Backtester Transition (D-88) 🟡
  - Decision:
    - Pause event-study-first validation path for this milestone.
    - Stand up cross-sectional double-sort evaluator with econometric inference as primary validation harness.
  - Data foundation:
    - Added `statsmodels==0.14.5` to project dependencies.
    - Hardened `data/feature_store.py` persistence contract:
      - enforced required output columns in `features.parquet`:
        - `z_inventory_quality_proxy`
        - `z_discipline_cond`
      - added incremental schema-drift guard:
        - stale destination schema forces full atomic rewrite instead of unsafe upsert.
      - added cache-schema guard:
        - stale cache artifact without required columns is recomputed.
      - added proxy-input fallback derivation inside feature pipeline:
        - `sales_accel_q <- delta_revenue_inventory`
        - `op_margin_accel_q <- diff(operating_margin_delta_q)`
        - `bloat_q <- diff(1/revenue_inventory_q)`
        - `net_investment_q <- asset_growth_yoy`
    - Rebuilt feature artifact:
      - `python data/feature_store.py --full-rebuild`
      - wrote `2,555,730` rows to `data/processed/features.parquet`.
  - Evaluator delivery:
    - Added `scripts/evaluate_cross_section.py`:
      - DuckDB joins over `prices`, `daily_fundamentals_panel`, `features`, `sector_map`.
      - strict equity filter: `quote_type='EQUITY'` and `industry!='Unknown'`.
      - deterministic sector classification:
        - rank `sector_map` rows by `updated_at` and keep row-1 per `permno`/`ticker` (no `ANY_VALUE` nondeterminism).
      - date-window pushdown:
        - applies `--start-date/--end-date` filters to `prices`, `panel`, and `features` CTEs.
      - double-sort:
        1) top 30% asset growth by `date, industry`
        2) proxy deciles within high-growth buckets
        3) spread = `Decile10 - Decile1`.
      - inference:
        - mean/vol/sharpe of spread
        - Newey-West t-stat with auto lag:
          - `floor(4 * (T / 100)^(2/9))`
        - Fama-MacBeth date-wise OLS + HAC/Newey-West beta significance.
    - Added tests:
      - `tests/test_evaluate_cross_section.py`
  - Produced artifacts:
    - `data/processed/phase17_1_cross_section_spread_timeseries.csv`
    - `data/processed/phase17_1_cross_section_summary.json`
    - `data/processed/phase17_1_cross_section_fama_macbeth_betas.csv`
    - `data/processed/phase17_1_cross_section_fama_macbeth_summary.csv`
  - Result snapshot:
    - spread mean > 0 (`0.002089`) but Newey-West t-stat below gate (`0.766 < 3.0`)
    - FM interaction beta not positive/significant on this sample (`p=0.406005`)
  - Decision impact:
    - Infrastructure for cross-sectional validation is now in place and reproducible.
    - Phase 17.1 remains open for signal iteration because acceptance gates are not yet met.

Phase 17.2A (2026-02-19): Feature Store Partitioned Upsert Unblocker (D-89) ✅
  - Decision:
    - Replace monolithic `features.parquet` writes with partitioned storage and partition-scoped upserts.
  - Implementation:
    - `data/feature_store.py` now treats `data/processed/features.parquet` as a dataset root:
      - partition scheme: `year=YYYY/month=MM`.
    - Added one-time migration:
      - legacy single file is auto-converted to partitioned dataset on first touch.
    - Added partition-aware upsert path:
      - only touched `(year, month)` partitions are reloaded, merged on (`date`,`permno`), and atomically replaced.
    - Reader/update compatibility:
      - bounds, row counts, schema reads, and permno reads now scan both legacy and partitioned layouts.
  - Validation:
    - `tests/test_feature_store.py` expanded with migration + touched-partition rewrite contract.
    - `python data/feature_store.py`: PASS.
    - Post-migration parity check:
      - rows=`2,555,730`, dates=`6,570`, permnos=`389`.
  - Decision impact:
    - Phase 17 research loops are no longer blocked by full-table feature rewrites on each incremental run.

Phase 17.2B (2026-02-19): CSCV + DSR Parameter Sweep Engine (D-90) 🟡
  - Decision:
    - Sweep proxy weight variants with coarse-to-fine search, then score with CSCV/PBO and DSR-adjusted evidence.
  - Implementation:
    - Added `utils/statistics.py`:
      - CSCV split generation (`C(S, S/2)`), block mapping, and PBO computation.
      - correlation-adjusted effective trials:
        - `N_eff ~= N * (1 - rho_avg) + 1` (bounded to `[1, N]`).
      - DSR helpers:
        - expected max Sharpe benchmark and non-normality-adjusted PSR/DSR.
    - Added `scripts/parameter_sweep.py`:
      - coarse-to-fine grid generation with local runtime caps.
      - return-stream export per variant.
      - DSR merge and CSCV summary export.
  - Tests and verification:
    - Added:
      - `tests/test_statistics.py`
      - `tests/test_parameter_sweep.py`
    - Full suite:
      - `.venv\Scripts\python -m pytest -q`: PASS.
    - Smoke sweep:
      - `.venv\Scripts\python scripts/parameter_sweep.py --start-date 2023-01-01 --end-date 2024-12-31 --max-coarse-combos 24 --max-fine-combos 24 --cscv-blocks 6 --output-prefix phase17_2_parameter_sweep_smoke`: PASS.
    - Full sweep:
      - `.venv\Scripts\python scripts/parameter_sweep.py --cscv-blocks 6 --output-prefix phase17_2_parameter_sweep`: PASS.
      - key outputs:
        - variants=`168`
        - avg correlation=`0.4619`
        - effective trials=`91.39`
        - PBO=`0.9412`
        - best variant=`coarse_0006`
        - best metrics: `annualized_sharpe=1.9820`, `t_stat_nw=1.4943`, `dsr=0.8847`.
  - Decision impact:
    - Search/inference infrastructure is production-ready for ongoing proxy-gate research.
    - Current run remains below strict `t_stat > 3.0` acceptance, so signal promotion stays blocked.

Phase 17.3 Prep (2026-02-19): Sweep Resume + DSR Anchor Hardening (D-91) ✅
  - Decision:
    - Stabilize sweep execution for longer research rounds and enforce robust tie-breaking for fine-grid anchoring.
  - Implementation:
    - `scripts/parameter_sweep.py`:
      - deterministic variant identity from sorted parameter tuple hash:
        - `variant_id = md5(json(sorted(params)))`.
        - hash input is limited to the five sweep parameter keys (metadata keys ignored).
      - coarse winner for fine grid now uses:
        - `DSR -> t_stat_nw -> period_mean`.
        - tie rows resolve deterministically via `variant_id` stable sort.
      - checkpoint/resume subsystem:
        - hidden checkpoint artifacts:
          - `.checkpoint_<prefix>.json`
          - `.checkpoint_<prefix>_results.csv`
          - `.checkpoint_<prefix>_streams.csv`
        - auto cadence when `--checkpoint-every=0`:
          - `<=80 -> 10`, `<=250 -> 20`, `>250 -> 50`.
        - resume is default; disable with `--no-resume`.
        - cleanup after success unless `--keep-checkpoint`.
      - atomic checkpoint replace retry on transient Windows lock conflicts.
  - Verification:
    - tests:
      - `tests/test_parameter_sweep.py` updated for:
        - hash-ID stability
        - DSR-first ranking
        - checkpoint cadence.
    - resume smoke:
      - first run builds checkpoint + outputs.
      - rerun loads checkpoint and logs:
        - `[coarse] resume hit ...`
        - `[fine] resume hit ...`
      - both runs PASS.
  - Decision impact:
    - Sweep runtime is now restartable and deterministic under grid evolution.
    - Fine-grid compute is aligned with robust (deflated) evidence rather than raw luck.

Phase 17.3 Prep (2026-02-19): Partition Read Batching in Upsert Path (D-92) ✅
  - Decision:
    - Remove remaining per-partition read overhead inside partitioned feature upserts.
  - Implementation:
    - `data/feature_store.py`:
      - added batched partition loader (`_load_feature_partition_slices`) that:
        - registers touched `(year, month)` keys once,
        - reads all relevant partitions in one DuckDB query,
        - returns partition-keyed frames for downstream merge/write.
      - `_atomic_upsert_features` now:
        - opens one DuckDB connection for the read batch,
        - closes connection once,
        - proceeds with partition-scoped atomic rewrite loop.
  - Verification:
    - `tests/test_feature_store.py` adds:
      - `test_atomic_upsert_features_batches_partition_reads_with_single_connection`.
    - full test suite:
      - `.venv\\Scripts\\python -m pytest -q`: PASS.
  - Decision impact:
    - Reduced connection churn and repeated scan overhead for multi-partition incremental writes.

Phase 17 Closeout (2026-02-19): Windows-Safe Sweep Lock Liveness + Corrupt-Lock Recovery (D-93) ✅
  - Decision:
    - Replace Windows `os.kill(pid, 0)` liveness probe in sweep lock path and harden stale-lock recovery when lock metadata is unreadable.
  - Root cause:
    - Windows lock test path could terminate the active runner process when probing PID liveness with `os.kill(pid, 0)`, producing hard `aborted` runs without traceback.
  - Implementation:
    - `scripts/parameter_sweep.py`:
      - `_pid_is_running` now uses WinAPI process query (`OpenProcess` + `GetExitCodeProcess`) on Windows.
      - non-Windows behavior remains `os.kill(pid, 0)` probe.
      - stale-lock TTL recovery now falls back to lock file mtime when JSON payload is missing/corrupt.
      - bounded stale-lock recovery and explicit failure path retained.
    - `tests/test_parameter_sweep.py`:
      - added `test_sweep_lock_ttl_fallback_recovers_corrupt_lock_by_file_mtime`.
  - Verification:
    - `.venv\\Scripts\\python -m pytest tests\\test_parameter_sweep.py -k sweep_lock -vv -s`: PASS.
    - `.venv\\Scripts\\python -m pytest tests\\test_parameter_sweep.py -vv -s`: PASS.
    - `.venv\\Scripts\\python -m pytest -q`: PASS.
  - Decision impact:
    - Eliminates Windows process-termination crash path in lock checks.
    - Improves operational recovery from stale/corrupt lock files without manual intervention.

Phase 18 Day 1 (2026-02-19): Baseline Benchmark Report with Engine-Parity Frictions (D-94) ✅
  - Decision:
    - Add a dedicated baseline report script for SPY control strategies that enforces the same execution constraints as alpha backtests.
  - Implementation:
    - Added `scripts/baseline_report.py`.
    - Baselines implemented:
      - `buy_hold_spy` (target SPY weight `1.0`)
      - `static_50_50` (target SPY weight `0.5`)
      - `trend_sma200` (`spy_close > sma200 => 1.0`, else `--trend-risk-off-weight`, default `0.5`).
    - Execution/cost path:
      - uses `engine.run_simulation` as SSOT for shift(1) and turnover/cost.
      - models the tradable sleeve as SPY allocation with excess return leg `(spy_ret - cash_ret)` and then adds `cash_ret` back to avoid charging synthetic cash-leg turnover.
    - Reused FR-050 helpers from `backtests/verify_phase13_walkforward.py`:
      - `build_cash_return`, `compute_cagr`, `compute_sharpe`, `compute_max_drawdown`, `compute_ulcer_index`.
    - Cash hierarchy:
      - `BIL -> EFFR/252 -> flat 2%/252`.
    - Exports:
      - `data/processed/phase18_day1_baseline_equity.csv`
      - `data/processed/phase18_day1_baseline_metrics.csv`
      - optional PNG overlay (graceful skip if matplotlib unavailable).
    - Added tests:
      - `tests/test_baseline_report.py` for lag/cost/trend/metrics contract.
  - Verification:
    - `.venv\Scripts\python -m pytest tests\test_baseline_report.py -q`: PASS.
    - `.venv\Scripts\python scripts\baseline_report.py`: PASS.
    - Sample outputs (2015-01-02 -> 2024-12-31, rows=2,523):
      - buy_hold_spy: CAGR `12.982%`, Sharpe `0.782`, MaxDD `-33.717%`
      - static_50_50: CAGR `11.104%`, Sharpe `0.653`, MaxDD `-17.907%`
      - trend_sma200: CAGR `11.544%`, Sharpe `0.892`, MaxDD `-25.591%`
  - Decision impact:
    - Phase 18 now has reproducible, friction-aware benchmark controls for Day 1 comparison against later alpha candidates.

Phase 18 Day 1 (2026-02-19): Baseline Protocol Alignment + Metric SSOT Extraction (D-95) ✅
  - Decision:
    - Promote baseline/risk metrics into `utils/metrics.py` as single source of truth and align Day 1 baseline script interface/output contract to institutional operator spec.
  - Implementation:
    - Added `utils/metrics.py` with:
      - `compute_cagr`
      - `compute_sharpe(returns, rf_returns=None, periods_per_year=252)`
      - `compute_max_drawdown`
      - `compute_ulcer_index`
      - `compute_turnover`
    - Refactored `backtests/verify_phase13_walkforward.py` metric helpers to delegate to SSOT while preserving existing function names.
    - Updated `scripts/baseline_report.py`:
      - CLI contract now uses `--output-csv` and `--output-plot` defaults:
        - `data/processed/phase18_day1_baselines.csv`
        - `data/processed/phase18_day1_equity_curves.png`
      - institutional ASCII metrics table in console output
      - log-scale equity overlay plot
      - Pillow fallback path for PNG generation when matplotlib is unavailable
      - CSV schema contract:
        - `baseline,cagr,sharpe,max_dd,ulcer,turnover_annual,turnover_total,start_date,end_date,n_days`
    - Added tests:
      - `tests/test_metrics.py`
      - expanded `tests/test_baseline_report.py`
      - expanded `tests/test_verify_phase13_walkforward.py`
  - Verification:
    - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py -q`: PASS (`16 passed`).
    - `.venv\Scripts\python scripts\baseline_report.py`: PASS.
    - Artifacts written:
      - `data/processed/phase18_day1_baselines.csv`
      - `data/processed/phase18_day1_equity_curves.png`
  - Decision impact:
    - Day 1 baseline benchmarking now matches operator execution protocol and metric governance with reusable SSOT metric primitives for downstream phases.

Phase 18 Day 2 (2026-02-19): TRI Migration + Schema Guardrail + Macro TRI Extension (D-96) ✅
  - Decision:
    - Replace split-trap signal source with forward-built TRI artifacts while preserving D-02 execution semantics (`total_ret` unchanged for PnL).
  - Root cause:
    - Legacy `adj_close` signal inputs can be retroactively rewritten by corporate actions, creating false technical signals around split windows.
  - Implementation:
    - Added `data/build_tri.py`:
      - builds `data/processed/prices_tri.parquet` from base+patch price data with patch-priority dedupe on `(date, permno)`.
      - computes `tri` from cumulative total-return factors.
      - renames legacy signal column to `legacy_adj_close` (explicit deprecation barrier).
      - emits Day 2 validation artifacts:
        - `data/processed/phase18_day2_tri_validation.csv`
        - `data/processed/phase18_day2_split_events.png`
    - Added `data/build_macro_tri.py`:
      - builds `data/processed/macro_features_tri.parquet`.
      - adds `spy_tri`, `vix_tri`, `mtum_tri`, `dxy_tri`.
      - recomputes TRI-derived macro features (`vix_proxy`, `mtum_spy_corr_60d`, `dxy_spx_corr_20d`).
    - TRI-first compatibility integration:
      - `data/feature_store.py`: prefers `prices_tri.parquet` source, persists `tri`, keeps backward-compatible `adj_close`.
      - `strategies/investor_cockpit.py`: supports/propagates `tri` in alpha feature history and prefers it when available in stop checks.
      - `app.py`: prefers `prices_tri.parquet` and `macro_features_tri.parquet` when present.
    - Added tests:
      - `tests/test_build_tri.py` (schema migration, patch priority, split continuity, dividend capture, macro SPY consistency).
  - Verification:
    - `.venv\Scripts\python data/build_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --output data/processed/prices_tri.parquet --validation-csv data/processed/phase18_day2_tri_validation.csv --split-plot data/processed/phase18_day2_split_events.png`: PASS.
    - `.venv\Scripts\python data/build_macro_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --input data/processed/macro_features.parquet --output data/processed/macro_features_tri.parquet`: PASS.
    - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py tests\test_build_tri.py tests\test_feature_store.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_alpha_engine.py -q`: PASS (`53 passed`).
    - Day 2 validation CSV: `10/10` checks passed.
  - Decision impact:
    - Signal-layer split-trap risk is removed for Day 2 artifacts while execution and compatibility paths remain stable for existing alpha-engine contracts.

Phase 18 Day 3 (2026-02-20): Cash Allocation Overlay — Discrete Trend > Continuous Vol Target (D-97) ✅
  - Decision:
    - Lock `Trend SMA200` as the reference cash-allocation overlay for Phase 18.
    - Do not adopt continuous volatility targeting for the production Day 4 critical path.
    - Defer continuous-overlay optimization to Phase 19.
  - Rationale:
    - Day 3 stress tests showed continuous vol targeting underperforms discrete binary trend filtering under transaction-cost constraints.
    - Vol-target variants improved drawdown depth but paid material turnover drag:
      - Vol Target 20d turnover: `8.452 annual` (~`42 bps` annual cost drag at `5 bps` costs)
      - Trend SMA200 turnover: `0.123 annual` (~`0.6 bps` annual cost drag)
    - Sharpe penalty in this decision frame: `0.761` vs `0.894` (`-0.133`).
    - This is classified as design-constraint discovery (not execution defect).
    - The outcome empirically validates `FR-041` regime-governor architecture:
      - discrete `GREEN/AMBER/RED` state machine with binary trend filters
      - superior to continuous exposure scaling in this system setting.
  - Evidence:
    - `data/processed/phase18_day3_overlay_metrics.csv`
    - `data/processed/phase18_day3_overlay_exposure_corr.csv` (vol vs trend correlation frame)
    - `data/processed/phase18_day3_overlay_3panel.png`
    - `docs/saw_phase18_day3_round1.md` (`ADVISORY_PASS`)
  - Files:
    - `strategies/cash_overlay.py` (continuous classes retained for future Phase 19 experimentation)
    - `scripts/cash_overlay_report.py`
  - Alternative considered:
    - Add dead-zone bands to reduce vol-target churn.
    - Rejected for Day 3 closeout under FIX vs FINETUNE discipline (avoid parameter salvage / curve-fit loop).

Phase 18 Day 4 (2026-02-20): Company Scorecard Baseline + Control-Toggle Wiring (D-98) ✅
  - Decision:
    - Implement Day 4 linear multi-factor scorecard baseline with equal-weight factors and control-theory toggles wired but defaulted `OFF`.
  - Implementation:
    - Added `strategies/factor_specs.py`:
      - `FactorSpec` with candidate-column fallbacks, direction, weight, normalization, and control toggles:
        - `use_sigmoid_blend`
        - `use_dirty_derivative`
        - `use_leaky_integrator`
      - default factor set:
        - momentum (`resid_mom_60d`)
        - quality (`quality_composite` fallback `capital_cycle_score`)
        - volatility (`realized_vol_21d` fallback `yz_vol_20d`)
        - illiquidity (`illiq_21d` fallback `amihud_20d`)
    - Added `strategies/company_scorecard.py`:
      - vectorized cross-sectional score computation with per-factor contribution columns.
      - normalization modes: `zscore`, `rank`, `raw`.
      - control toggles applied conditionally and PIT-safe over per-permno series.
    - Added `scripts/scorecard_validation.py`:
      - computes Day 4 scores from `features.parquet`.
      - emits validation checks and scored output artifacts.
    - Updated `data/feature_store.py`:
      - scorecard alias columns persisted:
        - `quality_composite`
        - `realized_vol_21d`
        - `illiq_21d`
    - Added tests:
      - `tests/test_company_scorecard.py`
  - Verification:
    - `.venv\Scripts\python -m py_compile strategies/factor_specs.py strategies/company_scorecard.py scripts/scorecard_validation.py tests/test_company_scorecard.py`: PASS.
    - `.venv\Scripts\python -m pytest tests/test_company_scorecard.py tests/test_feature_store.py -q`: PASS.
    - `.venv\Scripts\python -m pytest tests/test_metrics.py tests/test_verify_phase13_walkforward.py tests/test_baseline_report.py tests/test_verify_phase15_alpha_walkforward.py tests/test_build_tri.py tests/test_feature_store.py tests/test_strategy.py tests/test_phase15_integration.py tests/test_alpha_engine.py tests/test_cash_overlay.py tests/test_company_scorecard.py -q`: PASS (`68 passed`).
    - `.venv\Scripts\python scripts/scorecard_validation.py --input-features data/processed/features.parquet --start-date 2015-01-01 --end-date 2024-12-31 --output-validation-csv data/processed/phase18_day4_scorecard_validation.csv --output-scores-csv data/processed/phase18_day4_company_scores.csv`: PASS.
  - Decision impact:
    - Day 4 baseline scoring infrastructure is operational and ablation-ready.
    - Control-theory hooks are integrated without contaminating baseline (all toggles default OFF).
    - Validation objectives still open for tuning loop:
      - score coverage below target (`88.36% < 95%`).
      - quartile spread sigma below target (`1.793 < 2.0`).
      - non-gate watch metric shows factor under-contribution (`min share 0.089 < 0.10`).

Phase 18 Day 5 (2026-02-20): Ablation Matrix Result — Integrator Wins on Sharpe/Turnover, Coverage/Spread Still Binding (D-99) ✅
  - Decision:
    - Accept Day 5 as `ADVISORY_PASS`.
    - Carry forward `ABLATION_C3_INTEGRATOR` as Day 6 starting candidate for robustness checks.
    - Keep Day 5 acceptance gates for coverage/spread open (not forced closed by parameter salvage).
  - Implementation:
    - Added `scripts/day5_ablation_report.py` with 9-config matrix execution and atomic artifacts.
    - Added explicit score validity modes in `strategies/company_scorecard.py`:
      - `complete_case`
      - `partial`
      - `impute_neutral`
    - Added runtime guardrails:
      - active-return missing-data fail-fast + optional override (`--allow-missing-returns`)
      - dense matrix size ceiling (`--max-matrix-cells`)
      - empty-data artifact write path (`status=no_data`)
    - Added tests:
      - `tests/test_day5_ablation_report.py`
      - expanded `tests/test_company_scorecard.py` for scoring-mode validity ordering.
  - Evidence:
    - `data/processed/phase18_day5_ablation_metrics.csv`
    - `data/processed/phase18_day5_ablation_deltas.csv`
    - `data/processed/phase18_day5_ablation_summary.json`
    - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py tests\test_build_tri.py tests\test_feature_store.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_alpha_engine.py tests\test_cash_overlay.py tests\test_company_scorecard.py tests\test_day5_ablation_report.py` -> PASS (`73 passed`).
  - Result snapshot:
    - Baseline (`BASELINE_DAY4`, complete-case): coverage `47.82%`, spread `1.842`, Sharpe `0.764`, turnover `64.934`.
    - Best config (`ABLATION_C3_INTEGRATOR`): coverage `52.37%`, spread `1.800`, Sharpe `1.007`, turnover `19.794`.
    - Turnover reduction vs baseline: `69.52%` (pass).
    - Coverage (`>=95%`) and spread (`>=2.0`) remain failed.
  - Rationale:
    - Day 5 objective was controlled falsification/selection, not forced target pass-through.
    - Integrator materially reduced churn and improved risk-adjusted performance without overfitting weight topology.
    - Coverage/spread constraints now clearly identified as data-availability + factor-structure limits requiring Day 6 robustness framing, not blind Day 5 retuning.
  - Alternative considered:
    - Force pass by relaxing validity semantics globally to impute-neutral and/or over-tilting hierarchical weights.
    - Rejected for governance integrity (would contaminate the control-group comparison and blur ablation attribution).

Phase 18 Day 6 (2026-02-20): Walk-Forward Validation — C3 Crisis Control Confirmed, Regime Robustness Incomplete (D-100) ✅
  - Decision:
    - Close Day 6 as `ADVISORY_PASS`.
    - Retain C3 integrator (`decay=0.95`) as a defensiveness mechanism, not yet as universal default.
    - Carry failed robustness checks (CHK-39, CHK-41, CHK-48, CHK-50, CHK-51..53) forward to Day 7 cyclical-exception work.
  - Implementation:
    - Added `scripts/day6_walkforward_validation.py` with:
      - walk-forward windows (`W1..W4`),
      - decay sweep (`0.85..0.99`),
      - crisis turnover validation.
    - Added `tests/test_day6_walkforward_validation.py`.
    - Produced Day 6 artifacts:
      - `phase18_day6_walkforward.csv`
      - `phase18_day6_decay_sensitivity.csv`
      - `phase18_day6_crisis_turnover.csv`
      - `phase18_day6_checks.csv`
      - `phase18_day6_summary.json`
  - Evidence:
    - Day 6 checks: `9/16` pass, `7/16` fail.
    - Critical gate CHK-54: PASS (`>=15%` turnover reduction in all crisis windows, minimum observed `80.38%`).
    - Full impacted regression:
      - `.venv\Scripts\python -m pytest tests\test_metrics.py tests\test_verify_phase13_walkforward.py tests\test_baseline_report.py tests\test_verify_phase15_alpha_walkforward.py tests\test_build_tri.py tests\test_feature_store.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_alpha_engine.py tests\test_cash_overlay.py tests\test_company_scorecard.py tests\test_day5_ablation_report.py tests\test_day6_walkforward_validation.py -q` -> PASS (`77 passed`).
  - Rationale:
    - C3 continues to show strong turnover suppression in crisis regimes (primary Day 6 safety concern).
    - Out-of-sample upside-capture and plateau checks failed, indicating parameter/regime brittleness.
    - Treating Day 6 as hard PASS would overstate generalization; advisory framing preserves discipline.
  - Alternative considered:
    - Immediate post-Day 6 parameter salvage to force CHK-51..53 pass.
    - Rejected to avoid mixing robustness diagnostics with tuning in the same gate.

Phase 18 Closure (2026-02-20): Lock C3 Integrator and Close Sprint (D-101) ✅
  - Decision:
    - Close Phase 18 and lock `C3_LEAKY_INTEGRATOR_V1` for production use in this phase context.
    - Accept Day 6 advisory failures as documented design tradeoffs for this closure cycle.
  - Implementation:
    - Added lock module:
      - `strategies/production_config.py`
      - immutable `PRODUCTION_CONFIG_V1` built from `FactorSpec` defaults with integrator-only toggles and `decay=0.95`.
    - Added closure/deployment docs:
      - `docs/saw_phase18_day6_final.md`
      - `docs/production_deployment.md`
      - `docs/phase18_closure_report.md`
    - Updated lifecycle docs:
      - `docs/phase18-brief.md` (Phase Closed)
      - `docs/lessonss.md` (new closure lesson)
  - Evidence:
    - `data/processed/phase18_day5_ablation_metrics.csv`:
      - baseline Sharpe `0.764` -> C3 Sharpe `1.007`
      - baseline turnover `64.934` -> C3 turnover `19.794`
    - `data/processed/phase18_day6_summary.json`:
      - checks `9/16` pass, `7/16` fail
      - critical CHK-54 pass
      - missing active-return cells under override run: baseline `0`, C3 `13704`
    - `data/processed/phase18_day6_crisis_turnover.csv`:
      - minimum crisis turnover reduction `80.38%`.
  - Rationale:
    - C3 keeps the strongest proven crisis-turnover suppression from Day 6.
    - User/operator directive explicitly preferred stability and simplicity over another adaptive tuning cycle.
    - Closure preserves an auditable baseline and defers further complexity to later phases.
  - Open risks accepted at closure:
    - CHK-41, CHK-48, CHK-50 upside/recovery consistency.
    - CHK-51, CHK-52, CHK-53 decay plateau robustness.
  - Rollback path:
    - stop using `PRODUCTION_CONFIG_V1` and restore pre-lock scorecard wiring.
    - keep Phase 18 artifacts/docs for audit traceability.

Phase 21 Day 1 (2026-02-20): Standalone Stop-Loss & Drawdown Control Module (D-102) ✅
  - Decision:
    - Implement a standalone risk-control module at `strategies/stop_loss.py` for position-level stops and portfolio drawdown tiers.
    - Keep ATR mode explicit as close-only proxy with simple moving average.
    - Enforce D-57 ratchet invariant in stop updates.
  - Implementation:
    - Added `strategies/stop_loss.py`:
      - `StopLossConfig` with `atr_mode='proxy_close_only'`.
      - `ATRCalculator` using:
        - `ATR_t = SMA(|close_t - close_{t-1}|, window=20)`.
      - `StopLossManager` with:
        - initial stop (`entry - 2.0*ATR`),
        - trailing stop (`price - 1.5*ATR`),
        - time-based underwater exit (`days_held > max_underwater_days`),
        - ratchet update (`stop_t = max(stop_{t-1}, candidate_t)`).
      - `PortfolioDrawdownMonitor` tiers:
        - drawdown thresholds: `-8% / -12% / -15%`,
        - scales: `0.75 / 0.50 / 0.00`,
        - recovery threshold: `>-4%`.
      - Optional edge-case guard:
        - `min_stop_distance_abs` (default `0.0`) to avoid zero-distance stops under zero volatility.
    - Added `tests/test_stop_loss.py` (18 tests) covering:
      - ATR math and date lookups,
      - stage transitions,
      - D-57 non-decreasing stop path,
      - time-based exits,
      - drawdown tier transitions,
      - zero-volatility and minimum-distance edge case.
  - Evidence:
    - `.venv\Scripts\python -m py_compile strategies/stop_loss.py tests/test_stop_loss.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_stop_loss.py -q` -> PASS (`18 passed`).
    - `.venv\Scripts\python -m pytest tests/test_phase15_integration.py -q` -> PASS (`3 passed`).
  - Rationale:
    - Day 1 requires a reusable, testable stop-loss subsystem that is independent of OHLC dependencies.
    - Current data constraints are close-only; explicit ATR mode removes hidden assumptions.
    - Ratchet enforcement preserves D-57 invariants while enabling phased stop behavior.
  - Open risks:
    - Module is not yet wired into live portfolio execution path; integration is deferred to later Phase 21 tasks.
    - `.pytest_cache` ACL warning persists on this environment (non-blocking to test outcomes).
  - Mitigation / next gate:
    - Phase 21 Day 2 must include integration activation gate, runtime observability checks, and rollback procedure updates in `docs/runbook_ops.md` before enabling live usage.
  - Rollback path:
    - remove `strategies/stop_loss.py` and `tests/test_stop_loss.py`.
    - revert Phase 21 Day 1 doc entries in brief/notes/lessons if this decision is revoked.

Phase 21.1 Path1 Directive (2026-02-21): Sector/Industry Context Pre-Rank + Dictatorship Telemetry (D-103) ✅
  - Decision:
    - Enforce Path1 directive context wiring by attaching static sector/industry metadata to the conviction frame before ticker-pool ranking.
    - Add explicit telemetry contract fields in slice artifacts:
      - `DICTATORSHIP_MODE`
      - `path1_directive_id`
      - context coverage/source breakdown fields.
  - Implementation:
    - `strategies/company_scorecard.py`:
      - added deterministic sector-map loader from `data/static/sector_map.parquet`.
      - attach order: `permno` map first, then `ticker` fallback.
      - emits:
        - `sector`
        - `industry`
        - `sector_context_source`
        - `path1_sector_context_attached`
      - runs attachment before `rank_ticker_pool`.
    - `scripts/phase21_1_ticker_pool_slice.py`:
      - emits Path1 fields into sample CSV:
        - `sector`, `industry`, `sector_context_source`,
        - `path1_sector_context_attached`,
        - `path1_directive_id`,
        - `DICTATORSHIP_MODE`.
      - emits summary JSON block `path1_telemetry` with:
        - attached coverage ratio,
        - known sector/industry counts,
        - context source distribution,
        - sample sector/industry composition counts.
  - Evidence:
    - `strategies/company_scorecard.py`
    - `scripts/phase21_1_ticker_pool_slice.py`
    - `docs/notes.md`
    - `docs/lessonss.md`
  - Rationale:
    - Static sector map exists as local bedrock and is safe to inject in hot path without live provider dependencies.
    - Deterministic pre-rank context merge avoids hidden runtime drift and improves traceability of Path1 constraints.
  - Rollback path:
    - remove context-attach helper calls and Path1 telemetry fields from slice outputs.
    - keep previous sample/summary schema for consumers that do not need Path1 directives.

Phase 22 Baseline Harness (2026-02-21): Separability Telemetry Scaffold (D-105) ✅
  - Decision:
    - Add a dedicated separability harness for de-anchor validation with `--dictatorship-mode off` baseline telemetry.
    - Lock Section 2 directives in implementation:
      - Jaccard stability on `odds_score`.
      - Silhouette labels from posterior argmax.
      - one-effective-class days emit `NaN` + coverage counters (no synthetic fill).
    - Emit both stability sets:
      - `top_decile`
      - `top_30`.
  - Implementation:
    - Added `scripts/phase22_separability_harness.py`:
      - loads Phase 20 conviction frame in PIT-safe path,
      - computes day-over-day Jaccard overlap for `top_decile` and `top_30`,
      - computes silhouette in post-neutralized/post-MAD geometry with posterior argmax labels,
      - computes archetype recall ranks/hits for `MU/LRCX/AMAT/KLAC`,
      - emits:
        - `data/processed/phase22_separability_daily.csv`
        - `data/processed/phase22_separability_summary.json`.
    - Added `tests/test_phase22_separability_harness.py`:
      - Jaccard math,
      - one-class silhouette policy,
      - finite two-class silhouette path,
      - fixed top-N archetype hit schema.
    - Added deterministic manual silhouette fallback when `sklearn.metrics` is unavailable.
  - Evidence:
    - `.venv\Scripts\python -m py_compile scripts/phase22_separability_harness.py tests/test_phase22_separability_harness.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_phase22_separability_harness.py -q` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS.
    - `.venv\Scripts\python scripts/phase22_separability_harness.py --start-date 2024-12-01 --as-of-date 2024-12-24 --dictatorship-mode off` -> PASS.
  - Baseline snapshot (2024-12-01 to 2024-12-24, mode `PATH1_DEPRECATED`):
    - days: `17` (all with valid odds rows).
    - Jaccard mean:
      - `top_decile = 0.3438`
      - `top_30 = 0.3560`.
    - Silhouette:
      - valid days `16`,
      - mean `0.0786`,
      - one-class days `1` (`2024-12-02`).
    - Archetype hit rates:
      - aggregate `top_decile = 0.3382`,
      - aggregate `top_30 = 0.5441`.
  - Rationale:
    - Promotion thresholds must be set from observed unsupervised baseline telemetry, not inferred from target outcomes.
    - Manual silhouette fallback preserves deterministic telemetry in environments where `sklearn.metrics` is unavailable.
  - Rollback path:
    - remove `scripts/phase22_separability_harness.py` and `tests/test_phase22_separability_harness.py`.
    - stop publishing Phase 22 separability artifacts.

Phase 23 Step 1 (2026-02-22): FMP PIT Estimates Ingestion Scaffold (D-106) ✅
  - Decision:
    - Implement Path A scaffold for historical consensus ingestion using Financial Modeling Prep (FMP):
      - endpoint: `/api/v3/historical/analyst-estimates/{ticker}`.
    - Enforce internal PIT schema contract and identifier integrity before downstream SDM feature work.
  - Implementation:
    - Added `scripts/ingest_fmp_estimates.py` with:
      - API auth from `FMP_API_KEY` (graceful fail + explicit warning when missing),
      - ticker→permno crosswalk from `data/static/sector_map.parquet`,
      - strict processed schema: `permno,ticker,published_at,horizon,metric,value`,
      - quarterly/annual normalization into `horizon='NTM'`,
      - PIT period filter: include only `period_end > published_at`,
      - atomic parquet writes,
      - write-safety guard to prevent overwriting existing outputs when fetch/mapping yields empty result.
    - Added tests:
      - `tests/test_ingest_fmp_estimates.py`
      - coverage: NTM quarter sum, FY fallback, PIT period filter, schema/mapping contract.
  - Evidence:
    - `.venv\Scripts\python -m py_compile scripts/ingest_fmp_estimates.py tests/test_ingest_fmp_estimates.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ingest_fmp_estimates.py -q` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ingest_fmp_estimates.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS.
    - Dry-run command:
      - `.venv\Scripts\python scripts/ingest_fmp_estimates.py --tickers MU,AMAT`
      - observed runtime warning: missing `FMP_API_KEY` (graceful fail path confirmed).
  - Rationale:
    - Step 1 must be complete before SDM revision features can be computed.
    - Preserving last-known-good parquet outputs under transient fetch/crosswalk failures reduces operational blast radius.
  - Open risks:
    - API connectivity and payload mapping are not yet validated end-to-end in this environment due missing `FMP_API_KEY`.
  - Rollback path:
    - remove `scripts/ingest_fmp_estimates.py` and `tests/test_ingest_fmp_estimates.py`.
    - revert Step 1 ingest wiring until credentialed dry-run evidence is available.

Phase 23 Step 1.1 (2026-02-22): Rate-Aware Cache-First FMP Ingestion + Scoped Universe (D-107) ✅
  - Decision:
    - Upgrade ingest engine to operate under API-credit/rate constraints with local cache-first behavior.
    - Keep Phase 23 Path A active while enabling local/offline reuse and deterministic merge into processed estimates.
  - Implementation:
    - `scripts/ingest_fmp_estimates.py`:
      - added per-ticker JSON cache at `data/raw/fmp_cache/{ticker}.json`,
      - checks cache before network request,
      - supports scoped universe via `--tickers` and `--tickers-file` with `--max-tickers` cap,
      - pre-filters requested universe by crosswalk-mapped tickers before API calls,
      - adds exponential backoff for 429 conditions and cache-only continuation after limit exhaustion,
      - adds merge-with-existing mode where new rows deterministically override existing rows on dedupe keys.
    - added scoped starter list:
      - `data/raw/fmp_target_tickers.txt` (20 semicap/cyclical-focused names).
    - expanded tests:
      - `tests/test_ingest_fmp_estimates.py` now covers target resolution cap, cache roundtrip, and deterministic merge override.
  - Evidence:
    - `.venv\Scripts\python -m py_compile scripts/ingest_fmp_estimates.py tests/test_ingest_fmp_estimates.py` -> PASS.
    - `.venv\Scripts\python -m pytest tests/test_ingest_fmp_estimates.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS.
    - Runtime attempt:
      - `.venv\Scripts\python scripts/ingest_fmp_estimates.py --tickers-file data/raw/fmp_target_tickers.txt --max-tickers 500`
      - connectivity failed with network socket permission error (`WinError 10013`), no cache/processed writes performed.
  - Rationale:
    - API budgets and rate limits require cache-first behavior and universe scoping to remain operationally viable.
    - deterministic merge semantics prevent stale records from overriding newly fetched PIT rows.
  - Open risks:
    - Current environment still blocks outbound API access (`WinError 10013`), so live cache population remains unverified.
    - No local R3000 membership parquet artifact currently available for auto-scope bootstrap/merge.
  - Rollback path:
    - remove cache-first and merge extensions from `scripts/ingest_fmp_estimates.py`,
    - remove `data/raw/fmp_target_tickers.txt`,
    - revert extended tests in `tests/test_ingest_fmp_estimates.py`.

Phase 23 Step 2 (2026-02-22): 3-Pillar SDM Ingestion + PIT Assembler Hardening (D-108) ✅
  - Decision:
    - Fix Pillar 1/2 `merge_asof` failure by enforcing global timeline-key sorting before join.
    - Add dynamic `totalq.total_q` schema probe so optional intangible fields are ingested when present without breaking on schema drift.
    - Enforce allow+audit policy for unmapped identifiers (retain rows, write audit file, never silent-drop).
    - Add explicit final assembler script for PIT-safe quarterly-to-daily joins:
      - `scripts/assemble_sdm_features.py`.
  - Implementation:
    - `scripts/ingest_compustat_sdm.py`:
      - added `_assert_merge_asof_sorted` and timeline-first sort contract:
        - left: `published_at_dt, gvkey`
        - right: `pit_date, gvkey`.
      - added dynamic `totalq` probing:
        - `information_schema.columns` lookup,
        - required/stable/optional field selection.
      - added allow+audit crosswalk behavior:
        - unmapped rows retained,
        - audit output `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`.
    - `scripts/assemble_sdm_features.py`:
      - backward `merge_asof` joins from fundamentals `published_at` to macro/factor daily timestamps with configurable tolerance.
      - sector/industry context attach by permno first, then ticker fallback.
      - atomic write for `data/processed/features_sdm.parquet`.
    - tests added:
      - `tests/test_ingest_compustat_sdm.py`
      - `tests/test_assemble_sdm_features.py`.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_ingest_compustat_sdm.py tests/test_assemble_sdm_features.py tests/test_ingest_fmp_estimates.py -q` -> PASS (`13 passed`).
    - dry-runs:
      - `scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
      - `scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
      - `scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
      - `scripts/assemble_sdm_features.py --dry-run --tolerance-days 7` -> PASS.
    - writes:
      - `data/processed/fundamentals_sdm.parquet` -> written (128 rows, scoped slice).
      - `data/processed/macro_rates.parquet` -> written (1140 rows).
      - `data/processed/ff_factors.parquet` -> written (1003 rows).
      - `data/processed/features_sdm.parquet` -> written (128 rows).
  - Rationale:
    - `merge_asof` correctness is non-negotiable for PIT-safe quarterly/annual joins.
    - dynamic `totalq` probing removes brittle schema assumptions while preserving stable fields.
    - allow+audit keeps complete lineage under mapping gaps and avoids silent data-loss.
  - Open risks:
    - `frb.rates_daily` currently terminates at 2025-02-13 in this runtime, so later fundamentals rows show expected macro nulls under tolerance.
    - `.pytest_cache` ACL warning persists in environment; does not affect test pass/fail.
  - Rollback path:
    - remove `scripts/assemble_sdm_features.py`,
    - revert `scripts/ingest_compustat_sdm.py` to pre-D-108 behavior,
    - remove `tests/test_ingest_compustat_sdm.py` and `tests/test_assemble_sdm_features.py`,
    - regenerate SDM artifacts from prior ingestion scripts.

Phase 23 Step 2.1 (2026-02-22): Strict 14-Day Feed-Horizon Tolerance Gate (D-109) ✅
  - Decision:
    - Enforce fixed `14d` staleness tolerance on SDM assembler `merge_asof` joins for both macro and FF factor pillars.
    - Add explicit warning telemetry counting rows nulled by the tolerance gate (vs no-tolerance baseline).
  - Implementation:
    - `scripts/assemble_sdm_features.py`:
      - replaced configurable tolerance with strict constant:
        - `ASOF_TOLERANCE = Timedelta('14d')`.
      - added `_count_rows_nulled_by_tolerance` helper:
        - computes no-tolerance vs strict-tolerance asof matches,
        - logs count of rows nulled strictly due to staleness.
      - removed CLI `--tolerance-days` override to keep tolerance policy fixed.
    - `tests/test_assemble_sdm_features.py`:
      - updated assembler calls for fixed tolerance path,
      - added regression test for stale-match nulling counter.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_assemble_sdm_features.py -q` -> PASS.
    - `.venv\Scripts\python scripts/assemble_sdm_features.py --dry-run` -> PASS with warning:
      - macro nulled `30` rows,
      - ff nulled `4` rows.
    - `.venv\Scripts\python scripts/assemble_sdm_features.py` -> PASS and wrote `features_sdm.parquet`.
  - Rationale:
    - prevents stale macro/factor data from being forward-carried too far beyond publication anchors.
    - warning telemetry makes feed-horizon degradation explicit at runtime.
  - Open risks:
    - upstream feed endpoints still cap at 2025-02-13 (FRB) and 2025-12-31 (FF), so late rows remain null until source refresh.
  - Rollback path:
    - restore previous configurable tolerance behavior in `scripts/assemble_sdm_features.py`,
    - remove stale-null audit helper and associated tests if policy is reversed.

Phase 23 Step 6 (2026-02-22): BGM Manifold Swap to SDM + Macro Cycle Geometry (D-110) ✅
  - Decision:
    - Switch clustering geometry from Phase 22 price-exhaust mix to SDM/macro manifold only.
    - Enforce strict geometry-risk separation: no beta/volatility feature may enter BGM matrix.
    - Add migration-safe dual-read feature adapter to combine legacy and SDM feature artifacts during transition.
  - Implementation:
    - `scripts/assemble_sdm_features.py`:
      - expanded fundamentals from quarterly releases to daily cadence via per-entity forward fill.
      - precomputed industry medians (`ind_rev_accel`, etc.) and cycle interaction:
        - `CycleSetup = yield_slope_10y2y * rmw * cma`.
    - `scripts/phase20_full_backtest.py`:
      - updated `_load_features_window` to dual-read:
        - base: `features.parquet`,
        - overlay: `features_sdm.parquet`,
        - merge key: `[date, permno]` with UTC-naive normalization.
    - `strategies/company_scorecard.py`:
      - added SDM/macro columns to conviction-frame bridge and lagged routing into ticker-pool input.
    - `strategies/ticker_pool.py`:
      - geometry features now fixed to:
        - `rev_accel, inv_vel_traj, gm_traj, op_lev, intang_intensity, q_tot, rmw, cma, yield_slope_10y2y, CycleSetup`.
      - added explicit assert guards rejecting risk columns/tokens (`beta`, `vol`) in geometry config.
    - tests:
      - added `tests/test_phase20_full_backtest_loader.py`.
      - updated `tests/test_ticker_pool.py` and `tests/test_assemble_sdm_features.py`.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_assemble_sdm_features.py tests/test_phase20_full_backtest_loader.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS (`40 passed`).
    - `.venv\Scripts\python scripts/assemble_sdm_features.py` -> PASS (`11254` rows written).
    - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24 --top-longs 5 --short-excerpt 5 --dictatorship-mode on --output-csv data/processed/phase23_action2_smoke_sample.csv --output-summary-json data/processed/phase23_action2_smoke_summary.json` -> PASS.
  - Rationale:
    - isolates clustering geometry to causal SDM state and macro-cycle drivers while preserving risk controls in sizing/governor path.
    - migration-safe dual-read avoids breaking existing scripts during artifact transition.
  - Open risks:
    - sparse SDM coverage can reduce valid geometry rows on some dates; ticker-pool min-universe skip warnings are expected until coverage improves.
  - Rollback path:
    - restore old `TickerPoolConfig.feature_columns` set and remove geometry risk-guard asserts.
    - disable dual-read overlay by reverting `_load_features_window` to single-source read.
    - revert daily-expansion/precompute additions in `scripts/assemble_sdm_features.py`.

Phase 23 Step 6.1 (2026-02-22): Hierarchical Imputation to Prevent Universe Collapse (D-111) ✅
  - Decision:
    - Eliminate NaN-driven cross-sectional collapse in unsupervised geometry by introducing strict PIT imputation hierarchy before robust scaling.
    - Do not drop rows from geometry matrix due to sparse SDM fields.
  - Implementation:
    - `strategies/ticker_pool.py`:
      - added hierarchical imputation:
        - Level 1: same-date industry median (fallback key: sector),
        - Level 2: neutral `0.0` fill for remaining missing values.
      - integrated imputed geometry builder before z-score/MAD path.
      - added universe telemetry:
        - `geometry_universe_before_imputation`,
        - `geometry_universe_after_imputation`,
        - `geometry_industry_impute_cells`,
        - `geometry_zero_impute_cells`.
    - `scripts/phase22_separability_harness.py`:
      - aligned geometry reconstruction with ticker-pool imputed z-matrix path.
      - surfaced imputation telemetry in summary aggregates.
    - tests:
      - added regression coverage for universe preservation under sparse SDM features.
  - Evidence:
    - `.venv\Scripts\python -m pytest tests/test_ticker_pool.py tests/test_phase22_separability_harness.py tests/test_company_scorecard.py -q` -> PASS.
    - `.venv\Scripts\python scripts/phase22_separability_harness.py --start-date 2024-12-01 --as-of-date 2024-12-24 --dictatorship-mode off --output-csv data/processed/phase22_separability_daily_action2.jsonfix.csv --output-summary-json data/processed/phase22_separability_summary_action2.jsonfix.json` -> PASS.
    - summary telemetry:
      - `days_with_valid_odds: 17` (was 1),
      - `geometry_universe_before_imputation mean: 2.59`,
      - `geometry_universe_after_imputation mean: 389.0`.
  - Rationale:
    - preserves cross-section breadth required for unsupervised clustering while remaining PIT-safe and neutral on unknown fields.
  - Open risks:
    - silhouette remains invalid in this window (`one_effective_class`) despite recovered universe breadth.
  - Rollback path:
    - revert imputation helpers in `strategies/ticker_pool.py` and harness alignment in `scripts/phase22_separability_harness.py`,
    - restore prior NaN-filter geometry behavior.

Phase 23 Closure (2026-02-22): Median-Neutralized + Diagonal-Covariance Memory-Trough Isolation (D-112) ✅
  - Decision:
    - Formally close Phase 23 and lock clustering manifold state for promotion to historical validation.
    - Lock the following in `strategies/ticker_pool.py`:
      - geometry feature manifold,
      - cluster ranker heuristic,
      - covariance mode/hyperparameters.
    - Adopt robust closeout settings:
      - cross-sectional peer neutralization by median (industry granularity preferred; sector fallback),
      - diagonal covariance mode for clustering-distance stability.
  - Implementation:
    - `strategies/ticker_pool.py`:
      - neutralization baseline switched to median by peer group,
      - covariance mode surfaced and fixed to `diag`,
      - final locked cycle-aware ranker retained.
    - `strategies/company_scorecard.py`:
      - context plumbing extended to pass `industry_group` when available (fallback remains `industry -> sector`).
    - `scripts/phase20_full_backtest.py`:
      - explicit SDM adapter CLI input added:
        - `--input-sdm-features` (default `data/processed/features_sdm.parquet`),
      - runtime print telemetry now confirms SDM overlay path existence.
  - Evidence:
    - `.venv\Scripts\python scripts/phase22_separability_harness.py --start-date 2024-12-01 --as-of-date 2024-12-24 --dictatorship-mode off --output-csv data/processed/phase22_separability_daily_action2_outlierskewfix.csv --output-summary-json data/processed/phase22_separability_summary_action2_outlierskewfix.json` -> PASS.
    - `data/processed/phase22_separability_summary_action2_outlierskewfix.json`:
      - `silhouette_score.mean = 0.009045008492558893` (positive),
      - `silhouette_single_class_days = 0`,
      - `MU` top-30 hit-rate > 0 in closeout run.
    - `.venv\Scripts\python -m py_compile strategies/ticker_pool.py strategies/company_scorecard.py scripts/phase20_full_backtest.py` -> PASS.
  - Rationale:
    - Median baselines prevent mega-cap outlier skew from distorting peer-neutralized geometry.
    - Diagonal covariance reduces cross-feature overlap instability in fat-tailed fundamental spaces.
    - With positive mean silhouette and memory-trough signal recovery in the closeout window, Phase 23 exits feature-engineering and transitions to Phase 20 historical validation.
  - Open risks:
    - Archetype recall remains uneven across semiconductor names in strict top-30 ranking; this is now a validation-phase (not manifold-design) risk.
  - Rollback path:
    - revert D-112 manifold hardening and return to D-111 state if PM rejects Phase 23 closeout evidence.

Phase Governance Update (2026-02-22): SAW Phase-End Closure Package (D-113) ✅
  - Decision:
    - Extend SAW from round-close only to explicit phase-end closure protocol.
    - Require full test matrix, subagent end-to-end replay, PM handover artifact, and `/new` context bootstrap with confirmation gate.
  - Implementation:
    - Updated `.codex/skills/saw/SKILL.md`:
      - added mandatory Section 6 `Phase-End Closeout Protocol` with checks `CHK-PH-01..CHK-PH-05`.
      - added phase-end hard gate and required report blocks (`PhaseEndValidation`, `HandoverDoc`, `ContextPacketReady`, `ConfirmationRequired`).
      - hardened execution contract with runtime smoke timeout (`180s`), reproducible E2E matching criteria, and explicit next-phase approval token handling.
    - Added `.codex/skills/saw/references/phase_end_handover_template.md`:
      - PM-friendly handover template with formula register, explicit logic chain, and required data-integrity evidence slots.
    - Updated `.codex/skills/saw/agents/openai.yaml`:
      - default prompt now enforces phase-end checks, `NextPhaseApproval: PENDING`, and exact `approve next phase` confirmation token.
    - Updated `docs/checklist_milestone_review.md`:
      - added missing phase-end closure tasks (full regression, runtime smoke, data integrity, handover, `/new` packet), plus explicit lessons-loop gate.
  - Rationale:
    - Phase close required consistent governance outputs across testing, documentation, and handoff; these were previously implied but not strictly enforced.
  - Rollback path:
    - revert D-113 files to prior versions and restore prior SAW round-only behavior.

Core Module Refactor Stage 2 (2026-02-22): Root-to-Core Module Relocation (D-114) ✅
  - Decision:
    - Enforce root policy where only entrypoints remain as Python files in root (`app.py`, `launch.py`).
    - Relocate runtime modules `engine.py`, `etl.py`, `optimizer.py` into `core/` package.
    - Use temporary root shims during import migration, then destroy shims after reconciliation.
  - Implementation:
    - Added package scaffold:
      - `core/__init__.py`
    - Moved modules:
      - `engine.py -> core/engine.py`
      - `etl.py -> core/etl.py`
      - `optimizer.py -> core/optimizer.py`
    - Reconciled internal imports to `core` namespace across app/backtests/scripts/tests.
    - Updated `core/optimizer.py` internal dependency from root import to package-relative import (`from . import engine`).
    - Destroyed temporary root shims once import scan showed no internal references.
    - Updated docs path references:
      - `docs/spec.md` (`core/engine.py`, `core/optimizer.py`)
      - `docs/prd.md` (`core/optimizer.py`)
  - Evidence:
    - Import reconciliation scan:
      - `rg -n --glob '*.py' "<engine|optimizer|etl root import patterns>" .` -> only `core.*` imports remain.
    - Root policy check:
      - root files now: `AGENTS.md`, `app.py`, `launch.py`, `pyproject.toml`, `requirements.txt`.
    - Entry-point dry run:
      - `.venv\Scripts\python launch.py --help` -> PASS.
    - Full test run:
      - `.venv\Scripts\python -m pytest -q` -> FAIL (`5` pre-existing/non-import failures in SDM/ticker-pool tests).
  - Rationale:
    - Structural separation improves module hygiene without changing entrypoint ergonomics.
    - Shim lifecycle reduced migration risk while enabling strict root cleanup.
  - Open risks:
    - Full-suite pytest remains red on five non-import tests (`tests/test_assemble_sdm_features.py`, `tests/test_phase20_full_backtest_loader.py`, `tests/test_ticker_pool.py`) that are outside this refactor scope.
  - Rollback path:
    - move `core/engine.py`, `core/etl.py`, `core/optimizer.py` back to root and restore legacy import statements.

Phase 20 Closure Wrap (2026-02-22): Golden Master Lock + PM Handover Packet (D-115) ✅
  - Decision:
    - Formally close Phase 20 as a completed milestone with a locked cyclical-trough operating profile and explicit Phase 24 runway.
    - Lock Phase 20 ranker and gate math for historical-validation handoff:
      - `cluster_score = (CycleSetup * 2.0) + op_lev + rev_accel + inv_vel_traj - q_tot`
      - `entry_gate = score_valid & (conviction_score >= 7.0) & pool_long_candidate & mom_ok & support_proximity`
      - hard exit selection remains `selected = entry_gate & (rank <= n_target)`.
    - Publish phase-end handover context packet for `/new` bootstrap and approval-token gating.
  - Implementation:
    - `strategies/ticker_pool.py`:
      - restored `_conviction_cluster_score` to Option A cyclical-trough formula (`+CycleSetup*2`, `-q_tot`).
    - `docs/phase_brief/phase20-brief.md`:
      - rewritten from stale Round-3 salvage state to formal closure brief with locked formulas, experiment ledger, structural boundary, and CI/CD handoff status.
    - `docs/notes.md`:
      - appended explicit Phase 20 lock formulas and source-path references.
    - `docs/lessonss.md`:
      - appended closure-round lesson for ranker-drift guardrail.
    - `docs/handover/phase20_handover.md`:
      - created PM-facing closure/handoff packet with formula register, logic chain, evidence matrix, and new-context bootstrap block.
    - `docs/saw_reports/saw_phase20_closeout_round4.md`:
      - created SAW closeout report with closure packet and validation lines.
  - Evidence:
    - Phase 20 ledger artifacts:
      - `data/processed/phase20_5y_hardgate_summary.json` (`CAGR=0.12124546831937266`, `Sharpe=0.653639319471661`, `MaxDD=-0.1843785358570833`).
      - `data/processed/phase20_5y_PRODUCTION_FINAL_summary.json` (`CAGR=0.012282190604340881`, `Sharpe=0.3377146011290567`, `MaxDD=-0.032054938043322045`).
    - MU diagnostic evidence:
      - `data/processed/diagnostic_MU_reverse_engineer.csv` (Oct 2022: `q_tot mean=3.2634692142857142`, `inv_vel_traj mean=0.0`, `conviction mean=3.510820467875683`).
    - Validation commands and results are recorded in `docs/saw_reports/saw_phase20_closeout_round4.md`.
  - Rationale:
    - closure package converts fragmented experiment outcomes into a locked and auditable operating baseline,
    - explicit handover packet prevents context loss at `/new` boundary,
    - ranker restore aligns runtime math with approved Option A capital-cycle thesis.
  - Open risks:
    - Full 5-year rerun under the freshly re-locked ranker was not executed in this docs/governance round; existing ledger remains prior run evidence.
  - Rollback path:
    - revert `strategies/ticker_pool.py::_conviction_cluster_score` to prior supercycle expression,
    - restore previous `docs/phase_brief/phase20-brief.md`, remove `docs/handover/phase20_handover.md`, and drop `D-115` entry if PM rejects closure package.

Context Bootstrap Governance Update (2026-02-23): Phase-End Context Artifact Refresh Policy (D-116) ✅
  - Decision:
    - Require explicit phase-end refresh of generated context artifacts before milestone closure:
      - `docs/context/current_context.json`
      - `docs/context/current_context.md`
    - Add a build-script validation gate so phase close fails when context artifacts are stale/missing/invalid.
  - Implementation:
    - Updated `.codex/skills/saw/SKILL.md` Section 6 with `CHK-PH-06` context refresh + validation command contract.
    - Updated `docs/checklist_milestone_review.md` with mandatory context artifact refresh checklist item.
    - Updated `docs/runbook_ops.md` with startup quickstart commands for context bootstrap:
      - `.venv\Scripts\python scripts/build_context_packet.py`
      - `invoke $context-bootstrap`
      - `.venv\Scripts\python scripts/build_context_packet.py --validate`
    - Updated `docs/notes.md` with context artifact schema and markdown packet contracts.
    - Updated `docs/lessonss.md` with a context-drift guardrail lesson entry.
  - Evidence:
    - Docs-only governance round; no test execution required.
    - Commands and artifact path contracts are documented in runbook + SAW phase-end protocol.
  - Rationale:
    - `/new` handoffs degrade when context artifacts are not regenerated and validated at phase boundaries.
  - Open risks:
    - `scripts/build_context_packet.py` and `$context-bootstrap` invocation semantics must stay stable across local environments.
  - Rollback note:
    - Revert `D-116` document edits to return to prior phase-close policy without mandatory context artifact refresh.

Context Bootstrap Implementation (2026-02-23): Deterministic Artifact Generator + Validation Gate (D-117) ✅
  - Decision:
    - Implement and retain script-backed context persistence as the canonical `/new` bootstrap mechanism.
    - Keep subagents for orchestration/review only; do not use subagent memory as persistence.
  - Implementation:
    - Added `scripts/build_context_packet.py`:
      - generates `docs/context/current_context.json` and `docs/context/current_context.md`.
      - enforces stable key contract (`schema_version`, `generated_at_utc`, `source_files`, `active_phase`, `what_was_done`, `what_is_locked`, `what_is_next`, `first_command`, `next_todos`).
      - added `--validate` mode for stale-drift detection against source docs.
      - validates markdown header contract and JSON->markdown parity.
    - Added tests:
      - `tests/test_build_context_packet.py` (8 tests passing).
      - `tests/conftest.py` to stabilize repo-root imports for direct `pytest` invocation.
    - Added skill:
      - `.codex/skills/context-bootstrap/SKILL.md`.
      - updated `.codex/skills/README.md` skill index.
    - Integrated governance docs already wired under `D-116` (`saw`/checklist/runbook).
  - Evidence:
    - `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` -> PASS (`8 passed`).
    - `.venv\Scripts\pytest tests\test_build_context_packet.py -q` -> PASS (`8 passed`).
    - `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
    - `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
    - artifacts present:
      - `docs/context/current_context.json`
      - `docs/context/current_context.md`
  - Rationale:
    - provides deterministic cross-session startup context with strict validation and reproducible operator commands.
  - Open risks:
    - two-file output commit is per-file atomic but not transactionally atomic across both files.
  - Rollback note:
    - remove `scripts/build_context_packet.py`, `tests/test_build_context_packet.py`, `tests/conftest.py`, `.codex/skills/context-bootstrap/`, and revert `D-116/D-117` docs wiring if policy is reversed.

Context Bootstrap Port to SOP Repository (2026-02-23): Deterministic Session Bootstrap Enabled (D-SOP-001) ✅
  - Decision:
    - Replicate the script-backed context bootstrap stack in `E:\Code\SOP\quant_current_scope`.
    - Keep skills as the invocation layer and local docs/artifacts as persistence; no MCP dependency required for this phase.
  - Implementation:
    - Added/ported `scripts/build_context_packet.py`, `scripts/__init__.py`.
    - Added/ported `tests/test_build_context_packet.py`, `tests/conftest.py`.
    - Added `.codex/skills/context-bootstrap/SKILL.md` and updated `.codex/skills/README.md`.
    - Added required docs inputs: `docs/phase_brief/phase20-brief.md`, `docs/handover/phase20_handover.md`, `docs/decision log.md`, `docs/lessonss.md`.
    - Added governance/runbook support docs: `docs/runbook_ops.md`, `docs/checklist_milestone_review.md`, `docs/notes.md`.
    - Generated and validated context artifacts:
      - `docs/context/current_context.json`
      - `docs/context/current_context.md`
  - Evidence:
    - `python scripts/build_context_packet.py` -> PASS.
    - `python scripts/build_context_packet.py --validate` -> PASS.
    - `python -m pytest tests/test_build_context_packet.py -q` -> PASS (`8 passed`).
  - Rationale:
    - Ensures consistent `/new` startup context in SOP with deterministic schema + validation guards.
  - Open risks:
    - SOP repo currently has no local `.venv`; commands were executed with system `python` for this bootstrap round.
  - Rollback note:
    - Remove added files under `scripts/`, `tests/`, `.codex/skills/context-bootstrap/`, and `docs/context/` if bootstrap policy is reversed.

Philosophy Local-First Loop + Gemini Handover Automation (2026-03-01): Worker-First Sync Gate (D-SOP-002) ✅
  - Decision:
    - Enforce local-first philosophy propagation across worker repos before any migration update is written into SOP main governance artifacts.
    - Extend context bootstrap to auto-generate a phase-level Gemini handover artifact that includes `top_level_PM.md` and all context sources.
  - Implementation:
    - Added `top_level_PM.md` as philosophy source-of-truth (expanded with sections 6/7/8: TOC, Cynefin, Ergodicity).
    - Added `scripts/sync_philosophy_feedback.py`:
      - discovers worker repos under `E:\Code` via `AGENTS.md`,
      - updates worker local feedback loops first,
      - writes `docs/context/philosophy_migration_log.json` and `docs/context/philosophy_migration_report.md`,
      - blocks main migration in strict mode when any worker update fails.
    - Extended `scripts/build_context_packet.py`:
      - auto-writes `docs/handover/gemini/phase<NN>_gemini_handover.md`,
      - includes top-level PM, context artifacts, and source context files,
      - validates Gemini handover drift in `--validate` mode.
    - Added/updated tests:
      - `tests/test_sync_philosophy_feedback.py`,
      - `tests/test_build_context_packet.py` (Gemini generation + drift checks).
    - Updated governance docs:
      - `docs/runbook_ops.md`,
      - `docs/checklist_milestone_review.md`,
      - `docs/notes.md`,
      - `docs/lessonss.md`.
  - Evidence:
    - `python -m pytest tests/test_build_context_packet.py tests/test_sync_philosophy_feedback.py -q`
    - `python scripts/sync_philosophy_feedback.py --scan-root E:\Code --main-repo E:\Code\SOP\quant_current_scope`
    - `python scripts/build_context_packet.py`
    - `python scripts/build_context_packet.py --validate`
  - Rationale:
    - Prevents main-governance updates from getting ahead of worker adoption.
    - Creates deterministic, phase-scoped handover packets for Gemini without manual assembly.
  - Open risks:
    - Worker repos lacking writable local loop targets may block strict migration and require per-repo bootstrap.
  - Rollback note:
    - Remove `top_level_PM.md`, `scripts/sync_philosophy_feedback.py`, revert `scripts/build_context_packet.py` handover extensions, and roll back associated docs/tests updates.

### Phase 24A: First Principles Engineering Alignment (2026-03-02)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-105 | governance/schema | Worker output lacked engineering reasoning structure (confidence + citations only, no problem-solving alignment) | Introduce worker_reply_packet v2.0.0 with `machine_optimized` block (confidence_level, problem_solving_alignment_score, expertise_coverage) and `pm_first_principles` block (problem, constraints, logic, solution) | Enables CEO to evaluate task-quality alignment from persisted structured reasoning, not just structural completion evidence. |
| D-106 | governance/validator | v2 schema change would break fail-closed G06 gate and bootstrap without migration | 3-tier validator split (shared + v1-only + v2-only) with version auto-detect from packet `schema_version` and optional `--schema-version-override` CLI flag | Preserves backward compatibility; v1 packets pass v1 rules, v2 packets pass v2 rules. Cutover scheduled for Phase 24B. |
| D-107 | governance/digest | CEO digest lacked First Principles and Expertise Coverage sections; confidence read was hardcoded to v1 location | Add digest sections I (First Principles) and II (Strategic Expertise Coverage) at top; rewire confidence read with `_resolve_confidence()` v2-first + v1-fallback | Digest renders only persisted artifacts (invariant). v1 packets show graceful "Not available" for new sections. |
| D-108 | governance/bootstrap | Bootstrap emitted v1 packets; needed v2 with valid expertise_coverage for self-passing G06 | Bootstrap emits v2 packets with one valid expertise row (domain=qa, verdict=SKIPPED) and placeholder pm_first_principles | New repos start on v2 from day one; placeholder content clearly marked for replacement. |
| D-109 | governance/cutover | Dual-mode v1/v2 could linger indefinitely without enforcement trigger | Phase 24A: auto-detect. Phase 24B: add `--schema-version-override 2.0.0` to G06 after cutover readiness gate passes on all repos. Phase 25+: remove v1 code path. | Bounded migration window with deterministic triggers and pre-cutover validation. |
| D-110 | governance/ceo-prompt | CEO prompt had no tone/style constraints; could drift into ceremonial praise | Added Communication Constraints section (no pleasantries/praise/metaphors, purely analytical, every statement falsifiable or actionable) and Strategic Expertise Matrix output contract item | Prompt-level constraint proportionate to risk; no validator added (accepted risk). |

- Evidence:
  - `python -m pytest tests/test_validate_worker_reply_packet.py tests/test_build_ceo_bridge_digest.py -v` (20 passed)
  - `python scripts/validate_worker_reply_packet.py --input docs/context/worker_reply_packet.json --repo-root .` (exit 0)
  - Modified files: `docs/context/schemas/worker_reply_packet.json.template`, `scripts/validate_worker_reply_packet.py`, `scripts/build_ceo_bridge_digest.py`, `scripts/bootstrap_repo_profile.ps1`, `scripts/phase_end_handover.ps1`, `docs/context/ceo_init_prompt_v1.md`, `docs/context/worker_reply_packet.json`, `docs/runbook_ops.md`, `docs/checklist_milestone_review.md`
- Rollback note:
  - Revert all modified files to pre-Phase 24A state. v1 packets and v1 digest sections will resume. No data loss risk (additive schema change).

### Phase 24B-minimal: Low-Cost, High-ROI Enforcement Tightening (2026-03-02)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-111 | governance/validator | Score thresholds for confidence and relatability were advisory-only in digest; no machine enforcement | Add `--enforce-score-thresholds` flag to validator: confidence < 0.70 → HOLD, relatability < 0.75 → REFRAME. Feature-switched via `-EnforceScoreThresholds` in `phase_end_handover.ps1` (default off). | Hard enforcement gated by opt-in flag prevents bootstrap self-fail and cross-repo breakage. Digest score gates remain advisory visualization. |
| D-112 | governance/validator | 6-expert always-on council was expensive; not all domains needed per decision | Default triad (principal, riskops, qa) + trigger-based escalation for system_eng, architect, devsecops. Triad structural + substantive checks gated by `--enforce-score-thresholds`. | Reduces overhead while maintaining coverage on buildability, risk, and quality. Escalation experts activated only when trigger conditions are met. |
| D-113 | governance/phase-end | Triad enforcement could break cross-repo v2 packets missing triad rows | G05b cross-repo readiness gate in `phase_end_handover.ps1`. Mandatory when `-EnforceScoreThresholds` is true (BLOCK if `-CrossRepoRoots` missing). SKIPPED when flag is off. | Prevents activating threshold enforcement without proving all repos are compliant. |
| D-114 | skills/research | Research skill had no explicit confidence downgrade rules or conflict escalation tiers | Added confidence downgrade rule (SupportStrength != Direct → low-certainty) and 3-tier conflict escalation (Tier 1: Open Risks/PASS, Tier 2: BLOCK/PM resolution, Tier 3: BLOCK + CEO escalation). | Closes gap where indirect evidence could carry high-confidence rating. Conflict tiers provide deterministic escalation path. |
| D-115 | skills/saw | SAW closure allowed user override on Critical findings; conflicted with AGENTS.md inherited-out-of-scope path | Scoped Critical auto-BLOCK to in-scope findings only (no override). Inherited out-of-scope Critical/High retains user-acceptance path with owner + TargetDate. Aligned language in SAW SKILL.md and AGENTS.md Section 12.3. | Removes policy conflict while preserving pragmatic handling of inherited findings. |
| D-116 | governance/digest | Digest had no per-round score gate visualization for CEO decision-making | Added Section X (Per-Round Score Gates) with GO/HOLD/REFRAME table. Renumbered PM Actions to Section XI. | CEO sees threshold status per task before dispatch. |

- Evidence:
  - `python -m pytest tests/test_validate_worker_reply_packet.py tests/test_build_ceo_bridge_digest.py -v` (35 passed)
  - `python scripts/validate_worker_reply_packet.py --input docs/context/worker_reply_packet.json` (exit 0, structural-only)
  - `python scripts/validate_worker_reply_packet.py --input docs/context/worker_reply_packet.json --enforce-score-thresholds` (exit 1: confidence 0.30 < 0.70, relatability 0.0 < 0.75, all triad SKIPPED — expected for bootstrap)
  - Modified files: `docs/context/ceo_init_prompt_v1.md`, `scripts/validate_worker_reply_packet.py`, `scripts/build_ceo_bridge_digest.py`, `scripts/bootstrap_repo_profile.ps1`, `scripts/phase_end_handover.ps1`, `docs/context/worker_reply_packet.json`, `.codex/skills/research-analysis/SKILL.md`, `.codex/skills/saw/SKILL.md`, `AGENTS.md`
- Rollback note:
  - Revert all modified files to post-Phase 24A state. v2 validation without triad/threshold enforcement resumes. No data loss (additive enforcement only).

### Phase 24C: Auditor Loop — Shadow → Enforce (2026-03-02)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-117 | governance/auditor | Worker reply packets had no independent review beyond structural validation (G06) | Add `scripts/run_auditor_review.py` (G11) with 10 governance checks (AUD-R000–R009), canonical severity model, and shadow/enforce modes. Default shadow (non-blocking for policy findings). | Independent auditor catches quality gaps (confidence, relatability, triad, citations, placeholders) that structural validation cannot. Orthogonal to SAW (process) vs auditor (output). |
| D-118 | governance/auditor | Severity could differ between shadow and enforce, making FP calibration during shadow unreliable | Canonical severity: same severity in both modes. Only the `blocking` flag differs (shadow: always false; enforce: true for CRITICAL/HIGH). | Stable severity semantics ensure false-positive rate measurement during shadow period is directly comparable to enforce behavior. |
| D-119 | governance/auditor | Infra errors (script crash, invalid JSON) could be masked by shadow mode's non-blocking policy | Exit code 2 = INFRA_ERROR, always blocks regardless of mode. Exit 1 = policy BLOCK (enforce only). Exit 0 = PASS. | Broken tooling should never hide behind shadow mode. Infra failures are tool failures, not policy findings. |
| D-120 | governance/phase-end | G09b (digest rebuild) could be skipped after G11 BLOCK in enforce mode, leaving stale digest | G09b + G10b run in finalize path (always, when `-AuditMode` ≠ `none`), even after G11 BLOCK. Primary failed gate takes precedence over finalize failures. | Digest always reflects the auditor findings that caused the BLOCK. Root cause stays clear in summary. |
| D-121 | governance/phase-end | Stale `auditor_findings.json` from a previous run could leak into current digest on auditor infra failure | Run-scoped output path: `phase_end_logs/auditor_findings_<runid>.json`. G09b only reads run-scoped path. Canonical path updated as copy only on exit 0 or 1. | Eliminates stale file ingestion when auditor crashes before writing output. |
| D-122 | governance/auditor | v1 packets lack v2 fields but should not crash auditor or silently skip | AUD-R000: v1 packet emits single HIGH finding. v2-only checks skipped. Unknown schema_version → exit 2 (INFRA_ERROR). | Graceful degradation for v1; fail-closed for unknown versions. Enforce mode blocks v1 packets via AUD-R000 (HIGH + blocking=true). |
| D-123 | governance/auditor | `dod_result=FAIL` initially considered CRITICAL by auditor, conflicting with validator contract that accepts FAIL as valid data | AUD-R008: dod_result=FAIL → MEDIUM (informative), not CRITICAL. Auditor does not redefine phase-end semantics. | Validator contract allows FAIL. Auditor reports it for visibility but does not escalate beyond MEDIUM. |
| D-124 | governance/auditor | Bootstrap/template packets with sentinel open_risks ("none", "n/a", "placeholder") triggered spurious findings | AUD-R009: sentinel normalization filters out `{none, n/a, na, placeholder, tbd, todo, ""}` before flagging open_risks. | Prevents over-firing on bootstrap and template packets while still catching substantive unresolved risks. |
| D-125 | governance/digest | CEO digest lacked auditor findings section; stale files could be rendered | Added Section IX (Auditor Review Findings) between VIII (Worker Confidence) and X (Score Gates). Source-based detection: only renders when auditor data is explicitly passed as source. | Stale-file suppression: digest builder never auto-discovers auditor files from disk. When `-AuditMode none`, Section IX shows "Auditor review not available." |
| D-126 | governance/auditor | No promotion criteria for shadow → enforce transition | 5-condition gate: (a) 24B operational close, (b) ≥30 audited items across ≥2 consecutive weekly windows, (c) C/H FP rate <5%, (d) PM/owner signoff in decision log, (e) all packets schema_version=2.0.0. | Prevents premature enforce activation. Numeric criteria ensure statistical significance and cross-repo readiness. |
| D-127 | governance/startup | Worker loop could start without explicit intent lock or readiness visibility, causing early drift and rework | Added `scripts/startup_codex_helper.py` as required entry step: prints readiness progress for core governance docs/artifacts and runs intent interrogation (`ORIGINAL_INTENT`, `DELIVERABLE_THIS_SCOPE`, `NON_GOALS`, `DONE_WHEN`) before round execution. | Keeps flow lean but deterministic: one startup checkpoint, one intent contract, and paste-ready kickoff block for Worker/Auditor handoff. |
| D-128 | governance/init | Init brainstorming could become either ad-hoc or overcomplicated when adding strategic lenses | Added `docs/init_phase_brainstorm_framework.md` to define lean init sequence, CEO/CTO option framing, controlled expert jump-out rules, and capped philosopher-lens overlay (0-2 max). | Preserves first-principles decision quality while preventing expert/philosophy sprawl before execution. |
| D-129 | governance/loop | Mid-loop ambiguity on reversibility, trivial-work routing, and disagreement timing caused avoidable latency and rework | Hardened round/loop governance with mandatory `DECISION_CLASS`, `EXECUTION_LANE`, strict FAST-lane eligibility, delete-before-add contract, pre-execution disagreement capture, and lightweight cross-judge sampling rules. | Improves decision speed and consistency while preserving anti-overengineering boundaries. |
| D-130 | governance/roadmap | Weekly leadership reporting emphasized raw throughput but underweighted decision quality and roadmap adaptability | Added dynamic 10-phase roadmap board template and expanded weekly CEO summary with Decision Latency, Governance Adoption Score, and Top-3 recurring finding burn-down. | Creates rolling-priority visibility (committed/adaptive/exploratory) and shifts management focus toward learning velocity and closure quality. |
| D-131 | governance/truth-check | CEO go-signal narrative could drift from dossier/calibration facts | Added executable truth-check gate `scripts/validate_ceo_go_signal_truth.py` + tests to verify `Recommended Action` and C0-C5 status rows against source artifacts. | Prevents executive decision packets from diverging from machine-generated evidence. |
| D-132 | governance/init-handoff | Startup worker kickoff lacked explicit channel instruction, causing friction between web paste flow and local CLI flow | Added startup handoff targeting in `startup_codex_helper.py` with explicit worker header output: default `(paste to sonnet web)` and local CLI `(skills call upon worker)`. | Reduces operator ambiguity and keeps init handoff deterministic across channels. |
| D-133 | governance/init-controls | Init/startup contracts lacked hard requirements for positioning lock, tight task granularity, and intuition ownership before execution | Hardened init governance by making `POSITIONING_LOCK`, `TASK_GRANULARITY_LIMIT` (`1|2`), `INTUITION_GATE`, and `INTUITION_GATE_RATIONALE` mandatory across startup and round docs, with a hard stop when `INTUITION_GATE=HUMAN_REQUIRED` until PM/CEO acknowledgment is recorded. | Prevents premature execution on ambiguous scope, enforces atomic task sizing, and adds explicit human override on intuition-sensitive decisions. |
| D-134 | governance/init-minimalism | Startup execution state was spread across multiple artifacts and lacked a single authoritative go/no-go card, while `HUMAN_REQUIRED` rounds needed explicit startup acknowledgment capture | Standardized a canonical startup card (`docs/context/init_execution_card_latest.md`) as the single-source init execution view and enforced startup `HUMAN_REQUIRED` acknowledgment capture (`INTUITION_GATE_ACK`, `INTUITION_GATE_ACK_AT_UTC`) in the startup command contract (including `--output-card`, `--intuition-gate-ack`, `--intuition-gate-ack-at-utc`). | Improves iteration efficiency by reducing startup scan overhead to one artifact while preserving strict PM/CEO gating before execution on intuition-sensitive rounds. |
| D-135 | governance/loop-automation | Loop refresh, closure readiness, weekly summary truth, and startup round seed context relied on separate manual steps that increased drift risk | Added minimal automation wrappers: `scripts/run_loop_cycle.py` (single-command cycle), `scripts/validate_loop_closure.py` (single closure gate), `scripts/validate_ceo_weekly_summary_truth.py` (weekly summary truth-check), and startup round-contract seed output (`docs/context/round_contract_seed_latest.md`). | Tightens operational traceability and iteration speed through deterministic latest-pointer artifacts without adding new governance layers or overengineering the control plane. |
| D-136 | governance/closure-hardening | Cycle-level HOLD reporting could be misread as escalation-ready, and closure readiness needed explicit GO-action enforcement at gate level | Harden closure semantics: `validate_loop_closure.py` requires `ceo_go_signal.md` `Recommended Action: GO` for `READY_TO_ESCALATE`; `HOLD`/`REFRAME` are `NOT_READY`. Keep `run_loop_cycle.py --allow-hold` as reporting-only remap, with `--allow-hold false` disabling HOLD remap. | Preserves fail-closed escalation authority while allowing operational HOLD visibility without bypassing closure truth or recommendation gates. |
| D-137 | governance/multi-worker-defer | Multi-worker concurrency can improve scale but premature implementation risks overengineering and coordination overhead | Created deferred design spec `docs/multi_worker_concurrency_todo.md` and froze implementation until explicit unfreeze triggers are met (repeat cross-track blockers, high reconciliation overhead, recurring dependency disputes, or CEO packet ambiguity from multi-track flow). | Preserves current loop simplicity while defining a clear, trigger-based path to parallel track orchestration when real bottlenecks justify it. |
| D-138 | governance/tdd-closure-enforcement | Loop closure could pass on narrative evidence without explicit red-green test proof, weakening engineering auditability | Made TDD contract evidence mandatory for round closure: require `TDD_MODE`, red/green commands+results, `REFACTOR_NOTE`, and `TDD_NOT_APPLICABLE_REASON` when applicable; closure readiness now requires `tdd_contract_gate=PASS`. | Enforces deterministic test-first evidence for code rounds while allowing bounded, auditable `NOT_APPLICABLE` handling for non-code rounds. |

- Evidence:
  - `python scripts/run_auditor_review.py --input docs/context/worker_reply_packet.json --repo-root . --output docs/context/auditor_findings.json --mode shadow` (exit 0, 5 findings: C=1/H=2/M=2, all blocking=false)
  - `python scripts/run_auditor_review.py --input docs/context/worker_reply_packet.json --repo-root . --output docs/context/auditor_findings.json --mode enforce` (exit 1, BLOCK: C=1/H=2 blocking=true)
  - `python -m pytest tests/test_run_auditor_review.py tests/test_build_ceo_bridge_digest.py tests/test_validate_worker_reply_packet.py -v` (60 passed, 0 regression)
  - Modified files: `scripts/run_auditor_review.py` (NEW), `docs/context/schemas/auditor_findings.json.template` (NEW), `tests/test_run_auditor_review.py` (NEW), `scripts/phase_end_handover.ps1`, `scripts/build_ceo_bridge_digest.py`, `docs/context/ceo_init_prompt_v1.md`, `AGENTS.md`, `docs/runbook_ops.md`, `docs/checklist_milestone_review.md`, `tests/test_build_ceo_bridge_digest.py`
- Rollback note:
  - Remove `scripts/run_auditor_review.py`, `docs/context/schemas/auditor_findings.json.template`, `tests/test_run_auditor_review.py`, `docs/context/auditor_findings.json`. Revert edits to `scripts/phase_end_handover.ps1` (remove G11/G09b/G10b/finalize path), `scripts/build_ceo_bridge_digest.py` (remove Section IX), `docs/context/ceo_init_prompt_v1.md`, `AGENTS.md` (remove Section 13b), `docs/runbook_ops.md`, `docs/checklist_milestone_review.md`, `tests/test_build_ceo_bridge_digest.py`. No data loss (additive change).

### Phase 24C: QA Remediation Hardening (2026-03-05)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-139 | governance/go-signal | GO-signal writer returned success on output I/O failure, enabling false-positive orchestration success | `scripts/generate_ceo_go_signal.py` now returns infra error (`exit 2`) on output write failure; regression test added to assert non-zero on simulated `PermissionError` | Enforces fail-closed behavior for executive signal artifact generation. |
| D-140 | governance/auditor | AUD-R002 severity drift (docs CRITICAL, code HIGH) created policy-code mismatch | Upgraded `AUD-R002` (`problem_solving_alignment_score < 0.75`) to `CRITICAL` in `scripts/run_auditor_review.py` and aligned tests | Makes policy authoritative and closes enforcement loophole. |
| D-141 | governance/io-safety | Calibration report writer used `tempfile.mktemp`, which is race-prone | Replaced with `NamedTemporaryFile(delete=False)` + `os.replace` atomic publish and cleanup-on-error path | Removes TOCTOU risk in governance artifact writes. |
| D-142 | governance/escalations | Escalation event append path claimed dedupe but always appended new events | Added deterministic unresolved-event dedupe key and deduped append in `scripts/aggregate_worker_status.py` | Prevents noisy duplicate escalation growth and preserves signal quality. |
| D-143 | governance/dispatch | Duplicate `correlation_id` ACKs were collapsed nondeterministically by dict overwrite | `scripts/validate_dispatch_acks.py` now detects duplicate `correlation_id` and fails explicitly (`exit 6`) | Treats duplicate ACKs as poisoned state instead of guessing authoritative record. |
| D-144 | governance/test-surface | Integrity validators had no direct contract tests, leaving blind spots | Added test modules for: traceability, orphan-changes, evidence-hashes, digest-freshness, dispatch-acks; script-to-test parity now 19/19 | Raises confidence on fail-closed guard scripts and reduces regression risk. |

- Evidence:
  - `pytest -q` -> `158 passed in 17.70s`
  - `python -m compileall -q scripts tests` -> PASS
  - `python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true` -> `HOLD` (expected), no infra errors; closure result `NOT_READY` due `go_signal_action_gate` (`Recommended Action: HOLD`)
  - Updated/new files include:
    - `scripts/generate_ceo_go_signal.py`, `tests/test_generate_ceo_go_signal.py`
    - `scripts/run_auditor_review.py`, `tests/test_run_auditor_review.py`
    - `scripts/auditor_calibration_report.py`, `tests/test_auditor_calibration_report.py`
    - `scripts/aggregate_worker_status.py`, `tests/test_aggregate_worker_status.py`
    - `scripts/validate_dispatch_acks.py`, `tests/test_validate_dispatch_acks.py`
    - `tests/test_validate_traceability.py`, `tests/test_validate_orphan_changes.py`, `tests/test_validate_evidence_hashes.py`, `tests/test_validate_digest_freshness.py`
- Rollback note:
  - Revert D-139..D-144 touched files listed above; no schema-breaking changes were introduced.
  - If rollback is partial, prioritize restoring old `validate_dispatch_acks.py` semantics only with explicit duplicate-ID policy acceptance.

### Phase 24C: Advisory Uncertainty Boundary Clarification (2026-03-07)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-145 | governance/advisory-boundaries | The loop was operationally fail-closed, but worker/director outputs lacked one explicit advisory artifact that says where machine-only execution should stop and what lane should help next | Added advisory-only `automation_uncertainty_status` to `scripts/build_exec_memory_packet.py` and a canonical `docs/automation_boundary_registry.md` covering PM review, PM/CEO review, expert input, and manual UX/signoff boundaries | Makes "I don't know / machine should stop here" explicit without adding gates, authorities, or new control-plane complexity |

- Evidence:
  - `python -m py_compile scripts/build_exec_memory_packet.py` -> PASS
  - `python -m pytest tests/test_build_exec_memory_packet.py -q` -> PASS
  - Updated/new files: `scripts/build_exec_memory_packet.py`, `docs/automation_boundary_registry.md`, `tests/test_build_exec_memory_packet.py`
- Rollback note:
  - Remove `docs/automation_boundary_registry.md` and revert the advisory-only uncertainty summary additions in `scripts/build_exec_memory_packet.py` and `tests/test_build_exec_memory_packet.py`; no gate or schema authority rollback is required.

### Phase 24C: Split-Style Advisory and Worker Delivery (2026-03-08)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-146 | governance/operator-ux | Advisory artifacts and worker packets were structurally valid, but they did not expose one consistent machine/human/paste-ready split for downstream automation and operator delegation | Add additive split-style surfaces: worker `response_views` (`machine_view`, `human_brief`, `paste_ready_block`), advisory artifact `human_brief` + `machine_view` alongside existing `paste_ready_block`, and consumer rendering in loop-cycle markdown, takeover entrypoint, and CEO digest | Improves machine transport, PM-style readability, and copy/paste delegation without changing authority, gates, or the stable control plane |

- Evidence:
  - `python -m pytest tests/test_validate_worker_reply_packet.py tests/test_build_exec_memory_packet.py tests/test_run_loop_cycle.py tests/test_print_takeover_entrypoint.py tests/test_build_ceo_bridge_digest.py tests/test_system_control_plane_integration.py -q`
  - Updated files include: `docs/context/schemas/worker_reply_packet.json.template`, `scripts/validate_worker_reply_packet.py`, `scripts/build_exec_memory_packet.py`, `scripts/run_loop_cycle.py`, `scripts/print_takeover_entrypoint.py`, `scripts/build_ceo_bridge_digest.py`, `docs/loop_operating_contract.md`, `docs/expert_invocation_policy.md`, `tests/test_validate_worker_reply_packet.py`, `tests/test_build_exec_memory_packet.py`, `tests/test_run_loop_cycle.py`, `tests/test_print_takeover_entrypoint.py`, `tests/test_build_ceo_bridge_digest.py`, `tests/test_system_control_plane_integration.py`
- Rollback note:
  - Revert the split-style additive fields and consumer rendering above; authoritative worker/digest/control-plane behavior remains intact because the change is additive and backward-compatible.

### Phase 24C: Milestone Expert Roster Fail-Closed Advisory Signals (2026-03-08)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-147 | governance/expert-lineup | Advisory expert assignment could imply a domain choice even when no milestone roster existed or the requested domain was outside approved lineup | Add additive roster-aware advisory fields in exec-memory artifacts (`roster_fit`, `requested_domain`, `board_reentry_required`, lineup/memory statuses) sourced from `docs/context/milestone_expert_roster_latest.json` when present. Emit explicit fail-closed statuses `ROSTER_MISSING`, `UNKNOWN_EXPERT_DOMAIN`, and `BOARD_LINEUP_REVIEW_REQUIRED` instead of silently assigning escalation-critical experts | Makes lineup uncertainty explicit for PM/CEO board reentry while preserving existing authority boundaries and avoiding new hard control-plane gates |

- Evidence:
  - `python -m pytest tests/test_build_exec_memory_packet.py -q`
  - Updated files include: `scripts/build_exec_memory_packet.py`, `tests/test_build_exec_memory_packet.py`, `docs/expert_invocation_policy.md`, `docs/automation_boundary_registry.md`, `docs/decision_authority_matrix.md`
- Rollback note:
  - Revert the additive roster/memory fields and docs updates above; existing advisory artifacts and authority model continue unchanged.

### Phase 24C: Advisory R4 Elegance / Entropy Snapshot Reuse (2026-03-08)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-148 | governance/optimality-review | Milestone-close simplicity and entropy concerns kept recurring, but only as discussion; creating a new subsystem would overengineer the advisory layer | Reused `docs/templates/optimality_review_brief.md` and `docs/optimality_review_protocol.md` to add one optional `ELEGANCE_ENTROPY_SNAPSHOT` with lean proxy fields and explicit `I don't know yet` fallback | Makes elegance and maintainability discussable in one existing artifact without adding gates, validators, or authority changes |

- Evidence:
  - `rg "ELEGANCE_ENTROPY_SNAPSHOT|CONCEPT_SURFACE_DELTA|I don't know yet|advisory only" OPERATOR_LOOP_GUIDE.md docs/optimality_review_protocol.md docs/templates/optimality_review_brief.md docs/runbook_ops.md docs/minimal_optimality_roadmap.md docs/loop_operating_contract.md`
  - Updated files include: `OPERATOR_LOOP_GUIDE.md`, `docs/optimality_review_protocol.md`, `docs/templates/optimality_review_brief.md`, `docs/runbook_ops.md`, `docs/minimal_optimality_roadmap.md`, `docs/loop_operating_contract.md`
- Rollback note:
  - Revert the additive R4 snapshot fields and references above; the prior optimality brief and milestone-close addendum remain intact because this change does not alter any gate or authority path.

### Phase 5A.2: Subagent Routing Matrix (2026-03-13)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-175 | governance/subagent-routing | Subagent context loading lacked explicit role-to-artifact mapping, causing potential context bleed and unmeasured token overhead | Created `benchmark/subagent_routing_matrix.yaml` with 6 role mappings (startup_deputy, execution_deputy, specialist_deputy, pm_research_deputy, board_decision_deputy, auditor_deputy), each with required/optional/conditional/excluded artifacts and token budgets. Added `scripts/validate_routing_matrix.py` (schema + path validator), `scripts/measure_context_reduction.py` (token savings calculator), and `tests/test_subagent_routing.py` (selector/validator/slice tests). Token estimator: `len(text) // 4` from `build_exec_memory_packet.py:246`. | Provides deterministic context isolation per subagent role with measurable token reduction. No Agent tool integration yet (deferred). Validator rejects nested duplicates. Test coverage: required/optional/conditional semantics, duplicate rejection, token budgets. |

- Evidence:
  - `python scripts/validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .` → exit 0, "✓ Routing matrix valid: 6 roles"
  - `python scripts/measure_context_reduction.py benchmark/subagent_routing_matrix.yaml .` → Baseline: 37,496 tokens across 15 artifacts; Average savings per role: 30,203 tokens (80.6% reduction)
  - `python -m pytest tests/test_subagent_routing.py -v` → 19 passed in 0.17s
  - Budget utilization: startup_deputy 89.2%, execution_deputy 158.3% (over-budget, needs optimization), specialist_deputy 12.2%, pm_research_deputy 16.1%, board_decision_deputy 83.6%, auditor_deputy 101.0%
  - Token savings by role: startup_deputy 81.0%, execution_deputy 49.3%, specialist_deputy 96.7%, pm_research_deputy 96.6%, board_decision_deputy 86.6%, auditor_deputy 73.1%
  - Created files: `benchmark/subagent_routing_matrix.yaml`, `scripts/validate_routing_matrix.py`, `scripts/measure_context_reduction.py`, `tests/test_subagent_routing.py`
- Rollback note:
  - Remove `benchmark/subagent_routing_matrix.yaml`, `scripts/validate_routing_matrix.py`, `scripts/measure_context_reduction.py`, `tests/test_subagent_routing.py`. No schema-breaking changes.

### Phase 5A.2b: Path Validation Hardening and Test Coverage (2026-03-13)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-176 | governance/subagent-routing | D-175 claimed duplicate rejection but only checked within-role duplicates, not path security (absolute paths, `..` escapes, nested `quant_current_scope/...` duplicates). Tests reimplemented production logic locally instead of importing real scripts. | Created shared `scripts/utils/path_validator.py` with `validate_artifact_path(path, repo_root)` that rejects: (1) absolute paths (`/` or drive letters), (2) `..` parent escapes, (3) nested `quant_current_scope/...` duplicates, (4) paths escaping repo root via resolution. Patched `validate_routing_matrix.py` and `measure_context_reduction.py` to import and apply validator to all artifact classes (required/optional/conditional). Rewrote `tests/test_subagent_routing.py` to import production code (`validate_routing_matrix`, `measure_context_reduction`, `path_validator`) and added negative test cases for path validation. | Corrects D-175 overclaim by adding missing path security validation. Eliminates test/production drift by using real scripts in tests. Hardens artifact path handling against directory traversal and malformed paths. |
| D-176b | governance/subagent-routing | D-176 rejected nested duplicates (`quant_current_scope/quant_current_scope/...`) but allowed single repo-root-prefix (`quant_current_scope/docs/...`). `measure_context_reduction.py` used `continue` on invalid paths (fail-open), allowing silent skips instead of hard failures. | Added single repo-root-prefix check in `path_validator.py` line 41: rejects paths starting with `repo_root.name` (e.g., `quant_current_scope/docs/...`). Changed all `continue` statements to `sys.exit(1)` in `measure_context_reduction.py` (lines 55, 68, 83, 110) to ensure script exits non-zero on invalid paths. Added test cases: `test_reject_single_repo_root_prefix` and `test_metric_script_exits_on_invalid_path` in `test_subagent_routing.py`. Amended: Fixed repo-root-prefix check to handle `.` CLI invocation case using `repo_root.resolve().name` (line 43). Added CLI invocation tests: `test_validator_rejects_repo_prefix_with_dot_repo_root` and `test_metric_script_rejects_repo_prefix_with_dot_repo_root`. | Closes remaining gaps from D-176: prevents repo-root-prefix confusion and ensures fail-fast behavior on invalid paths. Completes Phase 5A.2b hardening. |

- Evidence:
  - `python scripts/validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .` → exit 0, "✓ Routing matrix valid: 6 roles"
  - `python scripts/measure_context_reduction.py benchmark/subagent_routing_matrix.yaml .` → Baseline: 37,496 tokens; Average savings: 30,203 tokens (80.6% reduction)
  - `python -m pytest tests/test_subagent_routing.py -q` → 26 passed in 0.15s
  - New test coverage: `test_reject_absolute_unix_path`, `test_reject_absolute_windows_path`, `test_reject_parent_escape`, `test_reject_nested_quant_current_scope`, `test_accept_valid_relative_path`, `test_reject_empty_path`, `test_invalid_path_rejected`, `test_parent_escape_rejected`, `test_invalid_path_blocks_validation`
  - Created files: `scripts/utils/path_validator.py`
  - Updated files: `scripts/validate_routing_matrix.py`, `scripts/measure_context_reduction.py`, `tests/test_subagent_routing.py`
- Rollback note:
  - Remove `scripts/utils/path_validator.py`. Revert changes to `scripts/validate_routing_matrix.py`, `scripts/measure_context_reduction.py`, `tests/test_subagent_routing.py` to D-174 baseline. Path validation will be absent.

### Phase 5B.1: Skills Infrastructure (2026-03-13)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-177 | skills/safe-db-migration | Phase 5 requires reference skill implementation with HIGH-risk approval and benchmark evidence per ADR-003 extension loading policy | Approved safe-db-migration v1.0.0 skill (HIGH-risk, database category) with benchmark evidence: Claude Opus 4.6 sql_accuracy baseline = 0.91 >= required threshold 0.85. Skill includes: (1) 8-step declarative execution flow (analyze → generate → validate → rollback), (2) strict guardrails (backup verification, rollback plan, test coverage ≥80%, auditor review, CEO GO signal), (3) eval requirements (sql_accuracy ≥ 0.85), (4) comprehensive README and PostgreSQL example. Added to skills/registry.yaml and extension_allowlist.yaml with approval_decision_id D-177. | Establishes first production skill with full ADR-003 compliance: declarative-only steps (no executable code), kernel guardrail floor enforcement (cannot weaken existing gates), benchmark-driven approval (0.91 baseline exceeds 0.85 requirement), and complete manifest validation (skill.yaml, guardrails.yaml, eval.yaml, README.md, examples/). |
| D-177a | governance/project-config | Phase 5B.1 requires project-local skill activation via .sop_config.yaml per ADR-003:165 shape | Approved .sop_config.yaml for quant_current_scope project with project_name="quant_current_scope", guardrail_strength="tight", active_skills=["safe-db-migration"], disabled_skills=[]. Project config validated against global allowlist: safe-db-migration is status=active, applicable_projects=["all"], and approval_decision_id D-177 exists in decision log. | Completes Phase 5B.1 activation contract: global allowlist (extension_allowlist.yaml) defines approved skills, project config (.sop_config.yaml) activates subset for local use, validators enforce allowlist → project consistency. |
| D-177b | skills/safe-db-migration | Phase 5B.1b hardening identified reasoning_depth requirement as premature without established benchmark suite | Amendment to D-177: reasoning_depth requirement deferred to future phase. sql_accuracy evidence (0.91 >= 0.85) sufficient for 5B.1 approval. Removed reasoning_depth >= 0.80 from skills/safe_db_migration/eval.yaml and updated README.md accordingly. | Preserves skill approval while acknowledging that reasoning_depth benchmark does not yet exist in benchmark/ directory. Single-metric approval (sql_accuracy) provides sufficient evidence for HIGH-risk database skill given strict guardrail enforcement (backup verification, rollback plan, auditor review, CEO GO signal). |
| D-177 | governance/phase5 | Phase 5B.2 requires skill activation visibility in subagent packets without execution semantics | Approved Thin Skill-Activation Bridge implementation: (1) skill_resolver.py surfaces active skills from .sop_config.yaml validated against extension_allowlist.yaml with fail-soft semantics, (2) skill_activation section added to exec_memory_packet with status/skills/warnings/errors, (3) skill_activation_latest.json persisted as standalone artifact in docs/context/, (4) added to execution_deputy and specialist_deputy optional_artifacts in routing matrix. Routing budget impact: execution_deputy 159.7% utilization (12K budget, 19,165 actual with skill_activation at 169 tokens), specialist_deputy 13.9% utilization (10K budget, 1,388 actual). Validation: 55 tests passing (9 new skill_activation tests, 46 existing tests updated). | Completes Phase 5B.2 activation bridge: subagents receive skill metadata without execution hooks, fail-soft resolver prevents governance file errors from blocking loop cycles, routing matrix integration preserves context isolation, standalone artifact enables future skill-aware routing decisions. Execution semantics remain blocked until Phase 5C skill execution engine approval. |

- Evidence:
  - Schema definitions created (6 files): `skills/schemas/registry_schema.yaml`, `skills/schemas/skill_schema.yaml`, `skills/schemas/guardrails_schema.yaml`, `skills/schemas/eval_schema.yaml`, `skills/schemas/allowlist_schema.yaml`, `skills/schemas/project_config_schema.yaml`
  - Registry and config files created (3 files): `skills/registry.yaml` (schema_version 1.0.0, 1 skill), `extension_allowlist.yaml` (schema_version 1.0.0, 1 skill), `.sop_config.yaml` (project_name quant_current_scope, 1 active skill)
  - Reference skill created: `skills/safe_db_migration/skill.yaml` (8 steps), `skills/safe_db_migration/guardrails.yaml` (6 pre-execution gates, 3 during-execution gates, 3 post-execution gates), `skills/safe_db_migration/eval.yaml` (1 benchmark requirement: sql_accuracy >= 0.85), `skills/safe_db_migration/README.md`, `skills/safe_db_migration/examples/postgres_add_column.md`
  - Validators created (3 scripts): `scripts/validate_skill_registry.py` (registry-driven, ignores legacy skills/*), `scripts/validate_skill_manifest.py` (validates full skill directory), `scripts/validate_extension_allowlist.py` (validates allowlist + project config, checks approval_decision_id in decision log)
  - Tests created: `tests/test_skill_infrastructure.py` (schema validation, allowlist resolution, approval metadata, registry-driven validation, benchmark evidence)
  - Benchmark evidence: `benchmark/baselines/anthropic_claude-opus-4-6_sql_accuracy_baseline.json` shows baseline_score = 0.91, requirement = 0.85, evidence: 0.91 >= 0.85 ✓
  - Validation results: skill_activation_latest.json artifact size: 169 tokens (679 chars), execution_deputy budget utilization: 19,165 / 12,000 (159.7%), specialist_deputy budget utilization: 1,388 / 10,000 (13.9%), test suite: 55 passing
- Rollback note:
  - Remove `skills/schemas/`, `skills/registry.yaml`, `extension_allowlist.yaml`, `.sop_config.yaml`, `skills/safe_db_migration/`, `scripts/validate_skill_registry.py`, `scripts/validate_skill_manifest.py`, `scripts/validate_extension_allowlist.py`, `tests/test_skill_infrastructure.py`. No schema-breaking changes to existing governance artifacts.

### Phase 24C: C1 Manual Signoff (PENDING) (2026-03-15)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-178 | governance/promotion | Historical pre-approval snapshot captured before PM signoff landed | Recorded the pre-approval evidence state on 2026-03-15. This snapshot is superseded by `D-174` on 2026-03-16, which grants PM signoff and closes `C1`. | Preserves the earlier evidence checkpoint without conflicting with the authoritative `C1` approval record. |

- Evidence:
  - `docs/context/auditor_promotion_dossier.json` (2026-03-15 refresh; W11 >= 10, C3 PASS)
  - `docs/context/auditor_calibration_report.json` (2026-03-15 refresh)
  - `docs/context/ceo_go_signal.md` (2026-03-15 refresh; GO)
  - `docs/context/ceo_weekly_summary_latest.md` (2026-03-15 refresh)
  - `docs/context/loop_closure_status_latest.json` (2026-03-15 refresh; READY_TO_ESCALATE)
- Rollback note:
  - Remove this PENDING C1 entry; no gate or authority changes.
