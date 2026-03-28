# Phase 6 — Kernel Reliability & Memory Reduction

> **Status**: Draft — awaiting Phase 5 completion
> **Effort estimate**: 3–5 weeks total, three sequential workstreams
> **Repo**: `E:\Code\SOP\quant_current_scope`
> **Prerequisite**: Phase 5 gate fully checked
> **Gate**: All three items complete before Phase 7 begins

---

## Context: What Phase 5 established

- All 14 Phase 2-4 artifact families added to `_MEMORY_TIER_FAMILIES` (hot/warm/cold)
- `MEMORY_TIER_CONTRACT.md` in `docs/context/` classifying all live artifacts
- `TierAwareCompactor` running after every run; hot never compacted; cold NDJSON windows enforced
- `ArtifactLifecycleManager` with `--prune` gate and `--max-context-artifacts` overflow warning
- `docs/context/` artifact count bounded; `docs/context/archive/` gitignored

Phase 6 addresses two remaining gaps before the system is release-ready:
1. Kernel reliability: first-run green behavior required, not rerun recovery
2. Memory reduction: deputy context hotspots reduced without changing authority semantics

These correspond to Stream B from `next_phase_plan.md` (Stream A confirmed complete;
Stream C/D covered by Phases 5 and 7 respectively).

---

## ENDGAME alignment

From ENDGAME.md Section 11 (Success Criteria):
- the human can explain the system in 5 minutes without phase-specific examples
- status stays thin; models need less guidance over time, not more

From `next_phase_plan.md` Non-Negotiable Rules:
- Release-readiness claims require first-run green behavior, not rerun recovery
- Every stream must end with executable verification commands
- Runtime artifact behavior must be enforced in code, not documented only

Phase 6 closes the gap between architecturally correct (Phases 1-5) and
operationally trustworthy (release-ready, deterministic, lean).

---

## Current State (as-inspected at Phase 5 completion)

| Area | What exists after Phase 5 | What is missing |
|---|---|---|
| Release gate | `run_fast_checks.py` + pytest suite | First-run stability unverified; rerun recovery may mask flakes |
| Operator docs | `README.md`, `OPERATOR_LOOP_GUIDE.md`, `docs/runbook_ops.md` | Legacy quant/data sections mixed into active runbook |
| Deputy context | `benchmark/subagent_routing_matrix.yaml` tracks budgets | `execution_deputy` over budget (driven by `docs/runbook_ops.md`) |
| Auditor context | `docs/context/auditor_*` | `auditor_deputy` slightly over budget |
| Context measurement | `scripts/measure_context_reduction.py` exists | Not run after Phase 5 artifact additions |
| Skill pilot | `skill_resolver.py`, `validate_skill_activation.py` exist | Stream D gate: Kernel + Memory streams must be green first |

---

## Sequencing Rule

```
6.1 First-Run Reliability  -->  6.2 Memory Reduction  -->  6.3 Skill Pilot Gate
```

Each item is a strict prerequisite for the next.

---

## Worker Guidance

**Plan path**: `E:\Code\SOP\quant_current_scope\docs\PHASE_6_PLAN.md`

**Approval status**: Draft. Phase 5 must fully close before implementation begins.

### Implementation notes

- 6.1-G3: 6.2 owns the `docs/runbook_ops.md` split. 6.1 only removes legacy quant/data content from existing file.
- 6.1-G4/CC-G1: Add `!/benchmark/subagent_routing_matrix.yaml` to `.gitignore` as first step of 6.2.
- 6.2-G2: `validate_routing_matrix.py` requires positional args: `benchmark/subagent_routing_matrix.yaml .`
- 6.2-G3: `docs/loop_operating_contract.md` references `runbook_ops.md` -- must be updated after split.
- 6.2-G4: Measure actual hotspot with `measure_context_reduction.py` before any auditor reduction.
- 6.3-G1: NO-GO is explicit default. GO requires named candidate + measurable value metric.
- CC-G2: No new D-183 modules in Phase 6; sync gate unaffected.

### Implementation checklist

**6.1 First-Run Reliability**
- [ ] Release command set green on 3 consecutive fresh runs (no state carryover)
- [ ] First-run flakes fixed or converted to regression tests
- [ ] Legacy quant/data content removed from `docs/runbook_ops.md` (not split yet)
- [ ] `README.md` and `OPERATOR_LOOP_GUIDE.md` aligned to current kernel only
- [ ] `tests/test_first_run_reliability.py` passes (6 tests); integration test uses `tmp_path`

