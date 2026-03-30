# Terminal Zero Governance — API Reference

Human-readable reference for the `sop` CLI and the GovernanceClient Python SDK.
The formal machine-readable spec lives at `docs/api/openapi.yaml`.

---

## CLI Reference

### `sop run` — Execute one governance loop cycle

**Synopsis**
```bash
sop run --repo-root <path> [--skip-phase-end] [--allow-hold]
```

**Parameters**

| Flag | Type | Default | Description |
|---|---|---|---|
| `--repo-root` | path | `.` | Root of the governed repository. All artifact paths are resolved relative to this directory. |
| `--skip-phase-end` | flag | off | Skip phase-end gate processing. Use for smoke tests and first-run scenarios where no round contract exists yet. |
| `--allow-hold` | flag | on | Treat a HOLD gate decision as non-blocking (cycle completes with `HOLD` result rather than failing). |

**Output artifacts written**

| Artifact | Path | Description |
|---|---|---|
| Loop cycle summary | `docs/context/loop_cycle_summary_latest.json` | Machine-readable result of the cycle |
| Loop cycle summary (human) | `docs/context/loop_cycle_summary_latest.md` | Human-readable rendering |
| Memory packet | `docs/context/exec_memory_packet_latest.json` | Updated state for next round |
| Audit log (appended) | `docs/context/audit_log.ndjson` | One entry per gate decision |
| Audit metrics (appended) | `docs/context/audit_metrics_latest.json` | Aggregate decision counts |

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Cycle completed — result is PASS or HOLD |
| `1` | Cycle completed — result is FAIL or a gate blocked |
| `2` | Infrastructure error — unhandled exception during cycle |

**Loop cycle summary schema** (`LoopCycleSummary`)

```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "2026-03-30T12:00:00Z",
  "final_result": "PASS",
  "final_exit_code": 0,
  "step_summary": {
    "pass_count": 5,
    "hold_count": 0,
    "fail_count": 0,
    "error_count": 0,
    "skip_count": 1,
    "total_steps": 6
  },
  "gate_decisions": [],
  "skills_status": "OK"
}
```

`final_result` values: `PASS` | `HOLD` | `FAIL` | `ERROR`

---

### `sop audit` — Query the governance audit log

**Synopsis**
```bash
sop audit --repo-root <path> [--tail N] [--filter-outcome OUTCOME]
```

**Parameters**

| Flag | Type | Default | Description |
|---|---|---|---|
| `--repo-root` | path | `.` | Root of the governed repository. |
| `--tail` | integer | (all) | Return only the last N entries. |
| `--filter-outcome` | string | (all) | Filter by decision value. Case-insensitive. |

**Allowed `--filter-outcome` values:** `ALLOW` `BLOCK` `HOLD` `PASS` `FAIL` `ERROR` `WARN` `SKIP`

**Audit entry schema** (`AuditEntry`) — all 8 fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Schema version, e.g. `"1.0"` |
| `timestamp_utc` | ISO 8601 datetime | yes | When the decision was recorded |
| `decision` | enum | yes | One of the 8 allowed decision values |
| `actor` | string | yes | Component or role that made the decision |
| `gate` | string | yes | Gate identifier (e.g. `gate_a`, `gate_b`, `closure`) |
| `trace_id` | string | yes | Unique ID linking entries within one `sop run` invocation |
| `outcome` | string | no | Human-readable outcome description |
| `artifact_refs` | object | no | Map of named artifact paths referenced by this decision |

**Example entry**
```json
{
  "schema_version": "1.0",
  "timestamp_utc": "2026-03-30T12:01:45Z",
  "decision": "PASS",
  "actor": "run_loop_cycle",
  "gate": "gate_a",
  "trace_id": "a1b2c3d4",
  "outcome": "All pre-work checks passed",
  "artifact_refs": {
    "summary": "docs/context/loop_cycle_summary_latest.json"
  }
}
```

