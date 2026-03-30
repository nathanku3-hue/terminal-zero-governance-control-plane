# Phase 5 — Golden Path Proof (Stream E)

> **Status**: BLOCKED — do not begin until Stream A + Stream B acceptance gates both pass
> **Date**: 2026-03-30
> **Stream**: E (external smoke CI)
> **Hard block**: Stream E item 1 = Stream A gate. Stream E item 2 = Stream B gate.
> **Roadmap alignment**: Fix-path to 8/10 — Production Readiness track

---

## Strategic Context

Stream E proves the install-to-run path works end-to-end on a clean machine.
It is the final integration gate before external operator onboarding.

**Entry requirements (both must be confirmed green before any work begins):**
1. Stream A complete — boundary sealing acceptance gates pass
2. Stream B complete — all 21 active tests pass, scan baseline committed, every hard
   failure path writes `run_failure_latest.json`, healthy path produces no failure artifact

---

## What Already Exists (Baseline)

| Asset | Location | State |
|---|---|---|
| `release-validation.yml` | `.github/workflows/` | Exists -- `cli-smoke`, `backward-compat`, `wheel-smoke`, `test-suite`, `publish-pypi` |
| `fast-checks.yml` | `.github/workflows/` | Exists |
| `full-test.yml` | `.github/workflows/` | Exists |
| `pyproject.toml` | repo root | Exists -- `sop` CLI, `schemas/**` in package-data |
| `cli-smoke` job | `release-validation.yml` | Exists -- `sop --help`, `sop version`, `sop init` on Windows + Linux |
| `backward-compat` job | `release-validation.yml` | Exists -- 5 `scripts/` entrypoints |
| `wheel-smoke` job | `release-validation.yml` | Exists -- manual trigger only |
| Golden path run assertion | (none) | Net-new |
| Preflight failure detection | (none) | Net-new |
| Shadowed-module fixture CI | (none) | Net-new |
| macOS runner | (none) | Net-new (best-effort, non-blocking) |

---

## Scope Boundary

| In Phase 5 | Deferred |
|---|---|
| Golden path: `sop run --repo-root .` on clean install | Performance benchmarks |
| Preflight failure: broken package path detected explicitly | Cross-version Python matrix |
| Healthy fixture: no `run_failure_latest.json`, no FATAL stderr | PyPI trusted publisher live test |
| Shadowed-module: detection identical on Windows + Linux | Full operator onboarding script |
| Windows primary + Linux secondary CI green | |
| macOS best-effort (non-blocking) | |
| `failure_class` in artifact matches stderr envelope | |
| `gate_decisions[]` visible in summary on healthy run | |

---

## Deliverables

### E-1: `golden-path` job in `release-validation.yml`

New job on `windows-latest` (primary) + `ubuntu-latest` (secondary).
Triggered on: push to main/master, PR, `workflow_dispatch`.

Assertions (all must pass):
1. `pip install -c constraints.txt .` exits 0
2. `sop run --repo-root .` exits 0 (healthy repo)
3. `run_failure_latest.json` does NOT exist after healthy run
4. No `FATAL` line on stderr after healthy run
5. `loop_cycle_summary_latest.json` exists and contains `gate_decisions[]` array
6. `skills_status` present at top-level key of summary JSON

### E-2: `preflight-failure-detection` job

New job. Assertions:
1. Corrupt/remove `sop` package path -- `sop run --repo-root .` exits non-zero
2. `run_failure_latest.json` written with `failure_class` present
3. FATAL stderr line present; `failure_class` matches artifact
4. Exit code non-zero

### E-3: `shadowed-module-smoke` job

New job. Assertions:
1. Place fake `phase_gate.py` in `scripts/` of clean checkout
2. `sop run --repo-root .` detects shadow and exits non-zero
3. `run_failure_latest.json` written with `failure_class: IMPORT_ERROR` or `PREFLIGHT_FAILED`
4. Behavior identical on Windows and Linux

### E-4: `golden-path-macos` job (non-blocking)

New job with `continue-on-error: true` on `macos-latest`.
Runs same assertions as E-1. Failure does not block merge.

---

## Entry Gate Checklist (verify before starting any work)

- [ ] Stream A: scoped rg scan returns zero matches on all operator-facing docs
- [ ] Stream A: template canonical sources documented in `docs/context/README.md`
- [ ] Stream A: `operator_onboarding_checklist.md` has `KERNEL_ACTIVATION_MATRIX.md` reference
- [ ] Stream B: all 21 active tests pass (`pytest tests/test_hardening.py --collect-only -q` shows 81 collected)
- [ ] Stream B: `run_failure_latest.json` written on every hard failure path
- [ ] Stream B: healthy path: no `run_failure_latest.json`, no FATAL on stderr
- [ ] Stream B: `gate_decisions[]` visible on every run
- [ ] Stream B: `check_fail_open.py` baseline committed; new BLOCKERs fail CI
- [ ] Stream B: `critical_scan_manifest.json` committed; symmetric rule enforced

---

## Execution Order

### Day 1 -- Entry Gate Verification

