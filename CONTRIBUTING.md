# Contributing

Thanks for contributing to Terminal Zero.

This repository is a script-driven governance control plane, not a hosted application. Contributions should prioritize deterministic local execution, auditable artifacts, and fail-closed behavior.

## Before You Start

1. Read `README.md` for repository intent and entrypoints.
2. Read `OPERATOR_LOOP_GUIDE.md` for the main startup -> loop -> closure flow.
3. Read `docs/loop_operating_contract.md` and `docs/runbook_ops.md` for operating constraints.

## Development Setup

Canonical dependency metadata for this script-first repo lives in `pyproject.toml`.
Use `constraints.txt` and `constraints-dev.txt` for pinned, validated installs.
`requirements.txt` and `requirements-dev.txt` remain compatibility shims for tools that still expect requirements files.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -c constraints.txt .
python -m pip install -c constraints-dev.txt ".[dev]"
```

## Contribution Scope

Good contribution examples:
- bug fixes in `scripts/` or validators,
- test coverage improvements in `tests/`,
- documentation corrections in `docs/`,
- operational safety hardening (truth checks, fail-closed behavior, artifact integrity).

Out of scope without prior agreement:
- introducing a hosted control plane or service promises,
- adding heavy frameworks unrelated to current script-first architecture,
- bypassing or weakening closure/validation gates.

## Pull Request Process

1. Keep changes small and focused on one concern.
2. Update docs in the same PR when behavior changes.
3. Include validation evidence in the PR description:
   - command(s) run,
   - key outcome lines,
   - interpreter used (for example `python --version`).
4. Link related issue(s) if applicable.

Use `.github/pull_request_template.md` when opening your PR.

## Validation Checklist

Run focused checks for touched areas, then run broader checks as needed.

Typical smoke checks:

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
python scripts/run_fast_checks.py --repo-root .
```

Typical tests:

```powershell
python -m pytest tests -v --tb=short
```

## Code and Docs Expectations

- Preserve script-first, artifact-contract architecture.
- Prefer explicit failure signals over silent degradation.
- Keep logs/evidence readable and machine-checkable.
- Do not commit secrets or credentials.

## Communication

Use GitHub Issues for bugs, enhancement requests, and clarifying questions.
For conduct and support expectations, see `CODE_OF_CONDUCT.md` and `SUPPORT.md`.
