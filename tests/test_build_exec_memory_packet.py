from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_exec_memory_packet.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_loop_summary() -> dict:
    return {
        "run_id": "20260304_000545",
        "final_result": "HOLD",
        "step_summary": {
            "pass": 4,
            "hold": 1,
            "fail": 1,
            "error": 0,
            "skip": 0,
            "total": 6,
        },
        "steps": [
            {"step_id": "G00", "status": "PASS"},
            {"step_id": "G01", "status": "PASS"},
            {"step_id": "G07", "status": "FAIL"},
            {"step_id": "G08", "status": "PASS"},
            {"step_id": "G09", "status": "PASS"},
            {"step_id": "G11", "status": "HOLD"},
        ],
    }


def _make_dossier() -> dict:
    return {
        "schema_version": "1.0.0",
        "report_type": "dossier",
        "promotion_criteria": {
            "c0_infra_health": {"met": True, "value": "0 failures"},
            "c1_24b_close": {"met": True, "value": "APPROVED"},
            "c2_min_items": {"met": True, "value": "50 >= 30"},
            "c3_min_weeks": {"met": False, "value": "1 consecutive weeks >= 2"},
        },
    }


def _make_calibration() -> dict:
    return {
        "schema_version": "1.0.0",
        "report_type": "weekly",
        "totals": {
            "items_reviewed": 50,
            "critical": 2,
            "high": 5,
            "medium": 10,
            "low": 3,
            "info": 1,
        },
    }


def _make_go_signal() -> str:
    return """# CEO Go Signal

**Status:** GREEN

All systems operational. Proceed with Phase 24C rollout.
"""


def _make_hold_go_signal() -> str:
    return """# CEO GO Signal

- Recommended Action: HOLD

## Blocking Reasons

- C3 not met (1 consecutive weeks >= 2).
- C4b not met (53.49%).

## Next Steps

1. Satisfy remaining automated dossier criteria (C0, C2, C3, C4, C4b, C5).
2. Regenerate dossier and calibration artifacts.
"""


def _make_decision_log() -> str:
    return """# Decision Log

## 2026-03-07
- Approved Phase 24C auditor calibration
- Deferred multi-worker concurrency to Phase 25
"""


def _make_milestone_roster() -> dict:
    return {
        "milestone_id": "phase24c-milestone-1",
        "mandatory_domains": ["principal", "riskops", "qa"],
        "optional_domains": ["system_eng", "architect"],
        "board_reentry_triggers": [
            "UNKNOWN_EXPERT_DOMAIN",
            "ROSTER_MISSING",
            "EXPERT_DISAGREEMENT",
            "MILESTONE_GATE_REVIEW",
        ],
        "unknown_expert_domain_policy": "ESCALATE_TO_BOARD",
    }


def _collect_explicit_uncertainty_metadata(packet: dict) -> list[tuple[str, str, str]]:
    emitted: list[tuple[str, str, str]] = []

    automation_status = packet.get("automation_uncertainty_status")
    if isinstance(automation_status, dict):
        value = str(automation_status.get("status", "")).strip()
        if value:
            emitted.append(("packet", "automation_uncertainty_status.status", value))

    candidate_sections = {
        "replanning": packet.get("replanning"),
        "next_round_handoff": packet.get("next_round_handoff"),
        "expert_request": packet.get("expert_request"),
        "pm_ceo_research_brief": packet.get("pm_ceo_research_brief"),
        "board_decision_brief": packet.get("board_decision_brief"),
    }
    for section_name, section in candidate_sections.items():
        if not isinstance(section, dict):
            continue
        for field_name in ("lean_uncertainty_status", "uncertainty_status"):
            if field_name not in section:
                continue
            value = str(section[field_name]).strip()
            emitted.append((section_name, field_name, value))
    return emitted


def _collect_boundary_registry_references(packet: dict) -> list[str]:
    refs: list[str] = []

    def add_reference(value: object) -> None:
        if not isinstance(value, str):
            return
        text = value.strip()
        normalized = text.lower()
        if not text or "boundary" not in normalized or "registry" not in normalized:
            return
        if text not in refs:
            refs.append(text)

    automation_status = packet.get("automation_uncertainty_status")
    if isinstance(automation_status, dict):
        add_reference(automation_status.get("boundary_registry"))

    inputs = packet.get("inputs")
    if isinstance(inputs, dict):
        for key, value in inputs.items():
            if "boundary" in str(key).lower() or "registry" in str(key).lower():
                add_reference(value)
            add_reference(value)

    for value in packet.get("source_bindings", []):
        add_reference(value)

    retrieval_namespaces = packet.get("retrieval_namespaces")
    if isinstance(retrieval_namespaces, dict):
        for entries in retrieval_namespaces.values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                add_reference(entry.get("source"))

    return refs


