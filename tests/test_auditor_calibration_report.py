"""Tests for scripts/auditor_calibration_report.py"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts import auditor_calibration_report

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "auditor_calibration_report.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_json_with_bom(path: Path, payload: dict) -> None:
    """Write JSON with UTF-8 BOM (regression guard for Fix 2)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8-sig")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _decision_log_with_d174() -> str:
    return """# Decision Log

| ID | Component | The Friction Point | The Decision (Hardcoded) | Rationale |
|------|-----------|---------------------|--------------------------|-----------|
| D-174 | governance/phase24c | C1 PM signoff for Phase 24C enforce promotion | PM signoff granted for Phase 24C enforce promotion. | Satisfies C1 manual signoff requirement. Enables enforce promotion path once C3 automated blocker clears. Date: 2026-03-16. |
"""


def _make_findings(
    run_id: str,
    mode: str = "shadow",
    timestamp: str = "2026-03-01T12:00:00Z",
    findings_list: list | None = None,
    items_reviewed: int = 10,
    schema_version: str = "2.0.0",
) -> dict:
    return {
        "schema_version": "1.0.0",
        "auditor_id": "auditor-v1",
        "audit_timestamp_utc": timestamp,
        "mode": mode,
        "reviewed_packet_path": "docs/context/worker_reply_packet.json",
        "reviewed_packet_schema_version": schema_version,
        "findings": findings_list or [],
        "summary": {
            "total_findings": len(findings_list or []),
            "items_reviewed": items_reviewed,
            "critical": sum(1 for f in (findings_list or []) if f.get("severity") == "CRITICAL"),
            "high": sum(1 for f in (findings_list or []) if f.get("severity") == "HIGH"),
            "medium": sum(1 for f in (findings_list or []) if f.get("severity") == "MEDIUM"),
            "low": sum(1 for f in (findings_list or []) if f.get("severity") == "LOW"),
            "info": sum(1 for f in (findings_list or []) if f.get("severity") == "INFO"),
            "gate_verdict": "PASS",
            "infra_error": False,
        },
    }

def _make_status(
    run_id: str,
    gates: list | None = None,
    started_utc: str = "2026-03-01T12:00:00Z",
) -> dict:
    return {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "started_utc": started_utc,
        "ended_utc": "2026-03-01T12:01:00Z",
        "result": "PASS",
        "gates": gates or [],
    }


def _make_gate(
    gate_name: str,
    status: str = "PASS",
    exit_code: int = 0,
    command: str = "",
) -> dict:
    return {
        "gate": gate_name,
        "status": status,
        "exit_code": exit_code,
        "command": command,
        "log_path": f"/tmp/{gate_name}.log",
        "started_utc": "2026-03-01T12:00:00Z",
        "ended_utc": "2026-03-01T12:01:00Z",
        "message": "",
    }


def _run_calibration(
    logs_dir: Path,
    repo_id: str = "test_repo",
    ledger_path: Path | None = None,
    mode: str = "weekly",
    from_utc: str | None = None,
    to_utc: str | None = None,
    min_items: int = 30,
    min_items_per_week: int = 10,
    min_weeks: int = 2,
    max_fp_rate: float = 0.05,
    decision_log_path: Path | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict, str]:
    output_json = logs_dir / "report.json"
    output_md = logs_dir / "report.md"

    args = [
        sys.executable,
        str(SCRIPT_PATH),
        "--logs-dir", str(logs_dir),
        "--repo-id", repo_id,
        "--output-json", str(output_json),
        "--output-md", str(output_md),
        "--mode", mode,
        "--min-items", str(min_items),
        "--min-items-per-week", str(min_items_per_week),
        "--min-weeks", str(min_weeks),
        "--max-fp-rate", str(max_fp_rate),
    ]
    
    if ledger_path:
        args.extend(["--ledger", str(ledger_path)])
    if decision_log_path:
        args.extend(["--decision-log-md", str(decision_log_path)])
    if from_utc:
        args.extend(["--from-utc", from_utc])
    if to_utc:
        args.extend(["--to-utc", to_utc])
    
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    
    report = {}
    if output_json.exists():
        report = json.loads(output_json.read_text(encoding="utf-8"))
    
    md_content = ""
    if output_md.exists():
        md_content = output_md.read_text(encoding="utf-8")
    
    return result, report, md_content


