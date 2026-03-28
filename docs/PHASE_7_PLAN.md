# Phase 7 — Skill Pilot & Endgame Closure

> **Status**: Approved -- awaiting Phase 6 completion
> **Effort estimate**: 2–4 weeks (GO path) or 1–2 weeks (NO-GO path)
> **Repo**: `E:\Code\SOP\quant_current_scope`
> **Prerequisite**: Phase 6 gate fully checked; `phase6_skill_pilot_decision.md` present
> **Gate**: ENDGAME success criteria met

---

## Context: What Phase 6 established

- Release command set green on 3 consecutive fresh runs
- `execution_deputy` and `auditor_deputy` within budget
- `docs/runbook_ops.md` split; operator docs describe one coherent surface
- `benchmark/subagent_routing_matrix.yaml` committed; routing validation passes
- Go/No-go decision on skill pilot in `docs/decisions/phase6_skill_pilot_decision.md`

Phase 7 has two paths depending on the Phase 6 Go/No-go decision.

---

## Path selection

Read `docs/decisions/phase6_skill_pilot_decision.md` before starting Phase 7.

| Decision | Phase 7 scope |
|---|---|
| **GO** | 7.1 Skill Pilot + 7.2 Endgame Closure |
| **NO-GO** | 7.1 skipped; 7.2 Endgame Closure only |

If NO-GO: Phase 7 is the final stabilization and ENDGAME verification pass.
If GO: Phase 7 proves or disproves value of one narrow skill path, then closes ENDGAME.

---

## ENDGAME alignment

From ENDGAME.md Section 11, the endgame is reached when:
- human can explain system in 5 minutes without phase-specific examples
- strategy and engineering loops are both explicit
- planner enters from small packets by default
- worker output reliably becomes planner truth
- new surfaces integrated or retired instead of silently accumulating
- same truth vocabulary works across repos
- status stays thin
- repeated misses become clearer guardrails
- models need less guidance over time, not more

Phase 7 is the last phase. It must verify each criterion is met, not just asserted.

---

## Current State (as-inspected at Phase 6 completion)

| Area | What exists after Phase 6 | What is missing |
|---|---|---|
| Skill pilot | `skill_resolver.py`, `validate_skill_activation.py`, skill registry | No execution semantics on any pilot path |
| ENDGAME verification | All phases 1-6 complete | No systematic check that ENDGAME criteria are met |
| Truth vocabulary | `bridge_contract`, `planner_packet`, `orchestrator_state` all live | Not verified to work identically across repos |
| Surface retirement | `ArtifactLifecycleManager` exists | No audit of surfaces added in phases 1-6 |
| Operator experience | Docs aligned, kernel reliable | No end-to-end 5-minute explainability verification |

---

## Sequencing Rule

```
7.1 Skill Pilot (GO only)  -->  7.2 Endgame Closure
```

If NO-GO: start directly at 7.2.

---

## Worker Guidance

**Plan path**: `E:\Code\SOP\quant_current_scope\docs\PHASE_7_PLAN.md`

**Approval status**: Approved. All gap patches factually grounded. Phase 6 must fully close before implementation begins.

### Key file locations (inherited from Phase 6)

| File | Note |
|---|---|
| `docs/decisions/phase6_skill_pilot_decision.md` | Determines GO/NO-GO path |
| `scripts/utils/skill_resolver.py` | Skill resolution logic |
| `scripts/validate_skill_activation.py` | Skill activation validator |
| `docs/context/skill_activation_latest.json` | Current skill activation state |
| `benchmark/subagent_routing_matrix.yaml` | Deputy routing (now committed) |
| `docs/context/planner_packet_current.md` | Fresh entry point (ENDGAME check) |

---

## Item 7.1 — Skill Execution Pilot (GO path only)

### Prerequisite: phase6_skill_pilot_decision.md says GO

### Skip condition

If NO-GO: skip this item. Document skip in one-line note. Proceed to 7.2.

### Step 1: Pilot setup

**7.1-G1 resolved**: `phase6_skill_pilot_decision.md` must contain these minimum fields
before Phase 7 can begin (defined in Phase 6.3-G2):
- `decision`: GO or NO-GO
- `candidate_skill`: name of the approved pilot skill
- `value_metric`: measurable criterion (e.g. "reduces loop latency by >10%")
- `rollback_path`: description of how to disable pilot without side effects

Use exactly the candidate and value metric approved in `phase6_skill_pilot_decision.md`.

Hard limits (from `next_phase_plan.md`):
- One narrow declarative skill only
- Execution semantics only for that pilot path
- Existing governance gates remain authoritative
- Rollback path exists before first pilot run
- Core kernel flow works with no skill execution enabled
- No automatic promotion of pilot output to production

### Step 2: Execution semantics

- Extend `skill_resolver.py` to resolve and invoke the pilot skill.
  **7.1-G2 resolved**: Invocation = subprocess call with JSON stdout output;
  output is advisory only (logged, not written to any governance artifact).
  Scope: one new function `invoke_pilot_skill(skill_name, ctx) -> dict | None`.
