# Phase 4 — Bridge Loop & Planner Feedback

> **Status**: Draft — awaiting Phase 3 completion
> **Effort estimate**: 4–7 weeks total, three sequential workstreams
> **Repo**: `E:\Code\SOP\quant_current_scope`
> **Prerequisite**: Phase 3 gate fully checked
> **Gate**: All three items complete before Phase 5 begins

---

## Context: What Phase 3 established

- `RollbackManager` with automatic artifact revert on Gate HOLD (exit code 5)
- Corrupt checkpoint detection; `_load_checkpoint()` introduced
- Cross-run regression baseline NDJSON; SLA breach detection per step
- Drift detection (`run_drift_latest.json`) after every run
- `--dry-run` gate evaluation without execution
- Parallel worker conflict detection with quorum policy
- Exit code table: 0=PASS, 1=HOLD, 2=write-error, 3=conflict, 4=timeout, 5=rollback

Phase 4 closes the Loop A to Loop B bridge: worker output must become planner truth.
Until this phase, execution truth stays inside the engineering loop and the planner
re-reads the whole repo to understand what changed. Phase 4 makes the bridge
explicit, thin, and machine-writable.

---

## ENDGAME alignment

From ENDGAME.md Section 3 (The Bridge Between A and B):
The engineering loop must return: what changed in the system, what changed in the
product stage, what assumption got stronger or weaker, what bottleneck moved,
what decision now matters, and what should not be done next.

From Section 8 (Orchestrator State Model):
The orchestrator should get this from small authoritative artifacts, not from
accumulated chat memory.

Phase 4 delivers both:
1. A machine-writable bridge artifact that translates execution truth into planner language
2. An orchestrator state surface that a fresh worker can load in one read

---

## Current State (as-inspected at Phase 3 completion)

| Area | What exists after Phase 3 | What is missing |
|---|---|---|
| Execution truth | `loop_run_trace_latest.json` with steps + metrics | Not translated into planner language |
| Bridge artifact | None | No `bridge_contract_current.md` |
| Planner entry | Whole-repo reread or chat memory | No compact planner packet |
| Orchestrator state | `LoopOrchestrator` runs the loop | No persistent state surface between runs |
| Bottleneck tracking | Gate HOLD reason in gate artifact | Not surfaced as named bottleneck |
| Decision tracking | None | No open-decision artifact |

---

## Sequencing Rule

```
4.1 Bridge Contract  -->  4.2 Planner Packet  -->  4.3 Orchestrator State Surface
```

Each item is a strict prerequisite for the next. No parallelism across items.

---

## Worker Guidance

**Plan path**: `E:\Code\SOP\quant_current_scope\docs\PHASE_4_PLAN.md`

Approved — conditional on Phase 3 gate. All gaps resolved. Rollback scope Option A selected. No remaining blockers.

### Implementation notes

- `_load_orchestrator_state()` does not yet exist — introduced as part of 4.3.
- Bridge/planner/state writers are called AFTER rm.revert()/rm.cleanup() (Option A).
  They are never rolled back. They must survive HOLD to communicate hold reason to planner.
- Revised call order in run_single(): _execute_loop_body() -> rm.revert/cleanup ->
  BridgeContractWriter -> PlannerPacketWriter -> OrchestratorStateWriter -> return.
- CC-G2: integration marker confirmed in pyproject.toml. No action needed.
- CC-G1: rollback_manager.py confirmed at line 71 of PHASE_0_SCRIPTS. Closed.
- All three new writers must be added to PHASE_0_SCRIPTS in test_script_surface_sync.py.

### Implementation checklist

**4.1 Bridge Contract**
- [ ] `integration` marker confirmed in pyproject.toml (already done)
- [ ] `BridgeContractWriter` in `src/sop/scripts/bridge_contract_writer.py`
- [ ] `scripts/bridge_contract_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `src/sop/schemas/bridge_contract.schema.json` (DO_NOT_REDECIDE minItems: 0)
- [ ] `bridge_contract_current.md` + JSON shadow written on every run
- [ ] Gate-absent handled: missing gate files treated as `{}` (PROCEED defaults)
- [ ] PM_DELTA: "Insufficient history" when fewer than 2 baseline records
- [ ] `_load_json_or_empty()` helper in orchestrator.py
- [ ] `tests/test_bridge_contract.py` passes (6 tests)

**4.2 Planner Packet**
- [ ] `PlannerPacketWriter` in `src/sop/scripts/planner_packet_writer.py`
- [ ] `scripts/planner_packet_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `src/sop/schemas/planner_packet.schema.json` (decision_tail minItems: 0)
- [ ] `planner_packet_current.md` + JSON shadow written on every run
- [ ] `active_brief`: falls back to "Advance to next phase" if not in exec_memory schema
- [ ] `decision_tail`: empty `[]` valid first run; cap 10 in JSON shadow; Markdown shows last 3
- [ ] `test_fresh_worker_needs_only_packet`: all 6 keys + 3 non-empty strings
- [ ] `tests/test_planner_packet.py` passes (6 tests)

