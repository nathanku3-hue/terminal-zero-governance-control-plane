"""tests/test_orchestrator.py

Phase 2.3 done criteria -- 5 tests:
  test_step_executor_run_missing_script
  test_step_executor_run_success
  test_orchestrator_build_summary_payload
  test_orchestrator_step_by_name
  test_run_cycle_returns_int
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "utils"))

from step_executor import StepExecutor
from orchestrator import LoopOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_runtime(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        steps=[],
        trace_id="20260328T120000Z-abcd",
        generated_at_utc="2026-03-28T12:00:00Z",
        temp_summary_path=tmp_path / "loop_cycle_summary_current.json",
        exec_memory_cycle_ready=False,
        repo_root_convenience=None,
    )


def _minimal_ctx(tmp_path: Path) -> SimpleNamespace:
    context_dir = tmp_path / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(
        repo_root=tmp_path,
        context_dir=context_dir,
        script_dir=tmp_path / "scripts",
        python_exe=sys.executable,
        skip_phase_end=True,
        allow_hold=True,
        freshness_hours=24.0,
        compaction_status_json=context_dir / "context_compaction_status_latest.json",
        disagreement_ledger_jsonl=context_dir / "disagreement_ledger.jsonl",
        exec_memory_current_json=context_dir / "exec_memory_packet_latest_current.json",
        exec_memory_current_md=context_dir / "exec_memory_packet_latest_current.md",
        exec_memory_latest_json=context_dir / "exec_memory_packet_latest.json",
        exec_memory_latest_md=context_dir / "exec_memory_packet_latest.md",
        exec_memory_build_status_json=context_dir / "exec_memory_packet_build_status_current.json",
        memory_packet_script=tmp_path / "scripts" / "build_exec_memory_packet.py",
        output_json=context_dir / "loop_cycle_summary_latest.json",
        pm_budget_tokens=1000,
        ceo_budget_tokens=1000,
    )


# ---------------------------------------------------------------------------
# Test 1 -- StepExecutor records ERROR for missing script
# ---------------------------------------------------------------------------

class TestStepExecutorMissingScript:
    def test_step_executor_run_missing_script(self, tmp_path: Path) -> None:
        ctx = _minimal_ctx(tmp_path)
        runtime = _minimal_runtime(tmp_path)
        executor = StepExecutor(ctx=ctx, runtime=runtime)
        missing = tmp_path / "nonexistent.py"
        executor.run("test_step", missing, [])
        assert len(runtime.steps) == 1
        step = runtime.steps[0]
        assert step["name"] == "test_step"
        assert step["status"] == "ERROR"
        assert step["exit_code"] is None
        assert "Missing script" in step["message"]


# ---------------------------------------------------------------------------
# Test 2 -- StepExecutor records PASS for successful script
# ---------------------------------------------------------------------------

class TestStepExecutorSuccess:
    def test_step_executor_run_success(self, tmp_path: Path) -> None:
        ctx = _minimal_ctx(tmp_path)
        runtime = _minimal_runtime(tmp_path)
        executor = StepExecutor(ctx=ctx, runtime=runtime)
        # Create a trivial script that exits 0
        script = tmp_path / "ok_script.py"
        script.write_text("import sys; sys.exit(0)", encoding="utf-8")
        executor.run("ok_step", script, [])
        assert len(runtime.steps) == 1
        step = runtime.steps[0]
        assert step["name"] == "ok_step"
        assert step["status"] == "PASS"
        assert step["exit_code"] == 0


# ---------------------------------------------------------------------------
# Test 3 -- LoopOrchestrator.build_summary_payload returns expected shape
# ---------------------------------------------------------------------------

class TestOrchestratorBuildSummaryPayload:
    def test_orchestrator_build_summary_payload(self, tmp_path: Path) -> None:
        ctx = _minimal_ctx(tmp_path)
        runtime = _minimal_runtime(tmp_path)
        runtime.steps = [
            {"name": "step_a", "status": "PASS", "exit_code": 0},
            {"name": "step_b", "status": "SKIP", "exit_code": 0},
        ]

        def _fake_lcs(**kw):
            return {"status": "skipped"}

        orch = LoopOrchestrator(
            ctx=ctx,
            runtime=runtime,
            helpers={"_load_compaction_status_summary": _fake_lcs},
        )
        payload = orch.build_summary_payload(disagreement_sla={})
        assert payload["schema_version"] == "1.0.0"
        assert payload["step_summary"]["pass_count"] == 1
        assert payload["step_summary"]["skip_count"] == 1
        assert payload["final_result"] == "PASS"
        assert payload["final_exit_code"] == 0


# ---------------------------------------------------------------------------
# Test 4 -- LoopOrchestrator._step_by_name finds and misses correctly
# ---------------------------------------------------------------------------

class TestOrchestratorStepByName:
    def test_orchestrator_step_by_name(self, tmp_path: Path) -> None:
        ctx = _minimal_ctx(tmp_path)
        runtime = _minimal_runtime(tmp_path)
        runtime.steps = [
            {"name": "alpha", "status": "PASS"},
            {"name": "beta", "status": "FAIL"},
        ]
        orch = LoopOrchestrator(ctx=ctx, runtime=runtime, helpers={})
        assert orch._step_by_name("alpha")["status"] == "PASS"
        assert orch._step_by_name("beta")["status"] == "FAIL"
        assert orch._step_by_name("gamma") is None


# ---------------------------------------------------------------------------
# Test 5 -- run_cycle() returns int exit code
# ---------------------------------------------------------------------------

class TestRunCycleReturnsInt:
    def test_run_cycle_returns_int(self, tmp_path: Path) -> None:
        """run_cycle(args) must return an int (Phase 2.3 thin wrapper)."""
        try:
            from sop.scripts.run_loop_cycle import run_cycle_int, parse_args
        except ImportError:
            from scripts.run_loop_cycle import run_cycle_int, parse_args

        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        context_dir = tmp_path / "context"
        context_dir.mkdir()
        script_dir = tmp_path / "scripts"
        script_dir.mkdir()
        for name in ["auditor_calibration_report.py","generate_ceo_go_signal.py",
                     "generate_ceo_weekly_summary.py","evaluate_context_compaction_trigger.py",
                     "build_exec_memory_packet.py","validate_ceo_go_signal_truth.py",
                     "validate_exec_memory_truth.py","validate_ceo_weekly_summary_truth.py",
                     "validate_round_contract_checks.py","validate_counterexample_gate.py",
                     "validate_dual_judge_gate.py","validate_refactor_mock_policy.py",
                     "validate_review_checklist.py","validate_interface_contracts.py",
                     "validate_parallel_fanin.py","validate_loop_closure.py",
                     "phase_end_handover.ps1"]:
            (script_dir / name).write_text("", encoding="utf-8")

        args = argparse.Namespace(
            repo_root=repo_root, context_dir=context_dir, scripts_dir=script_dir,
            logs_dir=None, repo_id="test", python_exe=sys.executable,
            freshness_hours=24.0, pm_budget_tokens=1000, ceo_budget_tokens=1000,
            compaction_pm_warn=0.7, compaction_ceo_warn=0.7, compaction_force=0.9,
            compaction_max_age_hours=168.0, skip_phase_end=True,
            phase_end_audit_mode="shadow", allow_hold=True,
            step_sla_seconds=300.0, force=False, dry_run=False,
            weekly_report_json=None, weekly_report_md=None, dossier_json=None,
            dossier_md=None, fp_ledger_json=None, disagreement_ledger_jsonl=None,
            output_json=None, output_md=None, go_signal_md=None, weekly_summary_md=None,
            weekly_summary_gen_script=None, go_truth_script=None, weekly_truth_script=None,
            memory_packet_script=None, compaction_trigger_script=None, memory_truth_script=None,
            exec_memory_json=None, exec_memory_md=None, exec_memory_build_status_json=None,
            compaction_state_json=None, compaction_status_json=None, closure_script=None,
            closure_output_json=None, closure_output_md=None, phase_end_script=None,
        )
        result = run_cycle_int(args)
        assert isinstance(result, int), f"run_cycle_int must return int, got {type(result)}"
