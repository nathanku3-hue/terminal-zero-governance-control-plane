# Phase 4 — Navigation Map + Boundary Sealing (Streams A + D)

> **Status**: Ready to execute
> **Date**: 2026-03-30
> **Streams**: A (Boundary Sealing) + D (Navigation Map) -- both parallel, no dependencies
> **Blocks**: Stream E (Stream A must complete before Stream E can start)
> **Roadmap alignment**: Fix-path to 8/10 -- Documentation + Production Readiness tracks

---

## Strategic Context

Stream A and D are fully independent parallel streams. Neither depends on Stream B or C.
Stream A must complete before Stream E. Stream D has no downstream blockers.
Stream D is substantially delivered -- three key artifacts already exist.
Phase 4 is a gap audit + completion pass, not a build-from-scratch.

---

## What Already Exists (Baseline)

| Asset | Location | State |
|---|---|---|
| `operator_navigation_map.md` | `docs/context/` | Complete -- 7 failure_class branches, gate HOLD, skills routing, WARN steps |
| `skill_readiness_matrix.md` | `docs/context/` | Complete -- 3 sections, diagnostic block, recovery steps |
| `operator_onboarding_checklist.md` | `docs/context/` | Complete -- prerequisites through failure triage |
| `OPERATOR_LOOP_GUIDE.md` | repo root | Complete -- PRIMARY/COMPAT paths, entry order |
| `KERNEL_ACTIVATION_MATRIX.md` | `../` (SOP root) | Exists |
| Absolute paths in operator docs | (none found) | Clean -- grep confirms no drive letters |
| Template sources | `docs/context/schemas/*.json.template` + `docs/context/templates/*.md.template` | Two dirs -- dual-source audit needed |

---

## Scope Boundary

| In Phase 4 | Deferred |
|---|---|
| Stream A: absolute path audit (all operator docs) | Cross-repo navigation |
| Stream A: template single-source confirmation | Full operator training materials |
| Stream A: kernel activation status references verified | Workflow status overlay automation |
| Stream D: gap audit of three existing navigation artifacts | |
| Stream D: verify all examples use sop PRIMARY path | |
| Stream D: cross-references between artifacts consistent | |
| Stream D: loop_readiness placeholder (post Stream C) | |

---

## Stream A -- Boundary Sealing

### A-1: Absolute Path Audit

Scan all operator-facing docs for hardcoded absolute paths (drive letters, home directory paths).

Files to scan:
- `OPERATOR_LOOP_GUIDE.md`
- `docs/context/operator_navigation_map.md`
- `docs/context/skill_readiness_matrix.md`
- `docs/context/operator_onboarding_checklist.md`
- `README.md`
- `docs/tech_stack.md`, `docs/directory_structure.md`, `docs/operating_principles.md`
- `docs/definition_of_done.md`, `docs/workflow_wiring_detailed.md`

Command (scope-restricted to operator-facing files only -- do NOT use --type md globally
as generated artifacts in docs/context/ contain absolute paths by design):
```
rg "[A-Z]:\\\\" docs/context/operator_navigation_map.md docs/context/skill_readiness_matrix.md docs/context/operator_onboarding_checklist.md OPERATOR_LOOP_GUIDE.md README.md docs/tech_stack.md docs/directory_structure.md docs/operating_principles.md docs/definition_of_done.md docs/workflow_wiring_detailed.md
```
Must return zero matches.

### A-2: Template Source Audit

Two template directories exist:
- `docs/context/schemas/` -- 7 `.json.template` files
- `docs/context/templates/` -- 1 `.md.template` file

Audit: confirm each template has exactly one canonical source.
Known gap to fix: `docs/context/README.md` classifies templates by type but does not
map each template to its single canonical source/owner.
Day 1 A-2 task: add a "Template Canonical Sources" section to `docs/context/README.md`
listing all 8 template files and their canonical source/owner. Additive only --
do not modify the existing N.1 classification table.

Templates to document (8 total):
- `docs/context/schemas/worker_reply_packet.json.template`
- `docs/context/schemas/auditor_fp_ledger.json.template`
- `docs/context/schemas/auditor_findings.json.template`
- `docs/context/schemas/pm_to_code_traceability.yaml.template`
- `docs/context/schemas/dispatch_ack.json.template`
- `docs/context/schemas/dispatch_manifest.json.template`
- `docs/context/schemas/worker_status.json.template`
- `docs/context/templates/e2e_evidence_index.md.template`

### A-3: Kernel Activation Status References

Confirm:
- All operator docs reference `../KERNEL_ACTIVATION_MATRIX.md` as step 1 of entry order
- No operator doc hardcodes a capability as always-active without matrix check
- Local `docs/context/` references resolve correctly relative to repo root

Known gap to fix: `operator_onboarding_checklist.md` has no `KERNEL_ACTIVATION_MATRIX.md`
reference. Day 1 A-3 task: add `../KERNEL_ACTIVATION_MATRIX.md` as entry step 1 to
`operator_onboarding_checklist.md` (additive -- do not remove existing content).


---

## Stream D -- Navigation Map Gap Audit

### D-1: Gap Audit Against Acceptance Criteria