# ---------------------------------------------------------------------------
# Basic weekly reports
# ---------------------------------------------------------------------------

def test_weekly_report_no_findings_files(tmp_path: Path) -> None:
    """Empty logs dir produces empty report."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    result, report, _ = _run_calibration(logs_dir)
    
    assert result.returncode == 0
    assert report["data_range"]["runs_included"] == 0
    assert report["totals"]["items_reviewed"] == 0


def test_weekly_report_single_run(tmp_path: Path) -> None:
    """Single run with findings produces correct totals."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    findings = [
        {"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"},
        {"finding_id": "F2", "rule_id": "R001", "severity": "HIGH"},
        {"finding_id": "F3", "rule_id": "R002", "severity": "MEDIUM"},
    ]
    
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", findings_list=findings, items_reviewed=50),
    )
    
    gates = [_make_gate("G11_auditor_review", command="--mode shadow")]
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=gates),
    )
    
    result, report, _ = _run_calibration(logs_dir)
    
    assert result.returncode == 0
    assert report["data_range"]["runs_included"] == 1
    assert report["totals"]["items_reviewed"] == 50
    assert report["totals"]["critical"] == 1
    assert report["totals"]["high"] == 1
    assert report["totals"]["medium"] == 1
    assert "R001" in report["per_rule_breakdown"]
    assert report["per_rule_breakdown"]["R001"]["total"] == 2


def test_weekly_report_multiple_runs_across_weeks(tmp_path: Path) -> None:
    """Multiple runs across 2 weeks aggregate correctly."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Week 1: 2026-W09 (March 1)
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", timestamp="2026-03-01T12:00:00Z", items_reviewed=20),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )
    
    # Week 2: 2026-W10 (March 8)
    _write_json(
        logs_dir / "auditor_findings_20260308_120000.json",
        _make_findings("20260308_120000", timestamp="2026-03-08T12:00:00Z", items_reviewed=30),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260308_120000.json",
        _make_status("20260308_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )
    
    result, report, _ = _run_calibration(logs_dir)
    
    assert result.returncode == 0
    assert report["data_range"]["runs_included"] == 2
    assert report["totals"]["items_reviewed"] == 50
    assert len(report["weekly_windows"]) == 2
    assert "2026-W09" in report["weekly_windows"]
    assert "2026-W10" in report["weekly_windows"]
    assert report["weekly_windows"]["2026-W09"]["items"] == 20
    assert report["weekly_windows"]["2026-W10"]["items"] == 30


# ---------------------------------------------------------------------------
# Run cohort filtering
# ---------------------------------------------------------------------------

def test_run_cohort_skips_no_g11(tmp_path: Path) -> None:
    """Status with G11 SKIPPED excluded from cohort."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000"),
    )
    
    gates = [_make_gate("G11_auditor_review", status="SKIPPED")]
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=gates),
    )
    
    result, report, _ = _run_calibration(logs_dir)
    
    assert result.returncode == 0
    assert report["data_range"]["runs_included"] == 0


