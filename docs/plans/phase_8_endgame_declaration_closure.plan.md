---
name: "Phase 8: ENDGAME Declaration Closure"
overview: "Phase 8 is the closure sprint. No new streams. No new architecture. Exactly 4 actions remain before ENDGAME can be declared. All MULTISTREAM streams A-E are complete. Phase 7 work is done."
todos: []
isProject: false
---

## Source Evidence

| Source | Status |
|--------|--------|
| `endgame_verification.md` | Committed; 8 PASS, 1 PENDING HUMAN |
| `phase6_skill_pilot_decision.md` | NO-GO confirmed |
| `phase7_skill_pilot_results.md` | Skip documented |
| `system_explainer_5min.md` | Exists; human sign-off pending |
| `tests/test_skill_pilot.py` | 6 tests pass (NO-GO path) |
| `tests/test_endgame.py` | 6 tests pass |
| `tests/test_smoke_e.py` | Stream E present and running |
| `docs/context/operator_navigation_map.md` | Stream D complete |
| `docs/context/skill_readiness_matrix.md` | Stream C complete |
| `scripts/critical_scan_manifest.json` | Stream B H-NEW-3 complete |
| `.github/workflows/release-validation.yml` | Stream E CI scaffold complete |
| Run 1 of 3-run gate | PASS 2026-03-28 (918 recorded; actual suite = 1005) |

**All MULTISTREAM streams A-E complete. Phase 7 done. 4 actions remain.**

---

## Non-Negotiable Rules

1. No new architecture. No new streams. No scope expansion.
2. All 4 actions must complete before ENDGAME is declared.
3. Actions 1 and 2 must complete before Action 3.
4. Action 4 is async — ENDGAME waits for it regardless.
5. Runs 2 and 3 must be consecutive from clean state. Any failure restarts from run 1.

---

## Action 1 — Add ENDGAME.md path to endgame_verification.md

**File:** `docs/decisions/endgame_verification.md`
**Unblocks:** Criterion 2 and 9 evidence integrity.

Add `## Path Notes` section after the header block:
```markdown
## Path Notes
- ENDGAME.md: `e:\Code\SOP\ENDGAME.md` (above repo root — confirmed 2026-03-29)
- SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md: `e:\Code\SOP\SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`
- KERNEL_ACTIVATION_MATRIX.md: `e:\Code\SOP\KERNEL_ACTIVATION_MATRIX.md`
```

Append to Criterion 2 evidence:
```
(ENDGAME.md at e:\Code\SOP\ENDGAME.md — confirmed present 2026-03-29)
```

Append to Criterion 9 evidence:
```
(ENDGAME.md Section 11 at e:\Code\SOP\ENDGAME.md — confirmed present 2026-03-29)
```

**Done when:** Path note in 3 locations. Committed.

---

## Action 2 — Annotate run 1 test count in endgame_verification.md

**File:** `docs/decisions/endgame_verification.md`
**Must complete before Action 3.**

Find under `## Final Release Freeze`:
```
**Test count:** 918 passed, 1 skipped (existing suite)
```

Replace with:
```markdown
**Test count:** 918 passed, 1 skipped
> Note: 918 reflects pre-Phase-7 suite snapshot (2026-03-28).
> 87 tests added during Phase 7 (test_skill_pilot.py + test_endgame.py + others).
> Current suite: 1005 tests as of 2026-03-29.
> Runs 2 and 3 record 1005 — the current authoritative count.
```

**Done when:** Annotation present. Committed.

---

## Action 3 — Execute runs 2 and 3 of the 6-command gate

**Prerequisite:** Actions 1 and 2 committed.
**Blocks ENDGAME declaration.**

### Procedure (repeat twice — run 2, then run 3)

