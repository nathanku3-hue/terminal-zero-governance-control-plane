# Phase 1 — Structural Plan

> **Status**: Draft — ready for review
> **Effort estimate**: 9–14 days total
> **Repo**: `E:\Code\SOP\quant_current_scope`
> **Prerequisite**: Phase 0 gate fully checked
> **Gate**: All three items complete before Phase 2 begins

---

## Context: What Phase 0 established

- JSON Schema enforcement on emit for `loop_cycle_summary`, `exec_memory_packet`, `worker_reply_packet`
- Linting clean, coverage baseline, CI lint gates across all three workflow files
- Integration tests for multi-role artifact isolation and schema validity post-cycle
- Byte-identical sync between `src/sop/scripts/` and `scripts/` enforced by `test_script_surface_sync.py`

Phase 1 builds on these. Phase 0 schemas define the data contracts Worker classes must emit.

---

## Current State (as-inspected)

| Area | What exists | What is missing |
|---|---|---|
| Role model | `worker`/`auditor` references at `run_loop_cycle.py:671-672,1512-1513`; lessons stubs per role | No `Worker` base class; role behavior embedded procedurally |
| Runtime state | `LoopCycleRuntime` dataclass (`loop_cycle_runtime.py:88`) — mutable, holds steps and advisory artifacts | No per-role skill injection; skills resolved globally |
| Skill mapping | `extension_allowlist.yaml` — skill registry with `skill_name`, `risk_level`, `status` | Skill-to-role assignments hardcoded; no per-Worker injection |
| State persistence | Artifacts written atomically to `docs/context/` | No checkpoint; interrupted loop leaves partial artifacts with no recovery path |

---

## Item 1.1 — Worker / Role Abstraction

### What to build

`src/sop/scripts/worker_base.py` — three classes:

```python
@dataclass
class WorkerSkill:
    name: str
    version: str
    risk_level: str
    approval_decision_id: str
    applicable_projects: list[str]

@dataclass
class WorkerResult:
    role: str
    status: str          # PASS / HOLD / FAIL / ERROR
    exit_code: int
    steps: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

class Worker(ABC):
    def __init__(self, repo_root: Path, skills: list[WorkerSkill]) -> None: ...
    @property
    @abstractmethod
    def role(self) -> str: ...
    @abstractmethod
    def run(self, context: Any) -> WorkerResult: ...
    def skill_names(self) -> list[str]: ...
```

Three concrete subclasses:
- `worker_role.py` — `WorkerRole(Worker)`: `role="worker"`, wraps existing worker-phase logic
- `auditor_role.py` — `AuditorRole(Worker)`: `role="auditor"`, wraps auditor invocation at lines 1066/1084
- `planner_role.py` — `PlannerRole(Worker)`: `role="planner"`, stub returns `WorkerResult(status="PASS", exit_code=0)`

Integrate into `run_loop_cycle.py` — but first map the real orchestration seams:

**AuditorRole owns** the two `run_python_step` calls at `run_loop_cycle.py:1064-1100` that
invoke `ctx.auditor_script` (assigned to `auditor_calibration_report.py` in
`loop_cycle_context.py:344`): steps `refresh_weekly_calibration` and `refresh_dossier`.
These become `AuditorRole.run()` in Phase 1.

**WorkerRole owns** all other steps: exec memory build/promotion, advisory artifact generation,
and loop summary write.

| Step | Location | Owner |
|---|---|---|
| Exec memory build + promotion | `run_loop_cycle.py` | `WorkerRole` |
| Advisory artifact generation | `run_loop_cycle.py` | `WorkerRole` |
| `refresh_weekly_calibration` | `run_loop_cycle.py:1064` | `AuditorRole` |
| `refresh_dossier` | `run_loop_cycle.py:1084` | `AuditorRole` |
| Loop summary write | `run_loop_cycle.py:~1631` | `WorkerRole` |