**4.3 Orchestrator State Surface**
- [ ] `OrchestratorStateWriter` in `src/sop/scripts/orchestrator_state_writer.py`
- [ ] `scripts/orchestrator_state_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `src/sop/schemas/orchestrator_state.schema.json`
- [ ] `orchestrator_state_latest.json` written on every run
- [ ] `evidence_freshness` emits `null` for missing artifacts (FileNotFoundError handled)
- [ ] Prior state load: None for missing file, bad JSON, missing schema_version, version mismatch
- [ ] `_load_orchestrator_state()` introduced in `orchestrator.py`
- [ ] `--force` added to `run_loop_cycle.py`, `LoopCycleContext`, `src/sop/__main__.py`
- [ ] `tests/test_orchestrator_state.py` passes (6 tests)

**Cross-cutting**
- [ ] Wiring order: _execute_loop_body -> rm.revert/cleanup -> bridge -> planner -> state
- [ ] All 3 new writer modules in `PHASE_0_SCRIPTS`
- [ ] `pytest tests/test_script_surface_sync.py` passes
- [ ] `pytest -m integration` passes
- [ ] All existing tests still pass
- [ ] ENDGAME: planner enters from planner_packet_current.md alone (no whole-repo reread)

### Success criteria

Phase 4 is successful when:
- `bridge_contract_current.md` is written after every run and a planner can read
  what changed and what to do next without opening any other file
- `planner_packet_current.md` alone is sufficient for a fresh worker to reconstruct
  the full current situation (6 sections, all non-trivially populated)
- `orchestrator_state_latest.json` gives the orchestrator full system awareness
  on startup without reading chat history
- All 18 new tests pass; all existing tests still pass
- At least one production run emits all three artifacts and they are schema-valid

### Key file locations (inherited from Phase 3)

| File | Note |
|---|---|
| `src/sop/scripts/orchestrator.py` | Add bridge + planner + state emit calls |
| `src/sop/scripts/phase_gate.py` | Gate results feed bridge contract |
| `docs/context/loop_run_trace_latest.json` | Primary input for bridge contract |
| `docs/context/phase_gate_a_latest.json` | Gate A result — feeds bottleneck field |
| `docs/context/phase_gate_b_latest.json` | Gate B result — feeds recommended next step |
| `docs/context/run_drift_latest.json` | Drift alerts — feed observability pack |

---

## Item 4.1 — Bridge Contract

### Prerequisite: Phase 3 gate fully checked

### Step 1: Define the bridge contract artifact

`docs/context/bridge_contract_current.md` — Markdown so both humans and planners
can read it. Backed by a JSON shadow for schema validation.

Minimum structure:
```
# Bridge Contract
> GeneratedAtUTC: 2026-03-28T12:00:00Z
> TraceID: 20260328T120000Z-a3f2
> GateResult: PROCEED

## SYSTEM_DELTA
What changed in the system this run.

## PM_DELTA
What changed in product meaning.

## OPEN_DECISION
The one decision required before the next run is meaningful. None if absent.

## RECOMMENDED_NEXT_STEP
The single most valuable next action for the planner.

## DO_NOT_REDECIDE
Decisions already settled; must not be re-opened next round.
```

`bridge_contract.schema.json` required fields (JSON shadow):
`schema_version`, `trace_id`, `generated_at_utc`, `gate_result`,
`system_delta`, `pm_delta`, `open_decision`, `recommended_next_step`,
`do_not_redecide` (array of str).

### Step 2: BridgeContractWriter

```python
class BridgeContractWriter:
    def __init__(self, context_dir: Path, schema_dir: Path) -> None: ...
    def write(
        self,
        trace: dict,          # loop_run_trace_latest.json content
        gate_a: dict,         # phase_gate_a_latest.json content
        gate_b: dict,         # phase_gate_b_latest.json content
        drift: dict,          # run_drift_latest.json content
    ) -> Path:
        """Derive bridge fields from artifacts; write MD + JSON shadow atomically."""
