---
name: workflow-status
description: Aggregate phase deliverables and success criteria into workflow-type-aware status snapshot. Use after phase brief is loaded or when status check is needed.
---

# Workflow Status Skill

Read phase brief + current artifacts → emit workflow status snapshot with per-type aggregation.

## 0. Inputs
1. `phase_brief_path`: path to current phase brief (e.g., `docs/phase_brief/phase24c-brief.md`)
2. `project_init_path`: path to project init (default: `docs/context/project_init_latest.md`)
3. `context_dir`: path to context artifacts (default: `docs/context`)

## 1. Load Phase Brief
1. Read phase brief from `phase_brief_path`.
2. Extract:
   - `phase_id`
   - `phase_name`
   - `workflow_weight` (frontend/backend/governance/data/research percentages)
   - `deliverables` table (id, name, workflow_type, status, owner, evidence_path)
   - `success_criteria` table (id, name, workflow_type, threshold, status, measured_value, evidence_path)
   - `realm_specific_criteria` table (if present)
3. If phase brief is missing or malformed, emit `Verdict: BLOCK` and stop.

## 2. Load Project Init
1. Read project init from `project_init_path`.
2. Extract:
   - `workflow_type` (frontend_heavy | backend_heavy | governance_heavy | data_heavy | research_heavy | full_stack)
   - `main_realm`
   - `side_realms`
3. If project init is missing, emit `Verdict: BLOCK` and stop.

## 3. Load Current Artifacts
1. Read status artifacts from `context_dir`:
   - `ceo_go_signal.md` (for governance status)
   - `loop_closure_status_latest.json` (for backend/data status)
   - `auditor_promotion_dossier.json` (for governance status)
   - `fast_checks_status_latest.json` (for backend status)
   - Any evidence paths listed in deliverables/success_criteria
2. For each artifact:
   - If missing and required by a deliverable/criterion, mark that item as `blocked`
   - If present, extract relevant status fields

## 4. Aggregate Per-Workflow-Type Status
1. For each workflow type (frontend, backend, governance, data, research):
   - Filter deliverables where `workflow_type` matches
   - Filter success_criteria where `workflow_type` matches
   - Compute type status:
     ```
     green:  all deliverables complete AND all criteria pass AND no blockers
     yellow: any deliverable in_progress AND no critical blockers
     red:    any deliverable blocked OR any criterion fail
     n/a:    workflow_weight = 0% for this type
     ```
2. Emit per-type status with counts:
   - `deliverables_total`
   - `deliverables_complete`
   - `deliverables_blocked`
   - `criteria_total`
   - `criteria_pass`
   - `criteria_fail`

## 5. Aggregate Overall Phase Status
1. Compute overall status:
   ```
   not_started:  all deliverables not_started
   in_progress:  any deliverable in_progress AND no critical blockers
   blocked:      any success_criterion fail OR any deliverable blocked
   complete:     all deliverables complete AND all success_criteria pass
   ```
2. Compute overall color:
   ```
   green:  overall_status = complete
   yellow: overall_status = in_progress
   red:    overall_status = blocked OR not_started (with past target date)
   ```

## 6. Validate Realm-Specific Criteria
1. If `realm_specific_criteria` section exists in phase brief:
   - For each criterion, check if validator exists
   - If validator is a script path, run it and capture exit code
   - If validator is "manual", mark status as `manual_check`
   - If validator is `$skill-name`, note that skill must be called separately
2. Emit realm criteria status with counts:
   - `realm_criteria_total`
   - `realm_criteria_pass`
   - `realm_criteria_fail`
   - `realm_criteria_manual_check`

