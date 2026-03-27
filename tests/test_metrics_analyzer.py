"""Tests for MetricsAnalyzer."""

import tempfile
from pathlib import Path

import pytest

from sop.tools.performance_metrics import PerformanceMetrics, ExecutionMetric
from sop.tools.metrics_analyzer import MetricsAnalyzer, PerformanceRecommendation


class TestMetricsAnalyzer:
    """Test MetricsAnalyzer."""

    def test_analyzer_creation(self):
        """Test creating analyzer."""
        metrics = PerformanceMetrics()
        analyzer = MetricsAnalyzer(metrics)
        assert analyzer.metrics is not None
        assert len(analyzer.recommendations) == 0

    def test_analyze_empty_metrics(self):
        """Test analyzing empty metrics."""
        metrics = PerformanceMetrics()
        analyzer = MetricsAnalyzer(metrics)
        recommendations = analyzer.analyze()
        assert len(recommendations) == 0

    def test_analyze_high_success_rate(self):
        """Test analyzing metrics with high success rate."""
        metrics = PerformanceMetrics()
        for i in range(10):
            metrics.add_metric(ExecutionMetric(
                timestamp=f"2026-03-29T10:30:{i:02d}.000000Z",
                tool_name="test_tool",
                success=True,
                duration_ms=100.0,
                exit_code=0
            ))
        
        analyzer = MetricsAnalyzer(metrics)
        recommendations = analyzer.analyze()
        # No recommendations for 100% success rate
        assert len(recommendations) == 0

    def test_analyze_low_success_rate(self):
        """Test analyzing metrics with low success rate."""
        metrics = PerformanceMetrics()
        # 7 successes, 3 failures = 70% success rate
        for i in range(7):
            metrics.add_metric(ExecutionMetric(
                timestamp=f"2026-03-29T10:30:{i:02d}.000000Z",
                tool_name="test_tool",
                success=True,
                duration_ms=100.0,
                exit_code=0
            ))
        for i in range(3):
            metrics.add_metric(ExecutionMetric(
                timestamp=f"2026-03-29T10:31:{i:02d}.000000Z",
                tool_name="test_tool",
                success=False,
                duration_ms=100.0,
                exit_code=1
            ))
        
        analyzer = MetricsAnalyzer(metrics)
        recommendations = analyzer.analyze()
        # Should have recommendation for low success rate
        assert len(recommendations) > 0
        assert any("Success rate" in rec.issue for rec in recommendations)

    def test_analyze_slow_execution(self):
        """Test analyzing metrics with slow execution."""
        metrics = PerformanceMetrics()
        for i in range(5):
            metrics.add_metric(ExecutionMetric(
                timestamp=f"2026-03-29T10:30:{i:02d}.000000Z",
                tool_name="slow_tool",
                success=True,
                duration_ms=10000.0,  # 10 seconds
                exit_code=0
            ))
        
        analyzer = MetricsAnalyzer(metrics)
        recommendations = analyzer.analyze()
        # Should have recommendation for slow execution
        assert len(recommendations) > 0
        assert any("duration" in rec.issue.lower() for rec in recommendations)

    def test_analyze_timeout_pattern(self):
        """Test analyzing metrics with timeout pattern."""
        metrics = PerformanceMetrics()
        # 8 successes, 2 timeouts
        for i in range(8):
            metrics.add_metric(ExecutionMetric(
                timestamp=f"2026-03-29T10:30:{i:02d}.000000Z",
                tool_name="timeout_tool",
                success=True,
                duration_ms=100.0,
                exit_code=0
            ))
        for i in range(2):
            metrics.add_metric(ExecutionMetric(
                timestamp=f"2026-03-29T10:31:{i:02d}.000000Z",
                tool_name="timeout_tool",
                success=False,
                duration_ms=30000.0,
                exit_code=-1
            ))
        
        analyzer = MetricsAnalyzer(metrics)
        recommendations = analyzer.analyze()
        # Should have recommendation for timeout pattern
        assert len(recommendations) > 0
        assert any("timeout" in rec.issue.lower() for rec in recommendations)

    def test_recommendation_to_dict(self):
        """Test converting recommendation to dict."""
        rec = PerformanceRecommendation(
            recommendation_id="rec_001",
            tool_name="test_tool",
            issue="Test issue",
            suggestion="Test suggestion",
            priority="high"
        )
        data = rec.to_dict()
        assert data["recommendation_id"] == "rec_001"
        assert data["tool_name"] == "test_tool"
        assert data["issue"] == "Test issue"
        assert data["suggestion"] == "Test suggestion"
        assert data["priority"] == "high"

    def test_save_recommendations(self):
        """Test saving recommendations to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = PerformanceMetrics()
            for i in range(7):
                metrics.add_metric(ExecutionMetric(
                    timestamp=f"2026-03-29T10:30:{i:02d}.000000Z",
                    tool_name="test_tool",
                    success=True,
                    duration_ms=100.0,
                    exit_code=0
                ))
            for i in range(3):
                metrics.add_metric(ExecutionMetric(
                    timestamp=f"2026-03-29T10:31:{i:02d}.000000Z",
                    tool_name="test_tool",
                    success=False,
                    duration_ms=100.0,
                    exit_code=1
                ))
            
            analyzer = MetricsAnalyzer(metrics)
            analyzer.analyze()
            
            file_path = Path(tmpdir) / "recommendations.json"
            analyzer.save_recommendations(file_path)
            
            # Verify file exists
            assert file_path.exists()
            
            # Verify content
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert data["schema_version"] == "1.0.0"
            assert "generated_at_utc" in data
            assert len(data["recommendations"]) > 0