- Wire into `LoopOrchestrator` as optional post-body hook
  (called only when `ctx.skill_pilot_enabled` is True).
  **Pilot output path**: Advisory output must be written OUTSIDE rollback scope
  (same Option A rule as bridge/planner/state). Use a path not covered by
  the rollback snapshot glob, e.g. `docs/context/pilot_output_latest.json`.
  If pilot output is intentionally revertable on HOLD, document that explicitly.
  Resolve at 7.1 Step 2 implementation time.

  **7.1-G3 resolved**: Hook runs AFTER `OrchestratorStateWriter.write()`,
  BEFORE `TierAwareCompactor.run()`. Has its own exception guard:
  pilot failure is non-fatal (logged to stderr; run continues normally).
  Canonical order: bridge -> planner -> state -> **pilot hook** -> compaction -> return.
- Governance gates remain authoritative; skill output is advisory only
- `skill_pilot_enabled: bool = False` on `LoopCycleContext` (opt-in)
- `--skill-pilot` flag on `run_loop_cycle.py` and `src/sop/__main__.py`

### Step 3: Value measurement

Measure against value metric from `phase6_skill_pilot_decision.md`.
Record in `docs/decisions/phase7_skill_pilot_results.md`:
- Value metric: measured vs target
- Governance gates: still passing?
- Core kernel without `--skill-pilot`: still green?
- Rollback verified: pilot disabled without side effects?

### Step 4: Tests

`tests/test_skill_pilot.py` — 6 tests:
- `test_skill_pilot_disabled_by_default`
- `test_kernel_flow_unchanged_without_pilot_flag`
- `test_pilot_skill_resolves_correctly`
- `test_governance_gates_still_pass_with_pilot`
- `test_pilot_rollback_leaves_no_side_effects`
- `test_pilot_value_metric_recorded` -- checks file exists + required fields present;
  human reviews the measured value (not a code-level assertion of metric outcome)

### Files to create
```
docs/decisions/phase7_skill_pilot_results.md
tests/test_skill_pilot.py
```

### Files to modify
```
src/sop/scripts/orchestrator.py         # optional skill-pilot post-body hook
src/sop/scripts/run_loop_cycle.py       # --skill-pilot flag
src/sop/scripts/loop_cycle_context.py  # skill_pilot_enabled: bool = False
src/sop/__main__.py                     # forward --skill-pilot
scripts/utils/skill_resolver.py         # pilot skill invocation
  # CC-G2: skill_resolver.py is a D-183 dual-surface script.
  # Both src/sop/scripts/utils/skill_resolver.py AND scripts/utils/skill_resolver.py
  # must be modified together; test_script_surface_sync.py will catch drift.
```

### Done criteria
- [ ] Pilot invoked end-to-end with `--skill-pilot` flag
- [ ] Governance gates pass with pilot enabled
- [ ] Core kernel green without `--skill-pilot` (default)
- [ ] Rollback verified: disabling pilot leaves no side effects
- [ ] Value metric measured and recorded
- [ ] `tests/test_skill_pilot.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 7.2 — Endgame Closure

### Prerequisite: 7.1 complete or skipped with documented NO-GO

### Step 1: ENDGAME criterion verification

For each criterion, produce a one-line pass/fail verdict with evidence.
Record in `docs/decisions/endgame_verification.md`.

| Criterion | Verification method |
|---|---|
| Human explains system in 5 minutes | Write 5-minute explainer; check for phase-specific jargon |
| Strategy + engineering loops explicit | Check ENDGAME.md Sections 3-4 against actual artifacts |
| Planner enters from small packets | `planner_packet_current.md` is sole entry; no whole-repo read |
| Worker output becomes planner truth | `bridge_contract` + `planner_packet` written after every run |
| Surfaces integrated or retired | Run `ArtifactLifecycleManager.scan()`; verify no unretired surfaces |
| Same truth vocabulary across repos | **7.2-G2 resolved**: Narrow to local repo check only.
  Verify `bridge_contract_current.md`, `planner_packet_current.md`,
  `orchestrator_state_latest.json`, `exec_memory_packet_latest.json` field names
  match `KERNEL_ACTIVATION_MATRIX.md` entries for `quant_current_scope`.
  Cross-repo check (Eureka, ToolLauncher) is deferred -- cannot access those repos mechanically. |
| Status stays thin | `docs/context/` count within `--max-context-artifacts` limit |
| Repeated misses → clearer guardrails | Check `docs/lessonss.md` (double-s; actual filename).
  Also check `docs/context/lessons_auditor_latest.md` and
  `docs/context/lessons_worker_latest.md`. All three are authoritative.
  **7.2-G1**: Do NOT reference `docs/lessons.md` (does not exist). |
| Models need less guidance over time | **Human review only** -- no mechanical test.
  Review Phase 1-7 plan lengths and prompt density trend. Mark PASS if trend is decreasing;
  FAIL if later phases require more prompt scaffolding than earlier phases. |

### Step 2: Surface retirement audit

Run `ArtifactLifecycleManager.scan()` and review:
- Any `active` artifact that should be merged into another surface
- Any surface added in Phases 1-6 that is now redundant
- Any `orphaned` artifact not yet archived

Document findings in `endgame_verification.md` under "Surface Audit".
For each finding: keep / merge / retire decision with one-line rationale.

### Step 3: Cross-repo vocabulary check

**7.2-G3 resolved**: `SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md` confirmed present at
`E:\Code\SOP\SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`. Include in vocabulary check.
**Test location**: File lives above `quant_current_scope`. Test must locate it via
`Path(__file__).parent.parent.parent / "SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md"`
or via an environment variable. Resolve at test-write time.

Verify `bridge_contract`, `planner_packet`, `orchestrator_state`, `exec_memory_packet`
field names match `KERNEL_ACTIVATION_MATRIX.md` and `SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`.
Document any drift in `endgame_verification.md` under "Vocabulary Drift".

### Step 4: Final release freeze

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
python scripts/run_fast_checks.py --repo-root .
python -m pytest -q
python scripts/validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .
```

