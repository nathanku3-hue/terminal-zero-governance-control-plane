"""sop._failure_reporter

D-183 Phase 2 Stream B — Task 1.1

Write a run_failure_latest.json artifact using stdlib only (tempfile.mkstemp +
os.replace — no atomic_write_json dependency).  On any write failure the
caller receives False and a machine-parseable FATAL envelope is emitted to
stderr; no exception is ever raised out of this module.

Failure classes
---------------
INSTALL_ERROR | IMPORT_ERROR | GATE_BLOCK | CONTRACT_VIOLATION |
ENTRYPOINT_DIVERGENCE | EXECUTION_ERROR | OBSERVABILITY_ERROR

Recoverability values
---------------------
RETRYABLE | REQUIRES_FIX
"""
from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = ["write_run_failure"]

_VALID_FAILURE_CLASSES = frozenset({
    "INSTALL_ERROR",
    "IMPORT_ERROR",
    "GATE_BLOCK",
    "CONTRACT_VIOLATION",
    "ENTRYPOINT_DIVERGENCE",
    "EXECUTION_ERROR",
    "OBSERVABILITY_ERROR",
})

_VALID_RECOVERABILITY = frozenset({"RETRYABLE", "REQUIRES_FIX"})

ARTIFACT_NAME = "run_failure_latest.json"

# G.3 — Failure origin map: coarse lifecycle phase for each failure_class
_FAILURE_ORIGIN_MAP: dict[str, str] = {
    "INSTALL_ERROR": "preflight",
    "IMPORT_ERROR": "import",
    "ENTRYPOINT_DIVERGENCE": "preflight",
    "EXECUTION_ERROR": "runtime",
    "GATE_BLOCK": "gate",
    "CONTRACT_VIOLATION": "runtime",
    "OBSERVABILITY_ERROR": "runtime",
}

# J.3 — Evaluation outcome source map
_EVALUATION_OUTCOME_SOURCE_MAP: dict[str, str] = {
    "INSTALL_ERROR":         "preflight",
    "IMPORT_ERROR":          "preflight",
    "ENTRYPOINT_DIVERGENCE": "preflight",
    "EXECUTION_ERROR":       "phase_gate",
    "GATE_BLOCK":            "phase_gate",
    "CONTRACT_VIOLATION":    "phase_gate",
    "OBSERVABILITY_ERROR":   "phase_gate",
}


def _get_evaluation_outcome_source(failure_class: str, failed_component: str) -> str:
    """J.3: Return evaluation_outcome_source based on failure_class and failed_component."""
    if "skill" in failed_component.lower():
        return "skill_resolver"
    return _EVALUATION_OUTCOME_SOURCE_MAP.get(failure_class, "phase_gate")


def _read_spec_phase(repo_root: str) -> "str | None":
    """J.1: Read spec_phase from planner_packet_current.md. Returns None on any failure."""
    try:
        packet = Path(repo_root) / "docs" / "context" / "planner_packet_current.md"
        if not packet.exists():
            return None
        for line in packet.read_text(encoding="utf-8").splitlines():
            if line.strip().lower().startswith("phase:"):
                return line.split(":", 1)[1].strip()[:64]
        return None
    except Exception:
        return None



def _lookup_error_code(failure_class: str) -> str:
    """Return the error code for *failure_class* from error_code_registry.json.

    Returns 'UNKNOWN' on any failure (registry absent, parse error, missing entry).
    """
    try:
        registry_path = (
            Path(__file__).parent.parent.parent
            / "docs" / "context" / "schemas" / "error_code_registry.json"
        )
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for entry in registry.get("codes", []):
            if entry.get("failure_class") == failure_class:
                return entry["code"]
        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _fatal_envelope(
    failure_class: str,
    failed_component: str,
    recoverability: str,
    artifact_write_failed: bool,
) -> str:
    """Return a single-line FATAL envelope string (machine-parseable)."""
    return (
        f"FATAL failure_class={failure_class}"
        f" failed_component={failed_component}"
        f" recoverability={recoverability}"
        f" artifact_write_failed={str(artifact_write_failed).lower()}"
    )


def _emit_fatal(
    failure_class: str,
    failed_component: str,
    recoverability: str,
    artifact_write_failed: bool,
) -> None:
    """Emit FATAL envelope to stderr (one line, no trailing newline needed)."""
    print(
        _fatal_envelope(failure_class, failed_component, recoverability, artifact_write_failed),
        file=sys.stderr,
    )


