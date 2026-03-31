# Phase 2 RBAC Evidence

## Date
- 2026-03-31

## Python / Interpreter
- Interpreter: `C:\Python314\python.exe`
- Version: `3.14.0`

## Commands Run
1. `python -m pytest -q -k "rbac or policy_rbac or policy_engine"`
2. `python -m pytest -q`
3. `python -m pytest -q tests/test_policy_engine.py`

## Total Pytest Result Count

### Targeted RBAC/Policy batch
- `10 passed, 3 skipped, 1057 deselected`

### Full suite snapshot
- `4 failed, 1061 passed, 5 skipped`
- Note: the 4 failures are pre-existing/unrelated to this RBAC change set:
  - `tests/test_observability.py::test_metrics_endpoint_produces_prometheus_format`
  - `tests/test_observability.py::test_failure_count_total_increments_on_failure`
  - `tests/test_observability.py::test_gate_duration_metric_emitted`
  - `tests/test_sop_cli.py::TestSopCLI::test_version`

### Focused policy test file
- `10 passed`

## Locked Acceptance Tests (Explicit)
- `test_rbac_role_scoped_block_matches_role` — PASS
- `test_rbac_role_scoped_block` — PASS
- `test_rbac_no_role_defaults_to_global` — PASS
- `test_rbac_missing_role_id_skips_role_scoped_rules` — PASS
- `test_policy_rbac_validate_cli` — PASS
- `test_rbac_validate_rejects_duplicate_role_id` — PASS

## Deferred Behavior (as required)
- `permissions` enforcement is deferred (schema-validated only in v1).
- `scope` enforcement is deferred (schema-validated only in v1).
- tenant scoping enforcement is deferred (multi-tenant groundwork only in v1).
