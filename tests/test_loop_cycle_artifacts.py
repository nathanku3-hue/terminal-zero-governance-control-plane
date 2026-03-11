from __future__ import annotations

import json
from pathlib import Path

import pytest


loop_cycle_artifacts = pytest.importorskip(
    "scripts.loop_cycle_artifacts",
    reason="P2-B1 leaf module has not landed in this checkout",
)


SECTION_KEYS = [
    "next_round_handoff",
    "expert_request",
    "pm_ceo_research_brief",
    "board_decision_brief",
]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload, indent=2) + "\n")


def _build_exec_memory_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-10T12:00:00Z",
        "next_round_handoff": {
            "status": "ACTION_REQUIRED",
            "recommended_intent": "close remaining promotion blockers",
            "recommended_scope": "current execution slice",
            "non_goals": "new architecture",
            "done_when": "blocking criteria reduced and artifacts refreshed",
            "done_when_checks": ["go_signal_action_gate", "freshness_gate"],
            "artifacts_to_refresh": [
                "docs/context/auditor_promotion_dossier.json",
                "docs/context/ceo_go_signal.md",
            ],
            "blocking_gap_codes": ["c3_min_weeks", "c4b_annotation_coverage"],
            "human_brief": (
                "Close remaining promotion blockers by refreshing dossier and GO "
                "artifacts without widening the slice."
            ),
            "machine_view": (
                "SURFACE: next_round_handoff\n"
                "STATUS: ACTION_REQUIRED\n"
                "RECOMMENDED_INTENT: close remaining promotion blockers"
            ),
            "paste_ready_block": "ORIGINAL_INTENT: close remaining promotion blockers",
        },
        "expert_request": {
            "status": "ADVISORY",
            "target_expert": "qa",
            "trigger_reason": "low_confidence",
            "question": "Validate the remaining ambiguous edge cases before escalation.",
            "requested_domain": "qa",
            "roster_fit": "APPROVED_MANDATORY",
            "milestone_id": "milestone-1",
            "board_reentry_required": "false",
            "board_reentry_reason_codes": ["none"],
            "expert_memory_status": "FRESH",
            "board_memory_status": "FRESH",
            "memory_reason_codes": ["none"],
            "source_artifacts": ["docs/context/ceo_go_signal.md"],
            "human_brief": (
                "Ask QA to validate the remaining ambiguous edge cases before escalation."
            ),
            "machine_view": (
                "SURFACE: expert_request\n"
                "STATUS: ADVISORY\n"
                "TARGET_EXPERT: qa\n"
                "REQUESTED_DOMAIN: qa"
            ),
            "paste_ready_block": (
                "=== EXPERT REQUEST ===\n"
                "TargetExpert: qa\n"
                "Question: Validate the remaining ambiguous edge cases before escalation.\n"
                "===================="
            ),
        },
        "pm_ceo_research_brief": {
            "status": "ADVISORY",
            "delegated_to": "principal",
            "question": "What is the top tradeoff to resolve before promotion?",
            "required_tradeoff_dimensions": ["impact", "risk", "effort", "maintainability"],
            "evidence_required": ["docs/context/ceo_go_signal.md"],
            "human_brief": "Delegate the top pre-promotion tradeoff to principal review.",
            "machine_view": (
                "SURFACE: pm_ceo_research_brief\n"
                "STATUS: ADVISORY\n"
                "DELEGATED_TO: principal"
            ),
            "paste_ready_block": (
                "=== PM/CEO RESEARCH BRIEF ===\n"
                "DelegatedTo: principal\n"
                "Question: What is the top tradeoff to resolve before promotion?\n"
                "=============================="
            ),
        },
        "board_decision_brief": {
            "status": "ADVISORY",
            "decision_topic": "Promotion readiness recommendation",
            "recommended_option": "Hold promotion until expert ambiguity is cleared.",
            "lineup_decision_needed": "false",
            "lineup_gap_domains": ["none"],
            "approved_roster_snapshot": {
                "mandatory": ["principal", "qa"],
                "optional": ["riskops"],
            },
            "reintroduce_board_when": "when milestone scope changes",
            "board_reentry_required": "false",
            "board_reentry_reason_codes": ["none"],
            "expert_memory_status": "FRESH",
            "board_memory_status": "FRESH",
            "memory_reason_codes": ["none"],
            "source_artifacts": [
                "docs/context/ceo_go_signal.md",
                "docs/context/expert_request_latest.md",
            ],
            "open_risks": ["stale evidence", "missing final signoff"],
            "ceo_lens": {"business_upside": "Protect escalation quality."},
            "cto_lens": {"architecture_coherence": "Avoid unresolved ambiguity."},
            "coo_lens": {"execution_load": "Keep coordination bounded to one expert pass."},
            "expert_lens": {
                "target_expert": "qa",
                "specialist_question": "Resolve ambiguity before escalation.",
            },
            "human_brief": (
                "Hold promotion until the expert ambiguity is cleared without widening "
                "the control-plane scope."
            ),
            "machine_view": (
                "SURFACE: board_decision_brief\n"
                "STATUS: ADVISORY\n"
                "DECISION_TOPIC: Promotion readiness recommendation"
            ),
            "paste_ready_block": (
                "=== BOARD DECISION BRIEF ===\n"
                "CEO: hold until ambiguity is cleared\n"
                "CTO: preserve interface and promotion discipline\n"
                "COO: keep follow-up to one expert pass\n"
                "============================"
            ),
        },
    }


