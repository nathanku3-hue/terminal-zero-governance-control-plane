# Repo Map Skill Pilot — Rollback Plan

**Date**: 2026-03-26  
**Status**: ACTIVE — required by D-190 before any execution semantics land  
**Skill**: `repo-map` (5C.1, `src/sop/scripts/repo_map.py`)  
**Authority boundary**: read-only, zero write authority, no new authority path  
**Decision**: D-190

---

## 1. What This Pilot Adds

The `repo-map` skill wires the existing `src/sop/scripts/repo_map.py` implementation as a callable skill via the `skill_resolver.py` seam. Concretely:

- `extension_allowlist.yaml` — `repo-map` entry added (status: active, risk_level: LOW)
- `.sop_config.yaml` — `repo-map` added to `active_skills`
- `skills/registry.yaml` — `repo-map` catalog entry added
- `skills/repo_map/skill.yaml` — skill manifest pointing to existing implementation

**Nothing else changes.** No new runtime hooks, no new authority paths, no changes to the auditor/CEO-GO chain.

---

## 2. Rollback Trigger

Roll back this pilot (remove `repo-map` from all surfaces below) if ANY of the following occur:

| Trigger | Action |
|---------|--------|
| `skill_resolver.py` raises an error or degrades due to `repo-map` entry | Remove from allowlist + config |
| `validate_skill_activation.py` fails after `repo-map` registration | Remove from allowlist + config |
| `build_context_packet.py --validate` fails after registration | Remove from allowlist + config |
| Full test suite regresses (any new failures) | Remove registration; fix root cause |
| PM/CEO revokes D-190 | Remove all surfaces immediately |
| Any governance gate weakened by this change | Remove immediately, escalate |

---

## 3. Rollback Procedure

### Step 1 — Remove from `.sop_config.yaml`

Delete the `repo-map` line from `active_skills`:

```yaml
active_skills:
  - safe-db-migration
  # repo-map line removed
```

### Step 2 — Remove from `extension_allowlist.yaml`

Delete the `repo-map` skill block entirely.

### Step 3 — Remove from `skills/registry.yaml`

Delete the `repo-map` skill entry entirely.

### Step 4 — Remove or archive `skills/repo_map/skill.yaml`

```bash
git rm skills/repo_map/skill.yaml
```

**Do NOT delete `src/sop/scripts/repo_map.py`** — the 5C.1 implementation is independent of the skill wiring and must not be removed.

### Step 5 — Verify

```bash
python scripts/validate_skill_activation.py
python scripts/build_context_packet.py --validate
python -m pytest -q
```

All three must pass before rollback is declared complete.

### Step 6 — Log rollback in decision log

```markdown
### Rollback: repo-map skill pilot
**Date:** <YYYY-MM-DD>
**Trigger:** <reason>
**Evidence:** <paths>
**Action:** Removed repo-map from allowlist, config, registry, and manifest
**Underlying implementation (repo_map.py) preserved:** YES
**Recovery Criteria:** validate_skill_activation + build_context_packet --validate + full suite all pass
```

---

## 4. Verification After Registration

After adding `repo-map` to all surfaces, run:

```bash
python scripts/validate_skill_activation.py
python scripts/build_context_packet.py --validate
python -m pytest -q
```

All three must pass. If any fails, execute rollback procedure immediately.

---

## 5. What Is NOT Rolled Back

- `src/sop/scripts/repo_map.py` — Phase 5C.1 implementation, governed by D-189, independent of skill wiring
- `tests/test_phase5c_repo_map.py` — test coverage for the implementation
- D-189 decision log entry

---

## 6. Governance Notes

- This rollback plan is a D-190 prerequisite. It must be committed before any execution semantics land.
- The `repo-map` skill is read-only. It cannot modify files, commit changes, or invoke any write-authority path.
- The pilot scope is one skill, one seam (`skill_resolver.py`). No other surfaces are touched.
- PM/CEO can revoke D-190 at any time. Rollback is one git commit.
