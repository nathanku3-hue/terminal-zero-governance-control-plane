# Terminal Zero Operations Runbook

## 1. Startup
- **Environment note**: `.venv\Scripts\python ...` examples assume a repo-local virtual environment. If `.venv` is unavailable, use `python ...` from a compatible Python 3.12+ interpreter and record that interpreter in validation evidence.
- **Codex Startup Helper (required before planning loop)**:
  - `.venv\Scripts\python scripts/startup_codex_helper.py --repo-root .`
  - Lean single-source init execution card quickstart (`HUMAN_REQUIRED`):
    - `.venv\Scripts\python scripts/startup_codex_helper.py --repo-root . --no-interactive --original-intent "<intent>" --deliverable-this-scope "<deliverable>" --non-goals "<non_goals>" --done-when "<done_when>" --positioning-lock "<positioning_lock>" --task-granularity-limit 1 --decision-class TWO_WAY --execution-lane STANDARD --intuition-gate HUMAN_REQUIRED --intuition-gate-rationale "<rationale>" --intuition-gate-ack PM_ACK --intuition-gate-ack-at-utc "<ISO8601_UTC>" --output-card docs/context/init_execution_card_latest.md --handoff-target local_cli`
  - Non-interactive Sonnet web quickstart:
    - `.venv\Scripts\python scripts/startup_codex_helper.py --repo-root . --no-interactive --original-intent "<intent>" --deliverable-this-scope "<deliverable>" --non-goals "<non_goals>" --done-when "<done_when>" --positioning-lock "<positioning_lock>" --task-granularity-limit 1 --decision-class TWO_WAY --execution-lane STANDARD --intuition-gate MACHINE_DEFAULT --intuition-gate-rationale "<rationale>" --handoff-target sonnet_web`
  - Non-interactive local CLI quickstart:
    - `.venv\Scripts\python scripts/startup_codex_helper.py --repo-root . --no-interactive --original-intent "<intent>" --deliverable-this-scope "<deliverable>" --non-goals "<non_goals>" --done-when "<done_when>" --positioning-lock "<positioning_lock>" --task-granularity-limit 2 --decision-class TWO_WAY --execution-lane STANDARD --intuition-gate HUMAN_REQUIRED --intuition-gate-rationale "<rationale>" --handoff-target local_cli`
  - Sonnet web handoff header (default): `--handoff-target sonnet_web` -> worker block starts with `WORKER_HEADER: (paste to sonnet web)`
  - Local CLI handoff header: `--handoff-target local_cli` -> worker block starts with `WORKER_HEADER: (skills call upon worker)`
  - Captures readiness-doc progress + required interrogation (`ORIGINAL_INTENT`, `DELIVERABLE_THIS_SCOPE`, `NON_GOALS`, `DONE_WHEN`, `POSITIONING_LOCK`, `TASK_GRANULARITY_LIMIT`, `DECISION_CLASS`, `EXECUTION_LANE`, `INTUITION_GATE`, `INTUITION_GATE_RATIONALE`).
  - If `INTUITION_GATE=HUMAN_REQUIRED`, record PM/CEO acknowledgment before execution commands.
  - Canonical one-glance operator view at startup: `docs/context/init_execution_card_latest.md`.
  - Writes:
    - `docs/context/init_execution_card_latest.md`
    - `docs/context/round_contract_seed_latest.md`
    - `docs/context/startup_intake_latest.json`
    - `docs/context/startup_intake_latest.md`
- **Current initialization**: `python scripts/startup_codex_helper.py --repo-root .`
- **Current loop cycle**: `python scripts/run_loop_cycle.py --repo-root . --skip-phase-end`
- **Loop supervision (single-cycle health check)**: `python scripts/supervise_loop.py --repo-root . --max-cycles 1`
- **Loop supervision (continuous monitor)**: `python scripts/supervise_loop.py --repo-root . --max-cycles 999 --check-interval-seconds 300`
- **Current procedures**: See `OPERATOR_LOOP_GUIDE.md` for the full startup -> loop -> closure -> takeover workflow.

## 1b. Current-Head Handoff Notes
- **Test-count rule**: historical handoffs may cite `303 passed` (Stream 2 merge-gate snapshot) or `308 passed` (post-blocker / pre-hardening baseline). For current `HEAD`, always quote a freshly rerun repo-wide `pytest` count and record the run date plus interpreter used, rather than reusing a prior total.
- **Phase-end integrity**: the fail-closed validator pass is already landed (`validate_orphan_changes.py`, `validate_dispatch_acks.py`); do not track it as an open TODO.
- **Phase-end coverage**: real PowerShell orchestration coverage now exists, including a non-`--skip-phase-end` path; production-path coverage is still partly stubbed in tests and should be described that way in handoffs.
- **Environment note**: prefer `.venv\Scripts\python` when available, but if `.venv` is absent the active compatible interpreter is acceptable as long as the handoff records which interpreter was used.

## 1a. Big-Change Manifest First (Pragmatic SOP)
- **When required**: cross-module, architecture-impacting, or high-risk/one-way changes.
- **Create manifest from template**:
  - `Copy-Item docs/templates/change_manifest_template.md docs/context/change_manifest_latest.md`