```

Field derivation rules:

**Gate file absence handling**: `phase_gate_a_latest.json` and `phase_gate_b_latest.json`
are only written when `PhaseGate` is active (not None). `BridgeContractWriter.write()`
treats absent gate files as empty dicts `{}` — same as a PROCEED with no hold reasons:
- `gate_a = {}` → no Gate A hold reason; `OPEN_DECISION` from gate_a = None
- `gate_b = {}` → no Gate B hold reason; use PROCEED defaults

- `SYSTEM_DELTA`: summarise steps with status != PASS; if all PASS: "All steps passed."
- `PM_DELTA`: derived from gate_b decision and step count delta vs last baseline record.
  If fewer than 2 baseline records exist: emit `"Insufficient history"` (no delta to compute)
- `OPEN_DECISION`: gate_a HOLD reason if present; else gate_b HOLD reason; else "None"
- `RECOMMENDED_NEXT_STEP`: if HOLD -> "Resolve: {hold_reason}"; if PROCEED -> "Begin next phase"
- `DO_NOT_REDECIDE`: gate decisions already recorded (PROCEED is settled).
  On first run with no prior decisions: empty array `[]` is valid.
  `bridge_contract.schema.json` sets `"minItems": 0` on this field.

`LoopOrchestrator.run_single()` calls `BridgeContractWriter.write()` after
`build_summary_payload()` completes, whether PROCEED or HOLD.

**Precise wiring point**: `build_summary_payload()` is called inside
`_execute_loop_body()` (it is an inner closure/method on `LoopOrchestrator`).
After `_execute_loop_body()` returns `exit_code`, and before `run_single()`
calls `rm.cleanup()` or `rm.revert()`, insert the bridge emit:
```python
exit_code = self._execute_loop_body()
# Bridge and planner artifacts written regardless of PROCEED/HOLD:
bridge_path = BridgeContractWriter(ctx.context_dir, ctx.schema_dir).write(
    trace=_load_json(ctx.context_dir / "loop_run_trace_latest.json"),
    gate_a=_load_json_or_empty(ctx.context_dir / "phase_gate_a_latest.json"),
    gate_b=_load_json_or_empty(ctx.context_dir / "phase_gate_b_latest.json"),
    drift=_load_json_or_empty(ctx.context_dir / "run_drift_latest.json"),
)
# Then rollback/cleanup as before
if exit_code == 1: rm.revert(...); return 5
rm.cleanup(); return exit_code
```
`_load_json_or_empty(path)` returns `{}` if path does not exist.

### Step 3: Tests

`tests/test_bridge_contract.py` — 6 tests:
- `test_bridge_written_on_proceed`
- `test_bridge_written_on_hold`
- `test_bridge_schema_valid`
- `test_system_delta_lists_error_steps`
- `test_open_decision_from_gate_hold`
- `test_do_not_redecide_is_list`

### Files to create
```
src/sop/scripts/bridge_contract_writer.py
scripts/bridge_contract_writer.py    # D-183 copy
src/sop/schemas/bridge_contract.schema.json
docs/context/schemas/bridge_contract.schema.json
tests/test_bridge_contract.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py      # call BridgeContractWriter after summary
scripts/orchestrator.py              # D-183 backport
```

### Done criteria
- [ ] `bridge_contract_current.md` written after every run (PROCEED or HOLD)
- [ ] JSON shadow validated against `bridge_contract.schema.json` at emit
- [ ] 5 required fields present: SYSTEM_DELTA, PM_DELTA, OPEN_DECISION, RECOMMENDED_NEXT_STEP, DO_NOT_REDECIDE
- [ ] `scripts/bridge_contract_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_bridge_contract.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 4.2 — Planner Packet

### Prerequisite: 4.1 complete

### Step 1: Define the planner packet artifact

`docs/context/planner_packet_current.md` — compact fresh-context packet for planner entry.
A fresh worker loading this file gets the full picture without reading the whole repo.

Minimum structure:
```
# Planner Packet
> GeneratedAtUTC: ...
> TraceID: ...
> RunResult: PASS

## Current Context
One paragraph: what the system is, what phase it is in, what the last run achieved.

## Active Brief
The current task or phase goal in one sentence.

## Bridge Truth
Copy of SYSTEM_DELTA + RECOMMENDED_NEXT_STEP from bridge_contract_current.md.

## Decision Tail
Last 3 decisions made (from DO_NOT_REDECIDE list, most recent first).

## Blocked Next Step
The OPEN_DECISION from bridge contract, or "None".

## Active Bottleneck
The highest-priority unresolved blocker. Derived from gate HOLD reasons
and drift alerts. "None" if no active blocker.
```

`planner_packet.schema.json` required fields (JSON shadow):
`schema_version`, `trace_id`, `generated_at_utc`, `run_result`,
`current_context`, `active_brief`, `bridge_truth_summary`,
`decision_tail` (array), `blocked_next_step`, `active_bottleneck`.

### Step 2: PlannerPacketWriter

```python
class PlannerPacketWriter:
    def __init__(self, context_dir: Path, schema_dir: Path) -> None: ...
    def write(
        self,
        trace: dict,            # loop_run_trace_latest.json
        bridge: dict,           # bridge_contract JSON shadow
        gate_a: dict,           # phase_gate_a_latest.json
        gate_b: dict,           # phase_gate_b_latest.json
        prior_packet: dict | None,  # previous planner_packet JSON shadow (for decision tail)
    ) -> Path:
        """Build planner packet from artifacts; write MD + JSON shadow atomically."""
```

Field derivation rules:
- `current_context`: static template filled with `trace.generated_at_utc` + `trace.final_result`
- `active_brief`: `exec_memory_packet_latest.json` schema does not declare `active_brief`
  (schema fields: `phase`, `overall_color`, `token_budget`, `next_round_handoff`).
  Since `additionalProperties: true`, the field may appear at runtime from
  `build_exec_memory_packet.py`. Strategy: attempt `packet.get("active_brief")`;
  if absent or None: fall back to `"Advance to next phase"`. Do not fail.
