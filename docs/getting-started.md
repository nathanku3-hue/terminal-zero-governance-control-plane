# Getting Started with Terminal Zero Governance

Zero to a working governance loop in under 10 minutes.

## Prerequisites

- Python 3.12 or later
- `pip` available in your environment
- A terminal (PowerShell on Windows, bash/zsh on Linux/macOS)

---

## Step 1 — Install

```bash
pip install terminal-zero-governance
```

Verify the install:

```bash
sop --help
sop version
```

---

## Step 2 — Bootstrap a governed repository

```bash
sop init my-governed-repo
```

This creates the directory `my-governed-repo/` with:

- `docs/context/` — artifact exchange directory
- `docs/` — contracts, runbooks, and policy docs
- `.gitignore` pre-configured for generated artifacts
- Seed configuration and Markdown templates

---

## Step 3 — Run one governance cycle

```bash
sop run --repo-root my-governed-repo --skip-phase-end
```

`--skip-phase-end` bypasses the phase-end gate so the cycle completes against
the seed values created by `sop init`. You will see step-by-step output ending
with a `PASS`, `HOLD`, or `FAIL` result.

> **Want the full startup intake workflow?**
> `sop startup` requires a pre-populated `startup_intake_latest.json` round
> contract (original intent, risk tier, decision class). Run
> `sop startup --help` and see `docs/operator_reference.md` for the full
> intake flow. The getting-started path uses `--skip-phase-end` so you can
> verify the install without preparing an intake document first.

---

## Step 4 — Query the audit log

```bash
sop audit --repo-root my-governed-repo --tail 5
```

This reads `docs/context/audit_log.ndjson` and prints the last 5 structured
audit entries. Each entry includes timestamp, decision (ALLOW/BLOCK/HOLD/PASS/
FAIL), actor, gate, and trace ID.

---

## Step 5 — Validate closure

```bash
sop validate --repo-root my-governed-repo
```

Outputs `READY_TO_ESCALATE`, `NOT_READY`, or an infrastructure failure reason.
This is the main go/not-yet gate before handing off to the next operator or
agent.

---

## What you have after these 5 steps

| Artifact | Location | Purpose |
|---|---|---|
| Loop cycle summary | `docs/context/loop_cycle_summary_latest.json` | Machine-readable run result |
| Audit log | `docs/context/audit_log.ndjson` | Append-only decision trail |
| Closure status | `docs/context/loop_closure_status_latest.json` | Readiness verdict |
| Memory packet | `docs/context/exec_memory_packet_latest.json` | State for next round |

---

## Next steps

| Goal | Where to go |
|---|---|
| Understand the system design | [docs/architecture.md](architecture.md) |
| Full CLI and SDK reference | [docs/api-reference.md](api-reference.md) |
| Use in a CI/CD pipeline | [docs/examples/cicd-pipeline-governance.md](examples/cicd-pipeline-governance.md) |
| Operator runbook | `docs/operator_reference.md` |
| Complete walkthrough | `USER_GUIDE.md` |
| Artifact classification | `docs/context/README.md` |