- **Review before coding**:
  - map proposal to `docs/logic_spine_index.md` (`SpineID`)
  - declare explicit module boundaries and non-goals
  - keep orchestrator/principal in governance mode only (no code/review execution)
- **Policy reference**: `docs/pragmatic_sop.md`

## 1a2. High-Semantic-Risk Falsification Pack (Repo-Init Truth Protocol)
- **When required**: domain meaning is ambiguous/high-impact and could be wrong even if implementation appears structurally correct.
- **Create pack from template**:
  - `Copy-Item docs/templates/domain_falsification_pack.md docs/context/domain_falsification_pack_latest.md`
- **Use before coding in those cases**:
  - test plausible counterexamples and document a `HOLD|REFRAME|PROCEED` verdict.
- **Policy reference**: `docs/repo_init_truth_protocol.md`
- **Authority note**: does not add any new decision authority.
- **Closure note**: if the active round contract sets `DOMAIN_FALSIFICATION_REQUIRED=YES`, closure runs a structural `domain_falsification_gate` before escalation.

## 1a3. Advisory Optimality Review Brief
- **When required**: high-impact, one-way, cross-module, architecture-affecting, or semantic-heavy decisions.
- **Create brief from template**:
  - `Copy-Item docs/templates/optimality_review_brief.md docs/context/optimality_review_brief_latest.md`
- **Keep it lean**:
  - capture top-level semantic tradeoffs only (max 2-3)
  - compare at most `2-3` real options in the same brief
  - include `PRIMARY_OBJECTIVE`, `TOP_LEVEL_TRADEOFFS`, `OPTION_SET`, `RECOMMENDED_OPTION`, `RECOMMENDED_BALANCE`, `WHAT_WOULD_FLIP_DECISION`
  - if comparison is not honest yet, explicitly write `I don't know yet` and name the missing evidence or expert lane
- **Policy reference**: `docs/optimality_review_protocol.md`
- **Roadmap reference**: `docs/minimal_optimality_roadmap.md`
- **Authority note**: advisory only; no new control-plane authority.

## 1a4. Advisory Milestone Optimality Review
- **When required**: milestone close for a major architecture, workflow, or operating-model wave.
- **Reuse the same template**:
  - `Copy-Item docs/templates/optimality_review_brief.md docs/context/milestone_optimality_review_latest.md`
- **Optional repo-root one-screen mirror**:
  - Create or update `MILESTONE_OPTIMALITY_REVIEW_LATEST.md` as a convenience-only repo-root mirror sourced from `docs/context/milestone_optimality_review_latest.md`.
  - Keep `MILESTONE_OPTIMALITY_REVIEW_LATEST.md` as a thin PM summary only; `docs/context/milestone_optimality_review_latest.md` remains the authoritative source.
  - Mirror family convention: convenience-only, intentionally thin, and no gate or authority change.
- **Fill the milestone-close addendum only once per milestone**:
  - `MILESTONE_ID`, `SHAPE_DELTA`, `KEEP_THIS_SHAPE_TODAY`, `TOP_2_REGRETS_IF_WRONG`, `WHAT_TO_REMOVE_NEXT`, `EVIDENCE_PATHS`
  - if the milestone is still too fresh to judge honestly, explicitly write `I don't know yet`
- **Optional R4 elegance / entropy snapshot in the same brief**:
  - `CONCEPT_SURFACE_DELTA`, `INTERFACE_SURFACE_DELTA`, `BOUNDARY_CROSSINGS_DELTA`, `FUTURE_EDIT_SURFACE`
  - `BIGGEST_SIMPLIFIER`, `BIGGEST_ENTROPY_RISK`, `ENTROPY_VERDICT`
  - use `I don't know yet` when integration is too fresh or the future edit surface is not yet observable honestly
- **Keep it lean**:
  - top-level only; no code-trivia replay
  - proxy-based only; do not invent a scoring engine
  - advisory only; no new gate and no new authority path

## 1a5. Advisory Shipped Outcome Feedback
- **When required**: after a shipped wave, rollback event, or meaningful post-merge learning update.
- **Capture outcome into the existing corpus**:
  - `.venv\Scripts\python scripts/capture_profile_outcome_record.py --repo-root . --project-profile "<project_profile>" --shipped "<true|false>" --rollback-status "<NO|PARTIAL|FULL>" --followup-changes-within-30d "<0+>" --semantic-issue-detected-after-merge "<NONE|PRESENT|I don't know yet>" --postmortem-note "<short_postmortem_note>"`
- **Keep it lean**:
  - capture once at known outcome, then optionally once again around 30 days
  - explicitly write `I don't know yet` if semantic outcome is still unclear
  - advisory only; no new gate and no new authority path
- **Policy reference**: `docs/shipped_outcome_feedback_protocol.md`

## 1a6. Advisory Thesis Pull
- **When allowed**: only when SOP is active in another repo or fresh real operating evidence exists there.
- **Required mix**:
  - local data-driven evidence from that repo is primary
  - combine it with `1-3` academic inputs only
  - include one explicit realm-specific repo lens
- **Research handling**:
  - classify each academic input as `SUPPORTS`, `CANDIDATE`, `FRONTIER`, or `NOT_ACTIONABLE`
  - use research to sharpen or challenge the local evidence, not replace it