## 7. Output Contract
1. Write `docs/context/workflow_status_latest.json`:
   ```json
   {
     "schema_version": "1.0.0",
     "generated_at_utc": "<timestamp>",
     "phase_id": "<phase_id>",
     "phase_name": "<phase_name>",
     "overall_status": "not_started | in_progress | blocked | complete",
     "overall_color": "green | yellow | red",
     "workflow_weight": {
       "frontend": 0,
       "backend": 20,
       "governance": 70,
       "data": 10,
       "research": 0
     },
     "workflow_status": {
       "frontend": {
         "status": "n/a | green | yellow | red",
         "deliverables_total": 0,
         "deliverables_complete": 0,
         "deliverables_blocked": 0,
         "criteria_total": 0,
         "criteria_pass": 0,
         "criteria_fail": 0
       },
       "backend": { ... },
       "governance": { ... },
       "data": { ... },
       "research": { ... }
     },
     "realm_criteria": {
       "total": 0,
       "pass": 0,
       "fail": 0,
       "manual_check": 0
     },
     "blocking_issues": [
       {"type": "deliverable", "id": "...", "name": "...", "reason": "..."},
       {"type": "criterion", "id": "...", "name": "...", "reason": "..."}
     ],
     "truth_layers": {
       "static_truth": ["top_level_PM.md", "decision log.md", "phase brief"],
       "live_truth": ["current_context.md"],
       "bridge_truth": ["bridge_contract_current.md"],
       "evidence_truth": ["done_checklist_current.md", "multi_stream_contract_current.md", "post_phase_alignment_current.md"],
       "planner_truth": ["planner_packet_current.md", "impact_packet_current.md"],
       "observability": ["observability_pack_current.md"]
     },
     "missing_artifacts": [
       {"artifact": "impact_packet_current.md", "reason": "mature repo but impact packet missing"},
       {"artifact": "observability_pack_current.md", "reason": "5+ phases completed but observability pack missing"}
     ],
     "repo_shape": {
       "stream_model": "single-stream | multi-stream",
       "maturity": "early | mature",
       "active_streams": ["Backend", "Frontend/UI", "Data", "Docs/Ops"],
       "deferred_streams": []
     },
     "kernel_activation": {
       "bridge_contract": "active",
       "done_checklist": "active",
       "planner_packet": "active",
       "impact_packet": "active | not_needed",
       "multi_stream_contract": "active | not_needed",
       "post_phase_alignment": "active | not_needed",
       "observability_pack": "active | not_needed",
       "artifact_pruning_rules": "active | not_needed"
     }
   }
   ```
2. Emit terminal output:
   - Phase summary (id, name, overall status, overall color)
   - Per-type status table (workflow_type, status, deliverables, criteria)
   - Blocking issues (if any)
   - Truth layers (which exist, which are missing)
   - Repo shape (stream model, maturity, active/deferred streams)
   - Kernel activation (which capabilities are active, which are not needed)
   - Next action
       "data": { ... },
       "research": { ... }
     },
     "realm_criteria": {
       "realm": "finance",
       "criteria_total": 3,
       "criteria_pass": 2,
       "criteria_fail": 0,
       "criteria_manual_check": 1,
       "details": [
         {
           "id": "FIN-01",
           "name": "PIT Discipline",
           "status": "pass",
           "validator": "scripts/validate_pit_discipline.py",
           "evidence": "..."
         }
       ]
     },
     "blocking_issues": [
       {
         "type": "deliverable | criterion",
         "id": "C1",
         "name": "Phase 24B Operational Close",
         "reason": "PM signoff pending"
       }
     ],
     "next_action": "<one-line next step>"
   }
   ```
2. Emit machine-check line:
   - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
3. Validate with:
   - `python .codex/skills/_shared/scripts/validate_workflow_status.py --status-json docs/context/workflow_status_latest.json --phase-brief <phase_brief_path> --project-init <project_init_path>`
4. Emit `WorkflowStatusValidation: PASS/BLOCK`.

## 8. Loop-Close Criteria
1. `PASS` only when:
   - Phase brief loaded successfully
   - Project init loaded successfully
   - All required artifacts found
   - Workflow weight sums to 100%
   - All deliverables have valid workflow_type
   - All success_criteria have valid workflow_type
   - Validation script returns exit code 0
2. `BLOCK` when:
   - Missing phase brief or project init
   - Workflow weight != 100%
   - Invalid workflow_type values
   - Validation script fails
   - Missing required closure packet fields
