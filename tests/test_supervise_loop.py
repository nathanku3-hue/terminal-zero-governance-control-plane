from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "supervise_loop.py"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload, indent=2))


def _run(repo_root: Path, freshness_hours: float = 24.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--check-interval-seconds",
            "0",
            "--max-cycles",
            "1",
            "--freshness-hours",
            str(freshness_hours),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _status_path(repo_root: Path) -> Path:
    return repo_root / "docs" / "context" / "supervisor_status_latest.json"


def _alerts_path(repo_root: Path) -> Path:
    return repo_root / "docs" / "context" / "supervisor_alerts_latest.md"


def _prepare_context(
    repo_root: Path,
    *,
    closure_result: str = "READY_TO_ESCALATE",
    closure_checks: list[dict] | None = None,
    go_action: str = "GO",
    dossier_criteria_rows: list[tuple[str, str, str]] | None = None,
    blocking_reasons: list[str] | None = None,
    next_steps: list[str] | None = None,
    intuition_gate: str = "MACHINE_DEFAULT",
    intuition_gate_ack: str = "N/A",
    extra_round_fields: dict[str, str] | None = None,
) -> Path:
    context = repo_root / "docs" / "context"
    _write_json(context / "loop_cycle_summary_latest.json", {"final_result": "PASS"})
    closure_payload: dict[str, object] = {"result": closure_result}
    if closure_checks is not None:
        closure_payload["checks"] = closure_checks
    _write_json(context / "loop_closure_status_latest.json", closure_payload)
    reason_lines = []
    if dossier_criteria_rows:
        reason_lines.extend(
            [
                "## Dossier Criteria",
                "",
                "| Criterion | Status | Value |",
                "|---|---|---|",
            ]
        )
        reason_lines.extend(
            f"| {criterion} | {status} | {value} |"
            for criterion, status, value in dossier_criteria_rows
        )
        reason_lines.append("")
    if blocking_reasons:
        reason_lines.extend(["## Blocking Reasons", ""])
        reason_lines.extend(f"- {reason}" for reason in blocking_reasons)
        reason_lines.append("")
    if next_steps:
        reason_lines.extend(["## Next Steps", ""])
        reason_lines.extend(
            f"{index}. {step}" for index, step in enumerate(next_steps, start=1)
        )
        reason_lines.append("")
    _write_text(
        context / "ceo_go_signal.md",
        "\n".join(
            [
                "# CEO GO Signal",
                "",
                f"- Recommended Action: {go_action}",
                "",
                *reason_lines,
            ]
        ),
    )
    round_lines = [
        "# Round Contract",
        "",
        "- DECISION_CLASS: TWO_WAY",
        "- RISK_TIER: MEDIUM",
        f"- INTUITION_GATE: {intuition_gate}",
        f"- INTUITION_GATE_ACK: {intuition_gate_ack}",
    ]
    if extra_round_fields:
        round_lines.extend(f"- {key}: {value}" for key, value in extra_round_fields.items())
    round_lines.append("")
    _write_text(context / "round_contract_latest.md", "\n".join(round_lines))
    return context


def test_supervisor_ready_event_and_pass_exit(tmp_path: Path) -> None:
    repo_root = tmp_path
    _prepare_context(repo_root, closure_result="READY_TO_ESCALATE", go_action="GO")

    result = _run(repo_root)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(_status_path(repo_root).read_text(encoding="utf-8"))
    assert payload["overall_status"] == "READY"
    assert payload["critical_found"] is False
    assert any(
        event["code"] == "READY_TO_ESCALATE" for event in payload["events"]
    )
    assert payload["manual_action_count"] == 0
    assert payload["manual_action_summary"]["total"] == 0
    assert payload["manual_actions"] == []
    assert _alerts_path(repo_root).exists()


def test_supervisor_hold_event_when_go_signal_hold(tmp_path: Path) -> None:
    repo_root = tmp_path
    _prepare_context(
        repo_root,
        closure_result="NOT_READY",
        go_action="HOLD",
        blocking_reasons=["C4b not met (53.49%)."],
        next_steps=["Regenerate dossier and calibration artifacts."],
    )

    result = _run(repo_root)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(_status_path(repo_root).read_text(encoding="utf-8"))
    assert payload["overall_status"] == "HOLD"
    assert any(event["code"] == "GO_SIGNAL_HOLD" for event in payload["events"])
    assert payload["manual_actions"]
    ids = {item["id"] for item in payload["manual_actions"]}
    assert "go_signal_not_go" in ids
    assert "annotation_gap_from_blocking_reason" in ids
    assert "go_next_step_1" in ids
    assert payload["manual_action_count"] == len(payload["manual_actions"])
    assert payload["manual_action_summary"]["p0"] >= 1
    alerts_text = _alerts_path(repo_root).read_text(encoding="utf-8")
    assert "## Manual Action Queue" in alerts_text
    assert "| Priority | ActionID | Source | Trigger | Action | Reason |" in alerts_text


def test_supervisor_critical_when_closure_infra_error(tmp_path: Path) -> None:
    repo_root = tmp_path
    _prepare_context(repo_root, closure_result="INPUT_OR_INFRA_ERROR", go_action="GO")

    result = _run(repo_root)

    assert result.returncode == 1, result.stdout + result.stderr
    payload = json.loads(_status_path(repo_root).read_text(encoding="utf-8"))
    assert payload["overall_status"] == "CRITICAL"
    assert payload["critical_found"] is True
    assert any(
        event["code"] == "CLOSURE_INPUT_OR_INFRA_ERROR" for event in payload["events"]
    )


def test_supervisor_warns_on_stale_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_context(repo_root, closure_result="NOT_READY", go_action="GO")

    stale_target = context / "loop_cycle_summary_latest.json"
    old_epoch = stale_target.stat().st_mtime - (3 * 3600)
    os.utime(stale_target, (old_epoch, old_epoch))

    result = _run(repo_root, freshness_hours=1.0)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(_status_path(repo_root).read_text(encoding="utf-8"))
    assert payload["overall_status"] == "WARN"
    assert any(event["code"] == "STALE_ARTIFACT" for event in payload["events"])
    assert any(item["id"] == "stale_loop_cycle_summary_latest_json" for item in payload["manual_actions"])


def test_supervisor_writes_outputs_with_missing_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path

    result = _run(repo_root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert _status_path(repo_root).exists()
    assert _alerts_path(repo_root).exists()
    payload = json.loads(_status_path(repo_root).read_text(encoding="utf-8"))
    assert any(event["code"] == "ARTIFACT_MISSING" for event in payload["events"])
    assert payload["manual_actions"]
    assert any("Generate missing artifact" in item["action"] for item in payload["manual_actions"])
    assert any(item["id"] == "missing_loop_cycle_summary_latest_json" for item in payload["manual_actions"])
    assert payload["manual_action_summary"]["p0"] >= 1


def test_supervisor_queues_human_ack_action_for_human_required_round(tmp_path: Path) -> None:
    repo_root = tmp_path
    _prepare_context(
        repo_root,
        closure_result="NOT_READY",
        go_action="HOLD",
        intuition_gate="HUMAN_REQUIRED",
        intuition_gate_ack="N/A",
    )

    result = _run(repo_root)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(_status_path(repo_root).read_text(encoding="utf-8"))
    assert any(item["id"] == "intuition_gate_ack_missing" for item in payload["manual_actions"])


def test_supervisor_derives_manual_queue_from_criteria_closure_and_round_todos(tmp_path: Path) -> None:
    repo_root = tmp_path
    _prepare_context(
        repo_root,
        closure_result="NOT_READY",
        closure_checks=[
            {"name": "go_signal_action_gate", "status": "FAIL"},
            {"name": "freshness_gate", "status": "FAIL"},
            {"name": "tdd_contract_gate", "status": "PASS"},
        ],
        go_action="HOLD",
        dossier_criteria_rows=[
            ("C1", "MANUAL_CHECK", "MANUAL_CHECK"),
            ("C4b", "FAIL", "53.49%"),
        ],
        blocking_reasons=["C4b not met (53.49%)."],
        next_steps=[
            "Satisfy remaining automated dossier criteria.",
            "Re-run phase-end handover to refresh this signal.",
        ],
        extra_round_fields={
            "EVIDENCE_COMMANDS": "TODO(add exact validation and evidence commands).",
            "EXPERT_PLAN": "TODO(list expert consult path and escalation trigger).",
        },
    )

    result = _run(repo_root)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(_status_path(repo_root).read_text(encoding="utf-8"))
    ids = [item["id"] for item in payload["manual_actions"]]
    assert "manual_signoff_c1" in ids
    assert "annotation_gap_c4b" in ids
    assert "closure_not_ready" in ids
    assert "round_contract_todo_fields" in ids
    assert payload["manual_action_summary"]["p0"] >= 3
    closure_reason = next(
        item["reason"] for item in payload["manual_actions"] if item["id"] == "closure_not_ready"
    )
    assert "failing checks" in closure_reason.lower()
    assert "freshness_gate" in closure_reason
    alerts_text = _alerts_path(repo_root).read_text(encoding="utf-8")
    assert "manual_signoff_c1" in alerts_text