def _run_script(
    tmp_path: Path,
    *,
    loop_summary: dict | None = None,
    dossier: dict | None = None,
    calibration: dict | None = None,
    go_signal: str | None = None,
    decision_log: str | None = None,
    milestone_roster: dict | None = None,
    pm_budget: int = 3000,
    ceo_budget: int = 1800,
    output_json_name: str = "exec_memory_packet_latest.json",
    output_md_name: str = "exec_memory_packet_latest.md",
    extra_args: list[str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    loop_path = context_dir / "loop_cycle_summary_latest.json"
    dossier_path = context_dir / "auditor_promotion_dossier.json"
    calibration_path = context_dir / "auditor_calibration_report.json"
    go_signal_path = context_dir / "ceo_go_signal.md"
    decision_log_path = tmp_path / "docs" / "decision log.md"
    output_json_path = context_dir / output_json_name
    output_md_path = context_dir / output_md_name
    status_json_path = context_dir / "exec_memory_packet_build_status_latest.json"

    if loop_summary is not None:
        _write_json(loop_path, loop_summary)
    if dossier is not None:
        _write_json(dossier_path, dossier)
    if calibration is not None:
        _write_json(calibration_path, calibration)
    if go_signal is not None:
        _write_text(go_signal_path, go_signal)
    if decision_log is not None:
        _write_text(decision_log_path, decision_log)
    if milestone_roster is not None:
        _write_json(context_dir / "milestone_expert_roster_latest.json", milestone_roster)

    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--context-dir",
        str(context_dir),
        "--loop-summary-json",
        str(loop_path),
        "--dossier-json",
        str(dossier_path),
        "--calibration-json",
        str(calibration_path),
        "--go-signal-md",
        str(go_signal_path),
        "--decision-log-md",
        str(decision_log_path),
        "--pm-budget-tokens",
        str(pm_budget),
        "--ceo-budget-tokens",
        str(ceo_budget),
        "--output-json",
        str(output_json_path),
        "--output-md",
        str(output_md_path),
        "--status-json",
        str(status_json_path),
    ]
    if extra_args:
        command.extend(extra_args)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    return result, output_json_path, output_md_path


# ---------------------------------------------------------------------------
# Success path tests
# ---------------------------------------------------------------------------


def test_success_path_generates_json_and_markdown(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json_path.exists()
    assert md_path.exists()
    status_payload = json.loads(
        (json_path.parent / "exec_memory_packet_build_status_latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert status_payload["authoritative_latest_written"] is True
    assert status_payload["reason"] == "ok"

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    assert packet["schema_version"] == "1.0.0"
    assert "generated_at_utc" in packet
    assert "hierarchical_summary" in packet
    assert "retrieval_namespaces" in packet
    assert "token_budget" in packet
    assert "source_bindings" in packet
    assert "semantic_claims" in packet
    assert isinstance(packet["semantic_claims"], list)
    assert packet["milestone_expert_roster_status"]["status"] == "ROSTER_MISSING"
    assert packet["inputs"]["milestone_expert_roster"] == "docs/context/milestone_expert_roster_latest.json"
    assert "replanning" in packet
    assert packet["replanning"]["status"] in {"CLEAR", "ACTION_REQUIRED"}
    assert "next_round_handoff" in packet
    assert packet["next_round_handoff"]["advisory"] is True
    assert "expert_request" in packet
    assert packet["expert_request"]["advisory"] is True
    assert packet["expert_request"]["status"] == "ACTION_REQUIRED"
    assert packet["expert_request"]["target_expert"] == "unknown"
    assert packet["expert_request"]["roster_fit"] == "ROSTER_MISSING"
    assert packet["expert_request"]["board_reentry_required"] is True
    assert "BOARD_LINEUP_REVIEW_REQUIRED" in packet["expert_request"]["board_reentry_reason_codes"]
    assert "question" in packet["expert_request"]
    assert "decision_depends_on" in packet["expert_request"]
    assert "source_artifacts" in packet["expert_request"]
    assert "DECISION_DEPENDS_ON:" in packet["expert_request"]["paste_ready_block"]
    assert "pm_ceo_research_brief" in packet
    assert packet["pm_ceo_research_brief"]["advisory"] is True
    assert packet["pm_ceo_research_brief"]["status"] == "ACTION_REQUIRED"
    assert packet["pm_ceo_research_brief"]["delegated_to"] == "principal"
    assert packet["pm_ceo_research_brief"]["lineup_review_required"] is True
    assert packet["pm_ceo_research_brief"]["candidate_new_domains"] == []
    assert "question" in packet["pm_ceo_research_brief"]
    assert "decision_depends_on" in packet["pm_ceo_research_brief"]
    assert "source_artifacts" in packet["pm_ceo_research_brief"]
    assert "DECISION_DEPENDS_ON:" in packet["pm_ceo_research_brief"]["paste_ready_block"]
    assert "board_decision_brief" in packet
    assert packet["board_decision_brief"]["advisory"] is True
    assert packet["board_decision_brief"]["lineup_decision_needed"] is True
    assert packet["board_decision_brief"]["lineup_gap_domains"] == []
    assert packet["milestone_expert_roster_status"]["status"] == "ROSTER_MISSING"
    for section_name, required_fields in (
        (
            "next_round_handoff",
            (
                "status",
                "recommended_intent",
                "recommended_scope",
                "done_when",
                "human_brief",
                "machine_view",
                "paste_ready_block",
            ),
        ),
        (
            "expert_request",
            (
                "status",
                "target_expert",
                "requested_domain",
                "roster_fit",
                "board_reentry_required",
                "board_reentry_reason_codes",
                "milestone_id",
                "question",
                "decision_depends_on",
                "human_brief",
                "machine_view",
                "paste_ready_block",
            ),
        ),
        (
            "pm_ceo_research_brief",
            (
                "status",
                "delegated_to",
                "question",
                "decision_depends_on",
                "lineup_review_required",
                "lineup_review_reason_codes",
                "approved_roster_snapshot",
                "human_brief",
                "machine_view",
                "paste_ready_block",
            ),
        ),
        (
            "board_decision_brief",
            (
                "status",
                "decision_topic",
                "decision_class",
                "risk_tier",
                "recommended_option",
                "lineup_decision_needed",
                "board_reentry_reason_codes",
                "approved_roster_snapshot",
                "reintroduce_board_when",
                "human_brief",
                "machine_view",
                "paste_ready_block",
            ),
        ),
    ):
        section = packet[section_name]
        for field_name in required_fields:
            value = section.get(field_name)
            assert value not in ("", [], None), f"{section_name}.{field_name}"
    assert "candidate_new_domains" in packet["pm_ceo_research_brief"]
    assert isinstance(packet["pm_ceo_research_brief"]["candidate_new_domains"], list)
    assert "lineup_gap_domains" in packet["board_decision_brief"]
    assert isinstance(packet["board_decision_brief"]["lineup_gap_domains"], list)

    md_content = md_path.read_text(encoding="utf-8")
    assert "## Next Round Handoff" in md_content
    assert "## Expert Request" in md_content
    assert "## PM/CEO Research Brief" in md_content
    assert "## Board Decision Brief" in md_content
    assert md_content.count("### Human Brief") >= 4
    assert md_content.count("### Machine View") >= 4
    assert md_content.count("### Paste-Ready Block") >= 4
    assert "EXPERT_LINEUP_STATUS:" in md_content
    assert "BOARD_MEMORY_STATUS:" in md_content


def test_hierarchical_summary_structure(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    hs = packet["hierarchical_summary"]

    assert "working_summary" in hs
    assert "issue_summary" in hs
    assert "daily_pm_summary" in hs
    assert "weekly_ceo_summary" in hs

    # Check content from loop schema fields
    assert "Run ID: 20260304_000545" in hs["working_summary"]
    assert "Final result: HOLD" in hs["working_summary"]
    assert "Steps total: 6" in hs["working_summary"]
    assert "Step outcomes: PASS=4, HOLD=1, FAIL=1, ERROR=0, SKIP=0" in hs["working_summary"]
    assert "UNKNOWN" not in hs["working_summary"]
    assert "critical" in hs["issue_summary"]
    assert "Working Context" in hs["daily_pm_summary"]
    assert "CEO Go Signal" in hs["weekly_ceo_summary"]


def test_hierarchical_summary_prefers_canonical_step_summary_keys(tmp_path: Path) -> None:
    loop_summary = _make_loop_summary()
    loop_summary["step_summary"] = {
        "pass_count": 9,
        "hold_count": 2,
        "fail_count": 3,
        "error_count": 1,
        "skip_count": 4,
        "total_steps": 19,
        # legacy keys intentionally conflicting; canonical values must win
        "pass": 4,
        "hold": 1,
        "fail": 1,
        "error": 0,
        "skip": 0,
        "total": 6,
    }

    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=loop_summary,
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    working_summary = packet["hierarchical_summary"]["working_summary"]
    assert "Steps total: 19" in working_summary
    assert "Step outcomes: PASS=9, HOLD=2, FAIL=3, ERROR=1, SKIP=4" in working_summary


def test_semantic_claims_have_source_bindings_and_summary_match(tmp_path: Path) -> None:
    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    claims = packet["semantic_claims"]
    source_bindings = packet["source_bindings"]
    hs = packet["hierarchical_summary"]
    summary_sections = [
        hs["working_summary"],
        hs["issue_summary"],
        hs["daily_pm_summary"],
        hs["weekly_ceo_summary"],
    ]

    assert claims, "semantic_claims should not be empty on success path"
    for claim in claims:
        assert {"claim_id", "text", "source_path"} <= set(claim.keys())
        assert claim["source_path"] in source_bindings
        assert any(claim["text"] in section for section in summary_sections)


def test_retrieval_namespaces_structure(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    ns = packet["retrieval_namespaces"]

    # Check all 4 namespaces exist
    assert "governance" in ns
    assert "operations" in ns
    assert "risk" in ns
    assert "roadmap" in ns

    # Check governance has sources
    assert len(ns["governance"]) > 0
    assert any("decision" in s["source"].lower() for s in ns["governance"])

    # Check operations has loop summary
    assert len(ns["operations"]) > 0
    assert any("loop_cycle" in s["source"] for s in ns["operations"])

    # Check risk has auditor reports
    assert len(ns["risk"]) > 0


def test_memory_tier_contract_uses_shared_mapping(tmp_path: Path) -> None:
    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    contract = packet["memory_tier_contract"]
    bindings = packet["memory_tier_bindings"]

    assert contract["source_of_truth"] == "scripts/utils/memory_tiers.py"
    assert contract["documentation"] == "docs/memory_tier_contract.md"

    families = {item["family"]: item for item in contract["families"]}
    assert families["loop_cycle_summary"]["tier"] == "hot"
    assert families["exec_memory_packet"]["tier"] == "hot"
    assert families["next_round_handoff"]["tier"] == "warm"
    assert families["skill_activation"]["tier"] == "warm"

    cold = {item["family"]: item for item in contract["cold_manual_fallbacks"]}
    assert cold["auditor_fp_ledger"]["tier"] == "cold"
    assert cold["auditor_fp_ledger"]["access"] == "manual_fallback"

    input_bindings = {item["family"]: item for item in bindings["inputs"]}
    output_bindings = {item["family"]: item for item in bindings["outputs"]}
    assert input_bindings["loop_cycle_summary"]["tier"] == "hot"
    assert input_bindings["auditor_promotion_dossier"]["tier"] == "warm"
    assert input_bindings["decision_log"]["tier"] == "warm"
    assert output_bindings["exec_memory_packet"]["tier"] == "hot"
    assert output_bindings["board_decision_brief"]["tier"] == "warm"


def test_compaction_retention_contract_protects_handoff_surfaces(tmp_path: Path) -> None:
    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    contract = packet["compaction_retention_contract"]

    assert contract["source_of_truth"] == "scripts/utils/compaction_retention.py"
    assert contract["documentation"] == "docs/compaction_behavior_contract.md"

    required_always = {row["packet_section"] for row in contract["required_always"]}
    required_if_present = {row["packet_section"] for row in contract["required_if_present"]}
    cold_manual = {row["surface"] for row in contract["cold_manual_fallback"]}

    assert required_always == {
        "next_round_handoff",
        "expert_request",
        "pm_ceo_research_brief",
        "board_decision_brief",
    }
    assert required_if_present == {"replanning", "automation_uncertainty_status"}
    assert cold_manual == {"auditor_fp_ledger"}

    for protected_section in required_always:
        assert protected_section in packet
        assert packet[protected_section] is not None


def test_token_budget_tracking(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    tb = packet["token_budget"]

    assert "pm_budget" in tb
    assert "ceo_budget" in tb
    assert "pm_actual" in tb
    assert "ceo_actual" in tb
    assert "pm_budget_ok" in tb
    assert "ceo_budget_ok" in tb

    assert tb["pm_budget"] == 3000
    assert tb["ceo_budget"] == 1800
    assert isinstance(tb["pm_actual"], int)
    assert isinstance(tb["ceo_actual"], int)
    assert isinstance(tb["pm_budget_ok"], bool)
    assert isinstance(tb["ceo_budget_ok"], bool)


def test_markdown_companion_format(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    md_content = md_path.read_text(encoding="utf-8")

    assert "# Exec Memory Packet" in md_content
    assert "## Token Budget" in md_content
    assert "## Source Bindings" in md_content
    assert "## Replanning" in md_content
    assert "## Retrieval Namespaces" in md_content
    assert "### governance" in md_content
    assert "### operations" in md_content
    assert "### risk" in md_content
    assert "### roadmap" in md_content


# ---------------------------------------------------------------------------
# Missing critical input tests
# ---------------------------------------------------------------------------


def test_missing_loop_summary_fails(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=None,  # Missing critical input
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 2, "Should fail with exit code 2 for missing critical input"
    assert "Critical input missing or invalid" in result.stderr
    assert not json_path.exists()
    assert not md_path.exists()
    status_payload = json.loads(
        (json_path.parent / "exec_memory_packet_build_status_latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert status_payload["authoritative_latest_written"] is False
    assert status_payload["reason"] == "critical_inputs_failed"


def test_missing_go_signal_fails(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=None,  # Missing critical input
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 2, "Should fail with exit code 2 for missing critical input"
    assert "Critical input missing or invalid" in result.stderr
    assert not json_path.exists()
    assert not md_path.exists()
    status_payload = json.loads(
        (json_path.parent / "exec_memory_packet_build_status_latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert status_payload["authoritative_latest_written"] is False
    assert status_payload["reason"] == "critical_inputs_failed"


def test_missing_optional_inputs_succeeds(tmp_path: Path) -> None:
    """Important and optional input degradation stays visible but non-fatal."""
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=None,
        calibration=None,
        go_signal=_make_go_signal(),
        decision_log=None,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json_path.exists()

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    assert "hierarchical_summary" in packet


def test_replanning_section_captures_blocking_gaps_and_recommendation(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_hold_go_signal(),
        decision_log=_make_decision_log(),
    )

    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    replanning = packet["replanning"]

    assert replanning["blocking_gap_count"] >= 3
    assert replanning["status"] == "ACTION_REQUIRED"
    assert any(gap["code"] == "c3_min_weeks" for gap in replanning["blocking_gaps"])
    assert any(gap["code"] == "blocking_reason" for gap in replanning["blocking_gaps"])
    assert replanning["next_replan_recommendation"].startswith(
        "Address final_result:HOLD from loop_cycle_summary"
    )

    md_content = md_path.read_text(encoding="utf-8")
    assert "BlockingGapCount" in md_content
    assert "NextReplanRecommendation" in md_content
    assert "[auditor_promotion_dossier] c3_min_weeks" in md_content


# ---------------------------------------------------------------------------
# Budget overflow tests
# ---------------------------------------------------------------------------


def test_budget_overflow_flags_and_truncates(tmp_path: Path) -> None:
    # Create very large content to exceed budget
    large_decision_log = "Decision: " + ("X" * 50000)

    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=large_decision_log,
        pm_budget=100,  # Very small budget
        ceo_budget=100,
    )

    # Should exit 1 when budget exceeded
    assert result.returncode == 1, "Should fail with exit code 1 when budget exceeded"
    assert "Token budget exceeded" in result.stderr

    # But files should still be written
    assert json_path.exists()
    packet = json.loads(json_path.read_text(encoding="utf-8"))

    tb = packet["token_budget"]
    assert tb["pm_budget_ok"] is False or tb["ceo_budget_ok"] is False

    # Check truncation marker
    hs = packet["hierarchical_summary"]
    assert "[TRUNCATED]" in hs["daily_pm_summary"] or "[TRUNCATED]" in hs["weekly_ceo_summary"]


def test_budget_ok_when_within_limits(tmp_path: Path) -> None:
    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
        pm_budget=10000,  # Large budget
        ceo_budget=10000,
    )

    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    tb = packet["token_budget"]

    assert tb["pm_budget_ok"] is True
    assert tb["ceo_budget_ok"] is True
    assert tb["pm_actual"] <= tb["pm_budget"]
    assert tb["ceo_actual"] <= tb["ceo_budget"]


def test_markdown_shows_budget_status(tmp_path: Path) -> None:
    # Create large content to ensure budget overflow
    large_decision_log = "Decision: " + ("X" * 50000)

    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=large_decision_log,
        pm_budget=100,  # Small budget to trigger overflow
        ceo_budget=100,
    )

    assert result.returncode == 1

    md_content = md_path.read_text(encoding="utf-8")
    # Should show OVER status for at least one budget
    assert "[FAIL] OVER" in md_content


def test_replanning_summary_tracks_gap_sources_and_next_action(tmp_path: Path) -> None:
    calibration = _make_calibration()
    calibration["fp_analysis"] = {"ch_unannotated": 3}
    dossier = _make_dossier()
    dossier["promotion_criteria"]["c1_24b_close"] = {
        "met": "MANUAL_CHECK",
        "value": "MANUAL_CHECK",
    }

    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=dossier,
        calibration=calibration,
        go_signal=_make_hold_go_signal(),
        decision_log=_make_decision_log(),
    )

    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    replanning = packet["replanning"]
    handoff = packet["next_round_handoff"]
    expert_request = packet["expert_request"]
    research_brief = packet["pm_ceo_research_brief"]
    board_brief = packet["board_decision_brief"]
    uncertainty = packet["automation_uncertainty_status"]

    assert replanning["status"] == "ACTION_REQUIRED"
    assert replanning["observed_loop_final_result"] == "HOLD"
    assert replanning["observed_go_action"] == "HOLD"
    assert replanning["blocking_gap_count"] >= 4
    assert "docs/context/loop_cycle_summary_latest.json" in replanning["recommended_artifacts_to_refresh"]
    assert "docs/context/auditor_promotion_dossier.json" in replanning["recommended_artifacts_to_refresh"]
    assert "docs/context/auditor_calibration_report.json" in replanning["recommended_artifacts_to_refresh"]
    assert "docs/context/ceo_go_signal.md" in replanning["recommended_artifacts_to_refresh"]
    assert any(gap["code"] == "fp_unannotated" for gap in replanning["blocking_gaps"])
    assert any(gap["code"] == "c1_24b_close" for gap in replanning["blocking_gaps"])
    assert replanning["next_replan_recommendation"].startswith("Annotate the remaining Critical/High findings")
    assert handoff["status"] == "ACTION_REQUIRED"
    assert handoff["observed_go_action"] == "HOLD"
    assert handoff["primary_blockers"][0] == "fp_unannotated"
    assert "go_signal_action_gate" in handoff["recommended_done_when_checks"]
    assert "freshness_gate" in handoff["recommended_done_when_checks"]
    assert "docs/context/auditor_calibration_report.json" in handoff["artifacts_to_refresh"]
    assert handoff["machine_view"].startswith("SURFACE: next_round_handoff")
    assert "Status ACTION_REQUIRED." in handoff["human_brief"]
    assert "HANDOFF_MODE: ADVISORY_EXEC_MEMORY_PACKET" in handoff["paste_ready_block"]
    assert "ORIGINAL_INTENT: Close annotation-driven promotion blockers before the next escalation attempt." in handoff["paste_ready_block"]
    assert expert_request["status"] == "ACTION_REQUIRED"
    assert expert_request["requested_domain"] == "riskops"
    assert expert_request["target_expert"] == "unknown"
    assert expert_request["roster_fit"] == "ROSTER_MISSING"
    assert expert_request["board_reentry_required"] is True
    assert "ROSTER_MISSING" in expert_request["board_reentry_reason_codes"]
    assert "BOARD_LINEUP_REVIEW_REQUIRED" in expert_request["board_reentry_reason_codes"]
    assert "go_signal_action_gate" in expert_request["decision_depends_on"]
    assert "docs/context/auditor_calibration_report.json" in expert_request["source_artifacts"]
    assert "QUESTION:" in expert_request["paste_ready_block"]
    assert "DECISION_DEPENDS_ON:" in expert_request["paste_ready_block"]
    assert research_brief["status"] == "ACTION_REQUIRED"
    assert research_brief["delegated_to"] == "principal"
    assert research_brief["decision_depends_on"] == expert_request["decision_depends_on"]
    assert "docs/context/auditor_calibration_report.json" in research_brief["source_artifacts"]
    assert "QUESTION:" in research_brief["paste_ready_block"]
    assert "SOURCE_ARTIFACTS:" in research_brief["paste_ready_block"]
    assert research_brief["lineup_review_required"] is True
    assert "BOARD_LINEUP_REVIEW_REQUIRED" in research_brief["lineup_review_reason_codes"]
    assert board_brief["advisory"] is True
    assert board_brief["status"] == "ACTION_REQUIRED"
    assert board_brief["decision_class"] == "ONE_WAY"
    assert board_brief["risk_tier"] == "HIGH"
    assert "docs/context/auditor_calibration_report.json" in board_brief["source_artifacts"]
    assert board_brief["expert_lens"]["target_expert"] == "unknown"
    assert board_brief["lineup_decision_needed"] is True
    assert "BOARD_LINEUP_REVIEW_REQUIRED" in board_brief["board_reentry_reason_codes"]
    assert any("fp_unannotated" in risk for risk in board_brief["open_risks"])
    assert "BOARD_DECISION_BRIEF_MODE: ADVISORY_EXEC_MEMORY_PACKET" in board_brief["paste_ready_block"]
    assert "ADVISORY_NOTE: Generated from existing exec memory artifacts; board-style lenses are advisory only and do not change decision authority." in board_brief["paste_ready_block"]
    assert uncertainty["status"] == "ACTION_REQUIRED"
    assert uncertainty["machine_confidence"] == "LIMITED"
    assert uncertainty["evidence_status"] == "INSUFFICIENT"
    assert uncertainty["machine_safe_to_continue"] is False
    assert uncertainty["human_help_needed"] is True
    assert uncertainty["expert_help_needed"] is True
    assert uncertainty["target_expert"] == "unknown"
    assert uncertainty["expert_lineup_status"] == "ROSTER_MISSING"
    assert uncertainty["expert_memory_status"] == "MISSING"
    assert uncertainty["board_memory_status"] == "BOARD_LINEUP_REVIEW_REQUIRED"
    assert uncertainty["board_reentry_required"] is True
    assert "ROSTER_MISSING" in uncertainty["reason_codes"]
    assert "BOARD_LINEUP_REVIEW_REQUIRED" in uncertainty["reason_codes"]
    assert uncertainty["boundary_registry"] == "docs/automation_boundary_registry.md"
    assert "ACTIVE_BLOCKERS" in uncertainty["reason_codes"]
    assert "EXPERT_INPUT_REQUIRED" in uncertainty["reason_codes"]

    md_content = md_path.read_text(encoding="utf-8")
    assert "## Automation Uncertainty Status" in md_content
    assert "AUTOMATION_UNCERTAINTY_STATUS: ACTION_REQUIRED" in md_content
    assert "## Replanning" in md_content
    assert "BlockingGapCount:" in md_content
    assert "NextReplanRecommendation:" in md_content
    assert "## Next Round Handoff" in md_content
    assert "## Expert Request" in md_content
    assert "## PM/CEO Research Brief" in md_content
    assert "## Board Decision Brief" in md_content
    assert "DecisionDependsOn:" in md_content
    assert "BOARD_DECISION_BRIEF_MODE: ADVISORY_EXEC_MEMORY_PACKET" in md_content
    assert "HANDOFF_MODE: ADVISORY_EXEC_MEMORY_PACKET" in md_content


def test_expert_assignment_uses_milestone_roster_when_present(tmp_path: Path) -> None:
    calibration = _make_calibration()
    calibration["fp_analysis"] = {"ch_unannotated": 2}
    dossier = _make_dossier()
    dossier["promotion_criteria"]["c1_24b_close"] = {
        "met": "MANUAL_CHECK",
        "value": "MANUAL_CHECK",
    }

    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=dossier,
        calibration=calibration,
        go_signal=_make_hold_go_signal(),
        decision_log=_make_decision_log(),
        milestone_roster=_make_milestone_roster(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    packet = json.loads(json_path.read_text(encoding="utf-8"))
    expert_request = packet["expert_request"]
    research_brief = packet["pm_ceo_research_brief"]
    board_brief = packet["board_decision_brief"]
    uncertainty = packet["automation_uncertainty_status"]

    assert packet["milestone_expert_roster_status"]["status"] == "ROSTER_READY"
    assert packet["inputs"]["milestone_expert_roster"] == "docs/context/milestone_expert_roster_latest.json"
    assert "docs/context/milestone_expert_roster_latest.json" in packet["source_bindings"]
    assert any(
        entry["source"] == "docs/context/milestone_expert_roster_latest.json"
        for entry in packet["retrieval_namespaces"]["governance"]
    )
    assert expert_request["status"] == "ACTION_REQUIRED"
    assert expert_request["requested_domain"] == "riskops"
    assert expert_request["target_expert"] == "riskops"
    assert expert_request["roster_fit"] == "IN_ROSTER"
    assert expert_request["board_reentry_required"] is False
    assert expert_request["board_reentry_reason_codes"] == []
    assert research_brief["lineup_review_required"] is False
    assert research_brief["lineup_review_reason_codes"] == []
    assert board_brief["lineup_decision_needed"] is False
    assert board_brief["board_reentry_reason_codes"] == []
    assert uncertainty["expert_lineup_status"] == "ROSTER_READY"
    assert uncertainty["expert_memory_status"] == "CONSISTENT"
    assert uncertainty["board_memory_status"] == "CONSISTENT"
    assert uncertainty["board_reentry_required"] is False


def test_next_round_handoff_is_clear_and_advisory_when_no_blockers(tmp_path: Path) -> None:
    loop_summary = {
        "run_id": "20260307_010101",
        "final_result": "PASS",
        "step_summary": {
            "pass": 3,
            "hold": 0,
            "fail": 0,
            "error": 0,
            "skip": 0,
            "total": 3,
        },
        "steps": [
            {"step_id": "G00", "status": "PASS"},
            {"step_id": "G01", "status": "PASS"},
            {"step_id": "G02", "status": "PASS"},
        ],
    }
    dossier = {
        "schema_version": "1.0.0",
        "report_type": "dossier",
        "promotion_criteria": {
            "c0_infra_health": {"met": True, "value": "0 failures"},
            "c1_24b_close": {"met": True, "value": "APPROVED"},
        },
    }
    calibration = {
        "schema_version": "1.0.0",
        "report_type": "weekly",
        "totals": {
            "items_reviewed": 10,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        },
        "fp_analysis": {"ch_unannotated": 0},
    }

    result, json_path, md_path = _run_script(
        tmp_path,
        loop_summary=loop_summary,
        dossier=dossier,
        calibration=calibration,
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )

    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    handoff = packet["next_round_handoff"]
    expert_request = packet["expert_request"]
    research_brief = packet["pm_ceo_research_brief"]
    board_brief = packet["board_decision_brief"]
    uncertainty = packet["automation_uncertainty_status"]

    assert handoff["advisory"] is True
    assert handoff["status"] == "CLEAR"
    assert handoff["recommended_done_when_checks"] == ["startup_gate_status"]
    assert handoff["artifacts_to_refresh"] == []
    assert handoff["primary_blockers"] == []
    assert handoff["machine_view"].startswith("SURFACE: next_round_handoff")
    assert "Status CLEAR." in handoff["human_brief"]
    assert "HANDOFF_STATUS: CLEAR" in handoff["paste_ready_block"]
    assert "ADVISORY_NOTE: Generated from current exec memory artifacts; startup interrogation remains authoritative before execution." in handoff["paste_ready_block"]
    assert expert_request["status"] == "OPTIONAL"
    assert expert_request["target_expert"] == "qa"
    assert expert_request["requested_domain"] == "qa"
    assert expert_request["roster_fit"] == "ROSTER_MISSING"
    assert expert_request["board_reentry_required"] is False
    assert "startup_gate_status" in expert_request["decision_depends_on"]
    assert expert_request["source_artifacts"] == []
    assert research_brief["status"] == "OPTIONAL"
    assert research_brief["delegated_to"] == "principal"
    assert "startup_gate_status" in research_brief["decision_depends_on"]
    assert research_brief["source_artifacts"] == []
    assert board_brief["advisory"] is True
    assert board_brief["status"] == "OPTIONAL"
    assert board_brief["decision_class"] == "TWO_WAY"
    assert board_brief["risk_tier"] == "LOW"
    assert board_brief["source_artifacts"] == []
    assert board_brief["expert_lens"]["target_expert"] == "qa"
    assert board_brief["open_risks"] == ["none"]
    assert "BOARD_DECISION_BRIEF_MODE: ADVISORY_EXEC_MEMORY_PACKET" in board_brief["paste_ready_block"]
    assert uncertainty["status"] == "CLEAR"
    assert uncertainty["machine_confidence"] == "SUFFICIENT"
    assert uncertainty["evidence_status"] == "SUFFICIENT"
    assert uncertainty["machine_safe_to_continue"] is True
    assert uncertainty["human_help_needed"] is False
    assert uncertainty["expert_help_needed"] is False
    assert uncertainty["target_expert"] == "none"
    assert uncertainty["expert_lineup_status"] == "ROSTER_MISSING"
    assert uncertainty["expert_memory_status"] == "MISSING"
    assert uncertainty["board_memory_status"] == "CONSISTENT"
    assert uncertainty["boundary_registry"] == "docs/automation_boundary_registry.md"

    md_content = md_path.read_text(encoding="utf-8")
    assert "## Board Decision Brief" in md_content
    assert "### Human Brief" in md_content
    assert "### Machine View" in md_content
    assert md_content.count("### Paste-Ready Block") >= 4
    assert "HANDOFF_STATUS: CLEAR" in md_content
    assert "BOARD_DECISION_BRIEF_MODE: ADVISORY_EXEC_MEMORY_PACKET" in md_content


# ---------------------------------------------------------------------------
# Deterministic token estimation tests
# ---------------------------------------------------------------------------


def test_token_estimation_deterministic(tmp_path: Path) -> None:
    """Run twice with same inputs, should get same token counts."""
    result1, json_path1, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result1.returncode == 0

    packet1 = json.loads(json_path1.read_text(encoding="utf-8"))

    # Run again
    result2, json_path2, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result2.returncode == 0

    packet2 = json.loads(json_path2.read_text(encoding="utf-8"))

    # Token counts should be identical
    assert packet1["token_budget"]["pm_actual"] == packet2["token_budget"]["pm_actual"]
    assert packet1["token_budget"]["ceo_actual"] == packet2["token_budget"]["ceo_actual"]


def test_explicit_uncertainty_metadata_is_nonempty_when_emitted(tmp_path: Path) -> None:
    calibration = _make_calibration()
    calibration["fp_analysis"] = {"ch_unannotated": 2}

    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=calibration,
        go_signal=_make_hold_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    emitted = _collect_explicit_uncertainty_metadata(packet)
    if not emitted:
        pytest.skip("Explicit uncertainty metadata is not emitted by the current packet builder.")

    for section_name, field_name, value in emitted:
        assert value, f"{section_name}.{field_name} must be non-empty when emitted"
        normalized = value.upper()
        if normalized in {"CLEAR", "ACTION_REQUIRED", "OPTIONAL"}:
            assert normalized != "CLEAR", (
                f"{section_name}.{field_name} should not contradict the action-required hold scenario"
            )


def test_boundary_registry_doc_is_bound_when_emitted(tmp_path: Path) -> None:
    _write_text(
        tmp_path / "docs" / "automation_boundary_registry.md",
        "# Automation Boundary Registry\n",
    )

    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )
    assert result.returncode == 0, result.stdout + result.stderr

    packet = json.loads(json_path.read_text(encoding="utf-8"))
    refs = _collect_boundary_registry_references(packet)
    if not refs:
        pytest.skip("Boundary registry doc is not emitted by the current packet builder.")

    for ref in refs:
        resolved = Path(ref)
        if not resolved.is_absolute():
            resolved = tmp_path / ref
        assert resolved.exists(), f"Boundary registry reference must resolve: {ref}"


# ---------------------------------------------------------------------------
# Input degradation tracking tests
# ---------------------------------------------------------------------------


def test_critical_input_missing_fails(tmp_path: Path) -> None:
    """Test that missing critical input (loop summary) causes exit code 2."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Create all files EXCEPT loop summary (critical)
    dossier_path = context_dir / "auditor_promotion_dossier.json"
    calibration_path = context_dir / "auditor_calibration_report.json"
    go_signal_path = context_dir / "ceo_go_signal.md"
    decision_log_path = tmp_path / "docs" / "decision log.md"
    output_json_path = context_dir / "exec_memory_packet_latest.json"
    output_md_path = context_dir / "exec_memory_packet_latest.md"
    status_json_path = context_dir / "exec_memory_packet_build_status_latest.json"

    # Missing: loop_summary_path
    loop_path = context_dir / "loop_cycle_summary_latest.json"

    _write_json(dossier_path, _make_dossier())
    _write_json(calibration_path, _make_calibration())
    _write_text(go_signal_path, _make_go_signal())
    _write_text(decision_log_path, _make_decision_log())

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--context-dir",
            str(context_dir),
            "--loop-summary-json",
            str(loop_path),  # Points to missing file
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--go-signal-md",
            str(go_signal_path),
            "--decision-log-md",
            str(decision_log_path),
            "--output-json",
            str(output_json_path),
            "--output-md",
            str(output_md_path),
            "--status-json",
            str(status_json_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}. stderr: {result.stderr}"
    assert "Critical input missing or invalid" in result.stderr

    assert not output_json_path.exists()
    assert not output_md_path.exists()
    status_payload = json.loads(status_json_path.read_text(encoding="utf-8"))
    assert status_payload["authoritative_latest_written"] is False
    assert status_payload["critical_inputs_ok"] is False
    assert status_payload["reason"] == "critical_inputs_failed"


def test_critical_input_missing_writes_only_non_authoritative_preview(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    dossier_path = context_dir / "auditor_promotion_dossier.json"
    calibration_path = context_dir / "auditor_calibration_report.json"
    go_signal_path = context_dir / "ceo_go_signal.md"
    decision_log_path = tmp_path / "docs" / "decision log.md"

    _write_json(dossier_path, _make_dossier())
    _write_json(calibration_path, _make_calibration())
    _write_text(go_signal_path, _make_go_signal())
    _write_text(decision_log_path, _make_decision_log())

    result, output_json_path, output_md_path = _run_script(
        tmp_path,
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
        output_json_name="exec_memory_packet_current.json",
        output_md_name="exec_memory_packet_current.md",
        extra_args=["--allow-degraded-output"],
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert output_json_path.exists()
    assert output_md_path.exists()
    status_payload = json.loads(
        (context_dir / "exec_memory_packet_build_status_latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert status_payload["authoritative_latest_written"] is False
    assert status_payload["degraded_preview_written"] is True
    assert status_payload["reason"] == "critical_inputs_failed_degraded_preview_only"

    packet = json.loads(output_json_path.read_text(encoding="utf-8"))
    critical_failures = [
        item for item in packet["input_status"]["critical"] if item["status"] == "missing_or_invalid"
    ]
    assert [item["file"] for item in critical_failures] == ["loop_cycle_summary_latest.json"]

    assert not (context_dir / "exec_memory_packet_latest.json").exists()
    assert not (context_dir / "exec_memory_packet_latest.md").exists()


def test_important_input_missing_warns(tmp_path: Path) -> None:
    """Test that missing important input (dossier) warns but succeeds with degradation tracking."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Create critical files but NOT dossier (important)
    loop_path = context_dir / "loop_cycle_summary_latest.json"
    dossier_path = context_dir / "auditor_promotion_dossier.json"  # Will be missing
    calibration_path = context_dir / "auditor_calibration_report.json"
    go_signal_path = context_dir / "ceo_go_signal.md"
    decision_log_path = tmp_path / "docs" / "decision log.md"
    output_json_path = context_dir / "exec_memory_packet_latest.json"
    output_md_path = context_dir / "exec_memory_packet_latest.md"
    status_json_path = context_dir / "exec_memory_packet_build_status_latest.json"

    _write_json(loop_path, _make_loop_summary())
    # Missing: dossier
    _write_json(calibration_path, _make_calibration())
    _write_text(go_signal_path, _make_go_signal())
    _write_text(decision_log_path, _make_decision_log())

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--context-dir",
            str(context_dir),
            "--loop-summary-json",
            str(loop_path),
            "--dossier-json",
            str(dossier_path),  # Points to missing file
            "--calibration-json",
            str(calibration_path),
            "--go-signal-md",
            str(go_signal_path),
            "--decision-log-md",
            str(decision_log_path),
            "--output-json",
            str(output_json_path),
            "--output-md",
            str(output_md_path),
            "--status-json",
            str(status_json_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Should succeed with exit code 0
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}"

    # Should have warning in stderr
    assert "WARNING: Important input degraded" in result.stderr

    # Check output JSON has input_status with degradation info
    assert output_json_path.exists()
    status_payload = json.loads(status_json_path.read_text(encoding="utf-8"))
    assert status_payload["authoritative_latest_written"] is True
    assert status_payload["critical_inputs_ok"] is True
    packet = json.loads(output_json_path.read_text(encoding="utf-8"))

    assert "input_status" in packet
    input_status = packet["input_status"]

    # Check structure
    assert "critical" in input_status
    assert "important" in input_status
    assert "optional" in input_status

    # Check that dossier is marked as missing in important
    important_missing = [
        item for item in input_status["important"] if item["status"] == "missing_or_invalid"
    ]
    assert len(important_missing) > 0, "Expected at least one important input to be missing"

    dossier_missing = [item for item in important_missing if "dossier" in item["file"].lower()]
    assert len(dossier_missing) == 1, f"Expected dossier to be missing, got: {important_missing}"


def test_all_inputs_loaded_success(tmp_path: Path) -> None:
    """Test that when all inputs are present, input_status reflects loaded state."""
    result, json_path, _ = _run_script(
        tmp_path,
        loop_summary=_make_loop_summary(),
        dossier=_make_dossier(),
        calibration=_make_calibration(),
        go_signal=_make_go_signal(),
        decision_log=_make_decision_log(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json_path.exists()

    packet = json.loads(json_path.read_text(encoding="utf-8"))

    assert "input_status" in packet
    input_status = packet["input_status"]

    # Check that critical inputs are loaded
    critical_loaded = [item for item in input_status["critical"] if item["status"] == "loaded"]
    assert len(critical_loaded) == 2, f"Expected 2 critical inputs loaded, got {len(critical_loaded)}"

    # Check that important inputs are loaded
    important_loaded = [item for item in input_status["important"] if item["status"] == "loaded"]
    assert len(important_loaded) == 2, f"Expected 2 important inputs loaded, got {len(important_loaded)}"

    # No missing critical inputs
    critical_missing = [
        item for item in input_status["critical"] if item["status"] == "missing_or_invalid"
    ]
    assert len(critical_missing) == 0, f"Expected no critical inputs missing, got {critical_missing}"

    optional_loaded = [item for item in input_status["optional"] if item["status"] == "loaded"]
    assert any(item["file"] == "decision log.md" for item in optional_loaded)


def test_skill_activation_section_present(tmp_path):
    """Test that skill_activation section is present in exec memory packet."""
    context_dir = tmp_path / "docs" / "context"
    context_dir.mkdir(parents=True)

    loop_summary_path = context_dir / "loop_cycle_summary_latest.json"
    _write_json(loop_summary_path, _make_loop_summary())

    go_signal_path = context_dir / "ceo_go_signal.md"
    _write_text(go_signal_path, "# CEO Go Signal\n\nApproved for Phase 4.\n")

    decision_log_path = tmp_path / "docs" / "decision log.md"
    _write_text(decision_log_path, "# Decision Log\n\n## D-001\n\nApproved.\n")

    # Create skill governance files
    sop_config_path = tmp_path / ".sop_config.yaml"
    _write_text(sop_config_path, "project_name: test_project\nactive_skills:\n  - test-skill\n")

    allowlist_path = tmp_path / "extension_allowlist.yaml"
    _write_text(
        allowlist_path,
        "skills:\n  - skill_name: test-skill\n    version: 1.0.0\n    status: active\n    applicable_projects:\n      - all\n"
    )

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    registry_path = skills_dir / "registry.yaml"
    _write_text(
        registry_path,
        "skills:\n  - name: test-skill\n    version: 1.0.0\n    category: testing\n"
    )

    output_json = context_dir / "exec_memory_packet_latest.json"
    output_md = context_dir / "exec_memory_packet_latest.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--context-dir",
            str(context_dir),
            "--loop-summary-json",
            str(loop_summary_path),
            "--go-signal-md",
            str(go_signal_path),
            "--decision-log-md",
            str(decision_log_path),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert output_json.exists()

    packet = json.loads(output_json.read_text(encoding="utf-8"))
    assert "skill_activation" in packet

    skill_activation = packet["skill_activation"]
    assert "status" in skill_activation
    assert "skills" in skill_activation
    assert "warnings" in skill_activation
    assert "errors" in skill_activation
    assert isinstance(skill_activation["skills"], list)
