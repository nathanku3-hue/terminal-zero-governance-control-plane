# Loop Operating Contract (Freeze Lifted) v1.2

> Internal governance contract for operator/worker/auditor loop behavior in this repository.
> External readers: start with `README.md`; use `SECURITY.md` for vulnerability reporting and `SUPPORT.md` for support channels.

Owner: PM  
Status: ACTIVE  
Last Updated: 2026-03-23  
Applies To: Phase 24C Closure and P2 Authorization (Freeze Lifted per D-185)

## 1) Current Mode

Architecture Status: **UNFROZEN** (D-185, 2026-03-23)
- Schema, prompt, and architecture scope now unblocked for P2 work.
- New gates/scripts/prompt redesign may proceed with standard review discipline.
- No runtime control-plane changes without explicit approval.

Operations Status: **ACTIVE**
- Continue enforce-mode operations per phase playbook.
- Continue annotation, weekly report, dossier, and GO signal refresh.
- Phase 24C closure: Ready for declaration.
- P2 work authorization: Ready.

Startup Rule (enforced):
- Start every round with `python scripts/startup_codex_helper.py --repo-root .`.
- Choose handoff mode at startup:
  - `--handoff-target sonnet_web` => worker kickoff emits `WORKER_HEADER: (paste to sonnet web)`.
  - `--handoff-target local_cli` => worker kickoff emits `WORKER_HEADER: (skills call upon worker)`.
- If `docs/context/next_round_handoff_latest.md` exists, treat it as an advisory acceleration artifact only.
  - It may be used to prefill the next round's thinking and kickoff draft.
  - It does not replace startup interrogation, round-contract completion, or PM/CEO acknowledgments required by this contract.
- If `docs/context/expert_request_latest.md` exists, treat it as an advisory worker-to-expert acceleration artifact only.
  - It may be used to accelerate a specialist ask when the worker reports low confidence, ambiguity, or blocked-by-expert state.
  - It does not auto-invoke experts, does not bypass cap/exception rules, and does not replace Worker/Auditor/PM/CEO authority.
- If `docs/context/pm_ceo_research_brief_latest.md` exists, treat it as an advisory PM/CEO delegation brief only.
  - It may be used to delegate focused tradeoff research to subagents/engineers.
  - It does not replace PM/CEO synthesis, prioritization, or final decision authority.
- If `docs/context/board_decision_brief_latest.md` exists, treat it as an advisory PM/CEO decision-support brief only.
  - PM may use it to package top-level tradeoffs and a recommended path for CEO review.
  - Any CTO/COO/expert sections inside the brief are analytic lenses only; they do not create new authorities, approvals, or veto paths.
  - CEO remains the final decision owner for strategic direction, GO/HOLD/REFRAME, and promotion decisions.
- Do not enter Worker/Auditor loop until startup interrogation captures:
  - `ORIGINAL_INTENT`
  - `DELIVERABLE_THIS_SCOPE`
  - `NON_GOALS`
  - `DONE_WHEN`
  - `POSITIONING_LOCK`
  - `TASK_GRANULARITY_LIMIT` (`1` or `2`)
  - `DECISION_CLASS`
  - `EXECUTION_LANE`
  - `RISK_TIER` (`LOW|MEDIUM|HIGH`)
  - `INTUITION_GATE` (`MACHINE_DEFAULT` or `HUMAN_REQUIRED`)
  - `INTUITION_GATE_RATIONALE`
  - `DONE_WHEN_CHECKS` (comma-separated closure/cycle check IDs)
  - `REFACTOR_BUDGET_MINUTES`
  - `REFACTOR_SPEND_MINUTES`
  - `REFACTOR_BUDGET_EXCEEDED_REASON` (required only if spend > budget)
  - `COUNTEREXAMPLE_TEST_COMMAND`
  - `COUNTEREXAMPLE_TEST_RESULT`
  - `MOCK_POLICY_MODE` (`STRICT` or `NOT_APPLICABLE`)
  - `MOCKED_DEPENDENCIES`
  - `INTEGRATION_COVERAGE_FOR_MOCKS` (`YES|NO|N/A`)
  - `OWNED_FILES`
  - `INTERFACE_INPUTS`
  - `INTERFACE_OUTPUTS`
  - `PARALLEL_SHARD_ID` (optional)
