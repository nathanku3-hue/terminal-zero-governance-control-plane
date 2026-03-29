# Skill Readiness Matrix

> Stream C artifact — Phase 3. Consumes `skills_status` field produced by Stream B H-5.
> Read this before interpreting any skills-related output in loop cycle summaries or run failure artifacts.
> All paths in this file are repo-root relative.

---

## How to Use This Matrix

The loop emits a `skills_status` field in its run output. Match that value to one of the three
sections below to determine the proceed/block ruling and the correct recovery path.

**Diagnostic query block** — run these before concluding a skills issue is real:

```powershell
# 1. Confirm sop package is installed and resolves from the expected location
python -c "import sop; print(sop.__file__)"

# 2. Check whether the skill resolver module is present in the installed package
python -c "from sop import skill_resolver; print('resolver present')"

# 3. List skills visible to the resolver (empty output = EMPTY_BY_DESIGN, error = RESOLVER_UNAVAILABLE)
python -m sop.skill_resolver list 2>&1

# 4. Confirm the active sop entry point
sop run --help 2>&1 | Select-String 'usage'
```

Run all four checks before escalating. Capture stdout and stderr for each.

---

## Section 1 — `RESOLVER_UNAVAILABLE`

### Meaning

The skill resolver module could not be imported or located by the loop. This indicates a broken
or incomplete package installation, a shadowed module on `sys.path`, or a missing resolver
component in the installed `sop` package. This value signals an infrastructure defect, not an
intentional configuration.

### Proceed / Block Ruling

**BLOCK** — Do not proceed with a loop pass that reports `RESOLVER_UNAVAILABLE`. The resolver
failure means skill activation state is unknown; any downstream skill-dependent step may silently
degrade or produce incorrect results.

### First Diagnostic Step

Run check 2 from the diagnostic query block above:

```powershell
python -c "from sop import skill_resolver; print('resolver present')"
```

If this raises `ImportError` or `ModuleNotFoundError`, the resolver component is absent from the
installed package. If it succeeds but the loop still emits `RESOLVER_UNAVAILABLE`, proceed to
checks 1 and 3 to identify path shadowing.

### Recovery Steps

1. Reinstall the package from repo root: `pip install -e .`
2. Confirm the installed location matches the repo: `python -c "import sop; print(sop.__file__)"`
3. If a shadowed module is found on `sys.path`, remove or rename it before reinstalling.
4. After reinstall, run the full diagnostic query block and confirm check 2 passes.
5. Re-run the loop command. Verify `skills_status` is no longer `RESOLVER_UNAVAILABLE`.
6. If the issue persists, check `docs/context/run_failure_latest.json` for
   `failure_class=SKILLS_RESOLVER_UNAVAILABLE` and inspect `failed_component` and
   `recoverability` fields.

### Artifact to Read

`docs/context/run_failure_latest.json` — look for `failure_class`, `failed_component`,
`recoverability`, and `artifact_write_failed` fields. Cross-reference with
`docs/context/loop_cycle_summary_latest.json` for the step name where the failure occurred.

---

## Section 2 — `EMPTY_BY_DESIGN`

### Meaning

The skill resolver is present and functional, but no skills are registered or activated for this
repo. This is an intentional configuration state, not a defect. It occurs when the repo has not
been set up with any skills, or when all previously active skills have been deliberately
deactivated.

### Proceed / Block Ruling

**PROCEED** — `EMPTY_BY_DESIGN` is not an error condition. The loop can run normally. Skill-
dependent steps will be skipped or will no-op as designed. No recovery action is required unless
the operator intended to activate skills for this run.

### First Diagnostic Step

Run check 3 from the diagnostic query block above:

```powershell
python -m sop.skill_resolver list 2>&1
```

Expect empty output or an explicit "no skills registered" message. If this command errors instead
of returning empty, re-classify as `RESOLVER_UNAVAILABLE` and follow Section 1.

### Recovery Steps

No recovery needed if this is the intended state. If skills were expected to be active:

1. Verify the skill registration files exist under `.codex/skills/` (canonical) or `skills/`
   (project deliverables — read-only unless brief authorizes).
2. Confirm skill activation configuration matches the current phase brief.
3. If skills should be active, register them per the skill activation protocol and re-run.
4. After registration, re-run the loop and confirm `skills_status` changes from
   `EMPTY_BY_DESIGN` to `OK`.

### Artifact to Read

`.codex/skills/README.md` — canonical skill registry. Confirm which skills are registered and
whether any are expected to be active for the current phase. Cross-reference with the active
phase brief in `docs/phase_brief/`.

---

## Section 3 — `OK`

### Meaning

The skill resolver is present, functional, and reports one or more skills in a healthy activation
state. The loop can proceed with full skill support. No operator action is required regarding
skills.

### Proceed / Block Ruling

**PROCEED** — No action needed. Skills are healthy. Continue with the normal operator sequence.

### First Diagnostic Step

No diagnostic action required. If you want to confirm which skills are active:

```powershell
python -m sop.skill_resolver list 2>&1
```

Expect a non-empty list of registered and active skills.

### Recovery Steps

None required. If a specific skill is not activating as expected despite `OK` status, check the
individual skill's `SKILL.md` trigger conditions and the active phase brief.

### Artifact to Read

`.codex/skills/README.md` — verify the expected skills are listed and their trigger conditions
match the current task. Consult `docs/context/loop_cycle_summary_latest.json` for the
`skill_activation` field if detailed activation trace is needed.

---

## Quick Reference

| `skills_status` value | Ruling | Action |
|---|---|---|
| `RESOLVER_UNAVAILABLE` | **BLOCK** | Reinstall package; check path shadowing |
| `EMPTY_BY_DESIGN` | **PROCEED** | No action unless skills were expected |
| `OK` | **PROCEED** | No action needed |

---

## Integration Note

This matrix is designed to be read independently of the running loop. All three values are
defined in the Stream B H-5 implementation (`sop/` package). Stream C finalizes this matrix
after H-5 is merged. If `skills_status` is absent from a run artifact, treat as
`RESOLVER_UNAVAILABLE` until H-5 is confirmed deployed.
