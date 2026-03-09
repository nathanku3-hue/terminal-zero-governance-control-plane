from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_interface_contracts.py"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _run(manifest_path: Path) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT_PATH), "--manifest-json", str(manifest_path)]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_interface_contracts_pass_for_valid_json_keys_and_text_markers(tmp_path: Path) -> None:
    producer = tmp_path / "producer.json"
    consumer = tmp_path / "consumer.md"
    manifest = tmp_path / "interface_contract_manifest.json"

    _write_json(producer, {"schema_version": "2.0.0", "metrics": {"coverage": 1.0}})
    _write_text(consumer, "# Report\nstatus: HOLD\n")
    _write_json(
        manifest,
        {
            "contracts": [
                {
                    "id": "IC-001",
                    "producer_path": str(producer),
                    "consumer_path": str(consumer),
                    "required_keys": ["schema_version", "metrics.coverage"],
                    "required_markers": ["# Report", "status: HOLD"],
                }
            ]
        },
    )

    result = _run(manifest)

    assert result.returncode == 0
    assert "gate passed" in (result.stdout + result.stderr).lower()


def test_interface_contracts_fail_when_file_missing(tmp_path: Path) -> None:
    producer = tmp_path / "producer.json"
    missing_consumer = tmp_path / "missing.md"
    manifest = tmp_path / "interface_contract_manifest.json"

    _write_json(producer, {"schema_version": "2.0.0"})
    _write_json(
        manifest,
        {
            "contracts": [
                {
                    "id": "IC-002",
                    "producer_path": str(producer),
                    "consumer_path": str(missing_consumer),
                    "required_keys": ["schema_version"],
                    "required_markers": [],
                }
            ]
        },
    )

    result = _run(manifest)

    assert result.returncode == 1
    assert "Missing consumer file" in (result.stdout + result.stderr)


def test_interface_contracts_fail_when_required_json_key_missing(tmp_path: Path) -> None:
    producer = tmp_path / "producer.json"
    consumer = tmp_path / "consumer.md"
    manifest = tmp_path / "interface_contract_manifest.json"

    _write_json(producer, {"schema_version": "2.0.0"})
    _write_text(consumer, "# Report\nstatus: HOLD\n")
    _write_json(
        manifest,
        {
            "contracts": [
                {
                    "id": "IC-003",
                    "producer_path": str(producer),
                    "consumer_path": str(consumer),
                    "required_keys": ["metrics.coverage"],
                    "required_markers": ["# Report"],
                }
            ]
        },
    )

    result = _run(manifest)

    assert result.returncode == 1
    assert "missing JSON key" in (result.stdout + result.stderr)


def test_interface_contracts_fail_when_required_text_marker_missing(tmp_path: Path) -> None:
    producer = tmp_path / "producer.json"
    consumer = tmp_path / "consumer.md"
    manifest = tmp_path / "interface_contract_manifest.json"

    _write_json(producer, {"schema_version": "2.0.0"})
    _write_text(consumer, "# Report\nstatus: HOLD\n")
    _write_json(
        manifest,
        {
            "contracts": [
                {
                    "id": "IC-004",
                    "producer_path": str(producer),
                    "consumer_path": str(consumer),
                    "required_keys": ["schema_version"],
                    "required_markers": ["missing marker"],
                }
            ]
        },
    )

    result = _run(manifest)

    assert result.returncode == 1
    assert "missing text marker" in (result.stdout + result.stderr)


def test_interface_contracts_error_when_manifest_missing(tmp_path: Path) -> None:
    manifest = tmp_path / "missing_manifest.json"

    result = _run(manifest)

    assert result.returncode == 2
    assert "manifest does not exist" in (result.stdout + result.stderr).lower()


def test_interface_contracts_error_when_manifest_json_invalid(tmp_path: Path) -> None:
    manifest = tmp_path / "interface_contract_manifest.json"
    _write_text(manifest, "{not-valid-json")

    result = _run(manifest)

    assert result.returncode == 2
    assert "invalid json in manifest" in (result.stdout + result.stderr).lower()
