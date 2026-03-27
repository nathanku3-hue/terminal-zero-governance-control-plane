"""Integration tests for Stream 3 performance metrics collection."""

import tempfile
from pathlib import Path
import json

import pytest

from sop.tools.validators import ClosurePacketTool
from sop.tools.performance_metrics import PerformanceMetrics, ExecutionMetric


class TestPerformanceMetricsModel:
    """Test PerformanceMetrics model."""

    def test_create_metric(self):
        """Test creating an execution metric."""
        metric = ExecutionMetric(
            timestamp="2026-03-29T10:30:45.123456Z",
            tool_name="test_tool",
            success=True,
            duration_ms=245.67,
            exit_code=0
        )
        assert metric.tool_name == "test_tool"
        assert metric.success is True
        assert metric.exit_code == 0

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = PerformanceMetrics()
        metric = ExecutionMetric(
            timestamp="2026-03-29T10:30:45.123456Z",
            tool_name="test_tool",
            success=True,
            duration_ms=245.67,
            exit_code=0
        )
        metrics.add_metric(metric)
        
        data = metrics.to_dict()
        assert data["schema_version"] == "1.0.0"
        assert "generated_at_utc" in data
        assert len(data["records"]) == 1
        assert data["records"][0]["tool_name"] == "test_tool"

    def test_metrics_from_dict(self):
        """Test creating metrics from dictionary."""
        data = {
            "schema_version": "1.0.0",
            "generated_at_utc": "2026-03-29T10:30:45.123456Z",
            "records": [
                {
                    "timestamp": "2026-03-29T10:30:45.123456Z",
                    "tool_name": "test_tool",
                    "success": True,
                    "duration_ms": 245.67,
                    "exit_code": 0
                }
            ]
        }
        metrics = PerformanceMetrics.from_dict(data)
        assert len(metrics.records) == 1
        assert metrics.records[0].tool_name == "test_tool"

    def test_metrics_save_and_load(self):
        """Test atomic save and load of metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "metrics.json"
            
            # Create and save metrics
            metrics = PerformanceMetrics()
            metric = ExecutionMetric(
                timestamp="2026-03-29T10:30:45.123456Z",
                tool_name="test_tool",
                success=True,
                duration_ms=245.67,
                exit_code=0
            )
            metrics.add_metric(metric)
            metrics.save_to_file(metrics_path)
            
            # Verify file exists
            assert metrics_path.exists()
            
            # Load and verify
            loaded = PerformanceMetrics.load_from_file(metrics_path)
            assert len(loaded.records) == 1
            assert loaded.records[0].tool_name == "test_tool"

    def test_metrics_atomic_rewrite(self):
        """Test that save uses atomic rewrite (temp + replace)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "metrics.json"
            
            # Save first version
            metrics1 = PerformanceMetrics()
            metrics1.add_metric(ExecutionMetric(
                timestamp="2026-03-29T10:30:45.123456Z",
                tool_name="tool1",
                success=True,
                duration_ms=100.0,
                exit_code=0
            ))
            metrics1.save_to_file(metrics_path)
            
            # Save second version (should replace, not append)
            metrics2 = PerformanceMetrics()
            metrics2.add_metric(ExecutionMetric(
                timestamp="2026-03-29T10:31:00.000000Z",
                tool_name="tool2",
                success=False,
                duration_ms=200.0,
                exit_code=1
            ))
            metrics2.save_to_file(metrics_path)
            
            # Load and verify only second version exists
            loaded = PerformanceMetrics.load_from_file(metrics_path)
            assert len(loaded.records) == 1
            assert loaded.records[0].tool_name == "tool2"

    def test_metrics_load_nonexistent_file(self):
        """Test loading from nonexistent file returns empty metrics."""
        metrics = PerformanceMetrics.load_from_file(Path("/nonexistent/path.json"))
        assert len(metrics.records) == 0
        assert metrics.schema_version == "1.0.0"


class TestValidatorToolMetricsCollection:
    """Test metrics collection in ValidatorTool."""

    def test_tool_records_success_metric(self):
        """Test that successful execution records metric."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "metrics.json"
            
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = metrics_path
            
            # Execute tool
            result = tool.execute(
                packet="ClosurePacket: RoundID=1; ScopeID=1; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS"
            )
            
            # Verify metric was recorded
            assert metrics_path.exists()
            metrics = PerformanceMetrics.load_from_file(metrics_path)
            assert len(metrics.records) >= 1
            assert metrics.records[-1].tool_name == "validate_closure_packet"
            assert metrics.records[-1].success is True
            assert metrics.records[-1].duration_ms > 0

    def test_tool_records_failure_metric(self):
        """Test that failed execution records metric."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "metrics.json"
            
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = metrics_path
            
            # Execute tool with invalid input
            result = tool.execute(packet="invalid packet")
            
            # Verify metric was recorded
            assert metrics_path.exists()
            metrics = PerformanceMetrics.load_from_file(metrics_path)
            assert len(metrics.records) >= 1
            assert metrics.records[-1].tool_name == "validate_closure_packet"
            assert metrics.records[-1].success is False

    def test_metrics_nonblocking_on_write_failure(self):
        """Test that metrics write failure doesn't block execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a path that will fail to write
            metrics_path = Path(tmpdir) / "readonly" / "metrics.json"
            
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = metrics_path
            
            # Execute tool - should succeed despite metrics write failure
            result = tool.execute(
                packet="ClosurePacket: RoundID=1; ScopeID=1; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS"
            )
            
            # Execution should succeed
            assert result is not None
            assert "valid" in result

    def test_metrics_append_multiple_records(self):
        """Test that multiple executions append to metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "metrics.json"
            
            repo_root = Path(".")
            tool = ClosurePacketTool.create(repo_root)
            tool.metrics_path = metrics_path
            
            # Execute tool twice
            tool.execute(packet="ClosurePacket: RoundID=1; ScopeID=1; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS")
            tool.execute(packet="ClosurePacket: RoundID=2; ScopeID=1; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK")
            
            # Verify both metrics recorded
            metrics = PerformanceMetrics.load_from_file(metrics_path)
            assert len(metrics.records) >= 2
