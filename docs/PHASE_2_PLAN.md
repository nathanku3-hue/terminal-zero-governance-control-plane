# Phase 2 — Scaling Plan

> **Status**: Approved — ready for implementation (all gaps resolved, closure inventory verified)
> **Effort estimate**: 3–7 weeks total, three sequential workstreams
> **Repo**: `E:\Code\SOP\quant_current_scope`
> **Prerequisite**: Phase 1 gate fully checked
> **Gate**: All three items complete before Phase 3 begins

---

## Context: What Phase 1 established

- `Worker` ABC, `WorkerRole`, `AuditorRole`, `PlannerRole` (stub) with D-183 copies
- `WorkerResult` as standardized role output
- Per-role skill injection via `resolve_skills_for_role()`
- Single-loop checkpoint with resume-on-partial

Phase 2 builds three scaling capabilities in strict sequence:
observability first, then automation, then orchestrator.

---

## Current State (as-inspected)

| Area | What exists | What is missing |
|---|---|---|
| Logging | `started_utc`/`ended_utc`/`duration_seconds` per step in `runtime.steps` | No structured JSON log per run; no trace ID |
| Metrics | Step status counts in `build_summary_payload()` at `run_loop_cycle.py:~650` | Not emitted as queryable artifact; no cross-run error rate |
| Time utils | `src/sop/scripts/utils/time_utils.py` with `utc_now()`, `utc_iso()` | Not used for trace ID generation |
| Phase automation | Manual phase-transition approvals | No automated gate evaluation; no handoff trigger |
| Orchestrator | Imperative loop body ~975 lines (~line 755-1730) | No separation from CLI; no parallel Worker coordination |
| Step execution | `run_python_step()` inner closure at ~line 975 | Cannot be called outside loop body; 8 total inner closures |
| CLI entrypoint | `src/sop/__main__.py` dispatches via `subprocess.run()` to `run_loop_cycle.py` | No `run_cycle()` function exists; introduced in 2.3 |

---

## Sequencing Rule

```
2.1 Observability  -->  2.2 SOP Automation  -->  2.3 Modular Orchestrator
```

Each item is a strict prerequisite for the next. No parallelism across items.
---

## Worker Guidance

**Plan path**: `E:\Code\SOP\quant_current_scope\docs\PHASE_2_PLAN.md`

**Approval status**: Approved. All gaps resolved. Closure inventory verified against source.

### Confirmed closure inventory (run_loop_cycle.py)

All 8 inner closures confirmed present in order. Imperative execution body begins after ~line 1240 with no further inner `def` blocks.

| Closure | Confirmed line | Closes over |
|---|---|---|
| `build_summary_payload` | ~823 | `runtime`, `ctx`, `_scan_disagreement_sla`, `_load_compaction_status_summary` |
| `run_python_step` | ~975 | `runtime`, `ctx`, `_run_command` |
| `_step_by_name` | ~994 | `runtime` |
| `_remove_if_exists` | ~998 | stdlib only |
| `_promote_exec_memory_outputs` | ~1005 | `ctx`, `_validate_exact_path`, `_atomic_write_text` |
| `_execute_exec_memory_stage` | ~1083 | all above + `_write_temp_summary_snapshot`, `_skip_step` |
| `_write_temp_summary_snapshot` | ~1168 | `runtime`, `ctx`, `build_summary_payload`, `_atomic_write_text` |
| `_write_round_contract_summary_snapshot` | ~1216 | `runtime`, `ctx`, `build_summary_payload`, `_atomic_write_text` |

### Implementation checklist (pure coding tasks — no further plan clarification needed)

**Schemas (3 new files)**
- [ ] `src/sop/schemas/loop_run_trace.schema.json`
- [ ] `src/sop/schemas/loop_run_steps.schema.json`
- [ ] `src/sop/schemas/phase_handoff.schema.json`