- `bridge_truth_summary`: SYSTEM_DELTA + RECOMMENDED_NEXT_STEP from bridge JSON shadow
- `decision_tail`: last 3 items from `prior_packet.decision_tail` + new DO_NOT_REDECIDE entries. On first run (`prior_packet=None`) and empty DO_NOT_REDECIDE: `decision_tail = []`. Empty array is valid. `planner_packet.schema.json` sets `"minItems": 0`. Cap: keep last **10** entries in JSON shadow (Markdown renders last 3 for humans; JSON retains 10 for machine use). Prune oldest first.. On first run (`prior_packet=None`) and empty DO_NOT_REDECIDE: `decision_tail = []`. Empty array is valid. `planner_packet.schema.json` sets `"minItems": 0`. Cap: keep last **10** entries in JSON shadow (Markdown renders last 3 for humans; JSON retains 10 for machine use). Prune oldest first..
  On first run (`prior_packet=None`) and empty DO_NOT_REDECIDE: `decision_tail = []`.
  Empty array is valid. `planner_packet.schema.json` sets `"minItems": 0`.
  Cap: keep last **10** entries in JSON shadow (not 3 — the Markdown renders the last 3
  for human readability, but the JSON shadow retains up to 10 for machine use).
  Prune by recency (oldest first out).
- `blocked_next_step`: `bridge.open_decision`
- `active_bottleneck`: first HOLD reason from gate_a or gate_b; else first drift alert; else "None"

`LoopOrchestrator.run_single()` calls `PlannerPacketWriter.write()` after
`BridgeContractWriter.write()` completes.

### Step 3: Tests

`tests/test_planner_packet.py` — 6 tests:
- `test_packet_written_on_every_run`
- `test_packet_schema_valid`
- `test_blocked_next_step_from_gate_hold`
- `test_decision_tail_carries_forward`
- `test_active_bottleneck_from_drift_alert`
- `test_fresh_worker_needs_only_packet` — assertion contract:
  (1) all 6 section keys present in JSON shadow,
  (2) `current_context`, `active_brief`, `bridge_truth_summary` are non-empty strings,
  (3) no field requires reading any file outside `planner_packet_current.md`

### Files to create
```
src/sop/scripts/planner_packet_writer.py
scripts/planner_packet_writer.py     # D-183 copy
src/sop/schemas/planner_packet.schema.json
docs/context/schemas/planner_packet.schema.json
tests/test_planner_packet.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py     # call PlannerPacketWriter after BridgeContractWriter
scripts/orchestrator.py             # D-183 backport
```

### Done criteria
- [ ] `planner_packet_current.md` written after every run
- [ ] JSON shadow validated against `planner_packet.schema.json` at emit
- [ ] 6 required sections: Current Context, Active Brief, Bridge Truth, Decision Tail, Blocked Next Step, Active Bottleneck
- [ ] `decision_tail` carries forward last 3 decisions across runs
- [ ] `scripts/planner_packet_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_planner_packet.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 4.3 — Orchestrator State Surface

### Prerequisite: 4.2 complete

### Step 1: Define the orchestrator state artifact

`docs/context/orchestrator_state_latest.json` — authoritative current state for the
orchestrator. Written after every run. A fresh orchestrator loading this one file
knows the full system state without reading chat history.

```json
{
  "schema_version": "1.0",
  "trace_id": "20260328T120000Z-a3f2",
  "generated_at_utc": "2026-03-28T12:01:00Z",
  "active_system": "quant_current_scope",
  "active_stream": "main",
  "blocked": false,
  "last_changed": "run_loop_cycle completed Phase 2.1 observability",
  "bottleneck": "None",
  "open_pm_decision": "None",
  "evidence_freshness": {
    "loop_run_trace_latest.json": "2026-03-28T12:01:00Z",
    "bridge_contract_current.md": "2026-03-28T12:01:00Z",
    "planner_packet_current.md": "2026-03-28T12:01:00Z"
  }
}
```

`orchestrator_state.schema.json` required fields:
`schema_version`, `trace_id`, `generated_at_utc`, `active_system`, `active_stream`,
`blocked` (bool), `last_changed`, `bottleneck`, `open_pm_decision`, `evidence_freshness` (dict).

### Step 2: OrchestratorStateWriter

```python
class OrchestratorStateWriter:
    def __init__(self, context_dir: Path, schema_dir: Path) -> None: ...
    def write(
        self,
        trace: dict,
        bridge: dict,
        planner_packet: dict,
        prior_state: dict | None,
    ) -> Path:
        """Build state from artifacts; write JSON atomically."""
