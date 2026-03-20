# Release Readiness Checklist — v0.1.0

Status: IN_PROGRESS
Created: 2026-03-20
Owner: PM

## Overview

This checklist gates the first public beta release of `terminal-zero-governance`.

Reference: `RELEASING.md` cut criteria (docs aligned, tests pass, CLI smoke, version match, changelog entry).

---

## C1 — Pre-Tag Cleanup (MUST complete before `git tag v0.1.0`)

| # | Item | Status | Action | Evidence |
|---|------|--------|--------|----------|
| C1.1 | Trusted Publisher | PENDING | Configure at https://pypi.org/manage/project/terminal-zero-governance/settings/publishing/ | Owner/repo/workflow green |
| C1.2 | Release notes owner | DONE | Fill `Release owner:` field in `RELEASE_NOTES_v0.1.0_PUBLIC_BETA.md:3` | @nathanku3-hue |
| C1.3 | CODEOWNERS confirmation | DONE | Confirm maintainer handle OR add follow-up note per `RELEASING.md:122` | @nathanku3-hue in .github/CODEOWNERS |
| C1.4 | README roadmap drift | DONE | Fix line 345: "W2 (Quant pilot) partial" → reflect kernel-complete state | Matches `ROADMAP.md` (all waves COMPLETE) |
| C1.5 | CHANGELOG publish drift | DONE | Fix line 60: remove "via workflow_run", state actual `needs:` gate | Matches `release-validation.yml:356` |
| C1.6 | Worktree clean | DONE | Commit or stash uncommitted changes before tagging | `git status --short` empty |
| C1.7 | Tests pass | DONE | Run `python -m pytest -q` | 475 passed, 1 skipped (78s) |
| C1.8 | CLI smoke | DONE | Run `sop --help && sop version && sop init /tmp/smoke-test` | sop --help ✓, sop version (0.1.0) ✓ |

**Why before tag:** `RELEASING.md:38` requires "Docs aligned" as explicit cut criterion. C1.4 and C1.5 are doc drift that would ship incorrect information in v0.1.0.

---

## C2 — Tag Push and Verification (MUST complete before declaring v0.1.0 complete)

| # | Item | Status | Action | Evidence |
|---|------|--------|--------|----------|
| C2.1 | Create tag | PENDING | `git tag v0.1.0` | Tag exists locally |
| C2.2 | Push tag | PENDING | `git push origin v0.1.0` | Workflow triggers in Actions |
| C2.3 | Validation pass | PENDING | Monitor Actions: cli-smoke, backward-compat, semver-check, release-gate, test-suite | All 5 jobs pass |
| C2.4 | Publish succeed | PENDING | Monitor publish-pypi job | Wheel published to PyPI |
| C2.5 | Install verify | PENDING | `pip install terminal-zero-governance && sop version` | Version matches tag |
| C2.6 | Wheel-smoke manual | PENDING | Trigger workflow_dispatch with `run_wheel_smoke: true` | Wheel install from built artifact passes |
| C2.7 | GitHub release | PENDING | Create release with `RELEASE_NOTES_v0.1.0_PUBLIC_BETA.md` body | Release visible on GitHub |

**Why after push:** `git push origin v0.1.0` triggers the workflow per `RELEASING.md:93`. C2 verifies the outcome, not the input.

**Nuance on C2.6:** wheel-smoke is currently optional (`release-validation.yml:273`). Run manually once for v0.1.0 confidence before promoting to mandatory in C3.

---

## C3 — Post-Release Hardening (SHOULD complete before v0.1.1)

| # | Item | Priority | Action | Rationale |
|---|------|----------|--------|-----------|
| C3.1 | Wheel-smoke mandatory | Medium | Promote wheel-smoke job to tag-triggered workflow | Proves real install from built artifact on every release |
| C3.2 | Release manifest | Medium | Add `upload-artifact` step; emit `release_manifest_{tag}.json` | Durable record: tag, run_id, wheel_hash, py_url |
| C3.3 | Shipped-outcome capture | Low | Wire `capture_profile_outcome_record.py` into release checklist | Feedback loop per `shipped_outcome_feedback_protocol.md` |
| C3.4 | macOS coverage | Low | Accept as best-effort; add if demand emerges | Already documented in `RELEASING.md:21` |

**Why after v0.1.0:** These are hardening, not blockers. Kernel is FROZEN; operational refinements driven by real release experience.

---

## Immediate Next Step

**C1.1: Configure PyPI Trusted Publisher**

1. Navigate to: https://pypi.org/manage/project/terminal-zero-governance/settings/publishing/
2. Add trusted publisher:
   - Owner: `<github-owner-or-org>`
   - Repository: `<repo-name>`
   - Workflow: `release-validation.yml`
   - Environment: (leave blank)
3. Save configuration.
4. Mark C1.1 PASS.

---

## Blockers

None currently.

---

## Notes

- Worktree currently clean (`git status --short` empty). Recheck before C1.6 if local changes resume.
- Release notes explicitly document known limitations (manual freshness discipline, macOS best-effort).
- Doc drifts fixed (2026-03-20): README:345, CHANGELOG:60, release notes owner placeholder marked with TODO.
