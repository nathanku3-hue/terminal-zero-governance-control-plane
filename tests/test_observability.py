"""tests/test_observability.py

Phase 2.1 done criteria — 6 tests:
  test_trace_artifact_written
  test_trace_schema_valid
  test_trace_id_format
  test_trace_id_on_runtime
  test_steps_ndjson_written
  test_metrics_match_steps
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Make scripts importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "utils"))

from loop_cycle_context import build_loop_cycle_context
from loop_cycle_runtime import build_loop_cycle_runtime, LoopCycleRuntime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TRACE_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{4}$")


def _minimal_args(tmp_path: Path) -> argparse.Namespace:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    context_dir = repo_root / "docs" / "context"
    context_dir.mkdir(parents=True)
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()

    for name in [
        "auditor_calibration_report.py",
        "generate_ceo_go_signal.py",
        "generate_ceo_weekly_summary.py",
        "evaluate_context_compaction_trigger.py",
        "build_exec_memory_packet.py",
        "validate_ceo_go_signal_truth.py",
        "validate_exec_memory_truth.py",
        "validate_ceo_weekly_summary_truth.py",
        "validate_round_contract_checks.py",
        "validate_counterexample_gate.py",
        "validate_dual_judge_gate.py",
        "validate_refactor_mock_policy.py",
        "validate_review_checklist.py",
        "validate_interface_contracts.py",
        "validate_parallel_fanin.py",
        "validate_loop_closure.py",
        "phase_end_handover.ps1",
    ]:
        (script_dir / name).write_text("", encoding="utf-8")

    return argparse.Namespace(
        repo_root=repo_root,
        context_dir=Path("docs/context"),
        scripts_dir=script_dir,
        logs_dir=None,
        repo_id="test-repo",
        python_exe=sys.executable,
        freshness_hours=24.0,
        pm_budget_tokens=100_000,
        ceo_budget_tokens=100_000,
        compaction_pm_warn=0.7,
        compaction_ceo_warn=0.7,
        compaction_force=0.9,
        compaction_max_age_hours=168.0,
        skip_phase_end=True,
        phase_end_audit_mode="shadow",
        allow_hold=True,
        weekly_report_json=None,
        weekly_report_md=None,
        dossier_json=None,
        dossier_md=None,
        fp_ledger_json=None,
        disagreement_ledger_jsonl=None,
        output_json=None,
        output_md=None,
        go_signal_md=None,
        weekly_summary_md=None,
        weekly_summary_gen_script=None,
        go_truth_script=None,
        weekly_truth_script=None,
        memory_packet_script=None,
        compaction_trigger_script=None,
        memory_truth_script=None,
        exec_memory_json=None,
        exec_memory_md=None,
        exec_memory_build_status_json=None,
        compaction_state_json=None,
        compaction_status_json=None,
        closure_script=None,
        closure_output_json=None,
        closure_output_md=None,
        phase_end_script=None,
    )


def _context_dir(args: argparse.Namespace) -> Path:
    """Return the resolved context_dir for test assertions."""
    return args.repo_root.resolve() / "docs" / "context"


def _context_dir(args: argparse.Namespace) -> Path:
    """Resolve the actual context_dir used by run_cycle."""
    return args.repo_root.resolve() / "docs" / "context"


def _run_cycle_for_test(args: argparse.Namespace):
    """Import and run run_cycle, returning (exit_code, payload, md)."""
    try:
        from sop.scripts.run_loop_cycle import run_cycle
    except ImportError:
        from scripts.run_loop_cycle import run_cycle
    return run_cycle(args)


# ---------------------------------------------------------------------------
# Test 1 — trace artifact written after every run
# ---------------------------------------------------------------------------

class TestTraceArtifactWritten:
    def test_trace_artifact_written(self, tmp_path: Path) -> None:
        args = _minimal_args(tmp_path)
        _run_cycle_for_test(args)
        trace_path = _context_dir(args) / "loop_run_trace_latest.json"
        assert trace_path.exists(), "loop_run_trace_latest.json must exist after run"


# ---------------------------------------------------------------------------
# Test 2 — trace schema valid (required keys present, types correct)
# ---------------------------------------------------------------------------

class TestTraceSchemaValid:
    def test_trace_schema_valid(self, tmp_path: Path) -> None:
        args = _minimal_args(tmp_path)
        _run_cycle_for_test(args)
        trace_path = _context_dir(args) / "loop_run_trace_latest.json"
        data = json.loads(trace_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert isinstance(data["trace_id"], str)
        assert isinstance(data["generated_at_utc"], str)
        assert isinstance(data["repo_id"], str)
        assert isinstance(data["duration_seconds"], (int, float))
        assert data["duration_seconds"] >= 0
        assert isinstance(data["steps"], list)
        assert isinstance(data["metrics"], dict)
        assert "pass_count" in data["metrics"]
        assert "total_steps" in data["metrics"]
        assert data["final_result"] in ("PASS", "FAIL", "ERROR", "HOLD")
        assert isinstance(data["final_exit_code"], int)


# ---------------------------------------------------------------------------
# Test 3 — trace_id format matches <YYYYMMDDTHHMMSSz>-<4hex>
# ---------------------------------------------------------------------------

class TestTraceIdFormat:
    def test_trace_id_format(self, tmp_path: Path) -> None:
        args = _minimal_args(tmp_path)
        _run_cycle_for_test(args)
        trace_path = _context_dir(args) / "loop_run_trace_latest.json"
        data = json.loads(trace_path.read_text(encoding="utf-8"))
        trace_id = data["trace_id"]
        assert TRACE_ID_RE.match(trace_id), (
            f"trace_id '{trace_id}' does not match expected pattern "
            r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{4}$"
        )


# ---------------------------------------------------------------------------
# Test 4 — trace_id present on LoopCycleRuntime before first step executes
# ---------------------------------------------------------------------------

class TestTraceIdOnRuntime:
    def test_trace_id_on_runtime(self, tmp_path: Path) -> None:
        ctx_mock = MagicMock()
        ctx_mock.context_dir = tmp_path
        runtime = build_loop_cycle_runtime(ctx_mock)
        assert isinstance(runtime.trace_id, str)
        assert len(runtime.trace_id) > 0
        assert TRACE_ID_RE.match(runtime.trace_id), (
            f"trace_id '{runtime.trace_id}' does not match expected pattern"
        )


# ---------------------------------------------------------------------------
# Test 5 — loop_run_steps_latest.ndjson written with one line per step
# ---------------------------------------------------------------------------

class TestStepsNdjsonWritten:
    def test_steps_ndjson_written(self, tmp_path: Path) -> None:
        args = _minimal_args(tmp_path)
        _run_cycle_for_test(args)
        ndjson_path = _context_dir(args) / "loop_run_steps_latest.ndjson"
        assert ndjson_path.exists(), "loop_run_steps_latest.ndjson must exist after run"
        lines = [ln for ln in ndjson_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) > 0, "NDJSON must have at least one line"
        # Each line must be valid JSON with required fields
        for line in lines:
            record = json.loads(line)
            assert "name" in record
            assert "status" in record
            assert "trace_id" in record


# ---------------------------------------------------------------------------
# Test 6 — metrics.pass_count equals count of PASS steps in the trace
# ---------------------------------------------------------------------------

class TestMetricsMatchSteps:
    def test_metrics_match_steps(self, tmp_path: Path) -> None:
        args = _minimal_args(tmp_path)
        _run_cycle_for_test(args)
        trace_path = _context_dir(args) / "loop_run_trace_latest.json"
        data = json.loads(trace_path.read_text(encoding="utf-8"))
        steps = data["steps"]
        metrics = data["metrics"]
        actual_pass = sum(1 for s in steps if s["status"] == "PASS")
        assert metrics["pass_count"] == actual_pass, (
            f"metrics.pass_count={metrics['pass_count']} but "
            f"counted {actual_pass} PASS steps in trace.steps"
        )
        assert metrics["total_steps"] == len(steps)
