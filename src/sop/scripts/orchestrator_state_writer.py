"""Phase 4.3 / Phase 5.1 -- OrchestratorStateWriter: authoritative current state for the orchestrator.

Writes orchestrator_state_latest.json after every run. A fresh orchestrator
loading this one file knows the full system state without reading chat history.

Phase 5.1: adds evidence_tier map classifying each tracked artifact by memory tier
(hot/warm/cold). evidence_tier is an optional field in the schema; existing
consumers that do not read it are unaffected.

D-183: scripts/orchestrator_state_writer.py must be byte-identical to this file.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
_SCHEMA_FILENAME = "orchestrator_state.schema.json"

_KEY_ARTIFACTS = [
    "loop_run_trace_latest.json",
    "bridge_contract_current.md",
    "planner_packet_current.md",
    "orchestrator_state_latest.json",
    "loop_cycle_checkpoint_latest.json",
    "run_regression_baseline.ndjson",
]

# Phase 5.1: memory tier classification for each key artifact.
_ARTIFACT_TIERS: dict[str, str] = {
    "loop_run_trace_latest.json": "hot",
    "bridge_contract_current.md": "warm",
    "planner_packet_current.md": "warm",
    "orchestrator_state_latest.json": "hot",
    "loop_cycle_checkpoint_latest.json": "hot",
    "run_regression_baseline.ndjson": "cold",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_osw_", suffix=".tmp")
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


def _get_mtime(path: Path) -> str | None:
    """Return ISO mtime string for path, or None if missing."""
    try:
        mtime = path.stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _validate_against_schema(data: dict, schema_dir: Path) -> None:
    """Validate data against orchestrator_state.schema.json if jsonschema is available."""
    schema_path = schema_dir / _SCHEMA_FILENAME
    if not schema_path.exists():
        return
    try:
        import jsonschema  # type: ignore[import]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        pass


def _load_orchestrator_state(context_dir: Path) -> dict | None:
    """Load orchestrator_state_latest.json; return None for all failure conditions.

    Returns None (and logs to stderr) for:
    - File does not exist (FileNotFoundError)
    - File is not valid JSON (json.JSONDecodeError)
    - Parsed dict is missing 'schema_version' field
    - schema_version does not match SCHEMA_VERSION
    """
    path = context_dir / "orchestrator_state_latest.json"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except Exception as exc:
        print(f"PRIOR_STATE_LOAD_FAILED: read error: {exc}", file=sys.stderr)
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"PRIOR_STATE_LOAD_FAILED: invalid JSON: {exc}", file=sys.stderr)
        return None

    if not isinstance(data, dict):
        print("PRIOR_STATE_LOAD_FAILED: parsed value is not a dict", file=sys.stderr)
        return None

    if "schema_version" not in data:
        print(
            "PRIOR_STATE_LOAD_FAILED: missing schema_version field", file=sys.stderr
        )
        return None

    if data["schema_version"] != SCHEMA_VERSION:
        print(
            f"PRIOR_STATE_LOAD_FAILED: schema_version mismatch "
            f"(got {data['schema_version']!r}, expected {SCHEMA_VERSION!r})",
            file=sys.stderr,
        )
        return None

    return data


class OrchestratorStateWriter:
    """Builds orchestrator state from artifacts and writes JSON atomically.

    The state surface gives a fresh orchestrator full system awareness on
    startup without requiring chat history.

    This writer is stateless: prior_state is passed explicitly at call time.
    """

    def __init__(self, context_dir: Path, schema_dir: Path) -> None:
        self.context_dir = context_dir
        self.schema_dir = schema_dir

    def write(
        self,
        trace: dict,
        bridge: dict,
        planner_packet: dict,
        prior_state: dict | None,
    ) -> Path:
        """Build state from artifacts; write JSON atomically.

        Args:
            trace: loop_run_trace_latest.json content
            bridge: bridge_contract JSON shadow content
            planner_packet: planner_packet JSON shadow content
            prior_state: previously loaded orchestrator_state (or None on first run)

        Returns:
            Path to the written JSON file.
        """
        trace_id = trace.get("trace_id", "unknown")
        generated_at = _utc_now_iso()

        active_system = trace.get("repo_id", "quant_current_scope")
        active_stream = "main"

        open_decision = bridge.get("open_decision", "None")
        bottleneck = planner_packet.get("active_bottleneck", "None")
        blocked = (open_decision != "None") or (bottleneck != "None")

        final_result = trace.get("final_result", "PASS")
        last_changed = f"{final_result} {trace.get('generated_at_utc', generated_at)}"

        open_pm_decision = open_decision

        evidence_freshness: dict[str, str | None] = {
            artifact: _get_mtime(self.context_dir / artifact)
            for artifact in _KEY_ARTIFACTS
        }

        # Phase 5.1: emit tier classification for each tracked artifact.
        evidence_tier: dict[str, str] = {
            artifact: _ARTIFACT_TIERS[artifact]
            for artifact in _KEY_ARTIFACTS
            if artifact in _ARTIFACT_TIERS
        }

        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "trace_id": trace_id,
            "generated_at_utc": generated_at,
            "active_system": active_system,
            "active_stream": active_stream,
            "blocked": blocked,
            "last_changed": last_changed,
            "bottleneck": bottleneck,
            "open_pm_decision": open_pm_decision,
            "evidence_freshness": evidence_freshness,
            "evidence_tier": evidence_tier,
        }

        _validate_against_schema(payload, self.schema_dir)

        out_path = self.context_dir / "orchestrator_state_latest.json"
        _atomic_write_json(out_path, payload)
        return out_path