**Storage:** `docs/context/audit_log.ndjson` — append-only, one JSON object per line.

---

### `sop policy validate` — Validate a policy rule file

**Synopsis**
```bash
sop policy validate --rule-file <path>
```

**Parameters**

| Flag | Type | Required | Description |
|---|---|---|---|
| `--rule-file` | path | yes | Path to the JSON policy rule file to validate. |

**Policy rule file schema**

A policy rule file is a JSON array of rule objects:

```json
[
  {
    "id": "require-round-contract",
    "condition": "round_contract_latest.md exists",
    "decision": "ALLOW",
    "rationale": "Round contract must be present before execution proceeds."
  }
]
```

Required fields per rule: `id`, `condition`, `decision`, `rationale`.

**Output on success**
```json
{ "valid": true, "rule_count": 3 }
```

**Output on failure**
```json
{ "error": "Missing required field: rationale", "detail": "Rule at index 1" }
```

**Exit codes:** `0` valid, `1` invalid rule file, `2` policy engine unavailable.

> **Note:** The policy engine is introduced in v0.2.0. On v0.1.x, this command
> returns exit code `2` with a `503`-equivalent message.

---

### `sop status` — Return most recent loop cycle summary

**Synopsis**
```bash
sop status --repo-root <path>
```

Reads `docs/context/loop_cycle_summary_latest.json` and prints a structured
summary. Returns a non-zero exit code and a human-readable message if no prior
run exists.

**Output schema:** same as `LoopCycleSummary` above.

**Exit codes:** `0` summary found and printed, `1` no prior run found.

---

### Other CLI subcommands

| Command | Description |
|---|---|
| `sop init <dir>` | Bootstrap a new governed repository at `<dir>`. Creates directory structure, `.gitignore`, seed config, and Markdown templates. |
| `sop startup --repo-root <path>` | Full startup intake flow. Requires `startup_intake_latest.json` to be pre-populated. See `docs/operator_reference.md`. |
| `sop validate --repo-root <path>` | Check closure readiness. Emits `READY_TO_ESCALATE` or `NOT_READY`. |
| `sop takeover --repo-root <path>` | Print structured takeover guidance for the next operator or agent. |
| `sop supervise --max-cycles N` | Monitor loop health for up to N cycles. |
| `sop version` | Print installed version. |

---

## Python SDK (v0.2.0 — forthcoming)

> Available after `pip install terminal-zero-governance==0.2.0`.
> Source: `src/sop/_client.py`.
> The CLI surface above is fully available now (v0.1.x).

The `GovernanceClient` class provides a Python-native interface to the same
operations exposed by the CLI. All methods accept a `repo_root` parameter and
return typed result objects.

```python
from sop import GovernanceClient

client = GovernanceClient(repo_root="my-governed-repo")

# Run one loop cycle
result = client.run(skip_phase_end=True)
print(result.final_result)   # "PASS" | "HOLD" | "FAIL" | "ERROR"
print(result.final_exit_code)  # 0 | 1 | 2

# Query audit log
entries = client.audit(tail=5)
for entry in entries:
    print(entry.decision, entry.gate, entry.timestamp_utc)

# Validate a policy rule file
validation = client.policy_validate(rule_file="policy_rules.json")
print(validation.valid, validation.rule_count)

# Get most recent loop status
status = client.status()
print(status.final_result)
```

**Method summary**

| Method | Maps to CLI | Returns |
|---|---|---|
| `client.run(skip_phase_end, allow_hold)` | `sop run` | `LoopCycleSummary` |
| `client.audit(tail, filter_outcome)` | `sop audit` | `list[AuditEntry]` |
| `client.policy_validate(rule_file)` | `sop policy validate` | `PolicyValidationResult` |
| `client.status()` | `sop status` | `LoopCycleSummary` |

---

## Formal spec

The OpenAPI 3.1 spec at `docs/api/openapi.yaml` defines the canonical schema
for all request/response objects referenced in this document.
