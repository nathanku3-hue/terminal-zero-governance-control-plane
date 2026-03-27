"""ValidatorTool base class for wrapping validator scripts as tools."""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sop.tools.tool import Tool
from sop.tools.tool_error import ToolExecutionError
from sop.tools.argument_marshaller import ArgumentMarshaller
from sop.tools.performance_metrics import PerformanceMetrics, ExecutionMetric
from sop.descriptors import ValidatorDescriptor


class ValidatorTool(Tool):
    """Wraps a validator script as a Tool (repo-scoped)."""

    def __init__(
        self,
        validator_script_path: str,
        descriptor: ValidatorDescriptor,
        repo_root: Path,
        metrics_path: Optional[Path] = None,
    ):
        """Initialize validator tool from script and descriptor.

        Args:
            validator_script_path: Path to validator .py script (relative to repo_root)
            descriptor: ValidatorDescriptor with CLI contract
            repo_root: Path to repo root (for resolving script path)
            metrics_path: Optional override for metrics file path (for testing)

        Raises:
            ToolExecutionError: If script not found
        """
        super().__init__(
            name=descriptor.name,
            description=descriptor.description,
            input_schema=descriptor.input_schema,
            output_schema=descriptor.output_schema,
        )
        self.validator_script = repo_root / validator_script_path
        self.descriptor = descriptor
        self.repo_root = repo_root
        self.metrics_path = metrics_path or (repo_root / "docs" / "context" / "performance_metrics_latest.json")

        if not self.validator_script.exists():
            raise ToolExecutionError(f"Validator script not found: {self.validator_script}")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute validator script with given inputs.

        Args:
            **kwargs: Input parameters matching input_schema

        Returns:
            Dict with 'valid', 'output', 'exit_code' keys

        Raises:
            ToolExecutionError: If execution fails
        """
        # Stream 1 contract: validate input BEFORE marshalling
        self.validate_input(**kwargs)

        # Use ArgumentMarshaller to convert kwargs to CLI args
        marshaller = ArgumentMarshaller()
        cli_args = marshaller.marshal(kwargs, self.input_schema)

        cmd = [sys.executable, str(self.validator_script)] + cli_args

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.repo_root),
            )
            duration_ms = (time.time() - start_time) * 1000

            # Collect metrics (Stream 3) - record all outcomes
            self._record_metric(
                success=result.returncode == 0,
                duration_ms=duration_ms,
                exit_code=result.returncode
            )

            return {
                "valid": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - start_time) * 1000
            self._record_metric(success=False, duration_ms=duration_ms, exit_code=-1)
            raise ToolExecutionError(f"Validator timeout: {self.name}")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._record_metric(success=False, duration_ms=duration_ms, exit_code=-1)
            raise ToolExecutionError(f"Validator execution failed: {e}")

    def _record_metric(self, success: bool, duration_ms: float, exit_code: int) -> None:
        """Record execution metric (Stream 3 - metrics collection).
        
        Args:
            success: Whether execution was successful
            duration_ms: Execution duration in milliseconds
            exit_code: Process exit code
        """
        try:
            # Load existing metrics
            metrics = PerformanceMetrics.load_from_file(self.metrics_path)
            
            # Add new metric
            metric = ExecutionMetric(
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                tool_name=self.name,
                success=success,
                duration_ms=duration_ms,
                exit_code=exit_code
            )
            metrics.add_metric(metric)
            
            # Save atomically
            self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics.save_to_file(self.metrics_path)
        except Exception as e:
            # Log but don't fail execution if metrics collection fails
            print(f"Warning: Failed to record metric: {e}", file=sys.stderr)