- Intuition gate behavior:
  - If `INTUITION_GATE=HUMAN_REQUIRED`, no execution command may run until PM/CEO acknowledgment is recorded (`INTUITION_GATE_ACK` + `INTUITION_GATE_ACK_AT_UTC`).
  - If `INTUITION_GATE=MACHINE_DEFAULT`, execution can proceed once all other mandatory startup fields are valid and required readiness artifacts are `READY`.

## 1a) Startup Go/No-Go Artifact

- `docs/context/init_execution_card_latest.md` is the authoritative startup go/no-go artifact.
- Operators must use this card as the canonical one-glance startup view before any execution command.
- Startup readiness is authoritative in practice: `startup_gate.status` must not be `READY_TO_EXECUTE` while required readiness artifacts are missing or stale.
- `docs/context/next_round_handoff_latest.md` is non-authoritative; if it conflicts with startup intake or other authoritative artifacts, startup intake and the source-of-truth hierarchy below win.
- `docs/context/expert_request_latest.md`, `docs/context/pm_ceo_research_brief_latest.md`, and `docs/context/board_decision_brief_latest.md` are also non-authoritative; if they conflict with startup intake, active round contract, or other authoritative artifacts, the authoritative artifacts win.
- Advisory split-style convention:
  - Worker packets keep `machine_optimized` and `pm_first_principles` as the authoritative structured contract, and may add `response_views` for machine transport, human brief, and paste-ready delegation.
  - Advisory artifacts keep `docs/context/*_latest.json` as the machine-canonical payload, `docs/context/*_latest.md` as the operator-facing summary, and `paste_ready_block` as the copy lane.
  - Repo-root mirrors such as `NEXT_ROUND_HANDOFF_LATEST.md` and `MILESTONE_OPTIMALITY_REVIEW_LATEST.md` follow the same family rule: convenience-only, intentionally thin, and backed by an authoritative `docs/context` source.
  - Repo-root mirrors do not add a new control-plane authority and make no gate or authority change.

## 1b) Pragmatic Philosophy Rules (Docs-as-Code)

- Canonical policy: `docs/pragmatic_sop.md` (CN/EN).
- Canonical logic spine index: `docs/logic_spine_index.md`.
- Big changes must be manifest-reviewed before coding via `docs/templates/change_manifest_template.md`.
- Repo-specific truth protocol is documented in `docs/repo_init_truth_protocol.md` (no universal truth engine assumption).
- High-semantic-risk pre-coding falsification uses `docs/templates/domain_falsification_pack.md` (working copy: `docs/context/domain_falsification_pack_latest.md`).
- Advisory optimality review uses `docs/optimality_review_protocol.md` and `docs/templates/optimality_review_brief.md` (working copy: `docs/context/optimality_review_brief_latest.md`).
- Cross-product or vendor/tool adoption comparisons use `docs/templates/product_comparison_template.md` (working copy: `docs/context/product_comparison_latest.md`) to make explicit `COPY`, `MODIFY_ON_TOP`, and `REJECT` calls; this remains advisory-only and does not change authority or closure behavior.
- The same brief may run in multi-option compare mode (`OPTION_A/B/C`) for high-impact decisions; it remains advisory-only and does not change authority or closure behavior.
- At milestone close, operators may also write `docs/context/milestone_optimality_review_latest.md` from the same template to record whether the overall system shape got simpler or more complex; this remains advisory-only.
- `MILESTONE_OPTIMALITY_REVIEW_LATEST.md` is an optional convenience-only repo-root mirror; it stays a thin PM summary and the `docs/context` milestone brief remains the authoritative source.
- The same milestone-close brief may also include an optional `ELEGANCE_ENTROPY_SNAPSHOT` using lean proxies (`CONCEPT_SURFACE_DELTA`, `INTERFACE_SURFACE_DELTA`, `BOUNDARY_CROSSINGS_DELTA`, `FUTURE_EDIT_SURFACE`, `BIGGEST_SIMPLIFIER`, `BIGGEST_ENTROPY_RISK`, `ENTROPY_VERDICT`); if the surface is still too fresh or unstable to judge honestly, explicitly record `I don't know yet`.
- After a shipped wave or meaningful post-merge learning update, operators may capture advisory shipped-outcome feedback into `docs/context/profile_outcomes_corpus/`; this improves learning only and does not change authority or closure behavior.
- Main orchestrator/principal role remains governance-only (scope/owner/checks), not implementation/review execution.
- AI execution remains bounded by explicit module boundaries and non-goals declared in active round/manifest artifacts.
- This section is process-level documentation only and does not add a new runtime control-plane authority.