- **Outcome discipline**:
  - thesis pulls may suggest `NO_CHANGE`, `WATCH`, or `HUMAN_REVIEW_HEURISTIC_UPDATE`
  - no automatic policy mutation; any philosophy or heuristic update requires explicit human review and a separate docs change
- **Artifacts**:
  - template: `docs/templates/thesis_pull_template.md`
  - authoritative working copy: `docs/context/thesis_pull_latest.md`
  - convenience-only thin mirror: `THESIS_PULL_LATEST.md`
- **Authority note**:
  - `docs/context/thesis_pull_latest.md` remains authoritative
  - `THESIS_PULL_LATEST.md` is intentionally thin and does not add a new gate or authority path
- **Policy reference**: `docs/thesis_pull_protocol.md`

## 1b. Startup Quickstart (Context Bootstrap)
- **Build Context Artifacts**: `.venv\Scripts\python scripts/build_context_packet.py`
- **Invoke Context Bootstrap Skill**: `invoke $context-bootstrap`
- **Validate Context Artifacts**: `.venv\Scripts\python scripts/build_context_packet.py --validate`
- **Gemini Handover Artifact**: `docs/handover/gemini/phase<NN>_gemini_handover.md` (auto-generated by `build_context_packet.py`)

## 1c. Philosophy Local-First Sync
- **Sync worker loops first, then migrate to SOP main**:
  - `.venv\Scripts\python scripts/sync_philosophy_feedback.py --scan-root E:\Code --main-repo E:\Code\SOP\quant_current_scope`
- **Scoped explicit workers (recommended when scan tree is large)**:
  - `.venv\Scripts\python scripts/sync_philosophy_feedback.py --main-repo E:\Code\SOP\quant_current_scope --worker-repo E:\Code\Film --worker-repo E:\Code\Quant --worker-repo E:\Code\atomic-mesh-ui-sandbox --worker-repo E:\Code\aa_vibe\athlete-ally-original`
- **Expected outputs**:
  - `docs/context/philosophy_migration_log.json`
  - `docs/context/philosophy_migration_report.md`
- **Fail-closed contract**:
  - if any worker local-loop update fails, migration status is `BLOCK` and main `docs/lessonss.md` is not updated.

## 1d. Next-Round Handoff Quick Guide
- **Purpose**: use the latest loop artifacts to generate and surface an advisory next-round kickoff packet before the next execution cycle.
- **Primary artifacts**:
  - `docs/context/next_round_handoff_latest.json`
  - `docs/context/next_round_handoff_latest.md`
- **Possible root convenience mirrors (when present)**:
  - `NEXT_ROUND_HANDOFF_LATEST.md`
  - `EXPERT_REQUEST_LATEST.md`
  - `PM_CEO_RESEARCH_BRIEF_LATEST.md`
  - `BOARD_DECISION_BRIEF_LATEST.md`
  - These repo-root files are optional convenience copies for paste-ready operator flow only; `docs/context/*` remains authoritative.
- **How to use it**:
  - Run one loop refresh so the latest closure, memory, and handoff artifacts are regenerated.
  - Print the takeover entrypoint so the advisory handoff is surfaced alongside the normal closure artifacts.
  - Use the handoff to prefill next-round thinking only; then immediately run the startup helper and revalidate intent, scope, risk, and acknowledgments before execution.
- **Authority rule**:
  - `next_round_handoff_latest.*` is advisory only.
  - `startup_codex_helper.py`, the startup card, and the source-of-truth hierarchy remain authoritative.
  - If the generated handoff conflicts with same-day startup intake, startup intake wins.
- **Single recommended command sequence**:
  - `.venv\Scripts\python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true; .venv\Scripts\python scripts/print_takeover_entrypoint.py --repo-root .; .venv\Scripts\python scripts/startup_codex_helper.py --repo-root .`
- **Expected operator outcome**:
  - `run_loop_cycle.py` refreshes `exec_memory_packet_latest.*` and `next_round_handoff_latest.*`.
  - `print_takeover_entrypoint.py` prints the advisory handoff when present and reminds operators about the repo-root mirror filenames.
  - `startup_codex_helper.py` converts that advisory context into the authoritative next-round startup packet.

## 2. Data Management
- **Legacy price refresh note**: The data updater entrypoint no longer exists in this repo. Data-pipeline refresh commands are not currently part of the active control-plane workflow.
- **Legacy universe hydration note**: Broad market-data hydration is not currently present in this repo surface.
- **Update Fundamentals**: `python data/fundamentals_updater.py --scope "Top 500"`
- **Build Feature Store (Incremental default)**: `python data/feature_store.py --start-year 2000 --universe-mode yearly_union --yearly-top-n 100`
- **Build Feature Store (Forced full rebuild)**: `python data/feature_store.py --start-year 2000 --full-rebuild`
- **Rebuild Sector Map**: `python data/build_sector_map.py`

## 3. Testing
- **Run All Tests**: `pytest`
- **Run Data Layer Tests**: `pytest tests/test_updater_parallel.py tests/test_feature_store.py tests/test_parallel_utils.py`
- **Run Data Validation Gate**: `python scripts/validate_data_layer.py`

