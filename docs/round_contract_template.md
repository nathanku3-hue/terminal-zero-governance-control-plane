# Round Contract Template v1.2

## Purpose
Use this contract at the start and end of every Worker ↔ Auditor round to prevent scope drift and keep outputs paste-ready for CEO decisions.

## Validity Rules
- A round is invalid if any mandatory field is empty.
- `DECISION_CLASS` is mandatory every round: `ONE_WAY` or `TWO_WAY`.
- `EXECUTION_LANE` is mandatory every round: `STANDARD` or `FAST`.
- `RISK_TIER` is mandatory every round: `LOW`, `MEDIUM`, or `HIGH`.
- `POSITIONING_LOCK`, `TASK_GRANULARITY_LIMIT`, `INTUITION_GATE`, and `INTUITION_GATE_RATIONALE` are mandatory every round.
- `TASK_GRANULARITY_LIMIT` must be `1` or `2` atomic tasks per worker per round.
- `OWNED_FILES`, `INTERFACE_INPUTS`, and `INTERFACE_OUTPUTS` are mandatory every round.
- For large-change scope (`DECISION_CLASS=ONE_WAY`, `RISK_TIER=HIGH`, or `CHANGE_BUDGET` implies >2 files or >0 architecture changes), `LOGIC_SPINE_INDEX_ARTIFACT`, `CHANGE_MANIFEST_ARTIFACT`, `ALLOWED_BOUNDARY_REFS`, and `NON_GOAL_REFS` are mandatory.
- `DONE_WHEN_CHECKS` is mandatory every round and must be a comma-separated list of check IDs that map to closure/cycle checks.
- `COUNTEREXAMPLE_TEST_COMMAND` and `COUNTEREXAMPLE_TEST_RESULT` are mandatory every round.
- `DOMAIN_FALSIFICATION_REQUIRED` is mandatory every round and must be `YES` or `NO`.
- `SEMANTIC_EXPERT_DOMAIN` is mandatory every round and must be one of `macro_econ`, `math_stats`, `product_ux`, `unknown`, or `none`.
- `PARALLEL_SHARD_ID` is optional; if provided, it must be stable for the round and unique among active shards unless PM override is recorded.
- `FAST_LANE_REQUEST=YES` is valid only if all `FAST_LANE_ELIGIBILITY_*` fields are `YES`.
- `EXECUTION_LANE=FAST` requires `DECISION_CLASS=TWO_WAY`.
- `TDD_MODE`, `RED_TEST_COMMAND`, `RED_TEST_RESULT`, `GREEN_TEST_COMMAND`, `GREEN_TEST_RESULT`, and `REFACTOR_NOTE` are mandatory every round.
- `REFACTOR_BUDGET_MINUTES` and `REFACTOR_SPEND_MINUTES` are mandatory every round.
- `MOCK_POLICY_MODE`, `MOCKED_DEPENDENCIES`, and `INTEGRATION_COVERAGE_FOR_MOCKS` are mandatory every round.
- If `TDD_MODE=REQUIRED`, red/green fields must contain executable evidence (no placeholders).
- If `TDD_MODE=NOT_APPLICABLE`, `TDD_NOT_APPLICABLE_REASON` is mandatory and red/green fields must be `N/A`.
- `REFACTOR_BUDGET_MINUTES` and `REFACTOR_SPEND_MINUTES` must be numeric and >=0.
- If `REFACTOR_SPEND_MINUTES > REFACTOR_BUDGET_MINUTES`, `REFACTOR_BUDGET_EXCEEDED_REASON` is required.
- `MOCK_POLICY_MODE=STRICT` requires non-empty `MOCKED_DEPENDENCIES` and `INTEGRATION_COVERAGE_FOR_MOCKS=YES`.
- `MOCK_POLICY_MODE=NOT_APPLICABLE` requires `INTEGRATION_COVERAGE_FOR_MOCKS=N/A`.
- If `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY`, `COUNTEREXAMPLE_TEST_*` must be executable evidence (not `N/A`) and dual-judge evidence is required before escalation.
- `DONE_WHEN_CHECKS` entries must resolve to `PASS` in latest closure/cycle outputs before escalation.
- Allowed closure check IDs include: `go_signal_action_gate`, `tdd_contract_gate`, `freshness_gate`, `go_signal_truth_gate`, `weekly_summary_truth_gate`, `exec_memory_truth_gate`, and required artifact checks.
- If `INTUITION_GATE=HUMAN_REQUIRED`, execution cannot start until PM/CEO acknowledgment is recorded (`INTUITION_GATE_ACK` + `INTUITION_GATE_ACK_AT_UTC`).
- If `DOMAIN_FALSIFICATION_REQUIRED=YES`, `DOMAIN_FALSIFICATION_ARTIFACT` and `SEMANTIC_RISK_REASON` must be non-placeholder values (not `N/A`), and `SEMANTIC_EXPERT_DOMAIN` must not be `none`.
- If `DOMAIN_FALSIFICATION_REQUIRED=NO`, set `DOMAIN_FALSIFICATION_ARTIFACT=N/A`, `SEMANTIC_RISK_REASON=N/A`, and `SEMANTIC_EXPERT_DOMAIN=none` unless a semantic risk is explicitly being reviewed.
- If `SEMANTIC_EXPERT_DOMAIN=unknown`, `BOARD_REENTRY_REQUIRED=YES` and non-placeholder `BOARD_REENTRY_REASON` are mandatory before escalation.
- `optimality_review_brief` fields are optional/advisory only and do not create new authority paths or required closure gates.
- Work outside `NON_GOALS` is a scope violation.
- Additive change without `DELETE_BEFORE_ADD_TARGETS` (or explicit `none`) is a scope violation.
- Auditor must return `PASS` or `BLOCK` with explicit rationale.
- CEO decision uses latest audited contract, not ad hoc chat context.
- Worker End-of-Round Submission must be handed to Auditor before Auditor Review starts.
- Missing Worker End-of-Round Submission => round status `INVALID` (cannot be forwarded to CEO).
- Missing `PRE_EXEC_DISAGREEMENT_CAPTURE` before execution start => round status `INVALID`.

