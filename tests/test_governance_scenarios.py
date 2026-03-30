"""tests/test_governance_scenarios.py

Phase 6 — End-to-End Integration Tests (3 tests).

Acceptance gates:
  test_governance_scenario_agent_blocked
    — audit_log.ndjson contains decision='SHADOW_BLOCK', actor='policy:gate_a'
      after a run with a shadow BLOCK rule.

  test_governance_scenario_audit_trail_complete
    — every *executed* (non-SKIP) step in loop_run_steps_latest.ndjson has
      a corresponding audit entry.  Gate + policy entries are additional,
      so the assertion is len(executed_steps) <= len(audit_entries_for_trace).

  test_governance_scenario_retry_loop_increments_attempt_id
    — trace_id in audit_metrics_latest.json differs between run 1 and run 2.
      Uses the metrics JSON (single overwritten value), not the accumulating
      NDJSON log, to avoid cross-run parse ambiguity.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "utils"))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _minimal_args(tmp_path: Path) -> argparse.Namespace:
    """Minimal args for run_cycle() — mirrors test_audit_log.py pattern."""
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
        policy_shadow_mode=True,
        policy_rule_file=None,
    )


def _context_dir(args: argparse.Namespace) -> Path:
    return args.repo_root.resolve() / "docs" / "context"


def _run_cycle(args: argparse.Namespace):
    try:
        from sop.scripts.run_loop_cycle import run_cycle
    except ImportError:
        from scripts.run_loop_cycle import run_cycle  # type: ignore[no-redef]
    return run_cycle(args)


def _make_shadow_block_rule() -> dict:
    """Return a shadow BLOCK rule that matches gate_a actor."""
    return {
        "rule_id": "test-shadow-block-gate-a",
        "decision": "BLOCK",
        "scope": "gate",
        "shadow": True,
        "description": "Phase 6 test: shadow-block gate_a for audit trail test",
        "match": {
            "field": "actor",
            "operator": "eq",
            "value": "gate_a",
        },
    }


# ---------------------------------------------------------------------------
# Test 1 — Shadow BLOCK rule produces SHADOW_BLOCK in audit log
# ---------------------------------------------------------------------------

class TestGovernanceScenarioAgentBlocked:
    def test_governance_scenario_agent_blocked(self, tmp_path: Path) -> None:
        """Running run_cycle with a shadow BLOCK rule on gate_a must produce at
        least one audit entry with decision='SHADOW_BLOCK' and
        actor='policy:gate_a'.
        """
        rule_file = tmp_path / "phase6_block_rules.json"
        rule_file.write_text(
            json.dumps({
                "schema_version": "1.0",
                "rules": [_make_shadow_block_rule()],
            }),
            encoding="utf-8",
        )

        args = _minimal_args(tmp_path)
        args.policy_shadow_mode = True
        args.policy_rule_file = rule_file

        _run_cycle(args)

        ctx_dir = _context_dir(args)
        audit_path = ctx_dir / "audit_log.ndjson"
        assert audit_path.exists(), (
            "audit_log.ndjson must exist after a run with a policy rule file"
        )

        entries = [
            json.loads(ln)
            for ln in audit_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(entries) > 0, "audit_log.ndjson must contain at least one entry"

        shadow_block_entries = [
            e for e in entries
            if e.get("decision") == "SHADOW_BLOCK"
            and e.get("actor") == "policy:gate_a"
        ]
        assert len(shadow_block_entries) >= 1, (
            "Expected at least one SHADOW_BLOCK entry with actor='policy:gate_a'. "
            f"Decisions found: {[e.get('decision') for e in entries]}"
        )

        entry = shadow_block_entries[0]
        assert entry["schema_version"] == "1.0"
        assert entry["gate"] == "exec_memory->advisory"
        assert isinstance(entry["trace_id"], str) and entry["trace_id"]


# ---------------------------------------------------------------------------
# Test 2 — Every executed step has a corresponding audit entry
#
# BLOCKER 1 fix: filter loop_run_steps_latest.ndjson to entries where
# status != 'SKIP' before comparing with audit_log.ndjson.
#
# Gate + policy evaluations produce *extra* audit entries, so the assertion
# is len(executed_steps) <= len(audit_entries_for_trace), not ==.
# ---------------------------------------------------------------------------

class TestGovernanceScenarioAuditTrailComplete:
    def test_governance_scenario_audit_trail_complete(self, tmp_path: Path) -> None:
        """Every executed (non-SKIP) step recorded in loop_run_steps_latest.ndjson
        must have at least one corresponding audit entry in audit_log.ndjson
        with the same trace_id.

        Gate A / Gate B evaluations and policy checks emit *additional* audit
        entries beyond step entries, so the audit log entry count is >=
        the executed step count.
        """
        args = _minimal_args(tmp_path)
        _run_cycle(args)

        ctx_dir = _context_dir(args)

        # --- load loop_run_steps_latest.ndjson ---
        steps_path = ctx_dir / "loop_run_steps_latest.ndjson"
        assert steps_path.exists(), (
            "loop_run_steps_latest.ndjson must exist in docs/context/ after a run"
        )

        all_step_records = [
            json.loads(ln)
            for ln in steps_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]

        # Filter to executed (non-skipped) steps only.
        # Skipped steps (_skip_step) have status='SKIP'; emit_audit_log is NOT
        # called for SKIP steps, so we must exclude them from the comparison.
        executed_steps = [
            r for r in all_step_records
            if str(r.get("status", "")).upper() != "SKIP"
        ]

        # --- load audit_log.ndjson ---
        audit_path = ctx_dir / "audit_log.ndjson"
        assert audit_path.exists(), (
            "audit_log.ndjson must exist in docs/context/ after a run"
        )

        audit_entries = [
            json.loads(ln)
            for ln in audit_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(audit_entries) > 0, "audit_log.ndjson must contain at least one entry"

        # --- derive trace_id from audit metrics (single authoritative value) ---
        metrics_path = ctx_dir / "audit_metrics_latest.json"
        assert metrics_path.exists(), (
            "audit_metrics_latest.json must exist after a run"
        )
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        trace_id = metrics["trace_id"]
        assert trace_id, "trace_id in audit_metrics_latest.json must be non-empty"

        # --- assertion ---
        audit_entries_for_trace = [
            e for e in audit_entries if e.get("trace_id") == trace_id
        ]

        # Gate A, Gate B, and policy entries are additional, so audit count >= executed
        assert len(executed_steps) <= len(audit_entries_for_trace), (
            f"Expected audit entry count ({len(audit_entries_for_trace)}) >= "
            f"executed step count ({len(executed_steps)}). "
            f"Executed steps: {[r.get('name') for r in executed_steps]}. "
            f"Audit decisions: {[e.get('decision') for e in audit_entries_for_trace]}."
        )


# ---------------------------------------------------------------------------
# Test 3 — Two consecutive runs produce different trace_ids
#
# BLOCKER 2 fix: compare trace_id from audit_metrics_latest.json (single
# overwritten value per run), not from the accumulating NDJSON log.
# ---------------------------------------------------------------------------

class TestGovernanceScenarioRetryLoopIncrementsAttemptId:
    def test_governance_scenario_retry_loop_increments_attempt_id(
        self, tmp_path: Path
    ) -> None:
        """Two consecutive run_cycle calls on the same repo must produce
        different trace_ids, as reported by audit_metrics_latest.json.

        audit_metrics_latest.json is atomically overwritten on each run,
        making it the clean single-value signal for the current run's trace_id.

        Also asserts that total_decisions increases after the second run,
        confirming the audit log accumulates across runs.
        """
        args = _minimal_args(tmp_path)
        ctx_dir = _context_dir(args)
        metrics_path = ctx_dir / "audit_metrics_latest.json"

        # --- Run 1 ---
        _run_cycle(args)

        assert metrics_path.exists(), (
            "audit_metrics_latest.json must exist after run 1"
        )
        metrics_1 = json.loads(metrics_path.read_text(encoding="utf-8"))
        trace_id_1 = metrics_1["trace_id"]
        total_decisions_1 = metrics_1["total_decisions"]
        assert trace_id_1, "trace_id after run 1 must be non-empty"

        # --- Run 2 (same args, same repo directory) ---
        _run_cycle(args)

        metrics_2 = json.loads(metrics_path.read_text(encoding="utf-8"))
        trace_id_2 = metrics_2["trace_id"]
        total_decisions_2 = metrics_2["total_decisions"]
        assert trace_id_2, "trace_id after run 2 must be non-empty"

        # Each run generates a fresh trace_id
        assert trace_id_1 != trace_id_2, (
            f"trace_id must differ between runs. "
            f"Run 1: {trace_id_1!r}, Run 2: {trace_id_2!r}"
        )

        # audit_log.ndjson accumulates — total_decisions after run 2 must
        # be strictly greater than after run 1.
        assert total_decisions_2 > total_decisions_1, (
            f"total_decisions must increase after run 2. "
            f"Run 1: {total_decisions_1}, Run 2: {total_decisions_2}"
        )