def test_run_cohort_shadow_only(tmp_path: Path) -> None:
    """Only shadow runs included, enforce excluded."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Shadow run
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", mode="shadow"),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )
    
    # Enforce run
    _write_json(
        logs_dir / "auditor_findings_20260302_120000.json",
        _make_findings("20260302_120000", mode="enforce"),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260302_120000.json",
        _make_status("20260302_120000", gates=[_make_gate("G11_auditor_review", command="--mode enforce")]),
    )
    
    result, report, _ = _run_calibration(logs_dir)
    
    assert result.returncode == 0
    assert report["data_range"]["runs_included"] == 1


def test_run_cohort_unpaired_findings_warn_weekly(tmp_path: Path) -> None:
    """Findings without status warns in weekly, doesn't increment infra_failures."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000"),
    )
    # No matching status file
    
    result, report, _ = _run_calibration(logs_dir, mode="weekly")
    
    assert result.returncode == 0
    assert "WARNING" in result.stderr
    assert report["data_range"]["runs_included"] == 0


def test_run_cohort_unpaired_findings_infra_dossier(tmp_path: Path) -> None:
    """Findings without status is infra failure in dossier."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000"),
    )
    # No matching status file
    
    result, report, _ = _run_calibration(logs_dir, mode="dossier", min_items=0)
    
    assert result.returncode == 1  # Dossier criteria not met
    assert report["promotion_criteria"]["c0_infra_health"]["met"] is False


def test_run_cohort_unpaired_status_infra_dossier(tmp_path: Path) -> None:
    """Status with G11 shadow executed but no findings is infra failure in dossier."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    gates = [_make_gate("G11_auditor_review", command="-AuditMode shadow")]
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=gates),
    )
    # No matching findings file
    
    result, report, _ = _run_calibration(logs_dir, mode="dossier", min_items=0)
    
    assert result.returncode == 1
    assert report["promotion_criteria"]["c0_infra_health"]["met"] is False


def test_run_cohort_unpaired_status_weekly_warn_only(tmp_path: Path) -> None:
    """Status with G11 shadow executed but no findings warns in weekly, no infra increment."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    gates = [_make_gate("G11_auditor_review", command="-AuditMode shadow")]
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=gates),
    )
    
    result, report, _ = _run_calibration(logs_dir, mode="weekly")
    
    assert result.returncode == 0
    assert "WARNING" in result.stderr


# ---------------------------------------------------------------------------
# BOM encoding test (Fix 2 regression guard)
# ---------------------------------------------------------------------------

def test_status_file_with_utf8_bom(tmp_path: Path) -> None:
    """Status files with UTF-8 BOM are loaded correctly."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", items_reviewed=25),
    )
    
    gates = [_make_gate("G11_auditor_review", command="--mode shadow")]
    _write_json_with_bom(  # Write with BOM
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=gates),
    )
    
    result, report, _ = _run_calibration(logs_dir)
    
    assert result.returncode == 0
    assert report["data_range"]["runs_included"] == 1
    assert report["totals"]["items_reviewed"] == 25


# ---------------------------------------------------------------------------
# C3 consecutive weeks logic (Fix 3 validation)
# ---------------------------------------------------------------------------