## 2) Worker <-> Auditor Back-and-Forth: Skills or MCP?

### Decision
Core loop should run via **skills/process contracts**, not MCP.

### Why
- Skills/contracts are deterministic and auditable for governance.
- MCP is useful for external context/tool access, but is not a reliable control-plane for verdict authority.

### Channel Policy
1. **Primary channel (required):** Skills + file artifacts
   - `docs/round_contract_template.md`
   - `docs/expert_invocation_policy.md`
   - `docs/disagreement_taxonomy.md`
   - `docs/disagreement_runbook.md`
2. **Secondary channel (optional):** MCP
   - Allowed for data retrieval or helper tooling.
   - Not authoritative for PASS/BLOCK/GO/HOLD/REFRAME decisions.
3. **Authority remains:**
   - Worker: implementation decisions
   - Auditor: scope/risk PASS/BLOCK
   - CEO: GO/HOLD/REFRAME

## 2a) Source-of-Truth Hierarchy (Model Reference Order)

Model must read and prioritize sources in this order:
1. Init baseline product artifacts (authoritative):
   - `top_level_PM.md`
   - Product spec / PRD provided at init (if present in repo)
2. Governance baseline (authoritative):
   - `docs/decision log.md`
3. Approved phase scope docs:
   - `docs/phase_brief/*.md`
4. Generated execution artifacts:
   - Dossier, calibration report, GO signal, phase-end status/summary
5. Worker-authored summaries and plans:
   - Useful for context, but non-authoritative if conflicting with sources 1-4

Conflict rule:
- If worker-authored text conflicts with sources 1-4, sources 1-4 win.
- Auditor must flag conflict as `D08` (criteria interpretation/source conflict) and require correction before CEO escalation.

## 2b) Per-Round Decision Class (Required)

Every round must declare `DECISION_CLASS`:
- `ONE_WAY`: hard to reverse, broad blast radius, or external side effects.
- `TWO_WAY`: reversible with bounded blast radius.

Acceptance checks:
- Missing `DECISION_CLASS` => round is `INVALID`.
- Missing `DECISION_CLASS_RATIONALE` => Auditor `BLOCK`.
- Misclassified high-impact work as `TWO_WAY` => Auditor raises `D08` and blocks escalation.

## 2c) Fast Lane for Trivial Work (Strict Eligibility)

`EXECUTION_LANE=FAST` is allowed only when all checks are `YES`:
- `FAST_LANE_ELIGIBILITY_LOC_LE_20`
- `FAST_LANE_ELIGIBILITY_FILES_LE_2`
- `FAST_LANE_ELIGIBILITY_NO_SCHEMA_API_CHANGE`
- `FAST_LANE_ELIGIBILITY_NO_SECURITY_COMPLIANCE_IMPACT`
- `FAST_LANE_ELIGIBILITY_NO_NEW_DEP_OR_INFRA`

Fast lane disqualifiers (any one => `STANDARD` lane):
- Any disagreement opened pre-execution.
- Any required expert beyond `qa`.
- Any change requiring PM/CEO override.

Acceptance checks:
- Worker must set `FAST_LANE_REQUEST`.
- Auditor must explicitly mark `FAST_LANE_ACCEPTED: YES/NO` before execution.
- If any eligibility check is `NO`, Auditor sets `FAST_LANE_ACCEPTED: NO` and route to `STANDARD`.

## 2d) Delete-Before-Add Rule

If a round introduces additions that supersede existing artifacts, delete/deprecate first.

Mandatory fields:
- `DELETE_BEFORE_ADD_TARGETS`
- `ADDITIONS_AFTER_DELETE`

