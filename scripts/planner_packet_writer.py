"""Phase 4.2 -- PlannerPacketWriter: compact fresh-context packet for planner entry.

Writes planner_packet_current.md + JSON shadow after every run.
A fresh worker loading planner_packet_current.md gets the full picture without
reading the whole repo.

D-183: scripts/planner_packet_writer.py must be byte-identical to this file.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
_SCHEMA_FILENAME = "planner_packet.schema.json"
_DECISION_TAIL_JSON_CAP = 10
_DECISION_TAIL_MD_DISPLAY = 3


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_ppw_", suffix=".tmp")
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
    """Validate data against planner_packet.schema.json if jsonschema is available."""
    schema_path = schema_dir / _SCHEMA_FILENAME
    if not schema_path.exists():
        return
    try:
        import jsonschema  # type: ignore[import]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        pass


class PlannerPacketWriter:
    """Builds planner packet from artifacts and writes MD + JSON shadow atomically.

    The planner packet is the single entry point for a fresh worker. Loading
    planner_packet_current.md alone is sufficient to reconstruct the full
    current situation without reading any other file.
    """

    def __init__(self, context_dir: Path, schema_dir: Path) -> None:
        self.context_dir = context_dir
        self.schema_dir = schema_dir

    def write(
        self,
        trace: dict,
        bridge: dict,
        gate_a: dict,
        gate_b: dict,
        prior_packet: dict | None,
    ) -> Path:
        """Build planner packet from artifacts; write MD + JSON shadow atomically.

        Args:
            trace: loop_run_trace_latest.json content
            bridge: bridge_contract JSON shadow content
            gate_a: phase_gate_a_latest.json content (or {} if absent)
            gate_b: phase_gate_b_latest.json content (or {} if absent)
            prior_packet: previous planner_packet JSON shadow (for decision tail),
                          or None on first run.

        Returns:
            Path to the written JSON shadow.
        """
        trace_id = trace.get("trace_id", "unknown")
        generated_at = _utc_now_iso()
        run_result = trace.get("final_result", "PASS")

        current_context = self._derive_current_context(trace)
        active_brief = self._derive_active_brief()
        bridge_truth_summary = self._derive_bridge_truth_summary(bridge)
        decision_tail = self._derive_decision_tail(bridge, prior_packet)
        blocked_next_step = bridge.get("open_decision", "None")
        active_bottleneck = self._derive_active_bottleneck(gate_a, gate_b)

        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "trace_id": trace_id,
            "generated_at_utc": generated_at,
            "run_result": run_result,
            "current_context": current_context,
            "active_brief": active_brief,
            "bridge_truth_summary": bridge_truth_summary,
            "decision_tail": decision_tail,
            "blocked_next_step": blocked_next_step,
            "active_bottleneck": active_bottleneck,
        }

        _validate_against_schema(payload, self.schema_dir)

        json_path = self.context_dir / "planner_packet_current.json"
        _atomic_write_json(json_path, payload)

        md_path = self.context_dir / "planner_packet_current.md"
        _atomic_write_text(md_path, self._render_markdown(payload))

        return json_path

    # ------------------------------------------------------------------
    # Field derivation helpers
    # ------------------------------------------------------------------

    def _derive_current_context(self, trace: dict) -> str:
        generated_at = trace.get("generated_at_utc", "unknown")
        final_result = trace.get("final_result", "PASS")
        repo_id = trace.get("repo_id", "quant_current_scope")
        metrics = trace.get("metrics", {}) or {}
        total_steps = metrics.get("total_steps", len(trace.get("steps", [])))
        pass_count = metrics.get("pass_count", 0)
        return (
            f"System: {repo_id}. Last run at {generated_at} achieved {final_result} "
            f"({pass_count}/{total_steps} steps passed). "
            f"Phase 4 bridge/planner/state surfaces are active."
        )

    def _derive_active_brief(self) -> str:
        """Attempt exec_memory_packet_latest.json.get('active_brief'); fall back gracefully."""
        exec_memory_path = self.context_dir / "exec_memory_packet_latest.json"
        if exec_memory_path.exists():
            try:
                packet = json.loads(exec_memory_path.read_text(encoding="utf-8"))
                brief = packet.get("active_brief")
                if brief and str(brief).strip():
                    return str(brief).strip()
            except Exception:
                pass
        return "Advance to next phase"

    def _derive_bridge_truth_summary(self, bridge: dict) -> str:
        """SYSTEM_DELTA + RECOMMENDED_NEXT_STEP from bridge JSON shadow."""
        system_delta = bridge.get("system_delta", "(no system delta)")
        recommended = bridge.get("recommended_next_step", "(no recommendation)")
        return f"SYSTEM_DELTA: {system_delta} | RECOMMENDED_NEXT_STEP: {recommended}"

    def _derive_decision_tail(
        self, bridge: dict, prior_packet: dict | None
    ) -> list[str]:
        """Merge prior tail + new DO_NOT_REDECIDE entries; cap at 10; prune oldest first."""
        prior_tail: list[str] = []
        if prior_packet is not None:
            raw = prior_packet.get("decision_tail") or []
            prior_tail = [str(x) for x in raw]

        new_decisions = bridge.get("do_not_redecide") or []
        combined = prior_tail + [str(d) for d in new_decisions]

        # Deduplicate preserving order (keep last occurrence)
        seen: set[str] = set()
        deduped: list[str] = []
        for item in reversed(combined):
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        deduped.reverse()

        # Cap at JSON shadow limit (keep most recent)
        return deduped[-_DECISION_TAIL_JSON_CAP:]

    def _derive_active_bottleneck(self, gate_a: dict, gate_b: dict) -> str:
        """First HOLD reason from gate_a or gate_b; else first drift alert; else 'None'."""
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
        # Check drift
        drift_path = self.context_dir / "run_drift_latest.json"
        if drift_path.exists():
            try:
                drift = json.loads(drift_path.read_text(encoding="utf-8"))
                alerts = drift.get("alerts") or []
                if alerts:
                    return alerts[0].get("message", "Drift alert detected")
            except Exception:
                pass
        return "None"

    # ------------------------------------------------------------------
    # Markdown renderer
    # ------------------------------------------------------------------

    def _render_markdown(self, payload: dict) -> str:
        tail = payload.get("decision_tail") or []
        tail_display = tail[-_DECISION_TAIL_MD_DISPLAY:] if tail else []

        lines = [
            "# Planner Packet",
            f"> GeneratedAtUTC: {payload['generated_at_utc']}",
            f"> TraceID: {payload['trace_id']}",
            f"> RunResult: {payload['run_result']}",
            "",
            "## Current Context",
            payload["current_context"],
            "",
            "## Active Brief",
            payload["active_brief"],
            "",
            "## Bridge Truth",
            payload["bridge_truth_summary"],
            "",
            "## Decision Tail",
        ]
        if tail_display:
            for item in reversed(tail_display):
                lines.append(f"- {item}")
        else:
            lines.append("_(none on first run)_")
        lines += [
            "",
            "## Blocked Next Step",
            payload["blocked_next_step"],
            "",
            "## Active Bottleneck",
            payload["active_bottleneck"],
            "",
        ]
        return "\n".join(lines)
