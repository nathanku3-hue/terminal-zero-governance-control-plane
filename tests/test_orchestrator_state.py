"""tests/test_orchestrator_state.py -- Phase 4.3 orchestrator state writer tests.

6 tests covering OrchestratorStateWriter behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from orchestrator_state_writer import OrchestratorStateWriter, _load_orchestrator_state
except ModuleNotFoundError:
    try:
        from scripts.orchestrator_state_writer import OrchestratorStateWriter, _load_orchestrator_state
    except ModuleNotFoundError:
        from sop.scripts.orchestrator_state_writer import OrchestratorStateWriter, _load_orchestrator_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trace(trace_id="20260328T120000Z-a3f2", final_result="PASS", repo_id="quant_current_scope"):
    return {
        "schema_version": "1.0",
        "trace_id": trace_id,
        "generated_at_utc": "2026-03-28T12:00:00Z",
        "repo_id": repo_id,
        "duration_seconds": 1.0,
        "steps": [],
        "metrics": {"pass_count": 0, "hold_count": 0, "fail_count": 0, "error_count": 0, "total_steps": 0},
        "final_result": final_result,
        "final_exit_code": 0,
    }


def _make_bridge(open_decision="None"):
    return {
        "schema_version": "1.0",
        "trace_id": "20260328T120000Z-a3f2",
        "generated_at_utc": "2026-03-28T12:00:00Z",
        "gate_result": "PROCEED" if open_decision == "None" else "HOLD",
        "system_delta": "All steps passed.",
        "pm_delta": "Insufficient history",
        "open_decision": open_decision,
        "recommended_next_step": "Begin next phase",
        "do_not_redecide": [],
    }


def _make_planner(active_bottleneck="None"):
    return {
        "schema_version": "1.0",
        "trace_id": "20260328T120000Z-a3f2",
        "generated_at_utc": "2026-03-28T12:00:00Z",
        "run_result": "PASS",
        "current_context": "System is running.",
        "active_brief": "Advance to next phase",
        "bridge_truth_summary": "SYSTEM_DELTA: All steps passed. | RECOMMENDED_NEXT_STEP: Begin next phase",
        "decision_tail": [],
        "blocked_next_step": "None",
        "active_bottleneck": active_bottleneck,
    }


def _writer(tmp_path):
    schema_dir = Path(__file__).parent.parent / "src" / "sop" / "schemas"
    return OrchestratorStateWriter(context_dir=tmp_path, schema_dir=schema_dir)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_state_written_after_every_run(tmp_path):
    """orchestrator_state_latest.json written after every run."""
    w = _writer(tmp_path)
    out = w.write(trace=_make_trace(), bridge=_make_bridge(), planner_packet=_make_planner(), prior_state=None)
    assert out.exists(), "orchestrator_state_latest.json must be written"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["trace_id"] == "20260328T120000Z-a3f2"
    assert data["active_system"] == "quant_current_scope"


def test_state_schema_valid(tmp_path):
    """JSON contains all required orchestrator_state schema fields."""
    w = _writer(tmp_path)
    out = w.write(trace=_make_trace(), bridge=_make_bridge(), planner_packet=_make_planner(), prior_state=None)
    data = json.loads(out.read_text(encoding="utf-8"))
    required = [
        "schema_version", "trace_id", "generated_at_utc", "active_system",
        "active_stream", "blocked", "last_changed", "bottleneck",
        "open_pm_decision", "evidence_freshness",
    ]
    for field in required:
        assert field in data, f"Missing required field: {field}"
    assert data["schema_version"] == "1.0"
    assert isinstance(data["blocked"], bool)
    assert isinstance(data["evidence_freshness"], dict)


def test_blocked_true_when_open_decision(tmp_path):
    """blocked=True when open_decision != 'None'."""
    w = _writer(tmp_path)
    bridge = _make_bridge(open_decision="exec_memory_cycle_ready is False")
    out = w.write(trace=_make_trace(final_result="HOLD"), bridge=bridge, planner_packet=_make_planner(), prior_state=None)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["blocked"] is True
    assert data["open_pm_decision"] == "exec_memory_cycle_ready is False"


def test_evidence_freshness_null_for_missing_artifacts(tmp_path):
    """evidence_freshness emits null for artifacts not yet written."""
    w = _writer(tmp_path)
    out = w.write(trace=_make_trace(), bridge=_make_bridge(), planner_packet=_make_planner(), prior_state=None)
    data = json.loads(out.read_text(encoding="utf-8"))
    freshness = data["evidence_freshness"]
    # tmp_path is empty -- no key artifacts exist
    assert freshness["loop_run_trace_latest.json"] is None
    assert freshness["bridge_contract_current.md"] is None
    assert freshness["planner_packet_current.md"] is None


def test_orchestrator_loads_prior_state_on_init(tmp_path):
    """_load_orchestrator_state() returns state dict when file exists and is valid."""
    state = {
        "schema_version": "1.0",
        "trace_id": "20260328T110000Z-beef",
        "generated_at_utc": "2026-03-28T11:00:00Z",
        "active_system": "quant_current_scope",
        "active_stream": "main",
        "blocked": False,
        "last_changed": "PASS 2026-03-28T11:00:00Z",
        "bottleneck": "None",
        "open_pm_decision": "None",
        "evidence_freshness": {},
    }
    (tmp_path / "orchestrator_state_latest.json").write_text(json.dumps(state), encoding="utf-8")
    loaded = _load_orchestrator_state(tmp_path)
    assert loaded is not None
    assert loaded["trace_id"] == "20260328T110000Z-beef"
    assert loaded["blocked"] is False


def test_prior_state_load_failure_returns_none(tmp_path):
    """_load_orchestrator_state() returns None for all 4 failure conditions."""
    state_path = tmp_path / "orchestrator_state_latest.json"

    # Condition 1: file missing
    assert _load_orchestrator_state(tmp_path) is None

    # Condition 2: invalid JSON
    state_path.write_text("not valid json{{{", encoding="utf-8")
    assert _load_orchestrator_state(tmp_path) is None

    # Condition 3: missing schema_version
    state_path.write_text(json.dumps({"trace_id": "x"}), encoding="utf-8")
    assert _load_orchestrator_state(tmp_path) is None

    # Condition 4: schema_version mismatch
    state_path.write_text(json.dumps({"schema_version": "9.9"}), encoding="utf-8")
    assert _load_orchestrator_state(tmp_path) is None
