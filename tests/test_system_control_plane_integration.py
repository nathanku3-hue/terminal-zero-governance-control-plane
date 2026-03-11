from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "scripts"
ACTUAL_SCRIPTS = (
    "startup_codex_helper.py",
    "loop_cycle_artifacts.py",
    "run_loop_cycle.py",
    "validate_loop_closure.py",
    "run_fast_checks.py",
    "print_takeover_entrypoint.py",
)
OPTIONAL_SIBLING_SCRIPTS = (
    "print_takeover_workflow_overlay_models.py",
)
REQUIRED_STARTUP_PATHS = (
    "docs/loop_operating_contract.md",
    "docs/round_contract_template.md",
    "docs/expert_invocation_policy.md",
    "docs/decision_authority_matrix.md",
    "docs/disagreement_taxonomy.md",
    "docs/disagreement_runbook.md",
    "docs/rollback_protocol.md",
    "docs/phase24c_transition_playbook.md",
    "docs/w11_comms_protocol.md",
    "docs/context/current_context.json",
    "docs/context/auditor_promotion_dossier.json",
    "docs/context/ceo_go_signal.md",
)
ROOT_CONVENIENCE_MIRRORS = (
    (
        "docs/context/next_round_handoff_latest.md",
        "NEXT_ROUND_HANDOFF_LATEST.md",
        "# Next Round Handoff",
        "ROUND: next",
    ),
    (
        "docs/context/expert_request_latest.md",
        "EXPERT_REQUEST_LATEST.md",
        "# Expert Request",
        "=== EXPERT REQUEST ===",
    ),
    (
        "docs/context/pm_ceo_research_brief_latest.md",
        "PM_CEO_RESEARCH_BRIEF_LATEST.md",
        "# PM/CEO Research Brief",
        "=== PM/CEO RESEARCH BRIEF ===",
    ),
    (
        "docs/context/board_decision_brief_latest.md",
        "BOARD_DECISION_BRIEF_LATEST.md",
        "# Board Decision Brief",
        "=== BOARD DECISION BRIEF ===",
    ),
)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload, indent=2))


def _touch_startup_docs(repo_root: Path) -> None:
    for rel in REQUIRED_STARTUP_PATHS:
        path = repo_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text("{}\n", encoding="utf-8")
        else:
            path.write_text("ok\n", encoding="utf-8")


def _copy_actual_scripts(repo_root: Path) -> None:
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for script_name in ACTUAL_SCRIPTS:
        shutil.copy2(SCRIPT_ROOT / script_name, scripts_dir / script_name)
    for script_name in OPTIONAL_SIBLING_SCRIPTS:
        source = SCRIPT_ROOT / script_name
        if source.exists():
            shutil.copy2(source, scripts_dir / script_name)


def _write_exit_zero_stub(path: Path) -> None:
    _write_text(
        path,
        "from __future__ import annotations\n"
        "import argparse\n"
        "parser = argparse.ArgumentParser(add_help=False)\n"
        "parser.parse_known_args()\n"
        "raise SystemExit(0)\n",
    )


def _write_auditor_report_stub(path: Path) -> None:
    _write_text(
        path,
        "from __future__ import annotations\n"
        "import argparse\n"
        "import json\n"
        "from pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--output-json', required=True)\n"
        "parser.add_argument('--output-md', required=True)\n"
        "parser.add_argument('--mode', required=True)\n"
        "parser.add_argument('--logs-dir')\n"
        "parser.add_argument('--repo-id')\n"
        "parser.add_argument('--ledger')\n"
        "args = parser.parse_args()\n"
        "output_json = Path(args.output_json)\n"
        "output_md = Path(args.output_md)\n"
        "output_json.parent.mkdir(parents=True, exist_ok=True)\n"
        "output_md.parent.mkdir(parents=True, exist_ok=True)\n"
        "if args.mode == 'weekly':\n"
        "    payload = {\n"
        "        'schema_version': '1.0.0',\n"
        "        'report_type': 'weekly',\n"
        "        'totals': {'items_reviewed': 54, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0},\n"
        "    }\n"
        "else:\n"
        "    payload = {\n"
        "        'schema_version': '1.0.0',\n"
        "        'report_type': 'dossier',\n"
        "        'fp_analysis': {'ch_unannotated': 0},\n"
        "        'promotion_criteria': {\n"
        "            'c0_infra_health': {'met': True, 'value': '0 failures'},\n"
        "            'c1_24b_close': {'met': True, 'value': 'APPROVED'},\n"
        "            'c2_min_items': {'met': True, 'value': '54 >= 30'},\n"
        "            'c3_min_weeks': {'met': True, 'value': '2 consecutive weeks >= 2'},\n"
        "            'c4_fp_rate': {'met': True, 'value': '0.00%'},\n"
        "            'c4b_annotation_coverage': {'met': True, 'value': '100.00%'},\n"
        "            'c5_all_v2': {'met': True, 'value': '1 versions: [\\'2.0.0\\']'},\n"
        "        },\n"
        "    }\n"
        "output_json.write_text(json.dumps(payload, indent=2) + '\\n', encoding='utf-8')\n"
        "output_md.write_text('# stub auditor report\\n', encoding='utf-8')\n",
    )


