# Quickstart (Observability)

## Context
Bootstrap Phase C observability using the canonical CLI exporter and a Prometheus textfile collector bridge.

## Prerequisites
- Python environment with `terminal-zero-governance` available
- Repo with `docs/context/audit_log.ndjson`
- Prometheus Node Exporter textfile collector enabled

## Commands
```bash
python -m sop metrics --repo-root . --format prometheus > ./sop_observability.prom
cat ./sop_observability.prom
```

## Output
```text
# HELP policy_decisions_total Total policy decisions by decision/actor.
# TYPE policy_decisions_total counter
policy_decisions_total{decision="PASS",actor="gate_a"} 3

# HELP gate_evaluation_duration_seconds Aggregated gate evaluation duration in seconds.
# TYPE gate_evaluation_duration_seconds gauge
gate_evaluation_duration_seconds{gate="exec_memory->advisory"} 2.0

# HELP failure_count_total Total FAIL/ERROR decisions.
# TYPE failure_count_total counter
failure_count_total 1
```

## Expected Decision
Exporter output is valid Prometheus exposition and includes canonical metric families for policy decisions, gate duration, and failure count.