| Criterion | Check |
|---|---|
| Operator reaches correct action in <3 steps from any failure state | Verify each failure_class branch |
| No absolute paths | Confirmed by Stream A A-1 |
| All examples use `sop` PRIMARY path | Grep for bare `python scripts/` without COMPAT label |
| `scripts/` compat path explicitly labeled | COMPAT label present on all compat examples |
| Cross-references between artifacts consistent | All links resolve to existing files |

### D-2: PRIMARY Path Verification

All `python scripts/` examples must carry the COMPAT label.
No bare `python scripts/` without label is permitted in operator docs.

### D-3: Cross-Reference Consistency

Confirm all cross-references resolve:
- `OPERATOR_LOOP_GUIDE.md` -> `docs/context/operator_navigation_map.md`
- `operator_navigation_map.md` -> `docs/context/skill_readiness_matrix.md` (Sections 1, 2)
- `operator_onboarding_checklist.md` -> `operator_navigation_map.md` and `skill_readiness_matrix.md`
- `skill_readiness_matrix.md` -> `run_failure_latest.json` and `loop_cycle_summary_latest.json`

### D-4: loop_readiness Placeholder

Add placeholder to `operator_navigation_map.md` Skills Status Routing section:
"Available after Stream C Phase B: `docs/context/loop_readiness_latest.json`"
Additive only -- do not block Phase 4 on Stream C.

---

## Execution Order

### Day 1 -- Stream A Audit

- [ ] A-1: Run absolute path scan; fix any found (expected: none)
- [ ] A-2: Audit template directories; document canonical source in `docs/context/README.md`
- [ ] A-3: Verify kernel activation matrix references in all operator docs
- [ ] Run `test_fresh_worker_navigation.py`, `test_first_run_reliability.py` -- no regressions

### Day 2 -- Stream D Gap Audit + Fixes

- [ ] D-1: Audit all three navigation artifacts against acceptance criteria
- [ ] D-2: Fix any bare `python scripts/` commands missing COMPAT label
- [ ] D-3: Walk all cross-references; confirm each resolves
- [ ] D-4: Add `loop_readiness_latest.json` placeholder to navigation map
- [ ] Notify Stream E: Stream A complete (after Day 1 gates pass)

---

## Acceptance Gates

### Stream A
- [ ] Scoped rg scan (operator-facing files only, not --type md globally) returns zero matches:
  `rg "[A-Z]:\\\\" docs/context/operator_navigation_map.md docs/context/skill_readiness_matrix.md docs/context/operator_onboarding_checklist.md OPERATOR_LOOP_GUIDE.md README.md docs/tech_stack.md docs/directory_structure.md docs/operating_principles.md docs/definition_of_done.md docs/workflow_wiring_detailed.md`
- [ ] Each template has exactly one canonical source
- [ ] `docs/context/README.md` documents canonical source for each template
- [ ] All operator docs reference `../KERNEL_ACTIVATION_MATRIX.md` as entry step 1
- [ ] No operator doc hardcodes a capability as always-active

### Stream D
- [ ] Operator reaches correct action from any failure_class in <3 steps
- [ ] All command examples use `sop run` as PRIMARY
- [ ] All `python scripts/` examples labeled COMPAT
- [ ] All cross-references resolve to existing files
- [ ] `loop_readiness_latest.json` placeholder added
- [ ] No absolute paths (confirmed by A-1)

### Combined
- [ ] Stream A and D acceptance gates both pass
- [ ] `test_fresh_worker_navigation.py`, `test_first_run_reliability.py`, `test_cli_script_parity.py` pass
- [ ] Stream E notified: Stream A complete, Stream E unblocked (pending Stream B)

---

## Tests

Documentation-only streams. No new test files required.

| Test | What it protects |
|---|---|
| `test_fresh_worker_navigation.py` | Fresh worker navigates from AGENTS.md to first action |
| `test_first_run_reliability.py` | First-run sequence produces expected artifacts |
| `test_cli_script_parity.py` | PRIMARY and COMPAT paths produce identical behavior |

---

## Implementation Review Rule

All changes in Phase 4 are documentation only. No code changes.
All paths in operator docs must be repo-root relative.
All command examples must label PRIMARY vs COMPAT explicitly.
Coordinate with Stream D: no new absolute paths added by any stream.

---

## Cross-Stream Coordination

| Event | Action |
|---|---|
| Stream A Day 1 complete | Notify Stream D: absolute path scan clean, safe to finalize |
| Stream A complete | Notify Stream E: boundary sealing done, Stream E entry gate met |
| Stream C Phase B complete | Update D-4 placeholder to live link |
| Stream E starts | Confirm Stream A gate is green before any Stream E work begins |

---

## What This Plan Does NOT Change

- No code changes -- documentation only
- `scripts/` content unchanged
- `src/sop/` package unchanged
- Runtime artifact schemas unchanged
- No existing cross-reference removed

---

## Completion Definition

Phase 4 is complete when:
1. Stream A: zero absolute paths in operator docs; single template source confirmed; kernel activation references verified
2. Stream D: all three navigation artifacts pass gap audit; all examples PRIMARY-labeled; all cross-references resolve
3. Existing tests pass with no regressions
4. Stream E entry gate met: Stream A complete
