# Terminal Zero In-Loop Operations Runbook (Active)

> Active execution path only. Non-runtime operator reference lives in
> `docs/runbook_ops_reference.md`.
> Internal in-loop execution guidance for the current governance control plane.

## Scope

- Primary use: run the loop pass after startup artifacts and the latest handoff are already in place.
- `OPERATOR_LOOP_GUIDE.md` remains the short startup -> loop -> closure -> takeover sequence.
- `docs/loop_operating_contract.md` remains the authoritative governance contract and authority model.
- Non-loop operator reference (startup, closure, takeover, supervision, troubleshooting) lives in
  `docs/runbook_ops_reference.md`.

## Runtime Assumptions

- Run commands from the repository root.
- PowerShell examples assume a repo-local `.venv`.
- Generated loop artifacts are written under `docs/context/`.

## Current Truth Surfaces

Before running the in-loop command, resolve the entry model against the target working repo for this
round. Do not assume these files exist locally under `docs/context/`; they are current truth surfaces
only when `KERNEL_ACTIVATION_MATRIX.md` says the capability is active and the artifact exists in
the repo you are operating.

- Check `E:\code\SOP\KERNEL_ACTIVATION_MATRIX.md`.
- Check `E:\code\SOP\SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md`.
- Current truth surfaces, when active and instantiated:
  `planner_packet_current.md`, `impact_packet_current.md`, `bridge_contract_current.md`,
  `done_checklist_current.md`, `multi_stream_contract_current.md`,
  `post_phase_alignment_current.md`, and `observability_pack_current.md`.

## Entry Order

1. Read `planner_packet_current.md` if it is active and instantiated.
2. Read `impact_packet_current.md` if it is active and instantiated.
3. Read `bridge_contract_current.md` if it is active and instantiated.
4. Read `done_checklist_current.md` if it is active and instantiated.
5. Read `multi_stream_contract_current.md`, `post_phase_alignment_current.md`, and
   `observability_pack_current.md` only when they are active and instantiated.

## When to Escalate

- Widen reads to phase briefs, decision logs, or the full repo only if an active required surface
  is missing, impact is still unclear after planner + impact, interface ownership is unclear, bridge
  truth conflicts with the decision tail, or the active bottleneck still cannot be named.

## What Changes After Execution

- Refresh the active instantiated surfaces you consumed or changed:
  `planner_packet_current.md`, `impact_packet_current.md`, `bridge_contract_current.md`,
  `done_checklist_current.md`, `multi_stream_contract_current.md`,
  `post_phase_alignment_current.md`, and `observability_pack_current.md`.

## In-Loop Inputs

- `docs/context/next_round_handoff_latest.md` is the current execution handoff.
- `docs/loop_operating_contract.md` remains the authoritative source for authority boundaries and
  escalation rules.
- `docs/context/skill_activation_latest.json` is optional supporting context only. It does not
  change authority or override the round contract.

## Loop Command

### Recommended command

```powershell
.venv\Scripts\python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
```

### Why these flags are the default

- `--skip-phase-end` keeps the active local operator path scoped to startup -> loop -> closure ->
  takeover.
- `--allow-hold true` records expected criteria shortfalls as `HOLD` instead of `FAIL`.

### Expected outputs

- `docs/context/loop_cycle_summary_latest.json`
- `docs/context/loop_cycle_summary_latest.md`
- `docs/context/exec_memory_packet_latest.json`
- `docs/context/exec_memory_packet_latest.md`
- refreshed closure-support artifacts under `docs/context/`

## HOLD / FAIL Checks

- Review the latest loop cycle summary before running standalone closure validation.
- If the cycle reports `HOLD` or `FAIL`, inspect the failing step names before proceeding.
- Treat the loop summary and closure artifacts as authoritative.

## Short Links

- Full operator sequence: `OPERATOR_LOOP_GUIDE.md`
- Non-loop operator reference: `docs/runbook_ops_reference.md`
- Governance authority model: `docs/loop_operating_contract.md`