## Round Header

| Field | Value |
|---|---|
| round_id | `<YYYYMMDD_HHMMSS_or_custom>` |
| phase | `<phase_id>` |
| task_id | `<directive_or_task>` |
| repo_id | `<repo_name>` |
| worker_id | `<worker_name>` |
| auditor_id | `<auditor_name>` |
| started_at_utc | `<ISO8601>` |
| decision_class | `ONE_WAY` or `TWO_WAY` |
| execution_lane | `STANDARD` or `FAST` |
| risk_tier | `LOW` or `MEDIUM` or `HIGH` |
| parallel_shard_id | `<optional shard id or N/A>` |

## Worker Contract (Mandatory)

### 1) Intent Lock
- ORIGINAL_INTENT: `<one sentence problem statement>`

### 2) Deliverable Lock
- DELIVERABLE_THIS_SCOPE: `<concrete output for this round only>`

### 3) Positioning and Intuition Controls
- POSITIONING_LOCK: `<explicit stance to hold across the round>`
- TASK_GRANULARITY_LIMIT: `1` or `2` (atomic tasks per worker per round)
- INTUITION_GATE: `MACHINE_DEFAULT` or `HUMAN_REQUIRED`
- INTUITION_GATE_RATIONALE: `<why machine-default or human acknowledgment is required>`
- INTUITION_GATE_ACK: `<PM_ACK|CEO_ACK|N/A>`
- INTUITION_GATE_ACK_AT_UTC: `<ISO8601|N/A>`

### 4) Decision Class and Lane
- DECISION_CLASS: `ONE_WAY` or `TWO_WAY`
- DECISION_CLASS_RATIONALE: `<one line on reversibility and blast radius>`
- EXECUTION_LANE: `STANDARD` or `FAST`
- RISK_TIER: `LOW` or `MEDIUM` or `HIGH`
- FAST_LANE_REQUEST: `YES` or `NO`
- FAST_LANE_ELIGIBILITY_LOC_LE_20: `YES/NO`
- FAST_LANE_ELIGIBILITY_FILES_LE_2: `YES/NO`
- FAST_LANE_ELIGIBILITY_NO_SCHEMA_API_CHANGE: `YES/NO`
- FAST_LANE_ELIGIBILITY_NO_SECURITY_COMPLIANCE_IMPACT: `YES/NO`
- FAST_LANE_ELIGIBILITY_NO_NEW_DEP_OR_INFRA: `YES/NO`

### 5) Scope Boundaries
- NON_GOALS: `<explicit out-of-scope list>`
- CHANGE_BUDGET: `<max files, max scripts, max architecture changes>`
- DELETE_BEFORE_ADD_TARGETS: `<paths to delete/deprecate first, or none>`
- ADDITIONS_AFTER_DELETE: `<planned additions after deletion step, or none>`
- OWNED_FILES: `<comma-separated file paths owned by this round>`
- INTERFACE_INPUTS: `<explicit upstream artifacts/contracts consumed>`
- INTERFACE_OUTPUTS: `<explicit downstream artifacts/contracts produced>`
- LOGIC_SPINE_INDEX_ARTIFACT: `<docs/logic_spine_index.md or scoped mirror; required for large-change scope>`
- CHANGE_MANIFEST_ARTIFACT: `<docs/context/change_manifest_latest.md or equivalent; required for large-change scope>`
- ALLOWED_BOUNDARY_REFS: `<canonical docs/spec refs that define allowed change boundaries; required for large-change scope>`
- NON_GOAL_REFS: `<canonical docs/spec refs that define out-of-scope boundaries; required for large-change scope>`
- PARALLEL_SHARD_ID: `<optional shard id, or N/A>`

### 6) Completion Gate
- DONE_WHEN: `<objective pass criteria>`
- DONE_WHEN_CHECKS: `<comma-separated check IDs that must be PASS>`
- REFACTOR_BUDGET_MINUTES: `<numeric minutes budget, >=0>`
- REFACTOR_SPEND_MINUTES: `<numeric minutes spent, >=0>`
- REFACTOR_BUDGET_EXCEEDED_REASON: `<required only if spend exceeds budget; else N/A>`
- STOP_CONDITION: `<what causes immediate stop/escalation>`

