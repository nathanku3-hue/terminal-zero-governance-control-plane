from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_round_contract_checks.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(round_md: Path, loop_json: Path, closure_json: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--round-contract-md",
            str(round_md),
            "--loop-summary-json",
            str(loop_json),
            "--closure-json",
            str(closure_json),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_round_contract_checks_passes_when_declared_checks_exist(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    loop_json = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    closure_json = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"

    _write_text(
        round_md,
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DONE_WHEN_CHECKS: refresh_dossier, go_signal_action_gate",
                "",
            ]
        ),
    )
    _write_json(loop_json, {"steps": [{"name": "refresh_dossier"}]})
    _write_json(closure_json, {"checks": [{"name": "go_signal_action_gate"}]})

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] DONE_WHEN_CHECKS validation passed." in result.stdout


def test_round_contract_checks_accepts_current_cycle_summary_schema(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    round_md = context_dir / "round_contract_latest.md"
    loop_json = context_dir / "loop_cycle_summary_current.json"
    closure_json = context_dir / "loop_closure_status_latest.json"

    _write_text(
        round_md,
        "\n".join(
            [
                "# Round Contract",
                "",
                "- DONE_WHEN_CHECKS: refresh_dossier, go_signal_action_gate",
                "",
            ]
        ),
    )
    _write_json(
        loop_json,
        {
            "schema_version": "1.0.0",
            "generated_at_utc": "2026-03-09T00:00:00Z",
            "repo_root": str(tmp_path),
            "context_dir": str(context_dir),
            "scripts_dir": str(tmp_path / "scripts"),
            "skip_phase_end": True,
            "allow_hold": True,
            "freshness_hours": 72.0,
            "step_summary": {
                "pass_count": 2,
                "hold_count": 0,
                "fail_count": 0,
                "error_count": 0,
                "skip_count": 1,
                "total_steps": 3,
            },
            "steps": [
                {"name": "phase_end_handover", "status": "SKIP"},
                {"name": "refresh_dossier", "status": "PASS"},
                {"name": "validate_loop_closure", "status": "PASS"},
            ],
            "disagreement_ledger_sla": {
                "path": str(context_dir / "disagreement_ledger.jsonl"),
                "exists": False,
                "total_entries": 0,
                "unresolved_entries": 0,
                "overdue_unresolved_count": 0,
                "overdue_unresolved": [],
                "parse_errors": [],
            },
            "lessons": {
                "worker": str(context_dir / "lessons_worker_latest.md"),
                "auditor": str(context_dir / "lessons_auditor_latest.md"),
            },
            "artifacts": {
                "weekly_report_json": str(context_dir / "auditor_calibration_report.json"),
                "weekly_report_md": str(context_dir / "auditor_calibration_report.md"),
                "dossier_json": str(context_dir / "auditor_promotion_dossier.json"),
                "dossier_md": str(context_dir / "auditor_promotion_dossier.md"),
                "go_signal_md": str(context_dir / "ceo_go_signal.md"),
                "weekly_summary_md": str(context_dir / "ceo_weekly_summary_latest.md"),
                "review_checklist_md": str(context_dir / "pr_review_checklist_latest.md"),
                "interface_contract_manifest_json": str(context_dir / "interface_contract_manifest_latest.json"),
                "exec_memory_json": str(context_dir / "exec_memory_packet_latest.json"),
                "exec_memory_md": str(context_dir / "exec_memory_packet_latest.md"),
                "next_round_handoff_json": str(context_dir / "next_round_handoff_latest.json"),
                "next_round_handoff_md": str(context_dir / "next_round_handoff_latest.md"),
                "expert_request_json": str(context_dir / "expert_request_latest.json"),
                "expert_request_md": str(context_dir / "expert_request_latest.md"),
                "pm_ceo_research_brief_json": str(context_dir / "pm_ceo_research_brief_latest.json"),
                "pm_ceo_research_brief_md": str(context_dir / "pm_ceo_research_brief_latest.md"),
                "board_decision_brief_json": str(context_dir / "board_decision_brief_latest.json"),
                "board_decision_brief_md": str(context_dir / "board_decision_brief_latest.md"),
                "compaction_state_json": str(context_dir / "context_compaction_state_latest.json"),
                "compaction_status_json": str(context_dir / "context_compaction_status_latest.json"),
                "closure_output_json": str(closure_json),
                "closure_output_md": str(context_dir / "loop_closure_status_latest.md"),
                "summary_output_json": str(context_dir / "loop_cycle_summary_latest.json"),
                "summary_output_md": str(context_dir / "loop_cycle_summary_latest.md"),
            },
            "next_round_handoff": None,
            "expert_request": None,
            "pm_ceo_research_brief": None,
            "board_decision_brief": None,
            "repo_root_convenience": {},
            "final_result": "PASS",
            "final_exit_code": 0,
        },
    )
    _write_json(closure_json, {"checks": [{"name": "go_signal_action_gate"}]})

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] DONE_WHEN_CHECKS validation passed." in result.stdout


