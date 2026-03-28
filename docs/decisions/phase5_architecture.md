# ADR-001: Phase 5 Architecture - Kernel/Plugin Boundary

**Status**: Draft
**Date**: 2026-03-11
**Deciders**: PM, CEO
**Context**: Phase 5 explores how the existing SOP control-plane kernel could evolve into a broader adaptive agent system.

> Boundary note: this ADR is a future-state architecture draft. It does not redefine the currently shipped `v1` product boundary. The shipped `v1` surface in this repository is the local script-driven governance control plane: startup, loop, closure, takeover, optional supervision, and the supporting docs/tests/artifacts for that path. Plugin architecture, benchmark-driven policy tuning, skills productization, subagent routing, worker execution loops, rollout automation, adaptive guardrails, and hierarchical memory optimization remain future-state only until separately approved, implemented, and added to the release contract.

---

## Decision

Freeze the current shipped `v1` boundary around the existing control-plane kernel, while keeping Phase 5 plugin and automation surfaces as draft future-state proposals.

This ADR therefore does two things:

1. records what is currently shipped and authoritative today, and
2. frames the plugin/worker/rollout architecture as proposed future-state work, not as an already shipped product surface.

---

## Context

Phase 5 explores adding:
- plugin architecture for tunable guardrails,
- model benchmark harnesses for capability-driven policy,
- skills libraries for reusable patterns,
- worker and rollout automation,
- hierarchical memory optimization.

**Critical question**: what stays in the authoritative kernel, and what remains future-state productization work?

**Constraint**: future-state work must not weaken existing governance (`docs/loop_operating_contract.md`, truth gates, auditor review, CEO GO signal).

---

## Current Shipped v1 Boundary

The currently shipped `v1` product is the script-driven governance control plane that already exists in this repository. Its authoritative surface is:

- `scripts/startup_codex_helper.py` for startup intake and round initialization,
- `scripts/run_loop_cycle.py` for loop execution and artifact refresh,
- `scripts/validate_loop_closure.py` for ready/not-ready closure validation,
- `scripts/print_takeover_entrypoint.py` for deterministic takeover guidance,
- `scripts/supervise_loop.py` for optional supervision,
- `docs/runbook_ops.md`, `OPERATOR_LOOP_GUIDE.md`, and `docs/loop_operating_contract.md` for the active operator contract,
- `docs/context/` for canonical runtime artifacts,
- the release and test surface that validates that operator flow.

No plugin layer, worker fleet, benchmark product surface, skills extension system, rollout automation layer, or memory-optimization subsystem is currently shipped as part of `v1`.

---

## Kernel Boundary (Authoritative - Shipped v1)

### 1. Authority Model
**Location**: `docs/loop_operating_contract.md`

**Stays in Kernel**:
- PM/CEO decision authority
- Auditor PASS/BLOCK authority
- Source-of-truth hierarchy (decision log.md, phase briefs, dossier, calibration, GO signal)
- Startup intake requirements (ORIGINAL_INTENT, DELIVERABLE_THIS_SCOPE, DONE_WHEN, etc.)
- Round contract requirements (DECISION_CLASS, RISK_TIER, INTUITION_GATE, etc.)

**Rationale**: These define WHO can decide WHAT. Plugins cannot override authority.

---

### 2. Truth Gates
**Location**: `scripts/validate_*.py`

**Stays in Kernel**:
- `validate_loop_closure.py` - authoritative ready/not-ready verdict
- `validate_ceo_go_signal_truth.py` - GO signal truth-check
- `validate_round_contract_checks.py` - DONE_WHEN validation
- `validate_counterexample_gate.py` - counterexample requirement
- `validate_dual_judge_gate.py` - dual-judge requirement for ONE_WAY HIGH
- `validate_refactor_mock_policy.py` - refactor budget enforcement
- All other `validate_*.py` scripts in truth-gate stack

**Rationale**: Truth gates are the enforcement layer. Plugins cannot bypass validation.

---

### 3. Closure & Escalation
**Location**: `docs/context/loop_closure_status_latest.json`

**Stays in Kernel**:
- READY_TO_ESCALATE verdict logic
- Required artifact checks (dossier, calibration, GO signal, startup card, exec memory)
- Freshness gates (72h threshold)
- Phase-end gate stack (context build, worker aggregate, traceability, evidence hashes, etc.)

**Rationale**: Closure is the final gate before CEO escalation. Plugins cannot auto-close.

---