### 7) Pre-Execution Disagreement Capture
- PRE_EXEC_DISAGREEMENT_CAPTURE: `<none or list: D-code | disagreement_risk | owner | due_utc>`
- PRE_EXEC_CAPTURED_AT_UTC: `<ISO8601, must be before first execution command>`
- PRE_EXEC_ALIGNMENT_ACK: `WORKER_ACK` and `AUDITOR_ACK`

### 8) Evidence Plan
- EVIDENCE_REQUIRED: `<tests, logs, artifacts required>`
- SOURCE_BASELINES: `<init artifacts consulted: top_level_PM/spec/PRD/decision log>`
- VERIFICATION_COMMANDS:
  1. `<command_1>`
  2. `<command_2>`
  3. `<command_3>`

### 8a) Optional Artifact Guidance (Activation by Presence)
- `docs/context/pr_review_checklist_latest.md` is optional in freeze mode; create it from `docs/templates/pr_review_checklist.md` only when the round intends to use explicit review-checklist evidence.
- `docs/context/interface_contract_manifest_latest.json` is optional in freeze mode; create it from `docs/templates/interface_contract_manifest.json` when the round adds or changes interface surfaces such as `INTERFACE_INPUTS`, `INTERFACE_OUTPUTS`, schemas, API/CLI/file contracts, or cross-repo handoff contracts.
- If either optional artifact is absent at closure, the corresponding validator result will be `SKIP`; treat that as "not activated," not as `PASS`.
- Do not claim review-checklist or interface-contract coverage in Auditor/CEO materials unless the corresponding artifact exists and is linked.

### 8b) Optional Advisory: optimality_review_brief (No New Gate)
- Use this advisory block for high-impact / one-way / cross-module / architecture-affecting rounds when top-level tradeoff framing is useful.
- This block is optional and non-blocking; it does not alter decision authority, escalation ownership, or closure gate requirements.
- Compare at most `2-3` real options inside the same brief.
- PRIMARY_OBJECTIVE: `<single top-level objective for this round>`
- TOP_LEVEL_TRADEOFFS: `<compact list of major tradeoffs>`
- OPTION_A_TOP_LEVEL_EFFECT: `<semantic/top-level effect>`
- OPTION_A_WHY_NOW: `<why this option now>`
- OPTION_A_COST_IF_WRONG: `<main downside if wrong>`
- OPTION_A_EVIDENCE_PATHS: `<artifact paths>`
- OPTION_B_TOP_LEVEL_EFFECT: `<semantic/top-level effect>`
- OPTION_B_WHY_NOW: `<why this option now>`
- OPTION_B_COST_IF_WRONG: `<main downside if wrong>`
- OPTION_B_EVIDENCE_PATHS: `<artifact paths>`
- OPTION_C_TOP_LEVEL_EFFECT: `<optional>`
- OPTION_C_WHY_NOW: `<optional>`
- OPTION_C_COST_IF_WRONG: `<optional>`
- OPTION_C_EVIDENCE_PATHS: `<optional artifact paths>`
- RECOMMENDED_OPTION: `<OPTION_A|OPTION_B|OPTION_C|I don't know yet>`
- RECOMMENDED_BALANCE: `<recommended tradeoff balance>`
- WHAT_WOULD_FLIP_DECISION: `<specific condition(s) that would change recommendation>`
- IF_NOT_READY_TO_COMPARE: `<if needed, say I don't know yet and name the missing evidence or expert lane>`

### 9) TDD Evidence (Mandatory)
- TDD_MODE: `REQUIRED` or `NOT_APPLICABLE`
- RED_TEST_COMMAND: `<command proving failure first, or N/A>`
- RED_TEST_RESULT: `<failing output summary, or N/A>`
- GREEN_TEST_COMMAND: `<command proving pass after implementation, or N/A>`
- GREEN_TEST_RESULT: `<passing output summary, or N/A>`
- COUNTEREXAMPLE_TEST_COMMAND: `<command testing a plausible contrary case, or N/A per mode>`
- COUNTEREXAMPLE_TEST_RESULT: `<result summary for counterexample case, or N/A per mode>`
- REFACTOR_NOTE: `<refactor/no-refactor note with rationale>`
- TDD_NOT_APPLICABLE_REASON: `<required when TDD_MODE=NOT_APPLICABLE; else N/A>`
- MOCK_POLICY_MODE: `STRICT` or `NOT_APPLICABLE`
- MOCKED_DEPENDENCIES: `<comma-separated mocked dependency list, or N/A>`
- INTEGRATION_COVERAGE_FOR_MOCKS: `YES` or `NO` or `N/A`

