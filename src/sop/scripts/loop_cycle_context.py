from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


def _resolve_path(repo_root: Path, candidate: Path) -> Path:
    """Resolve a path relative to repo_root if not absolute."""
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _resolve_with_default(repo_root: Path, value: Path | None, default_path: Path) -> Path:
    """Resolve a path with a default fallback."""
    if value is None:
        return default_path
    return _resolve_path(repo_root=repo_root, candidate=value)


@dataclass(frozen=True)
class LoopCycleContext:
    """Immutable context for loop cycle execution.

    Contains all resolved paths, CLI settings, and repo identity.
    No mutable runtime state (steps, exec_memory_cycle_ready, temp paths).
    """
    # Core paths
    repo_root: Path
    context_dir: Path
    script_dir: Path
    logs_dir: Path

    # Repo identity
    repo_id: str

    # CLI settings
    python_exe: str
    freshness_hours: float
    pm_budget_tokens: int
    ceo_budget_tokens: int
    compaction_pm_warn: float
    compaction_ceo_warn: float
    compaction_force: float
    compaction_max_age_hours: float
    skip_phase_end: bool
    phase_end_audit_mode: str
    allow_hold: bool

    # Artifact paths - auditor reports
    weekly_report_json: Path
    weekly_report_md: Path
    dossier_json: Path
    dossier_md: Path
    fp_ledger_json: Path
    disagreement_ledger_jsonl: Path

    # Artifact paths - CEO outputs
    go_signal_md: Path
    weekly_summary_md: Path

    # Artifact paths - exec memory
    exec_memory_latest_json: Path
    exec_memory_latest_md: Path
    exec_memory_current_json: Path
    exec_memory_current_md: Path
    exec_memory_build_status_json: Path

    # Artifact paths - advisory sections
    next_round_handoff_json: Path
    next_round_handoff_md: Path
    expert_request_json: Path
    expert_request_md: Path
    pm_ceo_research_brief_json: Path
    pm_ceo_research_brief_md: Path
    board_decision_brief_json: Path
    board_decision_brief_md: Path

    # Artifact paths - compaction
    compaction_state_json: Path
    compaction_status_json: Path

    # Artifact paths - loop cycle outputs
    output_json: Path
    output_md: Path
    closure_output_json: Path
    closure_output_md: Path

    # Artifact paths - validation inputs
    review_checklist_md: Path
    interface_contract_manifest_json: Path

    # Script paths
    phase_end_script: Path
    auditor_script: Path
    go_signal_script: Path
    go_truth_script: Path
    weekly_truth_script: Path
    weekly_summary_gen_script: Path
    round_contract_checks_script: Path
    counterexample_script: Path
    dual_judge_script: Path
    refactor_mock_policy_script: Path
    review_checklist_script: Path
    interface_contracts_script: Path
    parallel_fanin_script: Path
    memory_packet_script: Path
    compaction_trigger_script: Path
    memory_truth_script: Path
    closure_script: Path