```

Field derivation rules:
- `active_system`: `trace.repo_id`
- `active_stream`: "main" (Phase 4); multi-stream extension deferred to Phase 5
- `blocked`: `bridge.open_decision != "None"` or `planner_packet.active_bottleneck != "None"`
- `last_changed`: `trace.final_result` + `trace.generated_at_utc`
- `bottleneck`: `planner_packet.active_bottleneck`
- `open_pm_decision`: `bridge.open_decision`
- `evidence_freshness`: mtime (ISO string) of each key artifact in `context_dir`.
  Key artifacts: `loop_run_trace_latest.json`, `bridge_contract_current.md`,
  `planner_packet_current.md`. If an artifact does not exist (e.g. first Phase 4 run
  before bridge/planner writers have run): emit `null` for that key. Handle
  `FileNotFoundError` gracefully in `_get_mtime(path)` helper.

`LoopOrchestrator.run_single()` calls `OrchestratorStateWriter.write()` last
(after planner packet). Prior state loaded from `orchestrator_state_latest.json`
if it exists.

**prior_state threading**: `self._prior_state` is loaded in `__init__()` and
passed explicitly at call time in `run_single()`:
```python
OrchestratorStateWriter(ctx.context_dir, ctx.schema_dir).write(
    trace=trace, bridge=bridge_dict, planner_packet=planner_dict,
    prior_state=self._prior_state,   # loaded in __init__; may be None
)
```
`OrchestratorStateWriter` does not hold a reference to `self._prior_state` —
it receives it as a parameter. This keeps the writer stateless and testable.

### Step 3: Orchestrator self-load on startup

At the start of `LoopOrchestrator.__init__()`, load `orchestrator_state_latest.json`
if present. This gives the orchestrator full context before the first step runs:
```python
self._prior_state = _load_json_if_exists(
    ctx.context_dir / "orchestrator_state_latest.json"
)
```
If `blocked: true` in prior state and `--force` flag not set: log warning to stderr
but continue (do not block execution — the gate system handles blocking).

**Prior state load failure handling** — treat all of the following as `None` (first-run):
- File does not exist (`FileNotFoundError`)
- File is not valid JSON (`json.JSONDecodeError`)
- Parsed dict is missing `schema_version` field
- `schema_version` does not match current writer version
In all cases: log `PRIOR_STATE_LOAD_FAILED: <reason>` to stderr and proceed with `prior_state=None`.

### Step 4: Tests

`tests/test_orchestrator_state.py` — 6 tests:
- `test_state_written_after_every_run`
- `test_state_schema_valid`
- `test_blocked_true_when_open_decision`
- `test_evidence_freshness_contains_key_artifacts`
- `test_orchestrator_loads_prior_state_on_init`
- `test_fresh_worker_reconstructs_situation_from_state`

### Files to create
```
src/sop/scripts/orchestrator_state_writer.py
scripts/orchestrator_state_writer.py   # D-183 copy
src/sop/schemas/orchestrator_state.schema.json
docs/context/schemas/orchestrator_state.schema.json
tests/test_orchestrator_state.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py       # call OrchestratorStateWriter last; load prior state on init
scripts/orchestrator.py               # D-183 backport
```

### Done criteria
- [ ] `orchestrator_state_latest.json` written after every run
- [ ] JSON validated against `orchestrator_state.schema.json` at emit
- [ ] `blocked` correctly reflects open decision or active bottleneck
- [ ] `evidence_freshness` contains mtimes of key artifacts
- [ ] `LoopOrchestrator.__init__()` loads prior state if present
- [ ] `scripts/orchestrator_state_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_orchestrator_state.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bridge field derivation produces noise on first run | Medium | Medium | Suppress PM_DELTA when fewer than 2 baseline records; output "Insufficient history" |
| Decision tail grows stale across many runs | Low | Medium | Cap at 10 entries; prune by recency |
| Planner packet duplicates bridge contract | Medium | Low | Bridge is execution-to-PM translation; packet is planner entry point — different audience |
| OrchestratorStateWriter adds latency | Low | Low | JSON write is atomic and fast; evidence_freshness uses `stat()` only |
| D-183 drift across 3 new modules | Medium | High | test_script_surface_sync.py is hard gate; add all 3 in one PR |
| prior_state loading fails on schema version mismatch | Low | Medium | Treat load failure as None (first-run behavior); log warning |

---

## Cross-cutting Notes

**CC-G1 — rollback_manager.py sync gate (Phase 3 residual)**
Confirmed: `rollback_manager.py` is at line 71 of `PHASE_0_SCRIPTS` in
`test_script_surface_sync.py`. Phase 3 residual is closed.

**CC-G2 — integration marker**: Confirmed already in `pyproject.toml`. Closed — no action needed.




