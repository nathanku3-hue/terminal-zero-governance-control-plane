# Phase 5 — Memory Discipline & Compaction Lifecycle

> **Status**: Draft — awaiting Phase 4 completion
> **Effort estimate**: 4–7 weeks total, three sequential workstreams
> **Repo**: `E:\Code\SOP\quant_current_scope`
> **Prerequisite**: Phase 4 gate fully checked
> **Gate**: All three items complete before Phase 6 begins

---

## Context: What Phase 4 established

- `bridge_contract_current.md` — translates execution truth into planner language every run
- `planner_packet_current.md` — compact fresh-context packet; planner enters from it alone
- `orchestrator_state_latest.json` — orchestrator self-loads state on startup from disk
- Three new D-183 writer modules in `PHASE_0_SCRIPTS`
- `--force` flag on `run_loop_cycle.py` and `LoopCycleContext`
- Wiring order: `_execute_loop_body` → rollback → bridge → planner → state

Phase 5 addresses the remaining gap between "artifacts exist" and "artifacts stay lean".
Without memory discipline, every phase adds more surfaces, contexts grow, and the
planner starts rereading more. Phase 5 makes compaction deterministic and artifact
lifetime explicit so the system becomes lighter as it runs, not heavier.

---

## ENDGAME alignment

From ENDGAME.md Section 12 (Optimization Direction):
- make the orchestrator more state-aware through better artifacts, not more prompt text
- reduce human effort to the smallest set of decisions that preserve product truth

From ENDGAME.md Section 13 (Futureproofing):
- fewer prompts, fewer reminders, fewer manual restatements
- more reliance on clear artifacts and mechanical checks
- thinner but clearer artifacts

Phase 5 delivers the mechanical underpinning for both:
1. A formal memory tier contract (hot/warm/cold) so artifacts load only when needed
2. Deterministic compaction with retention rules that survive HOLD and restart
3. Artifact pruning so the `docs/context/` directory stays bounded

---

## Current State (as-inspected at Phase 4 completion)

| Area | What exists after Phase 4 | What is missing |
|---|---|---|
| Memory tiers | No formal tier model | No hot/warm/cold classification; all artifacts treated equally |
| Compaction | `evaluate_context_compaction_trigger.py` exists | No deterministic retention rules; no tier-aware compaction |
| Artifact lifetime | Artifacts written indefinitely | No pruning; `docs/context/` grows unbounded |
| Context budget | `benchmark/subagent_routing_matrix.yaml` tracks budgets | No enforcement; over-budget deputies not blocked |
| Planner entry | `planner_packet_current.md` provides compact entry | Packet not yet enforced as sole entry point; planners may still reread repo |
| Archive policy | No archive tier | Stale artifacts accumulate; no retirement path |

---

## Sequencing Rule

```
5.1 Memory Tier Contract  -->  5.2 Compaction Hardening  -->  5.3 Artifact Pruning & Lifecycle
```

Each item is a strict prerequisite for the next. No parallelism across items.

---

## Worker Guidance

**Plan path**: `E:\Code\SOP\quant_current_scope\docs\PHASE_5_PLAN.md`

Approved -- conditional on Phase 4 gate. All gaps resolved including 5.1-G5 scope correction. No remaining blockers.

### Key file locations (inherited from Phase 4)

| File | Note |
|---|---|
| `src/sop/scripts/orchestrator.py` | Add tier-aware artifact loading in 5.1 |
| `src/sop/scripts/utils/compaction_retention.py` | Extend `_compact_ndjson_rolling()`; add tier-aware compaction |
| `scripts/evaluate_context_compaction_trigger.py` | Compaction trigger logic |
| `scripts/build_exec_memory_packet.py` | Exec memory packet builder |
| `benchmark/subagent_routing_matrix.yaml` | Deputy context budgets |
| `docs/context/` | All live artifacts — 5.3 prunes this dir |

---

### Implementation notes

