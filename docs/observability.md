# Observability v1 (CLI Exporter)

## Metrics export CLI

Use the following command to export metrics in Prometheus exposition format to stdout:

```bash
sop metrics --repo-root <path> --format prometheus
```

CLI contract in v1:
- `--repo-root` is required.
- `--format` is required.
- Allowed `--format` value is only `prometheus`.
- Output is written to stdout.
- Successful execution exits with code `0`.
- No HTTP `/metrics` endpoint exists in v1.
- No daemon/background service exists in v1.

## Source of truth

Prometheus output in v1 is derived from exactly one source:
- `docs/context/audit_log.ndjson`

`docs/context/audit_metrics_latest.json` may still be produced by other flows, but it is not used by the `sop metrics` exporter in v1.

## Missing/empty/malformed handling

For `sop metrics --repo-root ... --format prometheus`:
- Missing `docs/context/audit_log.ndjson` -> emit zero-value metrics and exit `0`.
- Empty `docs/context/audit_log.ndjson` -> emit zero-value metrics and exit `0`.
- Malformed NDJSON line -> ignore that line and continue processing valid lines; exit `0` unless a fatal non-recoverable read error occurs (for example permissions/readability failure).

## Exported metrics and labels

The v1 exporter emits exactly these canonical metric families:

- `policy_decisions_total{decision,actor}`
- `gate_evaluation_duration_seconds{gate}`
- `failure_count_total`

Compatibility alias window (deprecated, still emitted in Phase C):

- `policy_decision_total{decision,actor}` -> alias of `policy_decisions_total`
- `gate_duration_seconds_total{gate}` -> alias of `gate_evaluation_duration_seconds`
- `failures_total` -> alias of `failure_count_total`

Alias families are temporary and must be treated as deprecated output for consumer migration.

Label schema:
- `policy_decisions_total`
  - `decision`: audit decision
  - `actor`: audit actor
- `gate_evaluation_duration_seconds`
  - `gate`: gate identifier
- `failure_count_total`
  - no labels in v1

## Metric semantics

### `failure_count_total`
Count of audit entries where `decision` is in `{"FAIL", "ERROR"}`.

### `gate_evaluation_duration_seconds{gate}`
Aggregate per gate using numeric `duration_seconds` values from audit entries.
- Non-numeric or missing durations are ignored.
- Gates with no numeric durations may be omitted.
- Exposition uses aggregate gauge-like values in v1 (no histogram buckets in v1).

## Structured log scope

Phase 3 structured log scope in v1 applies only to:
- `docs/context/audit_log.ndjson`

Guarantees:
- Every emitted audit log object includes `schema_version`.
- Every emitted audit log object includes `event_tag` in `{"STEP_EXECUTION", "GATE_DECISION", "POLICY_DECISION"}`.

No additional structured log stream is required in v1.

## CLI -> Prometheus bridge example (textfile collector)

Use a periodic command to write a `.prom` file for Node Exporter textfile collector.

Example (Linux cron style):

```bash
*/1 * * * * cd /opt/your-repo && /usr/bin/env python -m sop metrics --repo-root /opt/your-repo --format prometheus > /var/lib/node_exporter/textfile_collector/sop_observability.prom
```

This workflow explicitly bridges the CLI exporter to Prometheus scraping without any HTTP endpoint in the `sop` process.
