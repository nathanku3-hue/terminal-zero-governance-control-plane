"""tests/test_policy_engine.py

Phase 2 — Policy Engine acceptance gates.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULE_FILE = REPO_ROOT / "docs" / "policy_rules_default.json"


def _make_block_rule(shadow: bool = False) -> dict:
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
        "scope": "gate",
        "permissions": ["policy.evaluate.gate_a"],
        "tenant_id": "tenant-alpha",
        "actor": "gate_a",
    }


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
        policy_shadow_mode=True,
        policy_rule_file=None,
    )


def _run_cycle_for_test(args: argparse.Namespace):
    try:
        from sop.scripts.run_loop_cycle import run_cycle
    except ImportError:
        from scripts.run_loop_cycle import run_cycle  # type: ignore[no-redef]
    return run_cycle(args)


class TestPolicyEngineBlocksOnViolation:
    def test_policy_engine_blocks_on_violation(self) -> None:
        from sop._policy_engine import evaluate_policy

        rules = [_make_block_rule(shadow=False)]
        action = _gate_a_action()
        result = evaluate_policy(action, rules)

        assert result.decision == "BLOCK"
        assert result.rule_id == "test-block-gate-a"
        assert result.shadow is False


class TestShadowModeDoesNotBlock:
    def test_shadow_mode_does_not_block(self) -> None:
        from sop._policy_engine import evaluate_policy

        rules = [_make_block_rule(shadow=True)]
        action = _gate_a_action()
        result = evaluate_policy(action, rules)

        assert result.decision == "SHADOW_BLOCK"
        assert result.shadow is True
        assert result.rule_id == "test-block-gate-a"


class TestPolicyViolationAppearsInAuditLog:
    def test_policy_violation_appears_in_audit_log(self, tmp_path: Path) -> None:
        rule_file = tmp_path / "test_policy_rules.json"
        rule_file.write_text(
            json.dumps({
                "schema_version": "1.0",
                "rules": [_make_block_rule(shadow=True)],
            }),
            encoding="utf-8",
        )

        args = _minimal_args(tmp_path)
        args.policy_shadow_mode = True
        args.policy_rule_file = rule_file

        _run_cycle_for_test(args)

        context_dir = args.repo_root.resolve() / "docs" / "context"
        audit_path = context_dir / "audit_log.ndjson"
        assert audit_path.exists()

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
        assert len(shadow_block_entries) >= 1


class TestPolicyValidateCliValidRules:
    def test_policy_validate_cli_valid_rules(self) -> None:
        from sop.__main__ import build_parser, cmd_policy_validate

        assert DEFAULT_RULE_FILE.exists()
        parser = build_parser()
        args = parser.parse_args(["policy", "validate", "--rule-file", str(DEFAULT_RULE_FILE)])
        exit_code = cmd_policy_validate(args)
        assert exit_code == 0


def test_rbac_role_scoped_block_matches_role() -> None:
    from sop._policy_engine import evaluate_policy

    rules = [{
        "rule_id": "rbac-admin-block",
        "decision": "BLOCK",
        "scope": "gate",
        "match": {"field": "actor", "operator": "eq", "value": "gate_a"},
        "roles": ["admin"],
    }]
    action = {
        "gate": "exec_memory->advisory",
        "decision": "PROCEED",
        "trace_id": "rbac-match-001",
        "scope": "gate",
        "permissions": ["policy.evaluate.gate_a"],
        "tenant_id": "tenant-alpha",
        "actor": "gate_a",
        "role_id": "admin",
    }

    result = evaluate_policy(action, rules)
    assert result.decision == "BLOCK"
    assert result.rule_id == "rbac-admin-block"


def test_rbac_role_scoped_block() -> None:
    from sop._policy_engine import evaluate_policy

    rules = [{
        "rule_id": "rbac-admin-block",
        "decision": "BLOCK",
        "scope": "gate",
        "match": {"field": "actor", "operator": "eq", "value": "gate_a"},
        "roles": ["admin"],
    }]
    action = {
        "gate": "exec_memory->advisory",
        "decision": "PROCEED",
        "trace_id": "rbac-nomatch-001",
        "scope": "gate",
        "permissions": ["policy.evaluate.gate_a"],
        "tenant_id": "tenant-alpha",
        "actor": "gate_a",
        "role_id": "engineer",
    }

    result = evaluate_policy(action, rules)
    assert result.decision == "ALLOW"
    assert result.rule_id == "default"


def test_rbac_no_role_defaults_to_global() -> None:
    from sop._policy_engine import evaluate_policy

    rules = [{
        "rule_id": "global-block-gate-a",
        "decision": "BLOCK",
        "scope": "gate",
        "match": {"field": "actor", "operator": "eq", "value": "gate_a"},
    }]
    action = _gate_a_action(trace_id="rbac-global-001")

    result = evaluate_policy(action, rules)
    assert result.decision == "BLOCK"
    assert result.rule_id == "global-block-gate-a"


def test_rbac_missing_role_id_blocks() -> None:
    from sop._policy_engine import evaluate_policy

    rules = [{
        "rule_id": "rbac-admin-block",
        "decision": "BLOCK",
        "scope": "gate",
        "match": {"field": "actor", "operator": "eq", "value": "gate_a"},
        "roles": ["admin"],
    }]
    action = _gate_a_action(trace_id="rbac-missing-role-001")

    result = evaluate_policy(action, rules)
    assert result.decision == "BLOCK"
    assert "role context" in result.reason


def test_permission_enforcement_blocks_missing_permission() -> None:
    from sop._policy_engine import evaluate_policy

    rules = [{
        "rule_id": "perm-gate-a",
        "decision": "BLOCK",
        "scope": "gate",
        "permissions": ["policy.evaluate.gate_a"],
        "match": {"field": "actor", "operator": "eq", "value": "gate_a"},
    }]
    action = _gate_a_action(trace_id="perm-missing-001")
    action["permissions"] = ["policy.view"]

    result = evaluate_policy(action, rules)
    assert result.decision == "BLOCK"
    assert "requires permissions" in result.reason


def test_scope_enforcement_blocks_missing_scope_context() -> None:
    from sop._policy_engine import evaluate_policy

    rules = [_make_block_rule(shadow=False)]
    action = _gate_a_action(trace_id="scope-missing-001")
    del action["scope"]

    result = evaluate_policy(action, rules)
    assert result.decision == "BLOCK"
    assert "scope context" in result.reason


def test_tenant_boundary_blocks_cross_tenant() -> None:
    from sop._policy_engine import evaluate_policy

    rules = [{
        "rule_id": "tenant-gate-a",
        "decision": "BLOCK",
        "scope": "gate",
        "tenant_id": "tenant-alpha",
        "match": {"field": "actor", "operator": "eq", "value": "gate_a"},
    }]
    action = _gate_a_action(trace_id="tenant-cross-001")
    action["tenant_id"] = "tenant-beta"

    result = evaluate_policy(action, rules)
    assert result.decision == "BLOCK"
    assert "tenant boundary violation" in result.reason


def test_policy_rbac_validate_cli(tmp_path: Path) -> None:
    from sop.__main__ import build_parser, cmd_policy_rbac_validate

    role_file = tmp_path / "roles.json"
    role_file.write_text(
        json.dumps({
            "schema_version": "1.0",
            "roles": [{
                "role_id": "admin",
                "permissions": ["policy.validate"],
                "scope": "global",
            }],
        }),
        encoding="utf-8",
    )

    parser = build_parser()
    args = parser.parse_args(["policy", "rbac", "validate", "--role-file", str(role_file)])
    exit_code = cmd_policy_rbac_validate(args)
    assert exit_code == 0


def test_rbac_validate_rejects_duplicate_role_id(tmp_path: Path) -> None:
    from sop._policy_engine import PolicyLoadError, load_role_config

    role_file = tmp_path / "roles-duplicate.json"
    role_file.write_text(
        json.dumps({
            "schema_version": "1.0",
            "roles": [
                {"role_id": "admin", "permissions": [], "scope": "global"},
                {"role_id": "admin", "permissions": ["x"], "scope": "global"},
            ],
        }),
        encoding="utf-8",
    )

    with pytest.raises(PolicyLoadError, match="Duplicate role_id"):
        load_role_config(role_file)
