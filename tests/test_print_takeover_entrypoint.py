from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "print_takeover_entrypoint.py"
)

ARTIFACT_LINES = [
    "- docs/context/ceo_weekly_summary_latest.md",
    "- docs/context/ceo_go_signal.md",
    "- docs/context/exec_memory_packet_latest.json",
    "- docs/context/loop_cycle_summary_latest.json",
    "- docs/context/loop_closure_status_latest.json",
    "- docs/context/expert_request_latest.md",
    "- docs/context/pm_ceo_research_brief_latest.md",
    "- docs/context/board_decision_brief_latest.md",
]

ROOT_CONVENIENCE_LINES = [
    "- NEXT_ROUND_HANDOFF_LATEST.md",
    "- EXPERT_REQUEST_LATEST.md",
    "- PM_CEO_RESEARCH_BRIEF_LATEST.md",
    "- BOARD_DECISION_BRIEF_LATEST.md",
]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run(repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_entrypoint_ready_to_escalate_returns_zero(tmp_path: Path) -> None:
    closure_path = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"
    _write_json(
        closure_path,
        {
            "result": "READY_TO_ESCALATE",
            "checks": [{"name": "startup_gate_status", "status": "PASS"}],
        },
    )

    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "closure_result: READY_TO_ESCALATE" in result.stdout
    assert "startup_gate_status: PASS" in result.stdout


def test_entrypoint_not_ready_returns_one(tmp_path: Path) -> None:
    closure_path = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"
    _write_json(closure_path, {"result": "NOT_READY", "checks": []})

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "closure_result: NOT_READY" in result.stdout


def test_entrypoint_missing_closure_file_returns_two(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode == 2
    assert "Missing closure status file" in result.stderr


def test_entrypoint_malformed_closure_json_returns_two(tmp_path: Path) -> None:
    closure_path = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"
    closure_path.parent.mkdir(parents=True, exist_ok=True)
    closure_path.write_text("{ invalid json", encoding="utf-8")

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "ERROR:" in result.stderr


def test_entrypoint_prints_required_artifact_lines(tmp_path: Path) -> None:
    closure_path = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"
    _write_json(closure_path, {"result": "NOT_READY", "checks": []})

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    for artifact_line in ARTIFACT_LINES:
        assert artifact_line in result.stdout


def test_entrypoint_prints_root_convenience_mirror_hints(tmp_path: Path) -> None:
    closure_path = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"
    _write_json(closure_path, {"result": "NOT_READY", "checks": []})

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "root_convenience_mirrors:" in result.stdout
    for mirror_line in ROOT_CONVENIENCE_LINES:
        assert mirror_line in result.stdout
    assert result.stdout.index("root_convenience_mirrors:") < result.stdout.index("artifacts:")


def test_entrypoint_prints_advisory_next_round_handoff_when_present(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    _write_json(context_dir / "loop_closure_status_latest.json", {"result": "NOT_READY", "checks": []})
    (context_dir / "next_round_handoff_latest.md").write_text(
        "# Next Round Handoff\n\n- RecommendedIntent: close annotation gap\n- RecommendedScope: refresh dossier\n\n## Human Brief\n\nClose the annotation gap before escalation.\n\n## Paste-Ready Block\n\n```text\nHANDOFF_STATUS: ACTION_REQUIRED\n```\n",
        encoding="utf-8",
    )

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "advisory_next_round_handoff: present" in result.stdout
    assert "advisory_next_round_handoff_path: docs/context/next_round_handoff_latest.md" in result.stdout
    assert "advisory_next_round_handoff_summary: Close the annotation gap before escalation." in result.stdout
    assert "advisory_next_round_handoff_paste_ready_begin" in result.stdout
    assert "advisory_next_round_handoff_begin" in result.stdout
    assert "# Next Round Handoff" in result.stdout
    assert "RecommendedIntent: close annotation gap" in result.stdout
    assert "## Paste-Ready Block" in result.stdout
    assert "HANDOFF_STATUS: ACTION_REQUIRED" in result.stdout
    assert "advisory_next_round_handoff_paste_ready_end" in result.stdout
    assert "advisory_next_round_handoff_end" in result.stdout
    assert result.stdout.index("advisory_next_round_handoff: present") < result.stdout.index("artifacts:")


def test_entrypoint_prints_advisory_expert_artifacts_when_present(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    _write_json(context_dir / "loop_closure_status_latest.json", {"result": "NOT_READY", "checks": []})
    (context_dir / "expert_request_latest.md").write_text(
        "# Expert Request\n\n- TargetExpert: qa\n- Question: isolate confidence blocker\n\n## Machine View\n\n```text\nSURFACE: expert_request\nREQUESTED_DOMAIN: qa\nROSTER_FIT: APPROVED_MANDATORY\nMILESTONE_ID: milestone-1\nBOARD_REENTRY_REQUIRED: false\nEXPERT_MEMORY_STATUS: FRESH\nBOARD_MEMORY_STATUS: FRESH\n```\n\n## Human Brief\n\nAsk QA to isolate the confidence blocker before escalation.\n\n## Paste-Ready Block\n\n```text\nQUESTION: isolate confidence blocker\n```\n",
        encoding="utf-8",
    )
    (context_dir / "pm_ceo_research_brief_latest.md").write_text(
        "# PM/CEO Research Brief\n\n- DelegatedTo: principal\n- Tradeoff: speed vs rigor\n\n## Human Brief\n\nDelegate the speed-versus-rigor tradeoff to principal review.\n\n## Paste-Ready Block\n\n```text\nQUESTION: speed vs rigor\n```\n",
        encoding="utf-8",
    )
    (context_dir / "board_decision_brief_latest.md").write_text(
        "# Board Decision Brief\n\n- CEO: hold until evidence clears\n- CTO: protect interface stability\n- COO: keep rollout load bounded\n\n## Machine View\n\n```text\nSURFACE: board_decision_brief\nLINEUP_DECISION_NEEDED: false\nLINEUP_GAP_DOMAINS: none\nAPPROVED_ROSTER_SNAPSHOT: mandatory=principal,qa; optional=riskops\nREINTRODUCE_BOARD_WHEN: when milestone scope changes\nBOARD_REENTRY_REQUIRED: false\nEXPERT_MEMORY_STATUS: FRESH\nBOARD_MEMORY_STATUS: FRESH\n```\n\n## Human Brief\n\nHold until the evidence clears while keeping interface and rollout risk bounded.\n\n## Paste-Ready Block\n\n```text\nRECOMMENDED_OPTION: hold until evidence clears\n```\n",
        encoding="utf-8",
    )

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr

    assert "advisory_expert_request: present" in result.stdout
    assert "advisory_expert_request_path: docs/context/expert_request_latest.md" in result.stdout
    assert "advisory_expert_request_summary: Ask QA to isolate the confidence blocker before escalation." in result.stdout
    assert "advisory_expert_request_requested_domain: qa" in result.stdout
    assert "advisory_expert_request_roster_fit: APPROVED_MANDATORY" in result.stdout
    assert "advisory_expert_request_milestone_id: milestone-1" in result.stdout
    assert "advisory_expert_request_board_reentry_required: false" in result.stdout
    assert "advisory_expert_request_expert_memory_status: FRESH" in result.stdout
    assert "advisory_expert_request_board_memory_status: FRESH" in result.stdout
    assert "advisory_expert_request_paste_ready_begin" in result.stdout
    assert "advisory_expert_request_begin" in result.stdout
    assert "# Expert Request" in result.stdout
    assert "TargetExpert: qa" in result.stdout
    assert "## Paste-Ready Block" in result.stdout
    assert "QUESTION: isolate confidence blocker" in result.stdout
    assert "advisory_expert_request_paste_ready_end" in result.stdout
    assert "advisory_expert_request_end" in result.stdout

    assert "advisory_pm_ceo_research_brief: present" in result.stdout
    assert "advisory_pm_ceo_research_brief_path: docs/context/pm_ceo_research_brief_latest.md" in result.stdout
    assert "advisory_pm_ceo_research_brief_summary: Delegate the speed-versus-rigor tradeoff to principal review." in result.stdout
    assert "advisory_pm_ceo_research_brief_begin" in result.stdout
    assert "# PM/CEO Research Brief" in result.stdout
    assert "DelegatedTo: principal" in result.stdout
    assert "QUESTION: speed vs rigor" in result.stdout
    assert "advisory_pm_ceo_research_brief_end" in result.stdout

    assert "advisory_board_decision_brief: present" in result.stdout
    assert "advisory_board_decision_brief_path: docs/context/board_decision_brief_latest.md" in result.stdout
    assert "advisory_board_decision_brief_summary: Hold until the evidence clears while keeping interface and rollout risk bounded." in result.stdout
    assert "advisory_board_decision_brief_lineup_decision_needed: false" in result.stdout
    assert "advisory_board_decision_brief_lineup_gap_domains: none" in result.stdout
    assert "advisory_board_decision_brief_approved_roster_snapshot: mandatory=principal,qa; optional=riskops" in result.stdout
    assert "advisory_board_decision_brief_reintroduce_board_when: when milestone scope changes" in result.stdout
    assert "advisory_board_decision_brief_board_reentry_required: false" in result.stdout
    assert "advisory_board_decision_brief_expert_memory_status: FRESH" in result.stdout
    assert "advisory_board_decision_brief_board_memory_status: FRESH" in result.stdout
    assert "advisory_board_decision_brief_begin" in result.stdout
    assert "# Board Decision Brief" in result.stdout
    assert "CTO: protect interface stability" in result.stdout
    assert "RECOMMENDED_OPTION: hold until evidence clears" in result.stdout
    assert "advisory_board_decision_brief_end" in result.stdout

    assert result.stdout.index("advisory_expert_request: present") < result.stdout.index("artifacts:")
    assert result.stdout.index("advisory_pm_ceo_research_brief: present") < result.stdout.index("artifacts:")
    assert result.stdout.index("advisory_board_decision_brief: present") < result.stdout.index("artifacts:")


def test_entrypoint_extracts_lineup_memory_markers_without_machine_view(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    _write_json(context_dir / "loop_closure_status_latest.json", {"result": "NOT_READY", "checks": []})
    (context_dir / "expert_request_latest.md").write_text(
        "# Expert Request\n\n"
        "- TargetExpert: qa\n\n"
        "## Lineup\n\n"
        "- RequestedDomain: qa\n"
        "- RosterFit: APPROVED_MANDATORY\n"
        "- MilestoneId: milestone-2\n"
        "- BoardReentryRequired: true\n"
        "- BoardReentryReasonCodes: scope_change\n\n"
        "## Memory\n\n"
        "- ExpertMemoryStatus: STALE\n"
        "- BoardMemoryStatus: STALE\n"
        "- MemoryReasonCodes: context_shift\n\n"
        "## Human Brief\n\n"
        "Ask QA to resolve ambiguity before escalation.\n\n",
        encoding="utf-8",
    )
    (context_dir / "board_decision_brief_latest.md").write_text(
        "# Board Decision Brief\n\n"
        "- DecisionTopic: milestone lineup review\n\n"
        "## Lineup\n\n"
        "- LineupDecisionNeeded: true\n"
        "- LineupGapDomains: quant_research\n"
        "- ApprovedRosterSnapshot: mandatory=principal,qa\n"
        "- ReintroduceBoardWhen: when scope shifts\n"
        "- BoardReentryRequired: true\n"
        "- BoardReentryReasonCodes: lineup_change\n\n"
        "## Memory\n\n"
        "- ExpertMemoryStatus: STALE\n"
        "- BoardMemoryStatus: STALE\n"
        "- MemoryReasonCodes: context_shift\n\n"
        "## Human Brief\n\n"
        "Re-open board review when lineup and memory are stale.\n\n",
        encoding="utf-8",
    )

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr

    assert "advisory_expert_request_requested_domain: qa" in result.stdout
    assert "advisory_expert_request_roster_fit: APPROVED_MANDATORY" in result.stdout
    assert "advisory_expert_request_milestone_id: milestone-2" in result.stdout
    assert "advisory_expert_request_board_reentry_required: true" in result.stdout
    assert "advisory_expert_request_board_reentry_reason_codes: scope_change" in result.stdout
    assert "advisory_expert_request_expert_memory_status: STALE" in result.stdout
    assert "advisory_expert_request_board_memory_status: STALE" in result.stdout
    assert "advisory_expert_request_memory_reason_codes: context_shift" in result.stdout

    assert "advisory_board_decision_brief_lineup_decision_needed: true" in result.stdout
    assert "advisory_board_decision_brief_lineup_gap_domains: quant_research" in result.stdout
    assert "advisory_board_decision_brief_approved_roster_snapshot: mandatory=principal,qa" in result.stdout
    assert "advisory_board_decision_brief_reintroduce_board_when: when scope shifts" in result.stdout
    assert "advisory_board_decision_brief_board_reentry_required: true" in result.stdout
    assert "advisory_board_decision_brief_board_reentry_reason_codes: lineup_change" in result.stdout
    assert "advisory_board_decision_brief_expert_memory_status: STALE" in result.stdout
    assert "advisory_board_decision_brief_board_memory_status: STALE" in result.stdout
    assert "advisory_board_decision_brief_memory_reason_codes: context_shift" in result.stdout


def test_entrypoint_warns_and_continues_when_advisory_expert_artifacts_are_unreadable(
    tmp_path: Path,
) -> None:
    context_dir = tmp_path / "docs" / "context"
    _write_json(context_dir / "loop_closure_status_latest.json", {"result": "NOT_READY", "checks": []})
    (context_dir / "expert_request_latest.md").mkdir(parents=True)
    (context_dir / "pm_ceo_research_brief_latest.md").mkdir(parents=True)
    (context_dir / "board_decision_brief_latest.md").mkdir(parents=True)

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "WARNING: Unable to read docs/context/expert_request_latest.md" in result.stderr
    assert "WARNING: Unable to read docs/context/pm_ceo_research_brief_latest.md" in result.stderr
    assert "WARNING: Unable to read docs/context/board_decision_brief_latest.md" in result.stderr
    assert "advisory_expert_request: present" not in result.stdout
    assert "advisory_pm_ceo_research_brief: present" not in result.stdout
    assert "advisory_board_decision_brief: present" not in result.stdout
    for artifact_line in ARTIFACT_LINES:
        assert artifact_line in result.stdout


# ============================================================================
# Workflow Status Overlay Tests
# ============================================================================


def _run_with_workflow_status(repo_root: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    """Run script with workflow status JSON output flag."""
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--workflow-status-json-out",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _create_workflow_status_fixtures(tmp_path: Path) -> dict[str, Path]:
    """Create minimal test fixtures for workflow status overlay."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    # startup_intake_latest.json
    startup_intake = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "startup_gate": {"status": "READY_TO_EXECUTE"},
    }
    _write_json(context_dir / "startup_intake_latest.json", startup_intake)

    # loop_closure_status_latest.json
    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "NOT_READY",
        "checks": [
            {"name": "go_signal_action_gate", "status": "FAIL", "message": "Action is HOLD"}
        ],
    }
    _write_json(context_dir / "loop_closure_status_latest.json", closure_status)

    # loop_cycle_summary_latest.json
    cycle_summary = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "final_result": "HOLD",
    }
    _write_json(context_dir / "loop_cycle_summary_latest.json", cycle_summary)

    # exec_memory_packet_latest.json
    memory_packet = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
    }
    _write_json(context_dir / "exec_memory_packet_latest.json", memory_packet)

    # next_round_handoff_latest.md
    (context_dir / "next_round_handoff_latest.md").write_text(
        "# Next Round Handoff\n\nHandoff content here.\n",
        encoding="utf-8",
    )

    # round_contract_latest.md
    (context_dir / "round_contract_latest.md").write_text(
        "# Round Contract\n\nContract content here.\n",
        encoding="utf-8",
    )

    # README.md at repo root
    (tmp_path / "README.md").write_text("# Project README\n", encoding="utf-8")

    return {
        "repo_root": tmp_path,
        "context_dir": context_dir,
    }


def test_no_workflow_status_flag_unchanged_behavior(tmp_path: Path) -> None:
    """Verify that without the flag, behavior is identical to before."""
    closure_path = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"
    _write_json(closure_path, {"result": "NOT_READY", "checks": []})

    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "closure_result: NOT_READY" in result.stdout

    # Verify no workflow_status JSON is created
    workflow_status_path = tmp_path / "docs" / "context" / "workflow_status_latest.json"
    assert not workflow_status_path.exists()


def test_workflow_status_json_generation(tmp_path: Path) -> None:
    """Verify JSON generation with flag."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "closure_result: NOT_READY" in result.stdout

    # Verify JSON file is created
    assert output_path.exists()

    # Load and verify JSON structure
    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify required top-level fields
    assert "schema_version" in workflow_status
    assert workflow_status["schema_version"] == "1.0.0"
    assert "generated_at_utc" in workflow_status
    assert "repo_root" in workflow_status
    assert "overall_status" in workflow_status
    assert "nodes" in workflow_status
    assert "role_views" in workflow_status
    assert "metadata" in workflow_status

    # Verify nodes array is populated
    nodes = workflow_status["nodes"]
    assert isinstance(nodes, list)
    assert len(nodes) > 0

    # Verify each node has required fields
    for node in nodes:
        assert "node_id" in node
        assert "title" in node
        assert "status_color" in node
        assert "progress_state" in node
        assert "owner_role" in node
        assert "blockers" in node
        assert "source_of_truth" in node
        assert isinstance(node["blockers"], list)
        assert isinstance(node["source_of_truth"], str)

    # Verify role_views structure
    role_views = workflow_status["role_views"]
    assert "PM" in role_views
    assert "CEO" in role_views
    assert "Worker" in role_views
    assert "Auditor" in role_views
    assert "QA" in role_views


def test_workflow_status_derives_hold_state(tmp_path: Path) -> None:
    """Verify HOLD state mapping."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    # Load workflow status
    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify overall_status reflects blocking state
    assert workflow_status["overall_status"] == "yellow"

    # Find Execution node and verify it's yellow
    execution_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Execution"),
        None,
    )
    assert execution_node is not None
    assert execution_node["status_color"] == "yellow"
    assert execution_node["progress_state"] == "BLOCKED"
    assert "Execution on hold" in execution_node["blockers"]

    # Find ValidationClosure node and verify it's yellow
    validation_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "ValidationClosure"),
        None,
    )
    assert validation_node is not None
    assert validation_node["status_color"] == "yellow"
    assert validation_node["progress_state"] == "BLOCKED"
    assert len(validation_node["blockers"]) > 0


def test_workflow_status_marks_blocked_startup_gate_states_as_blocked(tmp_path: Path) -> None:
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    context_dir = fixtures["context_dir"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    _write_json(
        context_dir / "startup_intake_latest.json",
        {
            "schema_version": "1.0.0",
            "generated_at_utc": "2026-03-10T00:00:00Z",
            "startup_gate": {"status": "BLOCKED_READINESS"},
        },
    )

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))
    startup_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Startup"),
        None,
    )
    assert startup_node is not None
    assert startup_node["status_color"] == "yellow"
    assert startup_node["progress_state"] == "BLOCKED"
    assert "BLOCKED_READINESS" in " ".join(startup_node["blockers"])


def test_workflow_status_missing_artifacts_graceful(tmp_path: Path) -> None:
    """Verify graceful degradation when artifacts are missing."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Only create closure status (minimal requirement)
    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "NOT_READY",
        "checks": [],
    }
    _write_json(context_dir / "loop_closure_status_latest.json", closure_status)

    output_path = tmp_path / "docs" / "context" / "workflow_status_latest.json"
    result = _run_with_workflow_status(tmp_path, output_path)

    # Script should still succeed
    assert result.returncode == 1, result.stdout + result.stderr

    # Verify JSON is still generated
    assert output_path.exists()

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify missing artifacts result in gray/NOT_STARTED nodes
    startup_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Startup"),
        None,
    )
    assert startup_node is not None
    assert startup_node["status_color"] == "gray"
    assert startup_node["progress_state"] == "NOT_STARTED"

    execution_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Execution"),
        None,
    )
    assert execution_node is not None
    assert execution_node["status_color"] == "gray"
    assert execution_node["progress_state"] == "NOT_STARTED"


def test_workflow_status_role_views(tmp_path: Path) -> None:
    """Verify role view aggregation."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify role_views object is present
    role_views = workflow_status["role_views"]
    assert isinstance(role_views, dict)

    # Verify all expected roles exist
    assert "PM" in role_views
    assert "CEO" in role_views
    assert "Worker" in role_views
    assert "Auditor" in role_views
    assert "QA" in role_views

    # Verify nodes are grouped by owner_role
    pm_nodes = role_views["PM"]
    assert isinstance(pm_nodes, list)
    assert "Startup" in pm_nodes
    assert "PublicEntry" in pm_nodes
    assert "DocsSpine" in pm_nodes

    worker_nodes = role_views["Worker"]
    assert "RoundContract" in worker_nodes
    assert "Execution" in worker_nodes
    assert "MemoryArtifacts" in worker_nodes

    auditor_nodes = role_views["Auditor"]
    assert "ValidationClosure" in auditor_nodes

    # Note: Measurement and Authority owner_role is PM per spec
    pm_nodes_check = role_views["PM"]
    assert "Measurement" in pm_nodes_check
    assert "Authority" in pm_nodes_check
    # Note: Authority owner_role is PM per spec (CEO is advisory)
    assert "Authority" in pm_nodes_check

    # CEO role has no owner nodes in current spec
    ceo_nodes = role_views["CEO"]
    assert isinstance(ceo_nodes, list)


def test_workflow_status_artifact_provenance(tmp_path: Path) -> None:
    """Verify provenance tracking."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify each node has source_of_truth field
    for node in workflow_status["nodes"]:
        assert "source_of_truth" in node
        assert isinstance(node["source_of_truth"], str)

    # Verify specific provenance examples (normalize paths for cross-platform compatibility)
    startup_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Startup"),
        None,
    )
    assert startup_node is not None
    startup_source = startup_node["source_of_truth"].replace("\\", "/")
    assert "docs/context/startup_intake_latest.json" == startup_source

    execution_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Execution"),
        None,
    )
    assert execution_node is not None
    execution_source = execution_node["source_of_truth"].replace("\\", "/")
    assert "docs/context/loop_cycle_summary_latest.json" == execution_source

    validation_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "ValidationClosure"),
        None,
    )
    assert validation_node is not None
    validation_source = validation_node["source_of_truth"].replace("\\", "/")
    assert "docs/context/loop_closure_status_latest.json" == validation_source


