# Done Checklist — Phase 6 Post-Hardening Integration
Generated: 2026-03-30
Phase: phase-6-post-hardening-integration

## Phase 6 Acceptance Gates
- [x] Track 1: artifact_refs entries contain hash, content_kind, hash_strategy; mtime_utc still present
- [x] Track 2: error_code_registry.json committed (E001-E007, all failure_class values mapped)
- [x] Track 2: decision_basis_count present in every gate_decisions[] entry (tests pass)
- [x] Track 2: schema version policy CI check green (10 schemas checked, all declare schema_version)
- [x] Track 3: 0 real test failures — test_run_loop_cycle_skip_phase_end_success_and_overdue_ledger_flag passes
- [x] Track 3: scoped suite 0 skips on test_hardening.py (81 collected, 81 pass)
- [x] Track 4: skills_status ACTIVE achievable in CI via skill pilot (.sop_config.yaml active_skills present)
- [x] Track 4: loop_readiness_latest.json shows routing: skills_active when skill active
- [x] Track 5: attempt_id increments on retry (TestRetryLoop 3/3 pass)
- [x] Track 6: evaluation_outcome_source correctly set (TestEvaluationOutcomeSource 8/8 pass)
- [x] Scoped suite green: pytest tests/test_hardening.py tests/test_checklist_matrix.py tests/test_cli_script_parity.py -q — 117 passed, 1 skipped (test_run_output_parity by design)
- [x] No new regressions introduced by Phase 6 tracks
- [x] check_fail_open.py still passes; no new BLOCKERs

## Phase 7 Sprint Closure Gate
- [x] Phase 7 plan created: docs/plans/phase_7_sprint_closure.plan.md
- [x] All phases 2-6 complete
- [x] C-1: scoped test suite 0 failures, 1 expected skip (by design)
- [x] C-2: failure artifact contract verified (run_failure_latest.json on hard failures; error_code_registry E001-E007)
- [x] C-3: CI jobs present in release-validation.yml (cli-smoke, backward-compat, test-suite, release-gate, golden-path, preflight-failure-detection, shadowed-module-smoke) and fast-checks.yml
- [x] C-4: artifact integrity (hash/content_kind/hash_strategy, decision_basis_count, attempt_id, evaluation_outcome_source all tested and passing)
- [x] C-5: navigation + boundary clean (zero absolute paths in operator docs; Template Canonical Sources in README.md; KERNEL_ACTIVATION_MATRIX.md as onboarding step 1; sop run/sop validate commands valid)
- [x] C-6: skills_status ACTIVE; loop_readiness_latest.json routing=skills_active; check_loop_readiness.py dual copy confirmed
- [x] C-7: scan baseline symmetric; no new BLOCKERs; fail_open_allowlist.json committed
- [x] C-8: all truth surfaces current; no duplicate sections; all phase gates checked
- [x] ClosurePacket emitted and validated: Verdict=PASS
- [x] docs/context/closure_packet_sprint_6phase.md written

## Phases 2-5 Gates (carried forward as complete)
- [x] Phase 2: all 21 active tests pass; check_fail_open.py baseline committed; scan manifest symmetric
- [x] Phase 3: Phase A + Phase B complete; loop_readiness_latest.json live; checklist tests pass
- [x] Phase 4: Stream A zero absolute paths; templates documented; onboarding checklist fixed; Stream D gap audit passed
- [x] Phase 5: golden-path CI green on Windows + Linux; preflight-failure-detection + shadowed-module-smoke green
