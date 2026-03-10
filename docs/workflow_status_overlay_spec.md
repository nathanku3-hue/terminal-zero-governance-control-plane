# Workflow Status Overlay Specification v1.0

**Owner:** PM
**Status:** ACTIVE
**Version:** 1.0.0
**Last Updated:** 2026-03-10

---

## 1. Purpose & Scope

### Intent

The workflow status overlay is an **advisory-only** derived-state artifact that aggregates existing loop artifacts into a structured JSON view. It provides a machine-readable snapshot of workflow node statuses without creating new control-plane authority.

### Key Principles

- **Advisory Only**: Does not create new gates, authority paths, or approval requirements
- **Derived State**: All status information is computed from existing authoritative artifacts
- **Opt-In**: Generated only when explicitly requested via command-line flag
- **Non-Blocking**: Generation failures do not affect loop execution or exit codes
- **Canonical API**: `docs/context/` remains the authoritative artifact surface

### Use Cases

1. **Operator Dashboard**: Quick visual status of all workflow nodes
2. **Agent Context**: Structured input for AI agents to understand current state
3. **Debugging**: Trace which nodes are blocking and why
4. **Audit Trail**: Timestamped snapshot of workflow state with artifact provenance

---

## 2. Non-Goals (Explicit)

The workflow status overlay explicitly does NOT:

- ❌ Create new gate or authority path
- ❌ Replace existing artifacts as source of truth
- ❌ Couple to CI/CD pipelines in v0
- ❌ Run as a long-lived service
- ❌ Change exit codes or control flow
- ❌ Add new approval requirements
- ❌ Modify existing artifact contracts
- ❌ Introduce new runtime dependencies

---

## 3. JSON Schema Definition

### Top-Level Structure

```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "2026-03-10T12:00:00Z",
  "repo_root": "/path/to/repo",
  "source_of_truth_policy": "docs/loop_operating_contract.md#source-of-truth-hierarchy",
  "overall_status": "yellow",
  "overall_summary": "Execution HOLD, ValidationClosure NOT_READY",
  "nodes": [...],
  "role_views": {...},
  "artifact_inputs": [...]
}
```

### Node Object Schema

Each node in the `nodes` array has:

```json
{
  "node_id": "startup",
  "title": "Startup Gate",
  "owner_role": "PM",
  "advisory_roles": ["Worker", "Auditor"],
  "status_color": "green",
  "progress_state": "READY",
  "complexity_band": "LOW",
  "rigor_mode": "STANDARD",
  "capability_band": "agent_ok",
  "source_of_truth": "docs/context/startup_intake_latest.json",
  "supporting_artifacts": [
    "docs/context/init_execution_card_latest.md"
  ],
  "key_signals": [
    "startup_gate.status=READY_TO_EXECUTE"
  ],
  "blockers": [],
  "next_action": "Proceed to execution",
  "updated_at_utc": "2026-03-10T11:00:00Z"
}
```

### Field Definitions

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `schema_version` | string | "1.0.0" | Schema version for compatibility |
| `generated_at_utc` | string | ISO 8601 | Generation timestamp |
| `repo_root` | string | path | Repository root directory |
| `source_of_truth_policy` | string | reference | Link to authority hierarchy doc |
| `overall_status` | string | green/yellow/red/gray | Worst status across critical nodes |
| `overall_summary` | string | text | Human-readable summary |
| `nodes` | array | node objects | All workflow nodes |
| `role_views` | object | role → nodes | Nodes grouped by owner_role |
| `artifact_inputs` | array | provenance objects | Input artifacts with timestamps |

### Node Field Definitions

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `node_id` | string | identifier | Unique node identifier |
| `title` | string | text | Human-readable node name |
| `owner_role` | string | PM/CEO/Worker/Auditor/QA | Primary decision owner |
| `advisory_roles` | array | role strings | Supporting/advisory roles |
| `status_color` | string | green/yellow/red/gray/blue | Visual status indicator |
| `progress_state` | string | READY/IN_PROGRESS/BLOCKED/NOT_STARTED | Execution state |
| `complexity_band` | string | LOW/MEDIUM/HIGH | Estimated complexity |
| `rigor_mode` | string | STANDARD/FAST/HIGH_RIGOR | Quality/speed tradeoff |
| `capability_band` | string | agent_ok/agent_plus_review/human_required | Automation boundary |
| `source_of_truth` | string | artifact path | Primary authoritative artifact |
| `supporting_artifacts` | array | artifact paths | Additional evidence artifacts |
| `key_signals` | array | signal strings | Key status indicators |
| `blockers` | array | blocker strings | Current blocking issues |
| `next_action` | string | text | Recommended next step |
| `updated_at_utc` | string | ISO 8601 | Last update timestamp |

