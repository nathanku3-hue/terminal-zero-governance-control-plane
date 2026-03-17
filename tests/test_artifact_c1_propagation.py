"""Integration test: C1 APPROVED propagates from dossier to artifacts."""

from pathlib import Path
import json
import subprocess
import sys

def test_approved_dossier_propagates_to_exec_memory(tmp_path: Path) -> None:
    """When dossier shows C1 APPROVED, exec memory must not show MANUAL_CHECK."""

    # Create temp context dir with approved dossier
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    # Write approved dossier fixture
    dossier = {
        "schema_version": "1.0.0",
        "promotion_criteria": {
            "c0_infra_health": {"met": True, "value": "0 failures"},
            "c1_24b_close": {
                "met": True,
                "value": "APPROVED",
                "decision_id": "D-174",
                "decision_date": "2026-03-16"
            },
            "c2_min_items": {"met": True, "value": "72 >= 30"},
            "c3_min_weeks": {"met": True, "value": "2 consecutive weeks"},
            "c4_fp_rate": {"met": True, "value": "0.00%"},
            "c4b_annotation_coverage": {"met": True, "value": "100.00%"},
            "c5_all_v2": {"met": True, "value": "1 versions: ['2.0.0']"}
        }
    }
    (context_dir / "auditor_promotion_dossier.json").write_text(
        json.dumps(dossier, indent=2)
    )

    # Write GO signal fixture
    go_signal = """# CEO GO Signal

- Phase: Phase 24C
- Generated: 2026-03-16T13:37:26Z
- Recommended Action: GO

## Dossier Criteria

| Criterion | Status | Value |
|---|---|---|
| C0 | PASS | 0 failures |
| C1 | PASS | APPROVED |
| C2 | PASS | 72 >= 30 |
| C3 | PASS | 2 consecutive weeks |
| C4 | PASS | 0.00% |
| C4b | PASS | 100.00% |
| C5 | PASS | 1 versions: ['2.0.0'] |
"""
    (context_dir / "ceo_go_signal.md").write_text(go_signal)

    # Write minimal required inputs (avoid dependency on repo-local fixtures)
    (context_dir / "loop_cycle_summary_latest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "run_id": "TEST-RUN",
                "final_result": "PASS",
                "steps": [],
                "step_summary": {
                    "pass_count": 0,
                    "hold_count": 0,
                    "fail_count": 0,
                    "error_count": 0,
                    "skip_count": 0,
                    "total_steps": 0,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (context_dir / "auditor_calibration_report.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "totals": {"items_reviewed": 0, "critical": 0, "high": 0},
                "fp_analysis": {"ch_unannotated": 0},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Optional input (build_exec_memory_packet.py handles missing roster gracefully).
    (context_dir / "milestone_expert_roster_latest.json").write_text(
        json.dumps({"schema_version": "1.0.0", "all_domains": []}, indent=2),
        encoding="utf-8",
    )

    # build_exec_memory_packet.py derives repo_root from decision_log_path.parent.parent
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "decision log.md").write_text(
        "# Decision Log\n\n- (test fixture)\n",
        encoding="utf-8",
    )

    # Minimal files so skill resolver can load YAML without failing hard.
    # (Skill activation is fail-soft but missing YAML makes it 'failed'.)
    (tmp_path / ".sop_config.yaml").write_text(
        "project_name: quant_current_scope\nactive_skills: []\n",
        encoding="utf-8",
    )
    (tmp_path / "extension_allowlist.yaml").write_text(
        "skills: []\n",
        encoding="utf-8",
    )

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "registry.yaml").write_text("skills: []\n", encoding="utf-8")

    # Generate exec memory packet
    output_json = context_dir / "exec_memory_packet_latest.json"
    output_md = context_dir / "exec_memory_packet_latest.md"
    status_json = context_dir / "exec_memory_packet_build_status_latest.json"

    result = subprocess.run([
        sys.executable,
        "scripts/build_exec_memory_packet.py",
        "--loop-summary-json", str(context_dir / "loop_cycle_summary_latest.json"),
        "--dossier-json", str(context_dir / "auditor_promotion_dossier.json"),
        "--calibration-json", str(context_dir / "auditor_calibration_report.json"),
        "--go-signal-md", str(context_dir / "ceo_go_signal.md"),
        "--decision-log-md", str(docs_dir / "decision log.md"),
        "--context-dir", str(context_dir),
        "--output-json", str(output_json),
        "--output-md", str(output_md),
        "--status-json", str(status_json)
    ], capture_output=True, text=True)

    assert result.returncode == 0, f"Generator failed: {result.stderr}"

    # Verify exec memory packet does not contain MANUAL_CHECK
    packet = json.loads(output_json.read_text())
    packet_str = json.dumps(packet)

    assert "MANUAL_CHECK" not in packet_str, \
        "Exec memory packet must not contain MANUAL_CHECK when dossier shows C1 APPROVED"

    # Verify replanning section does not list C1 as a gap
    replanning = packet.get("replanning", {})
    gaps = replanning.get("blocking_gaps", [])

    c1_gaps = [g for g in gaps if "c1_24b_close" in str(g).lower()]
    assert len(c1_gaps) == 0, \
        f"Replanning must not list C1 as blocking gap when APPROVED: {c1_gaps}"


def test_manual_check_dossier_emits_manual_action(tmp_path: Path) -> None:
    """When dossier shows C1 MANUAL_CHECK, supervisor must emit manual_signoff_c1 action."""

    # Create temp context dir with MANUAL_CHECK dossier
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    # Write MANUAL_CHECK dossier fixture
    dossier = {
        "schema_version": "1.0.0",
        "promotion_criteria": {
            "c0_infra_health": {"met": True, "value": "0 failures"},
            "c1_24b_close": {"met": "MANUAL_CHECK", "value": "MANUAL_CHECK"},
            "c2_min_items": {"met": True, "value": "72 >= 30"},
            "c3_min_weeks": {"met": True, "value": "2 consecutive weeks"},
            "c4_fp_rate": {"met": True, "value": "0.00%"},
            "c4b_annotation_coverage": {"met": True, "value": "100.00%"},
            "c5_all_v2": {"met": True, "value": "1 versions: ['2.0.0']"}
        }
    }
    (context_dir / "auditor_promotion_dossier.json").write_text(
        json.dumps(dossier, indent=2)
    )

    # Write HOLD GO signal fixture
    go_signal = """# CEO GO Signal

- Phase: Phase 24C
- Generated: 2026-03-16T13:37:26Z
- Recommended Action: HOLD

## Dossier Criteria

| Criterion | Status | Value |
|---|---|---|
| C0 | PASS | 0 failures |
| C1 | MANUAL_CHECK | MANUAL_CHECK |
| C2 | PASS | 72 >= 30 |
"""
    (context_dir / "ceo_go_signal.md").write_text(go_signal)

    # Write minimal required loop artifacts (avoid dependency on repo-local fixtures)
    (context_dir / "loop_cycle_summary_latest.json").write_text(
        json.dumps({"schema_version": "1.0.0"}, indent=2),
        encoding="utf-8",
    )
    (context_dir / "loop_closure_status_latest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "result": "READY_TO_ESCALATE",
                "checks": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Round contract is a required supervisor input
    (context_dir / "round_contract_latest.md").write_text(
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DECISION_CLASS: TWO_WAY",
                "- RISK_TIER: MEDIUM",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Generate supervisor status
    result = subprocess.run([
        sys.executable,
        "scripts/supervise_loop.py",
        "--repo-root", str(tmp_path),
        "--context-dir", str(context_dir),
        "--check-interval-seconds", "0",
        "--max-cycles", "1"
    ], capture_output=True, text=True)

    assert result.returncode == 0, f"Supervisor failed: {result.stderr}"

    # Verify supervisor status contains manual_signoff_c1 action
    status_json = context_dir / "supervisor_status_latest.json"
    assert status_json.exists(), "Supervisor must write supervisor_status_latest.json"

    status = json.loads(status_json.read_text(encoding="utf-8"))
    manual_actions = status.get("manual_actions", [])

    c1_actions = [a for a in manual_actions if a.get("id") == "manual_signoff_c1"]
    assert len(c1_actions) > 0, \
        "Supervisor must emit manual_signoff_c1 action when C1 is MANUAL_CHECK"
