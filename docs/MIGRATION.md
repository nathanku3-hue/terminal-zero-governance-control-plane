# Migration Guide: scripts/*.py to sop CLI

## Status

- **Effective:** 2026-03-21
- **Decision:** D-183
- **Owner:** PM / Architecture Office

## Overview

This document defines the migration path from legacy `scripts/*.py` entrypoints to the canonical `sop` CLI.

**Key principle:** Both surfaces remain functional, but new users should prefer `sop`.

## Canonical Surface

Per `pyproject.toml:22`, the packaged canonical surface is:

```bash
sop startup --repo-root .
sop run --repo-root .
sop validate --repo-root .
sop takeover --repo-root .
sop supervise --max-cycles 1
sop init <target-dir>
```

Install: `pip install terminal-zero-governance`

## Compatibility Surface

Per `RELEASING.md:23`, `scripts/*.py` entrypoints remain functional for existing workflows:

```bash
python scripts/startup_codex_helper.py --repo-root .
python scripts/run_loop_cycle.py --repo-root .
python scripts/validate_loop_closure.py --repo-root .
python scripts/print_takeover_entrypoint.py --repo-root .
python scripts/supervise_loop.py --repo-root .
```

## Mapping Table

| sop CLI | scripts/*.py | Notes |
|---------|--------------|-------|
| `sop startup` | `startup_codex_helper.py` | Same entrypoint |
| `sop run` | `run_loop_cycle.py` | Same entrypoint |
| `sop validate` | `validate_loop_closure.py` | Output parity tested |
| `sop takeover` | `print_takeover_entrypoint.py` | Output parity tested |
| `sop supervise` | `supervise_loop.py` | Same entrypoint |
| `sop init` | (no script equivalent) | New in sop CLI |

## Artifact Parity Contract

Both surfaces MUST produce identical artifacts:

| Artifact | Path |
|----------|------|
| Loop cycle summary | `docs/context/loop_cycle_summary_latest.json` |
| Exec memory packet | `docs/context/exec_memory_packet_latest.json` |
| CEO go signal | `docs/context/ceo_go_signal.md` |
| Expert request | `docs/context/expert_request_latest.json` |
| PM/CEO research brief | `docs/context/pm_ceo_research_brief_latest.json` |
| Board decision brief | `docs/context/board_decision_brief_latest.json` |
| Next round handoff | `docs/context/next_round_handoff_latest.json` |
| Skill activation | `docs/context/skill_activation_latest.json` |

**Parity tests** in `tests/test_cli_script_parity.py` verify output parity for `takeover` and `validate` commands. Full artifact comparison for `startup`, `run`, and `supervise` is tracked for P1d.

## Anti-Drift Rules

To prevent `scripts/` and `src/sop/scripts/` from diverging:

1. **Canonical source:** `src/sop/scripts/` uses package-safe imports (`sop.scripts.*` with `scripts.*` fallback). `scripts/*.py` remain parallel implementations during transition.
2. **Parity tests:** Every release must pass `tests/test_cli_script_parity.py`.
3. **Deprecation path:** If a script is removed, the corresponding `sop` command must remain stable.
4. **New features:** New features go to `sop` CLI first. Backport to scripts is optional.

**Note:** The thin-wrapper architecture (scripts/*.py delegating to src/sop/scripts/) is the target state. During transition, both surfaces maintain parallel implementations that must produce identical artifacts.

## Migration Timeline

| Phase | Status | Description |
|-------|--------|-------------|
| v0.1.0 | CURRENT | Both surfaces functional, sop preferred |
| v0.2.0 | PLANNED | Add deprecation warning to scripts/*.py --help |
| v1.0.0 | PLANNED | scripts/*.py may be archived; sop is sole surface |

## For New Users

1. Install: `pip install terminal-zero-governance`
2. Initialize: `sop init my-project && cd my-project`
3. Run loop: `sop startup --repo-root . && sop run --repo-root .`
4. Validate: `sop validate --repo-root .`
5. Handoff: `sop takeover --repo-root .`

## For Existing Users

1. Continue using `scripts/*.py` if preferred
2. Test `sop` CLI in parallel: `sop --help`
3. Report any parity issues via GitHub issues
4. Plan migration before v1.0.0

## Related Documents

- `RELEASING.md:23` — Compatibility commitment
- `pyproject.toml:22` — Package configuration
- `tests/test_cli_script_parity.py` — Parity tests
- `tests/test_system_control_plane_integration.py` — Full loop contract tests