**6.2 Memory Reduction**
- [ ] `!/benchmark/subagent_routing_matrix.yaml` added to `.gitignore` (first step)
- [ ] `measure_context_reduction.py` run; post-Phase-5 baseline recorded
- [ ] `docs/runbook_ops.md` split into `runbook_ops_active.md` + `runbook_ops_reference.md`
- [ ] `docs/loop_operating_contract.md` updated to reference `runbook_ops_active.md`
- [ ] `execution_deputy` routed to `runbook_ops_active.md`; target <= 8000 tokens
- [ ] `auditor_deputy` at or under budget (target <= 8000); or documented capped exception
- [ ] `validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .` passes
- [ ] `tests/test_memory_reduction.py` passes (6 tests)

**6.3 Skill Pilot Gate**
- [ ] Go/No-go evaluation completed; NO-GO is default unless named candidate + value metric exist
- [ ] `docs/decisions/phase6_skill_pilot_decision.md` written (min: gate results, candidate, decision, reason)

**Cross-cutting**
- [ ] `benchmark/subagent_routing_matrix.yaml` committed (un-gitignored)
- [ ] `pytest -m integration` passes (integration tests use isolated tmp_path)
- [ ] All existing tests still pass

### Success criteria

Phase 6 is successful when:
- Release command set green on 3 consecutive fresh runs on fresh clone
- `execution_deputy` at or under 8000 tokens; `auditor_deputy` at or under 8000 tokens
- `benchmark/subagent_routing_matrix.yaml` is version-controlled and routing validation passes
- Go/No-go decision on skill pilot documented with minimum required content
- All 12 new tests pass (6 per workstream); all existing tests still pass
- ENDGAME: system is release-ready and deterministic; operator docs describe one coherent surface

### Implementation notes

- 6.1-G3: 6.2 owns the `docs/runbook_ops.md` split. 6.1 only removes legacy quant/data content from existing file.
- 6.1-G4/CC-G1: Add `!/benchmark/subagent_routing_matrix.yaml` to `.gitignore` as first step of 6.2.
- 6.2-G2: `validate_routing_matrix.py` requires positional args: `benchmark/subagent_routing_matrix.yaml .`
- 6.2-G3: `docs/loop_operating_contract.md` references `runbook_ops.md` -- must be updated after split.
- 6.2-G4: Measure actual hotspot with `measure_context_reduction.py` before any auditor reduction.
- 6.3-G1: NO-GO is explicit default. GO requires named candidate + measurable value metric.
- CC-G2: No new D-183 modules in Phase 6; sync gate unaffected.

### Implementation checklist

**6.1 First-Run Reliability**
- [ ] Release command set green on 3 consecutive fresh runs (no state carryover)
- [ ] First-run flakes fixed or converted to regression tests
- [ ] Legacy quant/data removed from `docs/runbook_ops.md` (not split yet -- 6.2 owns split)
- [ ] `README.md` and `OPERATOR_LOOP_GUIDE.md` aligned to current kernel only
- [ ] `tests/test_first_run_reliability.py` passes (6 tests); integration test uses `tmp_path`

**6.2 Memory Reduction**
- [ ] `!/benchmark/subagent_routing_matrix.yaml` added to `.gitignore` (first step)
- [ ] `measure_context_reduction.py` run; post-Phase-5 baseline recorded
- [ ] `docs/runbook_ops.md` split into `runbook_ops_active.md` + `runbook_ops_reference.md`
- [ ] `docs/loop_operating_contract.md` updated to reference `runbook_ops_active.md`
- [ ] `execution_deputy` routed to `runbook_ops_active.md`; target <= 8000 tokens
- [ ] `auditor_deputy` at or under budget (target <= 8000); or documented capped exception
- [ ] `validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .` passes
- [ ] `tests/test_memory_reduction.py` passes (6 tests)

**6.3 Skill Pilot Gate**
- [ ] Go/No-go evaluation completed; NO-GO is default unless named candidate + value metric exist
- [ ] `docs/decisions/phase6_skill_pilot_decision.md` written (min: gate results, candidate, decision, reason)