Instantiate `WorkerRole` and `AuditorRole` at the start of `run_cycle()` and thread through
existing step sequence without restructuring it. All existing tests must pass unchanged.

### Files to create
```
src/sop/scripts/worker_base.py
src/sop/scripts/worker_role.py
src/sop/scripts/auditor_role.py
src/sop/scripts/planner_role.py
scripts/worker_base.py              # D-183 compatibility copy
scripts/worker_role.py              # D-183 compatibility copy
scripts/auditor_role.py             # D-183 compatibility copy
scripts/planner_role.py             # D-183 compatibility copy
tests/test_worker_base.py
```

### Files to modify
```
src/sop/scripts/run_loop_cycle.py
scripts/run_loop_cycle.py           # backport (D-183)
tests/test_script_surface_sync.py   # add worker_base.py, worker_role.py, auditor_role.py, planner_role.py to PHASE_0_SCRIPTS or a new PHASE_1_SCRIPTS list
```

**D-183 dual-surface rule for Worker modules**: Current scripts use try/except fallback imports
(pattern at `loop_cycle_runtime.py:10`). Worker modules will be imported the same way:
```python
try:
    from sop.scripts.worker_base import Worker, WorkerSkill, WorkerResult
except ModuleNotFoundError:
    from scripts.worker_base import Worker, WorkerSkill, WorkerResult
```
Therefore `scripts/worker_base.py`, `scripts/worker_role.py`, `scripts/auditor_role.py`, and
`scripts/planner_role.py` must be byte-identical copies of their `src/sop/scripts/` originals,
and must be added to the sync-gate list in `tests/test_script_surface_sync.py:31`.

### Done criteria
- [ ] `Worker`, `WorkerRole`, `AuditorRole`, `PlannerRole` classes exist
- [ ] `WorkerResult` has `role`, `status`, `exit_code`, `steps`, `artifacts`, `errors`
- [ ] Step ownership mapped: WorkerRole owns exec-memory+advisory+summary; AuditorRole owns refresh_weekly_calibration+refresh_dossier
- [ ] Workers instantiated in `run_cycle()` without changing loop behavior
- [ ] All existing tests still pass
- [ ] `tests/test_worker_base.py` passes (5 tests: instantiation, result schema, skill injection, ABC enforcement)
- [ ] `pytest tests/test_script_surface_sync.py` passes

---

## Item 1.2 — Configurable Skill Mapping

### What to build

Depends on 1.1 (`WorkerSkill` imported from `worker_base`).

**Extend `extension_allowlist.yaml`** — add optional `assigned_roles`:
```yaml
  - skill_name: repo-map
    version: 1.0.0
    status: active
    risk_level: LOW
    approval_decision_id: D-176
    assigned_roles: [worker, auditor]   # optional; defaults to [worker] if absent
    applicable_projects: [all]
```

Update `skills/schemas/allowlist_schema.yaml` to include `assigned_roles` as optional.

**Extend `src/sop/scripts/utils/skill_resolver.py`** — add:
```python
def resolve_skills_for_role(repo_root: Path, project: str, role: str) -> list[WorkerSkill]:
    """Return WorkerSkill list for role. Skill without assigned_roles defaults to worker."""
```
`resolve_active_skills()` signature unchanged (backward-compatible).

**Wire in `run_loop_cycle.py`**:

`LoopCycleContext` carries `repo_id` (not `project_name`) at `loop_cycle_context.py:36`.
Derive `project_name` from `.sop_config.yaml` the same way `build_exec_memory_packet.py:1877` does:

```python
# Derive project_name from .sop_config.yaml (same pattern as build_exec_memory_packet.py:1877)
_project_name = "quant_current_scope"  # default
try:
    _sop_config_path = ctx.repo_root / ".sop_config.yaml"
    if _sop_config_path.exists():
        import yaml
        with _sop_config_path.open("r", encoding="utf-8") as _f:
            _sop_cfg = yaml.safe_load(_f)
            if isinstance(_sop_cfg, dict):
                _project_name = _sop_cfg.get("project_name", _project_name)
except Exception:
    pass

worker_skills = resolve_skills_for_role(ctx.repo_root, _project_name, "worker")
auditor_skills = resolve_skills_for_role(ctx.repo_root, _project_name, "auditor")
worker = WorkerRole(repo_root=ctx.repo_root, skills=worker_skills)
auditor = AuditorRole(repo_root=ctx.repo_root, skills=auditor_skills)
```

No skill names hardcoded in loop logic after this change.

**Note**: Do NOT add `project_name` to `LoopCycleContext` in Phase 1. It is a runtime-derived
value, not a CLI arg. If a future phase needs it as a stable context field, that is a separate
decision to record in `docs/decision log.md`.

### Files to create
```
tests/test_skill_mapping.py
```

### Step 5b: Update skill governance validators for assigned_roles

`assigned_roles` touches four existing contract surfaces — all must be updated together:

1. **`validate_extension_allowlist.py:41`** — `required_fields` currently lists 8 required fields.
   `assigned_roles` is optional — do NOT add to required_fields. Add optional validation:
   if present, must be a non-empty list; each entry in `["worker", "auditor", "planner"]`.

2. **`validate_skill_activation.py:117`** — validates `active_skills` from `.sop_config.yaml`
   against the emitted artifact using project-global lookup. This logic must remain unchanged.
   `assigned_roles` is an allowlist-internal field; per-role filtering is in `resolve_skills_for_role()`,
   not in the activation validator. Add a comment noting this separation.

3. **`build_exec_memory_packet.py:1891`** — calls `resolve_active_skills(repo_root, project_name)`.
   This call must remain unchanged. The exec memory packet emits the project-global skill list,
   not a role-filtered list. Per-role injection is a Worker instantiation concern only.

4. **`tests/test_skill_activation.py:194`** — asserts skill artifact shape: `name, version, status,
   manifest_path, category, description, approval_decision_id, risk_level`.
   `assigned_roles` must NOT appear in the emitted `skill_activation` artifact.
   Existing test assertions must pass without modification.

### Files to modify
```
extension_allowlist.yaml
skills/schemas/allowlist_schema.yaml
src/sop/scripts/utils/skill_resolver.py
src/sop/scripts/validate_extension_allowlist.py    # optional assigned_roles validation
src/sop/scripts/run_loop_cycle.py
scripts/utils/skill_resolver.py                    # backport
scripts/run_loop_cycle.py                          # backport
scripts/validate_extension_allowlist.py            # backport
```

### Done criteria
- [ ] `assigned_roles` in `extension_allowlist.yaml` for all current skills
- [ ] `validate_extension_allowlist.py` accepts optional `assigned_roles`; validates list of valid role strings
- [ ] `resolve_skills_for_role(repo_root, project, role)` exists; returns `list[WorkerSkill]`
- [ ] No skill names hardcoded in `run_loop_cycle.py`
- [ ] `resolve_active_skills()` signature unchanged; `build_exec_memory_packet.py:1891` call unchanged
- [ ] `validate_skill_activation.py:117` logic unchanged; `test_skill_activation.py:194` assertions pass
- [ ] `assigned_roles` does NOT appear in emitted `skill_activation` artifact
- [ ] `validate_extension_allowlist.py` updated for optional `assigned_roles`
- [ ] `tests/test_skill_mapping.py` passes (5 tests)
- [ ] All parity and integration tests still pass
- [ ] `pytest tests/test_script_surface_sync.py` passes

---

## Item 1.3 — State Persistence (Single-Loop)

### What to build

**Checkpoint contract** — `docs/context/loop_cycle_checkpoint_latest.json`:
```json
{
  "schema_version": "1.0",
  "generated_at_utc": "2026-03-27T12:00:00Z",
  "cycle_id": "2026-03-27T12:00:00Z",
  "completed_steps": ["exec_memory", "advisory"],
  "last_completed_step": "advisory",
  "exec_memory_cycle_ready": true,
  "partial": true
}
```