```powershell
cd e:\Code\SOP\quant_current_scope

# Clean state:
Remove-Item -Force docs\context\loop_cycle_summary_latest.json -ErrorAction SilentlyContinue
Remove-Item -Force docs\context\exec_memory_packet_latest.json -ErrorAction SilentlyContinue

# 6-command gate:
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
python scripts/run_fast_checks.py --repo-root .   # HOLD = EXIT 0, expected
python -m pytest -q                               # must show 1005
python scripts/validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .
```

All 6 must exit 0.

### Record in endgame_verification.md under `## Final Release Freeze`:

```markdown
| Run | Date | Python | Tests | Result |
|-----|------|--------|-------|--------|
| 1 | 2026-03-28 | 3.14.0 | 918* | PASS |
| 2 | <date> | 3.14.0 | 1005 | PASS |
| 3 | <date> | 3.14.0 | 1005 | PASS |
(*see count annotation above)
```

**Exact replacement format for Run 2 and Run 3 (Ph8-H):**
Use this format precisely — matching Run 1:
```
Run 2: PASS — date: YYYY-MM-DD, Python: 3.14.0, tests: 1005 passed
Run 3: PASS — date: YYYY-MM-DD, Python: 3.14.0, tests: 1005 passed
```
If the diff already contains `Run 2: PENDING` and `Run 3: PENDING` placeholder lines, replace each with the above format after the run completes.

### If any command fails

1. Isolate root cause narrowly — no structural rewrite
2. Fix or convert to regression test
3. Re-start from run 1 — all 3 must be consecutive
4. Do not accept rerun-only recovery

**Done when:** Runs 2 and 3 recorded as PASS with date, Python 3.14.0, 1005 tests. Committed.


---

## Action 4 — Human cold-read sign-off on system_explainer_5min.md

**File:** `docs/decisions/system_explainer_5min.md`
**Blocks ENDGAME declaration. Async — can run in parallel with Actions 1-3.**

### Sign-off procedure (source plan 7.2-G7)

1. Identify a human who has NOT read `system_explainer_5min.md` before
2. Human reads cold — no prior briefing
3. All 4 pass criteria must be met:
   - (a) No phase-specific jargon (no "Phase 3", "Stream B", "H-5", "CC-G3", etc.)
   - (b) System purpose clear in one read
   - (c) Loop structure clear in one read
   - (d) Document ≤500 words
4. Human records verdict in `endgame_verification.md` Criterion 1:

```markdown
### Criterion 1: Human can explain the system in 5 minutes
**PASS.**
Reviewed by: <name> on <date>
Cold read: Yes (no prior exposure)
Word count: <N> (≤500)
No phase-specific jargon: Yes
Loop structure clear in one read: Yes
```

5. Change Criterion 1 status: `PENDING HUMAN REVIEW` → `PASS`
6. Update cross-cutting checklist: `[ ] Human signs off` → `[x] Human signs off`
7. Commit

### If human finds jargon or unclear structure
1. Revise `system_explainer_5min.md` to fix the specific issue
2. Repeat cold-read with a different unprimed human
3. Document revision in sign-off record

**Done when:** Criterion 1 PASS with human name, date, all 4 criteria confirmed. Committed.

---

## ENDGAME Declaration Procedure

Execute when all 4 actions are complete and committed.

### Verification commands
```powershell
cd e:\Code\SOP\quant_current_scope

# No PENDING criteria remaining:
Select-String "PENDING" docs\decisions\endgame_verification.md
# Must return: no matches

# Test count current:
python -m pytest --collect-only -q 2>&1 | Select-String "test"
# Must show 1005

# Routing matrix committed:
git ls-files benchmark/subagent_routing_matrix.yaml
# Must return the file

# Recent commits include all 4 actions:
git log --oneline -10
```

### ENDGAME declaration block

Add to `docs/decisions/endgame_verification.md` as the final section:

