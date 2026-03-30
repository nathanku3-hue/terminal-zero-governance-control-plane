# Operator Navigation Map

> Stream D artifact — Phase 6.
> Provides deterministic routing from any operator state to the correct next action in ≤ 3 steps.
> All paths are repo-root relative. No absolute paths.
> Entry point labels: `sop run` = PRIMARY; `scripts/` commands = COMPAT (compatibility path only).

---

## Truth Surfaces Read Order

Before any operator action, resolve the entry model in this order:

1. `../KERNEL_ACTIVATION_MATRIX.md` — which kernel capabilities are mandatory right now
2. `../SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md` — which multi-stream surfaces are expected
3. `docs/context/planner_packet_current.md` — if active and instantiated
4. `docs/context/impact_packet_current.md` — if active and instantiated
5. `docs/context/bridge_contract_current.md` — if active and instantiated
6. `docs/context/done_checklist_current.md` — if active and instantiated
7. `docs/context/multi_stream_contract_current.md`, `post_phase_alignment_current.md`,
   `observability_pack_current.md` — only when active and instantiated

Escalate to phase briefs or decision logs only if a required active surface is missing or the
entry surfaces are insufficient to name the active bottleneck.

---

## First-Run Steps

Use this sequence when running in a repo for the first time or after a clean environment setup.

```
Step 1 — Verify install
  PRIMARY:  sop run --help
  COMPAT:   python scripts/startup_codex_helper.py --help
  Check:    Command resolves without ImportError; sop package path matches repo root
            (python -c "import sop; print(sop.__file__)")

Step 2 — Startup
  PRIMARY:  sop run startup --repo-root .
  COMPAT:   python scripts/startup_codex_helper.py --repo-root .
  Produces: docs/context/startup_intake_latest.json
            docs/context/init_execution_card_latest.md
            docs/context/round_contract_seed_latest.md
  Check:    All three artifacts written; no FATAL on stderr

Step 3 — Loop cycle
  PRIMARY:  sop run --repo-root . --skip-phase-end --allow-hold true
  COMPAT:   python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
  Produces: docs/context/loop_cycle_summary_latest.json
            docs/context/exec_memory_packet_latest.json
  Check:    Artifacts written; inspect skills_status in summary (see Skills Status Routing below)
```

---

## Normal Run Steps

Use this sequence for a standard operator pass when environment and startup are already complete.

```
Step 1 — Read truth surfaces
  Action:   Follow Truth Surfaces Read Order above
  Check:    Active bottleneck named; planner_packet and bridge_contract consistent

Step 2 — Loop cycle
  PRIMARY:  sop run --repo-root . --skip-phase-end --allow-hold true
  COMPAT:   python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
  Check:    Loop summary written; no FATAL on stderr; skills_status is OK or EMPTY_BY_DESIGN

Step 3 — Closure
  PRIMARY:  sop validate --repo-root .
  COMPAT:   python scripts/validate_loop_closure.py --repo-root .
  Produces: docs/context/loop_closure_status_latest.json
  Check:    Exit 0 = READY_TO_ESCALATE; Exit 1 = NOT_READY; Exit 2 = infra/input error

Step 4 — Takeover (when closure = READY_TO_ESCALATE)
  PRIMARY:  sop run takeover --repo-root .
  COMPAT:   python scripts/print_takeover_entrypoint.py --repo-root .
  Check:    Printed guidance reflects latest closure state
```

---

## Failure Decision Tree

Match the `failure_class` value from `docs/context/run_failure_latest.json` to the correct
branch. All seven `failure_class` values are covered. Each branch reaches a recovery action
in ≤ 3 steps.

### `IMPORT_ERROR`

```
Symptom:  Hard ImportError on startup or loop entry
Step 1:   python -c "import sop; print(sop.__file__)"
          → If error: go to Step 2
          → If path is outside repo root: shadow detected, go to Step 3
Step 2:   pip install -e .  →  re-run command
Step 3:   Remove shadowed module from sys.path or rename conflicting file → pip install -e . → re-run
```

### `PREFLIGHT_FAILED`

```
Symptom:  Preflight spec check at CLI entry failed; run did not start
Step 1:   Read FATAL stderr line: inspect failed_component field
Step 2:   Read docs/context/run_failure_latest.json → recoverability field
          → TRANSIENT: re-run command
          → PERMANENT: fix the spec mismatch identified in failed_component before re-running
Step 3:   After fix, re-run and confirm no PREFLIGHT_FAILED in new artifact
```

### `GATE_HOLD`

```
Symptom:  Gate A or Gate B returned HOLD; final_result = HOLD
Step 1:   Read docs/context/loop_cycle_summary_latest.json → gate_decisions[] array
          Identify which gate triggered HOLD and the criterion that was not met
Step 2:   Address the unmet criterion (see done_checklist_current.md for acceptance criteria)
Step 3:   Re-run loop cycle; confirm gate_decisions[] shows PASS for resolved gate
Note:     GATE_HOLD is expected behavior, not a defect. Use --allow-hold true to record without failing.
```

### `SKILLS_RESOLVER_UNAVAILABLE`

