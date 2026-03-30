# Phase 3 — Checklist Matrix (Stream C)

> **Status**: Ready to design; finalize after Stream B Day 4 (H-5) merged
> **Date**: 2026-03-30
> **Stream**: C (parallel to Stream B)
> **Input dependency**: Stream B H-5 (`skills_status` field stable)
> **Blocks**: Nothing
> **Roadmap alignment**: Fix-path to 8/10 — Code Maturity + Production Readiness

---

## Strategic Context

Stream C delivers a checklist projection that consumes the machine-readable `skills_status`
field introduced by Stream B H-5. Its purpose is to make loop readiness visible without
running the loop -- distinguishing a broken skill install from a legitimately skill-free repo.

This is a state-correctness problem, not a UX problem. `RESOLVER_UNAVAILABLE` (broken install)
must never be conflated with `EMPTY_BY_DESIGN` (healthy repo with no configured skills).

**Design rule**: Design and stub independently of Stream B. Finalize integration only after
Stream B Day 4 H-5 is merged and skills_status is stable. Wait for explicit notification.

---

## What Already Exists (Baseline)

| Asset | Location | State |
|---|---|---|
| `skill_resolver.py` | `scripts/utils/skill_resolver.py` | Mature -- returns `status: ok/degraded/failed` + `skills[]` |
| `validate_skill_activation.py` | `scripts/validate_skill_activation.py` | Mature -- fail-closed |
| `validate_skill_manifest.py` | `scripts/validate_skill_manifest.py` | Exists |
| `validate_skill_registry.py` | `scripts/validate_skill_registry.py` | Exists |
| `skills_status` in `runtime.steps` | `scripts/run_loop_cycle.py` | Net-new from H-5 |
| Checklist matrix / loop_readiness | (none) | Net-new in Phase 3 |

---

## Scope Boundary

| In Phase 3 | Deferred |
|---|---|
| Checklist projection consuming `skills_status` | Skill execution semantics (Phase 6 Stream D) |
| `RESOLVER_UNAVAILABLE` vs `EMPTY_BY_DESIGN` routing | Full skill pilot (Phase 6.3 gate) |
| Matrix: skill activation state -> loop readiness checks | Skill version drift detection |
| `loop_readiness_latest.json` artifact | Cross-run skill state history |
| 6 tests in `test_checklist_matrix.py` | Skill auto-promotion patterns |

---

## Deliverables

### D1: `scripts/check_loop_readiness.py`
Reads `skills_status` from `loop_cycle_summary_latest.json` and projects loop readiness.
Outputs `docs/context/loop_readiness_latest.json`:

```json
{
  "schema_version": "1.0",
  "generated_at_utc": "...",
  "skills_status": "RESOLVER_UNAVAILABLE | EMPTY_BY_DESIGN | ACTIVE",
  "loop_ready": true,
  "readiness_checks": [
    {"check": "skill_resolver_available", "result": "PASS | FAIL | SKIP", "reason": "..."}
  ],
  "routing": "broken_install | empty_by_design | skills_active",
  "operator_action": "..."
}
```

### D2: `src/sop/scripts/check_loop_readiness.py` (byte-identical D-183 copy)
Added to `DUAL_COPY_FILES` in `tests/test_cli_script_parity.py`.
Added to `critical_scan_manifest.json`.

### D3: `docs/context/loop_readiness_latest.json`
Emitted on every run after H-5 integration. Readable without running the loop.

### D4: `test_checklist_matrix.py` (7 tests)

---

## Routing Logic

| `skills_status` value | Meaning | `routing` | `loop_ready` | Operator action |
|---|---|---|---|---|
| `RESOLVER_UNAVAILABLE` | Import failed | `broken_install` | `false` | Fix install: `pip install -e .` |
| `EMPTY_BY_DESIGN` | Resolver loaded, returned `[]` | `empty_by_design` | `true` | None |
| `ACTIVE` | Skills resolved and present | `skills_active` | `true` | None |
| (absent) | Pre-H-5 build | `unknown` | `true` (fail-open) | Upgrade build |

**Key invariant**: `RESOLVER_UNAVAILABLE` must NEVER route to `empty_by_design`.

---

## Readiness Checks per Routing

### `broken_install`
- `skill_resolver_available`: FAIL
- `loop_ready`: false
- `operator_action`: "Skill resolver import failed. Run: pip install -e . then rerun sop."

### `empty_by_design`
- `skill_resolver_available`: PASS
- `skills_configured`: SKIP -- no skills in active_skills
- `loop_ready`: true
- `operator_action`: null

### `skills_active`
- `skill_resolver_available`: PASS
- `skills_configured`: PASS
- `skill_activation_valid`: PASS if `validate_skill_activation.py` exits 0, else FAIL
- `loop_ready`: true (false if activation validation fails)

---

## Execution Order

