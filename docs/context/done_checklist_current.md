# Done Checklist — External Readiness 6-Phase Sprint
Generated: 2026-03-31
Phase: external-readiness-sprint-2026-03-31

## C-1: Phase 1 — Audit Log
- [x] test_audit_log_emitted_on_governance_decision passes
- [x] test_metrics_export_schema_valid passes
- [x] sop audit CLI subcommand present in __main__.py
- [x] emit_audit_log wired at 3 call sites in run_loop_cycle.py (step, gate_a, gate_b)
- [x] write_audit_metrics called after every run
- [x] audit_log.ndjson written after sop run
- [x] audit_metrics_latest.json written after sop run

## C-2: Phase 2 — Policy Engine
- [x] src/sop/_policy_engine.py exists with PolicyResult, load_policy_rules, evaluate_policy
- [x] docs/policy_rules_default.json exists with valid rule schema (ALLOW + shadow BLOCK)
- [x] sop policy validate subcommand present in __main__.py
- [x] --policy-shadow-mode flag wired in run_loop_cycle.py parse_args() and sop run subparser
- [x] test_policy_engine_blocks_on_violation passes
- [x] test_shadow_mode_does_not_block passes
- [x] test_policy_violation_appears_in_audit_log passes
- [x] test_policy_validate_cli_valid_rules passes

## C-3: Phase 3 — API/SDK
- [x] src/sop/_client.py exists with GovernanceClient (run, audit, status, policy_validate)
- [x] from sop import GovernanceClient works (editable install confirmed)
- [x] docs/api/openapi.yaml exists with /run, /audit, /policy/validate, /status paths
- [x] pyproject.toml version bumped to 0.2.0
- [x] src/sop/__init__.py __version__ = "0.2.0"
- [x] CHANGELOG.md has 0.2.0 entry
- [x] test_governance_client_run_returns_summary_dict passes
- [x] test_governance_client_audit_returns_list passes
- [x] test_governance_client_status_returns_dict passes
- [x] test_openapi_spec_validates passes

## C-4: Phase 4 — Containers
- [x] Dockerfile exists: multi-stage, non-root user sop, python:3.12-slim pinned in both stages
- [x] Dockerfile: pip install --prefix=/install . (full package, not deps-only)
- [x] .dockerignore exists
- [x] docker-compose.yml exists with .:/workspace mount (not ./docs only)
- [x] charts/terminal-zero-governance/Chart.yaml exists with name, version, appVersion
- [x] charts/terminal-zero-governance/templates/job.yaml has restartPolicy: Never
- [x] charts/terminal-zero-governance/values.yaml exists
- [x] sop healthcheck subcommand present, exits 0 on clean install, no required args
- [x] .github/workflows/container-smoke.yml exists with working-directory: quant_current_scope
- [x] test_dockerfile_exists_and_has_non_root_user passes
- [x] test_helm_chart_yaml_valid passes

## C-5: Phase 5 — Documentation
- [x] docs/getting-started.md exists: pip install, sop init, sop run, sop audit, sop validate (5-step, no sop startup)
- [x] docs/architecture.md exists: ASCII diagram marker, audit_log, gate, run_loop_cycle
- [x] docs/api-reference.md exists
- [x] docs/examples/cicd-pipeline-governance.md exists
- [x] docs/context/README.md extended with Phase 1/2/3 artifacts in classification table
- [x] README.md has single Quickstart section near top, Documentation section with links
- [x] test_getting_started_covers_key_steps passes
- [x] test_architecture_md_has_component_overview passes
- [x] test_context_readme_separates_generated_vs_canonical passes

## C-6: Phase 6 — Integration Tests & Benchmarks
- [x] tests/test_governance_scenarios.py exists with 3 scenario tests
- [x] test_governance_scenario_agent_blocked passes (SHADOW_BLOCK in audit log)
- [x] test_governance_scenario_audit_trail_complete passes (executed steps <= audit entries)
- [x] test_governance_scenario_retry_loop_increments_attempt_id passes (trace_id differs across runs)
- [x] tests/test_policy_engine_benchmarks.py exists with 3 benchmark tests (win32-skip)
- [x] test_policy_evaluation_latency_p50_p95_p99 collected (skipped on Windows by design)
- [x] test_failure_detection_rate collected (skipped on Windows by design)
- [x] test_benchmark_regression_guard collected (skipped on Windows by design)
- [x] docs/benchmarks.md added to .gitignore
- [x] .github/workflows/integration-benchmarks.yml exists (Linux only, uploads artifact)

## C-7: Full Suite Regression
- [x] 99 tests across Phase 1-6 acceptance gate files: 0 failures
- [x] 87 tests (Phase 1-2): passed
- [x] 9 tests (Phase 3-5): passed
- [x] 3 tests (Phase 6 scenarios): passed
- [x] No regressions introduced by external readiness sprint

## C-8: Truth Surfaces Current
- [x] planner_packet_current.md updated for external-readiness-sprint-2026-03-31
- [x] done_checklist_current.md updated (this file)
- [x] bridge_contract_current.md updated
- [x] observability_pack_current.md updated — no active drift markers
- [x] closure_packet_external_readiness_sprint.md written