def test_dossier_c3_consecutive_weeks_pass(tmp_path: Path) -> None:
    """C3 passes with 2 consecutive weeks meeting min items."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Week 1: 2026-W09
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", timestamp="2026-03-01T12:00:00Z", items_reviewed=15),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Week 2: 2026-W10 (consecutive)
    _write_json(
        logs_dir / "auditor_findings_20260308_120000.json",
        _make_findings("20260308_120000", timestamp="2026-03-08T12:00:00Z", items_reviewed=20),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260308_120000.json",
        _make_status("20260308_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    result, report, _ = _run_calibration(logs_dir, mode="dossier", min_items=30, min_items_per_week=10, min_weeks=2)

    assert result.returncode == 0
    assert report["promotion_criteria"]["c3_min_weeks"]["met"] is True
    assert "2 consecutive weeks" in report["promotion_criteria"]["c3_min_weeks"]["value"]


def test_dossier_c1_derives_pass_from_d174_decision_log(tmp_path: Path) -> None:
    """C1 resolves to PASS/APPROVED when D-174 is present in decision log."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    decision_log_path = tmp_path / "docs" / "decision log.md"
    _write_text(decision_log_path, _decision_log_with_d174())

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", timestamp="2026-03-01T12:00:00Z", items_reviewed=15),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )
    _write_json(
        logs_dir / "auditor_findings_20260308_120000.json",
        _make_findings("20260308_120000", timestamp="2026-03-08T12:00:00Z", items_reviewed=20),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260308_120000.json",
        _make_status("20260308_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    result, report, md_content = _run_calibration(
        logs_dir,
        mode="dossier",
        min_items=30,
        min_items_per_week=10,
        min_weeks=2,
        decision_log_path=decision_log_path,
    )

    assert result.returncode == 0
    assert report["promotion_criteria"]["c1_24b_close"]["met"] is True
    assert report["promotion_criteria"]["c1_24b_close"]["value"] == "APPROVED"
    assert report["promotion_criteria"]["c1_24b_close"]["decision_id"] == "D-174"
    assert "| c1_24b_close | [OK] | APPROVED |" in md_content


def test_dossier_c3_non_consecutive_weeks_fail(tmp_path: Path) -> None:
    """C3 fails when weeks are not consecutive."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Week 1: 2026-W09
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", timestamp="2026-03-01T12:00:00Z", items_reviewed=15),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Week 3: 2026-W11 (gap, not consecutive)
    _write_json(
        logs_dir / "auditor_findings_20260315_120000.json",
        _make_findings("20260315_120000", timestamp="2026-03-15T12:00:00Z", items_reviewed=20),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260315_120000.json",
        _make_status("20260315_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    result, report, _ = _run_calibration(logs_dir, mode="dossier", min_items=30, min_items_per_week=10, min_weeks=2)

    assert result.returncode == 1
    assert report["promotion_criteria"]["c3_min_weeks"]["met"] is False


def test_dossier_c0_infra_failure_g11_exit2(tmp_path: Path) -> None:
    """C0 fails when G11 exit_code=2 (infra error)."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", items_reviewed=50),
    )

    gates = [_make_gate("G11_auditor_review", exit_code=2, command="--mode shadow")]
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=gates),
    )

    result, report, _ = _run_calibration(logs_dir, mode="dossier", min_items=30)

    assert result.returncode == 1
    assert report["promotion_criteria"]["c0_infra_health"]["met"] is False


def test_dossier_c0_ignores_policy_block(tmp_path: Path) -> None:
    """C0 passes when G11 exit_code=1 (policy block, not infra)."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", mode="enforce", items_reviewed=50),
    )

    gates = [_make_gate("G11_auditor_review", exit_code=1, command="--mode enforce")]
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=gates),
    )

    result, report, _ = _run_calibration(logs_dir, mode="dossier", min_items=30)

    # Run excluded from shadow cohort (enforce mode), so 0 runs
    assert result.returncode == 1  # C2 fails (0 items < 30)
    assert report["promotion_criteria"]["c0_infra_health"]["met"] is True


def test_dossier_c4b_annotation_coverage_fail(tmp_path: Path) -> None:
    """C4b fails when not all C/H findings annotated."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"

    findings = [
        {"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"},
        {"finding_id": "F2", "rule_id": "R001", "severity": "HIGH"},
    ]

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", findings_list=findings, items_reviewed=50),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Only 1 of 2 C/H annotated
    _write_json(ledger_path, {
        "schema_version": "1.0.0",
        "annotations": [
            {"repo_id": "test_repo", "run_id": "20260301_120000", "finding_id": "F1", "verdict": "TP", "annotated_by": "user", "annotated_at_utc": "2026-03-01T13:00:00Z"},
        ],
    })

    result, report, _ = _run_calibration(logs_dir, ledger_path=ledger_path, mode="dossier", min_items=30)

    assert result.returncode == 1
    assert report["promotion_criteria"]["c4b_annotation_coverage"]["met"] is False
    assert report["fp_analysis"]["annotation_coverage_ch"] == 0.5


