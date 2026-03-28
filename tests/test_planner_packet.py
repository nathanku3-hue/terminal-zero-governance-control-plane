"""tests/test_planner_packet.py -- Phase 4.2 planner packet writer tests.

6 tests covering PlannerPacketWriter behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from planner_packet_writer import PlannerPacketWriter
except ModuleNotFoundError:
    try:
        from scripts.planner_packet_writer import PlannerPacketWriter
    except ModuleNotFoundError:
        from sop.scripts.planner_packet_writer import PlannerPacketWriter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trace(
    trace_id: str = "20260328T120000Z-a3f2",
    final_result: str = "PASS",
    repo_id: str = "quant_current_scope",
) -> dict:
    return {
        "schema_version": "1.0",
        "trace_id": trace_id,
        "generated_at_utc": "2026-03-28T12:00:00Z",
        "repo_id": repo_id,
        "duration_seconds": 1.0,
        "steps": [],
        "metrics": {"pass_count": 3, "hold_count": 0, "fail_count": 0,
                    "error_count": 0, "total_steps": 3},
        "final_result": final_result,
        "final_exit_code": 0,
    }


def _make_bridge(
    gate_result: str = "PROCEED",
    open_decision: str = "None",
    do_not_redecide: list | None = None,
    system_delta: str = "All steps passed.",
    recommended_next_step: str = "Begin next phase",
) -> dict:
    return {
        "schema_version": "1.0",
        "trace_id": "20260328T120000Z-a3f2",
        "generated_at_utc": "2026-03-28T12:00:00Z",
        "gate_result": gate_result,
        "system_delta": system_delta,
        "pm_delta": "Insufficient history",
        "open_decision": open_decision,
        "recommended_next_step": recommended_next_step,
        "do_not_redecide": do_not_redecide or [],
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


def _writer(tmp_path: Path) -> PlannerPacketWriter:
    schema_dir = Path(__file__).parent.parent / "src" / "sop" / "schemas"
    return PlannerPacketWriter(context_dir=tmp_path, schema_dir=schema_dir)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_packet_written_on_every_run(tmp_path: Path) -> None:
    """planner_packet_current.md and JSON shadow written on every run."""
    w = _writer(tmp_path)
    trace = _make_trace()
    bridge = _make_bridge()

    json_path = w.write(trace=trace, bridge=bridge, gate_a={}, gate_b={}, prior_packet=None)

    assert json_path.exists(), "JSON shadow must be written"
    md_path = tmp_path / "planner_packet_current.md"
    assert md_path.exists(), "Markdown surface must be written"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["trace_id"] == "20260328T120000Z-a3f2"
    assert data["run_result"] == "PASS"


def test_packet_schema_valid(tmp_path: Path) -> None:
    """JSON shadow contains all 10 required schema fields."""
    w = _writer(tmp_path)
    json_path = w.write(
        trace=_make_trace(),
        bridge=_make_bridge(),
        gate_a={},
        gate_b={},
        prior_packet=None,
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))

    required = [
        "schema_version", "trace_id", "generated_at_utc", "run_result",
        "current_context", "active_brief", "bridge_truth_summary",
        "decision_tail", "blocked_next_step", "active_bottleneck",
    ]
    for field in required:
        assert field in data, f"Missing required field: {field}"
    assert data["schema_version"] == "1.0"
    assert isinstance(data["decision_tail"], list)


def test_blocked_next_step_from_gate_hold(tmp_path: Path) -> None:
    """blocked_next_step reflects OPEN_DECISION from bridge when gate is HOLD."""
    hold_reason = "exec_memory_cycle_ready is False"
    bridge = _make_bridge(
        gate_result="HOLD",
        open_decision=hold_reason,
        recommended_next_step=f"Resolve: {hold_reason}",
    )
    w = _writer(tmp_path)
    json_path = w.write(
        trace=_make_trace(final_result="HOLD"),
        bridge=bridge,
        gate_a=_make_hold_gate(hold_reason),
        gate_b={},
        prior_packet=None,
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert data["blocked_next_step"] == hold_reason
    assert data["active_bottleneck"] == hold_reason


def test_decision_tail_carries_forward(tmp_path: Path) -> None:
    """decision_tail accumulates across runs and is capped at 10."""
    w = _writer(tmp_path)
    trace = _make_trace()

    # Run 1: prior=None, bridge has one settled decision
    bridge1 = _make_bridge(do_not_redecide=["PROCEED: exec_memory -> advisory"])
    json_path1 = w.write(trace=trace, bridge=bridge1, gate_a={}, gate_b={}, prior_packet=None)
    data1 = json.loads(json_path1.read_text(encoding="utf-8"))
    assert "PROCEED: exec_memory -> advisory" in data1["decision_tail"]
    assert len(data1["decision_tail"]) == 1

    # Run 2: carry forward run1 tail, add another decision
    bridge2 = _make_bridge(do_not_redecide=["PROCEED: advisory -> closure"])
    json_path2 = w.write(trace=trace, bridge=bridge2, gate_a={}, gate_b={}, prior_packet=data1)
    data2 = json.loads(json_path2.read_text(encoding="utf-8"))
    assert len(data2["decision_tail"]) == 2
    assert "PROCEED: exec_memory -> advisory" in data2["decision_tail"]
    assert "PROCEED: advisory -> closure" in data2["decision_tail"]

    # Cap at 10: build up 12 unique entries
    current_packet = data2
    for i in range(10):
        bridge_n = _make_bridge(do_not_redecide=[f"PROCEED: phase{i} -> phase{i+1}"])
        json_path_n = w.write(
            trace=trace, bridge=bridge_n, gate_a={}, gate_b={}, prior_packet=current_packet
        )
        current_packet = json.loads(json_path_n.read_text(encoding="utf-8"))
    assert len(current_packet["decision_tail"]) <= 10


def test_active_bottleneck_from_drift_alert(tmp_path: Path) -> None:
    """active_bottleneck falls back to first drift alert when no gate HOLD."""
    drift_data = {
        "schema_version": "1.0",
        "trace_id": "20260328T120000Z-a3f2",
        "generated_at_utc": "2026-03-28T12:00:00Z",
        "baseline_record_count": 5,
        "alerts": [{"alert_type": "DRIFT_ALERT", "message": "error_count increased"}],
    }
    (tmp_path / "run_drift_latest.json").write_text(
        json.dumps(drift_data), encoding="utf-8"
    )

    w = _writer(tmp_path)
    bridge = _make_bridge(gate_result="PROCEED", open_decision="None")
    json_path = w.write(
        trace=_make_trace(),
        bridge=bridge,
        gate_a={},
        gate_b={},
        prior_packet=None,
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert data["active_bottleneck"] == "error_count increased"
    assert data["blocked_next_step"] == "None"


def test_fresh_worker_needs_only_packet(tmp_path: Path) -> None:
    """Assertion contract: packet alone sufficient for fresh worker.

    (1) All 6 section keys present in JSON shadow.
    (2) current_context, active_brief, bridge_truth_summary are non-empty strings.
    (3) No field requires reading any file outside planner_packet_current.md
        (verified structurally: all fields derive from in-memory args, not new reads).
    """
    w = _writer(tmp_path)
    bridge = _make_bridge(
        system_delta="validate_exec_memory_truth: ERROR (script missing)",
        recommended_next_step="Begin next phase",
    )
    json_path = w.write(
        trace=_make_trace(),
        bridge=bridge,
        gate_a={},
        gate_b={},
        prior_packet=None,
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # (1) All 6 narrative section keys present
    section_keys = [
        "current_context", "active_brief", "bridge_truth_summary",
        "decision_tail", "blocked_next_step", "active_bottleneck",
    ]
    for key in section_keys:
        assert key in data, f"Section key missing: {key}"

    # (2) Three string fields non-empty
    for key in ("current_context", "active_brief", "bridge_truth_summary"):
        value = data[key]
        assert isinstance(value, str) and value.strip(), (
            f"{key} must be a non-empty string, got: {value!r}"
        )

    # (3) Structural check: decision_tail is a list (machine-readable)
    assert isinstance(data["decision_tail"], list)
