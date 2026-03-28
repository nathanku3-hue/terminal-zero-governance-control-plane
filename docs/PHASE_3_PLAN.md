# Phase 3 — Reliability, Rollback, and Production Hardening

> **Status**: Draft — awaiting Phase 2 completion
> **Effort estimate**: 4–8 weeks total, three sequential workstreams
> **Repo**: `E:\Code\SOP\quant_current_scope`
> **Prerequisite**: Phase 2 gate fully checked
> **Gate**: All three items complete before Phase 4 begins

---

## Context: What Phase 2 established

- Structured run trace with `trace_id` on every loop cycle
- Per-step NDJSON logging with 500-record rolling window
- `PhaseGate` with Gate A + Gate B wired in `run_loop_cycle.py`
- `phase_gate_a/b_latest.json` emitted every run; `phase_handoff_latest.json` on Gate B PROCEED
- `StepExecutor` extracted; `LoopOrchestrator` encapsulates full loop logic
- `run_cycle(args) -> int` as thin wrapper; `__main__.py` unchanged
- 18 tests covering observability, gate, and orchestrator layers

Phase 3 builds three hardening capabilities in strict sequence:
rollback first, then production validation, then distributed coordination.

---

## Current State (as-inspected at Phase 2 completion)

| Area | What exists after Phase 2 | What is missing |
|---|---|---|
| Gate rollback | Gate HOLD exits code 1, writes checkpoint | No automated artifact revert; rollback is manual |
| Error recovery | Checkpoint resume skips completed steps | No artifact integrity check on resume |
| Production validation | Schema-validated artifacts at emit | No cross-run regression baseline; no drift detection |
| Parallel coordination | `run_parallel(n)` writes worker subdirs | No merge conflict detection; no quorum on divergent results |
| Observability pipeline | `loop_run_trace_latest.json` + NDJSON | No SLA breach detection on step duration |
| CLI surface | `sop run` via subprocess | No dry-run mode; no what-if gate evaluation |

---

## Sequencing Rule

```
3.1 Rollback & Recovery  -->  3.2 Production Validation  -->  3.3 Distributed Coordination
```

Each item is a strict prerequisite for the next. No parallelism across items.

---

## Worker Guidance

**Plan path**: `E:\Code\SOP\quant_current_scope\docs\PHASE_3_PLAN.md`

**Approval status**: Approved (conditional on Phase 2 gate). All 16 spec gaps resolved. Item 3.1 fully written. No remaining plan gaps.

### Implementation notes

- `_load_checkpoint()` does not yet exist in `run_loop_cycle.py`. The checkpoint file is read inline. This function must be introduced as part of 3.1 (the plan spec describes it as the intended location for the corrupt-state check).
- `integration` pytest marker not yet in `pyproject.toml`. Must be added before writing any `@pytest.mark.integration` tests (see CC-G1).
- All Phase 3 modified files (`orchestrator.py`, `phase_gate.py`, `step_executor.py`) are Phase 2 deliverables. Phase 3 must not begin until `pytest tests/test_script_surface_sync.py` passes with all Phase 2 D-183 copies present.

### Implementation checklist