### 10) Expert Invocation Plan
- DOMAIN_FALSIFICATION_REQUIRED: `YES` or `NO`
- DOMAIN_FALSIFICATION_ARTIFACT: `<path|N/A>`
- SEMANTIC_RISK_REASON: `<...|N/A>`
- SEMANTIC_EXPERT_DOMAIN: `<macro_econ|math_stats|product_ux|unknown|none>`
- PROJECT_PROFILE: `<startup profile key for curated domain-bucket bootstrap>`
- EVIDENCE_PROFILE_RECOMMENDATION_STATUS: `<PROFILE_RECOMMENDED|PROFILE_RECOMMENDED_UNKNOWN|RANKING_PRESENT_NO_RECOMMENDATION|RANKING_MISSING|RANKING_INVALID>`
- EVIDENCE_PROFILE_RECOMMENDATION: `<recommended profile or none>`
- EVIDENCE_PROFILE_RECOMMENDATION_CONFIDENCE: `<0.0-1.0 or N/A>`
- EVIDENCE_PROFILE_SELECTION_SOURCE_ARTIFACT: `<docs/context/profile_selection_ranking_latest.json or none>`
- EVIDENCE_PROFILE_SELECTION_USAGE: `advisory_only_no_authority_change`
- MILESTONE_ID: `<milestone identifier or startup default>`
- APPROVED_MANDATORY_EXPERT_DOMAINS: `<comma-separated mandatory domains for this milestone>`
- APPROVED_OPTIONAL_EXPERT_DOMAINS: `<comma-separated optional domains for this milestone>`
- BOARD_REENTRY_TRIGGERS: `<comma-separated triggers that require board lineup review>`
- UNKNOWN_EXPERT_DOMAIN_POLICY: `ESCALATE_TO_BOARD` or `ESCALATE_TO_PM` or `HOLD_AND_REQUEST_CLARIFICATION`
- BOARD_REENTRY_REQUIRED: `YES` or `NO`
- BOARD_REENTRY_REASON: `<trigger/rationale, or N/A>`
- TRIGGERED_EXPERTS: `<expert: trigger_reason>`
- CAP_APPLIED: `<x/3 per round, y/5 per task>`
- DEFERRED_EXPERTS: `<if any>`
- EXCEPTION_REQUEST: `<none or rationale>`
- GENERATED_EXPERT_REQUEST_ARTIFACT: `<docs/context/expert_request_latest.md or none>`
- GENERATED_PM_CEO_RESEARCH_BRIEF_ARTIFACT: `<docs/context/pm_ceo_research_brief_latest.md or none>`
- GENERATED_MILESTONE_EXPERT_ROSTER_ARTIFACT: `<docs/context/milestone_expert_roster_latest.json or none>`
- GENERATED_DOMAIN_BUCKET_BOOTSTRAP_ARTIFACT: `<docs/context/domain_bucket_bootstrap_latest.json or none>`
- GENERATED_ARTIFACT_USAGE_NOTE: `<advisory only; active round contract and startup intake remain authoritative>`

**Usage note:**
- Use `expert_request_latest.*` when the worker reports low confidence, ambiguity, or blocked-by-expert state and needs a bounded specialist ask.
- Use `pm_ceo_research_brief_latest.*` when PM/CEO wants to delegate tradeoff research to subagents/engineers before making a decision.
- Both generated artifacts are accelerators only; they do not change cap rules, exception rules, or final decision ownership.

## Worker End-of-Round Submission

| Field | Value |
|---|---|
| status | `COMPLETE` or `PARTIAL` or `BLOCKED` |
| artifacts_produced | `<paths>` |
| tests_run | `<summary>` |
| changes_made | `<short summary>` |
| risks_open | `<short list>` |
| contract_adherence | `YES` or `NO` |
| fast_lane_used | `YES` or `NO` |
| delete_before_add_executed | `YES` or `NO` |
| ended_at_utc | `<ISO8601>` |

## Auditor Review (Mandatory)