- `_MEMORY_TIER_FAMILIES` currently has 18 pre-Phase-2 families. Phase 5 adds all 14 missing Phase 2-4 families (hot + warm + cold).
- `MEMORY_TIER_CONTRACT_DOC_PATH` in `memory_tiers.py` must be updated from `docs/memory_tier_contract.md` to `docs/context/MEMORY_TIER_CONTRACT.md`.
- `TierAwareCompactor` imports `_MEMORY_TIER_FAMILIES` directly -- does not parse the MD file at runtime.
- Compactor receives `blocked` as constructor arg from current run exit_code -- not from stale on-disk state.
- Warm compaction is a No-op in Phase 5 (in-place overwrite pattern; no accumulation).
- Phase 4 residual: bridge_contract_writer.py, planner_packet_writer.py, orchestrator_state_writer.py must be in PHASE_0_SCRIPTS before Phase 5 sync-gate can pass.

### 14 families to add to _MEMORY_TIER_FAMILIES

| Family key | Representative artifact | Tier |
|---|---|---|
| `loop_run_trace` | `loop_run_trace_latest.json` | hot |
| `loop_cycle_checkpoint` | `loop_cycle_checkpoint_latest.json` | hot |
| `orchestrator_state` | `orchestrator_state_latest.json` | hot |
| `phase_gate_a` | `phase_gate_a_latest.json` | warm |
| `phase_gate_b` | `phase_gate_b_latest.json` | warm |
| `phase_handoff` | `phase_handoff_latest.json` | warm |
| `run_drift` | `run_drift_latest.json` | warm |
| `rollback` | `rollback_latest.json` | warm |
| `bridge_contract` | `bridge_contract_current.md` + `.json` | warm |
| `planner_packet` | `planner_packet_current.md` + `.json` | warm |
| `loop_run_steps` | `loop_run_steps_latest.ndjson` | cold |
| `run_regression_baseline` | `run_regression_baseline.ndjson` | cold |
| `worker_merge` | `worker_merge_latest.json` | cold |
| `loop_run_trace_master` | `loop_run_trace_master_latest.json` | cold |

### Implementation checklist

**5.1 Memory Tier Contract**
- [ ] Add all 14 families to `_MEMORY_TIER_FAMILIES` in `memory_tiers.py`
- [ ] Update `MEMORY_TIER_CONTRACT_DOC_PATH` to `docs/context/MEMORY_TIER_CONTRACT.md`
- [ ] Create `docs/context/MEMORY_TIER_CONTRACT.md` classifying all live artifacts
- [ ] `evidence_tier` map added to `orchestrator_state.schema.json` (optional field)
- [ ] `tests/test_memory_tier.py` passes (6 tests); `test_tier_assignment_is_exhaustive` uses static list

**5.2 Compaction Hardening**
- [ ] `compaction_report.schema.json` created in `src/sop/schemas/`
- [ ] `TierAwareCompactor` with `run() -> CompactionReport`; imports `_MEMORY_TIER_FAMILIES`
- [ ] Hot artifacts never compacted; warm No-op; cold NDJSON rolling windows enforced
- [ ] Compactor receives `blocked` as constructor arg (not from stale disk file)
- [ ] Both `src/sop/scripts/evaluate_context_compaction_trigger.py` and `scripts/` copy modified
- [ ] `scripts/tier_aware_compactor.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_compaction_hardening.py` passes (6 tests)

**5.3 Artifact Pruning and Lifecycle**
- [ ] `ArtifactLifecycleManager.scan()` uses `_MEMORY_TIER_FAMILIES` as orphan registry
- [ ] `archive_superseded(dry_run=True)` default; `--prune` required for actual moves
- [ ] `--max-context-artifacts` counts total file count in `docs/context/` (all files)
- [ ] `--prune` and `--max-context-artifacts` forwarded in `cmd_run()` subprocess call
- [ ] `docs/context/archive/` added to `.gitignore` (trailing slash; no conflicting blanket rule)
- [ ] `prune: bool` and `max_context_artifacts: int` added to `LoopCycleContext`
- [ ] `scripts/artifact_lifecycle_manager.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_artifact_lifecycle.py` passes (6 tests)