```
Add to `pyproject.toml` as the first task in 4.1 before writing any test file.

**CC-G3 — wiring order in run_single()**
Canonical call order in `run_single()` after `_execute_loop_body()` returns:
1. `BridgeContractWriter.write()` (reads gate + trace artifacts)
2. `PlannerPacketWriter.write()` (reads bridge JSON shadow)
3. `OrchestratorStateWriter.write()` (reads planner packet JSON shadow)
4. `rm.cleanup()` or `rm.revert()` (rollback manager)
5. `return exit_code` (or 5 on rollback)

Steps 1-3 run regardless of PROCEED/HOLD so all artifacts are always fresh.
Step 4 only reverts if exit_code == 1 (HOLD).

---

## Phase 4 to Phase 5 Gate

Phase 5 must not start until all of the following are true:

**Item 4.1 — Bridge Contract**
- [ ] `bridge_contract_current.md` written after every run
- [ ] JSON shadow validates against `bridge_contract.schema.json`
- [ ] All 5 fields present: SYSTEM_DELTA, PM_DELTA, OPEN_DECISION, RECOMMENDED_NEXT_STEP, DO_NOT_REDECIDE
- [ ] `scripts/bridge_contract_writer.py` D-183 copy; sync-gate updated
- [ ] `tests/test_bridge_contract.py` passes (6 tests)

**Item 4.2 — Planner Packet**
- [ ] `planner_packet_current.md` written after every run
- [ ] All 6 sections present; `decision_tail` carries forward across runs
- [ ] Fresh worker test passes: packet alone sufficient to reconstruct situation
- [ ] `scripts/planner_packet_writer.py` D-183 copy; sync-gate updated
- [ ] `tests/test_planner_packet.py` passes (6 tests)

**Item 4.3 — Orchestrator State Surface**
- [ ] `orchestrator_state_latest.json` written after every run
- [ ] `blocked` field reflects reality; `evidence_freshness` populated
- [ ] `LoopOrchestrator.__init__()` loads prior state
- [ ] `scripts/orchestrator_state_writer.py` D-183 copy; sync-gate updated
- [ ] `tests/test_orchestrator_state.py` passes (6 tests)

**Cross-cutting**
- [ ] All 3 new artifacts schema-validated at emit time
- [ ] `pytest tests/test_script_surface_sync.py` passes (3 new D-183 copies)
- [ ] `pytest -m integration` passes
- [ ] All existing tests still pass
- [ ] At least one production run with all 3 artifacts emitted and verified
- [ ] ENDGAME check: planner can enter from packet alone (no whole-repo reread required)

- [ ] All existing tests still pass

---

## Item 4.2 — Planner Packet

### Prerequisite: 4.1 complete

### Step 1: Define the planner packet artifact

`docs/context/planner_packet_current.md` — compact fresh-context packet for planner entry.

Minimum structure:
```
# Planner Packet
> GeneratedAtUTC: ...
> TraceID: ...
> RunResult: PASS

## Current Context
One paragraph: what the system is, what phase, what the last run achieved.

## Active Brief
The current task in one sentence.

## Bridge Truth
SYSTEM_DELTA + RECOMMENDED_NEXT_STEP from bridge_contract_current.md.

## Decision Tail
Last 3 decisions (DO_NOT_REDECIDE, most recent first).

## Blocked Next Step
OPEN_DECISION from bridge contract, or "None".

## Active Bottleneck
Highest-priority unresolved blocker, or "None".
```

`planner_packet.schema.json` required fields:
`schema_version`, `trace_id`, `generated_at_utc`, `run_result`,
`current_context`, `active_brief`, `bridge_truth_summary`,
`decision_tail` (array, minItems: 0), `blocked_next_step`, `active_bottleneck`.

### Step 2: PlannerPacketWriter

```python
class PlannerPacketWriter:
    def __init__(self, context_dir: Path, schema_dir: Path) -> None: ...
    def write(self, trace: dict, bridge: dict, gate_a: dict,
              gate_b: dict, prior_packet: dict | None) -> Path: ...
```

Field derivation rules:
- `current_context`: template filled with `trace.generated_at_utc` + `trace.final_result`
- `active_brief`: attempt `exec_memory_packet_latest.json.get("active_brief")`;
  fall back to `"Advance to next phase"` if absent or None
- `bridge_truth_summary`: SYSTEM_DELTA + RECOMMENDED_NEXT_STEP from bridge JSON shadow
- `decision_tail`: last 3 from `prior_packet.decision_tail` + new DO_NOT_REDECIDE entries.
  On first run (`prior_packet=None`) and empty DO_NOT_REDECIDE: `decision_tail = []`.
  Cap at **10** in JSON shadow (Markdown renders last 3). Prune oldest first.
- `blocked_next_step`: `bridge.open_decision`
- `active_bottleneck`: first HOLD reason from gate_a/gate_b; else first drift alert; else "None"

### Step 3: Tests

`tests/test_planner_packet.py` — 6 tests:
- `test_packet_written_on_every_run`
- `test_packet_schema_valid`
- `test_blocked_next_step_from_gate_hold`
- `test_decision_tail_carries_forward`
- `test_active_bottleneck_from_drift_alert`
- `test_fresh_worker_needs_only_packet` — assertion contract:
  (1) all 6 section keys present in JSON shadow,
  (2) `current_context`, `active_brief`, `bridge_truth_summary` non-empty strings,
  (3) no field requires reading any file outside `planner_packet_current.md`

### Files to create
```
src/sop/scripts/planner_packet_writer.py
scripts/planner_packet_writer.py     # D-183 copy
src/sop/schemas/planner_packet.schema.json
docs/context/schemas/planner_packet.schema.json
tests/test_planner_packet.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py     # call PlannerPacketWriter after BridgeContractWriter
scripts/orchestrator.py             # D-183 backport
```

### Done criteria
- [ ] `planner_packet_current.md` written after every run
- [ ] JSON shadow validated against `planner_packet.schema.json`
- [ ] 6 required sections present; empty `decision_tail` valid on first run
- [ ] `decision_tail` capped at 10 in JSON shadow; Markdown renders last 3
- [ ] `scripts/planner_packet_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_planner_packet.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 4.3 — Orchestrator State Surface