def test_markdown_output_exists(tmp_path: Path) -> None:
    """Markdown report is generated with expected structure."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000"),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    result, _, md_content = _run_calibration(logs_dir)

    assert result.returncode == 0
    assert "# Auditor Calibration Report" in md_content
    assert "## Summary" in md_content
    assert "## FP Analysis" in md_content


def test_infra_error_missing_dir(tmp_path: Path) -> None:
    """Exit 2 when logs dir doesn't exist."""
    logs_dir = tmp_path / "nonexistent"

    result, _, _ = _run_calibration(logs_dir)

    assert result.returncode == 2
    assert "ERROR" in result.stderr


# ---------------------------------------------------------------------------
# Gap fixes: timestamp validation, UNKNOWN week, invalid verdict
# ---------------------------------------------------------------------------

def test_infra_error_invalid_from_utc(tmp_path: Path) -> None:
    """Exit 2 when --from-utc is invalid timestamp."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    result, _, _ = _run_calibration(logs_dir, from_utc="not-a-date")

    assert result.returncode == 2
    assert "ERROR" in result.stderr
    assert "Invalid --from-utc" in result.stderr


def test_infra_error_invalid_to_utc(tmp_path: Path) -> None:
    """Exit 2 when --to-utc is invalid timestamp."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    result, _, _ = _run_calibration(logs_dir, to_utc="2026-99-99T00:00:00Z")

    assert result.returncode == 2
    assert "ERROR" in result.stderr
    assert "Invalid --to-utc" in result.stderr


def test_dossier_c3_unknown_week_no_crash(tmp_path: Path) -> None:
    """C3 handles UNKNOWN week bucket without crashing."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Run with bad timestamp (UNKNOWN week)
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", timestamp="invalid", items_reviewed=15),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Run with valid timestamp (2026-W10)
    _write_json(
        logs_dir / "auditor_findings_20260308_120000.json",
        _make_findings("20260308_120000", timestamp="2026-03-08T12:00:00Z", items_reviewed=20),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260308_120000.json",
        _make_status("20260308_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    result, report, _ = _run_calibration(logs_dir, mode="dossier", min_items=30, min_items_per_week=10, min_weeks=2)

    # Should not crash, but C3 fails (only 1 valid week)
    assert result.returncode == 1
    assert report["promotion_criteria"]["c3_min_weeks"]["met"] is False
    assert "UNKNOWN" in report["weekly_windows"]


def test_ledger_invalid_verdict_ignored(tmp_path: Path) -> None:
    """Annotations with invalid verdict are ignored."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"

    findings = [
        {"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"},
        {"finding_id": "F2", "rule_id": "R001", "severity": "HIGH"},
    ]

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", findings_list=findings, items_reviewed=50),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Ledger with invalid verdict "MAYBE"
    _write_json(ledger_path, {
        "schema_version": "1.0.0",
        "annotations": [
            {"repo_id": "test_repo", "run_id": "20260301_120000", "finding_id": "F1", "verdict": "MAYBE", "annotated_by": "user", "annotated_at_utc": "2026-03-01T13:00:00Z"},
            {"repo_id": "test_repo", "run_id": "20260301_120000", "finding_id": "F2", "verdict": "TP", "annotated_by": "user", "annotated_at_utc": "2026-03-01T13:00:00Z"},
        ],
    })

    result, report, _ = _run_calibration(logs_dir, ledger_path=ledger_path, mode="dossier", min_items=30)

    # Only 1 of 2 annotations valid (F2), so coverage = 0.5
    assert result.returncode == 1
    assert report["fp_analysis"]["ch_annotated"] == 1
    assert report["fp_analysis"]["annotation_coverage_ch"] == 0.5
    assert report["promotion_criteria"]["c4b_annotation_coverage"]["met"] is False
    assert "WARNING" in result.stderr
    assert "invalid verdict" in result.stderr