### 1) Contract Compliance Check
- ORIGINAL_INTENT present: `YES/NO`
- DELIVERABLE_THIS_SCOPE present: `YES/NO`
- POSITIONING_LOCK present: `YES/NO`
- TASK_GRANULARITY_LIMIT valid (`1/2`): `YES/NO`
- INTUITION_GATE valid (`MACHINE_DEFAULT/HUMAN_REQUIRED`): `YES/NO`
- INTUITION_GATE_RATIONALE present: `YES/NO`
- If `INTUITION_GATE=HUMAN_REQUIRED`, PM/CEO acknowledgment recorded before execution: `YES/NO`
- DECISION_CLASS + rationale present: `YES/NO`
- EXECUTION_LANE valid (`STANDARD/FAST`): `YES/NO`
- FAST lane eligibility all `YES` when requested: `YES/NO`
- FAST lane uses `DECISION_CLASS=TWO_WAY`: `YES/NO`
- RISK_TIER present and valid (`LOW/MEDIUM/HIGH`): `YES/NO`
- NON_GOALS respected: `YES/NO`
- DONE_WHEN met: `YES/NO`
- DONE_WHEN_CHECKS listed and mapped to closure/cycle checks: `YES/NO`
- DONE_WHEN_CHECKS all PASS in latest closure/cycle artifacts: `YES/NO`
- REFACTOR_BUDGET_MINUTES numeric and >=0: `YES/NO`
- REFACTOR_SPEND_MINUTES numeric and >=0: `YES/NO`
- If spend exceeds budget, REFACTOR_BUDGET_EXCEEDED_REASON present: `YES/NO`
- CHANGE_BUDGET respected: `YES/NO`
- DELETE_BEFORE_ADD respected: `YES/NO`
- OWNED_FILES declared and scoped to this round: `YES/NO`
- INTERFACE_INPUTS declared: `YES/NO`
- INTERFACE_OUTPUTS declared: `YES/NO`
- If large-change scope, LOGIC_SPINE_INDEX_ARTIFACT / CHANGE_MANIFEST_ARTIFACT / ALLOWED_BOUNDARY_REFS / NON_GOAL_REFS are present and non-placeholder: `YES/NO`
- DOMAIN_FALSIFICATION_REQUIRED valid and falsification artifact present when required: `YES/NO`
- If `SEMANTIC_EXPERT_DOMAIN=unknown`, UNKNOWN_EXPERT_DOMAIN_POLICY / BOARD_REENTRY_REQUIRED / BOARD_REENTRY_REASON are valid before escalation: `YES/NO`
- If `optimality_review_brief` is present, entries are internally consistent with DECISION_CLASS/RISK_TIER, compare no more than `2-3` options, bind each option to evidence paths, and are clearly labeled advisory-only: `YES/NO` (reminder only; non-gating).
- PARALLEL_SHARD_ID valid or `N/A`: `YES/NO`
- PRE_EXEC_DISAGREEMENT_CAPTURE completed before execution: `YES/NO`
- TDD_MODE valid (`REQUIRED/NOT_APPLICABLE`): `YES/NO`
- RED_TEST_COMMAND present and executable when required: `YES/NO`
- RED_TEST_RESULT records failing evidence when required: `YES/NO`
- GREEN_TEST_COMMAND present and executable when required: `YES/NO`
- GREEN_TEST_RESULT records passing evidence when required: `YES/NO`
- COUNTEREXAMPLE_TEST_COMMAND present and executable when required: `YES/NO`
- COUNTEREXAMPLE_TEST_RESULT records evidence when required: `YES/NO`
- REFACTOR_NOTE present: `YES/NO`
- If `TDD_MODE=NOT_APPLICABLE`, reason recorded and red/green fields are `N/A`: `YES/NO`
- MOCK_POLICY_MODE valid (`STRICT/NOT_APPLICABLE`): `YES/NO`
- If `MOCK_POLICY_MODE=STRICT`, MOCKED_DEPENDENCIES non-empty and INTEGRATION_COVERAGE_FOR_MOCKS=`YES`: `YES/NO`
- If `MOCK_POLICY_MODE=NOT_APPLICABLE`, INTEGRATION_COVERAGE_FOR_MOCKS=`N/A`: `YES/NO`
- If `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY`, dual-judge evidence present before escalation: `YES/NO`
- MILESTONE_ID and approved expert domain lists recorded: `YES/NO`
- UNKNOWN_EXPERT_DOMAIN_POLICY present and followed when unknown domain appears: `YES/NO`
- If any board reentry trigger fires, BOARD_REENTRY_REQUIRED and BOARD_REENTRY_REASON recorded: `YES/NO`

### 2) Technical/Risk Findings
| severity | finding_id | description | required_action |
|---|---|---|---|
| `<HIGH/MEDIUM/LOW>` | `<id>` | `<one line>` | `<one line>` |

### 3) Verdict
- SCOPE_MATCH: `PASS` or `BLOCK`
- FAST_LANE_ACCEPTED: `YES` or `NO` or `N/A`
- OVERENGINEER_FLAGS: `<none or list>`
- REQUIRED_CUTS: `<none or list>`
- MINIMAL_NEXT_STEP: `<single highest ROI next action>`

### 4) Auditor Metadata
| Field | Value |
|---|---|
| reviewed_at_utc | `<ISO8601>` |
| auditor_confidence | `<0.00-1.00>` |
| escalation_required | `YES/NO` |
| dual_judge_required | `YES/NO` |
| dual_judge_evidence | `<artifact paths or N/A>` |
| cross_judge_sampled | `YES/NO` |
| cross_judge_trigger | `random_10pct` or `low_confidence` or `high_impact` or `disagreement` or `none` |
| cross_judge_result | `CONCUR` or `DIVERGE` or `N/A` |

## CEO Decision Block

| Field | Value |
|---|---|
| decision | `GO` or `HOLD` or `REFRAME` |
| rationale | `<one paragraph>` |
| blockers | `<none or list>` |
| next_directive | `<single directive>` |
| decision_at_utc | `<ISO8601>` |

## Round Close Checklist
- Contract fields complete.
- Auditor verdict recorded.
- CEO decision recorded.
- Decision class/lane captured for round.
- Risk tier captured for round.
- Positioning/task/intuition controls captured for round.
- PM/CEO acknowledgment recorded when `INTUITION_GATE=HUMAN_REQUIRED`.
- Delete-before-add evidence linked when additions exist.
- Pre-execution disagreement capture recorded.
- OWNED_FILES and interface fields captured; shard overlap check complete (or PM override linked).
- Large-change rounds link logic spine, manifest, and canonical boundary/non-goal refs before execution.
- DONE_WHEN_CHECKS mapped and all listed checks are PASS.
- Refactor budget/spend fields validated against policy (or exceeded-reason recorded).
- TDD contract fields completed and mode/rationale valid.
- Counterexample test fields completed per mode/risk class.
- Mock policy fields validated (`STRICT` with integration coverage or `NOT_APPLICABLE` with `N/A` coverage).
- Dual-judge evidence attached when `RISK_TIER=HIGH` or `DECISION_CLASS=ONE_WAY`.
- Cross-judge sampling rule applied or explicitly `none`.
- If optional review-checklist/interface-contract evidence is expected for the round, instantiate the artifact before closure; otherwise treat validator `SKIP` as acceptable but non-evidentiary.
- Lessons entry appended with `source_role` and `round_id`.
- Artifacts linked for traceability.

