# Phase 2 — Execution Path Hardening

> **Status**: Ready to execute
> **Date**: 2026-03-30
> **Source**: IMMEDIATE_NEXT_STEP.md + MULTISTREAM_EXECUTION_PLAN.md (Stream B)
> **Roadmap alignment**: Fix-path to 8/10 — Code Maturity + Production Readiness tracks
> **Prerequisite**: Phase 5 release readiness gate green (all L + M + N surfaces complete)
> **Blocks**: Stream E (Golden Path Proof) — cannot start until Stream A + Stream B complete

---

## Strategic Context

This plan is Stream B of the multi-stream execution map. It is the **critical path** item.
Stream E (external smoke CI / golden path proof) is blocked until this plan and Stream A
(boundary sealing) are both complete.

The fix-path to 8/10 requires:
- **Code Maturity**: close all fail-open paths, expand to 21+ tests with error/boundary/integration coverage
- **Production Readiness**: every hard failure path writes an inspectable artifact; no silent import failures
- **API stability**: defined entrypoint contract (`sop run` primary, `scripts/` compat-only, explicit divergence detection)

This phase delivers the foundation that makes the golden path proof (Stream E) trustworthy.

---

## Scope Boundary

| In Phase 2 | Deferred to Phase 3+ |
|---|---|
| H-1 to H-6, H-NEW-1 to H-NEW-4 | Artifact canonical hash stability |
| `run_failure_latest.json` core schema | Schema version policy CI enforcement |
| `gate_decisions[]` with `mtime_utc` artifact_refs | Full `hash/content_kind/hash_strategy` in artifact_refs |
| Fixed stderr grammar | `decision_basis_count` |
| AST-first BLOCKER scan + manifest symmetry | Full `hash/content_kind/hash_strategy` (deferred) |
| Healthy-path equivalence fixture | Schema version policy CI enforcement |
| 21 active tests (target passing set; test_hardening.py collects 67) | |
| `attempt_id` (already shipped in _failure_reporter.py) | |
| `evaluation_outcome_source` (already shipped) | |
| `failure_origin` (already shipped) | |
| `spec_phase` (already shipped) | |

---

## Stream Map (Multi-Stream Context)

```
Stream A: Boundary Sealing       (Phase 0)  -- parallel, no dependencies
Stream B: Execution Hardening    (Phase 2)  -- THIS PLAN, critical path
Stream C: Checklist Matrix       (Phase 3)  -- parallel, benefits from H-5
Stream D: Navigation Map         (Phase 6)  -- parallel, no dependencies
Stream E: Golden Path Proof      (Phase 1)  -- BLOCKED until A + B complete
```

---

## Hardening Items

### H-NEW-2 (Day 1 — Confirm Baseline)
**_failure_reporter.py already implemented -- confirm baseline only**
- Atomic stdlib write: `tempfile.mkstemp` + `os.replace`. No external deps.
- Always overwrite. If write fails: emit one-line envelope to stderr then exit non-zero.
- Schema fields: `schema_version`, `failure_class`, `run_id`, `entrypoint`, `execution_mode`,
  `tool_version`, `package_version`, `python_version`, `platform`, `cwd`, `repo_root`,
  `module_origins`, `failed_at`, `failed_component`, `reason`, `recoverability`,
  `install_check`, `provenance_check`, `final_result: "ERROR"`
- Fixed stderr envelope grammar (machine-parsable, one line):
  `FATAL failure_class=<class> failed_component=<component> recoverability=<RETRYABLE|REQUIRES_FIX> artifact_write_failed=<true|false>`
- **Must be in place before H-1/H-2 introduce hard failures.**

### H-NEW-1 Stage 1 (Day 1)
**Preflight spec check at CLI entry**
- Use `importlib.util.find_spec()` to verify `PhaseGate`, `WorkerRole`, `AuditorRole`,
  `skill_resolver`, `atomic_io` are all resolvable before calling `run_cycle()`.
- On failure: write `run_failure_latest.json` with `failure_class: "INSTALL_ERROR"` then exit.

### H-1 (Day 1)
**PhaseGate = None -> hard ImportError**
- Replace final `PhaseGate = None` fallback in `scripts/run_loop_cycle.py` (~lines 50-57)
  with `raise ImportError("<clear install message>")` after writing failure artifact.

### H-2 (Day 1)
**Worker/Auditor stub block -> hard ImportError**
- Replace final stub class fallback in `scripts/run_loop_cycle.py` (~lines 70-107)
  with `raise ImportError` after writing failure artifact.