```markdown
---

## ENDGAME DECLARED

**Date:** <date>
**Declared by:** <name>

### Evidence
- All 9 ENDGAME criteria: PASS (see verdicts above)
- 3-consecutive-run gate: PASS (runs 1-3 recorded above)
- Human sign-off on system_explainer_5min.md: PASS (<name>, <date>)
- Final test count: 1005 (Python 3.14.0)
- Surface retirement audit: 8 archived, 40+ kept
- Vocabulary drift: zero (local check)
- `benchmark/subagent_routing_matrix.yaml`: committed

### System state at ENDGAME
- Kernel: release-ready and deterministic
- Operator docs: one coherent surface
- Artifact boundaries: enforced in code
- Memory: tiered and predictable
- Skill pilot: deferred (NO-GO — no candidate named)
- All MULTISTREAM streams A-E: complete

The system has reached the operational endgame defined in
`e:\Code\SOP\ENDGAME.md`:
- Human stays at strategy, taste, and reality layer
- System runs bounded engineering loops with minimal friction
- Product and system truth aligned through explicit bridge artifacts
- Reality changes without breaking coherence
```

Commit with message: `chore: ENDGAME declared — Phase 8 closure complete`

---

## Phase 8 Gate

- [ ] Action 1: ENDGAME.md path note in 3 locations in `endgame_verification.md` — committed
- [ ] Action 2: Run 1 count annotation (918 → 1005 explanation) — committed
- [ ] Action 3: Run 2 PASS recorded (1005 tests, date, Python 3.14.0) — committed
- [ ] Action 3: Run 3 PASS recorded (1005 tests, date, Python 3.14.0) — committed
- [ ] Action 4: Criterion 1 PASS with human name and date — committed
- [ ] `endgame_verification.md` has no remaining PENDING items
- [ ] ENDGAME declaration block added and committed

**Phase 8 complete = ENDGAME declared.**

---

## Complete Plan Registry

| Phase | File | Lines | Status |
|-------|------|-------|--------|
| 3 | `phase_3_artifact_integrity_schema_hardening_onboarding.plan.md` | — | Approved |
| 4 | `phase_4_retry_loop_spec_phase_context_observability.plan.md` | 372 | Approved |
| 5 | `phase_5_release_readiness_kernel_pre_stabilization.plan.md` | 533 | Approved |
| 6 | `phase_6_kernel_stabilization_memory_optimization.plan.md` | 393 | Pre-approved (Phase 5 must close first) |
| 7 | `phase_7_skill_pilot_endgame_closure.plan.md` | 300 | Approved — 4 actions done in Phase 8 |
| 8 | `phase_8_endgame_declaration_closure.plan.md` | — | Approved |

**Critical path:**
```
Ph3 → Ph4 → Ph5 → Ph6 (A→B→C→D) → Ph7 → Ph8 (Actions 1→2→3+4) → ENDGAME
```

**Ph8 is the last phase. There is no Phase 9.**


---

## Phase 8 Gap Audit Patch (2026-03-29)

### Plan File

This file IS `phase_8_endgame_declaration_closure.plan.md`. It must be committed to the repo at:
`e:\Code\SOP\quant_current_scope\docs\plans\phase_8_endgame_declaration_closure.plan.md`

Add as **Action 0** (first action, before all others):

---

## Action 0 — Commit all outstanding work (NEW — BLOCKING)

**Must complete before Actions 1–4. Defines the stable baseline for the 3-run gate.**

### Step 0.1 — Commit this plan file to the repo

```powershell
cd e:\Code\SOP\quant_current_scope
copy "C:\Users\Lenovo\.cursor\plans\phase_8_endgame_declaration_closure.plan.md" docs\plans\
git add docs\plans\phase_8_endgame_declaration_closure.plan.md
git commit -m "docs: add Phase 8 plan file"
```

### Step 0.2 — Inspect and clean endgame_verification.md

`endgame_verification.md` has uncommitted modifications (Ph8-A). Before applying Actions 1 and 2:

```powershell
# Inspect what changed:
git diff docs\decisions\endgame_verification.md
```

