# Artifact Policy: Source vs. Generated

## Purpose

This policy establishes clear boundaries between source files (committed to version control) and generated artifacts (ephemeral state, ignored by git). This prevents merge conflicts on machine-generated state and keeps the repository focused on human-authored source of truth.

## Source Files (Committed)

These files represent human-authored logic, templates, and documentation:

- **Scripts**: `scripts/*.py`, `scripts/*.ps1`, `scripts/*.sh`
- **Tests**: `tests/**/*.py`
- **Documentation**: `AGENTS.md`, `OPERATOR_LOOP_GUIDE.md`, `docs/*.md`, `docs/templates/*.md`, `docs/phase_brief/*.md`
- **Curated repo-root docs**: hand-maintained mirrors such as `THESIS_PULL_LATEST.md` when they are intentionally authored operator docs rather than runtime output
- **Configuration**: `*.json` (when hand-authored), `*.yaml`, `*.toml`
- **Skills**: `.codex/skills/**/*`, `skills/**/*`

## Generated Artifacts (Ignored)

These files are produced by scripts and represent ephemeral runtime state:

- **Latest state files**: `docs/context/*_latest.json`, `docs/context/*_latest.md`
  - Examples: `exec_memory_packet_latest.json`, `board_decision_brief_latest.md`
  - Rationale: these are regenerated on every loop cycle and represent current state, not historical record

- **Generated repo-root convenience mirrors**:
  - `NEXT_ROUND_HANDOFF_LATEST.md`
  - `EXPERT_REQUEST_LATEST.md`
  - `PM_CEO_RESEARCH_BRIEF_LATEST.md`
  - `BOARD_DECISION_BRIEF_LATEST.md`
  - `MILESTONE_OPTIMALITY_REVIEW_LATEST.md`
  - `TAKEOVER_LATEST.md`
  - These are convenience copies of authoritative artifacts and should not be treated as primary source files

- **Temporary directories**: `.tmp/`, `.tmp_pytest/`, `.ptemp/`, `tmp_test/`, `e2e_test/`
  - Used for scratch work, transient test repos, exploratory end-to-end fixtures, and intermediate processing

- **Python artifacts**: `__pycache__/`, `*.pyc`, `.pytest_cache/`

- **Build artifacts**: `dist/`, `build/`, `*.egg-info/`

## Rationale

1. **Avoid merge conflicts**: generated artifacts change frequently and mechanically. Committing them creates noise and conflicts when multiple agents or humans work in parallel.
2. **Single source of truth**: scripts, tests, and hand-authored docs are the source of truth. Runtime artifacts are derived state and should be regenerated when needed.
3. **Clear intent**: contributors should be able to distinguish between what the system is (`scripts/`, `tests/`, contracts, runbooks) and what the system most recently produced (`docs/context/*_latest.*`, repo-root convenience mirrors).
4. **Historical records are selective exceptions**: some dated artifacts are intentionally committed as audit records, but current-state mirrors should not crowd the repo surface.
5. **Filename alone is not enough**: `_LATEST` in a filename does not automatically make a file generated. Commit status depends on whether the file is curated source documentation or machine-produced state.

## Exceptions

Some generated files are committed when they serve as historical records:

- **Phase-end logs**: timestamped files under `docs/context/phase_end_logs/` when intentionally retained for audit history
- **Weekly summaries**: `docs/context/ceo_weekly_summary_YYYYMMDD.md`
- **Completed milestone records**: dated artifacts that capture a finished event rather than mutable current state
- **Curated operator mirrors**: `THESIS_PULL_LATEST.md` remains committed because it is currently maintained as a thin human-authored operator document, not an auto-generated loop artifact

## Verification

To verify this policy is working:

```powershell
# Generated convenience mirrors and _latest state should be ignored
git check-ignore NEXT_ROUND_HANDOFF_LATEST.md TAKEOVER_LATEST.md docs/context/exec_memory_packet_latest.json

# Source docs should not be ignored
git check-ignore OPERATOR_LOOP_GUIDE.md
# `git check-ignore` should print nothing and exit non-zero for this path

# Scratch/e2e sandbox content should be ignored
git check-ignore e2e_test\example_test.py
```

## Maintenance

When adding new generated artifacts:
1. Add the pattern to `.gitignore`
2. Document the rationale in this file
3. Verify with `git check-ignore` and `git status --short` that the behavior matches the intended boundary
