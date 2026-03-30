# Phase 6 — Post-Hardening Integration

> **Status**: BLOCKED — do not begin until Phase 2 + Phase 4 + Phase 5 all complete
> **Date**: 2026-03-30
> **Roadmap alignment**: Fix-path to 9-10/10
> **Entry condition**: Stream B (Phase 2) + Stream A (Phase 4) + Stream E (Phase 5) all green

---

## Strategic Context

Phases 2-5 deliver the fix-path to 8/10. Phase 6 pushes to 9-10/10 by resolving all items
explicitly deferred from Phase 2 and the SPEC_TO_MULTISTREAM Phase 6+ deferrals.

## Known Pre-existing Test State (read before touching any code)

Full suite (`pytest -q`) as of 2026-03-30: **528 passed, 2 skipped, 508 errors**.
The 508 errors are collection/fixture errors (not test failures) in:
- `test_run_auditor_review.py`
- `test_compaction_hardening.py`
- `test_run_loop_cycle.py`
- `test_validate_worker_reply_packet.py`

These are pre-existing infrastructure issues not introduced by Phases 2-5.

**1 real FAILED test**: `test_run_loop_cycle.py::test_run_loop_cycle_skip_phase_end_success_and_overdue_ledger_flag`
-- assertion error on step name ordering. Track 3 must fix this first.

Scoped suite (`pytest tests/test_hardening.py tests/test_checklist_matrix.py tests/test_cli_script_parity.py -q`):
**117 passed, 1 skipped** -- this is the known-good baseline.

---

**Entry requirements (all must be confirmed green):**
1. Phase 2 complete: 21 active tests pass, scan baseline committed, failure artifacts correct
2. Phase 4 complete: Stream A boundary sealing + Stream D navigation map
3. Phase 5 complete: Stream E golden path CI green on Windows + Linux
4. Phase 3 Phase B complete: `loop_readiness_latest.json` integrated with live H-5 output

---

## What Already Exists (Baseline)

| Asset | State | Note |
|---|---|---|
| `artifact_refs: {name: mtime_utc}` | Shipped in Phase 2 | Phase 6 adds hash/content_kind/hash_strategy |
| `attempt_id` in `_failure_reporter.py` | Shipped in Phase 2 | Phase 6 wires to retry loop |
| `evaluation_outcome_source` | Shipped in Phase 2 | Phase 6 wires to checkpoint resume |
| `failure_origin`, `spec_phase` | Shipped in Phase 2 | No change in Phase 6 |
| Schema version policy | Deferred from Phase 2 | Net-new CI check in Phase 6 |
| `error_code` registry | Deferred from Phase 2 | Net-new in Phase 6 |
| `decision_basis_count` | Deferred from Phase 2 | Net-new in Phase 6 |
| 3 skipped tests | Present at Phase 5 close | Phase 6 resolves to 0 |
| Skill pilot (`skills_status: ACTIVE`) | Not yet achievable in CI | Net-new in Phase 6 |

---

## Scope Boundary

| In Phase 6 | Deferred / Out of scope |
|---|---|
| Artifact hash stability (hash/content_kind/hash_strategy in artifact_refs) | Hosted autonomous agent platform |
| Schema version policy CI enforcement | Consumer chat product features |
| `error_code` registry committed | Plugin marketplace |
| `decision_basis_count` in gate_decisions[] | Zero-human autopilot |
| Kernel stabilization: 0 test skips (was 3 at Phase 5 close) | Cross-repo rollout automation |
| Skill pilot gate: `ACTIVE` in CI | Full operator fleet productization |
| Retry loop + `attempt_id` increment | |
| Checkpoint resume + `evaluation_outcome_source` | |

---

## Track 1 — Artifact Hash Stability
*(Phase 2 deferred: "Full hash/content_kind/hash_strategy in artifact_refs")*