def _write_go_signal_stub(path: Path) -> None:
    _write_text(
        path,
        "from __future__ import annotations\n"
        "import argparse\n"
        "from pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--calibration-json', required=True)\n"
        "parser.add_argument('--dossier-json', required=True)\n"
        "parser.add_argument('--output', required=True)\n"
        "args = parser.parse_args()\n"
        "output = Path(args.output)\n"
        "output.parent.mkdir(parents=True, exist_ok=True)\n"
        "output.write_text('''# CEO GO Signal\n\n- Recommended Action: GO\n\n## Next Steps\n\n1. Proceed to escalation.\n''', encoding='utf-8')\n",
    )


def _write_weekly_summary_stub(path: Path) -> None:
    _write_text(
        path,
        "from __future__ import annotations\n"
        "import argparse\n"
        "from pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--dossier-json', required=True)\n"
        "parser.add_argument('--calibration-json', required=True)\n"
        "parser.add_argument('--go-signal-md', required=True)\n"
        "parser.add_argument('--output', required=True)\n"
        "args = parser.parse_args()\n"
        "output = Path(args.output)\n"
        "output.parent.mkdir(parents=True, exist_ok=True)\n"
        "output.write_text('# CEO Weekly Summary\\n', encoding='utf-8')\n",
    )


def _write_compaction_stub(path: Path) -> None:
    _write_text(
        path,
        "from __future__ import annotations\n"
        "import argparse\n"
        "import json\n"
        "from pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--state-json', required=True)\n"
        "parser.add_argument('--output-json', required=True)\n"
        "parser.add_argument('--memory-json')\n"
        "parser.add_argument('--dossier-json')\n"
        "parser.add_argument('--go-signal-md')\n"
        "parser.add_argument('--pm-warn')\n"
        "parser.add_argument('--ceo-warn')\n"
        "parser.add_argument('--force')\n"
        "parser.add_argument('--max-age-hours')\n"
        "args = parser.parse_args()\n"
        "state_path = Path(args.state_json)\n"
        "output_path = Path(args.output_json)\n"
        "state_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "output_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "state_path.write_text(json.dumps({'state': 'ok'}, indent=2) + '\\n', encoding='utf-8')\n"
        "output_path.write_text(json.dumps({'status': 'ok'}, indent=2) + '\\n', encoding='utf-8')\n",
    )


