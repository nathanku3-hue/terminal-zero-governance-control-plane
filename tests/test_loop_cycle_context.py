from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

try:
    from loop_cycle_context import LoopCycleContext, build_loop_cycle_context
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from loop_cycle_context import LoopCycleContext, build_loop_cycle_context


def test_build_context_resolves_all_paths_absolutely(tmp_path: Path) -> None:
    """All paths in context must be absolute."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    args = argparse.Namespace(
        repo_root=repo_root,
        context_dir=Path("docs/context"),
        scripts_dir=None,
        python_exe=sys.executable,
        repo_id="test-repo",
        skip_phase_end=False,
        phase_end_script=None,
        phase_end_audit_mode="shadow",
        logs_dir=None,
        fp_ledger_json=None,
        weekly_report_json=None,
        weekly_report_md=None,
        dossier_json=None,
        dossier_md=None,
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
        compaction_pm_warn=0.75,
        compaction_ceo_warn=0.70,
        compaction_force=0.90,
        compaction_max_age_hours=24.0,
        pm_budget_tokens=3000,
        ceo_budget_tokens=1800,
        closure_script=None,
        closure_output_json=None,
        closure_output_md=None,
        freshness_hours=72.0,
        allow_hold=True,
        disagreement_ledger_jsonl=None,
        output_json=None,
        output_md=None,
    )

    ctx = build_loop_cycle_context(args)

    # All paths must be absolute
    assert ctx.repo_root.is_absolute()
    assert ctx.context_dir.is_absolute()
    assert ctx.script_dir.is_absolute()
    assert ctx.logs_dir.is_absolute()
    assert ctx.weekly_report_json.is_absolute()
    assert ctx.weekly_report_md.is_absolute()
    assert ctx.dossier_json.is_absolute()
    assert ctx.dossier_md.is_absolute()
    assert ctx.go_signal_md.is_absolute()
    assert ctx.weekly_summary_md.is_absolute()
    assert ctx.fp_ledger_json.is_absolute()
    assert ctx.disagreement_ledger_jsonl.is_absolute()
    assert ctx.output_json.is_absolute()
    assert ctx.output_md.is_absolute()
    assert ctx.closure_output_json.is_absolute()
    assert ctx.closure_output_md.is_absolute()
    assert ctx.phase_end_script.is_absolute()
    assert ctx.auditor_script.is_absolute()
    assert ctx.go_signal_script.is_absolute()
    assert ctx.closure_script.is_absolute()


def test_build_context_applies_defaults_correctly(tmp_path: Path) -> None:
    """Default paths should be applied when args are None."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    args = argparse.Namespace(
        repo_root=repo_root,
        context_dir=Path("docs/context"),
        scripts_dir=None,
        python_exe=sys.executable,
        repo_id="",
        skip_phase_end=False,
        phase_end_script=None,
        phase_end_audit_mode="shadow",
        logs_dir=None,
        fp_ledger_json=None,
        weekly_report_json=None,
        weekly_report_md=None,
        dossier_json=None,
        dossier_md=None,
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
        compaction_pm_warn=0.75,
        compaction_ceo_warn=0.70,
        compaction_force=0.90,
        compaction_max_age_hours=24.0,
        pm_budget_tokens=3000,
        ceo_budget_tokens=1800,
        closure_script=None,
        closure_output_json=None,
        closure_output_md=None,
        freshness_hours=72.0,
        allow_hold=True,
        disagreement_ledger_jsonl=None,
        output_json=None,
        output_md=None,
    )

    ctx = build_loop_cycle_context(args)

    # Check default paths are applied
    assert ctx.context_dir == repo_root / "docs/context"
    assert ctx.logs_dir == ctx.context_dir / "phase_end_logs"
    assert ctx.weekly_report_json == ctx.context_dir / "auditor_calibration_report.json"
    assert ctx.weekly_report_md == ctx.context_dir / "auditor_calibration_report.md"
    assert ctx.dossier_json == ctx.context_dir / "auditor_promotion_dossier.json"
    assert ctx.dossier_md == ctx.context_dir / "auditor_promotion_dossier.md"
    assert ctx.go_signal_md == ctx.context_dir / "ceo_go_signal.md"
    assert ctx.output_json == ctx.context_dir / "loop_cycle_summary_latest.json"
    assert ctx.output_md == ctx.context_dir / "loop_cycle_summary_latest.md"

    # Check repo_id derivation
    assert ctx.repo_id == "repo"