**Cross-cutting**
- [ ] Phase 4 residual: bridge/planner/state writers added to `PHASE_0_SCRIPTS`
- [ ] `pytest tests/test_script_surface_sync.py` passes
- [ ] `pytest -m integration` passes
- [ ] All existing tests still pass
- [ ] `docs/context/` artifact count bounded after 3 consecutive runs

### Success criteria

Phase 5 is successful when:
- All 14 Phase 2-4 families are in `_MEMORY_TIER_FAMILIES`; `test_tier_assignment_is_exhaustive` passes
- `TierAwareCompactor` runs after every run; hot artifacts never compacted; cold NDJSON windows enforced
- `ArtifactLifecycleManager.scan()` classifies all `docs/context/` artifacts correctly
- `docs/context/` artifact count does not grow unboundedly across 3 consecutive runs
- All 18 new tests pass (6 per workstream); all existing tests still pass
- ENDGAME: system is measurably lighter after Phase 5 -- compaction runs deterministically,
  planner packet remains the sole fresh entry point, context stays bounded


## Item 5.1 — Memory Tier Contract

### Prerequisite: Phase 4 gate fully checked

### Step 1: Define the three-tier model

All artifacts in `docs/context/` are classified into exactly one of three tiers:

| Tier | Description | Load policy | Examples |
|---|---|---|---|
| **hot** | Current loop execution state and active blockers | Loaded on every run | `exec_memory_packet_latest.json`, `loop_cycle_checkpoint_latest.json`, `orchestrator_state_latest.json` |
| **warm** | Latest validated governance artifacts and handoffs | Loaded when referenced by planner or bridge | `bridge_contract_current.md`, `planner_packet_current.md`, `phase_gate_a/b_latest.json`, `rollback_latest.json` |
| **cold** | Historical/archived context | Loaded only on explicit demand | NDJSON rolling logs, `run_regression_baseline.ndjson`, old phase gate artifacts |

### Step 2: Memory tier contract document

**5.1-G1 resolved**: `docs/memory_tier_contract.md` (existing) covers only
the two legacy scripts. The new Phase 5 file must be
`docs/context/MEMORY_TIER_CONTRACT.md` — a separate file that classifies
all Phase 2-4 live artifacts. Do not rename or modify the existing file.

Create `docs/context/MEMORY_TIER_CONTRACT.md`:
```markdown
# Memory Tier Contract
> Version: 1.0
> Updated: ...

## Hot Tier (loaded every run)
- exec_memory_packet_latest.json
- loop_cycle_checkpoint_latest.json
- orchestrator_state_latest.json
- loop_run_trace_latest.json

## Warm Tier (loaded when referenced)
- bridge_contract_current.md + .json
- planner_packet_current.md + .json
- phase_gate_a_latest.json
- phase_gate_b_latest.json
- rollback_latest.json
- run_drift_latest.json

## Cold Tier (load on explicit demand only)
- loop_run_steps_*.ndjson
- run_regression_baseline.ndjson
- worker_merge_latest.json
- loop_run_trace_master_latest.json

## Tier assignment rules
1. An artifact is hot if the orchestrator needs it before the first step runs.
2. An artifact is warm if the planner or bridge needs it but workers do not.
3. Everything else is cold.
```

**5.1-G2 resolved**: `memory_tiers.py` already has `_MEMORY_TIER_FAMILIES`
dict with hot/warm classifications. `TierAwareCompactor` must import
`_MEMORY_TIER_FAMILIES` from `src/sop/scripts/utils/memory_tiers.py` directly
(code wins on drift, per existing doc). Do NOT parse `MEMORY_TIER_CONTRACT.md`
at runtime. **Phase 5 adds all 14 missing Phase 2-4 families (hot + warm + cold) to
`_MEMORY_TIER_FAMILIES`**, not cold-tier only. Also updates `MEMORY_TIER_CONTRACT_DOC_PATH`
constant in `memory_tiers.py` from `docs/memory_tier_contract.md` to `docs/context/MEMORY_TIER_CONTRACT.md`.
### Step 3: Tier enforcement in OrchestratorStateWriter