def _write_memory_packet_stub(path: Path) -> None:
    _write_text(
        path,
        "from __future__ import annotations\n"
        "import argparse\n"
        "import json\n"
        "from pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--loop-summary-json')\n"
        "parser.add_argument('--output-json', required=True)\n"
        "parser.add_argument('--output-md', required=True)\n"
        "parser.add_argument('--status-json', required=True)\n"
        "parser.add_argument('--allow-degraded-output', action='store_true')\n"
        "parser.add_argument('--pm-budget-tokens')\n"
        "parser.add_argument('--ceo-budget-tokens')\n"
        "args = parser.parse_args()\n"
        "json_path = Path(args.output_json)\n"
        "md_path = Path(args.output_md)\n"
        "status_path = Path(args.status_json)\n"
        "json_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "md_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "status_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "payload = {\n"
        "    'schema_version': '1.0.0',\n"
        "    'generated_at_utc': '2026-03-07T00:00:00Z',\n"
        "    'token_budget': {\n"
        "        'pm_budget': 3000, 'ceo_budget': 1800, 'pm_actual': 100, 'ceo_actual': 80,\n"
        "        'pm_budget_ok': True, 'ceo_budget_ok': True,\n"
        "    },\n"
        "    'hierarchical_summary': {\n"
        "        'working_summary': 'ok', 'issue_summary': 'ok', 'daily_pm_summary': 'ok', 'weekly_ceo_summary': 'ok', 'replan_summary': 'ok'\n"
        "    },\n"
        "    'replanning': {'blocking_gaps': [], 'blocking_gap_count': 0, 'next_replan_recommendation': 'Proceed.'},\n"
        "    'next_round_handoff': {\n"
        "        'status': 'CLEAR',\n"
        "        'human_brief': 'Continue the current execution slice with the latest artifact evidence.',\n"
        "        'machine_view': 'SURFACE: next_round_handoff\\nSTATUS: CLEAR\\nRECOMMENDED_INTENT: Continue current execution slice',\n"
        "        'paste_ready_block': 'ROUND: next\\nORIGINAL_INTENT: Continue current execution slice'\n"
        "    },\n"
        "    'expert_request': {\n"
        "        'status': 'ADVISORY',\n"
        "        'target_expert': 'qa',\n"
        "        'trigger_reason': 'low_confidence',\n"
        "        'question': 'Validate the remaining ambiguous edge cases before escalation.',\n"
        "        'requested_domain': 'qa',\n"
        "        'roster_fit': 'APPROVED_MANDATORY',\n"
        "        'milestone_id': 'milestone-1',\n"
        "        'board_reentry_required': 'false',\n"
        "        'board_reentry_reason_codes': ['none'],\n"
        "        'expert_memory_status': 'FRESH',\n"
        "        'board_memory_status': 'FRESH',\n"
        "        'memory_reason_codes': ['none'],\n"
        "        'human_brief': 'Ask QA to validate the remaining ambiguous edge cases before escalation.',\n"
        "        'machine_view': 'SURFACE: expert_request\\nSTATUS: ADVISORY\\nTARGET_EXPERT: qa\\nREQUESTED_DOMAIN: qa\\nROSTER_FIT: APPROVED_MANDATORY\\nMILESTONE_ID: milestone-1\\nBOARD_REENTRY_REQUIRED: false\\nEXPERT_MEMORY_STATUS: FRESH\\nBOARD_MEMORY_STATUS: FRESH\\nQUESTION: Validate the remaining ambiguous edge cases before escalation.',\n"
        "        'decision_depends_on': 'go_signal_action_gate',\n"
        "        'source_artifacts': ['docs/context/ceo_go_signal.md'],\n"
        "        'paste_ready_block': '=== EXPERT REQUEST ===\\nTargetExpert: qa\\nQuestion: Validate the remaining ambiguous edge cases before escalation.\\n====================',\n"
        "    },\n"
        "    'pm_ceo_research_brief': {\n"
        "        'status': 'ADVISORY',\n"
        "        'delegated_to': 'principal',\n"
        "        'question': 'What is the top tradeoff to resolve before promotion?',\n"
        "        'human_brief': 'Delegate the top pre-promotion tradeoff to principal review.',\n"
        "        'machine_view': 'SURFACE: pm_ceo_research_brief\\nSTATUS: ADVISORY\\nDELEGATED_TO: principal\\nQUESTION: What is the top tradeoff to resolve before promotion?',\n"
        "        'required_tradeoff_dimensions': ['impact', 'risk', 'effort', 'maintainability'],\n"
        "        'evidence_required': ['docs/context/ceo_go_signal.md'],\n"
        "        'decision_depends_on': 'go_signal_action_gate',\n"
        "        'source_artifacts': ['docs/context/ceo_go_signal.md'],\n"
        "        'paste_ready_block': '=== PM/CEO RESEARCH BRIEF ===\\nDelegatedTo: principal\\nQuestion: What is the top tradeoff to resolve before promotion?\\n==============================',\n"
        "    },\n"
        "    'board_decision_brief': {\n"
        "        'status': 'ADVISORY',\n"
        "        'decision_topic': 'Promotion readiness recommendation',\n"
        "        'decision_class': 'TWO_WAY',\n"
        "        'risk_tier': 'LOW',\n"
        "        'recommended_option': 'Hold promotion until expert ambiguity is cleared.',\n"
        "        'lineup_decision_needed': 'false',\n"
        "        'lineup_gap_domains': ['none'],\n"
        "        'approved_roster_snapshot': {'mandatory': ['principal', 'qa'], 'optional': ['riskops']},\n"
        "        'reintroduce_board_when': 'when milestone scope changes',\n"
        "        'board_reentry_required': 'false',\n"
        "        'board_reentry_reason_codes': ['none'],\n"
        "        'expert_memory_status': 'FRESH',\n"
        "        'board_memory_status': 'FRESH',\n"
        "        'memory_reason_codes': ['none'],\n"
        "        'human_brief': 'Hold promotion until the expert ambiguity is cleared without widening the control-plane scope.',\n"
        "        'machine_view': 'SURFACE: board_decision_brief\\nSTATUS: ADVISORY\\nDECISION_TOPIC: Promotion readiness recommendation\\nLINEUP_DECISION_NEEDED: false\\nLINEUP_GAP_DOMAINS: none\\nAPPROVED_ROSTER_SNAPSHOT: mandatory=principal,qa; optional=riskops\\nREINTRODUCE_BOARD_WHEN: when milestone scope changes\\nBOARD_REENTRY_REQUIRED: false\\nEXPERT_MEMORY_STATUS: FRESH\\nBOARD_MEMORY_STATUS: FRESH\\nRECOMMENDED_OPTION: Hold promotion until expert ambiguity is cleared.',\n"
        "        'source_artifacts': ['docs/context/ceo_go_signal.md', 'docs/context/expert_request_latest.md'],\n"
        "        'ceo_lens': {'business_upside': 'Protect escalation quality.'},\n"
        "        'cto_lens': {'architecture_coherence': 'Avoid promoting with unresolved ambiguity.'},\n"
        "        'coo_lens': {'execution_load': 'Keep additional coordination bounded to one expert pass.'},\n"
        "        'expert_lens': {'target_expert': 'qa', 'specialist_question': 'Resolve ambiguity before escalation.'},\n"
        "        'paste_ready_block': '=== BOARD DECISION BRIEF ===\\nCEO: hold until ambiguity is cleared\\nCTO: preserve interface and promotion discipline\\nCOO: keep follow-up to one expert pass\\n============================',\n"
        "    },\n"
        "    'retrieval_namespaces': {'governance': [], 'operations': [], 'risk': [], 'roadmap': []},\n"
        "    'source_bindings': [],\n"
        "    'semantic_claims': [],\n"
        "}\n"
        "json_path.write_text(json.dumps(payload, indent=2) + '\\n', encoding='utf-8')\n"
        "md_path.write_text('# Exec Memory Packet\\n', encoding='utf-8')\n"
        "status_path.write_text(json.dumps({'schema_version': '1.0.0', 'generated_at_utc': '2026-03-07T00:00:00Z', 'authoritative_latest_written': True, 'reason': 'authoritative_written'}, indent=2) + '\\n', encoding='utf-8')\n",
    )


def _write_supporting_stubs(repo_root: Path) -> None:
    scripts_dir = repo_root / "scripts"
    _write_auditor_report_stub(scripts_dir / "auditor_calibration_report.py")
    _write_go_signal_stub(scripts_dir / "generate_ceo_go_signal.py")
    _write_weekly_summary_stub(scripts_dir / "generate_ceo_weekly_summary.py")
    _write_compaction_stub(scripts_dir / "evaluate_context_compaction_trigger.py")
    _write_memory_packet_stub(scripts_dir / "build_exec_memory_packet.py")

    for script_name in (
        "validate_ceo_go_signal_truth.py",
        "validate_ceo_weekly_summary_truth.py",
        "validate_exec_memory_truth.py",
        "validate_round_contract_checks.py",
        "validate_counterexample_gate.py",
        "validate_dual_judge_gate.py",
        "validate_refactor_mock_policy.py",
        "validate_parallel_fanin.py",
    ):
        _write_exit_zero_stub(scripts_dir / script_name)


def _write_round_contract_latest(repo_root: Path) -> None:
    _write_text(
        repo_root / "docs/context/round_contract_latest.md",
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DONE_WHEN_CHECKS: go_signal_action_gate,startup_gate_status,tdd_contract_gate",
                "- TDD_MODE: NOT_APPLICABLE",
                "- TDD_NOT_APPLICABLE_REASON: Integration test exercises composition only.",
                "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
                "- COUNTEREXAMPLE_TEST_RESULT: N/A",
                "- REFACTOR_BUDGET_MINUTES: 0",
                "- REFACTOR_SPEND_MINUTES: 0",
                "- REFACTOR_BUDGET_EXCEEDED_REASON: N/A",
                "- MOCK_POLICY_MODE: NOT_APPLICABLE",
                "- MOCKED_DEPENDENCIES: N/A",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
                "- DECISION_CLASS: TWO_WAY",
                "- RISK_TIER: LOW",
                "- DUAL_JUDGE_REQUIRED: NO",
                "- DUAL_JUDGE_AUDITOR_1_VERDICT: N/A",
                "- DUAL_JUDGE_AUDITOR_2_VERDICT: N/A",
                "",
            ]
        ),
    )