Acceptance checks:
- New additive artifact with no delete/deprecate target (or explicit `none` rationale) => Auditor `BLOCK`.
- Evidence must include paths showing delete/deprecate step completed before additive step.

## 2e) TDD Mode Semantics (Required)

TDD mode must be declared every round and interpreted consistently:
- `TDD_MODE=REQUIRED` for code-bearing rounds (any round that changes executable behavior: `scripts/`, `tests/`, app/runtime code, build logic, or validation logic).
- `TDD_MODE=NOT_APPLICABLE` only for non-code rounds (docs-only governance edits, planning-only rounds, or evidence curation with zero behavior change).
- If uncertain, default to `REQUIRED`.
- `NOT_APPLICABLE` requires explicit rationale and Auditor acceptance before closure.

## 3) Loop Sequence (Required)

0. Run startup helper and persist startup intake:
   - Readiness progress dashboard for required governance docs/artifacts.
   - Intent interrogation and paste-ready kickoff block.
1. Worker fills round contract:
   - `ORIGINAL_INTENT`
   - `DELIVERABLE_THIS_SCOPE`
   - `POSITIONING_LOCK`
   - `TASK_GRANULARITY_LIMIT`
   - `INTUITION_GATE`
   - `INTUITION_GATE_RATIONALE`
   - `DECISION_CLASS`
   - `EXECUTION_LANE`
   - `RISK_TIER`
   - `NON_GOALS`
   - `DONE_WHEN`
   - `DONE_WHEN_CHECKS`
   - `REFACTOR_BUDGET_MINUTES`
   - `REFACTOR_SPEND_MINUTES`
   - `REFACTOR_BUDGET_EXCEEDED_REASON`
   - `OWNED_FILES`
   - `INTERFACE_INPUTS`
   - `INTERFACE_OUTPUTS`
   - `PARALLEL_SHARD_ID` (optional)
   - `TDD_MODE`
   - `RED_TEST_COMMAND`
   - `RED_TEST_RESULT`
   - `GREEN_TEST_COMMAND`
   - `GREEN_TEST_RESULT`
   - `COUNTEREXAMPLE_TEST_COMMAND`
   - `COUNTEREXAMPLE_TEST_RESULT`
   - `MOCK_POLICY_MODE`
   - `MOCKED_DEPENDENCIES`
   - `INTEGRATION_COVERAGE_FOR_MOCKS`
   - `REFACTOR_NOTE`
   - `TDD_NOT_APPLICABLE_REASON` (required when `TDD_MODE=NOT_APPLICABLE`)
1a. Worker + Auditor capture pre-execution disagreement risks:
   - `PRE_EXEC_DISAGREEMENT_CAPTURE`
   - `PRE_EXEC_CAPTURED_AT_UTC`
   - `PRE_EXEC_ALIGNMENT_ACK`
1b. Apply intuition gate before execution:
   - If `INTUITION_GATE=HUMAN_REQUIRED`, record `INTUITION_GATE_ACK` (`PM_ACK` or `CEO_ACK`) and `INTUITION_GATE_ACK_AT_UTC` before step 2.
2. Worker executes scoped work and produces evidence artifacts.
2a. Worker submits End-of-Round Summary to Auditor (mandatory handoff).
3. Auditor validates scope/risk and returns PASS/BLOCK with findings.
4. If disagreement: classify with `D01..D10`, resolve/escalate by SLA.
5. Refresh decision artifacts:
   - Weekly calibration report
   - Promotion dossier
   - CEO GO signal
6. Publish paste-ready CEO packet only if end-loop criteria are met.

Handoff rule:
- If Worker End-of-Round Summary is missing, Auditor must mark round `NOT_READY` and stop escalation to CEO.
- If pre-execution disagreement capture is missing, Auditor must mark round `NOT_READY` and stop escalation to CEO.
- If `INTUITION_GATE=HUMAN_REQUIRED` and PM/CEO acknowledgment is missing before execution, Auditor must mark round `NOT_READY` and stop escalation to CEO.
- If TDD contract evidence is missing/invalid for declared mode, Auditor must mark round `NOT_READY` and stop escalation to CEO.
- If refactor/mock policy gate fails, Auditor must mark round `NOT_READY` and stop escalation to CEO.
- If `DONE_WHEN_CHECKS` contains unmapped check IDs or any listed check is not `PASS`, Auditor must mark round `NOT_READY`.
- If `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY` and dual-judge evidence is missing, Auditor must mark round `NOT_READY`.
- If active shards have overlapping `OWNED_FILES` without PM override, Auditor must mark round `NOT_READY`.