**7.2-G6**: Before accepting command 6 as green, verify
`benchmark/subagent_routing_matrix.yaml` is committed (Phase 6 CC-G1 resolved).
On a fresh clone, `git ls-files benchmark/subagent_routing_matrix.yaml` must return the file.

All 6 commands must pass on 3 consecutive fresh runs after endgame verification.
Record run dates, Python version, and test count in `endgame_verification.md`.

### Step 5: Tests

`tests/test_endgame.py` — 6 tests:
- `test_planner_packet_is_sole_entry_point`
- `test_bridge_contract_written_after_every_run`
- `test_context_count_within_max_artifacts_limit`
- `test_truth_vocabulary_consistent_with_kernel_matrix`
- `test_no_orphaned_artifacts_in_context_dir` -- `@pytest.mark.integration`;
  requires post-run `docs/context/` state; uses fixture dir on CI
- `test_final_release_commands_all_pass` (integration)

### Files to create
```
docs/decisions/endgame_verification.md
tests/test_endgame.py
```

### Done criteria
- [ ] All 9 ENDGAME criteria verified with pass/fail verdict and evidence
- [ ] Surface retirement audit complete; no unretired redundant surfaces
- [ ] Cross-repo vocabulary drift documented (zero drift target)
- [ ] Final release freeze: all 6 commands pass on 3 consecutive fresh runs
- [ ] `tests/test_endgame.py` passes (6 tests)
- [ ] All existing tests still pass
- [ ] `docs/decisions/endgame_verification.md` committed

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|
| Skill pilot scope creeps beyond one skill | Medium | High | Hard limits from next_phase_plan.md; governance gates remain authoritative |
| ENDGAME criterion "5-minute explainability" is subjective | Medium | Low | Require written explainer reviewed by human; fails if phase-specific jargon present |
| Surface retirement audit finds many unretired surfaces | Medium | Medium | Each finding needs keep/merge/retire decision; document not delete |
| Cross-repo vocabulary drift discovered late | Low | Medium | Check early in 7.2 Step 3; fix before final freeze |
| Final release freeze fails on first run | Low | High | Phase 6 already established 3-run green baseline; recheck flake list |
| GO pilot produces no measurable value | Medium | Low | Document clearly; NO-GO conclusion is a valid and complete outcome |

---

## Phase 7 Gate (ENDGAME)

The system has reached the ENDGAME when all of the following are true:

**Item 7.1 — Skill Pilot (if GO)**
- [ ] Pilot invoked end-to-end; governance gates pass; rollback verified
- [ ] Value metric measured and recorded in `phase7_skill_pilot_results.md`
- [ ] `tests/test_skill_pilot.py` passes (6 tests)

**Item 7.1 — Skill Pilot (if NO-GO)**
- [ ] NO-GO documented; 7.1 skipped; rationale in implementation log

**Item 7.2 — Endgame Closure**
- [ ] All 9 ENDGAME criteria: pass/fail verdict with evidence
- [ ] Surface retirement audit complete
- [ ] Cross-repo vocabulary: zero drift or documented exceptions
- [ ] Final release freeze: 6 commands pass on 3 consecutive fresh runs
- [ ] `endgame_verification.md` committed
- [ ] `tests/test_endgame.py` passes (6 tests)

**Cross-cutting**
- [ ] All existing tests still pass
- [ ] `pytest -m integration` passes
- [ ] Human signs off on 5-minute system explainer.
  **7.2-G7 process**: Written doc, max 500 words. Cold read by human who has not
  read it before. Pass criteria: (a) no phase-specific jargon, (b) system purpose
  and loop structure clear in one read. Async written review is sufficient.
- [ ] ENDGAME.md Section 11 criteria: all met per `endgame_verification.md`
