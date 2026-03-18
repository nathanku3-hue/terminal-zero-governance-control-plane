---
name: project-guider
description: Orchestrate session flow, hierarchy confirmation, confidence gating, and routing to the correct skill. Use at project start or when coordinating multi-step work across skills.
---

# Project Guider Skill

Coordinate session bootstrap, hierarchy confirmation, confidence-based routing, and downstream skill invocation.

## 0. Session Start
1. When the user requests `/new`, "start session", or "what's next":
   - Read `AGENTS.md` (navigation hub) to understand system wiring
   - Load `.codex/skills/README.md` (skill registry)
   - **Check kernel activation** (Section 0.1)
   - Call `$context-bootstrap` to load exec_memory_packet_latest.json
   - Load `docs/context/project_init_latest.md` (L1 hot memory)
   - **Load planner entry surfaces** (Section 0.2)
   - Call `$workflow-status` to get current phase snapshot
2. If `project_init_latest.md` is missing:
   - Trigger project init interrogation (Section 1)
   - Do not proceed until project init is complete
3. Emit combined session summary:
   - Project identity (name, realm, workflow profile)
   - Current phase (id, name, status)
   - Workflow status (per-type + overall)
   - Blocking issues (if any)
   - Next action

### 0.1 Kernel Activation Check (Mandatory)
1. Read `E:\code\SOP\KERNEL_ACTIVATION_MATRIX.md` at session start.
2. Determine repo shape:
   - Single-stream or multi-stream?
   - Early (< 5 scope boundaries) or mature (>= 5)?
3. Check which capabilities are activated for this repo:
   - Bridge contract: always active
   - Done checklist: always active
   - Planner packet: always active
   - Impact packet: active if mature
   - Multi-stream contract: active if multi-stream
   - Post-phase alignment: active if multi-stream
   - Observability pack: active if mature
   - Artifact pruning rules: active if > 20 untracked governance files
4. Emit `KernelActivation: <list of active capabilities>`.
5. If a capability is missing but should be active per activation trigger, emit `MissingArtifact: <capability>` and request creation before proceeding.

### 0.2 Planner Entry Surfaces (Mandatory)
1. Load planner entry surfaces in this order:
   - `docs/context/planner_packet_current.md` (compact entry point)
   - `docs/context/impact_packet_current.md` (if active)
   - `docs/context/bridge_contract_current.md` (PM/planner bridge)
   - `docs/context/done_checklist_current.md` (acceptance criteria)
2. Only escalate to wider reads (phase briefs, decision log, full repo) if one of these conditions applies:
   - Impact surface is unclear from planner packet + impact packet
   - Interface ownership is unclear from owned files list
   - Evidence conflicts between bridge truth and decision tail
   - Bottleneck cannot be named from current context
3. If escalation is needed, emit `EscalationTrigger: <condition>` and load the required wider surface.

**Deep Dive References**:
- System wiring and integration: `docs/workflow_wiring_detailed.md`
- Operating principles: `docs/operating_principles.md`
- Definition of done: `docs/definition_of_done.md`
- Tech stack constraints: `docs/tech_stack.md`
- Directory structure: `docs/directory_structure.md`
- Kernel activation matrix: `E:\code\SOP\KERNEL_ACTIVATION_MATRIX.md`
- Multi-stream execution checklist: `E:\code\SOP\SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`

## 1. Project Init Hierarchy Confirmation (Hard Stop)
1. Call `$hierarchy-init` at project start or when a new domain appears.
2. Do not proceed to execution or routing until hierarchy confirmation is approved.
3. Emit the hierarchy audit stamp in all outputs for this session.

## 2. Task Intake and Confidence
1. Restate the task in one line and identify the domain.
2. Self-report `Confidence: <0-100>`.
3. Call `$confidence-gate` with:
   - confidence score
   - task description
   - current domain
4. Capture the route decision (`PROCEED`, `ESCALATE`, or `MANUAL_CHECK`).

## 2.5. Workflow Status Check
1. Call `$workflow-status` to get current phase status snapshot.
2. Check `overall_color` from workflow status:
   - If `red` (blocked):
     - Emit `StatusAlert: BLOCKED`
     - List blocking issues from workflow_status_latest.json
     - Ask user: "Resolve blockers first, or proceed anyway?"
     - If user says "proceed anyway", log override in decision log and continue
     - If user says "resolve first", stop and emit next action to resolve blockers
   - If `yellow` (in_progress):
     - Emit `StatusAlert: IN_PROGRESS`
     - List any pending items (deliverables in_progress, criteria pending)
     - Continue to routing
   - If `green` (healthy):
     - Emit `StatusAlert: HEALTHY`
     - Continue to routing
3. Include workflow status snapshot in output (for L1 hot memory context).

## 3. Routing Rules
1. If `PROCEED`, route by task type:
   - Code implementation or multi-file changes: `$se-executor`
   - Architecture or boundary decisions: `$architect-review`
   - Evidence-backed research needs: `$research-analysis`
   - Post-work review and reconciliation: `$saw`
2. If `ESCALATE`, call `$role-injection` then invoke `$expert-researcher`.
3. If `MANUAL_CHECK`, stop and request PM/CEO or human review before proceeding.
4. If the expert response returns `Confidence < 80`, treat as `MANUAL_CHECK`.

## 4. Output Contract
1. Include:
   - `Domain`
   - `Task Summary`
   - `Confidence`
   - `RoutingDecision`
   - `RouteTo`
   - `RoleStamp` (when available)
   - `NextAction`
2. Emit one machine-check line:
   - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
3. Validate with:
   - `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
4. Emit `ClosureValidation: PASS/BLOCK`.