def test_persist_advisory_sections_writes_expected_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path
    context_dir = repo_root / "docs" / "context"
    exec_memory_json = context_dir / "exec_memory_packet_latest_current.json"
    exec_memory_payload = _build_exec_memory_payload()
    _write_json(exec_memory_json, exec_memory_payload)

    advisory_artifacts = loop_cycle_artifacts.persist_advisory_sections(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
    )

    assert set(advisory_artifacts.keys()) == set(SECTION_KEYS)

    for section_key in SECTION_KEYS:
        artifact_bundle = advisory_artifacts[section_key]
        assert isinstance(artifact_bundle, dict)
        assert artifact_bundle["status"] == exec_memory_payload[section_key]["status"]
        assert artifact_bundle["payload"] == exec_memory_payload[section_key]

        output_json = artifact_bundle["json"]
        output_md = artifact_bundle["md"]
        assert isinstance(output_json, Path)
        assert isinstance(output_md, Path)
        assert output_json.exists()
        assert output_md.exists()
        assert output_json.name == f"{section_key}_latest.json"
        assert output_md.name == f"{section_key}_latest.md"

        persisted_payload = json.loads(output_json.read_text(encoding="utf-8"))
        assert persisted_payload == {
            "schema_version": "1.0.0",
            "generated_at_utc": "2026-03-10T12:00:00Z",
            "source_exec_memory_json": str(exec_memory_json),
            section_key: exec_memory_payload[section_key],
        }

    next_round_handoff_markdown = advisory_artifacts["next_round_handoff"]["md"].read_text(
        encoding="utf-8"
    )
    assert "# Next Round Handoff" in next_round_handoff_markdown
    assert "## Done-When Checks" in next_round_handoff_markdown
    assert "## Primary Blockers" in next_round_handoff_markdown
    assert "## Artifacts To Refresh" in next_round_handoff_markdown
    assert "## Human Brief" in next_round_handoff_markdown
    assert "## Machine View" in next_round_handoff_markdown
    assert "## Paste-Ready Block" in next_round_handoff_markdown
    assert "ORIGINAL_INTENT: close remaining promotion blockers" in next_round_handoff_markdown

    expert_request_markdown = advisory_artifacts["expert_request"]["md"].read_text(
        encoding="utf-8"
    )
    assert "# Expert Request" in expert_request_markdown
    assert "## Lineup" in expert_request_markdown
    assert "RequestedDomain: qa" in expert_request_markdown
    assert "## Memory" in expert_request_markdown
    assert "ExpertMemoryStatus: FRESH" in expert_request_markdown
    assert "## Human Brief" in expert_request_markdown
    assert "## Machine View" in expert_request_markdown
    assert "## Paste-Ready Block" in expert_request_markdown
    assert "TargetExpert: qa" in expert_request_markdown

    research_brief_markdown = advisory_artifacts["pm_ceo_research_brief"]["md"].read_text(
        encoding="utf-8"
    )
    assert "# PM/CEO Research Brief" in research_brief_markdown
    assert "## Tradeoff Dimensions" in research_brief_markdown
    assert "## Evidence Required" in research_brief_markdown
    assert "## Human Brief" in research_brief_markdown
    assert "## Machine View" in research_brief_markdown
    assert "## Paste-Ready Block" in research_brief_markdown
    assert "DelegatedTo: principal" in research_brief_markdown

    board_brief_markdown = advisory_artifacts["board_decision_brief"]["md"].read_text(
        encoding="utf-8"
    )
    assert "# Board Decision Brief" in board_brief_markdown
    assert "## CEO Lens" in board_brief_markdown
    assert "## Lineup" in board_brief_markdown
    assert "LineupDecisionNeeded: false" in board_brief_markdown
    assert "ApprovedRosterSnapshot: mandatory=principal, qa; optional=riskops" in board_brief_markdown
    assert "## Memory" in board_brief_markdown
    assert "BoardMemoryStatus: FRESH" in board_brief_markdown
    assert "## Open Risks" in board_brief_markdown
    assert "## Human Brief" in board_brief_markdown
    assert "## Machine View" in board_brief_markdown
    assert "## Paste-Ready Block" in board_brief_markdown