## 4. Baseline Benchmarking (Phase 18 Day 1)
- **Run Baseline Report**: `.venv\Scripts\python scripts/baseline_report.py --start-date 2015-01-01 --end-date 2024-12-31 --cost-bps 5 --trend-risk-off-weight 0.5`
- **Output CSV (default)**: `data/processed/phase18_day1_baselines.csv`
- **Output Plot (default)**: `data/processed/phase18_day1_equity_curves.png`
- **Path Resolution Note**: relative CLI paths in `scripts/baseline_report.py` are resolved against repo root (`E:\Code\Quant`), not the caller working directory. Use absolute paths if external schedulers need other destinations.

## 4b. TRI Migration (Phase 18 Day 2)
- **Build TRI prices artifact**: `.venv\Scripts\python data/build_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --output data/processed/prices_tri.parquet --validation-csv data/processed/phase18_day2_tri_validation.csv --split-plot data/processed/phase18_day2_split_events.png`
- **Build macro TRI artifact**: `.venv\Scripts\python data/build_macro_tri.py --start-date 2015-01-01 --end-date 2024-12-31 --input data/processed/macro_features.parquet --output data/processed/macro_features_tri.parquet`
- **Primary Day 2 outputs**:
  - `data/processed/prices_tri.parquet`
  - `data/processed/macro_features_tri.parquet`
  - `data/processed/phase18_day2_tri_validation.csv`
  - `data/processed/phase18_day2_split_events.png`

## 4c. Cash Overlay Benchmarking (Phase 18 Day 3)
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

## 4d. Company Scorecard Validation (Phase 18 Day 4)
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

## 4e. Day 5 Ablation Matrix (Phase 18 Day 5)
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

## 4f. Day 6 Walk-Forward Validation (Phase 18 Day 6)
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
  - if either value is `> 0`, treat run as **data-quality warning** and do not promote as hard-pass without explicit acknowledgment.
- **Matrix safety control**:
  - default `--max-matrix-cells 25000000`
  - if raised, confirm memory headroom and record override in run notes.

## 4g. Stop-Loss Module Validation (Phase 21 Day 1)
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

## 4h. SDM 3-Pillar Ingestion + Assembly (Phase 23)
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

## 5. Emergency / Troubleshooting
- **Clear Cache**: Delete `data/processed/*.parquet` (Safe, will trigger redownload).
- **Force Rebuild**: Delete `data/processed/fundamentals_snapshot.parquet` to force a clean snapshot generation.

## 6. Closed Loop Operations (Phase 24+)
These scripts enforce the closed architecture. Add `--dry-run` to any command for a zero-write execution.

- **One-Click Phase-End (fail-closed, recommended)**:
  `powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoRoot .`
  - First-time bootstrap (create minimal required files/dirs):
    - `powershell -ExecutionPolicy Bypass -File scripts/bootstrap_repo_profile.ps1 -RepoProfile Quant`
    - `powershell -ExecutionPolicy Bypass -File scripts/bootstrap_repo_profile.ps1 -RepoProfile Film`
    - bootstrap now defaults to `-EnsureMinimalContext $true` and auto-runs `build_context_packet.py` + `--validate` to generate:
      - `docs/context/current_context.json`
      - `docs/context/current_context.md`
      - `docs/handover/gemini/phase<NN>_gemini_handover.md`
    - add `-WithContextSkeleton` when initializing a brand new repo to force-create missing context source docs (`phase0` brief/handover + decision log + lessons + `top_level_PM.md`).
    - add `-SkipContextBuild` only when intentionally deferring context artifact generation.
    - add `-Force` to overwrite scaffold files.
  - Profile mode (auto defaults for repo paths):
    - `powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoProfile Quant`
    - `powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoProfile Film`
    - profile/default `scan_root` is now pinned to `<repo>/docs` to avoid `tmp/e2e_test` false escalations.
  - New repo note:
    - before first git baseline commit, run with `-SkipOrphanGate` (or provide `-SinceCommit <commit>` explicitly after commit exists).
  - Explicit argument always overrides profile defaults (for local exceptions):
    - `powershell -ExecutionPolicy Bypass -File scripts/phase_end_handover.ps1 -RepoProfile Quant -TraceabilityPath docs/context/pm_to_code_traceability.yaml -DispatchManifestPath docs/context/dispatch_manifest.json -ScanRoot docs`
  - On any gate failure, run exits non-zero and writes:
    - `docs/context/phase_end_logs/phase_end_handover_status_<run_id>.json`
    - `docs/context/phase_end_logs/phase_end_handover_summary_<run_id>.md`
  - `failed_gate` + gate-specific `.log` path are included for immediate triage.
  - `G00_preflight` blocks early when required paths are missing before running the Python gates.
- **0. Worker Reply Packet Scaffold (one-time per repo)**:
  `Copy-Item docs/context/schemas/worker_reply_packet.json.template docs/context/worker_reply_packet.json`
  - Template is now v2.0.0 (includes `machine_optimized` and `pm_first_principles` blocks).
- **1. Status Aggregation & Escalation**:
  `.venv\Scripts\python scripts/aggregate_worker_status.py --scan-root docs --output docs/context/worker_status_aggregate.json --escalation-output docs/context/escalation_events.json`
- **2. Traceability Alignment Gate**:
  `.venv\Scripts\python scripts/validate_traceability.py --input docs/pm_to_code_traceability.yaml --strict --require-test`
