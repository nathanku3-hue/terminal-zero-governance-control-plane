# Terminal Zero Operator Reference

> Internal operator reference for the current governance control plane.
> This document keeps startup, closure, takeover, supervision, and troubleshooting detail out of the in-loop runbook.

## Scope

- `README.md` is the minimal public quickstart.
- `OPERATOR_LOOP_GUIDE.md` is the short recommended startup -> loop -> closure -> takeover sequence.
- `docs/runbook_ops.md` is the slim in-loop execution runbook for the active `run_loop_cycle.py` path.
- Archived historical quant/data/benchmark commands remain in `docs/archive/legacy_quant_runbook.md`.

## Environment

- Run commands from the repository root.
- PowerShell examples assume a repo-local `.venv`.
- If `.venv` is unavailable, use `python` from a compatible Python `3.12+` interpreter and record that interpreter in your run notes.
- Generated loop artifacts are written under `docs/context/`.

## Current Truth Surfaces

Before startup, loop, closure, or takeover work, resolve the entry model against the target working repo for this round. In `quant_current_scope`, do not assume these files exist locally under `docs/context/`; they are current truth surfaces only when `KERNEL_ACTIVATION_MATRIX.md` says the capability is active and the artifact exists in the repo you are operating.

- Check `../KERNEL_ACTIVATION_MATRIX.md`.
- Check `../SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`.
- Current truth surfaces, when active and instantiated in the target working repo: `planner_packet_current.md`, `impact_packet_current.md`, `bridge_contract_current.md`, `done_checklist_current.md`, `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and `observability_pack_current.md`.

## Entry Order

1. Read `planner_packet_current.md` if it is active and instantiated in the target working repo.
2. Read `impact_packet_current.md` if it is active and instantiated.
3. Read `bridge_contract_current.md` if it is active and instantiated.
4. Read `done_checklist_current.md` if it is active and instantiated.
5. Read `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and `observability_pack_current.md` only when they are active and instantiated.

## When to Escalate

- Widen reads to phase briefs, decision logs, or the full repo only if an active required surface is missing, impact is still unclear after planner + impact, interface ownership is unclear, bridge truth conflicts with the decision tail, or the active bottleneck still cannot be named.

## What Changes After Execution

- Refresh the active instantiated surfaces you consumed or changed in the target working repo: `planner_packet_current.md`, `impact_packet_current.md`, `bridge_contract_current.md`, `done_checklist_current.md`, `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and `observability_pack_current.md`.

## 1. Startup

### Required command

```powershell
.venv\Scripts\python scripts/startup_codex_helper.py --repo-root .
```

### What startup must produce

- `docs/context/startup_intake_latest.json`
- `docs/context/startup_intake_latest.md`
- `docs/context/init_execution_card_latest.md`
- `docs/context/round_contract_seed_latest.md`

### Optional non-interactive startup

Use the CLI flags exposed by `startup_codex_helper.py --help` when you need a fully non-interactive run. The helper supports explicit intent, deliverable, non-goals, done-when, governance-lane, intuition-gate, and handoff-target fields.

### Operator check

- Confirm the startup intake and init execution card were refreshed.
- If the startup card requires a human intuition gate, record the acknowledgment before moving into the loop.

## 2. Closure

### Required command

```powershell
.venv\Scripts\python scripts/validate_loop_closure.py --repo-root .
```

### Exit semantics

- Exit `0`: `READY_TO_ESCALATE`
- Exit `1`: `NOT_READY`
- Exit `2`: input or infrastructure error

### Expected outputs

- `docs/context/loop_closure_status_latest.json`
- `docs/context/loop_closure_status_latest.md`

### Operator check

- Use the closure status plus the latest loop summary as the authoritative readiness signal.
- Do not treat takeover guidance as an override for a `NOT_READY` closure result.

## 3. Takeover

### Required command

```powershell
.venv\Scripts\python scripts/print_takeover_entrypoint.py --repo-root .
```

### Optional overlays

Generate workflow-status overlays only when they are needed for operator visibility:

```powershell
.venv\Scripts\python scripts/print_takeover_entrypoint.py --repo-root . --workflow-status-json-out docs/context/workflow_status_latest.json --workflow-status-md-out docs/context/workflow_status_latest.md
```

### Operator check

- Confirm the printed takeover guidance reflects the latest closure state and loop artifacts.
- Treat `docs/context/workflow_status_latest.{json,md}` as optional visibility overlays, not as a separate authority path.

## 4. Optional Supervision

### One-cycle health check

```powershell
.venv\Scripts\python scripts/supervise_loop.py --repo-root . --max-cycles 1 --check-interval-seconds 0
```

### Watch mode

```powershell
.venv\Scripts\python scripts/supervise_loop.py --repo-root . --max-cycles 999999 --check-interval-seconds 60
```

### Supervisor outputs

- `docs/context/supervisor_status_latest.json`
- `docs/context/supervisor_alerts_latest.md`

## 5. Verification and Troubleshooting

Use these commands when validating the active operator surface or checking for drift between docs and CLI behavior:

```powershell
python scripts/startup_codex_helper.py --help
python scripts/run_loop_cycle.py --help
python scripts/validate_loop_closure.py --help
python scripts/print_takeover_entrypoint.py --help
python -m pytest -q
```

If you need historical quant/data/benchmark procedures, use `docs/archive/legacy_quant_runbook.md`. They are preserved for reference but are not part of the active governance control-plane operator path.