- [ ] **Day 1 pre-check**: Read `_build_artifact_refs` implementation in `run_loop_cycle.py`.
      Note: `hashlib` is already imported at line 4 -- hash fields may be partially
      scaffolded. Confirm whether `hash`, `content_kind`, `hash_strategy` are already
      present in the output. If present, Track 1 scope is test-only. If absent, implement.
- [ ] Add `hash`, `content_kind`, `hash_strategy` fields to `artifact_refs` entries in
      `loop_cycle_summary_latest.json`
- [ ] Implement in `run_loop_cycle.py` -- additive; `mtime_utc` remains
- [ ] Add `test_artifact_refs_hash_fields_present`
- [ ] Update `run_failure_latest.schema.json` if `artifact_refs` appears there
- [ ] Remove Phase 2 code comment "Phase 3 adds hash" from write site

## Track 2 — Schema Version Policy CI
*(Phase 2 deferred: "Schema version policy CI enforcement" + "error_code registry")*

- [x] ALREADY DONE: `error_code_registry.json` committed at `docs/context/schemas/` with
      5 codes (E001-E005) mapping `failure_class` values to codes and recoverability.
- [ ] Verify all `failure_class` values in `_failure_reporter.py` have corresponding
      entries in `error_code_registry.json` (currently E001-E005; confirm coverage is complete)
- [ ] Add `decision_basis_count` to every `gate_decisions[]` entry
- [ ] Add CI check: schema version mismatch in any artifact = CI fail
- [ ] Add `test_schema_version_policy_ci_enforcement`
- [ ] Add `test_decision_basis_count_present_in_gate_decisions`

## Track 3 — Kernel Stabilization
*(Phase 5 SPEC checklist: "Phase 6 will reduce test skip count from 3 toward 0")*

Current skip baseline: **2 skipped** (full suite) / **1 skipped** (scoped suite).
Note: planner_packet recorded "3 skipped at Phase 5 close" -- current measured state is 2
(Phase 2-4 work removed one skip).

- [ ] **First action**: fix 1 real FAILED test:
      `test_run_loop_cycle.py::test_run_loop_cycle_skip_phase_end_success_and_overdue_ledger_flag`
      (assertion error on step name ordering -- must be fixed before targeting 0 skips)
- [ ] Identify all remaining skipped tests (current: 2 full suite / 1 scoped)
- [ ] For each skip: document reason, implement fix, remove skip marker
- [ ] Confirm `pytest tests/test_hardening.py tests/test_checklist_matrix.py tests/test_cli_script_parity.py -q` shows 0 skips
- [ ] Record fix in `docs/context/lessons_worker_latest.md`

## Track 4 — Skill Pilot Gate
*(Phase 5 SPEC checklist deferred: "skill productization")*

- [ ] Register one skill in `.sop_config.yaml` `active_skills`
- [ ] Confirm `sop run --repo-root .` produces `skills_status: ACTIVE` in summary
- [ ] Confirm `loop_readiness_latest.json` shows `routing: skills_active`
- [ ] Add `test_skill_pilot_gate_active_in_ci` to `test_checklist_matrix.py`
- [ ] Notify Stream C: Phase B finalized with real ACTIVE skill

## Track 5 — Retry Loop + attempt_id
*(Phase 2 deferred: "attempt_id requires retry loop")*

- [ ] Implement retry loop in `run_loop_cycle.py` (max retries configurable)
- [ ] Wire `attempt_id` to increment on each retry
- [ ] Add `test_attempt_id_increments_on_retry`
- [ ] Update `run_failure_latest.json` schema: `attempt_id` field now required

## Track 6 — Checkpoint Resume
*(Phase 2 deferred: "evaluation_outcome_source requires checkpoint resume")*

- [ ] Implement checkpoint resume in `run_loop_cycle.py`
- [ ] Wire `evaluation_outcome_source` to `"resume"` vs `"fresh"`
- [ ] Add `test_checkpoint_resume_sets_evaluation_outcome_source`
- [ ] Add `test_fresh_run_sets_evaluation_outcome_source_fresh`

---

## Entry Gate Checklist (verify before starting any work)

