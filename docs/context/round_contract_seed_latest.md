# Round Contract Seed

- GENERATED_AT_UTC: 2026-03-30T09:19:36Z

## Prefilled Fields

- ORIGINAL_INTENT: Phase 2 execution hardening - Stream B critical path
- PRODUCT_STAGE_NOW: Phase 2 execution hardening in flight; Stream A+B parallel; Streams C+D independent
- PRODUCT_STAGE_INTENT: Complete Stream B to unblock Stream E (Golden Path Proof)
- PRODUCT_STAGE_OUT_OF_SCOPE: Stream E; Phase 3+; hash stability; schema version policy CI
- PRODUCT_PROBLEM_THIS_ROUND: Fail-open paths (PhaseGate=None stubs, silent imports) not yet hardened
- WHY_NOW: Stream B is critical path; blocks Stream E and 8/10 maturity target
- IF_WE_SKIP_THIS: System remains fail-open; Stream E cannot be unblocked; production readiness stays at 2.5/5
- DELIVERABLE_THIS_SCOPE: Complete Stream B hardening tasks H-1 through H-6 and H-NEW-1 through H-NEW-4; all 21 active tests pass
- NON_GOALS: Do not start Stream E before Stream A and B complete; no hash fields in Phase 2; no scripts/ first
- DONE_WHEN: All 21 active tests pass; run_failure_latest.json on every hard failure; gate_decisions visible on every run
- PLANNED_SURFACE_NAME: N/A
- PLANNED_SURFACE_TYPE: core
- REPLACES_OR_MERGES_WITH: N/A
- RETIRE_TRIGGER: N/A
- MVP_NEXT_STAGE_GATE: All 21 Stream B tests pass; check_fail_open baseline committed
- NEXT_SIMPLIFICATION_STEP: Phase 3: hash stability; Phase 4: Docker+JSON logs
- POSITIONING_LOCK: lean
- TASK_GRANULARITY_LIMIT: 1
- DECISION_CLASS: TWO_WAY
- RISK_TIER: MEDIUM
- EXECUTION_LANE: STANDARD
- WORKFLOW_LANE: DEFAULT
- WORKFLOW_LANE_RATIONALE: TODO(one line on why this governance lane is appropriate)
- QA_PRE_ESCALATION_REQUEST: NO
- SOCRATIC_CHALLENGE_REQUEST: NO
- INTUITION_GATE: MACHINE_DEFAULT
- INTUITION_GATE_RATIONALE: deterministic
- PROJECT_PROFILE: quant_default
- EVIDENCE_PROFILE_RECOMMENDATION_STATUS: PROFILE_RECOMMENDED
- EVIDENCE_PROFILE_RECOMMENDATION: quant_default
- EVIDENCE_PROFILE_RECOMMENDATION_CONFIDENCE: 0.0
- EVIDENCE_PROFILE_SELECTION_SOURCE_ARTIFACT: docs/context/profile_selection_ranking_latest.json
- EVIDENCE_PROFILE_SELECTION_USAGE: advisory_only_no_authority_change
- MILESTONE_ID: unspecified_milestone
- APPROVED_MANDATORY_EXPERT_DOMAINS: principal,riskops,qa
- APPROVED_OPTIONAL_EXPERT_DOMAINS: math_stats,portfolio_risk,market_microstructure,data_eng,infra_perf
- BOARD_REENTRY_TRIGGERS: unknown_domain,expert_conflict,one_way_or_high_risk,milestone_gate
- UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_BOARD
- BOARD_REENTRY_REQUIRED: TODO(YES|NO)
- BOARD_REENTRY_REASON: TODO(or N/A)
- DONE_WHEN_CHECKS: startup_gate_status,go_signal_action_gate,freshness_gate
- COUNTEREXAMPLE_TEST_COMMAND: pytest tests/test_hardening.py tests/test_smoke_e.py -q
- COUNTEREXAMPLE_TEST_RESULT: 98 passed
- REFACTOR_BUDGET_MINUTES: 30
- REFACTOR_SPEND_MINUTES: 0
- REFACTOR_BUDGET_EXCEEDED_REASON: N/A
- MOCK_POLICY_MODE: NOT_APPLICABLE
- MOCKED_DEPENDENCIES: N/A
- INTEGRATION_COVERAGE_FOR_MOCKS: N/A
- OWNED_FILES: sop/_failure_reporter.py,sop/scripts/phase_gate.py,sop/scripts/worker_role.py,sop/scripts/auditor_role.py,tests/test_hardening.py,tests/test_smoke_e.py
- INTERFACE_INPUTS: docs/context/round_contract_latest.md,docs/context/loop_cycle_summary_latest.json
- INTERFACE_OUTPUTS: docs/context/run_failure_latest.json,docs/context/loop_cycle_summary_latest.json
- PARALLEL_SHARD_ID: TODO(optional; use none if single-worker)

## TDD Contract (Proof at Closure)

- TDD_MODE: TODO(REQUIRED|NOT_APPLICABLE)
- RED_TEST_COMMAND: TODO
- RED_TEST_RESULT: TODO
- GREEN_TEST_COMMAND: TODO
- GREEN_TEST_RESULT: TODO
- REFACTOR_NOTE: TODO
- TDD_NOT_APPLICABLE_REASON: TODO(if NOT_APPLICABLE)

## TODO (Startup Cannot Infer)

- EVIDENCE_COMMANDS: TODO(add exact validation and evidence commands).
- EXPERT_PLAN: TODO(list expert consult path and escalation trigger).
- CHANGE_BUDGET_DETAILS: TODO(specify risk, rollback, and time budget constraints).