### Prerequisite: 4.2 complete

### Step 1: Define the orchestrator state artifact

`docs/context/orchestrator_state_latest.json`:
```json
{
  "schema_version": "1.0", "trace_id": "...", "generated_at_utc": "...",
  "active_system": "quant_current_scope", "active_stream": "main",
  "blocked": false, "last_changed": "PROCEED 2026-03-28T12:00:00Z",
  "bottleneck": "None", "open_pm_decision": "None",
  "evidence_freshness": {
    "loop_run_trace_latest.json": "2026-03-28T12:01:00Z",
    "bridge_contract_current.md": null,
    "planner_packet_current.md": null
  }
}
```

`orchestrator_state.schema.json` required fields:
`schema_version`, `trace_id`, `generated_at_utc`, `active_system`, `active_stream`,
`blocked` (bool), `last_changed`, `bottleneck`, `open_pm_decision`,
`evidence_freshness` (object, values: string or null).

### Step 2: OrchestratorStateWriter

```python
class OrchestratorStateWriter:
    def __init__(self, context_dir: Path, schema_dir: Path) -> None: ...
    def write(self, trace: dict, bridge: dict, planner_packet: dict,
              prior_state: dict | None) -> Path: ...
```

Field derivation:
- `active_system`: `trace["repo_id"]` (confirmed on `LoopCycleContext` line 36)
- `active_stream`: `"main"` (Phase 4; multi-stream deferred to Phase 5)
- `blocked`: `bridge["open_decision"] != "None"` or `planner_packet["active_bottleneck"] != "None"`
- `last_changed`: `trace["final_result"]` + `trace["generated_at_utc"]`
- `bottleneck`: `planner_packet["active_bottleneck"]`
- `open_pm_decision`: `bridge["open_decision"]`
- `evidence_freshness`: mtime (ISO string) of each key artifact.
  If artifact missing (e.g. first Phase 4 run): emit `null`. Handle `FileNotFoundError`
  in `_get_mtime(path)` helper.

### Step 3: Orchestrator self-load + --force flag

```python
# In LoopOrchestrator.__init__():
self._prior_state = _load_orchestrator_state(ctx.context_dir)
```

`_load_orchestrator_state()` returns `None` for ALL of:
- File missing (`FileNotFoundError`)
- Invalid JSON (`json.JSONDecodeError`)
- Missing `schema_version` field
- `schema_version` mismatch

Log `PRIOR_STATE_LOAD_FAILED: <reason>` to stderr in all cases.

If `blocked: true` and `--force` not set: log warning but continue.

`--force` must be added to: `parse_args()` in `run_loop_cycle.py`,
`LoopCycleContext` dataclass, and `cmd_run()` in `src/sop/__main__.py`.

**prior_state threading** — writer is stateless; prior_state passed explicitly:
```python
OrchestratorStateWriter(ctx.context_dir, ctx.schema_dir).write(
    trace=trace, bridge=bridge_dict, planner_packet=planner_dict,
    prior_state=self._prior_state,
)
```

### Step 4: Tests

`tests/test_orchestrator_state.py` — 6 tests:
- `test_state_written_after_every_run`
- `test_state_schema_valid`
- `test_blocked_true_when_open_decision`
- `test_evidence_freshness_null_for_missing_artifacts`
- `test_orchestrator_loads_prior_state_on_init`
- `test_prior_state_load_failure_returns_none`

### Files to create
```
src/sop/scripts/orchestrator_state_writer.py
scripts/orchestrator_state_writer.py   # D-183 copy
src/sop/schemas/orchestrator_state.schema.json
docs/context/schemas/orchestrator_state.schema.json
tests/test_orchestrator_state.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py        # OrchestratorStateWriter + prior_state load
src/sop/scripts/run_loop_cycle.py      # add --force to parse_args()
src/sop/scripts/loop_cycle_context.py  # add force: bool field
src/sop/__main__.py                    # pass --force through subprocess
scripts/orchestrator.py + scripts/run_loop_cycle.py  # D-183 backports
```

