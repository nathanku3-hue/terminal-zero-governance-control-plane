"""tests/test_policy_engine.py

Phase 2 — Policy Engine acceptance gates (4 tests):

  test_policy_engine_blocks_on_violation
  test_shadow_mode_does_not_block
  test_policy_violation_appears_in_audit_log
  test_policy_validate_cli_valid_rules
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULE_FILE = REPO_ROOT / "docs" / "policy_rules_default.json"


def _make_block_rule(shadow: bool = False) -> dict:
    """Return a single BLOCK rule that matches gate=exec_memory->advisory."""
    return {
        "rule_id": "test-block-gate-a",
        "decision": "BLOCK",
        "scope": "gate",
        "shadow": shadow,
        "description": "Test rule: block gate_a PROCEED",
        "match": {
            "field": "actor",
            "operator": "eq",
            "value": "gate_a",
        },
    }


def _gate_a_action(decision: str = "PROCEED", trace_id: str = "test-trace-001") -> dict:
    return {
        "gate": "exec_memory->advisory",
        "decision": decision,
        "trace_id": trace_id,
        "actor": "gate_a",
    }


def _minimal_args(tmp_path: Path) -> argparse.Namespace:
    """Minimal args for run_cycle() — mirrors the pattern in test_audit_log.py."""
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
        # Phase 2 policy engine
        policy_shadow_mode=True,
        policy_rule_file=None,
    )


def _run_cycle_for_test(args: argparse.Namespace):
    try:
        from sop.scripts.run_loop_cycle import run_cycle
    except ImportError:
        from scripts.run_loop_cycle import run_cycle  # type: ignore[no-redef]
    return run_cycle(args)


# ---------------------------------------------------------------------------
# Test 1 — pure unit: BLOCK rule triggers on matching action
# ---------------------------------------------------------------------------

class TestPolicyEngineBlocksOnViolation:
    def test_policy_engine_blocks_on_violation(self) -> None:
        """A non-shadow BLOCK rule must return decision='BLOCK' on a matching action."""
        from sop._policy_engine import evaluate_policy

        rules = [_make_block_rule(shadow=False)]
        action = _gate_a_action()
        result = evaluate_policy(action, rules)

        assert result.decision == "BLOCK", (
            f"Expected BLOCK, got {result.decision!r}. reason={result.reason!r}"
        )
        assert result.rule_id == "test-block-gate-a"
        assert result.shadow is False


# ---------------------------------------------------------------------------
# Test 2 — pure unit: shadow BLOCK rule logs but does not block
# ---------------------------------------------------------------------------

class TestShadowModeDoesNotBlock:
    def test_shadow_mode_does_not_block(self) -> None:
        """A shadow=True BLOCK rule must return SHADOW_BLOCK, not BLOCK.

        The gate outcome is unchanged — only the decision string differs.
        """
        from sop._policy_engine import evaluate_policy

        rules = [_make_block_rule(shadow=True)]
        action = _gate_a_action()
        result = evaluate_policy(action, rules)

        assert result.decision == "SHADOW_BLOCK", (
            f"Expected SHADOW_BLOCK, got {result.decision!r}"
        )
        assert result.shadow is True
        assert result.rule_id == "test-block-gate-a"


# ---------------------------------------------------------------------------
# Test 3 — integration: shadow BLOCK rule appears in audit log
# ---------------------------------------------------------------------------

class TestPolicyViolationAppearsInAuditLog:
    def test_policy_violation_appears_in_audit_log(self, tmp_path: Path) -> None:
        """Running run_cycle with a shadow BLOCK rule must produce a SHADOW_BLOCK
        audit log entry with actor='policy:gate_a'.
        """
        # Write a rule file with a shadow BLOCK rule that matches gate_a PROCEED
        rule_file = tmp_path / "test_policy_rules.json"
        rule_file.write_text(
            json.dumps({
                "schema_version": "1.0",
                "rules": [_make_block_rule(shadow=True)],
            }),
            encoding="utf-8",
        )

        args = _minimal_args(tmp_path)
        args.policy_shadow_mode = True   # shadow: log only, no blocking
        args.policy_rule_file = rule_file

        _run_cycle_for_test(args)

        context_dir = args.repo_root.resolve() / "docs" / "context"
        audit_path = context_dir / "audit_log.ndjson"
        assert audit_path.exists(), "audit_log.ndjson must exist after a run"

        entries = [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        shadow_block_entries = [
            e for e in entries
            if e.get("decision") == "SHADOW_BLOCK"
            and e.get("actor") == "policy:gate_a"
        ]
        assert len(shadow_block_entries) >= 1, (
            f"Expected at least one SHADOW_BLOCK entry with actor='policy:gate_a' in audit log. "
            f"Entries found: {[e.get('decision') for e in entries]}"
        )
        # Verify the entry has the expected structure
        entry = shadow_block_entries[0]
        assert entry["schema_version"] == "1.0"
        assert entry["gate"] == "exec_memory->advisory"
        assert isinstance(entry["trace_id"], str)
        # Gate outcome must not be blocked — run completes normally in shadow mode
        gate_a_entries = [e for e in entries if e.get("actor") == "gate_a"]
        assert len(gate_a_entries) >= 1, "Expected a gate_a audit entry"


# ---------------------------------------------------------------------------
# Test 4 — CLI: sop policy validate exits 0 on valid rule file
# ---------------------------------------------------------------------------

class TestPolicyValidateCliValidRules:
    def test_policy_validate_cli_valid_rules(self) -> None:
        """sop policy validate --rule-file <default> must exit 0 on a valid file."""
        from sop.__main__ import build_parser, cmd_policy_validate

        assert DEFAULT_RULE_FILE.exists(), (
            f"docs/policy_rules_default.json not found at {DEFAULT_RULE_FILE}. "
            "Create it before running this test."
        )

        parser = build_parser()
        args = parser.parse_args(
            ["policy", "validate", "--rule-file", str(DEFAULT_RULE_FILE)]
        )
        exit_code = cmd_policy_validate(args)
        assert exit_code == 0, (
            f"Expected exit code 0 for valid rule file, got {exit_code}"
        )

            