## 3a) Minimal Automation Commands (No New Control Plane)

- Single closure gate (run independently when you only need a ready/not-ready escalation verdict):
  - `python scripts/validate_loop_closure.py --repo-root .`
  - Closure recommendation rule: `READY_TO_ESCALATE` is allowed only when `ceo_go_signal.md` has `- Recommended Action: GO`, `tdd_contract_gate=PASS`, and `exec_memory_packet_latest.json` artifact is present; `HOLD`/`REFRAME` remains `NOT_READY`.
  - Outputs: `docs/context/loop_closure_status_latest.json`, `docs/context/loop_closure_status_latest.md`.
- Refactor/mock policy gate (round contract integrity for refactor budget + mock discipline):
  - `python scripts/validate_refactor_mock_policy.py --round-contract-md docs/context/round_contract_latest.md`
  - Gate result must be PASS before escalation.
- One-command cycle runner (existing gates + artifact refresh + closure check):
  - `python scripts/run_loop_cycle.py --repo-root .`
  - Optional rerun without phase-end: `python scripts/run_loop_cycle.py --repo-root . --skip-phase-end`
  - `--allow-hold` is reporting semantics only (step/status remap to `HOLD`) and does not bypass closure gate requirements.
  - Cycle includes weekly summary auto-refresh: `refresh_ceo_weekly_summary` step after `generate_ceo_go_signal` and before `validate_ceo_weekly_summary_truth`.
  - Cycle includes Phase A memory packet integration: `build_exec_memory_packet` step after `refresh_ceo_weekly_summary`, and `validate_exec_memory_truth` step after `validate_ceo_weekly_summary_truth`.
  - Outputs: `docs/context/loop_cycle_summary_latest.json`, `docs/context/loop_cycle_summary_latest.md`, `docs/context/lessons_worker_latest.md`, `docs/context/lessons_auditor_latest.md`, `docs/context/exec_memory_packet_latest.json`, `docs/context/exec_memory_packet_latest.md`, `docs/context/next_round_handoff_latest.json`, `docs/context/next_round_handoff_latest.md`, `docs/context/expert_request_latest.json`, `docs/context/expert_request_latest.md`, `docs/context/pm_ceo_research_brief_latest.json`, `docs/context/pm_ceo_research_brief_latest.md`, `docs/context/board_decision_brief_latest.json`, `docs/context/board_decision_brief_latest.md`.
  - `next_round_handoff_latest.*` is an advisory artifact generated from current blocking gaps and recommended refreshes; use it to accelerate the next loop kickoff, but always revalidate intent/scope/risk through the startup helper before execution.
  - `expert_request_latest.*` is an advisory artifact generated from the same loop evidence to accelerate a bounded specialist ask when the worker is blocked by low confidence or ambiguity.
  - `pm_ceo_research_brief_latest.*` is an advisory artifact generated from the same loop evidence to accelerate PM/CEO delegation of focused tradeoff research; PM/CEO remains the decision owner.
  - `board_decision_brief_latest.*` is an advisory artifact generated from the same evidence to package top-level tradeoffs for PM recommendation and CEO review; any CTO/COO/expert lenses are analytic inputs only, and CEO remains the final decision owner.
  - Advisory markdown outputs use a stable split lane: `Human Brief`, `Machine View`, and `Paste-Ready Block`.

## 4) End-Loop Criteria for Paste-Ready to CEO

A loop is "paste-ready to CEO" only when all checks pass:

### A. Contract Completeness
- Worker contract fields are complete (intent/deliverable/non-goals/done-when).
- `POSITIONING_LOCK` is complete before round execution.
- `TASK_GRANULARITY_LIMIT` is set to `1` or `2` atomic tasks per worker per round.
- `INTUITION_GATE` and `INTUITION_GATE_RATIONALE` are complete.
- If `INTUITION_GATE=HUMAN_REQUIRED`, `INTUITION_GATE_ACK` and `INTUITION_GATE_ACK_AT_UTC` are recorded before execution.
- `DECISION_CLASS`, `DECISION_CLASS_RATIONALE`, and `EXECUTION_LANE` are complete.
- `RISK_TIER` is complete and valid (`LOW|MEDIUM|HIGH`).
- If `EXECUTION_LANE=FAST`, all `FAST_LANE_ELIGIBILITY_*` fields are `YES` and Auditor accepted fast lane.
- `DELETE_BEFORE_ADD_TARGETS` and `ADDITIONS_AFTER_DELETE` are complete.
- `OWNED_FILES`, `INTERFACE_INPUTS`, and `INTERFACE_OUTPUTS` are complete.
- `DONE_WHEN_CHECKS` is complete and maps to closure/cycle check IDs.
- `REFACTOR_BUDGET_MINUTES` and `REFACTOR_SPEND_MINUTES` are complete, numeric, and policy-compliant.
- If spend exceeds budget, `REFACTOR_BUDGET_EXCEEDED_REASON` is explicitly recorded.
- `COUNTEREXAMPLE_TEST_COMMAND` and `COUNTEREXAMPLE_TEST_RESULT` are complete.
- `MOCK_POLICY_MODE`, `MOCKED_DEPENDENCIES`, and `INTEGRATION_COVERAGE_FOR_MOCKS` are complete and policy-compliant.
- `PRE_EXEC_DISAGREEMENT_CAPTURE` is completed before execution.
- TDD contract fields are complete; `TDD_MODE` matches round type (code vs non-code), and `TDD_NOT_APPLICABLE_REASON` is present when applicable.
- Auditor verdict is explicit (`PASS` or `BLOCK`) with rationale.
- `tdd_contract_gate` is `PASS` in closure status artifact.

### B. Evidence Binding
- Every key claim has an artifact path.
- Artifact timestamps are from current cycle.
- C0-C5 values are copied from dossier (not retyped from memory).
- Recommendation matches generated GO signal.
- Manual assumptions are explicitly labeled as assumptions.

### C. Governance Discipline
- All C/H findings are annotated (100% coverage).
- Disagreements (if any) logged with D-codes and resolution owner/SLA.
- No authority boundary violation in decision chain.
- Cross-judge sampling fields recorded (`cross_judge_sampled`, trigger, result).
- If `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY`, dual-judge evidence is present (`cross_judge_sampled=YES` and `cross_judge_result=CONCUR`).
- If parallel shards are active, no overlapping `OWNED_FILES` across shards unless PM override is documented.

### D. Packet Outputs Present
- `docs/context/auditor_calibration_report.json`
- `docs/context/auditor_promotion_dossier.json`
- `docs/context/ceo_go_signal.md`
- Weekly summary for leadership cycle (if due)

### E. Optional Gate Interpretation (Review Checklist / Interface Contract)
- `review_checklist_gate` and `interface_contract_gate` are activation-by-artifact-presence checks in current freeze mode; they do not create new required artifacts by themselves.
- `SKIP` is acceptable only when the corresponding artifact is genuinely not in scope for the round; `SKIP` means "gate not activated," not `PASS`.
- Operators must not cite a skipped optional gate as evidence of review or interface safety.
- Operators should instantiate `docs/context/pr_review_checklist_latest.md` from `docs/templates/pr_review_checklist.md` when the round expects explicit human review coverage or review-checklist evidence.
- Operators should instantiate `docs/context/interface_contract_manifest_latest.json` from `docs/templates/interface_contract_manifest.json` when the round adds or changes a declared interface surface (for example `INTERFACE_INPUTS`, `INTERFACE_OUTPUTS`, schemas, API/CLI/file contracts, or cross-repo handoff contracts).
- If an operator expects either optional gate to be active for the round, the artifact must be created before closure; absence at closure will remain `SKIP` and must be treated as missing optional evidence, not silent approval.

If any check fails: status is not paste-ready; return to Worker/Auditor loop.

## 4a) Cross-Judge Lightweight Sampling Policy

Purpose: calibrate Auditor quality without full dual review on every round.