```
Symptom:  skills_status = RESOLVER_UNAVAILABLE in loop summary
Step 1:   python -c "from sop import skill_resolver; print('resolver present')"
          → ImportError: resolver missing from package → go to Step 2
          → No error but loop still fails: path shadowing → go to Step 3
Step 2:   pip install -e . → re-run diagnostic → re-run loop
Step 3:   python -c "import sys; print([p for p in sys.path])"
          Remove or rename shadowed path → pip install -e . → re-run
Full matrix: docs/context/skill_readiness_matrix.md (Section 1)
```

### `ARTIFACT_WRITE_FAILED`

```
Symptom:  Loop completed but could not write output artifact; stderr shows artifact_write_failed=true
Step 1:   Check disk space and file permissions on docs/context/
Step 2:   Confirm no other process holds a lock on the target file
Step 3:   Re-run loop command; confirm artifact written on second attempt
Note:     Artifact writes use atomic mkstemp + os.replace; partial writes should not occur
```

### `SCHEMA_DRIFT`

```
Symptom:  test_schema_drift fails; schema contract gate triggered
Step 1:   Run: python -m pytest tests/ -k test_schema_drift -v
          Read the diff output to identify which field changed
Step 2:   If field change was intentional: update the schema in docs/context/schemas/
          and update the test fixture; commit both together
          If field change was unintentional: revert the code change that caused drift
Step 3:   Re-run full test suite; confirm test_schema_drift passes
```

### `UNKNOWN`

```
Symptom:  failure_class = UNKNOWN or field absent from run_failure_latest.json
Step 1:   Read full FATAL stderr envelope; capture failed_component and recoverability
Step 2:   Check docs/context/loop_cycle_summary_latest.json for the step name where
          execution stopped; cross-reference with docs/runbook_ops_active.md
Step 3:   If root cause still unclear, escalate: read phase brief in docs/phase_brief/
          and docs/decision_log.md for recent changes that may explain the failure
```

---

## Gate HOLD Path

Gate HOLD is not an error. It records that one or more acceptance criteria were not met on this
loop pass. The loop exits with `final_result = HOLD` and writes `gate_decisions[]` to the
loop cycle summary.

```
Operator receives HOLD closure result
  ↓
Read docs/context/loop_cycle_summary_latest.json → gate_decisions[]
  ↓
For each entry with status = HOLD:
  Read criterion field → identify the unmet acceptance criterion
  Read docs/context/done_checklist_current.md → locate the corresponding done check
  Address the criterion (implement, fix, or document)
  ↓
Re-run loop with: sop run --repo-root . --skip-phase-end --allow-hold true
  ↓
Confirm gate_decisions[] shows PASS for previously HOLD gates
  ↓
Re-run closure: sop validate --repo-root .
  ↓
Expect exit 0 (READY_TO_ESCALATE) when all gates pass
```

Do not bypass a HOLD by removing `--allow-hold true`. That flag records the HOLD as a
graded shortfall, not a failure. Removing it converts expected shortfalls into hard failures.

---

## Skills Status Routing

After each loop cycle, check `skills_status` in `docs/context/loop_cycle_summary_latest.json`.
Route to the correct action using this table:

| `skills_status` | Ruling | Next Step |
|---|---|---|
| `OK` | PROCEED | No action; continue to closure |
| `EMPTY_BY_DESIGN` | PROCEED | No action unless skills were expected; see matrix Section 2 |
| `RESOLVER_UNAVAILABLE` | **BLOCK** | Stop; follow SKILLS_RESOLVER_UNAVAILABLE branch above |

Full diagnostic steps and recovery procedures for all three values:
→ `docs/context/skill_readiness_matrix.md`

Available after Stream C Phase B: `docs/context/loop_readiness_latest.json`

---

## WARN Steps Explanation

`WARN` steps (introduced in Stream B H-6) are non-fatal observability signals. They appear in
the loop cycle summary as steps with `result = WARN` rather than `PASS` or `FAIL`.

**What WARN means:**
- The step attempted an action (e.g., writing a trace artifact) and encountered a non-critical
  failure that does not block loop completion.
- The loop continues past a WARN step. The run is not aborted.
- A `WARN` step does not set `final_result = HOLD` by itself.

**What to do with a WARN:**

```
Step 1:  Read the WARN step name from docs/context/loop_cycle_summary_latest.json
Step 2:  Check stderr for the corresponding WARN envelope line
         (format: WARN step=... component=... message=...)
Step 3:  If the WARN is for trace_write: check disk space and file permissions on docs/context/
         If repeated across runs: investigate root cause before next phase boundary
         If one-off: record in run notes and continue
```

Do not promote a WARN to a BLOCK without confirming recurrence. A single WARN on a trace write
is expected under some filesystem conditions and does not require immediate remediation.

---

## Compatibility Path Label

All `scripts/` commands in this document are labeled **COMPAT**. They exist for backward
compatibility with environments where the `sop` CLI is not yet installed.

**Rule:** New logic must be placed in the `sop` package first. The `scripts/` path is a
read-through compatibility shim only. Never implement new behavior in `scripts/` first
and backfill — this is how the compatibility path gets promoted back to the main path
against the README contract.

**When `sop` CLI is not yet available:** Use COMPAT commands only. Once `sop` is installed
(`pip install -e .` from repo root), prefer PRIMARY commands for all subsequent runs.