### H-NEW-1 Stage 2 (Day 2)
**Provenance check**
- Assert each module's `__file__` resolves under the expected package root.
- Derive expected root from `importlib.util.find_spec("sop").submodule_search_locations`
  at runtime — not hardcoded — works across install modes (editable, wheel, source).
- If `scripts/` path resolves differently from package path: `failure_class: "ENTRYPOINT_DIVERGENCE"`.

### H-NEW-4 (Day 2)
**Package path > scripts path strong assertion test**
- `test_package_path_takes_priority_over_scripts`: installs package, calls `sop run`,
  asserts critical modules resolve from package path; preflight fails immediately if package path missing.

### H-3 (Day 2)
**Gate HOLD -> explicit early return**
- After Gate B HOLD: `final_result = "NOT_READY"`, `final_exit_code = 1`.
- `gate_decision: "HOLD"` written as internal diagnostic in JSON.
- `gate_decisions[]` written on **every** run (healthy and blocked) with per-gate fields:
  `name`, `decision` (PROCEED|HOLD), `gate_executed: true|false`,
  `gate_impl` (e.g. `"sop.scripts.phase_gate.PhaseGate"`),
  `skipped_reason` (required when `gate_executed: false`),
  `conditions[]`, `evaluated_at_utc`,
  `artifact_refs: {name: mtime_utc}` for each artifact PhaseGate reads.

### H-4 (Day 3)
**WorkerRole.run() and AuditorRole.run() -> NotImplementedError**
- Replace stub bodies in `src/sop/scripts/worker_role.py` and `auditor_role.py`.

### H-5 (Day 4)
**skill_resolver -> machine-readable skills_status**
- Emit structured step into `runtime.steps`:
  - `skills_status: "RESOLVER_UNAVAILABLE"` — import failed
  - `skills_status: "EMPTY_BY_DESIGN"` — resolver loaded but returned `[]`
- **Cross-stream trigger**: notify Stream C when H-5 merges (skills_status field stable).

### H-6 (Day 4)
**atomic_write_json stub -> WARN step on trace write failure**
- Replace `except Exception: pass` on trace write with a `status: "WARN"` step in `runtime.steps`.

### H-NEW-3 (Day 5)
**check_fail_open.py — graded baseline scan**
- Three tiers: `BLOCKER` / `WARN` / `ALLOWLISTED`
- BLOCKER patterns (AST-based, not regex-only):
  - `except: pass`, hardcoded PASS in role stubs, `PhaseGate = None`
  - broad-except with silent downgrade (`except Exception: return []`)
  - tainted-fallback-chain (except assigns to result/status/summary without re-raise)
  - writes-success-after-exception, conditional fail-open (`if X is None: skip`)
- `critical_scan_manifest.json` committed as 
source of truth. Symmetric new-file rule: new *_gate.py or *_role.py not in manifest = CI fail.
- Zero-allowlist rule for critical-path files: run_loop_cycle.py, phase_gate.py,
  __main__.py, worker_role.py, auditor_role.py, planner_role.py.

---

## Day-by-Day Execution Order

### Day 1 -- Failure Infrastructure + Hard Imports
Stream A can run in parallel.
Gate: failure artifact infra must exist before H-1/H-2 introduce hard failures.

- [ ] H-NEW-2: build run_failure_latest.json atomic write + stderr fallback
- [ ] H-NEW-1 Stage 1: preflight spec check at CLI entry
- [ ] H-1: replace PhaseGate = None with hard ImportError
- [ ] H-2: replace worker/auditor stub block with hard ImportError
- [ ] Verify schema_version and failure_class present in all written artifacts
- [ ] Run existing test suite -- no regressions
- [ ] Package install regression: pip install -e . && sop run --repo-root . reaches preflight

### Day 2 -- Provenance + Gate HOLD
Stream C and D can advance in parallel.

- [ ] H-NEW-1 Stage 2: provenance check (module.__file__ vs expected package root)
- [ ] H-NEW-4: test_package_path_takes_priority_over_scripts
- [ ] H-3: wire Gate HOLD -> final_result = NOT_READY, gate_decision in JSON
- [ ] Add test_gate_a_hold_exits_early, test_gate_b_hold_sets_not_ready

### Day 3 -- Role Stubs + Double Failure Path

