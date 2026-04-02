# Phase 10 Continuous Compliance Evidence

## Date
2026-03-31

## Python / Interpreter
- `Python 3.14.0`
- Command: `python --version`

## Exact Commands Run
- `python -m pytest tests/test_phase10_nightly_audit_cli.py -q`
- `python -m pytest tests/test_phase10_nightly_audit_cli.py tests/test_sop_cli.py -q`
- `python -m pytest -q`

## Pytest Count
- Targeted: `4 passed`
- Focused CLI bundle: `17 passed`
- Full suite: `1104 passed, 5 skipped`

## Locked Contract Status
- stdout JSON == `docs/context/compliance_snapshot_latest.json`: **PASS**
- per-control PASS/FAIL logic: **PASS**
- escalation mapping lookup: **PASS**
- missing mapping row -> exit 3: **PASS**
- invalid JSON schema input -> exit 3: **PASS**

## Snapshot Excerpt

```json
{
  "overall_status": "FAIL",
  "controls": [
    {"control_id": "release", "status": "FAIL"},
    {"control_id": "evidence", "status": "FAIL"},
    {"control_id": "drift", "status": "FAIL"},
    {"control_id": "runbooks", "status": "PASS"}
  ],
  "failing_control_ids": ["release", "evidence", "drift"]
}
```

## Escalation Queue Excerpt

```json
{
  "queue_size": 3,
  "entries": [
    {"control_id": "release", "severity": "HIGH", "sla": "4h"},
    {"control_id": "evidence", "severity": "MEDIUM", "sla": "24h"},
    {"control_id": "drift", "severity": "HIGH", "sla": "8h"}
  ]
}
```
