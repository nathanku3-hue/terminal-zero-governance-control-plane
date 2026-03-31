# Phase 5 Plugin API v1 Evidence

Date: 2026-03-31
Interpreter: Python 3.14.0 (`C:\Python314\python.exe`)

## Scope Delivered

- Plugin interface + deterministic loader implementation
- `sop run` integration with `--plugin-dir` and default `.sop/plugins`
- Gate-level plugin chain execution with sorted order + BLOCK short-circuit
- Plugin BLOCK enforcement in gate outcome
- Plugin audit logging (`plugin:<name>`, status, version, decision)
- Example plugin
- Documentation: `docs/plugin-api.md`
- Acceptance tests: `tests/test_plugin_api_v1.py`

## Commands Executed

### Targeted acceptance tests

```bash
python -m pytest "e:\Code\SOP\quant_current_scope\tests\test_plugin_api_v1.py" -q
```

Result: **10 passed**

```bash
python -m pytest "e:\Code\SOP\quant_current_scope\tests\test_plugin_api_v1.py" "e:\Code\SOP\quant_current_scope\tests\test_script_surface_sync.py" -q
```

Result: **45 passed**

### Full suite

```bash
python -m pytest -q
```

Result: **1090 passed, 5 skipped, 1 failed**

Failure:
- `tests/test_endgame.py::test_context_count_within_max_artifacts_limit`
- Reason: `docs/context/` has **103** artifacts, exceeding the test threshold (**100**).
- This is a workspace state/hygiene failure (artifact count), not a plugin API runtime contract failure.

Verification command:

```bash
(Get-ChildItem "e:\Code\SOP\quant_current_scope\docs\context" -File | Measure-Object).Count
```

Output: `103`

## Acceptance Test Coverage (Locked Set)

Implemented in `tests/test_plugin_api_v1.py`:

1. `test_plugin_loader_discovers_example_plugin`
2. `test_plugin_discovery_non_recursive_and_underscore_ignored`
3. `test_plugin_export_contract_requires_plugin_symbol`
4. `test_plugin_version_incompatible_is_skipped`
5. `test_plugin_evaluate_called_in_policy_chain`
6. `test_plugin_execution_order_sorted_by_filename`
7. `test_plugin_block_short_circuits_remaining_plugins`
8. `test_plugin_block_is_enforced_in_gate_outcome`
9. `test_plugin_exception_is_captured_not_crashing_run`
10. `test_plugin_result_written_to_audit_log`

## Artifacts

- `src/sop/_plugins.py`
- `src/sop/scripts/run_loop_cycle.py`
- `src/sop/__main__.py`
- `scripts/run_loop_cycle.py` (synced parity)
- `.sop/plugins/example_warn.py`
- `docs/plugin-api.md`
- `tests/test_plugin_api_v1.py`
