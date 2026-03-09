# Artifact Policy: Source vs. Generated

## Purpose

This policy establishes clear boundaries between source files (committed to version control) and generated artifacts (ephemeral state, ignored by git). This prevents merge conflicts on machine-generated state and keeps the repository focused on human-authored source of truth.

## Source Files (Committed)

These files represent human-authored logic, templates, and documentation:

- **Scripts**: `scripts/*.py`, `scripts/*.ps1`, `scripts/*.sh`
- **Tests**: `tests/test_*.py`, `e2e_test/*.py`
- **Documentation**: `docs/*.md`, `docs/templates/*.md`, `docs/phase_brief/*.md`
- **Configuration**: `*.json` (when hand-authored), `*.yaml`, `*.toml`
- **Skills**: `.codex/skills/**/*`, `skills/**/*`

## Generated Artifacts (Ignored)

These files are produced by scripts and represent ephemeral runtime state:

- **Latest state files**: `docs/context/*_latest.json`, `docs/context/*_latest.md`
  - Examples: `exec_memory_packet_latest.json`, `board_decision_brief_latest.md`
  - Rationale: These are regenerated on every loop cycle and represent current state, not historical record

- **Temporary directories**: `.tmp/`, `tmp/`, `temp/`
  - Used for scratch work, test fixtures, intermediate processing

- **Python artifacts**: `__pycache__/`, `*.pyc`, `.pytest_cache/`

- **Build artifacts**: `dist/`, `build/`, `*.egg-info/`

## Rationale

1. **Avoid merge conflicts**: Generated artifacts change frequently and mechanically. Committing them creates noise and conflicts when multiple agents or humans work in paral**Single source of truth**: Scripts are the source of truth. Artifacts are derived state. If artifacts are lost, they can be regenerated from source.

3. **Clear intent**: Developers can immediately distinguish between "what the system does" (source) and "what the system produced" (artifacts).

4. **Audit trail**: Historical artifacts (e.g., `docs/context/phase_end_logs/*.md`) are committed because they represent point-in-time snapshots for audit purposes, not current state.

## Exceptions

Some generated files ARE committed when they serve as historical records:

- **Phase end logs**: `docs/context/phase_end_logs/phase_end_handover_summary_*.md`
- **Weekly summaries**: `docs/context/ceo_weekly_summary_YYYYMMDD.md`
- **Audit records**: Files with timestamps that represent completed milestones

The key distinction: if it has a timestamp and represents a completed event, it's a record (commit it). If it has `_latest` in the name, it's ephemeral state (ignore it).

## Verification

To verify this policy is working:

```bash
# Check that _latest files are ignored
git status | grep -i latest
# Should return nothing

# Check that source files are tracked
git ls-files scripts/ tests/ docs/*.md
# Should show all source files
```

## Maintenance

When adding new generated artifacts:
1. Add the pattern to `.gitignore`
2. Document the rationale in this file
3. Verify with `git status` that existing artifacts are now ignored