- [ ] H-4: WorkerRole.run() and AuditorRole.run() -> NotImplementedError
- [ ] Add test_worker_run_raises_not_implemented, test_auditor_run_raises_not_implemented
- [ ] Add test_failure_artifact_write_failure_emits_stderr
- [ ] Add test_double_failure_path (primary failure + artifact write failure combined)

### Day 4 -- Skills + Observability
Cross-stream trigger: notify Stream C when H-5 merges.

- [ ] H-5: skills_status machine-readable (RESOLVER_UNAVAILABLE vs EMPTY_BY_DESIGN)
- [ ] H-6: promote trace write failure to WARN step
- [ ] Add test_skill_resolver_missing_emits_resolver_unavailable
- [ ] Add test_skill_resolver_empty_emits_empty_by_design

### Day 5 -- Scan Baseline + Schema Contract + Equivalence

- [ ] H-NEW-3: write check_fail_open.py (BLOCKER/WARN/ALLOWLISTED, AST-first, manifest symmetry)
- [ ] Produce fail_open_allowlist.json
- [ ] Add test_check_fail_open_baseline, test_manifest_symmetry
- [ ] Add test_schema_drift [PHASE 2 SCHEMA CONTRACT GATE]
- [ ] Add test_healthy_path_equivalence (fixed known-good fixture)
- [ ] Add test_windows_path_fixture, test_shadowed_module_fixture
- [ ] Add test_compatibility_path_divergence_message, test_python_m_sop_provenance_matches_sop_run
- [ ] Run full test suite -- all 21 active tests must pass

---

## Test Coverage (21 Active Tests)

| Test | Assert |
|---|---|
| test_phasegate_import_failure_raises | ImportError raised; artifact written with schema_version and failure_class |
| test_preflight_spec_check_catches_missing | Preflight exits before run_cycle() when PhaseGate unresolvable |
| test_preflight_provenance_check_catches_wrong_module | Preflight exits when module resolves from wrong path |
| test_gate_a_hold_exits_early | Gate A HOLD: run_cycle() exits before advisory artifact generation |
| test_gate_b_hold_sets_not_ready | Gate B HOLD -> final_result = NOT_READY, gate_decision = HOLD in JSON |
| test_worker_run_raises_not_implemented | WorkerRole.run() raises NotImplementedError |
| test_auditor_run_raises_not_implemented | AuditorRole.run() raises NotImplementedError |
| test_skill_resolver_missing_emits_resolver_unavailable | Import failure -> skills_status = RESOLVER_UNAVAILABLE |
| test_skill_resolver_empty_emits_empty_by_design | Resolver returning [] -> skills_status = EMPTY_BY_DESIGN |
| test_failure_artifact_written_on_hard_failure | Artifact written with schema_version and failure_class on every hard failure |
| test_failure_artifact_write_failure_emits_stderr | Write fail: stderr one-line envelope, process exits non-zero |
| test_package_path_takes_priority_over_scripts | sop run resolves modules from package path; preflight fails if missing |
| test_check_fail_open_baseline | Output matches committed allowlist; new BLOCKERs fail CI |
| test_shadowed_module_fixture | Fake phase_gate.py in cwd/scripts/ detected; artifact records INSTALL_ERROR |
| test_compatibility_path_divergence_message | Error states: (1) divergence, (2) use sop run, (3) conflicting paths |
| test_healthy_path_equivalence | Clean install + fixed fixture -> same final_result/artifacts/exit-code as baseline |
| test_python_m_sop_provenance_matches_sop_run | python -m sop run and sop run agree on execution_mode and module_origins |
| test_double_failure_path | Primary + write failure: exits non-zero, stderr complete, no partial temp file |
| test_windows_path_fixture | Windows paths: shadowed-module detection identical to POSIX |
| test_manifest_symmetry | (a) Removing manifest file = CI fail; (b) new critical-role file without entry = CI fail |
| test_schema_drift [SCHEMA CONTRACT GATE] | Artifact validates against run_failure_latest.schema.json; all fields present |

---

## Acceptance Gates

