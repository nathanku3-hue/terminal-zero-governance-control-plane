"""
Integration tests for validate_saw_report_blocks descriptor.

These tests keep the sidecar metadata and validator CLI behavior aligned.
"""

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
    / "validate_saw_report_blocks.descriptor.json"
)

_VALIDATOR_PATH = (
    Path(__file__).parent.parent
    / ".codex"
    / "skills"
    / "_shared"
    / "scripts"
    / "validate_saw_report_blocks.py"
)

_VALID_REPORT = """SAW Verdict: PASS
Hierarchy Confirmation: in-scope items reconciled against inherited items
ClosurePacket: RoundID=round1; ScopeID=scope1; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS
ClosureValidation: PASS
Open Risks: none
Next action: archive and continue
Scope split: in-scope work separated from inherited context
"""


class TestSawReportBlocksDescriptor:
    """Test validate_saw_report_blocks descriptor integration."""

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

        assert descriptor.name == "validate_saw_report_blocks"
        assert descriptor.input_schema["type"] == "object"
        assert descriptor.output_schema["type"] == "object"

    def test_descriptor_documents_exactly_one_input_mode(self, descriptor_data):
        """Descriptor should reflect the CLI's mutually exclusive input modes."""
        input_schema = descriptor_data["input_schema"]
        properties = input_schema["properties"]

        assert properties["report"]["type"] == "string"
        assert properties["report_file"]["type"] == "string"
        assert input_schema["oneOf"] == [
            {"required": ["report"]},
            {"required": ["report_file"]},
        ]

    def test_descriptor_documents_output_schema(self, descriptor_data):
        """Descriptor should describe validator output and exit codes."""
        output_schema = descriptor_data["output_schema"]
        properties = output_schema["properties"]

        assert output_schema["required"] == ["valid", "output", "exit_code"]
        assert properties["valid"]["type"] == "boolean"
        assert properties["output"]["type"] == "string"
        assert properties["exit_code"]["type"] == "integer"
        assert properties["exit_code"]["enum"] == [0, 1]

    def test_descriptor_roundtrip_dict(self, descriptor_data):
        """Descriptor should roundtrip through the shared dataclass."""
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)

        assert descriptor.to_dict() == descriptor_data

    def test_descriptor_roundtrip_json(self, descriptor_data):
        """Descriptor JSON serialization should be stable."""
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)
        roundtrip_data = json.loads(descriptor.to_json())

        assert roundtrip_data == descriptor_data

    def test_validator_accepts_inline_report(self):
        """Validator should continue to work with inline report text."""
        assert _VALIDATOR_PATH.exists()

        result = subprocess.run(
            [sys.executable, str(_VALIDATOR_PATH), "--report", _VALID_REPORT],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "VALID"

    def test_validator_accepts_report_file(self, tmp_path):
        """Validator should continue to work with file-based input."""
        report_path = tmp_path / "saw_report.txt"
        report_path.write_text(_VALID_REPORT, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(_VALIDATOR_PATH), "--report-file", str(report_path)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "VALID"

    def test_validator_rejects_missing_input(self):
        """Validator should fail when neither input mode is provided."""
        result = subprocess.run(
            [sys.executable, str(_VALIDATOR_PATH)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 1
        assert "INVALID:" in result.stdout
        assert "--report or --report-file" in result.stdout

    def test_validator_rejects_missing_required_block(self):
        """Validator should still enforce required report blocks."""
        invalid_report = _VALID_REPORT.replace("Open Risks: none\n", "")

        result = subprocess.run(
            [sys.executable, str(_VALIDATOR_PATH), "--report", invalid_report],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 1
        assert "INVALID:" in result.stdout
        assert "Missing required token: Open Risks:" in result.stdout