---

## 4. Node Definitions

### 4.1 PublicEntry

**Purpose:** Public-facing documentation and entry points

**Owner Role:** PM
**Advisory Roles:** Worker, CEO

**Source of Truth:**
- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`

**Status Derivation:**
- Green: All required docs present and recently updated
- Yellow: Some docs stale (>90 days)
- Gray: Missing required docs

**Capability Band:** `agent_ok` (docs can be updated by agents within guidelines)

---

### 4.2 DocsSpine

**Purpose:** Governance documentation spine

**Owner Role:** PM
**Advisory Roles:** CEO, Auditor

**Source of Truth:**
- `docs/loop_operating_contract.md`
- `docs/round_contract_template.md`
- `docs/decision_authority_matrix.md`
- `docs/expert_invocation_policy.md`

**Status Derivation:**
- Green: All governance docs present and consistent
- Yellow: Docs present but version mismatches detected
- Red: Critical governance doc missing

**Capability Band:** `human_required` (governance changes require PM/CEO approval)

---

### 4.3 Startup

**Purpose:** Round initialization and intake

**Owner Role:** PM
**Advisory Roles:** Worker, Auditor

**Source of Truth:**
- `docs/context/startup_intake_latest.json`
- `docs/context/init_execution_card_latest.md`

**Status Derivation:**
- Green: `startup_gate.status=READY_TO_EXECUTE`
- Yellow: startup artifact exists and `startup_gate.status!=READY_TO_EXECUTE`
- Gray: Startup artifacts missing

**Key Signals:**
- `startup_gate.status`
- `intuition_gate`
- `intuition_gate_ack` (if HUMAN_REQUIRED)

**Blockers:**
- Missing required interrogation fields
- Intuition gate not acknowledged when required

**Capability Band:** `agent_plus_review` (agent can draft, PM reviews)

---

### 4.4 RoundContract

**Purpose:** Round scope and execution contract

**Owner Role:** Worker
**Advisory Roles:** Auditor, PM

**Source of Truth:**
- `docs/context/round_contract_latest.md`

**Status Derivation:**
- Green: Contract complete with all required fields
- Yellow: Contract present but missing optional fields
- Red: Contract missing required fields or Phase C fail-closed requirements violated
- Gray: No contract found

**Key Signals:**
- `DECISION_CLASS`
- `RISK_TIER`
- `EXECUTION_LANE`
- `TDD_MODE`
- `DONE_WHEN_CHECKS`

**Blockers:**
- Missing `DECISION_CLASS` or `RISK_TIER`
- Invalid `EXECUTION_LANE` for scope
- TDD contract incomplete

**Capability Band:** `agent_ok` (worker owns contract)

---

### 4.5 Authority

**Purpose:** Decision authority and expert routing

**Owner Role:** PM
**Advisory Roles:** CEO, Auditor

**Source of Truth:**
- `docs/decision_authority_matrix.md`
- `docs/expert_invocation_policy.md`
- `docs/disagreement_taxonomy.md`

**Status Derivation:**
- Green: Authority docs present and no active conflicts
- Yellow: Authority docs present, minor conflicts logged
- Red: Authority conflict unresolved or docs missing

**Capability Band:** `human_required` (authority changes require CEO approval)

---

### 4.6 Execution

**Purpose:** Loop cycle execution and results

**Owner Role:** Worker
**Advisory Roles:** Auditor, QA

**Source of Truth:**
- `docs/context/loop_cycle_summary_latest.json`

**Status Derivation:**
- Green: `final_result=PASS`
- Yellow: `final_result=HOLD`
- Red: `final_result=FAIL` or `final_result=ERROR`
- Gray: No cycle summary found

**Key Signals:**
- `final_result`
- `step_summary.pass_count`
- `step_summary.fail_count`
- `step_summary.hold_count`

**Blockers:**
- Failed steps in cycle
- Dossier criteria not met
- Closure validation failures

**Capability Band:** `agent_ok` (worker executes within contract)

---

### 4.7 MemoryArtifacts

**Purpose:** Execution memory and advisory handoffs

**Owner Role:** Worker
**Advisory Roles:** PM, CEO

**Source of Truth:**
- `docs/context/exec_memory_packet_latest.json`
- `docs/context/next_round_handoff_latest.json`
- `docs/context/expert_request_latest.json`
- `docs/context/pm_ceo_research_brief_latest.json`
- `docs/context/board_decision_brief_latest.json`

**Status Derivation:**
- Green: All memory artifacts present and fresh (<48h)
- Yellow: Some artifacts missing or stale
- Gray: No memory artifacts found

**Key Signals:**
- `exec_memory_packet` presence
- Advisory handoff artifact presence
- Artifact freshness

**Capability Band:** `agent_ok` (worker generates memory artifacts)

---

### 4.8 ValidationClosure

**Purpose:** Loop closure validation and escalation readiness

**Owner Role:** Auditor
**Advisory Roles:** PM, CEO

**Source of Truth:**
- `docs/context/loop_closure_status_latest.json`

**Status Derivation:**
- Green: `result=READY_TO_ESCALATE`
- Yellow: `result=NOT_READY`
- Red: `result=INPUT_OR_INFRA_ERROR`
- Gray: No closure status found

**Key Signals:**
- `result`
- `summary.pass_count`
- `summary.fail_count`
- Failed check names

**Blockers:**
- `go_signal_action_gate` not GO
- `tdd_contract_gate` not PASS
- `done_when_checks_gate` not PASS
- Missing required artifacts

**Capability Band:** `agent_plus_review` (auditor validates, PM/CEO escalate)

---

### 4.9 Measurement

**Purpose:** Phase C measurement and data collection

**Owner Role:** PM
**Advisory Roles:** CEO, Worker

**Source of Truth:**
- `phase_c_measurement/live_rounds.csv`
- `phase_c_measurement/README.md`

**Status Derivation:**
- Gray: Measurement directory absent
- Blue: Measurement active, below threshold
- Yellow: Measurement active, approaching threshold
- Green: Measurement complete, threshold met

**Key Signals:**
- Round count in `live_rounds.csv`
- Target threshold from README
- Collection progress percentage

**Capability Band:** `agent_ok` (automated measurement collection)

---

## 5. Source-of-Truth Hierarchy

The workflow status overlay respects the existing source-of-truth hierarchy defined in `docs/loop_operating_contract.md`:

1. **Init baseline product artifacts** (authoritative)
   - `top_level_PM.md`
   - Product spec / PRD

2. **Governance baseline** (authoritative)
   - `docs/decision log.md`

3. **Approved phase scope docs**
   - `docs/phase_brief/*.md`

4. **Generated execution artifacts**
   - Dossier, calibration report, GO signal, phase-end status/summary

5. **Worker-authored summaries and plans**
   - Useful for context, but non-authoritative if conflicting with sources 1-4

**Conflict Resolution:** If overlay-derived status conflicts with authoritative artifacts, the authoritative artifacts win. The overlay must be regenerated to reflect the correct state.

---

## 6. Capability/Boundary Mapping

The `capability_band` field maps workflow nodes to automation boundaries based on existing role and gate semantics from `docs/decision_authority_matrix.md` and `docs/expert_invocation_policy.md`.

### Capability Bands

| Band | Meaning | Agent Authority | Review Required |
|------|---------|-----------------|-----------------|
| `agent_ok` | Agent can proceed within existing boundaries | Full autonomy within contract | No pre-approval needed |
| `agent_plus_review` | Agent can proceed but requires review before escalation | Can execute, must pass review gate | QA/Auditor/Expert review required |
| `human_required` | PM/CEO/human acknowledgment needed | Cannot proceed without human approval | PM/CEO acknowledgment required |

### Mapping Rules

- **agent_ok**: Worker-owned nodes with clear contract boundaries (Execution, RoundContract, MemoryArtifacts, Measurement)
- **agent_plus_review**: Nodes requiring validation before escalation (Startup, ValidationClosure)
- **human_required**: Strategic/governance nodes requiring PM/CEO authority (DocsSpine, Authority, promotion decisions)

### Derivation from Existing Semantics

The capability band is derived from:
- `INTUITION_GATE` field in round contract (MACHINE_DEFAULT vs HUMAN_REQUIRED)
- `DECISION_CLASS` (ONE_WAY requires higher scrutiny)
- `RISK_TIER` (HIGH requires dual-judge review)
- Role authority from decision_authority_matrix.md
- Expert invocation requirements from expert_invocation_policy.md

---

## 7. Usage

### Generation Command

```bash
python scripts/print_takeover_entrypoint.py \
  --repo-root . \
  --workflow-status-json-out docs/context/workflow_status_latest.json
```

### Default Behavior (No Flag)

Without the `--workflow-status-json-out` flag, the script behaves exactly as before:
- Prints closure result and advisory handoffs to stdout
- Returns exit code based on closure result
- No workflow status JSON is generated

### Output Location

**Canonical location:** `docs/context/workflow_status_latest.json`

This follows the existing artifact convention where `docs/context/` contains all generated runtime state.

### Failure Handling

If workflow status generation fails:
- A warning is printed to stderr
- The script continues normally
- Exit code is NOT changed
- Existing output is NOT affected

This ensures the overlay is truly advisory and non-blocking.

---

## 8. Versioning

### Schema

**Current version:** `1.0.0`

The `schema_version` field in the JSON payload indicates the schema version. Future changes to the schema require a version bump following semantic versioning:

- **Major version** (2.0.0): Breaking changes to required fields or field semantics
- **Minor version** (1.1.0): Additive changes (new optional fields, new nodes)
- **Patch version** (1.0.1): Bug fixes, clarifications, no schema changes

### Compatibility

Consumers of the workflow status JSON should:
1. Check `schema_version` field
2. Validate against known schema versions
3. Gracefully handle unknown versions (warn and skip, or best-effort parsing)

---

## 9. Roadmap

### v0 (Current)

- ✅ JSON-only overlay
- ✅ 9 workflow nodes
- ✅ Role-based views
- ✅ Artifact provenance
- ✅ Optional generation via flag
- ✅ No control-plane changes

### v1 (Future)

- Add `docs/context/workflow_status_latest.md` (human-readable companion)
- Markdown includes: summary, legend, railway/flow view, collapsible node sections
- Update operator docs to reference both JSON and MD artifacts

### v2 (Future)

- Optional repo-local skill wrapper for convenience
- Skill runs overlay generation and surfaces artifact paths
- No duplicate logic in skill (thin wrapper only)

### v3 (Future - Only If Needed)

- MCP surface only if:
  - Multiple clients need live structured queries
  - Cross-repo workflow federation becomes necessary
  - Artifact-first workflow becomes too awkward operationally
- Until then: defer

---

## 10. Examples

### Example: Current Repo State (HOLD)

Based on the current repository state with `go_signal_action_gate=FAIL` and `closure result=NOT_READY`:

```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "2026-03-10T12:00:00Z",
  "overall_status": "yellow",
  "overall_summary": "Execution HOLD, ValidationClosure NOT_READY (go_signal_action_gate FAIL)",
  "nodes": [
    {
      "node_id": "startup",
      "status_color": "green",
      "progress_state": "READY",
      "key_signals": ["startup_gate.status=READY_TO_EXECUTE"]
    },
    {
      "node_id": "execution",
      "status_color": "yellow",
      "progress_state": "BLOCKED",
      "key_signals": ["final_result=HOLD"],
      "blockers": ["Dossier criteria not met: c3_min_weeks, c4b_annotation_coverage"]
    },
    {
      "node_id": "validation_closure",
      "status_color": "yellow",
      "progress_state": "BLOCKED",
      "key_signals": ["result=NOT_READY"],
      "blockers": ["go_signal_action_gate: Recommended action must be GO (actual=HOLD)"]
    }
  ]
}
```

---

## 11. Maintenance

### When to Regenerate

The workflow status overlay should be regenerated:
- After each loop cycle completion
- After manual artifact updates
- When operator needs current status snapshot
- Before CEO escalation review

### Staleness

The overlay is a point-in-time snapshot. If underlying artifacts change, the overlay becomes stale. Consumers should:
- Check `generated_at_utc` timestamp
- Compare against artifact modification time and regenerate if staleness exceeds acceptable threshold (e.g., 1 hour)

### Validation

To validate the overlay matches current state:
1. Check `artifact_inputs` provenance matches actual artifact timestamps
2. Verify `overall_status` reflects worst status across critical nodes
3. Confirm blockers match failed checks in closure status
4. Validate role_views correctly group nodes by owner_role

---

## 12. Governance

**Owner:** PM
**Approval Authority:** CEO (for spec changes)
**Review Cycle:** After v0 stabilization, before v1 planning

**Change Process:**
1. Propose spec change in decision log
2. PM reviews for consistency with existing contracts
3. CEO approves strategic direction
4. Update spec version
5. Implement changes
6. Update tests

---