Add `loop_cycle_checkpoint.schema.json` to `docs/context/schemas/` and `src/sop/schemas/`.

**Checkpoint write points in `run_loop_cycle.py`**:
1. After exec memory promotion succeeds — `completed_steps: ["exec_memory"]`, `partial: true`
2. After advisory artifacts written — `completed_steps: ["exec_memory", "advisory"]`, `partial: true`
3. After loop summary written — `partial: false` (terminal)

Use `atomic_write_json` from `scripts/utils/atomic_io.py`.

**Checkpoint load order — must happen BEFORE runtime construction.**

`build_loop_cycle_runtime()` writes lesson stubs immediately on construction
(`loop_cycle_runtime.py:40`, asserted by `test_loop_cycle_runtime.py:122`).
Checkpoint load must happen *before* `build_loop_cycle_runtime()` is called —
between lines 602 and 608 of `run_loop_cycle.py`:

```python
ctx = build_loop_cycle_context(args)
# 1. Load checkpoint BEFORE runtime (before any side effects)
checkpoint = _load_checkpoint(ctx)
resume_steps = _resolve_resume_steps(checkpoint)  # set[str] of steps to skip
# 2. Build runtime (writes lesson stubs — side effects begin here)
runtime = build_loop_cycle_runtime(ctx)
# 3. Use resume_steps to skip already-completed steps
```

Lesson stubs are always written (not skipped on resume). This preserves
the `test_loop_cycle_runtime.py:122` assertion.

**Stale checkpoint invalidation rules** — treat checkpoint as stale (return None) if:
1. `partial: false` — previous run completed cleanly; always start fresh
2. `generated_at_utc` older than `--max-checkpoint-age-hours` (default: 24h)
3. `cycle_id` present and does not match current invocation `--cycle-id` arg
4. Checkpoint fails schema validation against `loop_cycle_checkpoint.schema.json`

`_load_checkpoint()` returns `None` on any stale condition.
`_resolve_resume_steps(None)` returns empty set (full run).

**Resume skip logic**:
```python
if "exec_memory" in resume_steps:
    runtime.exec_memory_cycle_ready = True  # skip exec memory build; load existing artifact
if "advisory" in resume_steps:
    pass  # skip advisory artifact generation
```

**Register checkpoint as a live artifact** (three surfaces to update):

1. `src/sop/schemas/` — place `loop_cycle_checkpoint.schema.json` there. `sop init` copies
   it automatically via the `*.json` glob in `init_cmd.py:116` (`_copy_schemas()` globs
   every `*.json` in `src/sop/schemas/`). No `SCHEMAS` list exists in `init_cmd.py`;
   no code change to `init_cmd.py` is required.
2. `docs/context/schemas/` — place a copy there as well (follows Phase 0 pattern;
   `schemas/**` in pyproject.toml already covers it).
3. `tests/test_cli_script_parity.py` — add `"docs/context/loop_cycle_checkpoint_latest.json"`
   to `LOOP_ARTIFACTS` so parity suite covers the new live artifact.

### Files to create
```
docs/context/schemas/loop_cycle_checkpoint.schema.json
src/sop/schemas/loop_cycle_checkpoint.schema.json
tests/test_state_persistence.py
```

### Files to modify
```
src/sop/scripts/run_loop_cycle.py
scripts/run_loop_cycle.py           # backport
pyproject.toml                      # add state_persistence pytest marker
```

