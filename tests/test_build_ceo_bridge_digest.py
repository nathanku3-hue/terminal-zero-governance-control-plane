from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_ceo_bridge_digest.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_digest_includes_worker_confidence_section_when_reply_packet_provided(
    tmp_path: Path,
) -> None:
    agg_path = tmp_path / "worker_status_aggregate.json"
    trace_path = tmp_path / "pm_to_code_traceability.yaml"
    esc_path = tmp_path / "escalation_events.json"
    reply_path = tmp_path / "worker_reply_packet.json"
    out_path = tmp_path / "ceo_bridge_digest.md"

    _write_json(
        agg_path,
        {
            "summary": {"overall_health": "OK"},
            "workers": [
                {
                    "worker_id": "@backend-1",
                    "lane": "backend",
                    "heartbeat": {"status": "idle", "current_task": {"task_id": "IDLE"}},
                    "sla": {"escalation_status": "OK"},
                    "expert_gate": {
                        "system_eng": "PASS",
                        "architect": "PASS",
                        "principal": "PASS",
                        "riskops": "PASS",
                        "devsecops": "PASS",
                        "qa": "PASS",
                    },
                    "completion_log": [],
                    "blockers": [],
                }
            ],
        },
    )
    _write_yaml(
        trace_path,
        {
            "directives": [
                {
                    "directive_id": "PM-001",
                    "source": "top_level_PM.md#x",
                    "status": "VERIFIED",
                    "traceability": {
                        "code_diffs": [{"file": "scripts/a.py"}],
                        "validators": [{"path": "tests/test_a.py::test_a"}],
                    },
                }
            ]
        },
    )
    _write_json(esc_path, {"events": []})
    _write_json(
        reply_path,
        {
            "schema_version": "1.0.0",
            "worker_id": "@backend-1",
            "phase": "phase24",
            "generated_at_utc": "2026-03-01T12:00:00Z",
            "items": [
                {
                    "task_id": "T-101",
                    "decision": "done",
                    "dod_result": "PASS",
                    "evidence_ids": ["EV-101"],
                    "open_risks": [],
                    "confidence": {"score": 0.9, "band": "HIGH", "rationale": "validated"},
                    "citations": [
                        {
                            "type": "code",
                            "path": "scripts/a.py",
                            "locator": "L1",
                            "claim": "implemented",
                        }
                    ],
                }
            ],
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--sources",
            ",".join(
                [
                    str(agg_path),
                    str(trace_path),
                    str(esc_path),
                    str(reply_path),
                ]
            ),
            "--output",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    digest = out_path.read_text(encoding="utf-8")
    assert "## VI. Worker Confidence and Citations" in digest
    assert "| @backend-1 | T-101 | PASS | 0.90 (HIGH) |" in digest
    assert "## VII. Recommended PM Actions" in digest


def test_digest_handles_missing_reply_packet_source(tmp_path: Path) -> None:
    agg_path = tmp_path / "worker_status_aggregate.json"
    trace_path = tmp_path / "pm_to_code_traceability.yaml"
    out_path = tmp_path / "ceo_bridge_digest.md"

    _write_json(agg_path, {"summary": {}, "workers": []})
    _write_yaml(trace_path, {"directives": []})

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--sources",
            ",".join([str(agg_path), str(trace_path)]),
            "--output",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    digest = out_path.read_text(encoding="utf-8")
    assert "## VI. Worker Confidence and Citations" in digest
    assert "- No worker reply packet provided." in digest