Add `evidence_tier` map to `orchestrator_state_latest.json`:
```json
{
  "evidence_freshness": {"loop_run_trace_latest.json": "2026-03-28T12:01:00Z"},
  "evidence_tier": {
    "loop_run_trace_latest.json": "hot",
    "bridge_contract_current.md": "warm",
    "run_regression_baseline.ndjson": "cold"
  }
}
```

`orchestrator_state.schema.json` updated: add optional `evidence_tier` object.
Existing schema version still valid (no required field added).

### Step 4: Tests

`tests/test_memory_tier.py` — 6 tests:
- `test_tier_contract_file_exists`
- `test_all_hot_artifacts_classified`
- `test_all_warm_artifacts_classified`
- `test_tier_assignment_is_exhaustive` — validates against a static known-artifact
  list defined in code (not by scanning runtime `docs/context/`). The test
  asserts every name in the static list appears in `_MEMORY_TIER_FAMILIES`.
  This avoids environment-dependency on the runtime-generated directory.
- `test_evidence_tier_in_orchestrator_state`
- `test_hot_artifacts_have_freshness_entry`

**5.1-G4 — Phase 4 residual (must close before Phase 5 sync-gate passes)**:
`bridge_contract_writer.py`, `planner_packet_writer.py`,
`orchestrator_state_writer.py` are not yet in `PHASE_0_SCRIPTS`.
These must be added to `test_script_surface_sync.py` as part of Phase 4
closure before `pytest tests/test_script_surface_sync.py` can pass in Phase 5.

### Files to create
```
docs/context/MEMORY_TIER_CONTRACT.md
tests/test_memory_tier.py
```

### Files to modify
```
src/sop/scripts/orchestrator_state_writer.py  # add evidence_tier field
src/sop/schemas/orchestrator_state.schema.json # add optional evidence_tier
scripts/orchestrator_state_writer.py           # D-183 backport
```

### Done criteria
- [ ] `MEMORY_TIER_CONTRACT.md` exists with hot/warm/cold classification for all live artifacts
- [ ] Every artifact in `docs/context/` assigned to exactly one tier
- [ ] `evidence_tier` map in `orchestrator_state_latest.json`
- [ ] `tests/test_memory_tier.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 5.2 — Compaction Hardening

### Prerequisite: 5.1 complete

### Step 1: Deterministic retention rules

Compaction must be tier-aware. Rules applied in this order:

| Condition | Rule |
|---|---|
| Artifact is **hot** | Never compacted; always retained in full |
| Artifact is **warm** | No-op in Phase 5 — warm artifacts are in-place overwritten
  each run (bridge_contract_current.md, planner_packet_current.md, phase_gate_a/b_latest.json).
  No accumulation occurs; no compaction needed. Warm versioning deferred to Phase 6. |
| Artifact is **cold** NDJSON | Rolling window: keep last N records (configurable; default per artifact) |
| Artifact is **cold** non-NDJSON | Retained until explicit archive trigger (see 5.3) |

Default rolling windows:
- `run_regression_baseline.ndjson`: 100 records (Phase 3.2)
- `loop_run_steps_*.ndjson`: 500 records (Phase 2.1)
- Any new cold NDJSON: 200 records unless overridden

### Step 2: CompactionPolicy class

```python
@dataclass
class CompactionPolicy:
    artifact_path: str          # relative to context_dir
    tier: str                   # hot / warm / cold
    max_records: int | None     # None = no rolling limit
    superseded_by: str | None   # path of newer artifact that retires this one

class TierAwareCompactor:
    def __init__(self, context_dir: Path, tier_contract: dict) -> None: ...
    def run(self) -> CompactionReport: ...
    """Apply retention rules to all artifacts per tier contract."""