### Done criteria
- [ ] Checkpoint load happens before `build_loop_cycle_runtime()` at `run_loop_cycle.py:602`
- [ ] Stale invalidation: `partial: false`, age>24h, `cycle_id` mismatch, schema-invalid all return None
- [ ] `loop_cycle_checkpoint_latest.json` written after each major step
- [ ] Checkpoint validates against `loop_cycle_checkpoint.schema.json`
- [ ] Interrupted loop skips already-completed steps on re-run
- [ ] Lesson stubs always written on resume (`test_loop_cycle_runtime.py:122` still passes)
- [ ] Completed loop writes `partial: false`
- [ ] `loop_cycle_checkpoint.schema.json` placed in `src/sop/schemas/` (auto-copied by `init_cmd.py:116` glob)
- [ ] `loop_cycle_checkpoint_latest.json` in `LOOP_ARTIFACTS` in `tests/test_cli_script_parity.py`
- [ ] `tests/test_state_persistence.py` passes (5 tests)
- [ ] All existing tests still pass
- [ ] `pytest tests/test_script_surface_sync.py` passes

---

## Execution Order

```
Parallel start:
  Workstream A: 1.1 Worker/Role Abstraction
  Workstream C: 1.3 State Persistence (independent)

After 1.1 complete:
  Workstream B: 1.2 Configurable Skill Mapping (needs WorkerSkill from 1.1)

For every file change:
  1. Edit src/sop/scripts/ first (canonical per D-183)
  2. Copy to scripts/ (compatibility)
  3. Run pytest tests/test_script_surface_sync.py
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Worker class layer changes loop behavior | Medium | High | Only introduce class layer; do not restructure run_cycle(); all existing tests must pass |
| Skill resolver role-filter breaks allowlist parsing | Low | Medium | resolve_active_skills() unchanged; new function is additive only |
| Checkpoint resume skips steps that need re-execution | Medium | High | Resume only skips steps in completed_steps list; default is full re-run |
| D-183 drift: src/sop/scripts/ change not backported | Medium | High | test_script_surface_sync.py is hard gate |
| PlannerRole stub accumulates debt | Low | Low | Stub is explicit and tested; Phase 2 task is named |

---

## Phase 1 to Phase 2 Gate

Phase 2 must not start until all of the following are true:

**Item 1.1 — Worker Abstraction**
- [ ] `Worker`, `WorkerRole`, `AuditorRole`, `PlannerRole` classes exist
- [ ] `WorkerResult` shape matches Phase 0 artifact schemas
- [ ] Workers instantiated in `run_cycle()` without behavioral change
- [ ] `tests/test_worker_base.py` passes
- [ ] `scripts/worker_base.py`, `worker_role.py`, `auditor_role.py`, `planner_role.py` exist (D-183 copies)
- [ ] All four added to sync-gate list in `tests/test_script_surface_sync.py`

**Item 1.2 — Skill Mapping**
- [ ] `assigned_roles` in allowlist for all skills
- [ ] `resolve_skills_for_role()` exists
- [ ] No hardcoded skill names in loop logic
- [ ] `tests/test_skill_mapping.py` passes

**Item 1.3 — State Persistence**
- [ ] Checkpoint load before `build_loop_cycle_runtime()` at run_loop_cycle.py:602
- [ ] Stale checkpoint invalidation: partial=false, age>24h, cycle_id mismatch, schema-invalid all return None
- [ ] Checkpoint written and validated after each step
- [ ] Resume from partial checkpoint skips completed steps
- [ ] Lesson stubs always written on resume (test_loop_cycle_runtime.py:122 still passes)
- [ ] loop_cycle_checkpoint.schema.json placed in src/sop/schemas/ (auto-copied by init_cmd.py:116 glob)
- [ ] loop_cycle_checkpoint_latest.json in LOOP_ARTIFACTS in test_cli_script_parity.py
- [ ] `tests/test_state_persistence.py` passes

**Cross-cutting**
- [ ] `pytest tests/test_script_surface_sync.py` passes (all Phase 1 touched scripts byte-identical)
- [ ] `pytest -m parity` passes
- [ ] `pytest -m integration` passes
- [ ] All existing tests green on Windows and Ubuntu