def test_mirror_repo_root_convenience_copies_markdown_and_takeover_index(tmp_path: Path) -> None:
    repo_root = tmp_path
    context_dir = repo_root / "docs" / "context"
    exec_memory_json = context_dir / "exec_memory_packet_latest_current.json"
    _write_json(exec_memory_json, _build_exec_memory_payload())

    advisory_artifacts = loop_cycle_artifacts.persist_advisory_sections(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
    )
    mirrored_files = loop_cycle_artifacts.mirror_repo_root_convenience(
        repo_root=repo_root,
        context_dir=context_dir,
        advisory_artifacts=advisory_artifacts,
    )

    assert mirrored_files == {
        "next_round_handoff": repo_root / "NEXT_ROUND_HANDOFF_LATEST.md",
        "expert_request": repo_root / "EXPERT_REQUEST_LATEST.md",
        "pm_ceo_research_brief": repo_root / "PM_CEO_RESEARCH_BRIEF_LATEST.md",
        "board_decision_brief": repo_root / "BOARD_DECISION_BRIEF_LATEST.md",
        "takeover": repo_root / "TAKEOVER_LATEST.md",
    }

    for section_key, mirror_path in mirrored_files.items():
        assert mirror_path.exists()
        if section_key == "takeover":
            continue
        source_markdown = advisory_artifacts[section_key]["md"].read_text(encoding="utf-8")
        assert mirror_path.read_text(encoding="utf-8") == source_markdown

    takeover_markdown = mirrored_files["takeover"].read_text(encoding="utf-8")
    assert "# Takeover Latest" in takeover_markdown
    assert f"- SourceOfTruth: `{context_dir}`" in takeover_markdown
    assert "| Artifact | Status | RepoRootMirror | SourceMarkdown |" in takeover_markdown
    assert "`NEXT_ROUND_HANDOFF_LATEST.md`" in takeover_markdown
    assert "`EXPERT_REQUEST_LATEST.md`" in takeover_markdown
    assert "`PM_CEO_RESEARCH_BRIEF_LATEST.md`" in takeover_markdown
    assert "`BOARD_DECISION_BRIEF_LATEST.md`" in takeover_markdown
    assert f"`{advisory_artifacts['next_round_handoff']['md']}`" in takeover_markdown
    assert f"`{advisory_artifacts['expert_request']['md']}`" in takeover_markdown


@pytest.mark.parametrize("payload_text", [None, "{not json"])
def test_persist_advisory_sections_fail_closed_for_missing_or_malformed_exec_memory(
    tmp_path: Path, payload_text: str | None
) -> None:
    context_dir = tmp_path / "docs" / "context"
    exec_memory_json = context_dir / "exec_memory_packet_latest_current.json"

    if payload_text is not None:
        _write_text(exec_memory_json, payload_text)

    advisory_artifacts = loop_cycle_artifacts.persist_advisory_sections(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
    )

    assert advisory_artifacts == {
        "next_round_handoff": None,
        "expert_request": None,
        "pm_ceo_research_brief": None,
        "board_decision_brief": None,
    }
    assert not (context_dir / "next_round_handoff_latest.json").exists()
    assert not (context_dir / "expert_request_latest.json").exists()
    assert not (context_dir / "pm_ceo_research_brief_latest.json").exists()
    assert not (context_dir / "board_decision_brief_latest.json").exists()