---

## Paste-Ready Minimal Version

### Worker Paste Block
```text
ROUND: <round_id>
ORIGINAL_INTENT: <...>
DELIVERABLE_THIS_SCOPE: <...>
POSITIONING_LOCK: <...>
TASK_GRANULARITY_LIMIT: 1|2
INTUITION_GATE: MACHINE_DEFAULT|HUMAN_REQUIRED
INTUITION_GATE_RATIONALE: <...>
INTUITION_GATE_ACK: PM_ACK|CEO_ACK|N/A
INTUITION_GATE_ACK_AT_UTC: <ISO8601|N/A>
DECISION_CLASS: ONE_WAY|TWO_WAY
EXECUTION_LANE: STANDARD|FAST
RISK_TIER: LOW|MEDIUM|HIGH
FAST_LANE_REQUEST: YES|NO
FAST_LANE_ELIGIBILITY_LOC_LE_20: YES|NO
FAST_LANE_ELIGIBILITY_FILES_LE_2: YES|NO
FAST_LANE_ELIGIBILITY_NO_SCHEMA_API_CHANGE: YES|NO
FAST_LANE_ELIGIBILITY_NO_SECURITY_COMPLIANCE_IMPACT: YES|NO
FAST_LANE_ELIGIBILITY_NO_NEW_DEP_OR_INFRA: YES|NO
NON_GOALS: <...>
CHANGE_BUDGET: <...>
DELETE_BEFORE_ADD_TARGETS: <...>
ADDITIONS_AFTER_DELETE: <...>
OWNED_FILES: <...>
INTERFACE_INPUTS: <...>
INTERFACE_OUTPUTS: <...>
LOGIC_SPINE_INDEX_ARTIFACT: <...|N/A for non-large-change rounds>
CHANGE_MANIFEST_ARTIFACT: <...|N/A for non-large-change rounds>
ALLOWED_BOUNDARY_REFS: <...|N/A for non-large-change rounds>
NON_GOAL_REFS: <...|N/A for non-large-change rounds>
PARALLEL_SHARD_ID: <...|N/A>
PRE_EXEC_DISAGREEMENT_CAPTURE: <...>
DONE_WHEN: <...>
DONE_WHEN_CHECKS: <check_id_1,check_id_2,...>
REFACTOR_BUDGET_MINUTES: <numeric_minutes>
REFACTOR_SPEND_MINUTES: <numeric_minutes>
REFACTOR_BUDGET_EXCEEDED_REASON: <...|N/A>
STOP_CONDITION: <...>
EVIDENCE_REQUIRED: <...>
TDD_MODE: REQUIRED|NOT_APPLICABLE
RED_TEST_COMMAND: <...|N/A>
RED_TEST_RESULT: <...|N/A>
GREEN_TEST_COMMAND: <...|N/A>
GREEN_TEST_RESULT: <...|N/A>
COUNTEREXAMPLE_TEST_COMMAND: <...|N/A>
COUNTEREXAMPLE_TEST_RESULT: <...|N/A>
REFACTOR_NOTE: <...>
TDD_NOT_APPLICABLE_REASON: <...|N/A>
MOCK_POLICY_MODE: STRICT|NOT_APPLICABLE
MOCKED_DEPENDENCIES: <...|N/A>
INTEGRATION_COVERAGE_FOR_MOCKS: YES|NO|N/A
DOMAIN_FALSIFICATION_REQUIRED: YES|NO
DOMAIN_FALSIFICATION_ARTIFACT: <path|N/A>
SEMANTIC_RISK_REASON: <...|N/A>
SEMANTIC_EXPERT_DOMAIN: <macro_econ|math_stats|product_ux|unknown|none>
TRIGGERED_EXPERTS: <...>
CAP_APPLIED: <...>
MILESTONE_ID: <...>
EVIDENCE_PROFILE_RECOMMENDATION_STATUS: <...>
EVIDENCE_PROFILE_RECOMMENDATION: <...>
EVIDENCE_PROFILE_RECOMMENDATION_CONFIDENCE: <...>
EVIDENCE_PROFILE_SELECTION_SOURCE_ARTIFACT: docs/context/profile_selection_ranking_latest.json|none
EVIDENCE_PROFILE_SELECTION_USAGE: advisory_only_no_authority_change
APPROVED_MANDATORY_EXPERT_DOMAINS: <domain_1,domain_2,...>
APPROVED_OPTIONAL_EXPERT_DOMAINS: <domain_1,domain_2,...>
BOARD_REENTRY_TRIGGERS: <trigger_1,trigger_2,...>
UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_BOARD|ESCALATE_TO_PM|HOLD_AND_REQUEST_CLARIFICATION
BOARD_REENTRY_REQUIRED: YES|NO
BOARD_REENTRY_REASON: <...|N/A>
```