def test_build_context_respects_explicit_overrides(tmp_path: Path) -> None:
    """Explicit path overrides should be used instead of defaults."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    custom_logs = tmp_path / "custom_logs"
    custom_output = tmp_path / "custom_output.json"

    args = argparse.Namespace(
        repo_root=repo_root,
        context_dir=Path("docs/context"),
        scripts_dir=None,
        python_exe=sys.executable,
        repo_id="custom-id",
        skip_phase_end=True,
        phase_end_script=None,
        phase_end_audit_mode="live",
        logs_dir=custom_logs,
        fp_ledger_json=None,
        weekly_report_json=None,
        weekly_report_md=None,
        dossier_json=None,
        dossier_md=None,
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
        compaction_pm_warn=0.80,
        compaction_ceo_warn=0.75,
        compaction_force=0.95,
        compaction_max_age_hours=48.0,
        pm_budget_tokens=5000,
        ceo_budget_tokens=3000,
        closure_script=None,
        closure_output_json=None,
        closure_output_md=None,
        freshness_hours=96.0,
        allow_hold=False,
        disagreement_ledger_jsonl=None,
        output_json=custom_output,
        output_md=None,
    )

    ctx = build_loop_cycle_context(args)

    # Check explicit overrides are respected
    assert ctx.logs_dir == custom_logs
    assert ctx.output_json == custom_output
    assert ctx.repo_id == "custom-id"
    assert ctx.skip_phase_end is True
    assert ctx.phase_end_audit_mode == "live"
    assert ctx.freshness_hours == 96.0
    assert ctx.pm_budget_tokens == 5000
    assert ctx.ceo_budget_tokens == 3000
    assert ctx.compaction_pm_warn == 0.80
    assert ctx.compaction_ceo_warn == 0.75
    assert ctx.compaction_force == 0.95
    assert ctx.compaction_max_age_hours == 48.0
    assert ctx.allow_hold is False


def test_context_is_immutable(tmp_path: Path) -> None:
    """Context dataclass must be frozen (immutable)."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    args = argparse.Namespace(
        repo_root=repo_root,
        context_dir=Path("docs/context"),
        scripts_dir=None,
        python_exe=sys.executable,
        repo_id="test-repo",
        skip_phase_end=False,
        phase_end_script=None,
        phase_end_audit_mode="shadow",
        logs_dir=None,
        fp_ledger_json=None,
        weekly_report_json=None,
        weekly_report_md=None,
        dossier_json=None,
        dossier_md=None,
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
        compaction_pm_warn=0.75,
        compaction_ceo_warn=0.70,
        compaction_force=0.90,
        compaction_max_age_hours=24.0,
        pm_budget_tokens=3000,
        ceo_budget_tokens=1800,
        closure_script=None,
        closure_output_json=None,
        closure_output_md=None,
        freshness_hours=72.0,
        allow_hold=True,
        disagreement_ledger_jsonl=None,
        output_json=None,
        output_md=None,
    )

    ctx = build_loop_cycle_context(args)

    # Attempt to modify should raise FrozenInstanceError
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
        ctx.repo_id = "modified"  # type: ignore


def test_context_cli_settings_match_args(tmp_path: Path) -> None:
    """CLI settings in context must match args exactly."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    args = argparse.Namespace(
        repo_root=repo_root,
        context_dir=Path("docs/context"),
        scripts_dir=None,
        python_exe="/usr/bin/python3",
        repo_id="test-repo",
        skip_phase_end=True,
        phase_end_script=None,
        phase_end_audit_mode="live",
        logs_dir=None,
        fp_ledger_json=None,
        weekly_report_json=None,
        weekly_report_md=None,
        dossier_json=None,
        dossier_md=None,
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
        compaction_pm_warn=0.85,
        compaction_ceo_warn=0.80,
        compaction_force=0.92,
        compaction_max_age_hours=36.0,
        pm_budget_tokens=4000,
        ceo_budget_tokens=2500,
        closure_script=None,
        closure_output_json=None,
        closure_output_md=None,
        freshness_hours=48.0,
        allow_hold=False,
        disagreement_ledger_jsonl=None,
        output_json=None,
        output_md=None,
    )

    ctx = build_loop_cycle_context(args)

    # Verify all CLI settings match
    assert ctx.python_exe == "/usr/bin/python3"
    assert ctx.freshness_hours == 48.0
    assert ctx.pm_budget_tokens == 4000
    assert ctx.ceo_budget_tokens == 2500
    assert ctx.compaction_pm_warn == 0.85
    assert ctx.compaction_ceo_warn == 0.80
    assert ctx.compaction_force == 0.92
    assert ctx.compaction_max_age_hours == 36.0
    assert ctx.skip_phase_end is True
    assert ctx.phase_end_audit_mode == "live"
    assert ctx.allow_hold is False


def test_repo_id_derivation_matches_original(tmp_path: Path) -> None:
    """Repo ID derivation must match original run_loop_cycle.py logic."""
    # Test empty repo_id -> uses repo_root.name
    repo_root = tmp_path / "my_repo"
    repo_root.mkdir()

    args = argparse.Namespace(
        repo_root=repo_root,
        context_dir=Path("docs/context"),
        scripts_dir=None,
        python_exe=sys.executable,
        repo_id="",
        skip_phase_end=False,
        phase_end_script=None,
        phase_end_audit_mode="shadow",
        logs_dir=None,
        fp_ledger_json=None,
        weekly_report_json=None,
        weekly_report_md=None,
        dossier_json=None,
        dossier_md=None,
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
        compaction_pm_warn=0.75,
        compaction_ceo_warn=0.70,
        compaction_force=0.90,
        compaction_max_age_hours=24.0,
        pm_budget_tokens=3000,
        ceo_budget_tokens=1800,
        closure_script=None,
        closure_output_json=None,
        closure_output_md=None,
        freshness_hours=72.0,
        allow_hold=True,
        disagreement_ledger_jsonl=None,
        output_json=None,
        output_md=None,
    )

    ctx = build_loop_cycle_context(args)
    assert ctx.repo_id == "my_repo"

    # Test explicit repo_id
    args.repo_id = "explicit-id"
    ctx = build_loop_cycle_context(args)
    assert ctx.repo_id == "explicit-id"

    # Test whitespace-only repo_id -> uses repo_root.name
    args.repo_id = "   "
    ctx = build_loop_cycle_context(args)
    assert ctx.repo_id == "my_repo"
