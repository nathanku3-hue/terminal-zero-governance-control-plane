"""sop._audit_log

Phase 1 — Operational Observability & Audit Logs.

Every governance decision emits a structured JSON audit log entry.
Entries are appended as NDJSON to ``docs/context/audit_log.ndjson``.
A JSON metrics summary is written to
``docs/context/audit_metrics_latest.json`` on every loop run.

Audit log entry schema
-----------------------
    decision        str   — "ALLOW" | "BLOCK" | "HOLD" | "PASS" | "FAIL" | "ERROR" | "WARN"
    actor           str   — component that made the decision (e.g. "gate_a", "step:refresh_weekly_calibration")
    timestamp_utc   str   — ISO-8601 UTC
    outcome         str   — human-readable outcome label
    gate            str   — lifecycle phase / gate name (e.g. "exec_memory→advisory")
    artifact_refs   dict  — {name: mtime_utc} of relevant artifacts
    trace_id        str   — loop run trace_id
    event_tag       str   — "STEP_EXECUTION" | "GATE_DECISION" | "POLICY_DECISION"
    schema_version  str   — "1.0"

Public API
-----------
    emit_audit_log(dest_dir, entry)           — append one entry
    build_audit_entry(...)                    — build a validated entry dict
    write_audit_metrics(dest_dir, entries)    — write metrics summary JSON
    query_audit_log(dest_dir, tail, filter_outcome)  — CLI query helper
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "emit_audit_log",
    "build_audit_entry",
    "write_audit_metrics",
    "query_audit_log",
    "AUDIT_LOG_FILENAME",
    "AUDIT_METRICS_FILENAME",
]

AUDIT_LOG_FILENAME = "audit_log.ndjson"
AUDIT_METRICS_FILENAME = "audit_metrics_latest.json"
SCHEMA_VERSION = "1.0"

_VALID_DECISIONS = frozenset(
    {"ALLOW", "BLOCK", "HOLD", "PASS", "FAIL", "ERROR", "WARN", "SKIP"}
)


def _derive_event_tag(actor: str, provided: str | None = None) -> str:
    candidate = (provided or "").strip().upper()
    if candidate in {"STEP_EXECUTION", "GATE_DECISION", "POLICY_DECISION"}:
        return candidate
    actor_norm = actor.strip().lower()
    if actor_norm.startswith("step:"):
        return "STEP_EXECUTION"
    if actor_norm.startswith("policy:"):
        return "POLICY_DECISION"
    if actor_norm.startswith("gate_"):
        return "GATE_DECISION"
    return "STEP_EXECUTION"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_audit_entry(
    *,
    decision: str,
    actor: str,
    outcome: str,
    gate: str,
    trace_id: str,
    artifact_refs: dict[str, Any] | None = None,
    timestamp_utc: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a validated audit log entry dict.

    Parameters
    ----------
    decision:
        One of ALLOW | BLOCK | HOLD | PASS | FAIL | ERROR | WARN | SKIP.
    actor:
        Component that made the decision, e.g. ``"gate_a"`` or
        ``"step:refresh_weekly_calibration"``.
    outcome:
        Human-readable outcome label.
    gate:
        Lifecycle phase/gate name, e.g. ``"exec_memory→advisory"``.
    trace_id:
        Loop run trace_id (from LoopCycleRuntime).
    artifact_refs:
        Mapping of ``{artifact_name: mtime_utc}`` for referenced artifacts.
    timestamp_utc:
        ISO-8601 UTC timestamp. Defaults to now.
    extra:
        Optional additional fields merged into the entry.
    """
    entry: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "timestamp_utc": timestamp_utc or _utc_now_iso(),
        "decision": decision,
        "actor": actor,
        "outcome": outcome,
        "gate": gate,
        "trace_id": trace_id,
        "artifact_refs": artifact_refs or {},
    }
    if extra:
        for k, v in extra.items():
            if k not in entry:  # don't clobber required fields
                entry[k] = v
    return entry


