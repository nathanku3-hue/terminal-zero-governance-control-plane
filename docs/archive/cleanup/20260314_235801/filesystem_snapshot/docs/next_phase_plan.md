# Phase 6 Plan: Kernel Stabilization and Memory Optimization

## Status

Phase 5 is complete enough to stop expanding architecture and start hardening the shipped kernel.

This plan defines the **next phase only**.

### Progress Snapshot (2026-03-13)

- A1 / P0.1 is complete: the release-gate flake was narrowed and regression coverage was added around advisory publication, fast-check ordering, and loop-summary snapshot contracts.
- A2 / P0.2 is complete: active operator docs now describe the current control-plane only, and legacy quant/data material was moved out of the active runbook path.
- A3 / P0.3 is complete: artifact policy is documented and writer-side boundaries are enforced, but non-blocking hygiene debt remains under `docs/context/` and in the out-of-policy root mirror `MILESTONE_OPTIMALITY_REVIEW_LATEST.md`.
- A4 / P0.4 is complete: `README.md`, `RELEASING.md`, `docs/decisions/phase5_architecture.md`, and this plan now separate the shipped `v1` kernel from future-state plugin/worker/rollout surfaces, the relevant plan/ADR assets are tracked in git, and the Stream A verification surface passed 3 consecutive fresh runs in the current release-candidate working tree.

It does **not** approve:

- a full skill-forced execution architecture
- a maximal subagent rewrite
- a broad kernel refactor
- packaging / productization work beyond release-readiness needs

## Decision

The next phase will prioritize, in order:

1. kernel reliability and release confidence
2. targeted memory reduction on the current loop
3. tiered memory / compaction lifecycle improvements
4. optional skill-execution pilot only after earlier gates are green

## Why This Order

The repo already has meaningful Phase 5 foundations:

- advisory handoffs are operational
- subagent routing exists and is measured
- compaction trigger evaluation exists
- skill registry / allowlist / activation exist

The highest remaining gain is **not** more architecture. The highest remaining gain is making the current kernel deterministic, coherent, and lighter.

## Existing Foundation Already in Place

The following are treated as available inputs, not next-phase objectives:

- `scripts/build_exec_memory_packet.py`
- `scripts/evaluate_context_compaction_trigger.py`
- `benchmark/subagent_routing_matrix.yaml`
- `scripts/utils/skill_resolver.py`
- `scripts/validate_skill_activation.py`
- `docs/context/next_round_handoff_latest.*`
- `docs/context/skill_activation_latest.json`

## Non-Negotiable Rules

1. No work on skill execution semantics until Kernel Stream and Memory Stream exit criteria are met.
2. No broad refactor without a separate approved design task.
3. Every stream must end with executable verification commands, not narrative-only signoff.
4. Runtime artifact behavior must be enforced in code paths, not documented only.
5. Release-readiness claims require first-run green behavior, not rerun recovery.

## Stream Order

### Stream A: Kernel Stabilization

**Priority:** P0  
**Goal:** make the shipped control-plane deterministic, coherent, and release-blocking clean.

#### A1. Deterministic Release Gate

**Problem**

The release contract requires a green validation surface, but confidence is weakened if the first run is unstable.

**Scope**

- isolate and remove any first-run-only failures in the current kernel surface
- treat advisory artifact generation and loop summary publication as the first investigation surface
- keep the fix narrow; no structural rewrite

**Primary files**

- `scripts/run_loop_cycle.py`
- `scripts/loop_cycle_artifacts.py`
- `tests/test_loop_cycle_artifacts.py`
- `tests/test_run_loop_cycle.py`
- `RELEASING.md`

**Done when**

- the release command set below passes on 3 consecutive fresh runs
- any flake root cause is either fixed or converted into a focused regression test
- no rerun-only success is needed to get green