- **3. Evidence Hash Anti-Tamper Verification**:
  `.venv\Scripts\python scripts/validate_evidence_hashes.py --input docs/pm_to_code_traceability.yaml --evidence-dir docs/context/evidence_hashes`
- **4. Gemini Bridge Freshness Gate**:
  `.venv\Scripts\python scripts/validate_digest_freshness.py --input docs/context/ceo_bridge_digest.md --ttl-minutes 60`
- **5. Reverse-Traceability Orphan Gate**:
  `git merge-base HEAD origin/main` (Find since-commit)
  `.venv\Scripts\python scripts/validate_orphan_changes.py --traceability docs/pm_to_code_traceability.yaml --since-commit <COMMIT_HASH>`
- **6. Dispatch ACK & Lifecycle Verification**:
  `.venv\Scripts\python scripts/validate_dispatch_acks.py --manifest docs/context/dispatch_manifest.json --scan-root docs --timeout-minutes 10`
- **7. Worker Reply Confidence/Citation Gate**:
  `.venv\Scripts\python scripts/validate_worker_reply_packet.py --input docs/context/worker_reply_packet.json --repo-root . --require-existing-paths`
  - Worker reply packets declare their own `schema_version`. The validator auto-detects v1.0.0 vs v2.0.0 rules.
  - Use `--schema-version-override 2.0.0` to force strict v2 enforcement (v2 requires `machine_optimized` and `pm_first_principles` blocks).
  - Use `--enforce-score-thresholds` to enable hard threshold enforcement: confidence >= 0.70, relatability >= 0.75, triad coverage (principal/riskops/qa present), and triad substantive quality (at least one triad domain APPLIED or NOT_REQUIRED).
  - **Bootstrap incompatibility rule**: `--enforce-score-thresholds` must NOT be enabled while `worker_reply_packet.json` contains `phase: "phase_bootstrap"` or `worker_id: "@bootstrap"`. Bootstrap packets have placeholder scores (confidence=0.30, relatability=0.0, all-SKIPPED) that will hard-fail threshold enforcement by design. Replace bootstrap packet with real worker output before enabling threshold mode.
- **8. Build CEO Bridge Digest**:
  `.venv\Scripts\python scripts/build_ceo_bridge_digest.py --sources docs/context/worker_status_aggregate.json,docs/pm_to_code_traceability.yaml,docs/context/escalation_events.json,docs/context/worker_reply_packet.json --output docs/context/ceo_bridge_digest.md`
  - Digest v2.0.0 sections: I. First Principles Engineering Summary, II. Strategic Expertise Coverage, III. System Health, IV. Expert Verdict Matrix, V. Traceability Summary, VI. Recent Completions, VII. Active Escalations, VIII. Worker Confidence and Citations, X. Per-Round Score Gates, XI. Recommended PM Actions.
  - Score Gates section renders GO/HOLD/REFRAME per task based on confidence and relatability thresholds.
  - v1 packets render gracefully ("Not available (v1 packet)" for sections I and II).
- **9. CEO Go-Signal Truth-Check Gate**:
  `.venv\Scripts\python scripts/validate_ceo_go_signal_truth.py --dossier-json docs/context/auditor_promotion_dossier.json --calibration-json docs/context/auditor_calibration_report.json --go-signal-md docs/context/ceo_go_signal.md`
- **10. Build Exec Memory Packet (Phase A integration)**:
  `.venv\Scripts\python scripts/build_exec_memory_packet.py --output-json docs/context/exec_memory_packet_latest.json --output-md docs/context/exec_memory_packet_latest.md --pm-budget-tokens 3000 --ceo-budget-tokens 1800`
- **10a. Exec Memory Truth-Check Gate**:
  `.venv\Scripts\python scripts/validate_exec_memory_truth.py --memory-json docs/context/exec_memory_packet_latest.json --repo-root .`
- **10b. Refresh CEO Weekly Summary (auto-refresh source)**:
  `.venv\Scripts\python scripts/generate_ceo_weekly_summary.py --dossier-json docs/context/auditor_promotion_dossier.json --calibration-json docs/context/auditor_calibration_report.json --go-signal-md docs/context/ceo_go_signal.md --output docs/context/ceo_weekly_summary_latest.md`
- **10c. CEO Weekly Summary Truth-Check Gate**:
  `.venv\Scripts\python scripts/validate_ceo_weekly_summary_truth.py --weekly-md docs/context/ceo_weekly_summary_latest.md --dossier-json docs/context/auditor_promotion_dossier.json --calibration-json docs/context/auditor_calibration_report.json`
- **10d. TDD Contract Evidence (mandatory before closure gate)**:
  - Open the active round contract and complete:
    - `TDD_MODE`
    - `RED_TEST_COMMAND`
    - `RED_TEST_RESULT`
    - `GREEN_TEST_COMMAND`
    - `GREEN_TEST_RESULT`
    - `REFACTOR_NOTE`
    - `TDD_NOT_APPLICABLE_REASON` (required when `TDD_MODE=NOT_APPLICABLE`)
  - Mode rule:
    - code-changing round => `TDD_MODE=REQUIRED`
    - non-code round => `TDD_MODE=NOT_APPLICABLE` + explicit reason
  - Auditor must confirm TDD evidence before running closure.