def test_workflow_status_generation_failure_non_fatal(tmp_path: Path) -> None:
    """Verify failure handling - generation failure doesn't change exit code."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "READY_TO_ESCALATE",
        "checks": [],
    }
    _write_json(context_dir / "loop_closure_status_latest.json", closure_status)

    # Create a file where we expect a directory, which will cause mkdir to fail
    blocking_file = tmp_path / "blocked"
    blocking_file.write_text("blocking", encoding="utf-8")
    invalid_output_path = blocking_file / "workflow_status.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(tmp_path),
            "--workflow-status-json-out",
            str(invalid_output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Verify warning is printed to stderr
    assert "WARNING: Failed to generate workflow status overlay" in result.stderr

    # Verify exit code is NOT changed (still based on closure result)
    assert result.returncode == 0, result.stdout + result.stderr

    # Verify script completes successfully
    assert "closure_result: READY_TO_ESCALATE" in result.stdout


def test_workflow_status_ready_to_escalate_green(tmp_path: Path) -> None:
    """Verify green status when ready to escalate."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Create all artifacts in READY state
    startup_intake = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "startup_gate": {"status": "READY_TO_EXECUTE"},
    }
    _write_json(context_dir / "startup_intake_latest.json", startup_intake)

    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "READY_TO_ESCALATE",
        "checks": [{"name": "startup_gate_status", "status": "PASS"}],
    }
    _write_json(context_dir / "loop_closure_status_latest.json", closure_status)

    cycle_summary = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "final_result": "PASS",
    }
    _write_json(context_dir / "loop_cycle_summary_latest.json", cycle_summary)

    (context_dir / "round_contract_latest.md").write_text(
        "# Round Contract\n\nContract content.\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "docs" / "context" / "workflow_status_latest.json"
    result = _run_with_workflow_status(tmp_path, output_path)

    assert result.returncode == 0, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify overall_status is green
    assert workflow_status["overall_status"] == "green"

    # Verify critical nodes are green
    startup_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Startup"),
        None,
    )
    assert startup_node is not None
    assert startup_node["status_color"] == "green"

    execution_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Execution"),
        None,
    )
    assert execution_node is not None
    assert execution_node["status_color"] == "green"

    validation_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "ValidationClosure"),
        None,
    )
    assert validation_node is not None
    assert validation_node["status_color"] == "green"