**2.1 Observability**
- [ ] `trace_id` field added to `LoopCycleRuntime` at `loop_cycle_runtime.py:88`, set in `build_loop_cycle_runtime()` at factory time
- [ ] `_compact_ndjson_rolling(path, max_records=500)` added to `compaction_retention.py`; called once at run end
- [ ] NDJSON append helper covers both `run_python_step` paths (~line 978 missing-script AND ~line 993 `_run_command`)
- [ ] Trace artifact emitted after `build_summary_payload()`, validated against `loop_run_trace.schema.json`
- [ ] `tests/test_observability.py` — 6 tests passing

**2.2 Phase Gate**
- [ ] `src/sop/scripts/phase_gate.py` with `PhaseGate` class; `scripts/phase_gate.py` byte-identical D-183 copy
- [ ] Gate A wired at ~line 1665 (before `persist_advisory_sections()`); Gate B at ~line 1703 (before `build_summary_payload()`)
- [ ] HOLD path: write checkpoint (`partial=true`), emit gate artifact, `sys.exit(1)`
- [ ] `phase_gate_a_latest.json` + `phase_gate_b_latest.json` emitted on applicable runs
- [ ] `phase_handoff_latest.json` written on Gate B PROCEED
- [ ] `tests/test_phase_gate.py` — 7 tests passing
- [ ] `phase_gate.py` entry added to `PHASE_0_SCRIPTS` in `test_script_surface_sync.py`

**2.3 Orchestrator**
- [ ] `src/sop/scripts/step_executor.py` with `StepExecutor`; `_run_command` (line 404) moved here
- [ ] `src/sop/scripts/orchestrator.py` with `LoopOrchestrator`; all 8 closures become `self`-methods
- [ ] `scripts/step_executor.py` + `scripts/orchestrator.py` byte-identical D-183 copies
- [ ] `run_cycle(args) -> int` introduced in `run_loop_cycle.py` as thin wrapper; `if __name__` calls `sys.exit(run_cycle(parse_args()))`
- [ ] `__main__.py` unchanged
- [ ] `tests/test_orchestrator.py` — 5 tests passing
- [ ] `step_executor.py` + `orchestrator.py` entries added to `PHASE_0_SCRIPTS`

**Cross-cutting**
- [ ] `pytest tests/test_script_surface_sync.py` passes (all D-183 copies byte-identical)
- [ ] All existing tests still pass

### Key file locations

| File | Note |
|---|---|
| `src/sop/scripts/run_loop_cycle.py` | Primary target; 1730 lines |
| `src/sop/scripts/loop_cycle_runtime.py:88` | `LoopCycleRuntime` dataclass — add `trace_id` |
| `src/sop/scripts/utils/compaction_retention.py` | Add `_compact_ndjson_rolling()` |
| `src/sop/scripts/utils/atomic_io.py` | Use `atomic_write_json` for all new artifact writes |
| `src/sop/scripts/utils/time_utils.py` | Use `utc_now_iso()` for `trace_id` generation |
| `tests/test_script_surface_sync.py:31` | `PHASE_0_SCRIPTS` — add 3 new module entries |

---

## Item 2.1 — Observability & Telemetry

### Step 1: Define the run trace artifact

`docs/context/loop_run_trace_latest.json` — minimum schema:
```json
{
  "schema_version": "1.0",
  "trace_id": "20260327T120000Z-a3f2",
  "generated_at_utc": "2026-03-27T12:00:00Z",
  "repo_id": "quant_current_scope",
  "duration_seconds": 47.3,
  "steps": [
    {"name": "build_exec_memory_packet", "status": "PASS", "exit_code": 0,
     "started_utc": "...", "ended_utc": "...", "duration_seconds": 7.1}
  ],
  "metrics": {"pass_count": 12, "hold_count": 0, "fail_count": 0,
               "error_count": 0, "total_steps": 12, "artifact_count": 4},
  "final_result": "PASS",
  "final_exit_code": 0
}
```

`trace_id` format: `<utc_compact>-<4 hex chars from hash of repo_id+timestamp>`.
Use `time_utils.utc_now_iso()` already in `src/sop/scripts/utils/time_utils.py`.

Add `loop_run_trace.schema.json` to `src/sop/schemas/`.
It is auto-copied by `init_cmd.py:116` `*.json` glob — no code change to `init_cmd.py`.

