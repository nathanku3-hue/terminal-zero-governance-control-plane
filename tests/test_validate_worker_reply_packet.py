from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_worker_reply_packet.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_worker_reply_packet_passes_with_confidence_and_citations(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifact = repo_root / "scripts" / "sample.py"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("print('ok')\n", encoding="utf-8")

    packet = {
        "schema_version": "1.0.0",
        "worker_id": "@backend-1",
        "phase": "phase24",
        "generated_at_utc": "2026-03-01T12:00:00Z",
        "items": [
            {
                "task_id": "T-101",
                "decision": "implemented confidence/citation packet",
                "dod_result": "PASS",
                "evidence_ids": ["EV-101"],
                "open_risks": [],
                "confidence": {
                    "score": 0.93,
                    "band": "HIGH",
                    "rationale": "unit tests and schema validation passed",
                },
                "citations": [
                    {
                        "type": "code",
                        "path": "scripts/sample.py",
                        "locator": "L1",
                        "claim": "contains implementation entrypoint",
                    }
                ],
            }
        ],
    }
    packet_path = repo_root / "docs/context/worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(packet_path),
            "--repo-root",
            str(repo_root),
            "--require-existing-paths",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_worker_reply_packet_fails_without_confidence_or_citations(tmp_path: Path) -> None:
    packet = {
        "schema_version": "1.0.0",
        "worker_id": "@backend-1",
        "phase": "phase24",
        "generated_at_utc": "2026-03-01T12:00:00Z",
        "items": [
            {
                "task_id": "T-102",
                "decision": "done",
                "dod_result": "PASS",
                "evidence_ids": ["EV-102"],
                "open_risks": [],
                "confidence": {},
                "citations": [],
            }
        ],
    }
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--input", str(packet_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "confidence.score" in combined or "confidence.band" in combined
    assert "citations must be a non-empty list" in combined
