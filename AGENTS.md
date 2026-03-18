# AGENTS.md

> SYSTEM CONTEXT: You are a contributor to Terminal Zero (T0), a script-driven AI engineering governance control plane.
> ROOT PATH: `E:\Code\SOP\quant_current_scope`

## 0. Navigation Hub

**Fresh Worker Start**: Read this file first, then load `.codex/skills/README.md` (skill registry).

**Path Resolution Rule**: All paths in AGENTS.md and skill files are **repo-root relative** (root = `E:\Code\SOP\quant_current_scope`). Validator scripts must be executed with repo root as the working directory.

**Deep Dives Available**:
- [Tech Stack & Constraints](docs/tech_stack.md) - Runtime requirements, forbidden patterns, dependency management
- [Directory Structure](docs/directory_structure.md) - Purpose and ownership of each directory
- [Operating Principles](docs/operating_principles.md) - 8 core commandments with detailed rationale
- [Definition of Done](docs/definition_of_done.md) - Completion checklist and risk-tier requirements
- [Workflow Wiring](docs/workflow_wiring_detailed.md) - Deep-dive system integration reference

## 1. Quick Start

**Tech Stack**: Python 3.12+, script-first orchestration, JSON/Markdown contracts. Forbidden: SQLite, Flask, Django, ORMs without approval. → [Full details](docs/tech_stack.md)

**Primary Entrypoints**:
- `scripts/startup_codex_helper.py` - Initialize a round
- `scripts/run_loop_cycle.py` - Execute worker/auditor/CEO loop
- `scripts/supervise_loop.py` - Monitor loop health
- `scripts/print_takeover_entrypoint.py` - Print takeover guidance

**Testing**: `pytest` for all tests. Record fresh count + date + interpreter in evidence.

## 2. Directory Map

- `scripts/` - Control plane orchestration only
- `docs/context/` - Authoritative `_latest` artifacts for this repo (atomic writes required); current truth surfaces are only read here when this repo is the active working repo (see Section 2.1)
- `.codex/skills/` - Canonical skill definitions (source of truth)
- `skills/` - Project deliverables (not canonical)
- `tests/` - Test suites
- `data/`, `strategies/`, `views/` - Legacy quant-era (read-only unless brief authorizes)

→ [Full directory structure with ownership rules](docs/directory_structure.md)

### 2.1 Current Truth Surfaces (Mandatory Reading)

Before starting work, resolve the loop entry model against the target working repo for this round. In `quant_current_scope`, do not assume these files exist locally under `docs/context/`; they are current truth surfaces only when `KERNEL_ACTIVATION_MATRIX.md` says the capability is active and the artifact exists in the repo you are operating.

**Root SOP governance:**
- `E:\code\SOP\KERNEL_ACTIVATION_MATRIX.md` — when each kernel capability becomes mandatory
- `E:\code\SOP\SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md` — 11-section checklist for multi-stream execution readiness
- `E:\code\SOP\ENDGAME.md` — target state for SOP governance control plane

**Current truth surfaces (target working repo, when active and instantiated):**
- `planner_packet_current.md` — compact fresh-context packet for planner (current context, active brief, bridge truth, decision tail, blocked next step, active bottleneck)
- `impact_packet_current.md` — impact view (changed files, owned files, touched interfaces, failing checks)
- `bridge_contract_current.md` — translates recent execution truth into PM/planner next-step language (SYSTEM_DELTA, PM_DELTA, OPEN_DECISION, RECOMMENDED_NEXT_STEP, DO_NOT_REDECIDE)
- `done_checklist_current.md` — machine-checkable done criteria for current phase
- `multi_stream_contract_current.md` — cross-stream coordination map (Backend, Frontend/UI, Data, Docs/Ops)
- `post_phase_alignment_current.md` — post-phase stream status update and bottleneck analysis
- `observability_pack_current.md` — drift detection markers (high-risk attempts, stuck sessions, skill under-triggering, budget pressure, compaction/hallucination pressure)

**Entry order:**
1. Check `E:\code\SOP\KERNEL_ACTIVATION_MATRIX.md`.
2. Check `E:\code\SOP\SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`.
3. Read `planner_packet_current.md` if it is active and instantiated in the target working repo.
4. Read `impact_packet_current.md` if it is active and instantiated.
5. Read `bridge_contract_current.md` if it is active and instantiated.
6. Read `done_checklist_current.md` if it is active and instantiated.
7. Read `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and `observability_pack_current.md` only when they are active and instantiated.

**When to escalate:**
- Widen reads to phase briefs, decision logs, or the full repo only if an active required surface is missing, impact is still unclear after planner + impact, interface ownership is unclear, bridge truth conflicts with the decision tail, or the active bottleneck still cannot be named.

**What changes after execution:**
- Refresh the active instantiated surfaces you consumed or changed in the target working repo: `planner_packet_current.md`, `impact_packet_current.md`, `bridge_contract_current.md`, `done_checklist_current.md`, `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and `observability_pack_current.md`.

## 3. Workflow Wiring (Core Navigation)