**Cross-cutting**
- [ ] `benchmark/subagent_routing_matrix.yaml` committed (un-gitignored)
- [ ] `pytest -m integration` passes (integration tests use isolated `tmp_path`)
- [ ] All existing tests still pass

### Success criteria

Phase 6 is successful when:
- Release command set green on 3 consecutive fresh runs on fresh clone
- `execution_deputy` at or under 8000 tokens; `auditor_deputy` at or under 8000 tokens
- `benchmark/subagent_routing_matrix.yaml` committed; routing validation passes
- Go/No-go decision documented with minimum required content
- All 12 new tests pass (6 per workstream); all existing tests still pass
- ENDGAME: system release-ready and deterministic; operator docs describe one coherent surface

### Key file locations (inherited from Phase 5)

| File | Note |
|---|---|
| `scripts/run_fast_checks.py` | Release gate entry point |
| `scripts/run_loop_cycle.py` | Primary loop entrypoint |
| `scripts/supervise_loop.py` | Loop health monitor |
| `docs/runbook_ops.md` | Primary hotspot for execution_deputy over-budget |
| `benchmark/subagent_routing_matrix.yaml` | Deputy context budgets |
| `scripts/measure_context_reduction.py` | Context measurement tool |
| `docs/context/auditor_*` | Auditor deputy surface |

---

## Item 6.1 — First-Run Reliability

### Prerequisite: Phase 5 gate fully checked

### Step 1: Establish first-run baseline

Run release command set on fresh clone (no prior state in `docs/context/`):

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
python scripts/run_fast_checks.py --repo-root .
python -m pytest -q
```

Record pass/fail per command, first-run-only failures, rerun-recovery cases.
Target: all 5 commands green on 3 consecutive fresh runs with no state carryover.

### Step 2: Fix first-run flakes

Categories to investigate:
- Advisory writers assuming prior state exists
- Loop summary publication race between writers and readers
- Checkpoint loading on empty `docs/context/` (must behave as clean start)
- Phase 5 writers: first-run `null` in `evidence_freshness` must not raise

Fix approach: narrow and targeted. No structural rewrite. Each fix must:
- Reproduce on fresh clone before fix
- Be green on fresh clone after fix
- Have a focused regression test

### Step 3: Operator doc alignment

Align `README.md`, `OPERATOR_LOOP_GUIDE.md`, `docs/runbook_ops.md`:
- Remove or archive legacy quant/data sections from active runbook
- Keep only commands belonging to current kernel surface
- Startup to loop to closure to takeover flow described once, consistently

**6.1-G3 resolved**: 6.2 is the **sole owner** of the `docs/runbook_ops.md` split.
6.1 Step 3 only removes legacy quant/data content from the existing single file
(no split, no new files). The split into `runbook_ops_active.md` +
`runbook_ops_reference.md` happens in 6.2 Step 2.

### Step 4: Tests

**6.1-G1 resolved**: Stream A delivered regression coverage in
`tests/test_loop_cycle_artifacts.py` and `tests/test_run_loop_cycle.py`.
`tests/test_first_run_reliability.py` is a **new Phase 6 file** covering
clean-start behavior not yet tested. If Stream A coverage already satisfies
a specific test below, mark it as verified and skip the duplicate.

`tests/test_first_run_reliability.py` — 6 tests:
- `test_loop_cycle_clean_start_no_prior_state`
- `test_checkpoint_load_missing_returns_none`
- `test_evidence_freshness_null_does_not_raise`
- `test_advisory_writer_no_prior_artifact_ok`
- `test_run_fast_checks_exits_zero`
- `test_three_consecutive_fresh_runs_all_green` (integration, @pytest.mark.integration,
  uses `tmp_path` fixture with isolated `context_dir`; excluded from default `pytest -q` run)

### Files to modify
```
scripts/run_loop_cycle.py            # fix first-run assumptions
src/sop/scripts/orchestrator.py     # fix first-run assumptions
docs/runbook_ops.md                  # split: remove legacy quant/data
README.md                           # align to current kernel
OPERATOR_LOOP_GUIDE.md              # align; remove legacy commands
tests/test_first_run_reliability.py  # new
```

### Done criteria
- [ ] Release command set passes on 3 consecutive fresh runs (no state carryover)
- [ ] Any first-run flake fixed or converted to regression test
- [ ] No rerun-only success accepted as green
- [ ] `docs/runbook_ops.md` contains no legacy quant/data commands
- [ ] `README.md` and `OPERATOR_LOOP_GUIDE.md` describe current kernel only
- [ ] `tests/test_first_run_reliability.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 6.2 — Memory Reduction