- [ ] Scoped suite green: `pytest tests/test_hardening.py tests/test_checklist_matrix.py tests/test_cli_script_parity.py -q` shows 117 passed, 1 skipped
- [ ] Broader suite pre-existing failure state documented (508 collection errors + 1 real failure in test_run_loop_cycle.py -- pre-existing, not introduced by Phase 6 work)
- [ ] Phase 2: `pytest tests/test_hardening.py --collect-only -q` shows 81 collected
- [ ] Phase 2: `check_fail_open.py` baseline committed; `critical_scan_manifest.json` committed
- [ ] Phase 2: `run_failure_latest.json` on every hard failure; healthy path clean
- [ ] Phase 4: Stream A scoped rg scan zero matches; templates documented; onboarding checklist fixed
- [ ] Phase 4: Stream D gap audit passed; navigation map cross-references clean
- [ ] Phase 5: `golden-path` CI job green on Windows + Linux
- [ ] Phase 5: `preflight-failure-detection` + `shadowed-module-smoke` CI jobs green
- [ ] Phase 3: Phase B integrated; `loop_readiness_latest.json` emitted on every run

---

## Acceptance Gates

- [ ] `artifact_refs` entries contain `hash`, `content_kind`, `hash_strategy`; `mtime_utc` still present
- [ ] `error_code` registry committed to `docs/context/schemas/`
- [ ] `decision_basis_count` present in every `gate_decisions[]` entry
- [ ] Schema version policy CI check green
- [ ] `pytest -q` shows 0 skips (was 3 at Phase 5 close)
- [ ] `skills_status: ACTIVE` achievable in CI via skill pilot
- [ ] `loop_readiness_latest.json` shows `routing: skills_active` when skill active
- [ ] `attempt_id` increments correctly on retry
- [ ] `evaluation_outcome_source` correctly set: `"resume"` vs `"fresh"`
- [ ] Scoped suite green: `pytest tests/test_hardening.py tests/test_checklist_matrix.py tests/test_cli_script_parity.py -q` shows 0 skips, 0 failures
- [ ] 1 real failure in `test_run_loop_cycle.py` fixed (Track 3 first action)
- [ ] No new regressions introduced by Phase 6 tracks
- [ ] `check_fail_open.py` still passes; no new BLOCKERs

---

## Implementation Review Rule

New logic in `sop/` package path first. `scripts/` is D-183 byte-identical sync only.
All new fields are additive -- no existing field removed or renamed.
All new tests follow `test_hardening.py` naming and fixture conventions.
Any new `*_gate.py` or `*_role.py` registered in `critical_scan_manifest.json` immediately.

---

## What This Plan Does NOT Change

- `PhaseGate.evaluate()`, `emit()`, `emit_handoff()` -- untouched
- P0/P1/P4/P5 core artifact contracts -- no existing field removed or renamed
- `mtime_utc` in `artifact_refs` -- preserved (additive only)
- `attempt_id`, `failure_origin`, `evaluation_outcome_source`, `spec_phase` already shipped -- not re-implemented

---

## Cross-Stream Coordination

| Event | Action |
|---|---|
| Phase 2 + 4 + 5 all green | Phase 6 entry gate met; begin Track 3 (kernel stabilization) first |
| Track 1 complete (hash stable) | Track 2 CI enforcement can finalize |
| Track 4 complete (skill pilot) | Notify Stream C: Phase B finalized with real ACTIVE skill |
| Phase 6 complete | System at 9-10/10; ready for operator fleet onboarding |

---

## Completion Definition

Phase 6 is complete when:
1. `artifact_refs` hash fields present; `mtime_utc` still present
2. `error_code` registry committed; schema version policy CI enforced
3. `pytest -q` shows 0 skips
4. `skills_status: ACTIVE` achievable in CI
5. `attempt_id` increments on retry
6. `evaluation_outcome_source` correctly set on resume vs fresh
7. All existing tests pass; no regressions

Phase 6 complete = system at 9-10/10 = ready for external operator fleet onboarding.
