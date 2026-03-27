"""Integration tests for validator tool wrappers."""

import tempfile
from pathlib import Path

import pytest

from sop.tools.validators import (
    ClosurePacketTool,
    ArchitectCalibrationTool,
    SawReportBlocksTool,
)
from sop.tools.tool_error import ToolError


class TestClosurePacketTool:
    """Integration tests for ClosurePacketTool"""

    def test_tool_creation_from_descriptor(self):
        """Test creating tool from descriptor"""
        repo_root = Path(".")
        tool = ClosurePacketTool.create(repo_root)
        assert tool.name == "validate_closure_packet"
        assert tool.descriptor is not None
        assert tool.input_schema is not None

    def test_tool_execution_valid_input(self):
        """Test executing tool with valid input"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            # Execute with valid ClosurePacket format
            result = tool.execute(
                packet="ClosurePacket: RoundID=1; ScopeID=1; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS"
            )
            assert "valid" in result
            assert "exit_code" in result
            assert isinstance(result["valid"], bool)

    def test_tool_execution_with_optional_flags(self):
        """Test executing tool with optional boolean flags"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            result = tool.execute(
                packet="ClosurePacket: RoundID=1; ScopeID=1; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=test",
                require_open_risks_when_block=True,
            )
            assert "valid" in result
            assert "exit_code" in result

    def test_tool_execution_invalid_input_missing_required(self):
        """Test executing tool with missing required field"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            with pytest.raises(ToolError, match="Missing required field"):
                tool.execute()  # Missing packet

    def test_tool_execution_invalid_packet_format(self):
        """Test executing tool with invalid packet format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            result = tool.execute(packet="invalid packet format")
            assert result["valid"] is False

    def test_descriptor_roundtrip(self):
        """Test descriptor loads and serializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            descriptor_dict = tool.descriptor.to_dict()
            assert descriptor_dict is not None
            assert descriptor_dict["name"] == "validate_closure_packet"
            assert "input_schema" in descriptor_dict
            assert "output_schema" in descriptor_dict


class TestArchitectCalibrationTool:
    """Integration tests for ArchitectCalibrationTool"""

    def test_tool_creation_from_descriptor(self):
        """Test creating tool from descriptor"""
        repo_root = Path(".")
        tool = ArchitectCalibrationTool.create(repo_root)
        assert tool.name == "validate_architect_calibration"
        assert tool.descriptor is not None

    def test_tool_execution_valid_input(self):
        """Test executing tool with valid input"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ArchitectCalibrationTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            # Required fields: history_csv, active_profile
            result = tool.execute(
                history_csv="/path/to/history.csv",
                active_profile="test_profile"
            )
            assert "valid" in result
            assert "exit_code" in result

    def test_tool_execution_invalid_input(self):
        """Test executing tool with invalid input"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ArchitectCalibrationTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            with pytest.raises(ToolError):
                tool.execute()  # Missing required field

    def test_descriptor_roundtrip(self):
        """Test descriptor loads and serializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ArchitectCalibrationTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            descriptor_dict = tool.descriptor.to_dict()
            assert descriptor_dict is not None
            assert descriptor_dict["name"] == "validate_architect_calibration"


class TestSawReportBlocksTool:
    """Integration tests for SawReportBlocksTool"""

    def test_tool_creation_from_descriptor(self):
        """Test creating tool from descriptor"""
        repo_root = Path(".")
        tool = SawReportBlocksTool.create(repo_root)
        assert tool.name == "validate_saw_report_blocks"
        assert tool.descriptor is not None

    def test_tool_execution_valid_input(self):
        """Test executing tool with valid input"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = SawReportBlocksTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            # Check descriptor for required fields
            result = tool.execute(
                report="SAWBlock: test block content"
            )
            assert "valid" in result
            assert "exit_code" in result

    def test_tool_execution_invalid_input(self):
        """Test executing tool with invalid input"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = SawReportBlocksTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            with pytest.raises(ToolError):
                tool.execute()  # Missing required field

    def test_descriptor_roundtrip(self):
        """Test descriptor loads and serializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = SawReportBlocksTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            descriptor_dict = tool.descriptor.to_dict()
            assert descriptor_dict is not None
            assert descriptor_dict["name"] == "validate_saw_report_blocks"


class TestValidatorToolContract:
    """Test that ValidatorTool preserves Stream 1 contract"""

    def test_validate_input_called_before_execution(self):
        """Test that validate_input is called before marshalling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            
            # Missing required field should raise ToolError from validate_input
            with pytest.raises(ToolError, match="Missing required field"):
                tool.execute()  # No packet provided

    def test_constraint_validation_enforced(self):
        """Test that constraint validation is enforced"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = Path(tmpdir) / "metrics.json"
            
            # Invalid input should be caught by validate_input
            with pytest.raises(ToolError):
                tool.execute(unknown_field="value")  # Unknown field
