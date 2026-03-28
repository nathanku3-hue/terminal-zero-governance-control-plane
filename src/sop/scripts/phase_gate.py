"""Phase 2.2 — PhaseGate: automated phase-gate evaluator.

Evaluates three built-in gate conditions against the current runtime state,
emits a gate artifact, and optionally writes a phase handoff artifact.

Gate conditions:
  exec_memory_cycle_ready  -- runtime.exec_memory_cycle_ready is True
  no_schema_violations     -- loop_run_trace_latest.json final_result != 'ERROR'
  no_error_steps           -- no step in runtime.steps has status 'ERROR'

Decision: PROCEED if all pass; HOLD if any fail.

D-183: scripts/phase_gate.py must be byte-identical to this file.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_pg_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(data, indent=2) + "\n")
        os.replace(tmp, path)
    except Exception:
        try:
            Path(tmp).unlink(missing_ok=True)
        except Exception:
            pass
        raise


@dataclass
class PhaseGateResult:
    """Result bundle from PhaseGate.evaluate()."""

    all_conditions_met: bool
    decision: str  # PROCEED | HOLD
    conditions: list[dict[str, Any]] = field(default_factory=list)


class PhaseGate:
    """Evaluates automated phase-gate conditions and emits artifacts.

    Args:
        from_phase: Source phase name (e.g. 'exec_memory').
        to_phase: Target phase name (e.g. 'advisory').
        repo_root: Repository root path (used to locate context artifacts).
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, from_phase: str, to_phase: str, repo_root: Path) -> None:
        self.from_phase = from_phase
        self.to_phase = to_phase
        self.repo_root = repo_root

    def evaluate(self, runtime: Any) -> PhaseGateResult:
        """Evaluate built-in gate conditions against *runtime*.

        Args:
            runtime: LoopCycleRuntime instance (typed as Any to avoid circular
                     imports; duck-typed against .exec_memory_cycle_ready and
                     .steps).

        Returns:
            PhaseGateResult with decision PROCEED or HOLD.
        """
        conditions: list[dict[str, Any]] = []

        # Condition 1: exec_memory_cycle_ready
        em_ready = bool(getattr(runtime, "exec_memory_cycle_ready", False))
        conditions.append(
            {
                "name": "exec_memory_cycle_ready",
                "result": em_ready,
                "detail": (
                    "runtime.exec_memory_cycle_ready is True"
                    if em_ready
                    else "runtime.exec_memory_cycle_ready is False"
                ),
            }
        )

        # Condition 2: no_schema_violations -- trace final_result != ERROR
        context_dir = self.repo_root / "docs" / "context"
        trace_path = context_dir / "loop_run_trace_latest.json"
        no_schema_violations = True
        trace_detail = "loop_run_trace_latest.json not present (skipped)"
        if trace_path.exists():
            try:
                trace_data = json.loads(trace_path.read_text(encoding="utf-8"))
                trace_result = str(trace_data.get("final_result", "")).upper()
                if trace_result == "ERROR":
                    no_schema_violations = False
                    trace_detail = "loop_run_trace_latest.json final_result=ERROR"
                else:
                    trace_detail = f"loop_run_trace_latest.json final_result={trace_result}"
            except Exception as exc:
                no_schema_violations = False
                trace_detail = f"Failed to read loop_run_trace_latest.json: {exc}"
        conditions.append(
            {
                "name": "no_schema_violations",
                "result": no_schema_violations,
                "detail": trace_detail,
            }
        )

        # Condition 3: no_error_steps
        steps = getattr(runtime, "steps", []) or []
        error_steps = [
            s.get("name", "")
            for s in steps
            if str(s.get("status", "")).upper() == "ERROR"
        ]
        no_error_steps = len(error_steps) == 0
        conditions.append(
            {
                "name": "no_error_steps",
                "result": no_error_steps,
                "detail": (
                    "no ERROR steps"
                    if no_error_steps
                    else f"ERROR steps: {error_steps}"
                ),
            }
        )

        all_met = all(c["result"] for c in conditions)
        decision = "PROCEED" if all_met else "HOLD"
        return PhaseGateResult(
            all_conditions_met=all_met,
            decision=decision,
            conditions=conditions,
        )

    def emit(
        self,
        result: PhaseGateResult,
        trace_id: str,
        *,
        output_path: Path | None = None,
    ) -> Path:
        """Write the gate artifact atomically and return the path."""
        label = f"{self.from_phase}_to_{self.to_phase}"
        if output_path is None:
            context_dir = self.repo_root / "docs" / "context"
            output_path = context_dir / f"phase_gate_{label}_latest.json"

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "evaluated_at_utc": _utc_now_iso(),
            "trace_id": trace_id,
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "gate_conditions": [
                {"name": c["name"], "result": c["result"], "detail": c.get("detail", "")}
                for c in result.conditions
            ],
            "all_conditions_met": result.all_conditions_met,
            "decision": result.decision,
        }
        _atomic_write_json(output_path, payload)
        return output_path

    def evaluate_dry_run(self, context_dir: Path) -> PhaseGateResult:
        """Evaluate gate conditions without writing any artifacts (Phase 3.2).

        Gate A: exec_memory_packet_latest.json exists AND checkpoint has
                exec_memory_cycle_ready: true.
        Gate B: loop_run_trace_latest.json no_schema_violations + no_error_steps.

        No files are written. Returns PhaseGateResult with PROCEED or HOLD.
        """
        conditions: list[dict[str, Any]] = []

        # Gate A
        checkpoint_path = context_dir / "loop_cycle_checkpoint_latest.json"
        exec_memory_path = context_dir / "exec_memory_packet_latest.json"
        em_ready = False
        em_detail = "exec_memory_packet_latest.json missing or checkpoint not ready"
        if exec_memory_path.exists() and checkpoint_path.exists():
            try:
                cp = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                if bool(cp.get("exec_memory_cycle_ready", False)):
                    em_ready = True
                    em_detail = "exec_memory_packet_latest.json exists and checkpoint ready"
            except Exception as exc:
                em_detail = f"checkpoint read error: {exc}"
        conditions.append(
            {"name": "exec_memory_cycle_ready", "result": em_ready, "detail": em_detail}
        )

        # Gate B
        trace_path = context_dir / "loop_run_trace_latest.json"
        no_schema_violations = False
        no_error_steps = False
        b_detail = "loop_run_trace_latest.json not found"
        if trace_path.exists():
            try:
                trace_data = json.loads(trace_path.read_text(encoding="utf-8"))
                trace_result = str(trace_data.get("final_result", "")).upper()
                no_schema_violations = trace_result != "ERROR"
                steps = trace_data.get("steps", []) or []
                error_steps = [
                    s.get("name", "")
                    for s in steps
                    if str(s.get("status", "")).upper() == "ERROR"
                ]
                no_error_steps = len(error_steps) == 0
                b_detail = f"final_result={trace_result}; error_steps={error_steps}"
            except Exception as exc:
                b_detail = f"trace read error: {exc}"
        conditions.append(
            {"name": "no_schema_violations", "result": no_schema_violations, "detail": b_detail}
        )
        conditions.append(
            {"name": "no_error_steps", "result": no_error_steps, "detail": b_detail}
        )

        all_met = all(c["result"] for c in conditions)
        decision = "PROCEED" if all_met else "HOLD"
        return PhaseGateResult(
            all_conditions_met=all_met,
            decision=decision,
            conditions=conditions,
        )

    def emit_handoff(
        self,
        trace_id: str,
        *,
        output_path: Path | None = None,
    ) -> Path:
        """Write the phase handoff artifact (called only on PROCEED)."""
        if output_path is None:
            context_dir = self.repo_root / "docs" / "context"
            output_path = context_dir / "phase_handoff_latest.json"

        payload = {
            "schema_version": "1.0",
            "trace_id": trace_id,
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "triggered_at_utc": _utc_now_iso(),
        }
        _atomic_write_json(output_path, payload)
        return output_path