### Prerequisite: 6.1 complete

**6.1-G4 / CC-G1 resolved**: `/benchmark/` is gitignored (line 71 of `.gitignore`).
`benchmark/subagent_routing_matrix.yaml` is therefore not version-controlled.
Resolution: add a negation rule to `.gitignore` to un-gitignore this specific file:
```
!/benchmark/subagent_routing_matrix.yaml
```
This must be done as the first step of 6.2 before any routing matrix changes,
so that all Phase 6 routing changes are committed and reproducible on fresh clone.

### Step 1: Context measurement baseline

Run `scripts/measure_context_reduction.py` after Phase 5 to establish post-Phase-5
baseline for all deputies. Record results in `benchmark/subagent_routing_matrix.yaml`.

Target deputies:
- `execution_deputy` — primary hotspot (driven by `docs/runbook_ops.md` bulk)
- `auditor_deputy` — slightly over budget

**6.2-G1 resolved**: Token budget targets (from routing matrix):
- `execution_deputy` max: 12000 tokens. Target after split: <= 8000 (matching specialist_deputy budget)
- `auditor_deputy` max: 10000 tokens. Target: <= 8000. Current required artifacts:
  `auditor_calibration_report.json`, `auditor_promotion_dossier.json`,
  `loop_cycle_summary_latest.json`. Run `measure_context_reduction.py`
  first to confirm actual vs limit before making any changes.

### Step 2: execution_deputy context slimming (B1)

Split `docs/runbook_ops.md` into:
- `docs/runbook_ops_active.md` — minimal execution-path guidance needed inside the loop
- `docs/runbook_ops_reference.md` — non-runtime operator reference / archive material

Update `benchmark/subagent_routing_matrix.yaml` to route `execution_deputy` to
`runbook_ops_active.md` only.

Verification after split:
```powershell
python scripts/validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .
python scripts/measure_context_reduction.py
```

Done when: `execution_deputy` at or under budget, or documented exception with capped hotspot.
Routing validation passes. Operator docs coherent after split.

### Step 3: auditor_deputy surface tightening (B2)

Reduce `auditor_deputy` context without removing required evidence:
**6.2-G4 resolved**: Required artifacts are `auditor_calibration_report.json`,
`auditor_promotion_dossier.json`, `loop_cycle_summary_latest.json`.
No raw ledger in required set (`auditor_fp_ledger.json` is cold/manual fallback).
Run `measure_context_reduction.py` first to confirm actual hotspot before any reduction.
- Prefer summary/distilled artifacts over raw ledger bulk where safe
- Review `docs/context/auditor_*` for bulk that can be summarised
- Keep all governance evidence paths intact

Done when: `auditor_deputy` at or under budget, or explicitly justified with capped exception.
No governance evidence path weakened.

### Step 4: Tests

`tests/test_memory_reduction.py` — 6 tests:
- `test_routing_matrix_valid_after_split`
- `test_execution_deputy_within_budget`
- `test_auditor_deputy_within_budget`
- `test_runbook_split_active_contains_loop_commands`
- `test_runbook_split_reference_not_in_deputy_routing`
- `test_context_measurement_baseline_recorded`

### Files to modify
```
docs/runbook_ops.md                         # split into active + reference
benchmark/subagent_routing_matrix.yaml      # route execution_deputy to active only
docs/loop_operating_contract.md             # update runbook_ops.md ref to runbook_ops_active.md
docs/context/auditor_*                      # summarise bulk where safe
scripts/measure_context_reduction.py        # rerun; record baseline
tests/test_memory_reduction.py              # new
```

### Done criteria
- [ ] `scripts/measure_context_reduction.py` run; post-Phase-5 baseline recorded
- [ ] `docs/runbook_ops.md` split into `_active` and `_reference`
- [ ] `execution_deputy` at or under budget (or documented exception)
- [ ] `auditor_deputy` at or under budget (or capped exception)
- [ ] Routing validation passes after split
- [ ] `tests/test_memory_reduction.py` passes (6 tests)
- [ ] All existing tests still pass

