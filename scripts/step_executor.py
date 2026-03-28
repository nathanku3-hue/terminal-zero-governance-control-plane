"""Phase 2.3 -- StepExecutor: extracted step execution from run_loop_cycle.py.

Replaces the run_python_step() inner closure with a proper class.
_run_command() is moved here as a private static method.

D-183: scripts/step_executor.py must be byte-identical to this file.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_step_ndjson(path: Path, trace_id: str, step: dict) -> None:
    """Append a step record as a NDJSON line (non-blocking best-effort)."""
    try:
        record = dict(step)
        record["trace_id"] = trace_id
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        pass


class StepExecutor:
    """Executes a subprocess step and records the result on LoopCycleRuntime.

    Replaces the run_python_step() inner closure from run_loop_cycle.py.
    _run_command() is a private static method here instead of a module-level
    helper in run_loop_cycle.py.

    Args:
        ctx: LoopCycleContext (duck-typed; needs .python_exe, .repo_root,
             .context_dir).
        runtime: LoopCycleRuntime (duck-typed; needs .steps, .trace_id,
                 .generated_at_utc).
        step_sla_seconds: SLA threshold in seconds (Phase 3.2). Steps
                          exceeding this duration get sla_breach=True.
                          Default 300.0.
    """

    def __init__(self, ctx: Any, runtime: Any, step_sla_seconds: float = 300.0) -> None:
        self.ctx = ctx
        self.runtime = runtime
        self.step_sla_seconds = step_sla_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        step_name: str,
        script_path: Path,
        script_args: list[str],
    ) -> None:
        """Execute *script_path* as a subprocess step and record the result.

        Appends the step record to runtime.steps and to the per-step NDJSON
        log.  If *script_path* does not exist, an ERROR record is appended
        without launching a subprocess.

        Args:
            step_name: Logical name for this step (appears in runtime.steps).
            script_path: Absolute path to the Python script to execute.
            script_args: Additional CLI arguments passed after the script path.
        """
        ndjson_path = self.ctx.context_dir / "loop_run_steps_latest.ndjson"
        if not script_path.exists():
            missing_step: dict[str, Any] = {
                "name": step_name,
                "status": "ERROR",
                "exit_code": None,
                "command": [],
                "started_utc": self.runtime.generated_at_utc,
                "ended_utc": self.runtime.generated_at_utc,
                "duration_seconds": 0.0,
                "stdout": "",
                "stderr": "",
                "message": f"Missing script: {script_path}",
                "sla_breach": False,
            }
            self.runtime.steps.append(missing_step)
            _append_step_ndjson(ndjson_path, self.runtime.trace_id, missing_step)
            return
        command = [self.ctx.python_exe, str(script_path)] + script_args
        step_result = self._run_command(
            step_name=step_name,
            command=command,
            cwd=self.ctx.repo_root,
        )
        # Phase 3.2 -- sla_breach flag
        step_result["sla_breach"] = (
            step_result.get("duration_seconds", 0.0) > self.step_sla_seconds
        )
        self.runtime.steps.append(step_result)
        _append_step_ndjson(ndjson_path, self.runtime.trace_id, step_result)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _run_command(
        step_name: str,
        command: list[str],
        cwd: Path,
    ) -> dict[str, Any]:
        """Run *command* in *cwd* and return a step record dict.

        Moved here from run_loop_cycle.py:~404 (_run_command module function).
        """
        started = _utc_now()
        started_utc = _utc_iso(started)
        start_mono = time.monotonic()
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as exc:
            ended = _utc_now()
            return {
                "name": step_name,
                "status": "ERROR",
                "exit_code": None,
                "command": command,
                "started_utc": started_utc,
                "ended_utc": _utc_iso(ended),
                "duration_seconds": round(time.monotonic() - start_mono, 3),
                "stdout": "",
                "stderr": "",
                "message": f"Execution error: {exc}",
            }
        ended = _utc_now()
        status = "PASS" if result.returncode == 0 else "FAIL"
        return {
            "name": step_name,
            "status": status,
            "exit_code": result.returncode,
            "command": command,
            "started_utc": started_utc,
            "ended_utc": _utc_iso(ended),
            "duration_seconds": round(time.monotonic() - start_mono, 3),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": "",
        }