```

`CompactionReport` fields: `compacted` (list of paths), `retained` (list),
`skipped_hot` (list), `errors` (list).

`LoopOrchestrator` calls `TierAwareCompactor(ctx.context_dir, tier_contract).run()`
at the end of `run_single()` (after all writers; last operation before return).

### Step 3: Compaction safety rules

Allow compaction only at:
- End of a completed run (`partial: false` in checkpoint)
- After all three writers (bridge/planner/state) have written

Never compact during:
- Active `run_single()` execution (before writers complete)
- When this run is a HOLD (exit_code == 1 before rollback)

**5.2-G3 resolved**: `TierAwareCompactor` does NOT read `blocked` from
`orchestrator_state_latest.json` on disk (that file reflects the prior run).
Instead, `LoopOrchestrator.run_single()` passes `blocked: bool` directly as a
constructor argument, derived from the current run exit_code:
```python
TierAwareCompactor(ctx.context_dir, tier_contract, blocked=(exit_code==1)).run()
```
This avoids stale-state dependency and makes the compactor testable.

### Step 4: Compaction trigger integration

`evaluate_context_compaction_trigger.py` already exists. Extend to read
`MEMORY_TIER_CONTRACT.md` and pass tier assignments to `TierAwareCompactor`.
Do not change the trigger evaluation logic — only add tier-awareness to the
compaction execution path.

### Step 5: Tests

`tests/test_compaction_hardening.py` — 6 tests:
- `test_hot_artifacts_never_compacted`
- `test_warm_artifact_superseded_by_newer`
- `test_cold_ndjson_rolling_window_applied`
- `test_compaction_only_after_writers_complete`
- `test_compaction_skipped_when_blocked`
- `test_compaction_report_schema_valid` — requires `compaction_report.schema.json`
  (confirmed not yet present in `src/sop/schemas/`; must be created in 5.2)

### Files to create
```
src/sop/scripts/tier_aware_compactor.py
scripts/tier_aware_compactor.py          # D-183 copy
src/sop/schemas/compaction_report.schema.json
docs/context/schemas/compaction_report.schema.json
tests/test_compaction_hardening.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py                    # call TierAwareCompactor at end of run_single()
src/sop/scripts/evaluate_context_compaction_trigger.py  # canonical (D-183 source)
scripts/evaluate_context_compaction_trigger.py           # D-183 copy (already in PHASE_0_SCRIPTS)
  # Note: both surfaces must be modified together; sync-gate will catch drift
scripts/orchestrator.py                            # D-183 backport
# Note: scripts/tier_aware_compactor.py is in files-to-create above (D-183 copy)
```

### Done criteria
- [ ] `TierAwareCompactor` with `run() -> CompactionReport` exists
- [ ] Hot artifacts never compacted
- [ ] Warm artifacts retained until superseded
- [ ] Cold NDJSON rolling windows enforced
- [ ] Compaction only runs after all writers complete
- [ ] Compaction skipped when `blocked: true` (without `--force`)
- [ ] `scripts/tier_aware_compactor.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_compaction_hardening.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 5.3 — Artifact Pruning & Lifecycle

### Prerequisite: 5.2 complete

### Step 1: Artifact lifecycle states

Every artifact in `docs/context/` has exactly one lifecycle state:

| State | Meaning | Action |
|---|---|---|
| `active` | Currently written and read by the system | No action |
| `superseded` | A newer version replaces it; still on disk | Move to `docs/context/archive/` |
| `orphaned` | Written by a removed or disabled code path | Delete or archive |
| `fixture` | Committed stub in `docs/context/` (e.g. a schema stub or committed
  example file). In Phase 5 this state is vacuous — all Phase 2-4 artifacts are
  runtime-generated and live in `tests/fixtures/` not `docs/context/`. Reserved
  for future phases. | Keep; no action |

### Step 2: ArtifactLifecycleManager

