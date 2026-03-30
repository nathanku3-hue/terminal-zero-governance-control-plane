# Terminal Zero Governance — Architecture

This document describes the system design of the Terminal Zero (T0) governance
control plane: what it is, how it is structured, what data flows through it,
and what it is explicitly not.

---

## Component Overview

```
+------------------+
|   sop CLI        |  <-- operator / CI invocation surface
+--------+---------+
         |
         v
+--------+---------+     +---------------------+
| run_loop_cycle   |---->| Gate A (pre-work)   |
|                  |     | policy_rules.json   |
|  Steps (ordered) |     +---------------------+
|  1. refresh      |              |
|  2. truth check  |              v
|  3. gate eval    |     +---------------------+
|  4. closure      |---->| Gate B (post-work)  |
+--------+---------+     | closure validator   |
         |               +---------------------+
         |                         |
         v                         v
+--------+---------+     +---------+-----------+
| Audit Log        |     | loop_cycle_summary  |
| audit_log.ndjson |     | _latest.json / .md  |
| (append-only)    |     +---------------------+
+--------+---------+
         |
         v
+--------+---------+
| Audit Metrics    |
| audit_metrics    |
| _latest.json     |
+------------------+
```

**Reading the diagram:**
- Each `sop run` call flows top-to-bottom through this graph.
- Gate A runs before execution steps; Gate B runs after.
- Every gate decision is written to the append-only audit log.
- The loop cycle summary is the authoritative machine-readable result.

---

## Three-Layer Model

```
+---------------------------------------------+
| Layer 0 — Governance Boundary               |
|  P0: What is allowed?                       |
|  Artifacts: startup_intake_latest.json,     |
|             round_contract_latest.md,       |
|             init_execution_card_latest.md   |
|  Gate: explicit risk lane + intent          |
+---------------------------------------------+
         |
         v
+---------------------------------------------+
| Layer 1 — Execution Loop  (P1 + P2 + P3)   |
|  P1: Planning Truth  — what are we doing?   |
|  P2: Execution Truth — what is happening?   |
|  P3: Readiness Truth — is it done?          |
|  Entrypoint: run_loop_cycle.py              |
|  Artifacts: exec_memory_packet_latest.json, |
|             loop_cycle_summary_latest.json, |
|             loop_closure_status_latest.json |
+---------------------------------------------+
         |
         v
+---------------------------------------------+
| Layer 2 — Evidence Trail  (P4 + P5)         |
|  P4: Handoff Truth  — what does next need?  |
|  P5: Evidence Truth — what happened?        |
|  Artifacts: audit_log.ndjson,               |
|             audit_metrics_latest.json,      |
|             next_round_handoff_latest.json, |
|             loop_run_trace_latest.json      |
+---------------------------------------------+
```

---

## Key Data Flows

### Startup → Run → Closure

```
sop init
  └─> creates docs/context/ structure
      creates seed config

sop startup  (optional — full intake flow)
  reads  startup_intake_latest.json  (operator-authored)
  writes round_contract_latest.md
  writes init_execution_card_latest.md

sop run
  reads  round_contract_latest.md
  reads  exec_memory_packet_latest.json  (prior run, if any)
  runs   Gate A  (policy rules)
  runs   Steps   (truth refresh, checks)
  runs   Gate B  (closure validation)
  writes loop_cycle_summary_latest.json
  writes exec_memory_packet_latest.json  (updated)
  appends audit_log.ndjson
  appends audit_metrics_latest.json

sop validate
  reads  loop_cycle_summary_latest.json
  reads  loop_closure_status_latest.json
  emits  READY_TO_ESCALATE | NOT_READY

sop takeover
  reads  next_round_handoff_latest.json
  prints structured handoff for next operator/agent
```

### Artifact Dependency Chain

```
startup_intake_latest.json
        |
        v
round_contract_latest.md
        |
        v
exec_memory_packet_latest.json  <---+  (updated each run)
        |                           |
sop run (one cycle)                 |
        |                           |
        +---> loop_cycle_summary_latest.json
        |                           |
        +---> audit_log.ndjson      |
        |                           |
        +---> audit_metrics_latest.json
        |
        v
loop_closure_status_latest.json
        |
        v
next_round_handoff_latest.json
```

---

## Extension Points

### Policy Rules

Gate A and Gate B evaluate `policy_rules_default.json` (or a custom file
passed via `--policy-rules`). Rules are JSON objects with `id`, `condition`,
`decision`, and `rationale` fields. Add custom rules to extend gate behavior
without modifying loop scripts.

See `docs/api/openapi.yaml` path `/policy/validate` for the rule schema.

### Custom Gate Steps

Loop steps are defined in the loop operating contract
(`docs/loop_operating_contract.md`). Steps can be extended by adding entries
to the step registry — each step is a callable with a standard
`(context, config) -> StepResult` signature.

### Audit Consumers

`audit_log.ndjson` is an append-only newline-delimited JSON file. Any tool
that can read NDJSON can consume it: `jq`, custom scripts, CI log parsers.
See `docs/api-reference.md` for the full `AuditEntry` schema (8 fields).

### Memory Packet

`exec_memory_packet_latest.json` is the state bridge between loop cycles.
Custom fields can be added to carry cross-cycle context; the schema is
versioned and backward-compatible within a major version.

---

## What This System Is NOT

| Not this | Why it matters |
|---|---|
| No HTTP server | All operations are local process calls. There is no daemon, no port, no REST service running. |
| No hosted service | Nothing is sent to a remote server. All artifacts remain on the local filesystem. |
| No autopilot | Every phase gate requires a human or explicit operator decision to proceed. |
| No agent platform | This is a governance wrapper, not a model-hosting or agent-orchestration platform. |
| No consumer UI | The interface is the CLI 