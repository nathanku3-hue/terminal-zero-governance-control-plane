from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_repo() -> Path:
    return Path(tempfile.mkdtemp(prefix="phase10_nightly_audit_"))


def _cleanup_repo(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, indent=2) + "\n")


def _write_required_runbooks(repo_root: Path) -> None:
    _write(repo_root / "docs/runbooks/post-ga-operations.md", "# Post-GA Operations\n")
    _write(repo_root / "docs/runbooks/hotfix-protocol.md", "# Hotfix Protocol\n")
    _write(repo_root / "docs/runbooks/continuous-compliance.md", "# Continuous Compliance\n")


def _write_policy_table(repo_root: Path, include: set[str] | None = None) -> None:
    all_rows = {
        "release": ("HIGH", "4h", "Investigate release gate failure and remediate"),
        "evidence": ("MEDIUM", "24h", "Collect missing evidence and update docs"),
        "drift": ("HIGH", "8h", "Run regression triage and restore PASS status"),
        "runbooks": ("MEDIUM", "48h", "Update runbooks and policy docs"),
    }
    include = include or set(all_rows.keys())

    lines = [
        "# Compliance Violations",
        "",
        "| Violation Type | Severity | SLA | Required Action |",
        "|---|---|---|---|",
    ]
    for key in ("release", "evidence", "drift", "runbooks"):
        if key in include:
            severity, sla, action = all_rows[key]
            lines.append(f"| {key} | {severity} | {sla} | {action} |")
    lines.append("")
    _write(repo_root / "docs/policies/compliance_violations.md", "\n".join(lines))


def _run_nightly_audit(repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "sop",
            "ops",
            "nightly-audit",
            "--repo-root",
            str(repo_root),
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )


def test_stdout_equals_artifact_json_first_run_all_controls_pass() -> None:
    repo_root = _make_repo()
    try:
        _write_required_runbooks(repo_root)
        _write_policy_table(repo_root)

        _write_json(
            repo_root / "docs/context/change_review_result_latest.json",
            {"overall_status": "PASS"},
        )
        _write_json(
            repo_root / "docs/context/regression_watch_latest.json",
            {"overall_status": "PASS"},
        )
        _write(repo_root / "docs/evidence/phase9_post_ga_ops_evidence.md", "# Phase 9 Evidence\n")

        result = _run_nightly_audit(repo_root)
        assert result.returncode == 0, result.stderr

        snapshot_path = repo_root / "docs/context/compliance_snapshot_latest.json"
        assert snapshot_path.exists()

        stdout_json = result.stdout
        artifact_json = snapshot_path.read_text(encoding="utf-8")
        assert stdout_json == artifact_json

        payload = json.loads(stdout_json)
        assert "snapshot" not in payload
        assert payload["overall_status"] == "PASS"

        controls = {entry["control_id"]: entry for entry in payload["controls"]}
        assert controls["evidence"]["status"] == "PASS"
        assert "Informational" in controls["evidence"]["reason"]
    finally:
        _cleanup_repo(repo_root)


def test_per_control_failures_and_escalation_mapping_exit2() -> None:
    repo_root = _make_repo()
    try:
        _write_required_runbooks(repo_root)
        _write_policy_table(repo_root)
        assert (repo_root / "docs/policies/compliance_violations.md").exists()

        _write_json(
            repo_root / "docs/context/change_review_result_latest.json",
            {"overall_status": "FAIL"},
        )
        _write_json(
            repo_root / "docs/context/regression_watch_latest.json",
            {"overall_status": "FAIL"},
        )

        result = _run_nightly_audit(repo_root)
        assert result.returncode == 2, result.stderr

        snapshot = json.loads((repo_root / "docs/context/compliance_snapshot_latest.json").read_text(encoding="utf-8"))
        controls = {entry["control_id"]: entry for entry in snapshot["controls"]}

        assert controls["release"]["status"] == "FAIL"
        assert controls["evidence"]["status"] == "FAIL"
        assert controls["drift"]["status"] == "FAIL"
        assert controls["runbooks"]["status"] == "PASS"

        queue = json.loads((repo_root / "docs/context/compliance_escalation_queue_latest.json").read_text(encoding="utf-8"))
        entries = {entry["control_id"]: entry for entry in queue["entries"]}
        assert set(entries.keys()) == {"release", "evidence", "drift"}
        assert entries["release"]["severity"] == "HIGH"
        assert entries["release"]["sla"] == "4h"
        assert "Investigate release gate failure" in entries["release"]["required_action"]
    finally:
        _cleanup_repo(repo_root)


def test_missing_violation_mapping_row_exits_3() -> None:
    repo_root = _make_repo()
    try:
        _write_required_runbooks(repo_root)
        _write_policy_table(repo_root, include={"release", "evidence", "runbooks"})

        _write_json(
            repo_root / "docs/context/change_review_result_latest.json",
            {"overall_status": "PASS"},
        )
        _write_json(
            repo_root / "docs/context/regression_watch_latest.json",
            {"overall_status": "FAIL"},
        )
        _write(repo_root / "docs/evidence/phase9_post_ga_ops_evidence.md", "# Phase 9 Evidence\n")

        result = _run_nightly_audit(repo_root)
        assert result.returncode == 3
        assert "Missing escalation mapping row" in result.stderr
        assert not (repo_root / "docs/context/compliance_snapshot_latest.json").exists()
    finally:
        _cleanup_repo(repo_root)


def test_schema_invalid_input_exits_3() -> None:
    repo_root = _make_repo()
    try:
        _write_required_runbooks(repo_root)
        _write_policy_table(repo_root)

        _write_json(
            repo_root / "docs/context/change_review_result_latest.json",
            {"overall_status": "UNKNOWN"},
        )
        _write_json(
            repo_root / "docs/context/regression_watch_latest.json",
            {"overall_status": "PASS"},
        )
        _write(repo_root / "docs/evidence/phase9_post_ga_ops_evidence.md", "# Phase 9 Evidence\n")

        result = _run_nightly_audit(repo_root)
        assert result.returncode == 3
        assert "Schema-invalid JSON artifact" in result.stderr
    finally:
        _cleanup_repo(repo_root)