```python
**5.3-G1 resolved**: Orphan detection uses `_MEMORY_TIER_FAMILIES` from
`memory_tiers.py` as the canonical registry of known active artifact paths.
Any file in `docs/context/` whose name does not appear in any family's
`artifact_paths` tuple is classified as orphaned. No separate allowlist needed.
`scan()` cross-references `os.listdir(context_dir)` against the union of
all `artifact_paths` in `_MEMORY_TIER_FAMILIES`.

**5.3-G1 resolved**: Orphan detection uses `_MEMORY_TIER_FAMILIES` from `memory_tiers.py`
as the canonical registry. Any file in `docs/context/` whose name does not appear in any
family's `artifact_paths` tuple is classified as orphaned. `scan()` cross-references
`os.listdir(context_dir)` against the union of all `artifact_paths` in `_MEMORY_TIER_FAMILIES`.

class ArtifactLifecycleManager:
    def __init__(self, context_dir: Path, tier_contract: dict) -> None: ...
    def scan(self) -> LifecycleScanResult: ...
    """Classify all artifacts in context_dir by lifecycle state."""
    def archive_superseded(self, dry_run: bool = True) -> ArchiveResult: ...
    """Move superseded artifacts to docs/context/archive/. Default dry_run=True."""
```

`LifecycleScanResult` fields: `active` (list), `superseded` (list), `orphaned` (list),
`fixture` (list), `unclassified` (list).

`archive_superseded(dry_run=True)` default prevents accidental deletion.
Requires `--prune` CLI flag to execute (dry_run=False).

### Step 3: docs/context/ size bound

Add `--max-context-artifacts N` (default: 50) to `run_loop_cycle.py`.
After `TierAwareCompactor` runs, if total file count in `docs/context/`
(all files, not just active list) exceeds N:
- Log `CONTEXT_OVERFLOW: {count} artifacts > {N} limit` to stderr
- Do not block execution — warning only in Phase 5
  (blocking enforcement deferred to Phase 6)

### Step 4: `--prune` CLI flag

Add `--prune` to `run_loop_cycle.py`, `LoopCycleContext`, `src/sop/__main__.py`.
When set: runs `archive_superseded(dry_run=False)` after compaction.
Without `--prune`: lifecycle scan runs but archive step is dry-run only.

**5.3-G4 -- --prune forwarding**: cmd_run() in __main__.py calls _run_script() via subprocess. Add explicit forwarding: if ctx.prune: cli_args.append('--prune') and if ctx.max_context_artifacts != 50: cli_args.extend(['--max-context-artifacts', str(ctx.max_context_artifacts)])

**5.3-G4 -- --prune forwarding**: `cmd_run()` in `__main__.py` calls
`_run_script("run_loop_cycle.py", cli_args)` via subprocess. Add explicit forwarding:
```python
if ctx.prune:
    cli_args.append("--prune")
if ctx.max_context_artifacts != 50:  # non-default
    cli_args.extend(["--max-context-artifacts", str(ctx.max_context_artifacts)])
```

**5.3-G4 — --prune forwarding**: `cmd_run()` in `__main__.py` calls
`_run_script("run_loop_cycle.py", cli_args)` via subprocess. Add explicit
forwarding:
```python
if ctx.prune:
    cli_args.append("--prune")
if ctx.max_context_artifacts != 50:  # non-default
    cli_args.extend(["--max-context-artifacts", str(ctx.max_context_artifacts)])
```