### Phase A -- Design and Stub (start now, independent of Stream B)

- [ ] Define `loop_readiness_latest.json` schema (see D1)
- [ ] Write stub `check_loop_readiness.py` accepting static `skills_status` input
- [ ] Write `src/sop/scripts/check_loop_readiness.py` byte-identical copy
- [ ] Add to `DUAL_COPY_FILES` in `tests/test_cli_script_parity.py`:
      append `"check_loop_readiness.py"` to `TestByteIdentityContract` list
      (currently 8 entries -- will become 9)
- [ ] Add to `critical_scan_manifest.json` (currently 8 pairs -- will become 9)
- [ ] Write `tests/test_checklist_matrix.py` with all 7 tests (stub tests use mock input)
- [ ] Create `src/sop/schemas/` directory (does not exist yet)
- [ ] Add schema to `src/sop/schemas/loop_readiness.schema.json`
- [ ] Verify `pyproject.toml` or `setup.cfg` includes `src/sop/schemas/` in `package_data`
      so schema is bundled in wheel (not only under `pip install -e .`)
- [ ] Confirm `TestByteIdentityContract` does not need updating for schema files

### Phase B -- Final Integration (after Stream B Day 4 H-5 notification)

- [ ] Wire `check_loop_readiness.py` to read `skills_status` from
      `loop_cycle_summary_latest.json` top-level key:
      read `summary["skills_status"]` -- NOT `summary["runtime"]["steps"][-1]["skills_status"]`
      (top-level presence confirmed in healthy_path fixture JSON)
- [ ] Emit `loop_readiness_latest.json` as part of loop run output
- [ ] Verify all 7 tests pass against live H-5 output
- [ ] Confirm `TestByteIdentityContract` green (DUAL_COPY_FILES count +1)

---

## Test Coverage (7 Tests)

| Test | Assert |
|---|---|
| `test_resolver_unavailable_routes_broken_install` | `RESOLVER_UNAVAILABLE` -> `routing=broken_install`, `loop_ready=false` |
| `test_empty_by_design_routes_correctly` | `EMPTY_BY_DESIGN` -> `routing=empty_by_design`, `loop_ready=true` |
| `test_resolver_unavailable_never_maps_to_empty_by_design` | Invariant: `RESOLVER_UNAVAILABLE` can never produce `routing=empty_by_design` |
| `test_active_skills_routes_skills_active` | `ACTIVE` -> `routing=skills_active`, `loop_ready=true` |
| `test_loop_readiness_artifact_schema_valid` | Emitted artifact validates against schema; all required fields present |
| `test_loop_readiness_readable_without_running_loop` | Valid output from static input -- no live loop execution required |
| `test_absent_skills_status_routes_unknown` | Absent `skills_status` field -> `routing=unknown`, `loop_ready=true` (fail-open fallback preserved) |

---

## Acceptance Gates

- [ ] `check_loop_readiness.py` at `scripts/` and `src/sop/scripts/` (byte-identical)
- [ ] Added to `DUAL_COPY_FILES`; `TestByteIdentityContract` green
- [ ] Added to `critical_scan_manifest.json`
- [ ] `loop_readiness_latest.json` emitted with correct schema after every run
- [ ] `RESOLVER_UNAVAILABLE` -> `broken_install`, `loop_ready: false`
- [ ] `EMPTY_BY_DESIGN` -> `empty_by_design`, `loop_ready: true`
- [ ] Invariant: `RESOLVER_UNAVAILABLE` never maps to `empty_by_design`
- [ ] Matrix readable without running the loop
- [ ] No dependency on internal loop state beyond what H-5 exposes
- [ ] All 7 tests pass; no regressions

---

## Implementation Review Rule

New logic in `sop/` package path first. `scripts/` is D-183 byte-identical sync only.
`check_loop_readiness.py` must have zero BLOCKER findings per `check_fail_open.py`.
Add to `critical_scan_manifest.json` immediately on creation.

---

## Cross-Stream Coordination

| Event | Action |
|---|---|
| Stream B Day 4 (H-5) merged | Begin Phase B integration |
| Stream C Phase A complete | Notify: stub ready, integration can proceed |
| Stream C complete | No downstream blocks; Stream E does not depend on C |

---

## What This Plan Does NOT Change

- `skill_resolver.py` -- already correct, untouched
- `validate_skill_activation.py` -- untouched
- `skills_status` field in `runtime.steps` -- owned by Stream B H-5
- Skill execution semantics -- deferred to Phase 6 Stream D
- No existing field removed or renamed

---

## Completion Definition

Phase 3 is complete when:
1. `check_loop_readiness.py` dual copy committed and in manifest
2. `loop_readiness_latest.json` emitted correctly on every run
3. Routing invariant enforced: `RESOLVER_UNAVAILABLE` never maps to `empty_by_design`
4. All 7 tests pass
5. All existing tests still pass