def test_ledger_valid_verdicts_only(tmp_path: Path) -> None:
    """Only TP and FP verdicts are accepted."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"

    findings = [
        {"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"},
    ]

    # Week 1
    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", timestamp="2026-03-01T12:00:00Z", findings_list=findings, items_reviewed=20),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Week 2
    _write_json(
        logs_dir / "auditor_findings_20260308_120000.json",
        _make_findings("20260308_120000", timestamp="2026-03-08T12:00:00Z", findings_list=findings, items_reviewed=20),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260308_120000.json",
        _make_status("20260308_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Ledger with valid TP verdicts (both TP to pass FP rate)
    _write_json(ledger_path, {
        "schema_version": "1.0.0",
        "annotations": [
            {"repo_id": "test_repo", "run_id": "20260301_120000", "finding_id": "F1", "verdict": "TP", "annotated_by": "user", "annotated_at_utc": "2026-03-01T13:00:00Z"},
            {"repo_id": "test_repo", "run_id": "20260308_120000", "finding_id": "F1", "verdict": "TP", "annotated_by": "user", "annotated_at_utc": "2026-03-08T13:00:00Z"},
        ],
    })

    result, report, _ = _run_calibration(logs_dir, ledger_path=ledger_path, mode="dossier", min_items=30, min_items_per_week=10, min_weeks=2)

    assert result.returncode == 0
    assert report["fp_analysis"]["ch_annotated"] == 2
    assert report["fp_analysis"]["annotation_coverage_ch"] == 1.0
    assert report["promotion_criteria"]["c4b_annotation_coverage"]["met"] is True


# ---------------------------------------------------------------------------
# Final gap fixes: malformed ledger keys, weekly schema warning
# ---------------------------------------------------------------------------

def test_infra_error_ledger_missing_repo_id(tmp_path: Path) -> None:
    """Exit 2 when ledger annotation missing repo_id."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"

    findings = [{"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"}]

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", findings_list=findings, items_reviewed=50),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Ledger with missing repo_id
    _write_json(ledger_path, {
        "schema_version": "1.0.0",
        "annotations": [
            {"run_id": "20260301_120000", "finding_id": "F1", "verdict": "TP", "annotated_by": "user", "annotated_at_utc": "2026-03-01T13:00:00Z"},
        ],
    })

    result, _, _ = _run_calibration(logs_dir, ledger_path=ledger_path)

    assert result.returncode == 2
    assert "ERROR" in result.stderr
    assert "missing required key field" in result.stderr


def test_infra_error_ledger_missing_finding_id(tmp_path: Path) -> None:
    """Exit 2 when ledger annotation missing finding_id."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"

    findings = [{"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"}]

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", findings_list=findings, items_reviewed=50),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Ledger with missing finding_id
    _write_json(ledger_path, {
        "schema_version": "1.0.0",
        "annotations": [
            {"repo_id": "test_repo", "run_id": "20260301_120000", "verdict": "TP", "annotated_by": "user", "annotated_at_utc": "2026-03-01T13:00:00Z"},
        ],
    })

    result, _, _ = _run_calibration(logs_dir, ledger_path=ledger_path)

    assert result.returncode == 2
    assert "ERROR" in result.stderr
    assert "missing required key field" in result.stderr


def test_weekly_warns_missing_schema_version(tmp_path: Path) -> None:
    """Weekly mode warns about missing reviewed_packet_schema_version."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Findings without schema version (will be UNKNOWN)
    findings_dict = _make_findings("20260301_120000", items_reviewed=50)
    del findings_dict["reviewed_packet_schema_version"]

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        findings_dict,
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    result, report, _ = _run_calibration(logs_dir, mode="weekly")

    assert result.returncode == 0
    assert "WARNING" in result.stderr
    assert "missing reviewed_packet_schema_version" in result.stderr


# ---------------------------------------------------------------------------
# Final strict validation: annotations container and entry types
# ---------------------------------------------------------------------------

