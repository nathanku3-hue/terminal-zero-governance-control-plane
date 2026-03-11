from __future__ import annotations

import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from loop_cycle_context import build_loop_cycle_context
from loop_cycle_runtime import build_loop_cycle_runtime
from loop_cycle_runtime import LoopCycleRuntime


@pytest.fixture
def minimal_args(tmp_path: Path):
    """Create minimal argparse.Namespace for testing."""
    import argparse

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()

    # Create minimal script stubs
    for script_name in [
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
        (script_dir / script_name).write_text("", encoding="utf-8")

    args = argparse.Namespace(
        repo_root=repo_root,
        context_dir=context_dir,
        scripts_dir=script_dir,
        logs_dir=None,
        repo_id="test-repo",
        python_exe="python",
        freshness_hours=24.0,
        pm_budget_tokens=100000,
        ceo_budget_tokens=100000,
        compaction_pm_warn=0.7,
        compaction_ceo_warn=0.7,
        compaction_force=0.9,
        compaction_max_age_hours=168.0,
        skip_phase_end=False,
        phase_end_audit_mode="strict",
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
    return args


def test_build_loop_cycle_runtime_initializes_empty_state(minimal_args) -> None:
    """Test that build_loop_cycle_runtime initializes with empty/default state."""
    ctx = build_loop_cycle_context(minimal_args)
    runtime = build_loop_cycle_runtime(ctx)

    assert isinstance(runtime, LoopCycleRuntime)
    assert runtime.steps == []
    assert runtime.exec_memory_cycle_ready is False
    assert runtime.next_round_handoff_artifacts is None
    assert runtime.expert_request_artifacts is None
    assert runtime.pm_ceo_research_brief_artifacts is None
    assert runtime.board_decision_brief_artifacts is None
    assert runtime.repo_root_convenience is None


def test_runtime_temp_summary_path_derived_from_context(minimal_args) -> None:
    """Test that temp_summary_path is correctly derived from context_dir."""
    ctx = build_loop_cycle_context(minimal_args)
    runtime = build_loop_cycle_runtime(ctx)

    expected_path = ctx.context_dir / "loop_cycle_summary_current.json"
    assert runtime.temp_summary_path == expected_path


def test_runtime_lessons_paths_written_on_init(minimal_args) -> None:
    """Test that lessons stub files are written during initialization."""
    ctx = build_loop_cycle_context(minimal_args)
    runtime = build_loop_cycle_runtime(ctx)

    assert "worker" in runtime.lessons_paths
    assert "auditor" in runtime.lessons_paths

    worker_path = runtime.lessons_paths["worker"]
    auditor_path = runtime.lessons_paths["auditor"]

    assert worker_path.exists()
    assert auditor_path.exists()

    worker_content = worker_path.read_text(encoding="utf-8")
    auditor_content = auditor_path.read_text(encoding="utf-8")

    assert "Worker Lessons Stub" in worker_content
    assert "Auditor Lessons Stub" in auditor_content
    assert runtime.generated_at_utc in worker_content
    assert runtime.generated_at_utc in auditor_content


def test_runtime_generated_at_utc_is_iso_format(minimal_args) -> None:
    """Test that generated_at_utc is a valid ISO 8601 UTC timestamp."""
    ctx = build_loop_cycle_context(minimal_args)
    runtime = build_loop_cycle_runtime(ctx)

    # Should be parseable as ISO 8601
    parsed = datetime.fromisoformat(runtime.generated_at_utc)
    assert parsed.tzinfo is not None
    assert parsed.tzinfo == timezone.utc

    # Should match generated_at
    assert runtime.generated_at_utc == runtime.generated_at.isoformat()


def test_runtime_state_is_mutable(minimal_args) -> None:
    """Test that runtime state fields are mutable (not frozen)."""
    ctx = build_loop_cycle_context(minimal_args)
    runtime = build_loop_cycle_runtime(ctx)

    # Should be able to mutate steps
    runtime.steps.append({"name": "test_step", "status": "PASS"})
    assert len(runtime.steps) == 1

    # Should be able to mutate exec_memory_cycle_ready
    runtime.exec_memory_cycle_ready = True
    assert runtime.exec_memory_cycle_ready is True

    # Should be able to mutate advisory artifacts
    runtime.next_round_handoff_artifacts = {"status": "present", "json": Path("/test"), "md": Path("/test")}
    assert runtime.next_round_handoff_artifacts is not None


def test_runtime_timestamps_are_recent(minimal_args) -> None:
    """Test that generated_at timestamp is recent (within last minute)."""
    ctx = build_loop_cycle_context(minimal_args)
    before = datetime.now(timezone.utc)
    runtime = build_loop_cycle_runtime(ctx)
    after = datetime.now(timezone.utc)

    assert before <= runtime.generated_at <= after
    assert (after - runtime.generated_at).total_seconds() < 60