**3.1 Rollback**
- [ ] `_load_checkpoint()` introduced in `run_loop_cycle.py`; corrupt-state check inside it
- [ ] `RollbackManager` in `src/sop/scripts/rollback_manager.py`
- [ ] `scripts/rollback_manager.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `src/sop/schemas/rollback.schema.json` (7 fields)
- [ ] Gate HOLD triggers revert; `rollback_latest.json` schema-valid; exit code 5
- [ ] `tests/test_rollback.py` passes (6 tests)

**3.2 Production Validation**
- [ ] `step_sla_seconds: float = 300.0` on `LoopCycleContext`; `--step-sla-seconds` flag
- [ ] `sla_breach` field added before append in `StepExecutor.run()`
- [ ] `run_regression_baseline.ndjson` appended on PROCEED; capped at 100
- [ ] `run_drift_latest.json` emitted every run; alerts suppressed if <5 records
- [ ] `--dry-run` in `run_loop_cycle.py` AND `src/sop/__main__.py`
- [ ] `tests/test_production_validation.py` passes (6 tests)

**3.3 Distributed Coordination**
- [ ] `integration` marker added to `pyproject.toml` first
- [ ] `worker_merge_latest.json` on conflict; `loop_run_trace_master_latest.json` (no collision)
- [ ] `--parallel-quorum` (`all`/`majority`/`first`) with correct tie-breaking
- [ ] Exit codes: 0=PASS, 1=HOLD, 2=write-error, 3=conflict, 4=timeout, 5=rollback
- [ ] `tests/test_distributed.py` passes (6 tests)
- [ ] `pytest tests/test_script_surface_sync.py` passes
- [ ] All existing tests still pass

### Key file locations (inherited from Phase 2)

| File | Note |
|---|---|
| `src/sop/scripts/run_loop_cycle.py` | Primary target |
| `src/sop/scripts/orchestrator.py` | `LoopOrchestrator` — Phase 2 output |
| `src/sop/scripts/phase_gate.py` | `PhaseGate` — Phase 2 output |
| `src/sop/scripts/step_executor.py` | `StepExecutor` — Phase 2 output |
| `src/sop/scripts/loop_cycle_runtime.py` | `LoopCycleRuntime` — add rollback fields in 3.1 |
| `docs/context/loop_run_trace_latest.json` | Baseline input for 3.2 drift detection |

---

## Item 3.1 — Rollback & Recovery

### Prerequisite: Phase 2 gate fully checked

### Step 1: Define rollback contract

`docs/context/rollback_latest.json` minimum schema:
```json
{
  "schema_version": "1.0",
  "trace_id": "...",
  "triggered_at_utc": "...",
  "trigger": "gate_a_hold",
  "artifacts_reverted": [
    {"path": "docs/context/exec_memory_packet_latest.json",
     "restored_from": ".rollback_tmp/exec_memory_packet_latest.json",
     "status": "restored"}
  ],
  "artifacts_not_found": [],
  "rollback_result": "CLEAN"
}
```
`rollback_result`: `CLEAN` (all reverted), `PARTIAL` (some missing), `FAILED` (error).

`rollback.schema.json` required fields: `schema_version`, `trace_id`, `triggered_at_utc`,
`trigger` (enum: `gate_a_hold`, `gate_b_hold`, `exception`),
`artifacts_reverted` (array of `{path, restored_from, status}`),
`artifacts_not_found` (array of str), `rollback_result` (enum: `CLEAN`, `PARTIAL`, `FAILED`).

### Step 2: Pre-run snapshot and RollbackManager

Before any step executes, capture a snapshot of `docs/context/` artifact state:
- **Scope**: all `*_latest.json` and `*_latest.md` files in `docs/context/` (not subdirs)
- **Snapshot data structure**: `dict[str, dict]` mapping `str(path)` to
  `{"mtime": float, "size": int}` — held in-memory (not written to disk)
- **Copy strategy**: copy each scoped file to `docs/context/.rollback_tmp/` before the first step
- **On HOLD**: restore from `.rollback_tmp/`; write `rollback_latest.json`; delete temp dir
- **On PROCEED**: delete `.rollback_tmp/` without restoring
- `.rollback_tmp/` is dot-prefixed — excluded from snapshot scope; not a live artifact

```python
class RollbackManager:
    def __init__(self, context_dir: Path) -> None: ...
    def snapshot(self) -> None:                              # called before first step
    def revert(self, trace_id: str, trigger: str) -> RollbackResult: ...  # on HOLD
    def cleanup(self) -> None:                               # on clean PROCEED exit
```

`LoopOrchestrator` wiring contract (Phase 2 `LoopOrchestrator` must exist first):
```python
def run_single(self) -> int:
    rm = RollbackManager(self._ctx.context_dir)
    rm.snapshot()                          # before first step
    try:
        exit_code = self._execute_loop_body()
        if exit_code == 1:                 # HOLD
            rm.revert(self._runtime.trace_id, trigger="gate_hold")
            return 5                       # rollback exit code
        rm.cleanup()
        return exit_code
    except Exception:
        rm.revert(self._runtime.trace_id, trigger="exception")
        raise