- [ ] PhaseGate = None fallback gone; import failure raises ImportError with clear install message
- [ ] Worker/auditor stub block gone; import failure raises ImportError
- [ ] sop run performs two-stage preflight (spec + provenance) before calling run_cycle()
- [ ] Preflight detects modules resolving from wrong path, not only missing modules
- [ ] Every hard failure path writes run_failure_latest.json with schema_version and failure_class
- [ ] If artifact write fails: stderr emits one-line envelope, process exits non-zero
- [ ] Gate A HOLD: run_cycle() returns before advisory artifact generation
- [ ] Gate B HOLD: final_result = NOT_READY, final_exit_code = 1, gate_decision: HOLD in JSON
- [ ] WorkerRole.run() raises NotImplementedError
- [ ] AuditorRole.run() raises NotImplementedError
- [ ] skill_resolver import failure -> skills_status = RESOLVER_UNAVAILABLE
- [ ] skill_resolver returning [] -> skills_status = EMPTY_BY_DESIGN
- [ ] All 21 tests pass; existing suite passes with no regressions
- [ ] Package install regression passes
- [ ] check_fail_open.py baseline + fail_open_allowlist.json committed; new BLOCKERs fail CI
- [ ] critical_scan_manifest.json committed; symmetric manifest rule enforced
- [ ] Healthy-path fixture: no run_failure_latest.json, no FATAL envelope on stderr
- [ ] gate_decisions[] visible on every run (healthy and blocked)
- [ ] gate_executed: true in every gate entry on every run
- [ ] failure_class in artifact always matches stderr one-line envelope
- [ ] Operator can distinguish gate ran and passed from gate was skipped

---

## Roadmap Alignment (Fix-Path to 8/10)

### Code Maturity

| Action | Phase 2 Delivery |
|---|---|
| Expand test coverage | 21 tests: error conditions, boundary cases, cross-module interactions, CLI invocations |
| Formalize API stability | sop run primary, scripts/ compat-only, divergence = hard fail |
| Strengthen abstractions | AST-based check_fail_open.py; critical_scan_manifest.json prevents coverage drift |

### Production Readiness

| Action | Phase 2 Delivery |
|---|---|
| Smoke test foundation | Every hard failure writes inspectable artifact; healthy path produces none |
| CI proofs | test_schema_drift enforces schema contract every run; test_manifest_symmetry enforces scan coverage |
| Observable failures | Machine-parsable stderr envelope; module_origins in artifact for operator diagnosis |

### Unblocks Stream E (Golden Path Proof)

Once Phase 2 acceptance gates pass AND Stream A (boundary sealing) is complete:
- pip install terminal-zero-governance && sop run --repo-root . can be proven end-to-end
- No silent import failures; failure artifacts present on every hard failure
- Smoke CI on Windows (primary), Linux (secondary), macOS (best-effort)

---

## Implementation Review Rule

Any new logic must be placed in the sop package main path first.
Only after the main path works should compatibility behavior in scripts/ be considered.
Never implement in scripts/ first and backfill -- this is how the compatibility path
gets promoted back to the main path against the README contract.

---

## Risk Register

| Risk | Mitigation |
|---|---|
| H-1/H-2 hard failures before artifact infra is ready | Build H-NEW-2 FIRST on Day 1 |
| Stream C finalizes before H-5 is stable | Stub integration; wait for Day 4 notification |
| New critical-role file added without manifest entry | Symmetric manifest CI rule catches it immediately |
| Compatibility path promoted back to main path | New logic in sop/ first; never backfill from scripts/ |
| Stream E starts before Stream A boundary sealing | Hard block: Stream E checklist item 1 = Stream A gate |

---

## What This Plan Does NOT Change

- PhaseGate.evaluate(), emit(), emit_handoff() -- already correct, untouched
- Execution capabilities in WorkerRole or AuditorRole -- not added here
- P0/P1/P4/P5 core artifact contracts -- no existing field removed or renamed
- loop_cycle_summary_latest.json extended with gate_decisions[] -- additive only
- run_failure_latest.json is a new surface -- no existing artifact modified

---

## Cross-Stream Coordination

| Event | Trigger | Action |
|---|---|---|
| Day 4 (H-5) merged | skills_status stable | Notify Stream C to finalize checklist matrix |
| Stream A complete | Boundary sealing done | Notify Stream D to finalize navigation examples |
| Stream A + B both complete | All acceptance gates pass | Unblock Stream E |
| Any stream adds *_gate.py or *_role.py | New file | Register in critical_scan_manifest.json immediately |

---

## Completion Definition

Phase 2 is complete when:
1. All 21 active tests pass
2. run_failure_latest.json written on every hard failure path
3. Healthy-path fixture: no run_failure_latest.json, no FATAL on stderr
4. gate_decisions[] visible on every run; gate_executed: true on every gate
5. check_fail_open.py baseline committed; new BLOCKERs fail CI
6. critical_scan_manifest.json committed; symmetric rule enforced

Phase 2 complete + Stream A complete -> Stream E (Golden Path Proof) unblocked.