**Verification**

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
python scripts/run_fast_checks.py --repo-root .
python -m pytest -q
```

#### A2. Operator Contract Cleanup

**Problem**

Operator-facing docs still mix the active governance control plane with legacy data / benchmark surfaces.

**Scope**

- align `README.md`, `OPERATOR_LOOP_GUIDE.md`, and `docs/runbook_ops.md`
- remove or explicitly archive legacy quant/data sections from the active runbook
- keep only commands that belong to the current kernel surface

**Primary files**

- `README.md`
- `OPERATOR_LOOP_GUIDE.md`
- `docs/runbook_ops.md`

**Done when**

- every operator command in the active docs exists and belongs to the current repo surface
- the active runbook contains no legacy data-management commands
- startup -> loop -> closure -> takeover flow is described once and consistently

#### A3. Artifact Boundary Enforcement

**Problem**

Generated-state policy is not strict enough. The repo currently mixes canonical artifacts, convenience mirrors, and extra generated trees.

**Scope**

- classify runtime outputs into:
  - canonical
  - convenience mirror
  - generated non-canonical
  - fixture / archive
- enforce writer-side output boundaries for advisory artifacts and mirrors
- reconcile `.gitignore` with actual runtime behavior

**Primary files**

- `.gitignore`
- `scripts/loop_cycle_artifacts.py`
- `scripts/run_loop_cycle.py`
- `docs/context/*`

**Done when**

- artifact classes are documented in one place
- advisory writers only emit to approved locations
- root mirrors are explicitly convenience-only
- nested generated trees are either reclassified as fixtures / archive or removed from the active product surface

#### A4. Freeze the Real v1 Boundary

**Problem**

The repo has a working kernel, but some planning docs still present future-state plugin surfaces as if they were current architecture.

**Scope**

- document the current v1 boundary around the shipped kernel
- mark future Phase 5+ plugin / worker / rollout surfaces as future-state only
- keep roadmap language separate from shipped product language

**Primary files**

- `README.md`
- `RELEASING.md`
- `docs/decisions/phase5_architecture.md`

**Done when**

- no active doc presents missing plugin/worker/rollout surfaces as shipped functionality
- `README.md` and `RELEASING.md` describe the current kernel as the actual product boundary
- future-state material is clearly labeled as draft, deferred, or roadmap
- the `docs/decisions/phase5_architecture.md` rewrite is review-closed and tracked as part of the repository, not left as an untracked replacement file

### Kernel Stream Exit Criteria

Kernel Stream is complete only when all of the following are true:

- release command set passes on 3 consecutive fresh runs
- operator docs are aligned to the current kernel only
- artifact policy is documented and enforced in writers
- v1 boundary docs no longer overstate future-state architecture

No later stream may be treated as release-critical before this stream is green.

### Immediate Move After Stream A Closure

Stream A is complete. The next action is not more architecture work. The next action is:

1. start Stream B with `execution_deputy` context slimming as the first memory-reduction slice,
2. rerun routing validation and context measurement after the `docs/runbook_ops.md` split,
3. keep remaining artifact-hygiene cleanup as a separate, non-blocking follow-up unless it breaks release evidence or policy enforcement.

Concretely, the first next-phase implementation target should be the `docs/runbook_ops.md` split and routing-measurement rerun described in B1. Do not start Stream C or Stream D before B metrics are stable.

---

### Stream B: Targeted Memory Reduction

**Priority:** P1  
**Goal:** reduce the current token hotspots without changing authority or execution semantics.

#### B1. execution_deputy Context Slimming

**Problem**

`execution_deputy` is materially over budget, driven mainly by `docs/runbook_ops.md`.

**Scope**

- split the current ops document into:
  - minimal execution-path guidance needed inside the loop
  - non-runtime operator reference / archive material
- keep routing logic unchanged except for artifact selection updates

**Primary files**

- `docs/runbook_ops.md`
- `benchmark/subagent_routing_matrix.yaml`
- `scripts/measure_context_reduction.py`

**Done when**

- `execution_deputy` is at or under budget, or has an approved documented exception with a narrower hotspot
- routing validation still passes
- operator docs remain coherent after the split

#### B2. auditor_deputy Surface Tightening

**Problem**

`auditor_deputy` is still slightly over budget.

**Scope**

- reduce unnecessary auditor context without removing required evidence
- prefer summary / distilled artifacts over raw ledger bulk where safe

**Primary files**

- `benchmark/subagent_routing_matrix.yaml`
- `docs/context/auditor_*`
- any summary artifacts already produced by the loop

**Done when**

- `auditor_deputy` is at or under budget
- no governance evidence path is weakened

### Memory Reduction Stream Exit Criteria

- routing validator passes
- context measurement rerun is green
- `execution_deputy` is no longer the dominant uncontrolled hotspot
- `auditor_deputy` is brought within budget or explicitly justified with a capped exception

---

### Stream C: Tiered Memory and Compaction Lifecycle

**Priority:** P2  
**Goal:** formalize what stays hot, what becomes warm, and what should only load on demand.

#### C1. Memory Tier Contract

**Scope**

- define three explicit memory tiers:
  - hot: current loop execution state and blockers
  - warm: latest validated governance artifacts and handoffs
  - cold: archived / historical context loaded only on demand
- bind each tier to concrete artifact families

**Primary files**

- `scripts/build_exec_memory_packet.py`
- `scripts/evaluate_context_compaction_trigger.py`
- `docs/context/*`

**Done when**

- each key artifact family is assigned to a tier
- packet generation and compaction logic use the same tier model

#### C2. Compaction Behavior Hardening

**Scope**

- make compaction thresholds and outputs easier to reason about
- preserve authoritative handoff / blocker context under compaction
- avoid silent loss of high-value governance state
- allow compaction at clean task boundaries, after extracting a validated result, before large new context ingestion, or when superseded context can be summarized safely
- avoid compaction in the middle of complex multi-step execution when doing so would disrupt active reasoning or hide unresolved blockers

**Done when**

- compaction outputs have deterministic retention rules
- handoff and blocker surfaces survive compaction as designed
- tests cover tier-retention behavior

### Tiered Memory Stream Exit Criteria

- a written hot/warm/cold contract exists
- compaction logic is aligned with that contract
- packet / handoff continuity is verified under compaction

---

### Stream D: Optional Skill Execution Pilot

**Priority:** P3  
**Goal:** validate whether one narrow skill execution path adds value without forcing the architecture.

#### D1. Single-Skill Pilot Only

**Scope**

- choose one narrow declarative skill
- add execution semantics only for that pilot path
- keep existing governance gates authoritative
- if skill-governance gaps remain, harden identity/version/drift reporting before adding new execution semantics

**Hard limits**

- no full skill-execution engine
- no mandatory skill routing for all work
- no forced maximal subagent architecture
- no automatic promotion of generated or self-evolved skills into the approved production path

**Done when**

- one pilot proves either measurable value or clear non-value
- rollback path exists
- core kernel flow still works with no skill execution enabled

### Skill Pilot Entry Gate

Do not start Stream D until:

- Kernel Stream is green
- Memory Reduction Stream is green
- Tiered Memory Stream is green or explicitly waived

## Explicit Deferrals

The following are not part of the next phase:

- broad kernel rewrite
- package / hosted-service productization
- skill package-manager / hosted registry work
- benchmark expansion for its own sake
- automatic EvoSkill-style skill evolution or auto-promotion into the approved production surface
- filesystem-to-database or graph-first replacement of the current operator artifact surface
- maximal subagent decomposition
- worker/rollout/plugin implementation purely because the draft ADR names them

## Recommended Sequence

1. Finish Stream A completely.
2. Re-run release surface and freeze results.
3. Execute Stream B to remove the current routing hotspots.
4. Execute Stream C only after Stream B metrics are stable.
5. Consider Stream D only if the earlier streams are green and there is a specific pilot candidate.

## Success Definition for the Next Phase

The next phase is successful if, at the end:

- the current kernel is release-ready and deterministic
- operator docs describe one coherent product surface
- artifact boundaries are enforced by code and docs
- the worst routing hotspots are reduced materially
- memory compaction is tiered and predictable
- no premature forced skill/subagent architecture has been introduced

## Short Form Decision

The next phase is:

**stabilize the kernel, then shrink memory, then formalize tiers, then pilot skills only if still justified.**