### 4. Cycle Orchestration
**Location**: `scripts/run_loop_cycle.py`

**Stays in Kernel**:
- Phase-end handover orchestration
- Weekly calibration refresh
- Dossier refresh
- CEO GO signal refresh
- CEO weekly summary
- Exec-memory packet build
- Context compaction evaluation
- Truth gate execution
- Closure validation
- Round-contract checks
- Advisory persistence

**Rationale**: Cycle orchestrator is the heartbeat. Plugins can add steps but cannot remove kernel steps.

---

### 5. Supervision & Staleness Detection
**Location**: `scripts/supervise_loop.py`

**Stays in Kernel**:
- Staleness polling (detect missing/stale artifacts)
- Manual action queue emission
- Blocking detection (identify what's blocking progress)

**Rationale**: Supervision is the safety net. Plugins cannot disable supervision.

---

## Future-State Plugin Layer (Proposed Only - Not Shipped in v1)

Everything in this section is future-state only. These surfaces may inform future policy or automation, but they are not part of the currently shipped `v1` product boundary or release contract.

**Critical distinction**: "advisory" means plugins would **recommend** actions while the kernel would continue to **enforce** decisions.

### Plugin Recommendation vs Kernel Enforcement

**Plugin Role**: Measure, analyze, recommend
- Benchmark harness measures model capability → recommends guardrail strength
- Risk assessment analyzes task → recommends approval routing
- Skills define best practices → recommend additional safety requirements

**Kernel Role**: Validate, enforce, execute
- Kernel approval gate validates plugin recommendations against policy
- Kernel enforces authority boundaries (PM/CEO/Auditor decisions)
- Kernel executes actual approvals, escalations, or rejections

**Example Flow**:
```
1. Plugin risk assessment: "Task is LOW risk, recommend auto-approve"
2. Kernel approval gate validates:
   - Is task actually LOW risk per kernel classification? ✓
   - Does policy allow auto-approve for LOW risk? ✓
   - Are all required artifacts present? ✓
3. Kernel executes: Auto-approve (sandbox + automated tests)

Counter-example (plugin recommendation rejected):
1. Plugin risk assessment: "Task is LOW risk, recommend auto-approve"
2. Kernel approval gate validates:
   - Is task actually LOW risk per kernel classification? ✗ (Kernel classifies as HIGH)
3. Kernel overrides: Route to CEO GO signal (plugin recommendation rejected)
```

**Key Principle**: Plugins cannot execute approvals directly. All approvals flow through kernel enforcement.

---

### 1. Benchmark Harness
**Location**: `benchmark/` (future-state)

**Plugin Layer**:
- Model capability measurement (code_generation, sql_accuracy, reasoning_depth, hallucination_rate)
- Eval suites (Promptfoo configs, Inspect tasks/scorers)
- Benchmark results (opus_4_6_baseline.json)
- Guardrail recommendations (sql_tasks=tight, react_tasks=loose)

**Authority Boundary**:
- Benchmarks **inform** guardrail policy
- Benchmarks **do not** auto-approve high-risk tasks
- Policy changes require PM/CEO approval in `decision log.md`

**Rationale**: Benchmarks measure capability, but humans decide policy.

---

### 2. Skills Registry
**Location**: `skills/` (future-state)

**Plugin Layer**:
- Skill definitions (skill.yaml: name, version, description, category, steps)
- Guardrail profiles (guardrails.yaml: gates, failure_handling)
- Eval requirements (eval.yaml: benchmark thresholds per skill)
- Examples (postgres_add_column.md, functional_component.md)

**Authority Boundary**:
- Skills **recommend** guardrails (e.g., safe-db-migration requires rollback plan, auditor review, CEO GO signal)
- Skills **cannot weaken** kernel guardrails (kernel is floor, not ceiling)
- Skills **cannot bypass** truth gates or closure validation
- Skill activation requires extension allowlist approval

**Rationale**: Skills package best practices, but kernel enforces minimums.

---

### 3. Subagent Routing Matrix
**Location**: `subagent_routing_matrix.yaml` (future-state)

**Plugin Layer**:
- Role definitions (startup_deputy, execution_deputy, specialist_deputy, etc.)
- Context slicing (required_artifacts, excluded_artifacts, max_context_tokens per role)
- Memory optimization (reduce context bleed)

**Authority Boundary**:
- Routing **optimizes** memory usage
- Routing **does not change** authority model (PM/CEO/Auditor authority unchanged)
- Routing **does not bypass** source-of-truth hierarchy
- Subagents remain stateless; supervisor owns memory

**Rationale**: Routing is performance optimization, not governance change.

---

### 4. Worker Inner Loop
**Location**: `worker/` (future-state)

**Plugin Layer**:
- Repo map compression (repo_map.py: file → symbols → dependencies)
- Lint/test repair loop (lint_repair_loop.py, test_repair_loop.py)
- Sandbox execution (sandbox_executor.py: Docker-based isolation)

**Authority Boundary**:
- Worker loop **operates within** guardrails
- Worker loop **cannot bypass** auditor review for high-risk changes
- Worker loop **cannot bypass** CEO GO signal for ONE_WAY decisions
- Repair loop has max iteration limit (e.g., 5 attempts) then escalates to human

**Rationale**: Worker loop is fast iteration, but kernel gates remain required.

---

### 5. Rollout Automation
**Location**: `rollout/` (future-state)

**Plugin Layer**:
- GitHub automation (github_automation.py: issue-to-PR workflows)
- Sandbox runner (sandbox_runner.py: Docker-based execution)
- Risk assessment (approval_gate.py: classifies tasks as low/medium/high risk)

**Authority Boundary**:
- Risk assessment **recommends** approval routing (low → auto, medium → auditor, high → CEO)
- Kernel approval gate **enforces** routing decision (validates risk classification, checks policy, executes approval/escalation)
- Plugin risk assessment **cannot override** kernel classification (if kernel says HIGH, plugin cannot downgrade to LOW)
- Rollout automation **only executes** after kernel approval gate validates and approves
- Canary rollout requires PM/CEO approval before full rollout

**Rationale**: Plugins recommend, kernel enforces. Automation is for volume, not for bypassing governance.

---

### 6. Adaptive Guardrails and Memory Optimization
**Location**: `.sop_config.yaml` and related future-state memory policy/config surfaces

**Plugin Layer**:
- Guardrail strength tuning (loose/medium/tight per project/task)
- Model capability → guardrail strength mapping
- Failure → policy update feedback loop
- Hierarchical memory optimization and context-shaping policy

**Authority Boundary**:
- Adaptive guardrails **tune strength** based on model capability
- Adaptive guardrails **cannot weaken** kernel minimums
- Policy changes require PM/CEO approval in `decision log.md`
- No silent policy updates (all changes logged and approved)

**Rationale**: Adaptive tuning is optimization, but kernel sets floor.

---

## Boundary Rules for Any Future Phase 5 Work

Until a future-state surface is separately approved, implemented, and added to the release contract:

- it is not part of the shipped `v1` product boundary,
- it must not appear in release docs as a shipped capability,
- it must not weaken the kernel authority model or truth-gate stack,
- it must not be treated as an alternative source of truth to the active operator flow.

---

## Example Enforcement Patterns for a Future Plugin Layer

### 1. Explicit Reject List (Code-Enforced)
```python
# Example: benchmark harness
def apply_guardrail_recommendation(benchmark_result, task):
    recommendation = benchmark_result.guardrail_recommendations[task.domain]

    # REJECT: benchmark cannot auto-approve high-risk
    if task.risk_tier == "HIGH":
        return "require_ceo_go_signal"  # Always escalate, ignore benchmark

    # ACCEPT: benchmark can inform policy for low/medium risk
    if task.risk_tier in ["LOW", "MEDIUM"]:
        return recommendation  # Use benchmark recommendation
```

### 2. Kernel Guardrail Floor (Cannot Be Weakened)
```yaml
# Example: skill guardrail profile
# skills/safe_db_migration/guardrails.yaml
gates:
  post_execution:
    - auditor_review_required: true      # Skill requires auditor
    - ceo_go_signal_required: true       # Skill requires CEO GO

# Kernel enforcement:
# - If kernel says "HIGH risk requires CEO GO", skill cannot override to "no CEO GO needed"
# - Skill can only ADD gates (e.g., require rollback plan), not REMOVE kernel gates
```

### 3. Authority Validation (Runtime Check)
```python
# Example: subagent routing
def route_subagent(role, task):
    context = load_context_for_role(role)

    # VALIDATE: routing does not change authority
    assert task.decision_authority == "CEO"  # Authority unchanged
    assert task.auditor_review_required == True  # Gates unchanged

    # ACCEPT: routing only optimizes context size
    return execute_with_minimal_context(task, context)
```

### 4. Approval Logging (Audit Trail)
```python
# Example: adaptive policy update
def update_policy_from_failure(failure, new_policy):
    # REJECT: no silent policy updates
    if not pm_ceo_approved(new_policy):
        raise PolicyChangeRequiresApproval(
            "Policy changes must be recorded in decision log.md"
        )

    # ACCEPT: log and apply approved policy
    log_to_decision_log(new_policy, approver="PM/CEO", date=now())
    apply_policy(new_policy)
```

---

## Illustrative Future-State Integration Points

### 1. Startup Intake → Skills Selection
```
Kernel: startup_codex_helper.py captures ORIGINAL_INTENT, RISK_TIER, EXECUTION_LANE
Plugin: Skills registry suggests relevant skills based on EXECUTION_LANE
Kernel: Extension allowlist approves/denies skill activation
Result: Approved skills loaded, guardrail profiles merged with kernel minimums
```

### 2. Benchmark Results → Guardrail Tuning
```
Plugin: Benchmark harness measures model capability (sql_accuracy=0.78)
Plugin: Recommends guardrail strength (sql_tasks=tight)
Kernel: PM/CEO reviews recommendation, approves policy change in decision log.md
Kernel: Updated policy applied to future rounds
Result: Guardrails adapt to model capability, but humans approve changes
```

### 3. Worker Loop → Truth Gates
```
Plugin: Worker loop iterates (code → lint → test → fix)
Plugin: Repair loop converges after 3 iterations
Kernel: validate_round_contract_checks.py runs DONE_WHEN validation
Kernel: validate_loop_closure.py checks all required artifacts
Result: Worker optimizes iteration, kernel validates completion
```

### 4. Rollout Automation → Risk Assessment
```
Plugin: GitHub automation detects new issue (dependency update)
Plugin: Risk assessment classifies as LOW risk, recommends auto-approve
Kernel: Validates risk classification, checks policy, approves execution
Kernel: Approved automation executes in sandbox with automated tests
Kernel: If risk assessment fails or task is HIGH risk, route to CEO GO signal
Result: Low-risk automation (kernel-approved), high-risk governance
```

---

## Decision Rationale

### Why This Boundary?

1. **Preserves existing governance**: Kernel authority model unchanged
2. **Enables adaptive optimization**: Plugin layer can tune performance without weakening safety
3. **Clear audit trail**: All policy changes logged in decision log.md
4. **Fail-safe defaults**: Plugins cannot bypass kernel gates; kernel is floor, not ceiling
5. **Explicit reject list**: Code-enforced boundaries prevent accidental bypass

### What This Enables in a Future Phase

1. **Adaptive guardrails**: Tune strength based on model capability
2. **Skills library**: Package reusable patterns without hardcoding
3. **Memory optimization**: Reduce context bleed via subagent routing
4. **Fast iteration**: Worker loop optimizes lint/test cycles
5. **Volume automation**: Rollout automation for low-risk, high-volume tasks

### What This Prevents

1. **Authority bypass**: Plugins cannot override PM/CEO/Auditor decisions
2. **Silent policy changes**: All changes require approval in decision log.md
3. **Weakened guardrails**: Kernel minimums cannot be lowered by plugins
4. **Auto-approval of high-risk**: Benchmarks inform, humans decide
5. **Governance split**: Single source-of-truth hierarchy maintained

---

## Open Questions for PM/CEO

1. **Skill authoring authority**: Who can contribute skills to registry?
   - Recommendation: Internal team only for Phase 5, community in Phase 6

2. **Benchmark frequency**: How often re-run model benchmarks?
   - Recommendation: Per model version release + monthly

3. **Guardrail override**: Can PM/CEO override adaptive guardrails for specific tasks?
   - Recommendation: Yes, with explicit override log in decision log.md

4. **Rollout automation scope**: Max risk level for auto-approval?
   - Recommendation: LOW only, MEDIUM+ requires human review

5. **Plugin approval process**: How are new plugins/skills approved?
   - Recommendation: PM/CEO approval in decision log.md, then added to extension allowlist

---

## Next Steps

1. Keep this ADR marked as draft future-state architecture until Phase 5 surfaces are explicitly approved.
2. Record any future approval in `docs/decision log.md`.
3. Add separate ADRs for any future shipped surface before it is included in release criteria.
4. Update `README.md` and `RELEASING.md` only when a future-state surface becomes real shipped scope.

---

**Status**: Draft future-state proposal awaiting PM/CEO approval
