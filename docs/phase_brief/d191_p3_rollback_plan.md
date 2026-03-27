# D-183 P3 Rollback Plan

**Date**: 2026-03-26  
**Status**: ACTIVE — required by D-191 before any P3 execution semantics land  
**Decision**: D-191  
**Items covered**: P3.1 memory/rollback, P3.2 manifest-driven selective install, P3.3 canonical-to-multi-target, P3.4 specialist delegation

---

## 1. What P3 Adds

All four items are **additive, surface-only changes** to existing seams. No new runtime hooks, no new authority paths, no kernel changes.

| Item | Change | Seam |
|------|--------|------|
| P3.1 Memory/rollback | `skill_resolver.py` surfaces `rollback_state` from skill manifest | `skill_resolver.py` |
| P3.2 Manifest-driven selective install | `skill_resolver.py` surfaces `installs` from skill manifest | `skill_resolver.py` |
| P3.3 Canonical-to-multi-target | `skill_resolver.py` surfaces `targets` from skill manifest | `skill_resolver.py` |
| P3.4 Specialist delegation | tracked `skills/repo_map/skill.yaml` gains `specialist_delegation`; local `benchmark/subagent_routing_matrix.yaml` remains validator seam | `skills/repo_map/skill.yaml` + local benchmark routing matrix |

Skill manifests (`skills/*/skill.yaml`) gain optional `installs`, `targets`, and `rollback_state` fields. No existing field is removed or modified.

---

## 2. Rollback Triggers

Roll back all P3 changes if ANY of the following occur:

| Trigger | Action |
|---------|--------|
| `validate_skill_activation.py` fails | Revert `skill_resolver.py` to pre-P3 version |
| `build_context_packet.py --validate` fails | Revert `skill_resolver.py` |
| Full test suite regresses | Revert changes; fix root cause |
| Routing validator fails | Revert tracked `skills/repo_map/skill.yaml` specialist delegation block and remove the local benchmark delegation entry if present |
| PM/CEO revokes D-191 | Revert all P3 surfaces immediately |

---

## 3. Rollback Procedure

### P3.1 / P3.2 / P3.3 — Revert skill_resolver.py

```bash
git revert <P3-commit-hash> --no-edit
# OR restore from pre-P3 state:
git checkout <pre-P3-hash> -- scripts/utils/skill_resolver.py
```

### P3.4 — Revert tracked specialist delegation declaration

```bash
git checkout <pre-P3-hash> -- skills/repo_map/skill.yaml
```

If `benchmark/subagent_routing_matrix.yaml` exists locally, remove `repo-map` from `specialist_deputy.skill_delegation` there as well. The benchmark routing matrix is gitignored under `/benchmark/`, so this local cleanup is operational rather than tracked.

### Revert skill manifests

Remove `installs`, `targets`, and `rollback_state` sections from `skills/*/skill.yaml`.

### Verify after rollback

```bash
python scripts/validate_skill_activation.py
python scripts/validate_routing_matrix.py benchmark/subagent_routing_matrix.yaml .
python scripts/build_context_packet.py --validate
python -m pytest -q
```

All four must pass before rollback is declared complete.

---

## 4. What Is NOT Rolled Back

- `src/sop/scripts/repo_map.py` (D-189)
- `skills/repo_map/skill.yaml` (D-190 pilot) except for the P3-added `specialist_delegation` block
- `docs/phase_brief/repo_map_skill_rollback_plan.md` (D-190)
- D-189, D-190, D-191 decision log entries

---

## 5. Governance Notes

- P3 changes are advisory-surface additions only. They extend what the resolver surfaces and tracked skill metadata; they do not add execution semantics.
- No new authority paths are introduced.
- PM/CEO can revoke D-191 at any time. Full rollback is one `git revert`.
