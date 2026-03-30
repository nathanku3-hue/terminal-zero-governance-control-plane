"""tests/test_audit_log.py

Phase 1 acceptance gates — 2 tests:
  test_audit_log_emitted_on_governance_decision
  test_metrics_export_schema_valid
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

# Make scripts importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "utils"))


# ---------------------------------------------------------------------------
# Helpers (shared with test_observability.py pattern)
# ---------------------------------------------------------------------------

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
    return args.repo_root.resolve() / "docs" / "context"


def _run_cycle_for_test(args: argparse.Namespace):
    try:
        from sop.scripts.run_loop_cycle import run_cycle
    except ImportError:
        from scripts.run_loop_cycle import run_cycle  # type: ignore[no-redef]
    return run_cycle(args)


# ---------------------------------------------------------------------------
# Test 1 — audit_log.ndjson produced with valid entries after a run
# ---------------------------------------------------------------------------

class TestAuditLogEmittedOnGovernanceDecision:
    def test_audit_log_emitted_on_governance_decision(self, tmp_path: Path) -> None:
        args = _minimal_args(tmp_path)
        _run_cycle_for_test(args)

        audit_path = _context_dir(args) / "audit_log.ndjson"
        assert audit_path.exists(), (
            "audit_log.ndjson must exist in docs/context/ after a run"
        )

        lines = [
            ln.strip()
            for ln in audit_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(lines) > 0, "audit_log.ndjson must contain at least one entry"

        # Validate each entry has required schema fields
        required_fields = {
            "schema_version",
            "timestamp_utc",
            "decision",
            "actor",
            "outcome",
            "gate",
            "trace_id",
            "artifact_refs",
        }
        for line in lines:
            entry = json.loads(line)
            missing = required_fields - entry.keys()
            assert not missing, (
                f"Audit entry missing required fields {missing}: {entry}"
            )
            assert entry["schema_version"] == "1.0"
            assert isinstance(entry["timestamp_utc"], str)
            assert isinstance(entry["decision"], str)
            assert isinstance(entry["trace_id"], str)
            assert isinstance(entry["artifact_refs"], dict)

        # At least one step-level entry must be present
        step_entries = [e for e in map(json.loads, lines) if str(e.get("actor", "")).startswith("step:")]
        assert len(step_entries) > 0, (
            "Expected at least one audit entry with actor='step:<name>'"
        )


# ---------------------------------------------------------------------------
# Test 2 — audit_metrics_latest.json schema valid after a run
# ---------------------------------------------------------------------------

class TestMetricsExportSchemaValid:
    def test_metrics_export_schema_valid(self, tmp_path: Path) -> None:
        args = _minimal_args(tmp_path)
        _run_cycle_for_test(args)

        metrics_path = _context_dir(args) / "audit_metrics_latest.json"
        assert metrics_path.exists(), (
            "audit_metrics_latest.json must exist in docs/context/ after a run"
        )

        data = json.loads(metrics_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

        # Required top-level keys
        required_keys = {
            "schema_version",
            "generated_at_utc",
            "trace_id",
            "total_decisions",
            "decision_counts",
            "failure_count",
            "failure_rate",
            "block_count",
            "gate_duration_summary",
        }
        missing = required_keys - data.keys()
        assert not missing, f"audit_metrics_latest.json missing keys: {missing}"

        assert data["schema_version"] == "1.0"
        assert isinstance(data["total_decisions"], int)
        assert data["total_decisions"] >= 0
        assert isinstance(data["decision_counts"], dict)
        assert isinstance(data["failure_count"], int)
        assert isinstance(data["failure_rate"], float)
        assert 0.0 <= data["failure_rate"] <= 1.0
        assert isinstance(data["block_count"], int)
        assert isinstance(data["gate_duration_summary"], dict)
        assert isinstance(data["trace_id"], str)
        assert len(data["trace_id"]) > 0
        # total_decisions must match sum of decision_counts
        assert data["total_decisions"] == sum(data["decision_counts"].values()), (
            "total_decisions must equal sum of all decision_counts values"
        )