Add `docs/context/archive/` to `.gitignore` (not committed; local cleanup only). **5.3-G5**: Verify .gitignore has no conflicting docs/context/** blanket rule. Use narrowest pattern: docs/context/archive/ (trailing slash = directory only).
**5.3-G5**: Check `.gitignore` for existing `docs/context/**` blanket rules before adding.
Use narrowest pattern: `docs/context/archive/` (trailing slash = directory only).
**5.3-G5**: Verify `.gitignore` does not already have a conflicting `docs/context/**`
blanket rule before adding the archive entry. Add the narrowest possible pattern:
`docs/context/archive/` (trailing slash ensures only the directory is ignored,
not a hypothetical file named `archive`).

### Step 5: Tests

`tests/test_artifact_lifecycle.py` — 6 tests:
- `test_scan_classifies_all_artifacts`
- `test_superseded_artifact_identified`
- `test_archive_superseded_dry_run_no_files_moved`
- `test_archive_superseded_moves_files_with_prune_flag`
- `test_context_overflow_warning_logged`
- `test_orphaned_artifact_reported`

### Files to create
```
src/sop/scripts/artifact_lifecycle_manager.py
scripts/artifact_lifecycle_manager.py    # D-183 copy
tests/test_artifact_lifecycle.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py          # call ArtifactLifecycleManager after compaction
src/sop/scripts/run_loop_cycle.py        # --prune; --max-context-artifacts flags
src/sop/scripts/loop_cycle_context.py   # add prune: bool; max_context_artifacts: int
src/sop/__main__.py                      # pass --prune through subprocess
.gitignore                               # add docs/context/archive/
scripts/orchestrator.py + scripts/run_loop_cycle.py  # D-183 backports
```

### Done criteria
- [ ] `ArtifactLifecycleManager.scan()` classifies all `docs/context/` artifacts
- [ ] `archive_superseded(dry_run=True)` default; `--prune` required for actual move
- [ ] `--max-context-artifacts` warning logged when exceeded
- [ ] `docs/context/archive/` in `.gitignore`
- [ ] `scripts/artifact_lifecycle_manager.py` D-183 copy; added to `PHASE_0_SCRIPTS`
- [ ] `tests/test_artifact_lifecycle.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|
| Tier classification misses a new Phase 4 artifact | Medium | Medium | `test_tier_assignment_is_exhaustive` catches unclassified artifacts |
| Compaction deletes artifact still needed by warm reader | Low | High | Hot artifacts never compacted; warm retained until superseded |
| `archive_superseded` moves files a test expects | Medium | Medium | Default `dry_run=True`; `--prune` required for actual moves |
| `docs/context/archive/` committed accidentally | Low | Low | `.gitignore` entry in 5.3 |
| TierAwareCompactor adds latency at end of run | Low | Low | Runs after all writers; last operation; non-blocking on error |
| D-183 drift across 2 new modules | Medium | High | `test_script_surface_sync.py` is hard gate |

---

## Phase 5 to Phase 6 Gate

Phase 6 must not start until all of the following are true:

**Item 5.1 — Memory Tier Contract**
- [ ] `MEMORY_TIER_CONTRACT.md` exists with hot/warm/cold for all live artifacts
- [ ] Every `docs/context/` artifact assigned to exactly one tier
- [ ] `evidence_tier` map in `orchestrator_state_latest.json`
- [ ] `tests/test_memory_tier.py` passes (6 tests)

**Item 5.2 — Compaction Hardening**
- [ ] `TierAwareCompactor` exists; hot artifacts never compacted
- [ ] Cold NDJSON rolling windows enforced
- [ ] Compaction only runs after writers complete; skipped when blocked
- [ ] `scripts/tier_aware_compactor.py` D-183 copy; sync-gate updated
- [ ] `tests/test_compaction_hardening.py` passes (6 tests)

**Item 5.3 — Artifact Pruning & Lifecycle**
- [ ] `ArtifactLifecycleManager.scan()` classifies all context artifacts
- [ ] `--prune` flag gates actual archive moves
- [ ] `--max-context-artifacts` warning logged on overflow
- [ ] `docs/context/archive/` in `.gitignore`
- [ ] `scripts/artifact_lifecycle_manager.py` D-183 copy; sync-gate updated
- [ ] `tests/test_artifact_lifecycle.py` passes (6 tests)

**Cross-cutting**
- [ ] `pytest tests/test_script_surface_sync.py` passes (2 new D-183 copies)
- [ ] `pytest -m integration` passes
- [ ] All existing tests still pass
- [ ] `docs/context/` artifact count is bounded (no unbounded growth after 3 consecutive runs)
- [ ] ENDGAME check: system is lighter after Phase 5 than before (fewer artifacts in hot tier,
     compaction runs deterministically, planner packet remains the sole fresh entry point)