def write_run_failure(
    dest_dir: Path,
    payload: dict[str, Any],
) -> bool:
    """Write *run_failure_latest.json* to *dest_dir* atomically.

    Parameters
    ----------
    dest_dir:
        Directory where ``run_failure_latest.json`` will be written
        (created if absent).
    payload:
        Mapping containing at minimum the required fields listed in
        ``run_failure_latest.schema.json``.  The caller is responsible for
        populating all required fields before calling this function.

    Returns
    -------
    bool
        ``True`` if the artifact was written successfully.
        ``False`` if the write failed — a FATAL envelope has been emitted to
        stderr and the caller must handle the non-zero exit path.

    Raises
    ------
    Nothing — all exceptions are caught internally.
    """
    failure_class = str(payload.get("failure_class", "EXECUTION_ERROR"))
    failed_component = str(payload.get("failed_component", "unknown"))
    recoverability = str(payload.get("recoverability", "REQUIRES_FIX"))

    # Ensure dest_dir exists
    try:
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        _emit_fatal(failure_class, failed_component, recoverability, artifact_write_failed=True)
        return False

    dest_path = dest_dir / ARTIFACT_NAME

    # Serialise to JSON bytes
    try:
        content = json.dumps(payload, indent=2, default=str) + "\n"
        encoded = content.encode("utf-8")
    except Exception as exc:  # noqa: BLE001
        _emit_fatal(failure_class, failed_component, recoverability, artifact_write_failed=True)
        return False

    # Atomic write: mkstemp → write → os.replace
    tmp_fd: int | None = None
    tmp_path: str | None = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(dest_dir),
            prefix="_tmp_run_failure_",
            suffix=".json",
        )
        try:
            os.write(tmp_fd, encoded)
        finally:
            os.close(tmp_fd)
            tmp_fd = None  # mark closed so finally-block won't double-close
        os.replace(tmp_path, str(dest_path))
        tmp_path = None  # mark replaced so finally-block won't delete
        return True
    except Exception as exc:  # noqa: BLE001
        # Clean up temp file if it still exists
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except Exception:  # noqa: BLE001
                pass
        _emit_fatal(failure_class, failed_component, recoverability, artifact_write_failed=True)
        return False
    finally:
        # Safety: close fd if it was never closed (e.g. exception before close)
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except Exception:  # noqa: BLE001
                pass


def build_failure_payload(
    *,
    failure_class: str,
    run_id: str,
    entrypoint: str,
    execution_mode: str,
    failed_component: str,
    reason: str,
    recoverability: str,
    install_check: str = "unknown",
    provenance_check: str = "unknown",
    module_origins: dict[str, str] | None = None,
    failed_at: str | None = None,
    repo_root: str = "",
    cwd: str | None = None,
    attempt_id: "str | None" = None,
    decision_basis_count: int = 0,
) -> dict[str, Any]:
    """Build a complete run_failure payload with all required schema fields.

    Callers that need extra fields may update the returned dict before
    passing it to :func:`write_run_failure`.
    """
    try:
        import sop as _sop_pkg
        package_version: str = getattr(_sop_pkg, "__version__", "unknown")
    except Exception:  # noqa: BLE001
        package_version = "unknown"

    try:
        import importlib.metadata as _meta
        tool_version: str = _meta.version("terminal-zero-governance")
    except Exception:  # noqa: BLE001
        tool_version = package_version

    return {
        "schema_version": "1.1",
        "failure_class": failure_class,
        "run_id": run_id,
        "entrypoint": entrypoint,
        "execution_mode": execution_mode,
        "tool_version": tool_version,
        "package_version": package_version,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cwd": cwd if cwd is not None else os.getcwd(),
        "repo_root": repo_root,
        "module_origins": module_origins or {},
        "failed_at": failed_at or datetime.now(timezone.utc).isoformat(),
        "failed_component": failed_component,
        "reason": reason,
        "recoverability": recoverability,
        "install_check": install_check,
        "provenance_check": provenance_check,
        "final_result": "ERROR",
        "error_code": _lookup_error_code(failure_class),  # G.1: always present, UNKNOWN on any failure
        "failure_origin": _FAILURE_ORIGIN_MAP.get(failure_class, "runtime"),  # G.3: coarse lifecycle phase
        "attempt_id": attempt_id,  # I: None=not-set, "0"=first, "1"=retry
        "spec_phase": _read_spec_phase(repo_root) if repo_root else None,  # J.1
        "decision_basis_count": decision_basis_count,  # J.2
        "evaluation_outcome_source": _get_evaluation_outcome_source(failure_class, failed_component),  # J.3
    }