- **10e. Refactor/Mock Policy Gate (required)**:
  `.venv\\Scripts\\python scripts/validate_refactor_mock_policy.py --round-contract-md docs/context/round_contract_latest.md`
- **10f. Review Checklist Gate (optional, runs only when checklist artifact exists)**:
  `.venv\\Scripts\\python scripts/validate_review_checklist.py --input docs/context/pr_review_checklist_latest.md`
- **10g. Interface Contract Gate (optional, runs only when manifest artifact exists)**:
  `.venv\\Scripts\\python scripts/validate_interface_contracts.py --manifest-json docs/context/interface_contract_manifest_latest.json`
- **11. Single Closure Gate**:
  `.venv\Scripts\python scripts/validate_loop_closure.py --repo-root .`
  - `READY_TO_ESCALATE` requires `docs/context/ceo_go_signal.md` to contain `- Recommended Action: GO` (`go_signal_action_gate`).
  - `READY_TO_ESCALATE` also requires closure check `tdd_contract_gate=PASS`.
  - `READY_TO_ESCALATE` also requires `exec_memory_packet_latest.json` artifact present.
  - If recommended action is `HOLD` or `REFRAME`, closure result is `NOT_READY` (exit code `1`) even when truth-check scripts pass.
- **12. One-Command Cycle Runner**:
  `.venv\Scripts\python scripts/run_loop_cycle.py --repo-root .`
  - Revalidation-only pass (skip phase-end): `.venv\Scripts\python scripts/run_loop_cycle.py --repo-root . --skip-phase-end`
  - Default hold reporting semantics: `--allow-hold true` remaps expected `refresh_dossier` criteria shortfall and closure `NOT_READY` from `FAIL` to `HOLD` in cycle summary (`final_result=HOLD`, exit code `0`).
  - Disable hold mode with `--allow-hold false` to keep those steps as `FAIL` and preserve non-zero cycle exit behavior.
  - Cycle now includes `refresh_ceo_weekly_summary` step after `generate_ceo_go_signal`.
  - Cycle now includes `build_exec_memory_packet` step after `refresh_ceo_weekly_summary`.
  - Cycle now includes `validate_exec_memory_truth` step after `validate_ceo_weekly_summary_truth` and before `validate_loop_closure`.
  - Cycle now includes `validate_refactor_mock_policy` (required), plus conditional `validate_review_checklist` and `validate_interface_contracts` (SKIP when optional artifacts are absent).
- **12a. Supervisor Loop (Closed-Loop Watch)**:
  - One-cycle example: `.venv\\Scripts\\python scripts/supervise_loop.py --repo-root . --max-cycles 1 --check-interval-seconds 0`
  - Watch-mode example: `.venv\\Scripts\\python scripts/supervise_loop.py --repo-root . --max-cycles 999999 --check-interval-seconds 60`
  - Supervisor outputs:
    - `docs/context/supervisor_status_latest.json`
    - `docs/context/supervisor_alerts_latest.md`
- **Generated latest-pointer artifacts**:
  - `docs/context/loop_cycle_summary_latest.json`
  - `docs/context/loop_cycle_summary_latest.md`
  - `docs/context/loop_closure_status_latest.json`
  - `docs/context/loop_closure_status_latest.md`
  - `docs/context/lessons_worker_latest.md`
  - `docs/context/lessons_auditor_latest.md`
  - `docs/context/round_contract_seed_latest.md`
  - `docs/context/exec_memory_packet_latest.json`
  - `docs/context/exec_memory_packet_latest.md`

### Cutover Readiness Gate (Phase 24B prerequisite)
Before enabling `-EnforceScoreThresholds` in `phase_end_handover.ps1`, validate all active repos:
```
python scripts/validate_worker_reply_packet.py --input docs/context/worker_reply_packet.json --repo-root . --schema-version-override 2.0.0 --enforce-score-thresholds
```
- Run for: SOP repo, Quant repo (`E:\Code\Quant`), Film repo (`E:\Code\Film`).
- All must exit 0 before enabling `-EnforceScoreThresholds` in `phase_end_handover.ps1`.
- Alternatively, use `-CrossRepoRoots "E:\Code\Quant,E:\Code\Film"` with `-EnforceScoreThresholds` in phase_end_handover.ps1 — G05b gate validates automatically.
- Record results in `docs/context/phase_end_logs/cutover_readiness_v2_<timestamp>.json`.

### Auditor Review (Phase 24C)
Independent auditor gate (G11) reviews worker reply packets and emits structured findings.

**Run auditor manually**:
```
python scripts/run_auditor_review.py --input docs/context/worker_reply_packet.json --repo-root . --output docs/context/auditor_findings.json --mode shadow
```

**Exit codes**: `0` = PASS, `1` = BLOCK (enforce mode, Critical/High findings), `2` = INFRA_ERROR (always blocks).

**Output write contract**: Exit 0 and 1 always write valid JSON. Exit 2 may not.

**Gate verdict interpretation**: `summary.gate_verdict` can be PASS even with CRITICAL/HIGH counts in shadow mode. This is expected — verdict is driven by `blocking` flags, not severity counts.

**Phase-end integration**:
- Default: `-AuditMode shadow` (non-blocking for policy findings, blocks on infra errors).
- Enforce: `-AuditMode enforce` (Critical/High block handover).
- Skip: `-AuditMode none` (G11 SKIPPED, no auditor source passed to digest).