Sampling policy:
- Random sample: at least 10% of PASS rounds per week.
- Mandatory sample triggers:
  - `auditor_confidence < 0.70`
  - `RISK_TIER=HIGH`
  - `DECISION_CLASS=ONE_WAY` with `SCOPE_MATCH=PASS`
  - Reopened disagreement on same task within 48h

Mandatory fields (Auditor metadata):
- `cross_judge_sampled` (`YES/NO`)
- `cross_judge_trigger` (`random_10pct|low_confidence|high_impact|disagreement|none`)
- `cross_judge_result` (`CONCUR|DIVERGE|N/A`)

Acceptance checks:
- If mandatory trigger is present and `cross_judge_sampled=NO` => round `NOT_READY`.
- If `cross_judge_result=DIVERGE` => open disagreement (`D08` by default unless another code fits better) before CEO escalation.

## 4b) Risk-Tiered Judging Policy (Dual-Judge Gate)

Escalation policy:
- If `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY`, dual-judge evidence is required before CEO escalation.
- Dual-judge evidence means:
  1. Primary Auditor verdict is `PASS`.
  2. Cross-judge is sampled (`cross_judge_sampled=YES`).
  3. Cross-judge concurs (`cross_judge_result=CONCUR`).
  4. Evidence path for second judge is recorded in round artifacts.

Failure handling:
- Missing any dual-judge element => `NOT_READY` and return to Worker/Auditor loop.

## 4c) Parallel Fan-In Policy

Shard ownership rules:
- Parallel shards may run only when each shard declares `OWNED_FILES`.
- Active shards must not overlap `OWNED_FILES` unless PM override is explicitly recorded.
- `PARALLEL_SHARD_ID` is optional per round, but required when participating in fan-in.

Fan-in gate:
- Each shard must independently pass its evidence gate (`DONE_WHEN_CHECKS` all `PASS`) before fan-in.
- Fan-in is blocked if any shard is `NOT_READY`, has unresolved HIGH findings, or lacks dual-judge evidence when required.

## 5) Minimal CEO Paste Block (Output Contract)

```text
LOOP_STATUS: PASTE_READY|NOT_READY
ROUND_ID: <run_id>
RECOMMENDATION: GO|HOLD|REFRAME

C0: <PASS/FAIL>  C1: <MANUAL_CHECK/PASS/FAIL>
C2: <PASS/FAIL>  C3: <PASS/FAIL>
C4: <PASS/FAIL>  C4b: <PASS/FAIL>  C5: <PASS/FAIL>

KEY_BLOCKERS: <list or none>
EVIDENCE_PATHS:
- <artifact_path_1>
- <artifact_path_2>
- <artifact_path_3>

ASSUMPTIONS: <none or explicit list>
NEXT_DIRECTIVE: <single action>
```

## 6) Freeze Exit Condition

Freeze lifts only after ALL conditions below are met:
1. `C1` manual signoff is recorded in the decision log.
2. Canary enforce is complete and PM rollout approval is recorded in:
   - `docs/context/canary_enforce_log.md`
   - `docs/context/pm_canary_review_approval.md`
3. Enforce stability evidence is complete:
   - Count only phase-end status artifacts under `docs/context/phase_end_logs/phase_end_handover_status_*.json` produced after PM rollout approval and enforce-default activation.
   - At least `10` consecutive counted runs must be `PASS`.
   - Each counted run must satisfy all of:
     - top-level `result == "PASS"`
     - top-level `failed_exit_code == 0`
     - `finalize_failures` is empty
     - gate `G11_auditor_review` exists, has `status == "PASS"`, and its `command` includes `--mode enforce`
     - no skipped gates except explicitly scoped exceptions such as `G05b_cross_repo_readiness` for single-repo rollout
4. The latest available `docs/context/auditor_promotion_dossier.json` still shows all of:
   - `c0_infra_health.met == true`
   - `c4_fp_rate.met == true`
   - `c4b_annotation_coverage.met == true`
   - `c5_all_v2.met == true`
5. Mode transition evidence exists in `docs/context/phase_end_logs/`:
   - at least one earlier `PASS` run in `shadow` mode
   - at least one later `PASS` run in `enforce` mode

Until then: improve execution quality, not architecture complexity.
