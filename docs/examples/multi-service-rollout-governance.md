# Multi-Service Rollout Governance

## Context
A release manager coordinates a staged rollout across API, worker, and frontend services and needs a single governance loop to document go/no-go status per rollout window.

## Inputs
- Service list: `api`, `worker`, `frontend`.
- Deployment wave metadata (wave-1 canary, wave-2 regional).
- Governance workspace path: `rollout-governed-repo`.
- Artifact handoff requirement to release channel.

## Commands
```bash
pip install terminal-zero-governance
sop init rollout-governed-repo
sop run --repo-root rollout-governed-repo --skip-phase-end
sop status --repo-root rollout-governed-repo
sop audit --repo-root rollout-governed-repo --filter-outcome BLOCK
```

## Output
```text
$ sop status --repo-root rollout-governed-repo
final_result: PASS
ready_to_escalate: true
active_bottleneck: none

$ sop audit --repo-root rollout-governed-repo --filter-outcome BLOCK
(no BLOCK records)
artifacts: docs/context/audit_log.ndjson, docs/context/loop_cycle_summary_latest.json
```

## Expected Decision
If the governance result is `PASS` and no `BLOCK` records exist, continue to the next rollout wave. If any `BLOCK` appears, pause progression until mitigation evidence is logged.
