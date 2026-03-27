"""Performance metrics model for validator tool execution tracking."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any
import json
from pathlib import Path


@dataclass
class ExecutionMetric:
    """Single execution metric record."""
    timestamp: str  # ISO 8601 with Z suffix (UTC)
    tool_name: str
    success: bool
    duration_ms: float
    exit_code: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """Performance metrics collection and storage."""
    
    schema_version: str = "1.0.0"
    records: List[ExecutionMetric] = None
    
    def __post_init__(self):
        """Initialize records list."""
        if self.records is None:
            self.records = []
    
    def add_metric(self, metric: ExecutionMetric) -> None:
        """Add a metric record."""
        self.records.append(metric)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "records": [record.to_dict() for record in self.records]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceMetrics":
        """Create from dictionary."""
        metrics = cls(schema_version=data.get("schema_version", "1.0.0"))
        for record_data in data.get("records", []):
            metric = ExecutionMetric(
                timestamp=record_data["timestamp"],
                tool_name=record_data["tool_name"],
                success=record_data["success"],
                duration_ms=record_data["duration_ms"],
                exit_code=record_data["exit_code"]
            )
            metrics.add_metric(metric)
        return metrics
    
    def save_to_file(self, file_path: Path) -> None:
        """Save metrics to JSON file (atomic write + replace)."""
        # Write to temp file first
        temp_path = file_path.parent / f"{file_path.name}.tmp"
        
        with open(temp_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        # Atomic replace
        temp_path.replace(file_path)
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> "PerformanceMetrics":
        """Load metrics from JSON file."""
        if not file_path.exists():
            return cls()
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
