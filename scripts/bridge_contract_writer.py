"""Phase 4.1 -- BridgeContractWriter: translates execution truth into planner language.

Writes bridge_contract_current.md + JSON shadow after every run (PROCEED or HOLD).
D-183: scripts/bridge_contract_writer.py must be byte-identical to this file.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
_SCHEMA_FILENAME = "bridge_contract.schema.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_bcw_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            Path(tmp).unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _atomic_write_json(path: Path, data: Any) -> None:
    _atomic_write_text(path, json.dumps(data, indent=2) + "\n")


def _validate_against_schema(data: dict, schema_dir: Path) -> None:
    """Validate data against bridge_contract.schema.json if jsonschema is available."""
    schema_path = schema_dir / _SCHEMA_FILENAME
    if not schema_path.exists():
        return
    try:
        import jsonschema  # type: ignore[import]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        pass  # jsonschema not installed; skip validation


class BridgeContractWriter:
    """Derives bridge fields from run artifacts and writes MD + JSON shadow atomically.

    The bridge contract translates execution truth (loop_run_trace, gate results, drift)
    into planner language. It is written on every run regardless of PROCEED or HOLD so
    that a planner can always read what changed and what to do next without opening any
    other file.
    """

    def __init__(self, context_dir: Path, schema_dir: Path) -> None:
        self.context_dir = context_dir
        self.schema_dir = schema_dir

    def write(
        self,
        trace: dict,
        gate_a: dict,
        gate_b: dict,
        drift: dict,
    ) -> Path:
        """Derive bridge fields from artifacts; write MD + JSON shadow atomically.

        Args:
            trace: loop_run_trace_latest.json content
            gate_a: phase_gate_a_latest.json content (or {} if absent)
            gate_b: phase_gate_b_latest.json content (or {} if absent)
            drift: run_drift_latest.json content (or {} if absent)

        Returns:
            Path to the written JSON shadow.
        """
        trace_id = trace.get("trace_id", "unknown")
        generated_at = _utc_now_iso()

        # Derive gate_result
        gate_result = self._derive_gate_result(gate_a, gate_b)

        # Derive SYSTEM_DELTA
        system_delta = self._derive_system_delta(trace)

        # Derive PM_DELTA
        pm_delta = self._derive_pm_delta(trace, gate_b)

        # Derive OPEN_DECISION
        open_decision = self._derive_open_decision(gate_a, gate_b)

        # Derive RECOMMENDED_NEXT_STEP
        recommended_next_step = self._derive_recommended_next_step(
            gate_result, open_decision
        )

        # Derive DO_NOT_REDECIDE
        do_not_redecide = self._derive_do_not_redecide(gate_a, gate_b)

        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "trace_id": trace_id,
            "generated_at_utc": generated_at,
            "gate_result": gate_result,
            "system_delta": system_delta,
            "pm_delta": pm_delta,
            "open_decision": open_decision,
            "recommended_next_step": recommended_next_step,
            "do_not_redecide": do_not_redecide,
        }

        _validate_against_schema(payload, self.schema_dir)

        # Write JSON shadow
        json_path = self.context_dir / "bridge_contract_current.json"
        _atomic_write_json(json_path, payload)

        # Write Markdown surface
        md_path = self.context_dir / "bridge_contract_current.md"
        _atomic_write_text(md_path, self._render_markdown(payload))

        return json_path

    # ------------------------------------------------------------------
    # Field derivation helpers
    # ------------------------------------------------------------------

    def _derive_gate_result(self, gate_a: dict, gate_b: dict) -> str:
        """PROCEED if all gates pass (or absent); HOLD if any gate is HOLD."""
        for gate in (gate_a, gate_b):
            if gate.get("decision") == "HOLD":
                return "HOLD"
        return "PROCEED"

    def _derive_system_delta(self, trace: dict) -> str:
        """Summarise steps with status != PASS; if all PASS: 'All steps passed.'"""
        steps = trace.get("steps", []) or []
        non_pass = [
            s for s in steps
            if str(s.get("status", "")).upper() != "PASS"
        ]
        if not non_pass:
            return "All steps passed."
        parts = []
        for s in non_pass:
            name = s.get("name", "unknown")
            status = s.get("status", "UNKNOWN")
            msg = s.get("message", "") or s.get("stderr", "") or ""
            if msg:
                parts.append(f"{name}: {status} ({msg[:120]})")
            else:
                parts.append(f"{name}: {status}")
        return "; ".join(parts)

    def _derive_pm_delta(self, trace: dict, gate_b: dict) -> str:
        """Derive PM_DELTA from gate_b decision and baseline step count.

        Emits 'Insufficient history' when fewer than 2 baseline records exist.
        """
        baseline_path = self.context_dir / "run_regression_baseline.ndjson"
        records: list[dict] = []
        if baseline_path.exists():
            try:
                for line in baseline_path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped:
                        records.append(json.loads(stripped))
            except Exception:
                pass
        if len(records) < 2:
            return "Insufficient history"
        decision = gate_b.get("decision", "PROCEED")
        final_result = trace.get("final_result", "PASS")
        prev_step_count = records[-2].get("step_count", 0)
        curr_step_count = trace.get("metrics", {}).get("total_steps") or len(
            trace.get("steps", [])
        )
        delta = curr_step_count - prev_step_count
        direction = f"+{delta}" if delta >= 0 else str(delta)
        return (
            f"Gate: {decision}; result: {final_result}; "
            f"step count delta vs prior run: {direction}"
        )

    def _derive_open_decision(self, gate_a: dict, gate_b: dict) -> str:
        """HOLD reason from gate_a if present; else gate_b; else 'None'."""
        for gate in (gate_a, gate_b):
            if gate.get("decision") == "HOLD":
                conditions = gate.get("gate_conditions", []) or []
                failed = [
                    c.get("detail", c.get("name", ""))
                    for c in conditions
                    if not c.get("result", True)
                ]
                if failed:
                    return failed[0]
                return "Gate HOLD (no condition detail available)"
        return "None"

    def _derive_recommended_next_step(self, gate_result: str, open_decision: str) -> str:
        """If HOLD: 'Resolve: {hold_reason}'; if PROCEED: 'Begin next phase'."""
        if gate_result == "HOLD":
            return f"Resolve: {open_decision}"
        return "Begin next phase"

    def _derive_do_not_redecide(self, gate_a: dict, gate_b: dict) -> list[str]:
        """Gate PROCEED decisions are settled. Empty list on first run."""
        settled: list[str] = []
        for gate in (gate_a, gate_b):
            if gate.get("decision") == "PROCEED":
                from_phase = gate.get("from_phase", "")
                to_phase = gate.get("to_phase", "")
                if from_phase and to_phase:
                    settled.append(f"PROCEED: {from_phase} -> {to_phase}")
                else:
                    settled.append("PROCEED")
        return settled

    # ------------------------------------------------------------------
    # Markdown renderer
    # ------------------------------------------------------------------

    def _render_markdown(self, payload: dict) -> str:
        lines = [
            "# Bridge Contract",
            f"> GeneratedAtUTC: {payload['generated_at_utc']}",
            f"> TraceID: {payload['trace_id']}",
            f"> GateResult: {payload['gate_result']}",
            "",
            "## SYSTEM_DELTA",
            payload["system_delta"],
            "",
            "## PM_DELTA",
            payload["pm_delta"],
            "",
            "## OPEN_DECISION",
            payload["open_decision"],
            "",
            "## RECOMMENDED_NEXT_STEP",
            payload["recommended_next_step"],
            "",
            "## DO_NOT_REDECIDE",
        ]
        dnd = payload.get("do_not_redecide") or []
        if dnd:
            for item in dnd:
                lines.append(f"- {item}")
        else:
            lines.append("_(none on first run)_")
        lines.append("")
        return "\n".join(lines)