def emit_audit_log(dest_dir: Path, entry: dict[str, Any]) -> bool:
    """Append *entry* as an NDJSON line to ``audit_log.ndjson`` in *dest_dir*.

    Returns True on success, False on any write failure.
    Never raises — audit log write failures must never abort the loop.
    """
    try:
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        log_path = dest_dir / AUDIT_LOG_FILENAME
        line = json.dumps(entry, separators=(",", ":"), default=str) + "\n"
        with log_path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)
        return True
    except Exception:  # noqa: BLE001
        return False


def _load_audit_entries(dest_dir: Path) -> list[dict[str, Any]]:
    """Load all valid NDJSON entries from audit_log.ndjson. Skips malformed lines."""
    log_path = Path(dest_dir) / AUDIT_LOG_FILENAME
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # skip malformed lines
    except Exception:  # noqa: BLE001
        pass
    return entries


def write_audit_metrics(
    dest_dir: Path,
    trace_id: str,
    entries: list[dict[str, Any]] | None = None,
) -> bool:
    """Write ``audit_metrics_latest.json`` summarising the current log.

    Parameters
    ----------
    dest_dir:
        Directory containing ``audit_log.ndjson`` and where the metrics
        file will be written.
    trace_id:
        Current loop run trace_id.
    entries:
        Pre-loaded entries. If None, entries are loaded from disk.

    Returns True on success, False on any write failure.
    Never raises.
    """
    try:
        dest_dir = Path(dest_dir)
        if entries is None:
            entries = _load_audit_entries(dest_dir)

        decision_counts: dict[str, int] = {}
        gate_durations: dict[str, list[float]] = {}
        failure_count = 0
        block_count = 0

        for e in entries:
            dec = str(e.get("decision", "UNKNOWN"))
            decision_counts[dec] = decision_counts.get(dec, 0) + 1
            if dec in {"FAIL", "ERROR"}:
                failure_count += 1
            if dec == "BLOCK":
                block_count += 1
            gate = str(e.get("gate", ""))
            dur = e.get("duration_seconds")
            if gate and isinstance(dur, (int, float)):
                gate_durations.setdefault(gate, []).append(float(dur))

        gate_duration_summary: dict[str, dict[str, float]] = {}
        for gate, durs in gate_durations.items():
            if durs:
                gate_duration_summary[gate] = {
                    "count": len(durs),
                    "mean_seconds": round(sum(durs) / len(durs), 3),
                    "min_seconds": round(min(durs), 3),
                    "max_seconds": round(max(durs), 3),
                }

        total = len(entries)
        metrics: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": _utc_now_iso(),
            "trace_id": trace_id,
            "total_decisions": total,
            "decision_counts": decision_counts,
            "failure_count": failure_count,
            "failure_rate": round(failure_count / total, 4) if total > 0 else 0.0,
            "block_count": block_count,
            "gate_duration_summary": gate_duration_summary,
        }

        # Atomic write
        metrics_path = dest_dir / AUDIT_METRICS_FILENAME
        content = json.dumps(metrics, indent=2, default=str) + "\n"
        encoded = content.encode("utf-8")
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(dest_dir), prefix="_tmp_audit_metrics_", suffix=".json"
        )
        try:
            os.write(tmp_fd, encoded)
        finally:
            os.close(tmp_fd)
        os.replace(tmp_path, str(metrics_path))
        return True
    except Exception:  # noqa: BLE001
        return False


def query_audit_log(
    dest_dir: Path,
    tail: int | None = None,
    filter_outcome: str | None = None,
) -> list[dict[str, Any]]:
    """Load and filter audit log entries for CLI display.

    Parameters
    ----------
    dest_dir:
        Directory containing ``audit_log.ndjson``.
    tail:
        If set, return only the last *tail* entries (after filtering).
    filter_outcome:
        If set, keep only entries where ``decision`` equals this value
        (case-insensitive). Accepts e.g. ``"BLOCK"``.

    Returns a list of entry dicts.
    """
    entries = _load_audit_entries(dest_dir)
    if filter_outcome:
        needle = filter_outcome.upper()
        entries = [e for e in entries if str(e.get("decision", "")).upper() == needle]
    if tail is not None and tail > 0:
        entries = entries[-tail:]
    return entries
