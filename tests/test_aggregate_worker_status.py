from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "aggregate_worker_status.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _worker_status_payload(
    *,
    worker_id: str = "@qa-1",
    task_id: str = "T-100",
    last_write_utc: str = "2020-01-01T00:00:00Z",
) -> dict:
    return {
        "worker_id": worker_id,
        "heartbeat": {
            "status": "executing",
            "last_write_utc": last_write_utc,
            "current_task": {"task_id": task_id},
            "ttl_seconds": 300,
            "clock_skew_grace_seconds": 30,
        },
        "completion_log": [],
    }


def _run_aggregate(
    *,
    scan_root: Path,
    output_path: Path,
    escalation_output_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--scan-root",
            str(scan_root),
            "--output",
            str(output_path),
            "--escalation-output",
            str(escalation_output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_escalation_append_dedupes_same_unresolved_issue(tmp_path: Path) -> None:
    scan_root = tmp_path / "scan"
    worker_status_path = scan_root / "docs" / "context" / "worker_status.json"
    aggregate_out = tmp_path / "worker_status_aggregate.json"
    escalation_out = tmp_path / "escalation_events.json"
    _write_json(worker_status_path, _worker_status_payload())

    first = _run_aggregate(
        scan_root=scan_root,
        output_path=aggregate_out,
        escalation_output_path=escalation_out,
    )
    assert first.returncode == 2, first.stdout + first.stderr
    first_events = json.loads(escalation_out.read_text(encoding="utf-8"))["events"]
    assert len(first_events) == 1

    second = _run_aggregate(
        scan_root=scan_root,
        output_path=aggregate_out,
        escalation_output_path=escalation_out,
    )
    assert second.returncode == 2, second.stdout + second.stderr
    second_events = json.loads(escalation_out.read_text(encoding="utf-8"))["events"]
    assert len(second_events) == 1
    assert second_events[0]["worker_id"] == "@qa-1"
    assert second_events[0]["task_id"] == "T-100"
    assert second_events[0]["stale_since_utc"] == "2020-01-01T00:00:00Z"


def test_escalation_append_allows_new_event_when_existing_is_resolved(
    tmp_path: Path,
) -> None:
    scan_root = tmp_path / "scan"
    worker_status_path = scan_root / "docs" / "context" / "worker_status.json"
    aggregate_out = tmp_path / "worker_status_aggregate.json"
    escalation_out = tmp_path / "escalation_events.json"
    _write_json(worker_status_path, _worker_status_payload())

    _write_json(
        escalation_out,
        {
            "events": [
                {
                    "event_id": "ESC-20260301000000-@qa-1",
                    "worker_id": "@qa-1",
                    "task_id": "T-100",
                    "stale_since_utc": "2020-01-01T00:00:00Z",
                    "stale_duration_minutes": 999.0,
                    "clock_skew_suspect": False,
                    "escalated_utc": "2026-03-01T00:00:00Z",
                    "recommended_action": "CHECK_WORKER_ALIVE",
                    "action_taken": "CHECKED",
                    "resolved": True,
                }
            ]
        },
    )

    result = _run_aggregate(
        scan_root=scan_root,
        output_path=aggregate_out,
        escalation_output_path=escalation_out,
    )
    assert result.returncode == 2, result.stdout + result.stderr

    events = json.loads(escalation_out.read_text(encoding="utf-8"))["events"]
    assert len(events) == 2
    active_events = [
        event
        for event in events
        if event.get("worker_id") == "@qa-1"
        and event.get("task_id") == "T-100"
        and event.get("stale_since_utc") == "2020-01-01T00:00:00Z"
        and event.get("resolved") is not True
    ]
    assert len(active_events) == 1


def test_parse_failure_recorded(tmp_path: Path) -> None:
    scan_root = tmp_path / "scan"
    worker_a_path = scan_root / "worker_a" / "worker_status.json"
    worker_b_path = scan_root / "worker_b" / "worker_status.json"
    aggregate_out = tmp_path / "worker_status_aggregate.json"
    escalation_out = tmp_path / "escalation_events.json"

    # Create valid worker status
    _write_json(worker_a_path, _worker_status_payload(worker_id="@worker-a"))

    # Create invalid worker status (corrupted JSON)
    worker_b_path.parent.mkdir(parents=True, exist_ok=True)
    worker_b_path.write_text("{invalid json content", encoding="utf-8")

    result = _run_aggregate(
        scan_root=scan_root,
        output_path=aggregate_out,
        escalation_output_path=escalation_out,
    )

    # Should succeed despite parse failure
    assert result.returncode == 2, result.stdout + result.stderr

    aggregate_data = json.loads(aggregate_out.read_text(encoding="utf-8"))

    # Check parse_failures field exists and contains worker_b error
    assert "parse_failures" in aggregate_data
    parse_failures = aggregate_data["parse_failures"]
    assert len(parse_failures) == 1

    failure = parse_failures[0]
    assert "file" in failure
    assert str(worker_b_path) in failure["file"]
    assert "error" in failure
    assert "timestamp_utc" in failure
    assert failure["timestamp_utc"].endswith("Z")

    # Verify valid worker was processed
    assert aggregate_data["summary"]["total_workers"] == 1
    assert len(aggregate_data["workers"]) == 1
    assert aggregate_data["workers"][0]["worker_id"] == "@worker-a"