### Auditor Paste Block
```text
ROUND: <round_id>
SCOPE_MATCH: PASS|BLOCK
OVERENGINEER_FLAGS: <...>
REQUIRED_CUTS: <...>
MINIMAL_NEXT_STEP: <...>
FAST_LANE_ACCEPTED: YES|NO|N/A
DUAL_JUDGE_REQUIRED: YES|NO
DUAL_JUDGE_EVIDENCE: <...|N/A>
FINDINGS: <...>
CROSS_JUDGE_SAMPLED: YES|NO
CROSS_JUDGE_RESULT: CONCUR|DIVERGE|N/A
```

### CEO Paste Block
```text
ROUND: <round_id>
DECISION: GO|HOLD|REFRAME
RATIONALE: <...>
BLOCKERS: <...>
NEXT_DIRECTIVE: <...>
```

---

## Example: Simple Bug Fix Round

### Worker Contract
```text
ROUND: 20260304_150000
ORIGINAL_INTENT: Fix BOM encoding crash in JSON loader
DELIVERABLE_THIS_SCOPE: Change encoding parameter from utf-8 to utf-8-sig
POSITIONING_LOCK: Keep scope strictly to BOM decoding fix in existing loader path
TASK_GRANULARITY_LIMIT: 1
INTUITION_GATE: MACHINE_DEFAULT
INTUITION_GATE_RATIONALE: Deterministic low-blast bug fix with direct reproduction evidence
INTUITION_GATE_ACK: N/A
INTUITION_GATE_ACK_AT_UTC: N/A
DECISION_CLASS: TWO_WAY
EXECUTION_LANE: FAST
RISK_TIER: LOW
FAST_LANE_REQUEST: YES
FAST_LANE_ELIGIBILITY_LOC_LE_20: YES
FAST_LANE_ELIGIBILITY_FILES_LE_2: YES
FAST_LANE_ELIGIBILITY_NO_SCHEMA_API_CHANGE: YES
FAST_LANE_ELIGIBILITY_NO_SECURITY_COMPLIANCE_IMPACT: YES
FAST_LANE_ELIGIBILITY_NO_NEW_DEP_OR_INFRA: YES
NON_GOALS: Refactor JSON loader, add new features, change error handling
CHANGE_BUDGET: 1 file, 1 line change, 0 architecture changes
DELETE_BEFORE_ADD_TARGETS: none
ADDITIONS_AFTER_DELETE: none
OWNED_FILES: scripts/validate_loop_closure.py
INTERFACE_INPUTS: docs/context/phase_end_logs/*
INTERFACE_OUTPUTS: docs/context/loop_closure_status_latest.json
PARALLEL_SHARD_ID: N/A
PRE_EXEC_DISAGREEMENT_CAPTURE: none
DONE_WHEN: Tests pass, no BOM crash on real phase_end_logs files
DONE_WHEN_CHECKS: tdd_contract_gate,freshness_gate,go_signal_truth_gate
REFACTOR_BUDGET_MINUTES: 20
REFACTOR_SPEND_MINUTES: 8
REFACTOR_BUDGET_EXCEEDED_REASON: N/A
STOP_CONDITION: If fix requires >10 LOC or architectural change
EVIDENCE_REQUIRED: Test run output showing BOM files load successfully
TDD_MODE: REQUIRED
RED_TEST_COMMAND: pytest tests/test_json_loader.py::test_bom_file_fails_without_sig -q
RED_TEST_RESULT: FAIL (UnicodeDecodeError reproduced before fix)
GREEN_TEST_COMMAND: pytest tests/test_json_loader.py::test_bom_file_loads_with_sig -q
GREEN_TEST_RESULT: PASS (1 passed)
COUNTEREXAMPLE_TEST_COMMAND: N/A
COUNTEREXAMPLE_TEST_RESULT: N/A (LOW risk + TWO_WAY change)
REFACTOR_NOTE: No refactor beyond minimal fix to keep blast radius bounded.
TDD_NOT_APPLICABLE_REASON: N/A
MOCK_POLICY_MODE: STRICT
MOCKED_DEPENDENCIES: filesystem_adapter
INTEGRATION_COVERAGE_FOR_MOCKS: YES
TRIGGERED_EXPERTS: none (straightforward fix)
CAP_APPLIED: 0/3 per round, 0/5 per task
```

### Auditor Review
```text
ROUND: 20260304_150000
SCOPE_MATCH: PASS
FAST_LANE_ACCEPTED: YES
DUAL_JUDGE_REQUIRED: NO
DUAL_JUDGE_EVIDENCE: N/A
OVERENGINEER_FLAGS: none
REQUIRED_CUTS: none
MINIMAL_NEXT_STEP: Deploy fix and verify on production logs
FINDINGS: none
CROSS_JUDGE_SAMPLED: YES
CROSS_JUDGE_RESULT: CONCUR
```

### CEO Decision
```text
ROUND: 20260304_150000
DECISION: GO
RATIONALE: Minimal fix, no scope creep, tests pass, ready for deployment
BLOCKERS: none
NEXT_DIRECTIVE: Continue with W11 shadow runs
```

---

## Example: New System Component Round

