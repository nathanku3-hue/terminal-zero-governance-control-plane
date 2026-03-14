# Terminal Zero Governance Control Plane

`quant_current_scope` is a script-driven AI engineering governance control plane. It runs a bounded startup -> loop -> closure -> takeover sequence, writes auditable artifacts, and keeps escalation decisions grounded in explicit evidence instead of informal prompt state.

## Start Here

- External/public orientation: start with this README, then `CONTRIBUTING.md`, `SUPPORT.md`, and `SECURITY.md`.
- Local operator flow: use `OPERATOR_LOOP_GUIDE.md`.
- Internal governance and operator procedures: use `docs/loop_operating_contract.md`, `docs/runbook_ops.md`, and `docs/operator_reference.md`.

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
- `scripts/run_loop_cycle.py` — execute one loop pass and refresh loop artifacts.
- `scripts/validate_loop_closure.py` — evaluate round readiness / closure state.
- `scripts/print_takeover_entrypoint.py` — print deterministic takeover guidance from current artifacts.
- `scripts/supervise_loop.py` — optional loop-health monitoring across one or more cycles.

## Shipped v1 Boundary

The shipped `v1` product in this repository is the local, script-driven governance control plane. That boundary includes:

- the bounded `startup -> loop -> closure -> takeover` operator flow driven by the canonical entrypoints above,
- auditable runtime artifacts under `docs/context/`,
- current operator docs, release docs, and validation/tests for that flow,
- optional supervision and workflow overlays as operator aids, not as alternative authority surfaces.

The following surfaces are not part of shipped `v1` and should be treated as future-state only until separately approved, implemented, and added to the release contract:

- plugin architecture,
- benchmark harness as a product boundary,
- skills registry as a shipped extension system,
- subagent routing matrix and worker inner loop,
- rollout automation,
- adaptive guardrails and broader memory optimization.

## Quickstart

This README stays intentionally short. Use `OPERATOR_LOOP_GUIDE.md` for the full local operator sequence and expected outputs.

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

### 2) Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -c constraints.txt .
python -m pip install -c constraints-dev.txt ".[dev]"
```

### 3) Verify the operator entrypoints

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/validate_loop_closure.py --help
python scripts/print_takeover_entrypoint.py --help
```

### 4) Run the control-plane operator flow

```powershell
python scripts/startup_codex_helper.py --repo-root .
python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
python scripts/validate_loop_closure.py --repo-root .
python scripts/print_takeover_entrypoint.py --repo-root .
```

### 5) Optional supervision

```powershell
python scripts/supervise_loop.py --repo-root . --max-cycles 1 --check-interval-seconds 0
```

### 6) Run tests

```powershell
python -m pytest -q
```

## Repository Layout

- `scripts/` — orchestration, validation, reporting, and takeover entrypoints.
- `docs/` — operating contracts, runbooks, policy docs, and phase briefs.
- `docs/context/` — generated machine/human artifacts exchanged between loop stages.
- `tests/` — script and control-plane contract coverage.
- `.github/workflows/` — CI workflows, including fast checks.

## Runtime Artifacts and Root Mirrors

Some root-level `*_LATEST.md` files are runtime convenience mirrors for operators. They are not the public API surface of the repository and should not be treated as canonical documentation for external readers.

For authoritative internal operator procedures, start with:
- `OPERATOR_LOOP_GUIDE.md`
- `docs/runbook_ops.md`
- `docs/operator_reference.md`
- `docs/loop_operating_contract.md`

## Documentation Routing

### Public / External Docs

- `README.md` — minimal public quickstart and project framing.
- `CHANGELOG.md` — release-facing change history for public packaging waves.
- `RELEASING.md` — manual release process, cut criteria, and validation checklist.
- `CONTRIBUTING.md` — contribution workflow and validation expectations.
- `SUPPORT.md` — support scope and help channels.
- `CODE_OF_CONDUCT.md` — community participation standards.
- `GOVERNANCE.md` — maintainer decision model and repository governance.
- `SECURITY.md` — public vulnerability disclosure policy.

### Internal Operator Docs

- `OPERATOR_LOOP_GUIDE.md` — recommended local command sequence and expected outputs.
- `docs/runbook_ops.md` — slim in-loop execution runbook for the active `run_loop_cycle.py` path.
- `docs/operator_reference.md` — startup, closure, takeover, supervision, and troubleshooting reference for the current control-plane path.
- `docs/loop_operating_contract.md` — governance contract and authority model.
- `docs/decisions/phase5_architecture.md` — draft future-state architecture notes, not the shipped `v1` contract.
- `docs/archive/legacy_quant_runbook.md` — archived historical quant/data/benchmark commands that are no longer part of the active operator path.
- `docs/security.md` — internal security operations policy.
- `.github/pull_request_template.md` — PR evidence checklist used by maintainers/contributors.
- `docs/context/workflow_status_latest.{json,md}` — optional runtime workflow status overlays.

## CI Surface

- `.github/workflows/fast-checks.yml` runs the fast operator gate.
- `.github/workflows/full-test.yml` runs the full `pytest` suite.

## License

This repository is licensed under the MIT License. See `LICENSE`.