def test_workflow_status_relative_output_path(tmp_path: Path) -> None:
    """Verify relative output path is resolved against repo root."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]

    # Use relative path
    relative_output_path = Path("workflow_status_test.json")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--workflow-status-json-out",
            str(relative_output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, result.stdout + result.stderr

    # Verify file is created at repo_root / relative_path
    expected_path = repo_root / relative_output_path
    assert expected_path.exists()

    workflow_status = json.loads(expected_path.read_text(encoding="utf-8"))
    assert "schema_version" in workflow_status


def test_workflow_status_timestamps_valid_iso8601(tmp_path: Path) -> None:
    """Verify timestamps are valid ISO 8601 format."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Verify top-level timestamp
    from datetime import datetime
    generated_at = workflow_status["generated_at_utc"]
    assert isinstance(generated_at, str)
    # Should parse without error
    datetime.fromisoformat(generated_at.replace("Z", "+00:00"))

    # Verify node timestamps
    for node in workflow_status["nodes"]:
        updated_at = node.get("updated_at_utc")
        if updated_at is not None:
            assert isinstance(updated_at, str)
            datetime.fromisoformat(updated_at.replace("Z", "+00:00"))


def test_workflow_status_color_values_valid(tmp_path: Path) -> None:
    """Verify status color values are valid."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    valid_colors = {"green", "yellow", "red", "gray", "blue"}
    valid_states = {"READY", "IN_PROGRESS", "BLOCKED", "NOT_STARTED", "ACTIVE", "COMPLETE", "ERROR"}

    # Verify overall_status
    assert workflow_status["overall_status"] in valid_colors

    # Verify each node
    for node in workflow_status["nodes"]:
        assert node["status_color"] in valid_colors, f"Invalid color: {node['status_color']}"
        assert node["progress_state"] in valid_states, f"Invalid state: {node['progress_state']}"


def test_workflow_status_measurement_node_active(tmp_path: Path) -> None:
    """Verify measurement node shows ACTIVE when directory exists."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]

    # Create phase_c_measurement directory
    measurement_dir = repo_root / "phase_c_measurement"
    measurement_dir.mkdir(parents=True, exist_ok=True)
    (measurement_dir / "test_file.txt").write_text("test", encoding="utf-8")

    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"
    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    measurement_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "Measurement"),
        None,
    )
    assert measurement_node is not None
    assert measurement_node["status_color"] == "blue"
    assert measurement_node["progress_state"] == "ACTIVE"


