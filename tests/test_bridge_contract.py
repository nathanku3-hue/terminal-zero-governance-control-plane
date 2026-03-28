"""tests/test_bridge_contract.py -- Phase 4.1 bridge contract writer tests.

6 tests covering BridgeContractWriter behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from bridge_contract_writer import BridgeContractWriter
except ModuleNotFoundError:
    try:
        from scripts.bridge_contract_writer import BridgeContractWriter
    except ModuleNotFoundError:
        from sop.scripts.bridge_contract_writer import BridgeContractWriter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trace(
    trace_id: str = "20260328T120000Z-a3f2",
    final_result: str = "PASS",
    steps: list | None = None,
    repo_id: str = "quant_current_scope",
) -> dict:
    return {
        "schema_version": "1.0",
        "trace_id": trace_id,
        "generated_at_utc": "2026-03-28T12:00:00Z",
        "repo_id": repo_id,
        "duration_seconds": 1.0,
        "steps": steps or [],
        "metrics": {
            "pass_count": 0,
            "hold_count": 0,
            "fail_count": 0,
            "error_count": 0,
            "total_steps": 0,
        },
        "final_result": final_result,
        "final_exit_code": 0,
    }


def _make_gate(decision: str = "PROCEED", from_phase: str = "a", to_phase: str = "b") -> dict:
    return {
        "schema_version": "1.0",
        "evaluated_at_utc": "2026-03-28T12:00:00Z",
        "trace_id": "20260328T120000Z-a3f2",
        "from_phase": from_phase,
        "to_phase": to_phase,
        "gate_conditions": [
            {"name": "exec_memory_cycle_ready", "result": decision == "PROCEED", "detail": "ok"}
        ],
        "all_conditions_met": decision == "PROCEED",
        "decision": decision,
    }


def _make_hold_gate(hold_detail: str = "exec_memory_cycle_ready is False") -> dict:
    return {
        "schema_version": "1.0",
        "evaluated_at_utc": "2026-03-28T12:00:00Z",
        "trace_id": "20260328T120000Z-a3f2",
        "from_phase": "exec_memory",
        "to_phase": "advisory",
        "gate_conditions": [
            {"name": "exec_memory_cycle_ready", "result": False, "detail": hold_detail}
        ],
        "all_conditions_met": False,
        "decision": "HOLD",
    }


def _writer(tmp_path: Path) -> BridgeContractWriter:
    schema_dir = Path(__file__).parent.parent / "src" / "sop" / "schemas"
    return BridgeContractWriter(context_dir=tmp_path, schema_dir=schema_dir)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bridge_written_on_proceed(tmp_path: Path) -> None:
    """bridge_contract_current.md and JSON shadow written when gate PROCEED."""
    w = _writer(tmp_path)
    trace = _make_trace(final_result="PASS")
    json_path = w.write(trace=trace, gate_a={}, gate_b={}, drift={})

    assert json_path.exists(), "JSON shadow must be written"
    md_path = tmp_path / "bridge_contract_current.md"
    assert md_path.exists(), "Markdown surface must be written"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["gate_result"] == "PROCEED"
    assert data["trace_id"] == "20260328T120000Z-a3f2"


def test_bridge_written_on_hold(tmp_path: Path) -> None:
    """bridge_contract_current.md and JSON shadow written even when gate HOLD."""
    w = _writer(tmp_path)
    trace = _make_trace(final_result="HOLD")
    gate_a = _make_hold_gate("exec_memory_cycle_ready is False")
    json_path = w.write(trace=trace, gate_a=gate_a, gate_b={}, drift={})

    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["gate_result"] == "HOLD"
    md_path = tmp_path / "bridge_contract_current.md"
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")
    assert "GateResult: HOLD" in md_content


def test_bridge_schema_valid(tmp_path: Path) -> None:
    """JSON shadow contains all required schema fields."""
    w = _writer(tmp_path)
    trace = _make_trace()
    json_path = w.write(trace=trace, gate_a={}, gate_b={}, drift={})
    data = json.loads(json_path.read_text(encoding="utf-8"))

    required = [
        "schema_version", "trace_id", "generated_at_utc", "gate_result",
        "system_delta", "pm_delta", "open_decision",
        "recommended_next_step", "do_not_redecide",
    ]
    for field in required:
        assert field in data, f"Missing required field: {field}"
    assert data["schema_version"] == "1.0"


def test_system_delta_lists_error_steps(tmp_path: Path) -> None:
    """SYSTEM_DELTA includes names of non-PASS steps."""
    steps = [
        {"name": "step_ok", "status": "PASS", "exit_code": 0,
         "started_utc": "2026-03-28T12:00:00Z", "ended_utc": "2026-03-28T12:00:01Z",
         "duration_seconds": 1.0},
        {"name": "step_fail", "status": "ERROR", "exit_code": 1,
         "started_utc": "2026-03-28T12:00:01Z", "ended_utc": "2026-03-28T12:00:02Z",
         "duration_seconds": 1.0, "message": "script missing"},
    ]
    w = _writer(tmp_path)
    trace = _make_trace(steps=steps, final_result="ERROR")
    json_path = w.write(trace=trace, gate_a={}, gate_b={}, drift={})
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert "step_fail" in data["system_delta"]
    assert "step_ok" not in data["system_delta"]


def test_open_decision_from_gate_hold(tmp_path: Path) -> None:
    """OPEN_DECISION reflects the HOLD reason from gate_a."""
    hold_detail = "exec_memory_cycle_ready is False"
    gate_a = _make_hold_gate(hold_detail)
    w = _writer(tmp_path)
    trace = _make_trace(final_result="HOLD")
    json_path = w.write(trace=trace, gate_a=gate_a, gate_b={}, drift={})
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert data["open_decision"] == hold_detail
    assert data["recommended_next_step"].startswith("Resolve:")


def test_do_not_redecide_is_list(tmp_path: Path) -> None:
    """DO_NOT_REDECIDE is always a list; empty list valid on first run."""
    w = _writer(tmp_path)

    # First run: no gate files -- empty list valid
    trace = _make_trace()
    json_path = w.write(trace=trace, gate_a={}, gate_b={}, drift={})
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(data["do_not_redecide"], list)

    # With PROCEED gate: list contains settled decision
    gate_b = _make_gate(decision="PROCEED", from_phase="exec_memory", to_phase="advisory")
    json_path2 = w.write(trace=trace, gate_a={}, gate_b=gate_b, drift={})
    data2 = json.loads(json_path2.read_text(encoding="utf-8"))
    assert isinstance(data2["do_not_redecide"], list)
    assert len(data2["do_not_redecide"]) >= 1
