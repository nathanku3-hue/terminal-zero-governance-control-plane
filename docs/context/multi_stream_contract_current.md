# Multi-Stream Contract
Generated: 2026-03-29
Phase: phase-5-release-readiness

## Active Stream
**Stream M — Deterministic Release Gate** (P0, critical path)
- Scope: 3 consecutive fresh runs of 5-step verification sequence; finalize `docs/decisions/phase5_architecture.md` Draft → Accepted.
- Owner: Worker/executor
- Deliverable: `phase5_architecture.md` status = Accepted + 3-run evidence block appended.
- Blocking: Phase 5 close gate cannot be declared until M is green.

## Deferred Streams
**Stream L — Current Truth Surfaces** (completing, unblocked)
- Status: All 6 truth surfaces instantiated. `SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md` completing.
- Deferred item: None — L is in final verification.

**Stream N — docs/context/ Hygiene** (completing, unblocked)
- Status: README.md classification, .gitignore update, and archive in progress.
- Deferred item: None — N is in final verification.

**Phase 6 Streams** (deferred until Phase 5 close gate met):
- Stream A: Kernel stabilization (P0) — entry blocked until Phase 5 green.
- Stream B: Memory reduction (P1) — blocked until A green.
- Stream C: Tiered memory (P2) — blocked until A green.
- Stream D: Skill pilot (P3) — blocked until A + B + C green.

## Stream Dependencies
- M depends on: Pre-execution steps complete (DONE), Ph5-G complete (DONE), Stream L truth surfaces instantiated (DONE).
- N depends on: Pre-execution steps complete (DONE).
- Phase 6 Stream A depends on: Phase 5 close gate (L + M + N all green).
- Phase 6 Stream B depends on: Phase 6 Stream A green.
- Phase 6 Stream C depends on: Phase 6 Stream A green.
- Phase 6 Stream D depends on: Phase 6 Streams A + B + C all green.

## Shared Integration Success Criteria
- [ ] `python -m pytest -q` passes in <60s with zero unexpected failures across all three M.1 runs.
- [ ] `python scripts/check_fail_open.py` exits 0 on all three M.1 runs.
- [ ] `python scripts/check_schema_version_policy.py` exits 0 on all three M.1 runs.
- [ ] `python -m sop --help`, `python scripts/startup_codex_helper.py --help`, `python scripts/run_loop_cycle.py --help` all exit 0 on all three runs.
- [ ] `TestByteIdentityContract` green (8 files in `DUAL_COPY_FILES`).
- [ ] `_read_spec_phase('.')` returns `"phase-5-release-readiness"`.
- [ ] `SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md` has zero unchecked/undisposed items.
- [ ] `docs/decisions/phase5_architecture.md` status = Accepted.

## Owner/Handoff Path per Stream
- Stream L → Worker completes SPEC checklist → surfaces handed to planner packet for Phase 6 entry.
- Stream M → Worker executes 3 runs, records evidence → PM/CEO reviews architecture doc Accepted status.
- Stream N → Worker classifies files + updates .gitignore + archives → surfaces handed off as clean baseline for Phase 6.
- Phase 6 → Entry gate: `docs/next_phase_plan.md` readable + all Phase 5 gates green → Phase 6 Stream A begins.