def test_workflow_status_memory_artifacts_partial(tmp_path: Path) -> None:
    """Verify memory artifacts node handles partial presence."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "NOT_READY",
        "checks": [],
    }
    _write_json(context_dir / "loop_closure_status_latest.json", closure_status)

    # Create only memory packet, not handoff
    memory_packet = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
    }
    _write_json(context_dir / "exec_memory_packet_latest.json", memory_packet)

    output_path = tmp_path / "docs" / "context" / "workflow_status_latest.json"
    result = _run_with_workflow_status(tmp_path, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    memory_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "MemoryArtifacts"),
        None,
    )
    assert memory_node is not None
    assert memory_node["status_color"] == "yellow"
    assert memory_node["progress_state"] == "BLOCKED"
    assert len(memory_node["blockers"]) > 0
    assert any("Missing:" in blocker for blocker in memory_node["blockers"])


def test_workflow_status_round_contract_fail_closed_triggers(tmp_path: Path) -> None:
    """Verify RoundContract checks fail-closed triggers (QA, Socratic, INTUITION_GATE)."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal closure status
    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "NOT_READY",
        "checks": []
    }
    (context_dir / "loop_closure_status_latest.json").write_text(json.dumps(closure_status))

    # Create round contract with fail-closed triggers
    round_contract = """# Round Contract

- DECISION_CLASS: ONE_WAY
- RISK_TIER: HIGH
- TDD_MODE: REQUIRED
- DONE_WHEN_CHECKS: startup_gate_status
- EXECUTION_LANE: STANDARD
- INTUITION_GATE: MACHINE_DEFAULT
- QA_PRE_ESCALATION_REQUIRED: YES
- QA_VERDICT: PENDING
- SOCRATIC_CHALLENGE_REQUIRED: YES
- SOCRATIC_CHALLENGE_RESOLVED: NO
- WORKFLOW_LANE: DEFAULT
"""
    (context_dir / "round_contract_latest.md").write_text(round_contract)

    repo_root = tmp_path
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Find RoundContract node
    round_contract_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "RoundContract"),
        None,
    )
    assert round_contract_node is not None

    # Verify fail-closed triggers are detected
    assert round_contract_node["status_color"] == "red"
    assert round_contract_node["progress_state"] == "BLOCKED"
    assert len(round_contract_node["blockers"]) > 0

    # Verify specific fail-closed blockers
    blockers_text = " ".join(round_contract_node["blockers"])
    assert "QA" in blockers_text or "qa" in blockers_text.lower()
    assert "Socratic" in blockers_text or "socratic" in blockers_text.lower()

    # Verify no parsing errors
    assert "name 'qad' is not defined" not in blockers_text
    assert "Failed to parse" not in blockers_text or round_contract_node["progress_state"] != "ERROR"