```
`_execute_loop_body()` is the extracted full loop body from Phase 2.3.

**Exit code table** (resolves collision with existing `return 2` at `run_loop_cycle.py:549,2048`):
- HOLD = 1 (Gate A or B returns HOLD; existing)
- write-error = 2 (existing OSError on summary write — do NOT reassign)
- conflict = 3 (Phase 3.3 parallel conflict — new)
- timeout = 4 (Phase 3.3 parallel timeout — new)
- rollback = 5 (new; RollbackManager.revert() triggered)

### Step 3: Corrupt-state detection on resume

When `_load_checkpoint()` finds a valid partial checkpoint, run integrity check
for each artifact named in `completed_steps`:
1. **File existence**: `path.exists()` — fail if missing
2. **JSON parse**: `json.loads(path.read_text())` — fail if parse error
3. **Required field presence**: `"schema_version" in parsed` — fail if absent
   (Full schema validation skipped here for performance)

If any check fails:
- Log `RESUME_BLOCKED: artifact missing or corrupt: <path>` to stderr
- Return `None` (treat checkpoint as stale; full re-run)

Integrity check location: inside `_load_checkpoint()`, after stale-age check.
Add `--skip-integrity-check` CLI flag for emergency bypass (default: enabled).

### Step 4: Tests

`tests/test_rollback.py` — 6 tests:
- `test_snapshot_created_before_steps`
- `test_revert_on_hold_restores_artifacts`
- `test_rollback_artifact_written`
- `test_rollback_schema_valid`
- `test_corrupt_checkpoint_forces_full_run`
- `test_cleanup_removes_snapshot_on_proceed`

### Files to create
```
src/sop/scripts/rollback_manager.py
scripts/rollback_manager.py              # D-183 copy
src/sop/schemas/rollback.schema.json
docs/context/schemas/rollback.schema.json
tests/test_rollback.py
```

### Done criteria
- [ ] `RollbackManager` with `snapshot()`, `revert()`, `cleanup()` exists
- [ ] `LoopOrchestrator` wires rollback at correct lifecycle points per contract above
- [ ] Gate HOLD triggers revert; `rollback_latest.json` emitted and schema-valid
- [ ] Corrupt artifact on resume forces full re-run (JSON parse + field existence check)
- [ ] Exit code 5 on rollback (not 2; distinct from write-error and HOLD)
- [ ] `scripts/rollback_manager.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_rollback.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 3.2 — Production Validation

### Prerequisite: 3.1 complete

### Step 1: Cross-run regression baseline

After each successful (PROCEED) run, append a compact record to
`docs/context/run_regression_baseline.ndjson`:
```json
{"trace_id": "...", "run_at_utc": "...", "final_result": "PASS",
 "step_count": 12, "pass_count": 12, "error_count": 0,
 "p50_duration_s": 4.2, "p95_duration_s": 18.1}
```
Keep last 100 records via `_compact_ndjson_rolling()` (Phase 2).

**p50/p95**: sort `duration_seconds` across all steps in current run; computed in
`LoopOrchestrator` after `run_single()` returns. Appended only on PROCEED.
Drift detection runs on every run; alerts suppressed if <5 baseline records exist.

### Step 2: Step duration SLA

**SLA field**: one global `step_sla_seconds: float = 300.0` on `LoopCycleContext`
(not per-step). Configurable via `--step-sla-seconds` (default: 300).

**Injection point**: `StepExecutor.run()` receives `step_sla_seconds` as constructor arg.
After `_run_command()` returns, before appending to `runtime.steps`, add
`"sla_breach": True` if `duration_seconds > step_sla_seconds`. Avoids post-append mutation.
Add `sla_breach_count` to `loop_run_trace_latest.json` metrics block.

### Step 3: Drift detection

Compare current metrics against last 10 baseline records after every run:
- `error_count` increased from 0 in last 5 runs → `DRIFT_ALERT` to stderr
- `p95_duration_s` increased >50% vs trailing 10-run average → `PERF_REGRESSION`
- Write `docs/context/run_drift_latest.json` every run (`alerts: []` = clean)

### Step 4: Dry-run gate evaluation

Add `--dry-run` to:
1. `parse_args()` in `run_loop_cycle.py`
2. `cmd_run()` in `src/sop/__main__.py` (passes flag through to subprocess)

`PhaseGate.evaluate_dry_run(context_dir: Path) -> PhaseGateResult`:
- Gate A: check `exec_memory_packet_latest.json` exists AND checkpoint has
  `exec_memory_cycle_ready: true`
- Gate B: check `no_schema_violations` + `no_error_steps` from existing trace artifact
- No artifact writes; exits 0 on PROCEED, 1 on HOLD

### Step 5: Tests