**Promotion gate (shadow → enforce)** — all 5 conditions must be met:
1. Phase 24B operational close complete (real worker packet, cross-repo readiness, one successful enforced run).
2. Minimum 30 audited items across ≥ 2 consecutive weekly windows.
3. Critical+High false-positive rate < 5% (formula: false_positives among C/H findings / total C/H findings).
4. Explicit signoff by PM or designated owner in decision log.
5. All packets must be `schema_version=2.0.0` (enforce mode rejects v1 packets via AUD-R000 HIGH + blocking).

### Weekly Metrics Reference
Manual derivation one-liners for CEO weekly review KPIs:
- **Rework Rate**: `python -c "import json; p=json.load(open('docs/context/worker_reply_packet.json')); items=[i for i in p['items'] if i['dod_result'] in ('PARTIAL','FAIL')]; print(f'{len(items)/len(p[\"items\"])*100:.1f}%')"` — compare across consecutive packets for same task_id within current phase
- **False-Pass Rate**: count items with `dod_result=PASS` in worker packet that later received `SAW Verdict: BLOCK` or failed a phase-end gate in `logs/` — divide by total PASS items
- **Time-to-Decision**: `dispatch_manifest.json` → `dispatched_utc` vs `worker_reply_packet.json` → `generated_at_utc` — compute per-item delta in hours, report median
- **Expertise Coverage %**: `python -c "import json; p=json.load(open('docs/context/worker_reply_packet.json')); triad={'principal','riskops','qa'}; covered=[i for i in p['items'] if all(any(e['domain']==d and e['verdict']=='APPLIED' for e in i.get('machine_optimized',{}).get('expertise_coverage',[])) for d in triad)]; print(f'{len(covered)/len(p[\"items\"])*100:.1f}%')"` — count items where all 3 triad domains have `verdict=APPLIED`

## 7. Manual Capture Alert Protocol
Workers must handle missing visual evidence according to the strict E2E capture policy:
- **Scope**: E2E Evidence MUST be a `REAL_CAPTURE` containing the actual state of web sessions or CommandPlan round-trip payloads.
- **Rules of Engagement**: E2E Workers CANNOT simulate or render substitute images to bypass missing captures. 
- **Action**: When missing captures are blocked by the CI `validate_traceability` equivalent or E2E audit, the Worker MUST trigger a notification to the User directly containing:
  - Task ID (e.g. `T12`)
  - Capture Context (e.g. "Missing CEO Commandpaste Visual proof from Gemini")
  - Acceptable Naming Protocol (e.g. `e2e_evidence/T12_manual1_ceo_paste_timestamp.png`)
  - Timeout Deadline (15min Warning / 30min Critical `BLOCK`)

## 7b. Manual Capture Drop Zone Loop (Desktop Shortcut + Worker Polling)
Use this loop to keep user interaction minimal while preserving strict evidence integrity:

- **One-time setup (create desktop drop shortcut)**:
  - `powershell -ExecutionPolicy Bypass -File scripts/setup_manual_capture_dropzone.ps1`
- **Worker watch mode (polling)**:
  - `.venv\Scripts\python scripts/manual_capture_watcher.py --watch --interval-seconds 10 --warn-minutes 15 --block-minutes 30`
- **One-shot evaluation (CI/manual run)**:
  - `.venv\Scripts\python scripts/manual_capture_watcher.py --fail-on-block`
- **Dry-run (no writes)**:
  - `.venv\Scripts\python scripts/manual_capture_watcher.py --dry-run --print-json`

Runtime behavior:
- User drops capture files into `Desktop/Evidence_Drop`.
- Worker validates extension/header/size and copies accepted files into `e2e_test/docs/context/e2e_evidence/`.
- Worker automatically updates:
  - `e2e_test/docs/context/e2e_evidence/index.md`
  - `e2e_test/docs/context/e2e_evidence/manual_capture_queue.json`
  - `e2e_test/docs/context/e2e_evidence/manual_capture_alerts.json`
- Status transitions:
  - `<15m`: `Machine PASS + Manual Pending`
  - `>=15m`: `WARNED` (reminder event)
  - `>=30m`: `BLOCK` (escalation event)

## 7c. Dual Repo Minimal Setup (No Multi-tenant Overbuild)
Use this when at most two repos are active in parallel.

- **A. Initialize each repo evidence structure (once per repo)**:
  - `powershell -ExecutionPolicy Bypass -File scripts/init_manual_capture_repo.ps1 -RepoRoot E:\Code\Quant -TaskId T12`
  - `powershell -ExecutionPolicy Bypass -File scripts/init_manual_capture_repo.ps1 -RepoRoot E:\Code\Film -TaskId T12`
- **B. Create two dedicated drop zones (avoid route ambiguity)**:
  - `powershell -ExecutionPolicy Bypass -File scripts/setup_manual_capture_dropzone.ps1 -DropDir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop_Quant -ShortcutName "E2E Drop Quant.lnk"`
  - `powershell -ExecutionPolicy Bypass -File scripts/setup_manual_capture_dropzone.ps1 -DropDir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop_Film -ShortcutName "E2E Drop Film.lnk"`
