"""
Integration tests for validate_architect_calibration descriptor.

These tests verify both the sidecar metadata and the real validator CLI
behavior so descriptor drift does not silently accumulate.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sop.descriptors import ValidatorDescriptor


_DESCRIPTOR_PATH = (
    Path(__file__).parent.parent
    / ".codex"
    / "skills"
    / "_shared"
    / "scripts"
    / "validate_architect_calibration.descriptor.json"
)

_VALIDATOR_PATH = (
    Path(__file__).parent.parent
    / ".codex"
    / "skills"
    / "_shared"
    / "scripts"
    / "validate_architect_calibration.py"
)


class TestArchitectCalibrationDescriptor:
    """Test validate_architect_calibration descriptor integration."""

    @pytest.fixture
    def descriptor_data(self):
        """Load descriptor JSON data."""
        with open(_DESCRIPTOR_PATH, encoding="utf-8") as handle:
            return json.load(handle)

    def test_descriptor_file_exists(self):
        """Descriptor sidecar file should exist next to the validator."""
        assert _DESCRIPTOR_PATH.exists()

    def test_descriptor_loads_with_validator_descriptor(self, descriptor_data):
        """Descriptor should deserialize into the shared dataclass."""
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)

        assert descriptor.name == "validate_architect_calibration"
        assert descriptor.input_schema["type"] == "object"
        assert descriptor.output_schema["type"] == "object"

    def test_descriptor_documents_cli_contract(self, descriptor_data):
        """Descriptor should match the validator's argparse surface."""
        input_schema = descriptor_data["input_schema"]
        properties = input_schema["properties"]

        assert input_schema["required"] == ["history_csv", "active_profile"]
        assert properties["history_csv"]["type"] == "string"
        assert properties["active_profile"]["type"] == "string"
        assert properties["min_rows"]["type"] == "integer"
        assert properties["min_rows"]["default"] == 5
        assert properties["tolerance"]["type"] == "number"
        assert properties["tolerance"]["default"] == 0.1

    def test_descriptor_documents_output_and_exit_codes(self, descriptor_data):
        """Descriptor should preserve the validator's non-obvious exit mapping."""
        output_schema = descriptor_data["output_schema"]
        properties = output_schema["properties"]

        assert output_schema["required"] == ["valid", "output", "exit_code"]
        assert properties["valid"]["type"] == "boolean"
        assert properties["output"]["type"] == "string"
        assert properties["exit_code"]["type"] == "integer"
        assert properties["exit_code"]["enum"] == [0, 1, 2]
        assert "INSUFFICIENT" in properties["exit_code"]["description"]

    def test_descriptor_roundtrip_dict(self, descriptor_data):
        """Descriptor should roundtrip through the dataclass unchanged."""
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)

        assert descriptor.to_dict() == descriptor_data

    def test_descriptor_roundtrip_json(self, descriptor_data):
        """Descriptor JSON serialization should be stable."""
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)
        roundtrip_data = json.loads(descriptor.to_json())

        assert roundtrip_data == descriptor_data

    def test_declared_capabilities_are_informational(self, descriptor_data):
        """Capabilities should remain metadata only."""
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)

        assert descriptor.declared_capabilities == [
            "read_csv",
            "aggregate_profile_outcomes",
            "detect_calibration_drift",
        ]

    def test_validator_pass_invalid_drift_and_insufficient_paths(self, tmp_path):
        """Real validator behavior should stay aligned with the descriptor."""
        assert _VALIDATOR_PATH.exists()

        history_path = tmp_path / "history.csv"
        rows = [
            {"profile": "steady", "outcome": "1.0"},
            {"profile": "steady", "outcome": "1.0"},
            {"profile": "steady", "outcome": "1.0"},
            {"profile": "drifted", "outcome": "0.0"},
            {"profile": "drifted", "outcome": "0.0"},
            {"profile": "drifted", "outcome": "0.0"},
        ]
        with open(history_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["profile", "outcome"])
            writer.writeheader()
            writer.writerows(rows)

        pass_result = subprocess.run(
            [
                sys.executable,
                str(_VALIDATOR_PATH),
                "--history-csv",
                str(history_path),
                "--active-profile",
                "steady",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert pass_result.returncode == 0
        assert "PASS:" in pass_result.stdout

        drift_result = subprocess.run(
            [
                sys.executable,
                str(_VALIDATOR_PATH),
                "--history-csv",
                str(history_path),
                "--active-profile",
                "drifted",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert drift_result.returncode == 2
        assert "DRIFT:" in drift_result.stdout

        invalid_result = subprocess.run(
            [
                sys.executable,
                str(_VALIDATOR_PATH),
                "--history-csv",
                str(history_path),
                "--active-profile",
                "missing",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert invalid_result.returncode == 1
        assert "INVALID:" in invalid_result.stdout

        insufficient_path = tmp_path / "insufficient.csv"
        with open(insufficient_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["profile", "outcome"])
            writer.writeheader()
            writer.writerows(rows[:2])

        insufficient_result = subprocess.run(
            [
                sys.executable,
                str(_VALIDATOR_PATH),
                "--history-csv",
                str(insufficient_path),
                "--active-profile",
                "steady",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert insufficient_result.returncode == 0
        assert "INSUFFICIENT:" in insufficient_result.stdout