def test_round_contract_checks_fails_on_unknown_id(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    loop_json = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    closure_json = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"

    _write_text(round_md, "- DONE_WHEN_CHECKS: does_not_exist\n")
    _write_json(loop_json, {"steps": [{"name": "refresh_dossier"}]})
    _write_json(closure_json, {"checks": [{"name": "go_signal_action_gate"}]})

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 1
    assert "Unknown DONE_WHEN_CHECKS ids: does_not_exist" in (result.stdout + result.stderr)


def test_round_contract_checks_fails_on_empty_list(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    loop_json = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    closure_json = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"

    _write_text(round_md, "- DONE_WHEN_CHECKS:   \n")
    _write_json(loop_json, {"steps": [{"name": "refresh_dossier"}]})
    _write_json(closure_json, {"checks": [{"name": "go_signal_action_gate"}]})

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 1
    assert "DONE_WHEN_CHECKS must declare a non-empty check list." in (result.stdout + result.stderr)


def test_round_contract_checks_returns_exit_2_on_missing_inputs(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    loop_json = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    closure_json = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"

    _write_text(round_md, "- DONE_WHEN_CHECKS: refresh_dossier\n")
    _write_json(loop_json, {"steps": [{"name": "refresh_dossier"}]})
    # closure_json intentionally missing

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 2
    assert "Missing input file" in (result.stdout + result.stderr)


def test_round_contract_checks_returns_exit_2_on_malformed_json(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    loop_json = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    closure_json = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"

    _write_text(round_md, "- DONE_WHEN_CHECKS: refresh_dossier\n")
    _write_json(loop_json, {"steps": [{"name": "refresh_dossier"}]})
    closure_json.parent.mkdir(parents=True, exist_ok=True)
    closure_json.write_text("{ invalid json", encoding="utf-8")

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 2
    assert "Invalid JSON" in (result.stdout + result.stderr)


def test_large_change_scope_requires_boundary_and_manifest_refs(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    loop_json = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    closure_json = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"

    _write_text(
        round_md,
        "\n".join(
            [
                "# Round Contract",
                "- DECISION_CLASS: ONE_WAY",
                "- RISK_TIER: HIGH",
                "- CHANGE_BUDGET: 5 files, 1 architecture changes",
                "- DONE_WHEN_CHECKS: refresh_dossier",
                "",
            ]
        ),
    )
    _write_json(loop_json, {"steps": [{"name": "refresh_dossier"}]})
    _write_json(closure_json, {"checks": []})

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 1
    output = result.stdout + result.stderr
    assert "LOGIC_SPINE_INDEX_ARTIFACT" in output
    assert "CHANGE_MANIFEST_ARTIFACT" in output
    assert "ALLOWED_BOUNDARY_REFS" in output
    assert "NON_GOAL_REFS" in output


def test_large_change_scope_passes_with_boundary_and_manifest_refs(tmp_path: Path) -> None:
    round_md = tmp_path / "docs" / "context" / "round_contract_latest.md"
    loop_json = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    closure_json = tmp_path / "docs" / "context" / "loop_closure_status_latest.json"
    logic_spine = tmp_path / "docs" / "context" / "logic_spine_index_latest.md"
    change_manifest = tmp_path / "docs" / "context" / "change_manifest_latest.json"
    logic_spine.parent.mkdir(parents=True, exist_ok=True)
    logic_spine.write_text("# logic spine\n", encoding="utf-8")
    change_manifest.write_text("{\"changes\": []}\n", encoding="utf-8")

    _write_text(
        round_md,
        "\n".join(
            [
                "# Round Contract",
                "- DECISION_CLASS: ONE_WAY",
                "- RISK_TIER: HIGH",
                "- CHANGE_BUDGET: 5 files, 1 architecture changes",
                f"- LOGIC_SPINE_INDEX_ARTIFACT: {logic_spine}",
                f"- CHANGE_MANIFEST_ARTIFACT: {change_manifest}",
                "- ALLOWED_BOUNDARY_REFS: docs/spec.md#scope,docs/phase_brief/phase24-brief.md",
                "- NON_GOAL_REFS: docs/round_contract_template.md#non-goals",
                "- DONE_WHEN_CHECKS: refresh_dossier",
                "",
            ]
        ),
    )
    _write_json(loop_json, {"steps": [{"name": "refresh_dossier"}]})
    _write_json(closure_json, {"checks": []})

    result = _run(round_md, loop_json, closure_json)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] DONE_WHEN_CHECKS validation passed." in result.stdout