- **C. Register both watcher tasks (logon auto-start)**:
  - `powershell -ExecutionPolicy Bypass -File scripts/register_dual_repo_manual_capture_tasks.ps1 -RepoARoot E:\Code\Quant -RepoADropDir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop_Quant -RepoAName Quant -RepoBRoot E:\Code\Film -RepoBDropDir C:\Users\Lenovo\OneDrive\桌面\Evidence_Drop_Film -RepoBName Film`
- **D. Verify task registration**:
  - `Get-ScheduledTask -TaskName "ManualCapture-*"`

## 8. Auditor Calibration Reporting

### Weekly Calibration Report
Generate weekly FP rate and rule-level statistics for shadow-mode auditor runs:

```bash
python scripts/auditor_calibration_report.py \
  --logs-dir docs/context/phase_end_logs \
  --repo-id quant_current_scope \
  --ledger docs/context/auditor_fp_ledger.json \
  --output-json docs/context/auditor_calibration_report.json \
  --output-md docs/context/auditor_calibration_report.md \
  --mode weekly
```

**Outputs:**
- `docs/context/auditor_calibration_report.json` - Machine-readable report
- `docs/context/auditor_calibration_report.md` - Human-readable summary
- `docs/context/ceo_go_signal.md` - Auto-refreshed during `phase_end_handover.ps1` (fail-open; missing artifacts emit warnings without changing gate verdict)

### Promotion Dossier
Verify all 5 promotion criteria before shadow-to-enforce transition:

```bash
python scripts/auditor_calibration_report.py \
  --logs-dir docs/context/phase_end_logs \
  --repo-id quant_current_scope \
  --ledger docs/context/auditor_fp_ledger.json \
  --output-json docs/context/auditor_promotion_dossier.json \
  --output-md docs/context/auditor_promotion_dossier.md \
  --mode dossier \
  --min-items 30 \
  --min-items-per-week 10 \
  --min-weeks 2 \
  --max-fp-rate 0.05
```

**Exit codes:**
- `0` = All automated criteria met (C0, C2-C5)
- `1` = One or more criteria not met
- `2` = Infra error (bad ledger, missing dir)

### FP Annotation Workflow
1. Review C/H findings in `docs/context/phase_end_logs/auditor_findings_<run_id>.json`
2. Annotate each C/H finding in `docs/context/auditor_fp_ledger.json`:
   ```json
   {
     "repo_id": "quant_current_scope",
     "run_id": "20260301_120000",
     "finding_id": "AUD-001",
     "verdict": "TP",
     "annotated_by": "username",
     "annotated_at_utc": "2026-03-01T13:00:00Z",
     "notes": "Confirmed low confidence"
   }
   ```
3. Run weekly report to track annotation coverage

### Time Filtering
Filter runs by audit timestamp (useful after schema version upgrades):

```bash
python scripts/auditor_calibration_report.py \
  --logs-dir docs/context/phase_end_logs \
  --repo-id quant_current_scope \
  --output-json docs/context/auditor_calibration_report_filtered.json \
  --output-md docs/context/auditor_calibration_report_filtered.md \
  --from-utc 2026-03-03T00:00:00Z \
  --to-utc 2026-03-17T00:00:00Z
```

## 9. Shadow-to-Enforce Operational Workflow

### 10-Step Promotion Procedure

**1. Freeze + Tag**
```bash
git tag phase24c-shadow-ready
git push origin phase24c-shadow-ready
```

**2. Archive Baseline**
Create snapshot of pre-shadow state (PowerShell):
```powershell
New-Item -ItemType Directory -Force -Path docs\context\phase24c_baseline
Copy-Item docs\context\phase_end_logs\*.json docs\context\phase24c_baseline\
Copy-Item docs\context\auditor_calibration_report.md docs\context\phase24c_baseline\
Copy-Item docs\context\ceo_bridge_digest.md docs\context\phase24c_baseline\
```

**3. Weekly Shadow Runs**
Run phase-end with `-AuditMode shadow` across all repos for 2+ weeks:
```powershell
.\scripts\phase_end_handover.ps1 -AuditMode shadow
```

**4. FP Annotation**
After each run, annotate all C/H findings in `auditor_fp_ledger.json` (see Section 8).

**5. Weekly Calibration Reports**
Generate weekly reports to track FP rate trends:
```bash
python scripts/auditor_calibration_report.py --mode weekly ...
```

**6. Close 24B Prerequisites**
- Replace bootstrap packet with real worker reply
- Verify cross-repo readiness
- Run one enforce-mode auditor cycle to validate blocking behavior (findings will block if C/H present)

**7. Promotion Dossier**
When ready, generate dossier and verify all criteria:
```bash
python scripts/auditor_calibration_report.py --mode dossier ...
```
Expected: Exit 0, all criteria met (C0-C5).

**8. Canary Enforce**
Enable enforce mode on one repo for 3-5 cycles:
```powershell
.\scripts\phase_end_handover.ps1 -AuditMode enforce
```
Monitor for false positives and policy blocks.

**9. Full Enforce Rollout**
After canary success, enable enforce across all repos.

**10. Rollback (if needed)**
Revert to shadow mode (findings still visible in digest):
```powershell
.\scripts\phase_end_handover.ps1 -AuditMode shadow
```