- [ ] Confirm Stream A acceptance gates all pass
- [ ] Confirm Stream B acceptance gates all pass (`pytest -q`; inspect artifacts)
- [ ] Run `release-validation.yml` `cli-smoke` and `backward-compat` locally -- green
- [ ] Confirm `sop run --repo-root .` exits 0 on current repo
      Note: `sop run` IS the loop cycle command. `sop run loop` is not a valid subcommand.
      Valid subcommands: startup, run, validate, takeover, supervise, init, version.
      **Stream D Day 2 flag**: `operator_navigation_map.md` uses `sop run loop` and
      `sop run closure` -- both invalid. Correct to `sop run --repo-root .` and
      `sop validate --repo-root .` respectively. Fix before Phase 4 Day 2 completes.

### Day 2 -- E-1: Golden Path Job

- [ ] Add `golden-path` job to `release-validation.yml`
- [ ] Assert: no `run_failure_latest.json` after healthy run
- [ ] Assert: no `FATAL` on stderr
- [ ] Assert: `loop_cycle_summary_latest.json` with `gate_decisions[]` and `skills_status`
- [ ] Green on Windows + Linux runners

### Day 3 -- E-2 + E-3: Failure Detection + Shadowed Module

- [ ] Add `preflight-failure-detection` job
- [ ] Assert: non-zero exit + artifact + FATAL stderr; `failure_class` matches
- [ ] Add `shadowed-module-smoke` job
- [ ] Assert: shadow detected on Windows + Linux; correct `failure_class` in artifact

### Day 4 -- E-4: macOS + Full Integration Run

- [ ] Add `golden-path-macos` with `continue-on-error: true`
- [ ] Run full `release-validation.yml` end-to-end
- [ ] All required jobs green: `golden-path`, `preflight-failure-detection`,
      `shadowed-module-smoke`, `cli-smoke`, `backward-compat`, `test-suite`
- [ ] macOS: best-effort result recorded; non-blocking
- [ ] Notify: Stream E complete, system ready for external operator onboarding

---

## Acceptance Gates

- [ ] `golden-path` job green on Windows + Linux
- [ ] Healthy run: no `run_failure_latest.json`, no FATAL on stderr
- [ ] Healthy run: `gate_decisions[]` in `loop_cycle_summary_latest.json`
- [ ] Healthy run: `skills_status` at top-level key of summary JSON
- [ ] `preflight-failure-detection` green: broken install detected explicitly
- [ ] `failure_class` in artifact always matches FATAL stderr envelope
- [ ] `shadowed-module-smoke` green: shadow detected identically on Windows + Linux
- [ ] `cli-smoke`, `backward-compat`, `test-suite` still green (no regressions)
- [ ] macOS: best-effort job runs; failure non-blocking
- [ ] `publish-pypi` dependency chain unchanged

---

## CI Job Dependency Graph

```
cli-smoke -----------+
backward-compat -----+--> publish-pypi (tags only; needs: list UNCHANGED)
test-suite ----------+
semver-check --------+
release-gate --------+

golden-path          -- required CI, does NOT feed publish-pypi (no sign-off)
preflight-failure    -- required CI, does NOT feed publish-pypi (no sign-off)
shadowed-module      -- required CI, does NOT feed publish-pypi (no sign-off)

golden-path-macos (continue-on-error: true) -- non-blocking
```

**Decision (GAP-1)**: The three new jobs (`golden-path`, `preflight-failure-detection`,
`shadowed-module-smoke`) are required CI checks but are NOT added to `publish-pypi`'s
`needs:` list. Rationale: no explicit sign-off to modify the publish gate has been
recorded. The `publish-pypi` `needs:` list remains:
`[cli-smoke, backward-compat, semver-check, release-gate, test-suite]`.
If a future decision adds the new jobs to the publish gate, record sign-off here before
making the change.

---

## Implementation Review Rule

All new CI job steps must use the same venv pattern as existing jobs:
- Windows: `.venv\Scripts\python` / `.venv\Scripts\sop`
- Linux: `.venv/bin/python` / `.venv/bin/sop`
- Install: `pip install -c constraints.txt .` (not editable install in CI)
- No absolute paths in any CI step
- Do not modify `publish-pypi` job or its `needs:` list without explicit sign-off

---

## What This Plan Does NOT Change

- Existing `cli-smoke`, `backward-compat`, `wheel-smoke`, `semver-check`,
  `test-suite`, `publish-pypi` jobs -- no modifications
- `fast-checks.yml`, `full-test.yml` -- no modifications
- `pyproject.toml` -- no modifications (schemas already in package-data)
- `constraints.txt` / `constraints-dev.txt` -- no modifications
- No source code changes -- CI YAML only

---

## Cross-Stream Coordination

| Event | Action |
|---|---|
| Stream A complete | Stream E entry gate item 1 met |
| Stream B complete | Stream E entry gate item 2 met |
| Stream E Day 1 entry gate verified | Begin E-1 work |
| Stream E complete | System ready for external operator onboarding |

---

## Completion Definition

Phase 5 is complete when:
1. `golden-path` job green on Windows and Linux on a clean install
2. `run_failure_latest.json` present on every hard failure; absent on healthy run
3. Smoke CI detects broken package path explicitly (preflight fails, not silent)
4. Smoke CI detects shadowed-module correctly on both platforms
5. All existing CI jobs still green (no regressions)
6. macOS best-effort result recorded

Phase 5 complete = Stream E green = system ready for external operator onboarding.
