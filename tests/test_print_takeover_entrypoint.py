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