### Session Lifecycle
```
Fresh Worker Start
    ↓
Read AGENTS.md (this file)
    ↓
Load .codex/skills/README.md (skill registry)
    ↓
Check KERNEL_ACTIVATION_MATRIX.md (which capabilities are active)
    ↓
Check SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md (which multi-stream surfaces are expected)
    ↓
User invokes /new or "start session"
    ↓
$project-guider activated
    ↓
Resolve current truth surfaces in target working repo:
  - planner_packet_current.md (when active and instantiated)
  - impact_packet_current.md (when active and instantiated)
  - bridge_contract_current.md (when active and instantiated)
  - done_checklist_current.md (when active and instantiated)
  - multi_stream_contract_current.md (when active and instantiated)
  - post_phase_alignment_current.md (when active and instantiated)
  - observability_pack_current.md (when active and instantiated)
    ↓
Escalate to wider reads only if required active surfaces are missing or the entry surfaces are insufficient
    ↓
Load context: project_init_latest.md + exec_memory_packet_latest.json
    ↓
$workflow-status invoked
    ↓
Check overall_color: green/yellow/red
    ↓
If red → StatusAlert: BLOCKED (ask user to resolve or proceed)
    ↓
Route to appropriate skill based on task type
    ↓
Execute skill workflow
    ↓
Refresh current truth surfaces:
  - planner_packet_current.md (when active)
  - impact_packet_current.md (when active)
  - bridge_contract_current.md (when active)
  - done_checklist_current.md (when active)
  - multi_stream_contract_current.md (when active)
  - post_phase_alignment_current.md (when active)
  - observability_pack_current.md (when active)
    ↓
Emit validation tokens (PASS/BLOCK/DRIFT/INSUFFICIENT)
    ↓
Generate worker_reply_packet.json
    ↓
Run auditor review (shadow/enforce mode)
    ↓
SAW protocol (if applicable)
    ↓
Phase closure
```

### Skill Activation Matrix

| Skill | Trigger | Model | Validator | Output |
|-------|---------|-------|-----------|--------|
| saw | Workflow invoked | codex-5.4 | validate_saw_report_blocks.py | SAWBlockValidation: PASS/BLOCK |
| research-analysis | Workflow invoked | claude | validate_research_claims.py | ClaimValidation: PASS/BLOCK |
| se-executor | Trigger-based | codex-5.2 | validate_se_evidence.py | EvidenceValidation: PASS/BLOCK |
| architect-review | Trigger-based | claude | validate_architect_calibration.py | CalibrationValidation: PASS/DRIFT/INSUFFICIENT |
| project-guider | Session start | claude | N/A | Session routing |
| workflow-status | Via project-guider | claude | N/A | workflow_status_latest.json |
| quick-gate | Pre-commit | codex-5.2 | Multiple validators | QuickGate: PASS/BLOCK |

### Validation Chain

**Pre-Commit** ($quick-gate): Schema version, test suite, file existence, workflow weights, git status
**Post-Work** (Skill validators): Skill-specific validation with PASS/BLOCK/DRIFT/INSUFFICIENT tokens
**Phase-End** (Auditor): worker_reply_packet.json validation, shadow/enforce mode

### Artifact Flow

**Input**: `project_init_latest.md`, `exec_memory_packet_latest.json`, `phase<N>-brief.md`, `workflow_status_latest.json`
**Working**: `docs/evidence/<phase>/*.json`, `hierarchy_confirmation_latest.md`, `confidence_gate_latest.json`
**Output**: `worker_reply_packet.json`, `closure_packet_latest.json`, `auditor_findings_latest.json`, `saw_report_latest.md`

→ [Full workflow wiring with confidence routing, model strategy, error handling](docs/workflow_wiring_detailed.md)

## 4. Operating Principles

1. **Docs-as-Code**: Behavior changes require doc updates in same milestone
2. **Atomic Safety**: Critical writes use temp → replace pattern
3. **Top-Down Delivery**: Spec → Interface → Implementation → Test
4. **Defense in Depth**: Assume API failures, handle NaN data gracefully
5. **Subagent-First**: Use subagents for multi-file changes, ETL, strategy logic
6. **Guardrailed Delegation**: Bounded scope, acceptance checks, no destructive ops without confirmation
7. **Review Gated**: Milestone review mandatory before closure
8. **Self-Learning**: Record mistakes in `docs/lessonss.md`

→ [Full principles with rationale, implementation, examples](docs/operating_principles.md)

## 5. Definition of Done

A task is NOT done until:
- Code implemented with acceptance criteria met
- Tests pass (record pytest count + date + interpreter)
- Docs updated (phase brief, decision log, code comments)
- Milestone review gate passes (risk-tier checks)
- Evidence footer included (observability rating, validation results)
- Validation tokens emitted (PASS/BLOCK/DRIFT/INSUFFICIENT)

**Risk Tiers**: Low (unit tests + static checks), Medium (+ integration/smoke), High (+ data integrity + rollback), Critical (+ dry-run + user sign-off)

→ [Full DoD checklist with risk-tier requirements, common failures](docs/definition_of_done.md)

## 6. Milestone Review Gate

Before closing a milestone, spawn reviewer subagents:
- Architecture review
- Code quality review
- Test coverage review
- Performance review

Address CRITICAL/HIGH findings. Document MEDIUM/LOW for future work.

## 7. SAW Protocol (Subagents-After-Work)

Independent review after implementation complete. Emit `SAWBlockValidation: PASS/BLOCK` from `validate_saw_report_blocks.py`.

## 8. Auditor Protocol

Independent automated review of `worker_reply_packet.json` via `scripts/run_auditor_review.py`.
- **Shadow mode** (default): Findings logged, non-blocking
- **Enforce mode**: CRITICAL/HIGH block handover

Auditor is orthogonal to SAW: SAW reviews process, auditor reviews final output packet.

## 9. Change Discipline

- No destructive operations without explicit user confirmation
- Never revert unrelated local changes
- Read files before overwriting
- Keep dependencies minimal and justified

## 10. Evidence Footer (Mandatory)

```markdown
## Evidence Footer
**Observability**: 4/5
**Evidence Paths**: docs/evidence/phase24c/saw_report_001.json
**Validation Results**: SAWBlockValidation: PASS, QuickGate: PASS (51/51)
**Run Metadata**: Date: 2026-03-16, Python: 3.12.1 (.venv/bin/python), Tests: 308 passed
```