---

## Item 6.3 — Skill Pilot Gate

### Prerequisite: 6.2 complete

### Step 1: Evaluate Stream D entry criteria

From `next_phase_plan.md` Stream D entry gate — do not start until:
- Kernel Stream green (6.1 done)
- Memory Reduction Stream green (6.2 done)
- Tiered Memory Stream green (Phase 5 done)

This item is an evaluation gate, not an implementation workstream.
**6.3-G1 resolved**: NO-GO is the explicit default. GO requires:
(1) all three stream gates green, (2) a named pilot candidate,
(3) a defined measurable value metric before evaluation starts.
If no candidate is named before Phase 6 closes: decision is NO-GO.

Phase 6 ends here unless the gate is green AND a specific pilot candidate exists.

### Step 2: Pilot candidate selection

If gate is green, evaluate candidate skills against these criteria:
- Narrow declarative scope (one well-defined task)
- Existing governance gates remain authoritative
- Rollback path exists without affecting core kernel flow
- Measurable value criterion defined before pilot starts

Hard limits (from `next_phase_plan.md`):
- No full skill-execution engine
- No mandatory skill routing for all work
- No forced maximal subagent architecture
- No automatic promotion of generated/self-evolved skills to production

### Step 3: Go/No-go decision

Output of this item is one of:
- **GO**: pilot candidate selected, scope bounded, rollback path defined, Phase 7 = pilot
- **NO-GO**: gate not green or no justified candidate; Phase 7 = defer Stream D

Document decision in `docs/decisions/phase6_skill_pilot_decision.md`.
**6.3-G2**: Minimum content required:
- Gate evaluation results: 6.1 status, 6.2 status, Phase 5 status
- Pilot candidate name or "none"
- Decision: GO or NO-GO
- Reason (one sentence minimum)

### Files to create
```
docs/decisions/phase6_skill_pilot_decision.md
```

### Done criteria
- [ ] Stream D entry criteria evaluated against 6.1 + 6.2 + Phase 5 results
- [ ] Go/No-go decision documented in `docs/decisions/phase6_skill_pilot_decision.md`
- [ ] If GO: pilot candidate named, scope bounded, rollback path defined
- [ ] If NO-GO: reason documented; Stream D deferred

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|
| First-run flake is structural, not narrow | Medium | High | Cap investigation at 2 days; if structural, document and defer to Phase 7 |
| `docs/runbook_ops.md` split breaks operator workflow | Low | High | Keep `runbook_ops.md` as redirect stub pointing to both files |
| `execution_deputy` still over budget after split | Low | Medium | Document approved exception with capped token count |
| `auditor_deputy` tightening removes required evidence | Low | High | Require governance evidence path check before any reduction |
| Skill pilot scope creep to full engine | Medium | High | Hard limits from `next_phase_plan.md` enforced; gate item only |
| Phase 5 artifact additions pushed `execution_deputy` further over budget | Medium | Medium | Measure first (Step 1) before any doc changes |

---

## Phase 6 to Phase 7 Gate

Phase 7 must not start until all of the following are true:

**Item 6.1 — First-Run Reliability**
- [ ] Release command set green on 3 consecutive fresh runs
- [ ] No rerun-only success; all flakes fixed or have regression tests
- [ ] Operator docs aligned to current kernel only
- [ ] `tests/test_first_run_reliability.py` passes (6 tests)

**Item 6.2 — Memory Reduction**
- [ ] Post-Phase-5 baseline recorded in `benchmark/subagent_routing_matrix.yaml`
- [ ] `execution_deputy` at or under budget (or documented capped exception)
- [ ] `auditor_deputy` at or under budget (or documented capped exception)
- [ ] `docs/runbook_ops.md` split complete; routing validation passes
- [ ] `tests/test_memory_reduction.py` passes (6 tests)

**Item 6.3 — Skill Pilot Gate**
- [ ] Go/No-go decision documented in `docs/decisions/phase6_skill_pilot_decision.md`
- [ ] If GO: pilot candidate, scope, and rollback path defined

**Cross-cutting**
- [ ] `pytest -m integration` passes
- [ ] All existing tests still pass
- [ ] ENDGAME check: system is release-ready and deterministic; operator docs describe
     one coherent product surface; worst routing hotspots reduced materially