`tests/test_production_validation.py` — 6 tests:
- `test_baseline_record_appended_on_proceed`
- `test_baseline_rolling_capped_at_100`
- `test_sla_breach_flagged_in_step_record`
- `test_drift_alert_on_error_increase`
- `test_drift_clean_on_stable_run`
- `test_dry_run_evaluates_gates_without_executing`

### Files to create
```
src/sop/schemas/run_drift.schema.json
docs/context/schemas/run_drift.schema.json
tests/test_production_validation.py
```

### Files to modify
```
src/sop/scripts/phase_gate.py          # add evaluate_dry_run()
src/sop/scripts/step_executor.py       # step_sla_seconds arg; sla_breach field
src/sop/scripts/loop_cycle_context.py  # add step_sla_seconds field
src/sop/scripts/orchestrator.py        # append baseline; run drift check
src/sop/scripts/run_loop_cycle.py      # --dry-run; --step-sla-seconds
src/sop/__main__.py                    # pass --dry-run to subprocess
scripts/phase_gate.py + scripts/step_executor.py + scripts/orchestrator.py + scripts/run_loop_cycle.py  # D-183 backports
```

### Done criteria
- [ ] `run_regression_baseline.ndjson` appended on PROCEED; capped at 100 records
- [ ] `sla_breach` in step records; `sla_breach_count` in trace metrics
- [ ] `run_drift_latest.json` emitted every run; alerts suppressed <5 records
- [ ] `--dry-run` evaluates gates without executing steps or writing artifacts
- [ ] `--dry-run` passed through `__main__.py` subprocess call
- [ ] `tests/test_production_validation.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 3.3 — Distributed Coordination

### Prerequisite: 3.2 complete

### Step 1: Parallel worker merge conflict detection

`worker_merge_latest.json` schema fields:
```json
{
  "schema_version": "1.0", "trace_id": "master-...", "triggered_at_utc": "...",
  "quorum_policy": "all", "worker_count": 2,
  "workers": [{"worker_id": 0, "trace_id": "...", "final_result": "PASS"},
               {"worker_id": 1, "trace_id": "...", "final_result": "HOLD"}],
  "conflicts": [{"worker_ids": [0,1], "field": "final_result", "values": ["PASS","HOLD"]}],
  "aggregate_result": "CONFLICT"
}
```
Conflict: two+ workers produce different `final_result`. Exit code 3.

### Step 2: Quorum policy

`--parallel-quorum` (default: `all`):
- `all` — all workers must PASS
- `majority` — strict majority (> n/2, rounded up) must PASS;
  ties go to CONFLICT (e.g. n=2: 1 PASS + 1 HOLD = tie = CONFLICT;
  n=3: 2 PASS + 1 HOLD = PROCEED)
- `first` — first worker to PASS wins; remaining queued futures cancelled via
  `Future.cancel()` (running workers complete but results ignored)

### Step 3: Master trace — separate path (no collision)

Master trace written to `docs/context/loop_run_trace_master_latest.json`
(separate from Phase 2.1 single-run `loop_run_trace_latest.json`).

```json
{
  "schema_version": "1.0", "trace_id": "master-...", "worker_count": 2,
  "quorum_policy": "all",
  "workers": [{"worker_id": 0, "trace_id": "...", "final_result": "PASS"}],
  "aggregate_result": "PASS", "conflicts": []
}
```

### Step 4: Timeout and exit code precedence

`--parallel-timeout-seconds` (default: 600):
- Cancel queued futures via `executor.shutdown(cancel_futures=True)`
- Running workers complete (ThreadPoolExecutor cannot interrupt them)
- Timed-out workers marked `"final_result": "TIMEOUT"` in master trace
- Exit code 4

**Exit code precedence** when multiple conditions apply:
TIMEOUT (4) > CONFLICT (3) > HOLD (1) > rollback (5)

**Full exit code table:**
- 0 = PASS
- 1 = HOLD (Gate A or B)
- 2 = write-error (existing OSError on summary write — unchanged)
- 3 = conflict (parallel workers disagree)
- 4 = timeout (parallel worker exceeded deadline)
- 5 = rollback (RollbackManager.revert() triggered)

### Step 5: Tests

`tests/test_distributed.py` — 6 tests:
- `test_parallel_all_pass_no_conflict`
- `test_parallel_conflict_detected`
- `test_quorum_majority_proceeds` — n=3, 2 PASS + 1 HOLD = PROCEED
- `test_master_trace_written_to_separate_path` — no collision with Phase 2.1
- `test_worker_timeout_exits_code_4`
- `test_worker_subdirs_isolated_no_collision` — regression guard for Phase 2.3

### Files to create
```
src/sop/schemas/worker_merge.schema.json
src/sop/schemas/loop_run_trace_master.schema.json
docs/context/schemas/worker_merge.schema.json
docs/context/schemas/loop_run_trace_master.schema.json
tests/test_distributed.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py    # merge validation, quorum, timeout
scripts/orchestrator.py            # D-183 backport
```

### Done criteria
- [ ] Conflict detection with `worker_merge_latest.json`; exit code 3
- [ ] `--parallel-quorum` (`all`/`majority`/`first`) with correct tie-breaking
- [ ] Master trace at `loop_run_trace_master_latest.json` (no Phase 2.1 collision)
- [ ] Timeout cancels queued futures; exit code 4
- [ ] Exit code table: 0=PASS, 1=HOLD, 2=write-error, 3=conflict, 4=timeout, 5=rollback
- [ ] `tests/test_distributed.py` passes (6 tests)
- [ ] All existing tests still pass
- [ ] `pytest tests/test_script_surface_sync.py` passes

---

## Cross-cutting

### CC-G1: integration pytest marker

Add `integration` marker to `pyproject.toml` before writing any integration-marked tests:
```toml
markers = [
  "parity: CLI-vs-script parity contract tests",
  "state_persistence: Phase 1.3 checkpoint and resume tests",
  "integration: end-to-end integration tests requiring live filesystem",
]
```

### CC-G3: Phase 2 dependency enforcement

All Phase 3 items modify `orchestrator.py`, `phase_gate.py`, `step_executor.py` — files
that do not exist until Phase 2 completes. Phase 3 implementation must not begin until
`pytest tests/test_script_surface_sync.py` passes with all three Phase 2 D-183 copies present.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Snapshot temp dir grows large | Medium | Medium | Scope to `*_latest.*` only; cleanup on every exit path |
| Integrity check on resume adds latency | Low | Low | JSON parse only; `--skip-integrity-check` bypass available |
| Drift detection false positives on first run | Medium | Low | Suppress if <5 baseline records |
| `first` quorum can't cancel running workers | High | Medium | Document limitation; running workers complete but results ignored |
| Exit code 2 collision | Resolved | — | write-error keeps 2; rollback assigned 5 |
| Phase 2 deliverables not ready | Medium | High | Phase 3 gate requires Phase 2 sync-gate passing |

---

## Phase 3 to Phase 4 Gate

Phase 4 must not start until all of the following are true:

**Item 3.1 — Rollback & Recovery**
- [ ] `RollbackManager` exists; `LoopOrchestrator` wires it per contract
- [ ] Gate HOLD triggers revert; `rollback_latest.json` schema-valid
- [ ] Corrupt checkpoint forces full re-run (JSON parse + field check)
- [ ] Exit code 5 on rollback (not 2)
- [ ] `scripts/rollback_manager.py` D-183 copy; sync-gate updated
- [ ] `tests/test_rollback.py` passes (6 tests)

**Item 3.2 — Production Validation**
- [ ] Regression baseline NDJSON appended on PROCEED; capped at 100
- [ ] `sla_breach` flagged in step records and trace metrics
- [ ] `run_drift_latest.json` emitted every run; alerts suppressed <5 records
- [ ] `--dry-run` passes through `__main__.py`; no artifact writes
- [ ] `tests/test_production_validation.py` passes (6 tests)

**Item 3.3 — Distributed Coordination**
- [ ] Conflict detection with `worker_merge_latest.json`; exit code 3
- [ ] Quorum policy `all`/`majority`/`first` with correct tie-breaking
- [ ] Master trace at separate path (no Phase 2.1 collision)
- [ ] Timeout exit code 4; running workers allowed to complete
- [ ] `tests/test_distributed.py` passes (6 tests)

**Cross-cutting**
- [ ] `integration` marker registered in `pyproject.toml`
- [ ] Exit codes consistent: 0=PASS, 1=HOLD, 2=write-error, 3=conflict, 4=timeout, 5=rollback
- [ ] `pytest tests/test_script_surface_sync.py` passes
- [ ] `pytest -m integration` passes
- [ ] All existing tests green on Windows
- [ ] At least one production run completed with rollback enabled