def build_loop_cycle_context(args: argparse.Namespace) -> LoopCycleContext:
    """Build immutable loop cycle context from parsed arguments.

    Resolves all paths absolutely and applies defaults.
    """
    repo_root = args.repo_root.resolve()
    context_dir = _resolve_path(repo_root=repo_root, candidate=args.context_dir)
    script_dir = (
        _resolve_path(repo_root=repo_root, candidate=args.scripts_dir)
        if args.scripts_dir is not None
        else Path(__file__).resolve().parent
    )

    logs_dir = _resolve_with_default(
        repo_root=repo_root,
        value=args.logs_dir,
        default_path=context_dir / "phase_end_logs",
    )

    # Resolve artifact paths with defaults
    weekly_report_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_report_json,
        default_path=context_dir / "auditor_calibration_report.json",
    )
    weekly_report_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_report_md,
        default_path=context_dir / "auditor_calibration_report.md",
    )
    dossier_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.dossier_json,
        default_path=context_dir / "auditor_promotion_dossier.json",
    )
    dossier_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.dossier_md,
        default_path=context_dir / "auditor_promotion_dossier.md",
    )
    go_signal_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.go_signal_md,
        default_path=context_dir / "ceo_go_signal.md",
    )
    weekly_summary_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_summary_md,
        default_path=context_dir / "ceo_weekly_summary_latest.md",
    )
    fp_ledger_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.fp_ledger_json,
        default_path=context_dir / "auditor_fp_ledger.json",
    )
    disagreement_ledger_jsonl = _resolve_with_default(
        repo_root=repo_root,
        value=args.disagreement_ledger_jsonl,
        default_path=context_dir / "disagreement_ledger.jsonl",
    )

    output_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.output_json,
        default_path=context_dir / "loop_cycle_summary_latest.json",
    )
    output_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.output_md,
        default_path=context_dir / "loop_cycle_summary_latest.md",
    )
    closure_output_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.closure_output_json,
        default_path=context_dir / "loop_closure_status_latest.json",
    )
    closure_output_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.closure_output_md,
        default_path=context_dir / "loop_closure_status_latest.md",
    )

    # Resolve script paths with defaults
    phase_end_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.phase_end_script,
        default_path=script_dir / "phase_end_handover.ps1",
    )
    go_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.go_truth_script,
        default_path=script_dir / "validate_ceo_go_signal_truth.py",
    )
    weekly_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_truth_script,
        default_path=script_dir / "validate_ceo_weekly_summary_truth.py",
    )
    weekly_summary_gen_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_summary_gen_script,
        default_path=script_dir / "generate_ceo_weekly_summary.py",
    )
    memory_packet_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.memory_packet_script,
        default_path=script_dir / "build_exec_memory_packet.py",
    )
    compaction_trigger_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.compaction_trigger_script,
        default_path=script_dir / "evaluate_context_compaction_trigger.py",
    )
    memory_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.memory_truth_script,
        default_path=script_dir / "validate_exec_memory_truth.py",
    )
    closure_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.closure_script,
        default_path=script_dir / "validate_loop_closure.py",
    )

    # Exec memory paths
    exec_memory_latest_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.exec_memory_json,
        default_path=context_dir / "exec_memory_packet_latest.json",
    )
    exec_memory_latest_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.exec_memory_md,
        default_path=context_dir / "exec_memory_packet_latest.md",
    )
    exec_memory_current_json = exec_memory_latest_json.with_name(
        f"{exec_memory_latest_json.stem}_current{exec_memory_latest_json.suffix}"
    )
    exec_memory_current_md = exec_memory_latest_md.with_name(
        f"{exec_memory_latest_md.stem}_current{exec_memory_latest_md.suffix}"
    )
    exec_memory_build_status_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.exec_memory_build_status_json,
        default_path=context_dir / "exec_memory_packet_build_status_current.json",
    )

    # Compaction paths
    compaction_state_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.compaction_state_json,
        default_path=context_dir / "context_compaction_state_latest.json",
    )
    compaction_status_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.compaction_status_json,
        default_path=context_dir / "context_compaction_status_latest.json",
    )

    # Derive repo_id
    repo_id = args.repo_id.strip() or repo_root.name or "repo"

    return LoopCycleContext(
        # Core paths
        repo_root=repo_root,
        context_dir=context_dir,
        script_dir=script_dir,
        logs_dir=logs_dir,

        # Repo identity
        repo_id=repo_id,

        # CLI settings
        python_exe=args.python_exe,
        freshness_hours=args.freshness_hours,
        pm_budget_tokens=args.pm_budget_tokens,
        ceo_budget_tokens=args.ceo_budget_tokens,
        compaction_pm_warn=args.compaction_pm_warn,
        compaction_ceo_warn=args.compaction_ceo_warn,
        compaction_force=args.compaction_force,
        compaction_max_age_hours=args.compaction_max_age_hours,
        skip_phase_end=args.skip_phase_end,
        phase_end_audit_mode=args.phase_end_audit_mode,
        allow_hold=bool(args.allow_hold),

        # Artifact paths - auditor reports
        weekly_report_json=weekly_report_json,
        weekly_report_md=weekly_report_md,
        dossier_json=dossier_json,
        dossier_md=dossier_md,
        fp_ledger_json=fp_ledger_json,
        disagreement_ledger_jsonl=disagreement_ledger_jsonl,

        # Artifact paths - CEO outputs
        go_signal_md=go_signal_md,
        weekly_summary_md=weekly_summary_md,

        # Artifact paths - exec memory
        exec_memory_latest_json=exec_memory_latest_json,
        exec_memory_latest_md=exec_memory_latest_md,
        exec_memory_current_json=exec_memory_current_json,
        exec_memory_current_md=exec_memory_current_md,
        exec_memory_build_status_json=exec_memory_build_status_json,

        # Artifact paths - advisory sections
        next_round_handoff_json=context_dir / "next_round_handoff_latest.json",
        next_round_handoff_md=context_dir / "next_round_handoff_latest.md",
        expert_request_json=context_dir / "expert_request_latest.json",
        expert_request_md=context_dir / "expert_request_latest.md",
        pm_ceo_research_brief_json=context_dir / "pm_ceo_research_brief_latest.json",
        pm_ceo_research_brief_md=context_dir / "pm_ceo_research_brief_latest.md",
        board_decision_brief_json=context_dir / "board_decision_brief_latest.json",
        board_decision_brief_md=context_dir / "board_decision_brief_latest.md",

        # Artifact paths - compaction
        compaction_state_json=compaction_state_json,
        compaction_status_json=compaction_status_json,

        # Artifact paths - loop cycle outputs
        output_json=output_json,
        output_md=output_md,
        closure_output_json=closure_output_json,
        closure_output_md=closure_output_md,

        # Artifact paths - validation inputs
        review_checklist_md=context_dir / "pr_review_checklist_latest.md",
        interface_contract_manifest_json=context_dir / "interface_contract_manifest_latest.json",

        # Script paths
        phase_end_script=phase_end_script,
        auditor_script=script_dir / "auditor_calibration_report.py",
        go_signal_script=script_dir / "generate_ceo_go_signal.py",
        go_truth_script=go_truth_script,
        weekly_truth_script=weekly_truth_script,
        weekly_summary_gen_script=weekly_summary_gen_script,
        round_contract_checks_script=script_dir / "validate_round_contract_checks.py",
        counterexample_script=script_dir / "validate_counterexample_gate.py",
        dual_judge_script=script_dir / "validate_dual_judge_gate.py",
        refactor_mock_policy_script=script_dir / "validate_refactor_mock_policy.py",
        review_checklist_script=script_dir / "validate_review_checklist.py",
        interface_contracts_script=script_dir / "validate_interface_contracts.py",
        parallel_fanin_script=script_dir / "validate_parallel_fanin.py",
        memory_packet_script=memory_packet_script,
        compaction_trigger_script=compaction_trigger_script,
        memory_truth_script=memory_truth_script,
        closure_script=closure_script,
    )