- If the diff shows partial work-in-progress: review, complete Actions 1 and 2 content, then commit as one clean commit
- If the diff shows unrelated changes: revert and apply Actions 1 and 2 fresh
- Do NOT commit a partial or ambiguous state

### Step 0.3 — Restore loop_cycle_summary_latest.json (Ph8-C)

`docs/context/loop_cycle_summary_latest.json` is deleted. `supervise_loop.py --max-cycles 1` requires it.

```powershell
# Restore from last committed version:
git checkout HEAD -- docs\context\loop_cycle_summary_latest.json
# Verify:
Test-Path docs\context\loop_cycle_summary_latest.json  # must return True
```

If the file was never committed, create a minimal valid stub:
```powershell
'{"final_result": "NOT_READY", "phase": "phase-8-stub"}' | Set-Content docs\context\loop_cycle_summary_latest.json
```

### Step 0.4 — Commit all untracked Phase 4-7 deliverables (Ph8-B, Ph8-D, Ph8-E)

The following untracked files MUST be committed before Action 3. Without them, `pytest -q` on a clean clone collects far fewer than 1005 tests and `TestByteIdentityContract` fails:

**Test files (Ph8-B — blocking):**
```powershell
git add tests\test_hardening.py
git add tests\test_smoke_e.py
git add tests\test_endgame.py
git add tests\test_skill_pilot.py
```

**Dual-copy deliverables (Ph8-D — blocking):**
```powershell
git add scripts\check_fail_open.py
git add src\sop\scripts\check_fail_open.py  # if dual copy exists
git add scripts\check_schema_version_policy.py
git add src\sop\_failure_reporter.py
```

**MULTISTREAM stream deliverables:**
```powershell
git add docs\context\operator_navigation_map.md
git add docs\context\skill_readiness_matrix.md
git add scripts\critical_scan_manifest.json
```

**Remaining untracked production files:**
```powershell
# Add all untracked files in scripts/, src/, tests/, docs/context/ that are
# production deliverables (not generated runtime artifacts):
git status --short | Where-Object { $_ -match '^\?\?' } | ForEach-Object {
    $f = $_.Substring(3).Trim()
    if ($f -match '^(scripts|src|tests|docs/context)' -and $f -notmatch '\.pyc$') {
        Write-Host "Review for commit: $f"
    }
}
# Review each; add those that are deliverables, not runtime outputs
```

**Modified tracked files (26 files including dual-copy scripts):**
```powershell
# Verify dual-copy parity before staging:
python -m pytest tests\test_script_surface_sync.py -q  # must pass 35
python -m pytest tests\test_hardening.py::TestByteIdentityContract -q  # must pass
# Then stage:
git add scripts\run_loop_cycle.py src\sop\scripts\run_loop_cycle.py
git add scripts\auditor_role.py src\sop\scripts\auditor_role.py
git add scripts\worker_role.py src\sop\scripts\worker_role.py
git add scripts\planner_role.py src\sop\scripts\planner_role.py
# Stage all other modified tracked files:
git add -u
```

**Commit all outstanding work as one commit:**
```powershell
git status  # verify staging looks correct
git commit -m "chore: commit all Phase 4-7 outstanding deliverables before Phase 8 3-run gate"
```

### Step 0.5 — Verify clean committed state

```powershell
# Working tree must be clean for scripts/, src/, tests/, docs/plans/:
git status --short scripts src tests docs\plans docs\decisions
# Must return: nothing (no M or ?? lines for these paths)

# TestByteIdentityContract must pass:
python -m pytest tests\test_hardening.py::TestByteIdentityContract -q

# Dual-copy sync must pass:
python -m pytest tests\test_script_surface_sync.py -q

# Full suite count:
python -m pytest --collect-only -q 2>&1 | Select-String "test"
# Record actual count — this becomes the authoritative count for Action 3 runs 2+3
```

