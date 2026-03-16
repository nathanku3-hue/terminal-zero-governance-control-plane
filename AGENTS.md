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
- `docs/context/` - Authoritative `_latest` artifacts (atomic writes required)
- `.codex/skills/` - Canonical skill definitions (source of truth)
- `skills/` - Project deliverables (not canonical)
- `tests/` - Test suites
- `data/`, `strategies/`, `views/` - Legacy quant-era (read-only unless brief authorizes)

→ [Full directory structure with ownership rules](docs/directory_structure.md)

## 3. Workflow Wiring (Core Navigation)

### Session Lifecycle
```
Fresh Worker Start
    ↓
Read AGENTS.md (this file)
    ↓
Load .codex/skills/README.md (skill registry)
    ↓
User invokes /new or "start session"
    ↓
$project-guider activated
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
