# Operator Loop Guide

`README.md` is the minimal public quickstart; this guide is the fuller local operator sequence for the current control-plane path only.

Run these commands from the repository root. The examples below assume PowerShell and a repo-local `.venv`. If `.venv` is unavailable, use `python` from a compatible Python `3.12+` interpreter and record that interpreter in your run notes.

Historical quant/data/benchmark commands are intentionally out of this guide. They live in `docs/archive/legacy_quant_runbook.md`.

## Recommended command sequence

```powershell
.venv\Scripts\python scripts/startup_codex_helper.py --repo-root .
.venv\Scripts\python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
.venv\Scripts\python scripts/validate_loop_closure.py --repo-root .
.venv\Scripts\python scripts/print_takeover_entrypoint.py --repo-root .
```

## Expected outcomes by step

- `startup_codex_helper.py` writes the startup intake, init execution card, and round-contract seed under `docs/context/`.
- `run_loop_cycle.py` refreshes the loop summary, exec-memory, and closure-support artifacts under `docs/context/`.
- `validate_loop_closure.py` writes the current closure verdict as `READY_TO_ESCALATE`, `NOT_READY`, or an infra/input error.
- `print_takeover_entrypoint.py` prints deterministic takeover guidance from the latest loop artifacts.

## Optional overlays

Generate workflow-status overlays only when they are needed for operator visibility:

```powershell
.venv\Scripts\python scripts/print_takeover_entrypoint.py --repo-root . --workflow-status-json-out docs/context/workflow_status_latest.json --workflow-status-md-out docs/context/workflow_status_latest.md
```

## Optional supervision

Use the supervisor only when you want a one-cycle health check or watch mode on top of the main operator flow:

```powershell
.venv\Scripts\python scripts/supervise_loop.py --repo-root . --max-cycles 1 --check-interval-seconds 0
```

## Minimal operator checks

- Run `python scripts/startup_codex_helper.py --help` if startup arguments are unclear.
- Run `python scripts/run_loop_cycle.py --help` to review `--skip-phase-end` and `--allow-hold`.
- Run `python scripts/validate_loop_closure.py --help` to confirm closure exit-code semantics.
- Run `python scripts/print_takeover_entrypoint.py --help` to confirm overlay output flags.