### Done criteria
- [ ] `orchestrator_state_latest.json` written after every run; schema-valid
- [ ] `blocked` reflects open decision or active bottleneck
- [ ] `evidence_freshness` emits `null` for missing artifacts
- [ ] Prior state load failure returns `None` for all 4 error conditions
- [ ] `LoopOrchestrator.__init__()` loads prior state
- [ ] `--force` added to `run_loop_cycle.py`, `LoopCycleContext`, `__main__.py`
- [ ] `scripts/orchestrator_state_writer.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_orchestrator_state.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Cross-cutting Notes

**CC-G1**: `rollback_manager.py` confirmed at line 71 of `PHASE_0_SCRIPTS`. Closed.

**CC-G2**: `integration` marker confirmed already in `pyproject.toml`. Closed — no action needed.




**CC-G3 — wiring order in run_single()**:
1. `BridgeContractWriter.write()` (reads gate + trace from disk)
2. `PlannerPacketWriter.write()` (reads bridge JSON shadow)
3. `OrchestratorStateWriter.write()` (reads planner packet; receives `self._prior_state`)
4. `rm.cleanup()` or `rm.revert()`
5. `return exit_code` (or 5 on rollback)

Revised canonical call order in `run_single()` (4.3-G6 resolved as Option A):
1. `exit_code = self._execute_loop_body()`
2. `if exit_code == 1: rm.revert(...); else: rm.cleanup()`
3. `BridgeContractWriter.write(...)` (OUTSIDE rollback scope -- never reverted)
4. `PlannerPacketWriter.write(...)` (OUTSIDE rollback scope -- never reverted)
5. `OrchestratorStateWriter.write(...)` (OUTSIDE rollback scope -- never reverted)
6. `return 5 if reverted else exit_code`

Rationale: bridge/planner/state are translation artifacts (Loop B to Loop A),
not execution artifacts. They must survive a HOLD to communicate the HOLD reason.
Steps 1-3 run on both PROCEED and HOLD. Writers in steps 3-5 always write.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| PM_DELTA noise on first run | Medium | Medium | Emit "Insufficient history" when <2 baseline records |
| decision_tail grows stale | Low | Medium | Cap at 10; prune by recency |
| evidence_freshness null on first Phase 4 run | High | Low | null is valid per schema; handled in _get_mtime() |
| prior_state schema version mismatch | Low | Medium | Return None + log; proceed as first run |
| --force not threaded through __main__.py | Medium | Medium | Files-to-modify list includes __main__.py |
| D-183 drift across 3 new modules | Medium | High | test_script_surface_sync.py is hard gate |

---

## Phase 4 to Phase 5 Gate

Phase 5 must not start until all of the following are true:

**Item 4.1 — Bridge Contract**
- [ ] `bridge_contract_current.md` written on every run; JSON shadow schema-valid
- [ ] All 5 fields: SYSTEM_DELTA, PM_DELTA, OPEN_DECISION, RECOMMENDED_NEXT_STEP, DO_NOT_REDECIDE
- [ ] Gate-absent edge case handled (empty dict = PROCEED defaults)
- [ ] PM_DELTA suppressed with "Insufficient history" when <2 baseline records
- [ ] DO_NOT_REDECIDE empty array valid on first run
- [ ] `scripts/bridge_contract_writer.py` D-183 copy; sync-gate updated
- [ ] `tests/test_bridge_contract.py` passes (6 tests)

**Item 4.2 — Planner Packet**
- [ ] `planner_packet_current.md` written on every run; JSON shadow schema-valid
- [ ] All 6 sections present; empty decision_tail valid; cap at 10 in JSON shadow
- [ ] `active_brief` falls back gracefully when not in exec_memory schema
- [ ] Fresh worker test passes (3-part assertion contract)
- [ ] `scripts/planner_packet_writer.py` D-183 copy; sync-gate updated
- [ ] `tests/test_planner_packet.py` passes (6 tests)

**Item 4.3 — Orchestrator State Surface**
- [ ] `orchestrator_state_latest.json` written on every run; schema-valid
- [ ] `blocked` correct; `evidence_freshness` null for missing artifacts
- [ ] Prior state load failure returns None for all 4 error conditions
- [ ] `--force` flag added to run_loop_cycle.py + LoopCycleContext + __main__.py
- [ ] `scripts/orchestrator_state_writer.py` D-183 copy; sync-gate updated
- [ ] `tests/test_orchestrator_state.py` passes (6 tests)

**Cross-cutting**
- [ ] `integration` marker registered in `pyproject.toml` before any integration tests written
- [ ] CC-G3 wiring order implemented: bridge → planner → state → rollback
- [ ] `pytest tests/test_script_surface_sync.py` passes (3 new D-183 copies)
- [ ] `pytest -m integration` passes
- [ ] All existing tests still pass
- [ ] ENDGAME check: planner enters from `planner_packet_current.md` alone