### Step 2: Add trace_id to LoopCycleRuntime

Add field to `loop_cycle_runtime.py`:
```python
trace_id: str = field(default="")
```
Set in `build_loop_cycle_runtime()` before returning. Add `trace_id` to
`loop_cycle_checkpoint.schema.json`; on resume, assert checkpoint `trace_id` matches `runtime.trace_id`.

### Step 3: Emit trace artifact at run end

In `run_loop_cycle.py` after `build_summary_payload()`:
- Build trace payload from `runtime.steps`, `runtime.trace_id`, `runtime.generated_at_utc`, `ctx.repo_id`
- Validate against `loop_run_trace.schema.json` before write (Phase 0 emit-time gate pattern)
- Write atomically via `atomic_write_json` from `scripts/utils/atomic_io.py`

### Step 4: Per-step NDJSON logging

Append each step record as a newline-delimited JSON line to
`docs/context/loop_run_steps_latest.ndjson` as each step completes (not batched at end).

Maintain `docs/context/loop_run_steps_rolling.ndjson` — last 500 records, pruned by
existing `compaction_retention.py` in `src/sop/scripts/utils/`.

### Step 5: Tests

`tests/test_observability.py` — 6 tests:
- `test_trace_artifact_written`
- `test_trace_schema_valid`
- `test_trace_id_format` — matches `<timestamp>-<4hex>` pattern
- `test_trace_id_on_runtime` — set before first step executes
- `test_steps_ndjson_written` — one line per step
- `test_metrics_match_steps` — `pass_count` equals step records with status PASS

### Files to create
```
src/sop/schemas/loop_run_trace.schema.json
docs/context/schemas/loop_run_trace.schema.json
tests/test_observability.py
```

### Files to modify
```
src/sop/scripts/loop_cycle_runtime.py   # add trace_id field
src/sop/scripts/run_loop_cycle.py       # emit trace + ndjson per step
src/sop/scripts/loop_cycle_context.py  # add loop_run_trace_latest path
scripts/loop_cycle_runtime.py           # D-183 backport
scripts/run_loop_cycle.py               # D-183 backport
scripts/loop_cycle_context.py           # D-183 backport
```

### Done criteria
- [ ] `loop_run_trace_latest.json` emitted and schema-valid after every run
- [ ] `trace_id` on `LoopCycleRuntime` set before first step
- [ ] `loop_run_steps_latest.ndjson` written with one line per step
- [ ] `trace_id` in checkpoint schema; resume asserts match
- [ ] `tests/test_observability.py` passes (6 tests)
- [ ] All existing tests still pass
- [ ] `pytest tests/test_script_surface_sync.py` passes

---

## Item 2.2 — SOP Automation / Phase Progression

### Prerequisite: 2.1 complete

### Step 1: Define the phase-gate contract

`docs/context/phase_gate_latest.json` — minimum schema:
```json
{
  "schema_version": "1.0",
  "evaluated_at_utc": "...",
  "trace_id": "...",
  "from_phase": "exec_memory",
  "to_phase": "advisory",
  "gate_conditions": [
    {"name": "exec_memory_cycle_ready", "result": true},
    {"name": "no_schema_violations", "result": true},
    {"name": "no_error_steps", "result": true}
  ],
  "all_conditions_met": true,
  "decision": "PROCEED"
}
```

Add `phase_gate.schema.json` to `src/sop/schemas/`.

### Step 2: Implement gate evaluator

Create `src/sop/scripts/phase_gate.py`:
```python
@dataclass
class PhaseGateResult:
    all_conditions_met: bool
    decision: str          # PROCEED | HOLD
    conditions: list[dict[str, Any]]

class PhaseGate:
    def __init__(self, from_phase: str, to_phase: str, repo_root: Path) -> None: ...
    def evaluate(self, runtime: LoopCycleRuntime) -> PhaseGateResult: ...
    def emit(self, result: PhaseGateResult, trace_id: str) -> Path: ...
```

Three built-in gate conditions:
1. `exec_memory_cycle_ready` — `runtime.exec_memory_cycle_ready is True`
2. `no_schema_violations` — `loop_run_trace_latest.json` `final_result` not `ERROR`
3. `no_error_steps` — no step in `runtime.steps` has status `ERROR`

