# Phase 3 Observability Evidence

- Date: 2026-03-31
- Python: 3.14.0
- Interpreter: `C:\Python314\python.exe`

## Exact commands run

```bash
python -m pytest tests/test_observability.py -k "metrics_endpoint_produces_prometheus_format or structured_log_schema_version_present or failure_count_total_increments_on_failure or gate_duration_metric_emitted"
python -m pytest tests/test_sop_cli.py
python -m pytest tests/test_cli_script_parity.py::TestByteIdentityContract::test_dual_copy_byte_identity tests/test_hardening.py::TestManifestSymmetry::test_manifest_pairs_byte_identical
python -m pytest
```

## Pytest count

- Full suite collected: 1085 tests

## Locked observability tests summary

- `test_metrics_endpoint_produces_prometheus_format`: PASS
- `test_structured_log_schema_version_present`: PASS
- `test_failure_count_total_increments_on_failure`: PASS
- `test_gate_duration_metric_emitted`: PASS

Result: **4/4 PASS, 0 FAIL**

## Full suite summary

- PASS: 1080
- SKIPPED: 5
- FAIL: 0
