# Operator Loop Guide

`README.md` is the minimal public quickstart; this guide is the fuller local operator sequence for the current control-plane path only.

Run these commands from the repository root. The examples below assume PowerShell and a repo-local `.venv`. If `.venv` is unavailable, use `python` from a compatible Python `3.12+` interpreter and record that interpreter in your run notes.

Historical quant/data/benchmark commands are intentionally out of this guide. They live in `docs/archive/legacy_quant_runbook.md`.

## Current Truth Surfaces (Read First)

Before running any loop commands, resolve the entry model against the target working repo for this round. In `quant_current_scope`, do not assume these files exist locally under `docs/context/`; they are current truth surfaces only when `KERNEL_ACTIVATION_MATRIX.md` says the capability is active and the artifact exists in the repo you are operating.

**Root SOP governance:**
- `../KERNEL_ACTIVATION_MATRIX.md` — when each kernel capability becomes mandatory
- `../SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md` — 11-section checklist for multi-stream execution readiness

**Current truth surfaces (target working repo, when active and instantiated):**
- `planner_packet_current.md` — compact entry point (current context, active brief, bridge truth, decision tail, blocked next step, active bottleneck)
- `impact_packet_current.md` — impact view (changed files, owned files, touched interfaces, failing checks)
- `bridge_contract_current.md` — PM/planner bridge (SYSTEM_DELTA, PM_DELTA, OPEN_DECISION, RECOMMENDED_NEXT_STEP)
- `done_checklist_current.md` — machine-checkable done criteria
- `multi_stream_contract_current.md` — cross-stream coordination map (Backend, Frontend/UI, Data, Docs/Ops)
- `post_phase_alignment_current.md` — post-phase stream status update
- `observability_pack_current.md` — drift detection markers

**Entry order:**
1. Check `../KERNEL_ACTIVATION_MATRIX.md`.
2. Check `../SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`.
3. Read `planner_packet_current.md` if it is active and instantiated in the target working repo.
4. Read `impact_packet_current.md` if it is active and instantiated.
5. Read `bridge_contract_current.md` if it is active and instantiated.
6. Read `done_checklist_current.md` if it is active and instantiated.
7. Read `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and `observability_pack_current.md` only when they are active and instantiated.

**When to escalate:**
- Widen reads to phase briefs, decision logs, or the full repo only if an active required surface is missing, impact is still unclear after planner + impact, interface ownership is unclear, bridge truth conflicts with the decision tail, or the active bottleneck still cannot be named.

**What changes after execution:**
- Refresh the active instantiated surfaces you consumed or changed in the target working repo: `planner_packet_current.md`, `impact_packet_current.md`, `bridge_contract_current.md`, `done_checklist_current.md`, `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and `observability_pack_current.md`.

## Entry Paths

Two entry paths exist. Use the PRIMARY path. The COMPAT path is a backward-compatibility shim
for environments where the `sop` CLI is not yet installed; it must not be used as the default
once `sop` is available.

| Label | Command prefix | When to use |
|---|---|---|
| **PRIMARY** | `sop run <subcommand> --repo-root .` | Default for all operators with `sop` installed |
| **COMPAT** | `python scripts/<script>.py --repo-root .` | Only when `sop` CLI is not yet available |

Install check: `sop run --help` — if this resolves without error, use PRIMARY.
Full entry path reference with first-run steps, failure routing, and compat path label:
→ [`docs/context/operator_navigation_map.md`](docs/context/operator_navigation_map.md)

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

## Skills Status

After each loop cycle, the run summary includes a `skills_status` field with one of three machine-readable values: `OK` (resolver healthy, skills active), `EMPTY_BY_DESIGN` (resolver healthy, no skills registered — proceed unless skills were expected), or `RESOLVER_UNAVAILABLE` (resolver missing or broken — block and reinstall before continuing). For the full proceed/block ruling, first diagnostic step, recovery steps, and artifact cross-references for each value, see [`docs/context/skill_readiness_matrix.md`](docs/context/skill_readiness_matrix.md).
