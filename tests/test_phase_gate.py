"""tests/test_phase_gate.py

Phase 2.2 done criteria -- 7 tests:
  test_gate_proceed_when_all_conditions_met
  test_gate_hold_when_exec_memory_not_ready
  test_gate_hold_when_error_step_present
  test_gate_artifact_written_on_proceed
  test_gate_artifact_written_on_hold
  test_gate_artifact_schema_valid
  test_handoff_artifact_written_on_gate_b_proceed
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from phase_gate import PhaseGate, PhaseGateResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runtime(
    exec_memory_cycle_ready: bool = True,
    steps: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        exec_memory_cycle_ready=exec_memory_cycle_ready,
        steps=steps if steps is not None else [],
        trace_id="20260328T120000Z-abcd",
    )


def _make_gate(tmp_path: Path, from_phase: str = "exec_memory", to_phase: str = "advisory") -> PhaseGate:
    return PhaseGate(from_phase=from_phase, to_phase=to_phase, repo_root=tmp_path)


# ---------------------------------------------------------------------------
# Test 1 -- PROCEED when all conditions met
# ---------------------------------------------------------------------------

class TestGateProceedAllConditionsMet:
    def test_gate_proceed_when_all_conditions_met(self, tmp_path: Path) -> None:
        gate = _make_gate(tmp_path)
        runtime = _make_runtime(exec_memory_cycle_ready=True, steps=[
            {"name": "step_a", "status": "PASS"},
            {"name": "step_b", "status": "SKIP"},
        ])
        result = gate.evaluate(runtime)
        assert result.decision == "PROCEED"
        assert result.all_conditions_met is True
        assert all(c["result"] for c in result.conditions)


# ---------------------------------------------------------------------------
# Test 2 -- HOLD when exec_memory_cycle_ready is False
# ---------------------------------------------------------------------------

class TestGateHoldExecMemoryNotReady:
    def test_gate_hold_when_exec_memory_not_ready(self, tmp_path: Path) -> None:
        gate = _make_gate(tmp_path)
        runtime = _make_runtime(exec_memory_cycle_ready=False)
        result = gate.evaluate(runtime)
        assert result.decision == "HOLD"
        assert result.all_conditions_met is False
        em_cond = next(c for c in result.conditions if c["name"] == "exec_memory_cycle_ready")
        assert em_cond["result"] is False


# ---------------------------------------------------------------------------
# Test 3 -- HOLD when an ERROR step is present
# ---------------------------------------------------------------------------

class TestGateHoldErrorStep:
    def test_gate_hold_when_error_step_present(self, tmp_path: Path) -> None:
        gate = _make_gate(tmp_path)
        runtime = _make_runtime(
            exec_memory_cycle_ready=True,
            steps=[
                {"name": "build_exec_memory_packet", "status": "ERROR"},
            ],
        )
        result = gate.evaluate(runtime)
        assert result.decision == "HOLD"
        err_cond = next(c for c in result.conditions if c["name"] == "no_error_steps")
        assert err_cond["result"] is False


# ---------------------------------------------------------------------------
# Test 4 -- Gate artifact written on PROCEED
# ---------------------------------------------------------------------------

class TestGateArtifactWrittenOnProceed:
    def test_gate_artifact_written_on_proceed(self, tmp_path: Path) -> None:
        gate = _make_gate(tmp_path)
        runtime = _make_runtime(exec_memory_cycle_ready=True)
        result = gate.evaluate(runtime)
        out = tmp_path / "phase_gate_a_latest.json"
        gate.emit(result, runtime.trace_id, output_path=out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["decision"] == "PROCEED"


# ---------------------------------------------------------------------------
# Test 5 -- Gate artifact written on HOLD
# ---------------------------------------------------------------------------

class TestGateArtifactWrittenOnHold:
    def test_gate_artifact_written_on_hold(self, tmp_path: Path) -> None:
        gate = _make_gate(tmp_path)
        runtime = _make_runtime(exec_memory_cycle_ready=False)
        result = gate.evaluate(runtime)
        out = tmp_path / "phase_gate_a_latest.json"
        gate.emit(result, runtime.trace_id, output_path=out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["decision"] == "HOLD"


# ---------------------------------------------------------------------------
# Test 6 -- Gate artifact schema valid
# ---------------------------------------------------------------------------

class TestGateArtifactSchemaValid:
    def test_gate_artifact_schema_valid(self, tmp_path: Path) -> None:
        gate = _make_gate(tmp_path, from_phase="exec_memory", to_phase="advisory")
        runtime = _make_runtime(exec_memory_cycle_ready=True)
        result = gate.evaluate(runtime)
        out = tmp_path / "phase_gate_schema_test.json"
        gate.emit(result, runtime.trace_id, output_path=out)
        data = json.loads(out.read_text(encoding="utf-8"))
        # Required fields
        assert "schema_version" in data
        assert data["schema_version"] == "1.0"
        assert "evaluated_at_utc" in data
        assert "trace_id" in data
        assert "from_phase" in data
        assert "to_phase" in data
        assert "gate_conditions" in data
        assert isinstance(data["gate_conditions"], list)
        assert "all_conditions_met" in data
        assert "decision" in data
        assert data["decision"] in ("PROCEED", "HOLD")
        # Each condition has name + result
        for cond in data["gate_conditions"]:
            assert "name" in cond
            assert "result" in cond
            assert isinstance(cond["result"], bool)


# ---------------------------------------------------------------------------
# Test 7 -- Handoff artifact written on Gate B PROCEED
# ---------------------------------------------------------------------------

class TestHandoffArtifactOnGateBProceed:
    def test_handoff_artifact_written_on_gate_b_proceed(self, tmp_path: Path) -> None:
        gate = PhaseGate(
            from_phase="advisory",
            to_phase="summary",
            repo_root=tmp_path,
        )
        runtime = _make_runtime(exec_memory_cycle_ready=True)
        result = gate.evaluate(runtime)
        assert result.decision == "PROCEED"
        handoff_out = tmp_path / "phase_handoff_latest.json"
        gate.emit_handoff(runtime.trace_id, output_path=handoff_out)
        assert handoff_out.exists()
        data = json.loads(handoff_out.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert data["from_phase"] == "advisory"
        assert data["to_phase"] == "summary"
        assert "trace_id" in data
        assert "triggered_at_utc" in data
