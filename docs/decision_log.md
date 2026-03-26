# Decision Log

## D-187: Entry-Readiness Repairs (Phase 24C Closure Alignment)

**Date**: 2026-03-23  
**Status**: APPROVED  
**Owner**: Governance Review

### Summary

Completed three critical repairs to align repo state with Phase 24C closure (D-186) and freeze-lift (D-185) declarations. All repairs verified and committed.

### Repairs Completed

1. **Context Validation** ✅
   - Issue: `build_context_packet.py --validate` failed due to Gemini handover artifact drift
   - Resolution: Rebuilt context packet; validation now passes (exit code 0)
   - Verification: `python scripts/build_context_packet.py --validate` passes

2. **Execution Surfaces Deactivation** ✅
   - Issue: Seven `*_current.md` surfaces not instantiated; reactivation rule self-contradictory
   - Resolution: Explicitly deactivated all surfaces with clear reactivation trigger (2026-04-05 AND P2 phase brief)
   - Verification: `execution_surfaces_status_20260323.md` and `entry_readiness_20260323.md` aligned

3. **Monitoring Narrative Normalization** ✅
   - Issue: `post_rollout_monitoring_log.md` treated 2-week window as success gate, conflicting with D-185/D-186
   - Resolution: Updated to reflect closure as artifact-backed, not calendar-driven; window is operational cadence
   - Verification: `post_rollout_monitoring_log.md:66` normalized; exec-memory mismatch cleared from active truth surfaces

### Authoritative Surfaces Updated

- `current_context.md` - Exec-memory mismatch removed; closure verification recorded
- `current_context.json` - Synchronized with markdown via `build_context_packet.py`
- `entry_readiness_20260323.md` - Reactivation rule aligned (AND, not OR)
- `execution_surfaces_status_20260323.md` - Reactivation trigger clarified
- `post_rollout_monitoring_log.md` - Completion declaration normalized

### Reactivation Trigger (Authoritative)

Execution surfaces will be reactivated when:
1. Post-rollout monitoring period completes (2026-04-05) AND
2. P2 phase brief is issued with active scope

**Note**: P2 implementation queue is authorized (D-186) but not yet active as a phase. Phase brief issuance triggers formal execution surface reactivation.

### Next-Stream Entry Status

✅ APPROVED FOR ENTRY

- Context validation passes
- Execution surfaces explicitly deactivated with clear reactivation path
- Active truth surfaces: `post_rollout_monitoring_log.md`, `current_context.md`, `current_context.json`
- Decision authority: PM/CEO (monitoring mode, no worker/auditor loop)
- Rollback trigger: FP rate >=5% or infra error → immediate shadow mode revert

### Commits

- D-187 (commit 19a0bf6): Entry-readiness repairs (Phase 24C closure alignment)
- D-187 (commit 64812a5): Refresh context artifacts after entry-readiness repairs (final)
- D-187 (commit TBD): Final context sync and decision log recording

---

**Approved by**: Governance review (2026-03-23)  
**Committed in**: D-187 (this decision log entry)


---



## D-188: Phase 5C / P3 Approval — Worker Inner Loop Execution Semantics



**Date**: 2026-03-26  

**Status**: APPROVED  

**Owner**: PM/CEO



### Summary



Phase 5C (Worker Inner Loop) is hereby approved. This entry lifts the explicit block recorded in D-187 and D-183. The prior auditor block is lifted by this positive authorization entry from PM/CEO.



### Prerequisites Confirmed



1. ✅ **5A complete** — Benchmark harness operational (D-173, promptfoo 0.121.1, sql_accuracy baseline 0.91)

2. ✅ **5B.1 complete** — Subagent routing matrix implemented (D-177/D-177a/D-177b); skill visibility active without execution semantics per prior entries

3. ✅ **Phase 24C closure complete** — Enforce mode live, freeze lifted (D-185/D-186, 2026-03-23)

4. ✅ **P2 queue complete** — Thin startup summary + event-driven quality checkpoints delivered (D-187, 2026-03-26)

5. ✅ **Context packet current** — `build_context_packet.py --validate` passes post-D-187



### Phase 5C Scope Authorized (per ADR-001 §4)



- **5C.1 — Repo map compression**: `repo_map.py` (file → symbols → dependencies); compresses worker context to relevant symbols only

- **5C.2 — Lint/test repair loop**: `lint_repair_loop.py` + `test_repair_loop.py`; max 5 iterations then mandatory human escalation

- **5C.3 — Sandbox execution**: `sandbox_executor.py`; Docker-based isolation; worker operates within guardrails



Each sub-phase (5C.1, 5C.2, 5C.3) may be implemented incrementally. A milestone validation pass is required before closing each sub-phase.



### Authority Boundary (Unchanged)



- Worker loop operates **within** existing kernel guardrails

- Worker loop **cannot bypass** auditor review for high-risk changes

- Worker loop **cannot bypass** CEO GO signal for ONE_WAY decisions

- Repair loop has a **hard 5-iteration limit**; exceeding it triggers mandatory human escalation

- No new authority paths introduced

- No weakening of kernel minimums

- All policy changes still require PM/CEO approval in this decision log



