"""Metrics analyzer for performance feedback generation."""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone
import json

from sop.tools.performance_metrics import PerformanceMetrics


class PerformanceRecommendation:
    """Single performance recommendation."""
    
    def __init__(
        self,
        recommendation_id: str,
        tool_name: str,
        issue: str,
        suggestion: str,
        priority: str,
    ):
        self.recommendation_id = recommendation_id
        self.tool_name = tool_name
        self.issue = issue
        self.suggestion = suggestion
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recommendation_id": self.recommendation_id,
            "tool_name": self.tool_name,
            "issue": self.issue,
            "suggestion": self.suggestion,
            "priority": self.priority,
        }


class MetricsAnalyzer:
    """Analyze performance metrics and generate recommendations."""
    
    def __init__(self, metrics: PerformanceMetrics):
        """Initialize analyzer with metrics.
        
        Args:
            metrics: PerformanceMetrics instance to analyze
        """
        self.metrics = metrics
        self.recommendations: List[PerformanceRecommendation] = []
        self._rec_counter = 0
    
    def analyze(self) -> List[PerformanceRecommendation]:
        """Analyze metrics and generate recommendations (idempotent).
        
        Returns:
            List of PerformanceRecommendation objects
        """
        # Clear previous recommendations (idempotent)
        self.recommendations = []
        self._rec_counter = 0
        
        if not self.metrics.records:
            return []
        
        # Group metrics by tool
        tool_metrics: Dict[str, List[Any]] = {}
        for record in self.metrics.records:
            if record.tool_name not in tool_metrics:
                tool_metrics[record.tool_name] = []
            tool_metrics[record.tool_name].append(record)
        
        # Analyze each tool
        for tool_name, records in tool_metrics.items():
            self._analyze_tool(tool_name, records)
        
        return self.recommendations
    
    def _get_unique_rec_id(self, base_timestamp: int) -> str:
        """Get unique recommendation ID with counter.
        
        Args:
            base_timestamp: Base timestamp in milliseconds
            
        Returns:
            Unique recommendation ID
        """
        rec_id = f"rec_{base_timestamp}_{self._rec_counter}"
        self._rec_counter += 1
        return rec_id
    
    def _analyze_tool(self, tool_name: str, records: List[Any]) -> None:
        """Analyze metrics for a single tool.
        
        Args:
            tool_name: Name of the tool
            records: List of ExecutionMetric records for this tool
        """
        if not records:
            return
        
        # Calculate statistics
        total = len(records)
        successful = sum(1 for r in records if r.success)
        _failed = total - successful  # noqa: F841
        success_rate = successful / total if total > 0 else 0
        
        avg_duration = sum(r.duration_ms for r in records) / total if total > 0 else 0
        _max_duration = max(r.duration_ms for r in records) if records else 0  # noqa: F841
        
        # Generate unique recommendation IDs with counter
        base_id = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # Check success rate
        if success_rate < 0.9:
            rec_id = self._get_unique_rec_id(base_id)
            self.recommendations.append(PerformanceRecommendation(
                recommendation_id=rec_id,
                tool_name=tool_name,
                issue=f"Success rate {success_rate:.1%} (below 90% threshold)",
                suggestion="Review error patterns in logs and investigate failure causes",
                priority="high" if success_rate < 0.7 else "medium",
            ))
        
        # Check execution time
        if avg_duration > 5000:  # 5 seconds
            rec_id = self._get_unique_rec_id(base_id)
            self.recommendations.append(PerformanceRecommendation(
                recommendation_id=rec_id,
                tool_name=tool_name,
                issue=f"Average duration {avg_duration:.0f}ms (above 5s threshold)",
                suggestion="Profile execution and identify performance bottlenecks",
                priority="medium",
            ))
        
        # Check for timeout patterns
        timeouts = sum(1 for r in records if r.exit_code == -1)
        if timeouts > 0:
            timeout_rate = timeouts / total
            rec_id = self._get_unique_rec_id(base_id)
            self.recommendations.append(PerformanceRecommendation(
                recommendation_id=rec_id,
                tool_name=tool_name,
                issue=f"Timeout rate {timeout_rate:.1%} ({timeouts} timeouts)",
                suggestion="Increase timeout threshold or optimize validator performance",
                priority="high",
            ))
    
    def save_recommendations(self, file_path: Path) -> None:
        """Save recommendations to JSON file (atomic write + replace).
        
        Args:
            file_path: Path to save recommendations
        """
        # Create envelope
        data = {
            "schema_version": "1.0.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "recommendations": [rec.to_dict() for rec in self.recommendations]
        }
        
        # Write to temp file first
        temp_path = file_path.parent / f"{file_path.name}.tmp"
        
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Atomic replace
        temp_path.replace(file_path)
    
    @classmethod
    def generate_report(cls, metrics_path: Path, report_path: Path) -> None:
        """Generate feedback report from metrics (convenience method).
        
        Args:
            metrics_path: Path to performance_metrics_latest.json
            report_path: Path to save performance_recommendations_latest.json
        """
        # Load metrics
        metrics = PerformanceMetrics.load_from_file(metrics_path)
        
        # Analyze
        analyzer = cls(metrics)
        analyzer.analyze()
        
        # Save report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        analyzer.save_recommendations(report_path)
