# Terminal Zero In-Loop Operations Runbook

> **Phase 6 split**: This file has been split into two files.
> - **Active (in-loop)**: `docs/runbook_ops_active.md` — loaded by `execution_deputy`
> - **Reference (non-runtime)**: `docs/runbook_ops_reference.md` — operator reference only
>
> This file is retained as a redirect stub. Prefer the split files above.


> Internal in-loop execution guidance for the current governance control plane.
> This runbook intentionally stays narrow: it covers the active `run_loop_cycle.py` path only.

## Scope

- Primary use: run the loop pass after startup artifacts and the latest handoff are already in place.
- `OPERATOR_LOOP_GUIDE.md` remains the short startup -> loop -> closure -> takeover sequence.
- `docs/operator_reference.md` contains startup, closure, takeover, supervision, and troubleshooting reference material that is not needed inside the loop.
- `docs/loop_operating_contract.md` remains the authoritative governance contract and authority model.

## Runtime Assumptions

- Run commands from the repository root.
- PowerShell examples assume a repo-local `.venv`.
- Generated loop artifacts are written under `docs/context/`.

## Current Truth Surfaces

Before running the in-loop command, resolve the entry model against the target working repo for this round. In `quant_current_scope`, do not assume these files exist locally under `docs/context/`; they are current truth surfaces only when `KERNEL_ACTIVATION_MATRIX.md` says the capability is active and the artifact exists in the repo you are operating.

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

## In-Loop Inputs

- `docs/context/next_round_handoff_latest.md` is the current execution handoff.
- `docs/loop_operating_contract.md` remains the authoritative source for authority boundaries and escalation rules.
- `docs/context/skill_activation_latest.json` is optional supporting context only. It does not change authority or override the round contract.

## Loop Command

### Recommended command

```powershell
.venv\Scripts\python scripts/run_loop_cycle.py --repo-root . --skip-phase-end --allow-hold true
```

### Why these flags are the default

- `--skip-phase-end` keeps the active local operator path scoped to the current startup -> loop -> closure -> takeover surface.
- `--allow-hold true` records expected criteria shortfalls as `HOLD` instead of `FAIL` in the cycle summary when that is the intended operator posture.

### Expected outputs

- `docs/context/loop_cycle_summary_latest.json`
- `docs/context/loop_cycle_summary_latest.md`
- `docs/context/exec_memory_packet_latest.json`
- `docs/context/exec_memory_packet_latest.md`
- refreshed closure-support artifacts under `docs/context/`

## Subagent Review Choreography

When executing bounded work with subagent delegation, follow this review sequence:

```
Implementer → Spec Compliance Review → Code Quality Review → Continue/Close
```

### Sequence Steps

1. **Implementer**: Executes the bounded scope against the round contract.
2. **Spec Compliance Review**: Verifies the implementation matches the agreed specification in `planner_packet_current.md` and `bridge_contract_current.md`.
3. **Code Quality Review**: Checks code quality, test coverage, and lint/typecheck status.
4. **Continue/Close**: If both reviews pass, continue to next bounded piece or close the round. If either review fails, return to Implementer with explicit remediation notes.

### Invariants

| Invariant | Meaning |
|-----------|---------|
| No new authority | Review sequence does not override PM/CEO approval gates |
| No runtime hooks | This is a choreography pattern, not automated enforcement |
| No Phase 5C execution semantics | Execution semantics remain blocked until Phase 5C |
| Re-review required | If spec or quality review fails, the work must return to Implementer |

### Failure Handling

- **Spec compliance fails**: Return to Implementer with specific spec drift notes. Do not proceed to code quality review until spec compliance passes.
- **Code quality fails**: Return to Implementer with specific quality issues. Spec compliance remains valid; only fix quality issues.

This choreography is advisory-only. It does not create a new gate or authority path.

## HOLD / FAIL Checks

- Review the latest loop cycle summary before running standalone closure validation.
- If the cycle reports `HOLD` or `FAIL`, inspect the failing step names before proceeding.
- Treat the loop summary and closure artifacts as authoritative. Do not treat optional overlays or advisory mirrors as overrides.

## Short Links

- Full operator sequence: `OPERATOR_LOOP_GUIDE.md`
- Non-loop operator reference: `docs/operator_reference.md`
- Governance authority model: `docs/loop_operating_contract.md`