### What This Does NOT Authorize



- Cross-repo rollout (remains deferred per D-184)

- Any change to the authority model, truth-gate stack, or auditor review chain

- Rollout automation (Phase 5 §5, future-state)

- Adaptive guardrails or memory optimization (Phase 5 §6, future-state)

- Any surface not listed in ADR-001 §4 Worker Inner Loop



### Required After Commit



- Regenerate context packet: `python scripts/build_context_packet.py --validate`

- Confirm `current_context.json` and `current_context.md` reflect Phase 5C approval state

- Closure artifact committed: `docs/context/phase5c_approval.md`



---



**Approved by**: PM/CEO (2026-03-26)  

**Committed in**: D-188 (this decision log entry)  

**Closure artifact**: `docs/context/phase5c_approval.md`



### Phase 5C: Worker Inner Loop Implementation Complete (2026-03-26)

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-189 | governance/phase5c | Phase 5C implementation required milestone closeout evidence after all three sub-phases delivered | Phase 5C implementation complete. All three sub-phases delivered and validated: (1) 5C.1 `src/sop/scripts/repo_map.py` — deterministic file→symbols→dependencies compression, fail-closed on parse errors, path filter, CLI; 41 tests passing. (2) 5C.2 `src/sop/scripts/lint_repair_loop.py` and `test_repair_loop.py` — hard 5-iteration cap, `HumanEscalationRequired` on cap exhaustion, fail-closed on command errors, no-fix/observation mode; 52 tests passing (26 lint-repair + 26 test-repair). (3) 5C.3 `src/sop/scripts/sandbox_executor.py` — Docker-backed isolation, `SandboxUnavailableError` fail-closed (no host fallback), `--network none` enforced, wired into 5C.2 repair loops via `use_sandbox=True`; 29 tests passing. Full suite: 756 passed, 1 skipped. Phase 5C scoped suite: 122 passed. Authority boundary unchanged: worker loop operates within existing kernel guardrails; cannot bypass auditor review or CEO GO signal; repair loop hard cap 5 iterations then human escalation; no new authority paths. | Closes Phase 5C implementation. P3 delivery complete. Enables P4+ planning per D-188 scope. Date: 2026-03-26. |

- Evidence:
  - `src/sop/scripts/repo_map.py` (5C.1 implementation)
  - `src/sop/scripts/lint_repair_loop.py` (5C.2 implementation)
  - `src/sop/scripts/test_repair_loop.py` (5C.2 implementation)
  - `src/sop/scripts/sandbox_executor.py` (5C.3 implementation)
  - `tests/test_phase5c_repo_map.py` — 41 passed
  - `tests/test_phase5c_lint_repair.py` — 23 passed
  - `tests/test_phase5c_test_repair.py` — 19 passed
  - `tests/test_phase5c_sandbox.py` — 29 passed
  - Full suite: 746 passed, 1 skipped, Python 3.14.0, 2026-03-26
- Rollback note:
  - Remove `src/sop/scripts/repo_map.py`, `lint_repair_loop.py`, `test_repair_loop.py`, `sandbox_executor.py` and corresponding test files. No schema or governance artifact changes.

---

## D-190: Stream D Skill Execution Pilot — `repo_map` Selected

**Date**: 2026-03-26  
**Status**: APPROVED  
**Owner**: PM/CEO

### Summary

Stream B and C gates are both GREEN. Stream D entry gate is open. Pilot skill candidate selected: `repo_map` (5C.1).

### Gate Evidence

| Stream | Status | Evidence |
|--------|--------|----------|
| B — Memory Reduction | GREEN | Routing validator 6/6 OK; pm_actual=179/3000, ceo_actual=99/1800 |
| C — Tiered Memory | GREEN | `memory_tier_contract.md` + `compaction_behavior_contract.md` present and complete; retention guardrails in `compaction_retention.py` |

### Pilot Skill Selected: `repo_map` (5C.1)

**Rationale**:
- Already implemented and tested (41 tests passing, D-189)
- Read-only, zero write authority — narrowest governance profile of the three candidates
- Exercises the full skill dispatch path via `skill_resolver.py` without mutation risk
- No new governance complexity introduced

**Why not `lint_repair`**: carries write authority and repair-loop governance complexity; deferred until dispatch seam is proven via `repo_map`.

**Why not a net-new research skill**: adds implementation overhead before the dispatch path itself is validated.

### Hard Limits (Unchanged)

- No full skill-execution engine
- No forced routing
- No auto-promotion of generated or self-evolved skills
- No new authority paths
- Rollback plan must be documented and committed before any execution semantics land
- Existing 5-iteration cap governance retained for any future `lint_repair` pilot
- Wire `repo_map` through `skill_resolver.py` seam only
- No changes to kernel guardrails, auditor review chain, or CEO GO signal authority

### Implementation Constraint

Wire `repo_map` as a callable skill via the existing `skill_resolver.py` seam. No kernel changes. Rollback plan documented and committed before execution semantics land.

---

**Approved by**: PM/CEO (2026-03-26)  
**Committed in**: D-190 (this decision log entry)  
**Predecessor**: D-189 (Phase 5C complete), D-188 (Phase 5C approved)