### Worker Contract
```text
ROUND: 20260304_160000
ORIGINAL_INTENT: Implement auditor calibration reporting system
DELIVERABLE_THIS_SCOPE: Calibration script with weekly/dossier modes, 28 tests
POSITIONING_LOCK: Deliver reporting pipeline only; no new governance gates in this round
TASK_GRANULARITY_LIMIT: 2
INTUITION_GATE: HUMAN_REQUIRED
INTUITION_GATE_RATIONALE: Promotion-impacting governance output requires explicit PM/CEO acknowledgment before execution
INTUITION_GATE_ACK: PM_ACK
INTUITION_GATE_ACK_AT_UTC: 2026-03-04T16:05:00Z
DECISION_CLASS: TWO_WAY
EXECUTION_LANE: STANDARD
RISK_TIER: HIGH
FAST_LANE_REQUEST: NO
FAST_LANE_ELIGIBILITY_LOC_LE_20: NO
FAST_LANE_ELIGIBILITY_FILES_LE_2: NO
FAST_LANE_ELIGIBILITY_NO_SCHEMA_API_CHANGE: NO
FAST_LANE_ELIGIBILITY_NO_SECURITY_COMPLIANCE_IMPACT: YES
FAST_LANE_ELIGIBILITY_NO_NEW_DEP_OR_INFRA: YES
NON_GOALS: Rewrite auditor rules, add new gates, redesign FP ledger, add UI
CHANGE_BUDGET: 2 files (script + tests), 0 architecture changes (uses existing schemas)
DELETE_BEFORE_ADD_TARGETS: none
ADDITIONS_AFTER_DELETE: tests/test_auditor_calibration_report.py
OWNED_FILES: scripts/auditor_calibration_report.py,tests/test_auditor_calibration_report.py
INTERFACE_INPUTS: docs/context/phase_end_logs/*,docs/context/auditor_fp_ledger.json
INTERFACE_OUTPUTS: docs/context/auditor_calibration_report.json,docs/context/auditor_promotion_dossier.json
LOGIC_SPINE_INDEX_ARTIFACT: docs/logic_spine_index.md
CHANGE_MANIFEST_ARTIFACT: docs/context/change_manifest_latest.md
ALLOWED_BOUNDARY_REFS: docs/phase_brief/phase24c-brief.md,docs/loop_operating_contract.md
NON_GOAL_REFS: docs/phase_brief/phase24c-brief.md#non-goals,docs/loop_operating_contract.md
PARALLEL_SHARD_ID: shard-auditor-reporting
PRE_EXEC_DISAGREEMENT_CAPTURE: D07|coverage threshold expectation|worker+qa|2026-03-04T16:10:00Z
DONE_WHEN: Script runs on real data, 28 tests pass, dossier validates C0-C5
DONE_WHEN_CHECKS: tdd_contract_gate,go_signal_truth_gate,weekly_summary_truth_gate,exec_memory_truth_gate
REFACTOR_BUDGET_MINUTES: 90
REFACTOR_SPEND_MINUTES: 95
REFACTOR_BUDGET_EXCEEDED_REASON: Required additional cleanup to preserve report determinism and test stability.
STOP_CONDITION: If implementation requires >3 new files or schema changes
EVIDENCE_REQUIRED: Test output (28 pass), dossier JSON with criteria validation
TDD_MODE: REQUIRED
RED_TEST_COMMAND: pytest tests/test_auditor_calibration_report.py::test_missing_criteria_blocks_dossier -q
RED_TEST_RESULT: FAIL before implementation (criteria mismatch reproduced)
GREEN_TEST_COMMAND: pytest tests/test_auditor_calibration_report.py -q
GREEN_TEST_RESULT: PASS (28 passed)
COUNTEREXAMPLE_TEST_COMMAND: pytest tests/test_auditor_calibration_report.py::test_rejects_incomplete_annotation_coverage -q
COUNTEREXAMPLE_TEST_RESULT: PASS (counterexample validated, unsafe promotion path blocked)
REFACTOR_NOTE: Consolidated helper function names after green pass; no behavior change.
TDD_NOT_APPLICABLE_REASON: N/A
MOCK_POLICY_MODE: STRICT
MOCKED_DEPENDENCIES: phase_end_log_reader,clock_source
INTEGRATION_COVERAGE_FOR_MOCKS: YES
TRIGGERED_EXPERTS: principal (new_system_component), riskops (fp_tracking), qa (new_test_file)
CAP_APPLIED: 3/3 per round, 3/5 per task
```

### Auditor Review
```text
ROUND: 20260304_160000
SCOPE_MATCH: PASS
FAST_LANE_ACCEPTED: N/A
DUAL_JUDGE_REQUIRED: YES
DUAL_JUDGE_EVIDENCE: docs/context/cross_judge_round_20260304_160000.md
OVERENGINEER_FLAGS: none
REQUIRED_CUTS: none
MINIMAL_NEXT_STEP: Execute first shadow cycle and annotate C/H findings
FINDINGS: none (all 28 tests pass, criteria logic correct)
CROSS_JUDGE_SAMPLED: NO
CROSS_JUDGE_RESULT: N/A
```

### CEO Decision
```text
ROUND: 20260304_160000
DECISION: GO
RATIONALE: Scope respected, tests comprehensive, ready for operational use
BLOCKERS: none
NEXT_DIRECTIVE: Start shadow calibration window (2-week evidence collection)
```
