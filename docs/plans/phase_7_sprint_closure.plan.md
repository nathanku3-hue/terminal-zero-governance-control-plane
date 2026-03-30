# Phase 7 — Sprint Closure Gate

> **Status**: BLOCKED — do not begin until all 6 phases complete
> **Date**: 2026-03-30
> **Type**: Terminal gate — no new code, no new features
> **Purpose**: Mechanically verify the 6-phase sprint is fully closed and emit a valid ClosurePacket

---

## What This Phase Does

Phase 7 is a single terminal verification pass. It produces no new artifacts beyond the
closure packet itself. It declares the 6-phase sprint done or explicitly lists what blocks
closure.

This is NOT a new work phase. If any check fails, the failing phase is the blocker —
Phase 7 does not fix anything, it surfaces what is still open.

---

## Entry Condition

All six prior phases must be fully closed:

| Phase | Plan | Entry check |
|---|---|---|
| 2 | `phase_2_execution_hardening.plan.md` | All 21 active tests pass; `check_fail_open.py` baseline committed; scan manifest symmetric |
| 3 | `phase_3_checklist_matrix.plan.md` | Phase A + Phase B complete; `loop_readiness_latest.json` live; 6 checklist tests pass |
| 4 | `phase_4_navigation_boundary.plan.md` | Stream A: zero absolute paths, templates documented, onboarding checklist fixed; Stream D: gap audit passed, cross-references clean |
| 5 | `phase_5_golden_path_proof.plan.md` | `golden-path` CI green on Windows + Linux; `preflight-failure-detection` + `shadowed-module-smoke` green |
| 6 | `phase_6_post_hardening_integration.plan.md` | All 6 tracks complete; 0 test skips; `skills_status: ACTIVE` in CI; schema version policy CI enforced |

---

## Closure Checklist (machine-checkable)

### C-1: Test Suite
- [ ] `pytest tests/test_hardening.py tests/test_checklist_matrix.py tests/test_cli_script_parity.py -q` → 0 failures; 1 expected skip permitted (`test_run_output_parity` — explicitly marked `pytest.skip`, pending healthy-path fixture; this skip persists by design through Phase 6)
- [ ] `pytest tests/test_hardening.py --collect-only -q` → 81 collected, 0 skips, 0 failures
- [ ] 1 real failure in `test_run_loop_cycle.py` resolved (Track 3)

### C-2: Failure Artifact Contract
- [ ] `run_failure_latest.json` written on every hard failure path
- [ ] Healthy path: no `run_failure_latest.json`, no FATAL on stderr
- [ ] `failure_class` in every failure artifact matches FATAL stderr envelope
- [ ] `error_code_registry.json` coverage complete (all `failure_class` values mapped)

### C-3: CI Green
- [ ] `release-validation.yml` jobs green: `cli-smoke`, `backward-compat`, `test-suite`, `release-gate`
- [ ] `golden-path` job green on Windows + Linux
- [ ] `preflight-failure-detection` job green
- [ ] `shadowed-module-smoke` job green
- [ ] `fast-checks.yml` green on push

### C-4: Artifact Integrity
- [ ] `artifact_refs` entries contain `hash`, `content_kind`, `hash_strategy`; `mtime_utc` present
- [ ] `decision_basis_count` present in every `gate_decisions[]` entry
- [ ] Schema version policy CI check green
- [ ] `attempt_id` increments on retry
- [ ] `evaluation_outcome_source` correctly set: `"resume"` vs `"fresh"`

### C-5: Navigation + Boundary
- [ ] Scoped rg scan (operator-facing files only) returns zero absolute path matches
- [ ] `docs/context/README.md` has "Template Canonical Sources" section
- [ ] `operator_onboarding_checklist.md` has `KERNEL_ACTIVATION_MATRIX.md` as entry step 1
- [ ] All `operator_navigation_map.md` commands use valid subcommands (`sop run`, `sop validate`)
- [ ] All operator doc cross-references resolve to existing files

### C-6: Skills + Loop Readiness
- [ ] `skills_status: ACTIVE` achievable in CI via skill pilot
- [ ] `loop_readiness_latest.json` shows `routing: skills_active` when skill active
- [ ] `check_loop_readiness.py` dual copy committed; manifest entry present

### C-7: Scan Baseline
- [ ] `check_fail_open.py` passes; no new BLOCKERs
- [ ] `critical_scan_manifest.json` symmetric; no orphan entries
- [ ] `fail_open_allowlist.json` committed

### C-8: Truth Surfaces Current
- [ ] `planner_packet_current.md` reflects Phase 6 complete state
- [ ] `bridge_contract_current.md` reflects Phase 6 complete state
- [ ] `done_checklist_current.md` has no duplicate sections; all phase gates checked
- [ ] `post_phase_alignment_current.md` reflects all streams closed
- [ ] `observability_pack_current.md` shows no active drift markers

---

## Closure Packet Format

When all C-1 through C-8 checks pass, emit the following line verbatim in the
closure artifact and verify it with `validate_closure_packet`:

```
ClosurePacket: RoundID=sprint-6phase-2026-03-30; ScopeID=phases-2-3-4-5-6; ChecksTotal=<N>; ChecksPassed=<N>; ChecksFailed=0; Verdict=PASS; NextAction=System at 9-10/10 -- ready for external operator fleet onboarding
```

If any check fails:
```
ClosurePacket: RoundID=sprint-6phase-2026-03-30; ScopeID=phases-2-3-4-5-6; ChecksTotal=<N>; ChecksPassed=<N>; ChecksFailed=<N>; Verdict=BLOCK; OpenRisks=<list failing checks>; NextAction=<name the blocking phase>
```

Validate with:
```powershell
.venv\Scripts\python -m sop.tools.validators.closure_packet_tool --packet "<packet line>" --require-open-risks-when-block true --require-next-action-when-block true
```

---

## Closure Artifact

Write to: `docs/context/closure_packet_sprint_6phase.md`

**This file does not exist at Phase 7 entry — Phase 7 creates it. Its absence is not a blocker.**

Contents:
```markdown
# Sprint Closure — 6-Phase Fix-Path to 9-10/10
Date: <date>
Verdict: PASS | BLOCK

## Checks Summary
<table of C-1 through C-8 with PASS/FAIL per item>

## ClosurePacket
ClosurePacket: RoundID=...; ...

## What Changed
- Phase 2: 21 active hardening tests; failure artifacts on every hard failure
- Phase 3: loop readiness + checklist matrix
- Phase 4: boundary sealing + navigation map
- Phase 5: golden path CI on Windows + Linux
- Phase 6: hash stability, schema version CI, 0 skips, skill pilot, retry loop, checkpoint resume

## System State After Sprint
Fix-path to 9-10/10 complete. External operator fleet onboarding ready.
```

---

## What Phase 7 Does NOT Do

- Does not fix failing checks — routes back to the blocking phase
- Does not introduce new code, tests, or CI jobs
- Does not modify any existing plan
- Does not change the `needs:` list on `publish-pypi`
- Does not re-open any deferred item

---

## Completion Definition

Phase 7 is complete when:
1. All C-1 through C-8 checks pass
2. `closure_packet_sprint_6phase.md` written to `docs/context/`
3. `ClosurePacket` line validates with `Verdict=PASS`
4. Truth surfaces (C-8) all current

Phase 7 complete = 6-phase sprint closed = system ready for external operator fleet onboarding.