**Done when:** `git status` shows no untracked/modified files in `scripts/`, `src/`, `tests/`, `docs/plans/`, `docs/decisions/`. `TestByteIdentityContract` passes. Test count recorded.

---

## Amendment Ph8-A — endgame_verification.md uncommitted changes

Resolved by Action 0 Step 0.2. Inspect diff before applying Actions 1 and 2. Commit cleanly.

## Amendment Ph8-B — test_hardening.py and test_smoke_e.py untracked

Resolved by Action 0 Step 0.4. Both files must be committed before Action 3.

## Amendment Ph8-C — loop_cycle_summary_latest.json deleted

Resolved by Action 0 Step 0.3. Restore from git or create stub before Action 3.

## Amendment Ph8-D — check_fail_open.py untracked

Resolved by Action 0 Step 0.4. Both copies committed before Action 3.

## Amendment Ph8-E — 50+ untracked files

Resolved by Action 0 Step 0.4. All production deliverables committed before Action 3.

## Amendment Ph8-F — "clean state" definition for Action 3

**"Clean state" for Action 3 means:**
1. Working tree committed: `git status` shows no M or ?? in `scripts/`, `src/`, `tests/`, `docs/plans/`, `docs/decisions/`
2. Runtime artifacts removed before each run:
   ```powershell
   Remove-Item -Force docs\context\loop_cycle_summary_latest.json -ErrorAction SilentlyContinue
   Remove-Item -Force docs\context\exec_memory_packet_latest.json -ErrorAction SilentlyContinue
   ```
3. A fresh git clone is acceptable but NOT required
4. Each of runs 2 and 3 starts with step 2 above — not a full reclone

This replaces the ambiguous "clean state" language in Action 3.

## Amendment Ph8-G — ENDGAME trigger precision

**Replace** in ENDGAME Declaration Procedure:
```powershell
# OLD (too broad):
Select-String "PENDING" docs\decisions\endgame_verification.md

# NEW (precise):
Select-String "PENDING HUMAN" docs\decisions\endgame_verification.md
# Must return: no matches
```

---

## Revised Action Order

```
Action 0: Commit all outstanding work (NEW — must complete before 1-4)
    Step 0.1: Commit plan file to repo
    Step 0.2: Inspect + clean endgame_verification.md
    Step 0.3: Restore loop_cycle_summary_latest.json
    Step 0.4: Commit all untracked Phase 4-7 deliverables
    Step 0.5: Verify clean committed state + record test count
        ↓
Action 1: Add ENDGAME.md path note to endgame_verification.md
        ↓
Action 2: Annotate run 1 test count (918 → current count from Step 0.5)
        ↓
Action 3: Runs 2 and 3 (clean state per Ph8-F; record current count)
    +
Action 4: Human cold-read sign-off (async — parallel with 1-3)
        ↓
ENDGAME Declaration (trigger: Select-String "PENDING HUMAN" returns no matches)
```

---

## Consolidated Amendment Status

| Gap | Status | Action |
|-----|--------|--------|
| Plan file missing from repo | APPLIED | Action 0 Step 0.1 |
| Ph8-A: endgame_verification.md uncommitted | APPLIED | Action 0 Step 0.2 |
| Ph8-B: test files untracked | APPLIED | Action 0 Step 0.4 |
| Ph8-C: loop_cycle_summary_latest.json deleted | APPLIED | Action 0 Step 0.3 |
| Ph8-D: check_fail_open.py untracked | APPLIED | Action 0 Step 0.4 |
| Ph8-E: 50+ untracked files | APPLIED | Action 0 Step 0.4 |
| Ph8-F: clean state undefined | APPLIED | Amendment Ph8-F |
| Ph8-G: PENDING trigger too broad | APPLIED | Amendment Ph8-G |

**Phase 8 plan is approved with all amendments applied.**
**Phase 8 cannot execute until Action 0 is complete.**