def test_workflow_status_round_contract_clean_pass(tmp_path: Path) -> None:
    """Verify RoundContract shows green when all fail-closed checks pass."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal closure status
    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "NOT_READY",
        "checks": []
    }
    (context_dir / "loop_closure_status_latest.json").write_text(json.dumps(closure_status))

    # Create round contract with all checks passing
    round_contract = """# Round Contract

- DECISION_CLASS: TWO_WAY
- RISK_TIER: LOW
- TDD_MODE: NOT_APPLICABLE
- TDD_NOT_APPLICABLE_REASON: docs-only change
- DONE_WHEN_CHECKS: startup_gate_status
- EXECUTION_LANE: STANDARD
- INTUITION_GATE: MACHINE_DEFAULT
- QA_PRE_ESCALATION_REQUIRED: NO
- SOCRATIC_CHALLENGE_REQUIRED: NO
- WORKFLOW_LANE: DEFAULT
"""
    (context_dir / "round_contract_latest.md").write_text(round_contract)

    repo_root = tmp_path
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    workflow_status = json.loads(output_path.read_text(encoding="utf-8"))

    # Find RoundContract node
    round_contract_node = next(
        (node for node in workflow_status["nodes"] if node["node_id"] == "RoundContract"),
        None,
    )
    assert round_contract_node is not None

    # Verify clean pass
    assert round_contract_node["status_color"] == "green"
    assert round_contract_node["progress_state"] == "READY"
    assert len(round_contract_node["blockers"]) == 0


# ============================================================================
# Workflow Status Markdown Tests
# ============================================================================


def _run_with_workflow_status_md(repo_root: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    """Run script with workflow status Markdown output flag."""
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--workflow-status-md-out",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_workflow_status_md_generation(tmp_path: Path) -> None:
    """Verify MD file created with --workflow-status-md-out flag."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.md"

    result = _run_with_workflow_status_md(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    # Verify MD file is created
    assert output_path.exists()

    # Verify it's readable text
    md_content = output_path.read_text(encoding="utf-8")
    assert len(md_content) > 0
    assert "# Workflow Status Overlay" in md_content


def test_workflow_status_md_structure(tmp_path: Path) -> None:
    """Verify MD contains expected sections."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.md"

    result = _run_with_workflow_status_md(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    md_content = output_path.read_text(encoding="utf-8")

    # Verify header section
    assert "# Workflow Status Overlay" in md_content
    assert "**Generated:**" in md_content
    assert "**Overall Status:**" in md_content
    assert "**Summary:**" in md_content

    # Verify legend section
    assert "## Status Legend" in md_content
    assert "🟢 Green = Ready" in md_content
    assert "🟡 Yellow = Blocked" in md_content
    assert "🔵 Blue = In Progress" in md_content
    assert "⚪ Gray = Not Started" in md_content
    assert "🔴 Red = Failed" in md_content

    # Verify railway section
    assert "## Workflow Railway" in md_content
    assert "→" in md_content

    # Verify node details section
    assert "## Node Details" in md_content

    # Verify role views section
    assert "## Role Views" in md_content

    # Verify metadata section
    assert "## Metadata" in md_content


def test_workflow_status_md_node_count(tmp_path: Path) -> None:
    """Verify MD renders all 9 nodes in stable order."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.md"

    result = _run_with_workflow_status_md(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    md_content = output_path.read_text(encoding="utf-8")

    # Verify all 9 nodes are present
    expected_nodes = [
        "Startup",
        "Execution",
        "ValidationClosure",
        "RoundContract",
        "MemoryArtifacts",
        "Measurement",
        "PublicEntry",
        "DocsSpine",
        "Authority",
    ]

    for node_name in expected_nodes:
        assert node_name in md_content, f"Node {node_name} not found in MD"


def test_workflow_status_md_blocked_startup(tmp_path: Path) -> None:
    """Verify blocked startup renders with blockers in MD."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    context_dir = fixtures["context_dir"]
    output_path = repo_root / "docs" / "context" / "workflow_status_latest.md"

    _write_json(
        context_dir / "startup_intake_latest.json",
        {
            "schema_version": "1.0.0",
            "generated_at_utc": "2026-03-10T00:00:00Z",
            "startup_gate": {"status": "BLOCKED_READINESS"},
        },
    )

    result = _run_with_workflow_status_md(repo_root, output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    md_content = output_path.read_text(encoding="utf-8")

    # Verify blocked status is rendered
    assert "yellow" in md_content or "🟡" in md_content
    assert "BLOCKED" in md_content


def test_workflow_status_md_generation_failure_non_fatal(tmp_path: Path) -> None:
    """Verify MD generation failure doesn't change exit code."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    closure_status = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "result": "READY_TO_ESCALATE",
        "checks": [],
    }
    _write_json(context_dir / "loop_closure_status_latest.json", closure_status)

    # Create a file where we expect a directory
    blocking_file = tmp_path / "blocked"
    blocking_file.write_text("blocking", encoding="utf-8")
    invalid_output_path = blocking_file / "workflow_status.md"

    result = subprocess.run(
        [
            sys.executable,
          str(SCRIPT_PATH),
            "--repo-root",
            str(tmp_path),
            "--workflow-status-md-out",
            str(invalid_output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Verify warning is printed to stderr
    assert "WARNING: Failed to generate workflow status Markdown overlay" in result.stderr

    # Verify exit code is NOT changed (still based on closure result)
    assert result.returncode == 0, result.stdout + result.stderr

    # Verify script completes successfully
    assert "closure_result: READY_TO_ESCALATE" in result.stdout


def test_workflow_status_both_flags_emit_consistent_outputs(tmp_path: Path) -> None:
    """Verify a single run can emit both JSON and Markdown workflow overlays."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]

    json_out = repo_root / "workflow_status.json"
    md_out = repo_root / "workflow_status.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--workflow-status-json-out",
            str(json_out),
            "--workflow-status-md-out",
            str(md_out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert json_out.exists()
    assert md_out.exists()

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    md_content = md_out.read_text(encoding="utf-8")

    assert f"**Overall Status:** {payload['overall_status']}" in md_content
    for node in payload["nodes"]:
        assert node["title"] in md_content


def test_workflow_status_md_only_no_json(tmp_path: Path) -> None:
    """Verify MD-only flag doesn't create JSON file."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]
    md_output_path = repo_root / "docs" / "context" / "workflows_latest.md"
    json_output_path = repo_root / "docs" / "context" / "workflow_status_latest.json"

    result = _run_with_workflow_status_md(repo_root, md_output_path)
    assert result.returncode == 1, result.stdout + result.stderr

    # Verify MD file is created
    assert md_output_path.exists()

    # Verify JSON file is NOT created
    assert not json_output_path.exists()


def test_workflow_status_md_relative_path(tmp_path: Path) -> None:
    """Verify relative MD path resolves to repo_root."""
    fixtures = _create_workflow_status_fixtures(tmp_path)
    repo_root = fixtures["repo_root"]

    # Use relative path
    relative_output_path = Path("workflow_status_test.md")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--workflow-status-md-out",
            str(relative_output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, result.stdout + result.stderr

    # Verify file is created at repo_root / relative_path
    expected_path = repo_root / relative_output_path
    assert expected_path.exists()

    md_content = expected_path.read_text(encoding="utf-8")
    assert "# Workflow Status Overlay" in md_content


def test_workflow_status_md_fallback_next_action_when_missing(tmp_path: Path) -> None:
    """Verify renderer uses _derive_next_action_fallback() when node lacks next_action field."""
    # Import the renderer directly to test with a modified payload
    import sys
    from pathlib import Path as PathlibPath

    script_dir = PathlibPath(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(script_dir))

    import print_takeover_entrypoint

    # Create a minimal payload with a node missing next_action
    payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T00:00:00Z",
        "repo_root": str(tmp_path),
        "source_of_truth_policy": "docs/loop_operating_contract.md#source-of-truth-hierarchy",
        "overall_status": "yellow",
        "overall_summary": "Test node without next_action",
        "nodes": [
            {
                "node_id": "TestNode",
                "title": "Test Node",
                "status_color": "yellow",
                "progress_state": "BLOCKED",
                "owner_role": "Worker",
                "blockers": ["Test blocker"],
                "source_of_truth": "test.json",
                # Intentionally omit next_action to trigger fallback
            }
        ],
        "role_views": {"Worker": ["TestNode"], "PM": [], "CEO": [], "Auditor": [], "QA": []},
        "metadata": {
            "generator": "test",
            "advisory_only": True,
        }
    }

    # Render the markdown
    md_content = print_takeover_entrypoint._render_workflow_status_markdown(payload)

    # Verify next action is present
    assert "**Next Action:**" in md_content

    # Verify fallback logic was used (should show "Resolve blockers: Test blocker")
    assert "Resolve blockers: Test blocker" in md_content