def test_infra_error_ledger_annotations_not_list(tmp_path: Path) -> None:
    """Exit 2 when ledger 'annotations' is not a list."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"

    findings = [{"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"}]

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", findings_list=findings, items_reviewed=50),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Ledger with annotations as string instead of list
    _write_json(ledger_path, {
        "schema_version": "1.0.0",
        "annotations": "not-a-list",
    })

    result, _, _ = _run_calibration(logs_dir, ledger_path=ledger_path)

    assert result.returncode == 2
    assert "ERROR" in result.stderr
    assert "annotations' must be a list" in result.stderr


def test_infra_error_ledger_annotation_entry_not_dict(tmp_path: Path) -> None:
    """Exit 2 when ledger annotation entry is not a dict."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    ledger_path = tmp_path / "ledger.json"

    findings = [{"finding_id": "F1", "rule_id": "R001", "severity": "CRITICAL"}]

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", findings_list=findings, items_reviewed=50),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Ledger with annotation entry as string instead of dict
    _write_json(ledger_path, {
        "schema_version": "1.0.0",
        "annotations": ["not-a-dict", "also-not-a-dict"],
    })

    result, _, _ = _run_calibration(logs_dir, ledger_path=ledger_path)

    assert result.returncode == 2
    assert "ERROR" in result.stderr
    assert "must be a dict" in result.stderr


# ---------------------------------------------------------------------------
# Output path handling: auto-create parent directories
# ---------------------------------------------------------------------------

def test_autocreate_output_parent_directories(tmp_path: Path) -> None:
    """Output paths with missing parent directories are auto-created."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    _write_json(
        logs_dir / "auditor_findings_20260301_120000.json",
        _make_findings("20260301_120000", items_reviewed=50),
    )
    _write_json(
        logs_dir / "phase_end_handover_status_20260301_120000.json",
        _make_status("20260301_120000", gates=[_make_gate("G11_auditor_review", command="--mode shadow")]),
    )

    # Output paths in non-existent nested directories
    output_json = tmp_path / "nested" / "deep" / "path" / "report.json"
    output_md = tmp_path / "another" / "nested" / "report.md"

    result, report, md_content = _run_calibration(
        logs_dir,
        repo_id="test_repo",
        mode="weekly",
    )

    # Override with nested paths
    import subprocess
    import sys
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--logs-dir", str(logs_dir),
            "--repo-id", "test_repo",
            "--output-json", str(output_json),
            "--output-md", str(output_md),
            "--mode", "weekly",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert output_json.exists()
    assert output_md.exists()
    assert output_json.parent.exists()
    assert output_md.parent.exists()


def test_atomic_write_text_uses_named_tempfile_and_replace(
    tmp_path: Path, monkeypatch
) -> None:
    """Atomic writer uses NamedTemporaryFile(delete=False) + os.replace."""
    target = tmp_path / "nested" / "report.json"
    named_tempfile_kwargs: dict = {}
    replace_called = {"value": False}

    original_named_tempfile = auditor_calibration_report.tempfile.NamedTemporaryFile
    original_replace = auditor_calibration_report.os.replace

    def _tracking_named_tempfile(*args, **kwargs):
        del args
        named_tempfile_kwargs.update(kwargs)
        return original_named_tempfile(**kwargs)

    def _tracking_replace(src, dst):
        replace_called["value"] = True
        return original_replace(src, dst)

    monkeypatch.setattr(
        auditor_calibration_report.tempfile,
        "NamedTemporaryFile",
        _tracking_named_tempfile,
    )
    monkeypatch.setattr(auditor_calibration_report.os, "replace", _tracking_replace)

    auditor_calibration_report._atomic_write_text(target, '{"ok": true}')

    assert named_tempfile_kwargs["delete"] is False
    assert Path(named_tempfile_kwargs["dir"]) == target.parent
    assert replace_called["value"] is True
    assert target.read_text(encoding="utf-8") == '{"ok": true}'