Decision: `PROCEED` if all pass; `HOLD` if any fail.
Automatic rollback is Phase 3 — not implemented here.

D-183: create `scripts/phase_gate.py` byte-identical copy.
Add to `tests/test_script_surface_sync.py` sync-gate list.

### Step 3: Wire gate into run_loop_cycle.py

Insert at two existing transition points:
1. **Gate A** — after exec memory promotion, before advisory artifact generation
2. **Gate B** — after advisory artifacts, before loop summary write

If gate returns `HOLD`: skip subsequent steps, write gate artifact,
emit loop summary with `final_result: HOLD`.
If gate returns `PROCEED`: continue normally, emit gate artifact for audit trail.

### Step 4: Automated handoff artifact

When Gate B returns `PROCEED`, write
`docs/context/phase_handoff_latest.json`:
```json
{"from_phase": "advisory", "to_phase": "summary",
 "trace_id": "...", "triggered_at_utc": "..."}
```

This is the automated handoff signal. Two automated transitions (Gate A + Gate B)
meet the roadmap requirement. No subprocess trigger in Phase 2; that is Phase 3.

### Step 5: Tests

`tests/test_phase_gate.py` — 7 tests:
- `test_gate_proceed_when_all_conditions_met`
- `test_gate_hold_when_exec_memory_not_ready`
- `test_gate_hold_when_error_step_present`
- `test_gate_artifact_written_on_proceed`
- `test_gate_artifact_written_on_hold`
- `test_gate_artifact_schema_valid`
- `test_handoff_artifact_written_on_gate_b_proceed`

### Files to create
```
src/sop/scripts/phase_gate.py
scripts/phase_gate.py               # D-183 copy
src/sop/schemas/phase_gate.schema.json
docs/context/schemas/phase_gate.schema.json
tests/test_phase_gate.py
```

### Files to modify
```
src/sop/scripts/run_loop_cycle.py
scripts/run_loop_cycle.py           # D-183 backport
tests/test_script_surface_sync.py   # add phase_gate.py
```

### Done criteria
- [ ] `PhaseGate` class with `evaluate()` and `emit()` exists
- [ ] Gate A wired before advisory generation; Gate B before loop summary
- [ ] `phase_gate_latest.json` emitted on every run (PROCEED or HOLD)
- [ ] `phase_handoff_latest.json` written when Gate B returns PROCEED
- [ ] Gate HOLD skips steps and emits HOLD summary without crashing
- [ ] `scripts/phase_gate.py` D-183 copy exists; added to sync-gate list
- [ ] `tests/test_phase_gate.py` passes (7 tests)
- [ ] All existing tests still pass
- [ ] `pytest tests/test_script_surface_sync.py` passes

---

## Item 2.3 — Modular Orchestrator Layer

### Prerequisite: 2.1 + 2.2 complete

### Step 1: Extract step executor from run_cycle()

Current: `run_python_step()` is a closure inside `run_cycle()` at `run_loop_cycle.py:762`.
It captures `ctx`, `runtime`, and the inner `_run_command` from the enclosing scope.

Extract to `src/sop/scripts/step_executor.py`:
```python
class StepExecutor:
    """Executes a subprocess step and records the result on LoopCycleRuntime."""
    def __init__(self, ctx: LoopCycleContext, runtime: LoopCycleRuntime) -> None: ...
    def run(self, step_name: str, script_path: Path, script_args: list[str]) -> None: ...
```

`StepExecutor.run()` replaces the `run_python_step()` closure.
The existing `_run_command()` function (called at `run_loop_cycle.py:~780`) moves to
`step_executor.py` as a private method.

D-183: create `scripts/step_executor.py` byte-identical copy.
Add to `tests/test_script_surface_sync.py` sync-gate list.

### Step 2: Extract loop logic from CLI entrypoint

Current: `src/sop/__main__.py` calls `run_cycle(args)` directly.

Create `src/sop/scripts/orchestrator.py`:
```python
class LoopOrchestrator:
    """Coordinates one or 