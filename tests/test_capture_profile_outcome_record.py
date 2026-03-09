from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "capture_profile_outcome_record.py"
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_capture_profile_outcome_record_happy_path(tmp_path: Path) -> None:
    loop_closure_path = tmp_path / "docs/context/loop_closure_status_latest.json"
    startup_path = tmp_path / "docs/context/startup_intake_latest.json"
    round_contract_path = tmp_path / "docs/context/round_contract_latest.md"
    go_signal_path = tmp_path / "docs/context/ceo_go_signal.md"

    _write_json(loop_closure_path, {"result": "READY_TO_ESCALATE"})
    _write_json(
        startup_path,
        {
            "domain_bucket_bootstrap": {"project_profile": "quant_default"},
            "interrogation": {"project_profile": "general_software"},
        },
    )
    _write_text(
        round_contract_path,
        "\n".join(
            [
                "# Round Contract",
                "- PROJECT_PROFILE: data_platform",
                "- BOARD_REENTRY_REQUIRED: NO",
                "- BOARD_REENTRY_REASON: N/A",
            ]
        )
        + "\n",
    )
    _write_text(
        go_signal_path,
        "\n".join(
            [
                "# CEO GO Signal",
                "- Recommended Action: GO",
            ]
        )
        + "\n",
    )

    result = _run(
        tmp_path,
        "--shipped",
        "true",
        "--rollback-status",
        "no",
        "--followup-changes-within-30d",
        "1",
        "--semantic-issue-detected-after-merge",
        "present",
        "--postmortem-score",
        "8.5",
        "--postmortem-note",
        "Scope landed cleanly and no new board review was needed.",
        "--notes",
        "Shipped with expected scope.",
        "--captured-at-utc",
        "2026-03-08T00:00:00Z",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PROFILE_OUTCOME_CAPTURE_STATUS: WRITTEN" in result.stdout
    assert "PROJECT_PROFILE: quant_default" in result.stdout
    assert "LOOP_CLOSURE_RESULT: READY_TO_ESCALATE" in result.stdout
    assert "GO_ACTION: GO" in result.stdout
    assert "SHIPPED: TRUE" in result.stdout
    assert "ROLLBACK_STATUS: NO" in result.stdout
    assert "FOLLOWUP_CHANGES_WITHIN_30D: 1" in result.stdout
    assert "SEMANTIC_ISSUE_DETECTED_AFTER_MERGE: PRESENT" in result.stdout

    corpus_dir = tmp_path / "docs/context/profile_outcomes_corpus"
    output_files = list(corpus_dir.glob("profile_outcome_*.json"))
    assert len(output_files) == 1

    payload = json.loads(output_files[0].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.1.0"
    assert payload["advisory_only"] is True
    assert payload["control_plane_impact"] == "none"
    assert payload["captured_at_utc"] == "2026-03-08T00:00:00Z"
    assert payload["project_profile"] == "quant_default"
    assert payload["loop_closure_result"] == "READY_TO_ESCALATE"
    assert payload["go_action"] == "GO"
    assert payload["ready"] is True
    assert payload["shipped"] is True
    assert payload["rollback_status"] == "NO"
    assert payload["followup_changes_within_30d"] == 1
    assert payload["semantic_issue_detected_after_merge"] == "PRESENT"
    assert payload["postmortem_score"] == 8.5
    assert payload["postmortem_note"] == "Scope landed cleanly and no new board review was needed."
    assert payload["notes"] == "Shipped with expected scope."
    assert payload["board_reentry_required"] is False
    assert payload["unknown_domain_triggered"] is False
    assert payload["artifact_context"]["loop_closure_present"] is True
    assert payload["artifact_context"]["startup_intake_present"] is True
    assert payload["artifact_context"]["round_contract_present"] is True
    assert payload["artifact_context"]["go_signal_present"] is True


def test_capture_profile_outcome_record_missing_artifacts_fallback(tmp_path: Path) -> None:
    output_path = tmp_path / "docs/context/profile_outcomes_corpus/custom_record.json"

    result = _run(
        tmp_path,
        "--shipped",
        "false",
        "--captured-at-utc",
        "2026-03-08T00:00:00Z",
        "--output-json",
        str(output_path),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["project_profile"] == "unknown"
    assert payload["loop_closure_result"] == "UNKNOWN"
    assert payload["go_action"] == "UNKNOWN"
    assert payload["ready"] is False
    assert payload["shipped"] is False
    assert payload["rollback_status"] == "NO"
    assert payload["followup_changes_within_30d"] == 0
    assert payload["semantic_issue_detected_after_merge"] == "I don't know yet"
    assert payload["postmortem_score"] is None
    assert payload["postmortem_note"] == ""
    assert payload["notes"] == ""
    assert payload["board_reentry_required"] is False
    assert payload["unknown_domain_triggered"] is False
    assert payload["artifact_context"]["loop_closure_present"] is False
    assert payload["artifact_context"]["startup_intake_present"] is False
    assert payload["artifact_context"]["round_contract_present"] is False
    assert payload["artifact_context"]["go_signal_present"] is False


def test_capture_profile_outcome_record_prefers_closure_result_over_go_action(tmp_path: Path) -> None:
    loop_closure_path = tmp_path / "docs/context/loop_closure_status_latest.json"
    go_signal_path = tmp_path / "docs/context/ceo_go_signal.md"
    output_path = tmp_path / "docs/context/profile_outcomes_corpus/conflict_record.json"

    _write_json(loop_closure_path, {"result": "NOT_READY"})
    _write_text(
        go_signal_path,
        "\n".join(
            [
                "# CEO GO Signal",
                "- Recommended Action: GO",
            ]
        )
        + "\n",
    )

    result = _run(
        tmp_path,
        "--project-profile",
        "quant_default",
        "--shipped",
        "false",
        "--captured-at-utc",
        "2026-03-08T00:00:00Z",
        "--output-json",
        str(output_path),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["loop_closure_result"] == "NOT_READY"
    assert payload["go_action"] == "GO"
    assert payload["ready"] is False
