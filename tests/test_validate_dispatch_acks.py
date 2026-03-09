from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_dispatch_acks.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _manifest(*, correlation_ids: list[str], plan_hash: str = "plan-hash") -> dict:
    deadline = datetime.now(timezone.utc) + timedelta(minutes=10)
    return {
        "command_plan_hash_sha256": plan_hash,
        "ack_deadline_utc": _iso_utc(deadline),
        "tasks": [{"correlation_id": cid} for cid in correlation_ids],
    }


def _completed_ack(*, correlation_id: str, plan_hash: str) -> dict:
    now = _iso_utc(datetime.now(timezone.utc))
    return {
        "correlation_id": correlation_id,
        "command_plan_hash_sha256": plan_hash,
        "current_state": "COMPLETED",
        "lifecycle": [
            {"state": "STARTED", "utc": now},
            {
                "state": "COMPLETED",
                "utc": now,
                "bound_artifacts": ["scripts/example.py"],
            },
        ],
    }


def _run_validator(
    manifest_path: Path,
    scan_root: Path,
    *,
    timeout_minutes: int = 10,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--manifest",
        str(manifest_path),
        "--scan-root",
        str(scan_root),
        "--timeout-minutes",
        str(timeout_minutes),
    ]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_validate_dispatch_acks_passes_with_single_valid_ack(tmp_path: Path) -> None:
    manifest_path = tmp_path / "dispatch_manifest.json"
    _write_json(manifest_path, _manifest(correlation_ids=["CID-001"], plan_hash="plan-hash"))

    ack_path = tmp_path / "worker_a" / "dispatch_ack.json"
    _write_json(
        ack_path,
        _completed_ack(correlation_id="CID-001", plan_hash="plan-hash"),
    )

    result = _run_validator(manifest_path, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_dispatch_acks_fails_on_duplicate_correlation_id(tmp_path: Path) -> None:
    manifest_path = tmp_path / "dispatch_manifest.json"
    _write_json(manifest_path, _manifest(correlation_ids=["CID-001"], plan_hash="plan-hash"))

    ack_payload = _completed_ack(correlation_id="CID-001", plan_hash="plan-hash")
    _write_json(tmp_path / "worker_a" / "dispatch_ack.json", ack_payload)
    _write_json(tmp_path / "worker_b" / "dispatch_ack.json", ack_payload)

    result = _run_validator(manifest_path, tmp_path)
    assert result.returncode == 6
    combined = result.stdout + result.stderr
    assert "Duplicate correlation_id" in combined
    assert "CID-001" in combined


def test_validate_dispatch_acks_hash_mismatch_exit_code_unchanged(tmp_path: Path) -> None:
    manifest_path = tmp_path / "dispatch_manifest.json"
    _write_json(manifest_path, _manifest(correlation_ids=["CID-001"], plan_hash="expected-plan-hash"))

    _write_json(
        tmp_path / "worker_a" / "dispatch_ack.json",
        _completed_ack(correlation_id="CID-001", plan_hash="wrong-plan-hash"),
    )

    result = _run_validator(manifest_path, tmp_path)
    assert result.returncode == 2
    assert "Hash mismatches" in (result.stdout + result.stderr)


def test_validate_dispatch_acks_fails_on_malformed_json(tmp_path: Path) -> None:
    manifest_path = tmp_path / "dispatch_manifest.json"
    _write_json(manifest_path, _manifest(correlation_ids=["CID-001"], plan_hash="plan-hash"))

    # Write malformed JSON
    ack_path = tmp_path / "worker_a" / "dispatch_ack.json"
    ack_path.parent.mkdir(parents=True, exist_ok=True)
    ack_path.write_text("{invalid json content", encoding="utf-8")

    result = _run_validator(manifest_path, tmp_path)
    assert result.returncode == 2  # INFRA_ERROR
    combined = result.stdout + result.stderr
    assert "Malformed dispatch_ack.json" in combined


def test_validate_dispatch_acks_fails_on_malformed_deadline(tmp_path: Path) -> None:
    manifest_path = tmp_path / "dispatch_manifest.json"

    # Create manifest with malformed deadline
    manifest_data = {
        "command_plan_hash_sha256": "plan-hash",
        "ack_deadline_utc": "not-a-valid-iso-date",
        "tasks": [{"correlation_id": "CID-001"}],
    }
    _write_json(manifest_path, manifest_data)

    # Don't create any ack files - the validator should fail on deadline parse before checking acks
    result = _run_validator(manifest_path, tmp_path)
    assert result.returncode == 2  # INFRA_ERROR
    combined = result.stdout + result.stderr
    assert "Malformed ack_deadline_utc" in combined
