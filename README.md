# Terminal Zero Governance Control Plane

`quant_current_scope` is a script-driven AI engineering governance control plane. It is built to run a bounded startup -> execution -> closure -> takeover loop, generate auditable artifacts, and keep escalation decisions tied to explicit evidence instead of informal prompt state.

## Who This Repository Is For

This repository is primarily for:
- operators running the governance loop locally,
- engineers maintaining the loop scripts and artifact contracts,
- reviewers who need auditable startup, closure, and handoff outputs.

It is not packaged as a consumer application or hosted service.

## Platform Assumptions

- Python `3.12+` is the intended runtime.
- Operator examples primarily assume Windows PowerShell and a repo-local `.venv`.
- A compatible system `python` is acceptable when `.venv` is unavailable.
- Canonical dependency metadata lives in `pyproject.toml`.
- Use `constraints.txt` and `constraints-dev.txt` for pinned, validated installs.
- `requirements.txt` and `requirements-dev.txt` are compatibility shims for tools that still expect requirements files.
- CI fast checks run on GitHub Actions with Ubuntu and Python `3.12`.

## Canonical Entrypoints

- `scripts/startup_codex_helper.py` — initialize a round and produce startup intake artifacts.
- `scripts/run_loop_cycle.py` — execute one loop pass and write cycle artifacts.
- `scripts/validate_loop_closure.py` — evaluate round readiness / closure state.
- `scripts/supervise_loop.py` — monitor loop health across one or more cycles.
- `scripts/print_takeover_entrypoint.py` — print takeover guidance from current artifacts.

## Quickstart

### 1) Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies (P2 canonical model)

```powershell
python -m pip install --upgrade pip
# Runtime install from canonical metadata + runtime constraints
python -m pip install -c constraints.txt .
# Contributor/test extras from canonical metadata + dev constraints
python -m pip install -c constraints-dev.txt ".[dev]"
```

### 3) Smoke-check the main entrypoints

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/supervise_loop.py --max-cycles 1
```

### 4) Run the core operator flow

```powershell
python scripts/startup_codex_helper.py --repo-root .
python scripts/run_loop_cycle.py --repo-root . --skip-phase-end
python scripts/validate_loop_closure.py --repo-root .
python scripts/print_takeover_entrypoint.py --repo-root .
```

### 5) Run tests

```powershell
python -m pytest tests -v --tb=short
```

## Repository Layout

- `scripts/` — orchestration, validation, reporting, and takeover entrypoints.
- `docs/` — operating contracts, runbooks, policy docs, and phase briefs.
- `docs/context/` — generated machine/human artifacts exchanged between loop stages.
- `tests/` — script and control-plane contract coverage.
- `.github/workflows/` — CI workflows, including fast checks.

## Runtime Artifacts and Root Mirrors

Some root-level `*_LATEST.md` files are runtime convenience mirrors for operators. They are not the public API surface of the repository and should not be treated as canonical documentation for external readers.

For authoritative source material, start with:
- `docs/runbook_ops.md`
- `docs/loop_operating_contract.md`
- `OPERATOR_LOOP_GUIDE.md`

## Additional Operator Docs

- `OPERATOR_LOOP_GUIDE.md` — concise operator command sequence and expected outputs.
- `docs/runbook_ops.md` — detailed operating runbook.
- `docs/loop_operating_contract.md` — current governance contract and authority model.
- `SECURITY.md` — public vulnerability disclosure policy for external reporters.
- `docs/security.md` — internal security operations policy.

## Contributing and Community

- `CONTRIBUTING.md` — development workflow, contribution expectations, and validation checklist.
- `GOVERNANCE.md` — project decision model and maintainer responsibilities.
- `CODE_OF_CONDUCT.md` — community standards for participation.
- `SUPPORT.md` — support scope and where to ask for help.
- `.github/pull_request_template.md` — pull request checklist for governance, tests, and docs.

## CI Surface

- `.github/workflows/fast-checks.yml` runs the fast operator gate.
- `.github/workflows/full-test.yml` runs the full `pytest` suite.

## License

This repository is licensed under the MIT License. See `LICENSE`.
