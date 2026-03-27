from pathlib import Path
from sop.tools.performance_metrics import PerformanceMetrics
from sop.tools.metrics_analyzer import MetricsAnalyzer

# Load metrics
metrics_path = Path("docs/context/performance_metrics_latest.json")
report_path = Path("docs/context/performance_recommendations_latest.json")

# Generate report
MetricsAnalyzer.generate_report(metrics_path, report_path)
print(f"✅ Report generated: {report_path}")
print(f"✅ File exists: {report_path.exists()}")