def _run_script(script_path: Path, repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_control_plane_scripts_compose_end_to_end(tmp_path: Path) -> None:
    repo_root = tmp_path
    _touch_startup_docs(repo_root)
    _copy_actual_scripts(repo_root)
    _write_supporting_stubs(repo_root)

    startup_result = _run_script(
        repo_root / "scripts" / "startup_codex_helper.py",
        repo_root,
        "--no-interactive",
        "--original-intent",
        "Exercise startup to fast-check control-plane composition.",
        "--deliverable-this-scope",
        "One green control-plane pass with deterministic temp artifacts.",
        "--non-goals",
        "No phase-end handover or cross-repo promotion work.",
        "--done-when",
        "Startup, loop cycle, closure, and fast checks all complete successfully.",
        "--positioning-lock",
        "Keep the integration slice deterministic and artifact-bound.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--risk-tier",
        "LOW",
        "--done-when-checks",
        "startup_gate_status,go_signal_action_gate,tdd_contract_gate",
        "--refactor-budget-minutes",
        "0",
        "--refactor-spend-minutes",
        "0",
        "--refactor-budget-exceeded-reason",
        "N/A",
        "--counterexample-test-command",
        "N/A",
        "--counterexample-test-result",
        "N/A",
        "--mock-policy-mode",
        "NOT_APPLICABLE",
        "--mocked-dependencies",
        "N/A",
        "--integration-coverage-for-mocks",
        "N/A",
        "--owned-files",
        "scripts/startup_codex_helper.py,scripts/run_loop_cycle.py",
        "--interface-inputs",
        "docs/loop_operating_contract.md,docs/round_contract_template.md",
        "--interface-outputs",
        "docs/context/startup_intake_latest.json,docs/context/init_execution_card_latest.md,docs/context/round_contract_seed_latest.md",
        "--intuition-gate",
        "MACHINE_DEFAULT",
        "--intuition-gate-rationale",
        "This is a deterministic integration test fixture.",
    )
    assert startup_result.returncode == 0, startup_result.stdout + startup_result.stderr
    assert (repo_root / "docs/context/startup_intake_latest.json").exists()
    assert (repo_root / "docs/context/init_execution_card_latest.md").exists()

    _write_round_contract_latest(repo_root)

    cycle_result = _run_script(
        repo_root / "scripts" / "run_loop_cycle.py",
        repo_root,
        "--skip-phase-end",
        "--allow-hold",
        "true",
    )
    assert cycle_result.returncode == 0, cycle_result.stdout + cycle_result.stderr

    loop_payload = json.loads(
        (repo_root / "docs/context/loop_cycle_summary_latest.json").read_text(encoding="utf-8")
    )
    assert loop_payload["final_result"] == "PASS"
    assert (repo_root / "docs/context/expert_request_latest.json").exists()
    assert (repo_root / "docs/context/expert_request_latest.md").exists()
    assert (repo_root / "docs/context/pm_ceo_research_brief_latest.json").exists()
    assert (repo_root / "docs/context/pm_ceo_research_brief_latest.md").exists()
    assert (repo_root / "docs/context/board_decision_brief_latest.json").exists()
    assert (repo_root / "docs/context/board_decision_brief_latest.md").exists()

    for source_rel, mirror_name, expected_heading, expected_paste_token in ROOT_CONVENIENCE_MIRRORS:
        source_path = repo_root / source_rel
        mirror_path = repo_root / mirror_name
        assert source_path.exists(), source_rel
        assert mirror_path.exists(), mirror_name
        assert mirror_path.parent == repo_root
        mirror_text = mirror_path.read_text(encoding="utf-8")
        source_text = source_path.read_text(encoding="utf-8")
        assert mirror_text == source_text
        assert expected_heading in mirror_text
        assert "## Human Brief" in mirror_text
        assert "## Machine View" in mirror_text
        assert "## Paste-Ready Block" in mirror_text
        assert expected_paste_token in mirror_text

    expert_request_payload = json.loads(
        (repo_root / "docs/context/expert_request_latest.json").read_text(encoding="utf-8")
    )
    assert expert_request_payload["expert_request"]["target_expert"] == "qa"

    research_brief_payload = json.loads(
        (repo_root / "docs/context/pm_ceo_research_brief_latest.json").read_text(encoding="utf-8")
    )
    assert research_brief_payload["pm_ceo_research_brief"]["delegated_to"] == "principal"

    board_brief_payload = json.loads(
        (repo_root / "docs/context/board_decision_brief_latest.json").read_text(encoding="utf-8")
    )
    assert board_brief_payload["board_decision_brief"]["recommended_option"] == (
        "Hold promotion until expert ambiguity is cleared."
    )

    expert_request_markdown = (repo_root / "docs/context/expert_request_latest.md").read_text(
        encoding="utf-8"
    )
    assert "## Lineup" in expert_request_markdown
    assert "RequestedDomain: qa" in expert_request_markdown
    assert "## Memory" in expert_request_markdown
    assert "ExpertMemoryStatus: FRESH" in expert_request_markdown

    board_decision_markdown = (repo_root / "docs/context/board_decision_brief_latest.md").read_text(
        encoding="utf-8"
    )
    assert "## Lineup" in board_decision_markdown
    assert "LineupDecisionNeeded: false" in board_decision_markdown
    assert "## Memory" in board_decision_markdown
    assert "BoardMemoryStatus: FRESH" in board_decision_markdown

    closure_result = _run_script(
        repo_root / "scripts" / "validate_loop_closure.py",
        repo_root,
    )
    assert closure_result.returncode == 0, closure_result.stdout + closure_result.stderr

    closure_payload = json.loads(
        (repo_root / "docs/context/loop_closure_status_latest.json").read_text(encoding="utf-8")
    )
    assert closure_payload["result"] == "READY_TO_ESCALATE"

    fast_checks_json = repo_root / "docs/context/fast_checks_status_latest.json"
    fast_checks_result = _run_script(
        repo_root / "scripts" / "run_fast_checks.py",
        repo_root,
        "--json-out",
        str(fast_checks_json),
    )
    assert fast_checks_result.returncode == 0, fast_checks_result.stdout + fast_checks_result.stderr
    assert "overall_status: PASS" in fast_checks_result.stdout

    fast_payload = json.loads(fast_checks_json.read_text(encoding="utf-8"))
    assert fast_payload["overall_status"] == "PASS"
    assert fast_payload["hold_detected"] is False
    assert all(item["status"] == "PASS" for item in fast_payload["checks"])

    takeover_result = _run_script(
        repo_root / "scripts" / "print_takeover_entrypoint.py",
        repo_root,
    )
    assert takeover_result.returncode == 0, takeover_result.stdout + takeover_result.stderr
    assert "closure_result: READY_TO_ESCALATE" in takeover_result.stdout
    assert "expert_request_latest.md" in takeover_result.stdout
    assert "pm_ceo_research_brief_latest.md" in takeover_result.stdout
    assert "board_decision_brief_latest.md" in takeover_result.stdout
    assert "advisory_expert_request_requested_domain: qa" in takeover_result.stdout
    assert "advisory_expert_request_roster_fit: APPROVED_MANDATORY" in takeover_result.stdout
    assert "advisory_expert_request_milestone_id: milestone-1" in takeover_result.stdout
    assert "advisory_expert_request_expert_memory_status: FRESH" in takeover_result.stdout
    assert "advisory_board_decision_brief: present" in takeover_result.stdout
    assert "advisory_board_decision_brief_lineup_decision_needed: false" in takeover_result.stdout
    assert "advisory_board_decision_brief_reintroduce_board_when: when milestone scope changes" in takeover_result.stdout
    assert "advisory_board_decision_brief_board_memory_status: FRESH" in takeover_result.stdout
    assert "advisory_board_decision_brief_begin" in takeover_result.stdout
