from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

try:
    from utils.path_validator import validate_artifact_path
except ModuleNotFoundError:
    try:
        from scripts.utils.path_validator import validate_artifact_path
    except ModuleNotFoundError:
        import os as _os
        def validate_artifact_path(path: str, repo_root: Path) -> tuple[bool, str]:  # type: ignore[misc]
            """Simplified fallback matching scripts/utils/path_validator.py."""
            path = str(path).strip()
            if not path:
                return False, "Empty path"
            if path.startswith("/") or (len(path) >= 2 and path[1] == ":"):
                return False, f"Absolute path not allowed: {path}"
            if ".." in path.split(_os.sep):
                return False, f"Parent directory escape (..) not allowed: {path}"
            return True, ""

try:
    from loop_cycle_artifacts import (
        REPO_ROOT_CONVENIENCE_SPECS,
        mirror_repo_root_convenience,
        persist_advisory_sections,
    )
    from loop_cycle_context import build_loop_cycle_context
    from loop_cycle_runtime import build_loop_cycle_runtime
except ModuleNotFoundError:
    from scripts.loop_cycle_artifacts import (
        REPO_ROOT_CONVENIENCE_SPECS,
        mirror_repo_root_convenience,
        persist_advisory_sections,
    )
    from scripts.loop_cycle_context import build_loop_cycle_context
    from scripts.loop_cycle_runtime import build_loop_cycle_runtime

DOSSIER_HOLD_MARKER = "DOSSIER CRITERIA NOT MET"
APPROVED_CONTEXT_RELATIVE = Path("docs/context")

# ---------------------------------------------------------------------------
# H-NEW-2 — Failure reporter: must be imported before any hard-import block
# so that _write_hard_failure is defined when PhaseGate / Role imports fail.
# ---------------------------------------------------------------------------
try:
    from sop._failure_reporter import write_run_failure as _wr_fn, build_failure_payload as _bfp_fn  # type: ignore[assignment]
except ModuleNotFoundError:
    try:
        from sop._failure_reporter import write_run_failure as _wr_fn, build_failure_payload as _bfp_fn  # type: ignore[no-redef,assignment]
    except ModuleNotFoundError:
        _wr_fn = None  # type: ignore[assignment]
        _bfp_fn = None  # type: ignore[assignment]


def _write_hard_failure(
    failure_class: str,
    failed_component: str,
    reason: str,
    recoverability: str,
) -> None:
    """Write run_failure_latest.json before a hard ImportError is raised.

    Safe to call at module level — never raises, never blocks the ImportError
    that follows it.
    """
    if _wr_fn is None or _bfp_fn is None:
        # Failure reporter itself unavailable — emit minimal stderr envelope.
        import sys as _sys
        print(
            f"FATAL failure_class={failure_class}"
            f" failed_component={failed_component}"
            f" recoverability={recoverability}"
            f" artifact_write_failed=true",
            file=_sys.stderr,
        )
        return
    import os as _os
    from pathlib import Path as _Path
    _dest = _Path(_os.getcwd()) / "docs" / "context"
    _payload = _bfp_fn(
        failure_class=failure_class,
        run_id="pre-init",
        entrypoint="unknown",
        execution_mode="unknown",
        failed_component=failed_component,
        reason=reason,
        recoverability=recoverability,
    )
    _wr_fn(_dest, _payload)


# Phase 2.2 — PhaseGate import
try:
    from phase_gate import PhaseGate
except ModuleNotFoundError:
    try:
        from scripts.phase_gate import PhaseGate
    except ModuleNotFoundError:
        try:
            from sop.scripts.phase_gate import PhaseGate
        except ModuleNotFoundError:
            _write_hard_failure("IMPORT_ERROR", "PhaseGate", "PhaseGate could not be imported", "REQUIRES_FIX")
            raise ImportError(
                "PhaseGate could not be imported from any known path. "
                "Install the package: pip install terminal-zero-governance"
            )

# Phase 2.1 — observability helpers
try:
    from utils.compaction_retention import _compact_ndjson_rolling
    from utils.atomic_io import atomic_write_json
except ModuleNotFoundError:
    try:
        from scripts.utils.compaction_retention import _compact_ndjson_rolling
        from scripts.utils.atomic_io import atomic_write_json
    except ModuleNotFoundError:
        try:
            from sop.scripts.utils.compaction_retention import _compact_ndjson_rolling
            from sop.scripts.utils.atomic_io import atomic_write_json
        except ModuleNotFoundError:
            def _compact_ndjson_rolling(path, max_records=500): pass  # type: ignore[misc]
            def atomic_write_json(path, data, **kw): pass  # type: ignore[misc]

# ---------------------------------------------------------------------------
# Phase 1.1 — Worker / Role Abstraction imports (fail-silent when not installed)
# ---------------------------------------------------------------------------
try:
    from worker_base import Worker, WorkerResult, WorkerSkill
    from worker_role import WorkerRole
    from auditor_role import AuditorRole
    from planner_role import PlannerRole
except ModuleNotFoundError:
    try:
        from scripts.worker_base import Worker, WorkerResult, WorkerSkill
        from scripts.worker_role import WorkerRole
        from scripts.auditor_role import AuditorRole
        from scripts.planner_role import PlannerRole
    except ModuleNotFoundError:
        try:
            from sop.scripts.worker_base import Worker, WorkerResult, WorkerSkill  # noqa: F401
            from sop.scripts.worker_role import WorkerRole
            from sop.scripts.auditor_role import AuditorRole
            from sop.scripts.planner_role import PlannerRole
        except ModuleNotFoundError:
            _write_hard_failure("IMPORT_ERROR", "WorkerRole/AuditorRole/PlannerRole", "Worker/Auditor/Planner roles could not be imported", "REQUIRES_FIX")
            raise ImportError(
                "Worker/Auditor/Planner roles could not be imported. "
                "Install the package: pip install terminal-zero-governance"
            )

# ---------------------------------------------------------------------------
# Phase 1.2 — Configurable Skill Mapping import (fail-silent when not installed)
# ---------------------------------------------------------------------------
_SKILL_RESOLVER_AVAILABLE = False
try:
    from utils.skill_resolver import resolve_skills_for_role, resolve_active_skills
    _SKILL_RESOLVER_AVAILABLE = True
except (ModuleNotFoundError, ImportError):
    try:
        from sop.scripts.utils.skill_resolver import resolve_skills_for_role, resolve_active_skills  # type: ignore[no-redef]
        _SKILL_RESOLVER_AVAILABLE = True
    except (ModuleNotFoundError, ImportError):
        try:
            from scripts.utils.skill_resolver import resolve_skills_for_role, resolve_active_skills  # type: ignore[no-redef]
            _SKILL_RESOLVER_AVAILABLE = True
        except (ModuleNotFoundError, ImportError):
            def resolve_skills_for_role(repo_root, project, role):  # type: ignore[misc]
                return []
            def resolve_active_skills(repo_root, project):  # type: ignore[misc]
                return {"status": "failed", "skills": [], "warnings": [], "errors": ["resolver unavailable"]}

# ---------------------------------------------------------------------------
# ExecMemoryStageResult — explicit result bundle for exec memory stage
# ---------------------------------------------------------------------------

@dataclass
class ExecMemoryStageResult:
    """Structured result from _execute_exec_memory_stage()."""
    cycle_ready: bool
    build_status: dict | None
    promotion_result: str  # promoted | not_authoritative | build_failed | script_missing | snapshot_unavailable
    advisory_note: str


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# F.1 — Artifact reference helpers (sha256 drift detection)
# ---------------------------------------------------------------------------

def _sha256_file(path: "Path") -> "str | None":
    """Return sha256 hex digest of *path*, or None if absent/unreadable/oversized."""
    try:
        data = path.read_bytes()
        if len(data) > 10 * 1024 * 1024:  # 10 MB cap
            return None  # emit WARN step at call site if needed
        return hashlib.sha256(data).hexdigest()
    except Exception:
        return None  # allowlisted: artifact may not exist at gate time


def _classify_content_kind(path: "Path") -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in (".md", ".markdown"):
        return "markdown"
    if suffix in (".yaml", ".yml"):
        return "yaml"
    if suffix == ".ndjson":
        return "ndjson"
    return "unknown"


def _file_mtime_utc(path: "Path") -> "str | None":
    try:
        import datetime as _dt
        mtime = path.stat().st_mtime
        return _dt.datetime.fromtimestamp(mtime, tz=_dt.timezone.utc).isoformat()
    except Exception:
        return None


def _build_artifact_refs(paths: "list[Path]") -> dict:
    refs: dict = {}
    for p in paths:
        refs[p.name] = {
            "mtime_utc": _file_mtime_utc(p),
            "hash": _sha256_file(p),
            "content_kind": _classify_content_kind(p),
            "hash_strategy": "sha256",
        }
    return refs


# Phase 1.3 — State Persistence helpers
# ---------------------------------------------------------------------------

_CHECKPOINT_REQUIRED_FIELDS = {
    "schema_version",
    "generated_at_utc",
    "cycle_id",
    "completed_steps",
    "last_completed_step",
    "partial",
}


def _write_checkpoint(
    path: Path,
    cycle_id: str,
    completed_steps: list[str],
    exec_memory_cycle_ready: bool,
    partial: bool,
) -> None:
    """Write a loop-cycle checkpoint atomically.

    Call after each major step:
    1. After exec memory promotion  -> completed_steps=["exec_memory"], partial=True
    2. After advisory artifacts     -> completed_steps=["exec_memory","advisory"], partial=True
    3. After loop summary written   -> partial=False  (terminal)
    """
    import json as _json
    from datetime import datetime as _dt, timezone as _tz

    last_step = completed_steps[-1] if completed_steps else None
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": _dt.now(_tz.utc).isoformat(),
        "cycle_id": cycle_id,
        "completed_steps": completed_steps,
        "last_completed_step": last_step,
        "exec_memory_cycle_ready": exec_memory_cycle_ready,
        "partial": partial,
    }
    try:
        _atomic_write_text(path, _json.dumps(payload, indent=2) + "\n")
    except Exception:
        pass  # Checkpoint write failure must never abort the loop


def _load_checkpoint(
    path: Path,
    max_age_hours: float = 24.0,
    current_cycle_id: str | None = None,
) -> dict | None:
    """Load and validate checkpoint; return None on any stale/invalid condition.

    Stale conditions (return None):
    1. File missing
    2. ``partial`` is False  — previous run completed cleanly
    3. ``generated_at_utc`` older than ``max_age_hours``
    4. ``cycle_id`` present and does not match ``current_cycle_id`` (when provided)
    5. Missing required fields (schema-invalid)
    """
    import json as _json
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    if not path.exists():
        return None
    try:
        data = _json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    # Schema check: required fields present
    if not _CHECKPOINT_REQUIRED_FIELDS.issubset(data.keys()):
        return None

    # Stale: completed cleanly
    if not data.get("partial", True):
        return None

    # Stale: too old
    try:
        generated_at = _dt.fromisoformat(data["generated_at_utc"])
        if _dt.now(_tz.utc) - generated_at > _td(hours=max_age_hours):
            return None
    except Exception:
        return None

    # Stale: cycle_id mismatch
    if current_cycle_id is not None:
        if data.get("cycle_id") != current_cycle_id:
            return None

    # Phase 3.1 -- Corrupt-state detection on resume
    # skip_integrity_check is set via --skip-integrity-check CLI flag
    import os as _os
    skip_integrity = _os.environ.get("SOP_SKIP_INTEGRITY_CHECK", "").lower() in {"1", "true"}
    if not skip_integrity:
        completed = data.get("completed_steps", [])
        if isinstance(completed, list):
            pass  # integrity check applies to artifact paths, wired in run_cycle()

    return data


def _resolve_resume_steps(checkpoint: dict | None) -> set[str]:
    """Return set of step names to skip on resume.

    Returns empty set if checkpoint is None (full run).
    """
    if checkpoint is None:
        return set()
    completed = checkpoint.get("completed_steps", [])
    return set(completed) if isinstance(completed, list) else set()
    """Result bundle from exec-memory stage execution."""

    def __init__(
        self,
        cycle_ready: bool,
        build_status: dict[str, Any] | None,
        promotion_result: str,
        advisory_note: str,
    ):
        self.cycle_ready = cycle_ready
        self.build_status = build_status
        self.promotion_result = promotion_result
        self.advisory_note = advisory_note


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_path(repo_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _resolve_with_default(repo_root: Path, value: Path | None, default_path: Path) -> Path:
    if value is None:
        return default_path
    return _resolve_path(repo_root=repo_root, candidate=value)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _find_weekly_summary(context_dir: Path, explicit: Path | None, repo_root: Path) -> Path:
    if explicit is not None:
        return _resolve_path(repo_root=repo_root, candidate=explicit)

    default_latest = context_dir / "ceo_weekly_summary_latest.md"
    if default_latest.exists():
        return default_latest

    candidates: list[tuple[float, str, Path]] = []
    for path in context_dir.glob("ceo_weekly_summary*.md"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        candidates.append((mtime, path.name, path))
    if not candidates:
        return default_latest
    candidates.sort(reverse=True)
    return candidates[0][2]


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _empty_compaction_summary(
    *,
    status: str,
    step_status: str | None,
    source_json: Path,
) -> dict[str, Any]:
    return {
        "status": status,
        "step_status": step_status,
        "source_json": str(source_json),
        "generated_at_utc": None,
        "should_compact": None,
        "can_compact": None,
        "decision_mode": None,
        "reasons": [],
        "guardrail_violations": [],
    }


def _load_compaction_status_summary(
    *,
    step: dict[str, Any] | None,
    status_json: Path,
) -> dict[str, Any]:
    step_status = None
    if step is not None:
        step_status_text = str(step.get("status", "")).strip().upper()
        step_status = step_status_text or None

    if step is None:
        return _empty_compaction_summary(
            status="skipped",
            step_status=step_status,
            source_json=status_json,
        )
    if step_status != "PASS":
        non_pass_status = {
            "SKIP": "skipped",
            "FAIL": "failed",
            "ERROR": "error",
            "HOLD": "held",
        }.get(step_status or "", "skipped")
        return _empty_compaction_summary(
            status=non_pass_status,
            step_status=step_status,
            source_json=status_json,
        )

    if not status_json.exists():
        return _empty_compaction_summary(
            status="missing",
            step_status=step_status,
            source_json=status_json,
        )

    try:
        payload = json.loads(status_json.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return _empty_compaction_summary(
            status="invalid",
            step_status=step_status,
            source_json=status_json,
        )

    if not isinstance(payload, dict):
        return _empty_compaction_summary(
            status="invalid",
            step_status=step_status,
            source_json=status_json,
        )

    should_compact = payload.get("should_compact")
    can_compact = payload.get("can_compact")
    decision_mode = payload.get("decision_mode")
    generated_at_utc = payload.get("generated_at_utc")

    return {
        "status": "available",
        "step_status": step_status,
        "source_json": str(status_json),
        "generated_at_utc": generated_at_utc if isinstance(generated_at_utc, str) else None,
        "should_compact": should_compact if isinstance(should_compact, bool) else None,
        "can_compact": can_compact if isinstance(can_compact, bool) else None,
        "decision_mode": (
            str(decision_mode).strip()
            if isinstance(decision_mode, str) and str(decision_mode).strip()
            else None
        ),
        "reasons": _coerce_string_list(payload.get("reasons")),
        "guardrail_violations": _coerce_string_list(payload.get("guardrail_violations")),
    }


def _run_command(step_name: str, command: list[str], cwd: Path) -> dict[str, Any]:
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


def _skip_step(step_name: str, message: str) -> dict[str, Any]:
    now = _utc_now()
    stamp = _utc_iso(now)
    return {
        "name": step_name,
        "status": "SKIP",
        "exit_code": 0,
        "command": [],
        "started_utc": stamp,
        "ended_utc": stamp,
        "duration_seconds": 0.0,
        "stdout": "",
        "stderr": "",
        "message": message,
    }


def _append_step_ndjson(path: Path, trace_id: str, step: dict) -> None:
    """Append a step record as a NDJSON line (non-blocking best-effort)."""
    import json as _json
    try:
        record = dict(step)
        record["trace_id"] = trace_id
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(_json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        pass  # NDJSON append failure must never abort the loop


def _parse_iso8601_utc(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def _build_hold_summary_payload(
    *,
    gate_a_hold: bool,
    gate_b_hold: bool,
    gate_decisions: list[dict],
    steps: list | None = None,
    artifacts: dict | None = None,
    ctx_fields: dict | None = None,
) -> dict[str, Any]:
    """H-3: Build a summary payload for a Gate HOLD outcome.

    Returns final_result='HOLD', final_exit_code=0.
    Includes real step data and artifacts so trace/output writes are complete.
    """
    from datetime import datetime as _dt, timezone as _tz
    _now = _dt.now(_tz.utc).isoformat()
    _gate_name = "gate_a" if gate_a_hold else "gate_b"
    _steps = steps or []
    _step_summary: dict[str, Any] = {
        "pass_count": sum(1 for s in _steps if s.get("status") == "PASS"),
        "hold_count": sum(1 for s in _steps if s.get("status") == "HOLD") + 1,
        "fail_count": sum(1 for s in _steps if s.get("status") == "FAIL"),
        "error_count": sum(1 for s in _steps if s.get("status") == "ERROR"),
        "skip_count": sum(1 for s in _steps if s.get("status") == "SKIP"),
        "total_steps": len(_steps),
    }
    _payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at_utc": _now,
        "final_result": "HOLD",
        "final_exit_code": 0,
        "hold_reason": f"{_gate_name} decision=HOLD",
        "gate_decisions": gate_decisions,
        "steps": _steps,
        "step_summary": _step_summary,
    }
    if artifacts is not None:
        _payload["artifacts"] = artifacts
    if ctx_fields is not None:
        _payload.update(ctx_fields)
    return _payload

def _write_hard_failure(
    failure_class: str,
    failed_component: str,
    reason: str,
    recoverability: str,
) -> None:
    """Module-level shim: write run_failure_latest.json with available context.

    Called from _error_result(), the OSError output-write catch, and main().
    Has no dependency on run_cycle() context — uses only module-level info.
    Emits FATAL envelope to stderr if the write itself fails.
    """
    try:
        from sop._failure_reporter import write_run_failure, build_failure_payload
    except Exception:
        try:
            from sop._failure_reporter import write_run_failure, build_failure_payload  # type: ignore[no-redef]
        except Exception:
            # Cannot import reporter — emit raw FATAL and return
            print(
                f"FATAL failure_class={failure_class}"
                f" failed_component={failed_component}"
                f" recoverability={recoverability}"
                f" artifact_write_failed=true",
                file=sys.stderr,
            )
            return
    try:
        import uuid as _uuid
        _run_id = str(_uuid.uuid4())
    except Exception:
        _run_id = "unknown"
    payload = build_failure_payload(
        failure_class=failure_class,
        run_id=_run_id,
        entrypoint="run_loop_cycle.py",
        execution_mode="script",
        failed_component=failed_component,
        reason=reason,
        recoverability=recoverability,
    )
    _dest = Path("docs/context")
    write_run_failure(_dest, payload)


def _error_result(message: str) -> tuple[int, dict[str, Any], str]:
    _write_hard_failure("EXECUTION_ERROR", "run_cycle", message, "REQUIRES_FIX")
    generated_at_utc = _utc_iso(_utc_now())
    payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "steps": [],
        "final_result": "ERROR",
        "final_exit_code": 2,
        "message": message,
    }
    markdown = "\n".join(
        [
            "# Loop Cycle Summary",
            "",
            f"- GeneratedAtUTC: {generated_at_utc}",
            "- FinalResult: ERROR",
            "- FinalExitCode: 2",
            f"- Message: {message}",
            "",
        ]
    )
    return 2, payload, markdown


def _first_relative_path_component(candidate: Path) -> str:
    for part in candidate.as_posix().split("/"):
        if part and part != ".":
            return part
    return ""


def _validate_repo_root_argument(repo_root_arg: Path) -> str | None:
    if not repo_root_arg.is_absolute():
        first_component = _first_relative_path_component(repo_root_arg)
        cwd_name = Path.cwd().resolve().name
        if first_component and first_component == cwd_name:
            return (
                f"Relative --repo-root must not start with the current repo root name "
                f"'{cwd_name}'."
            )
        is_valid, error = validate_artifact_path(repo_root_arg.as_posix(), Path.cwd().resolve())
        if not is_valid:
            return f"Invalid --repo-root path: {error}"

    # Note: We allow nested same-name directories (e.g., GitHub Actions clones
    # into repo-name/repo-name) since this is a common CI pattern.
    return None


def _validate_exact_path(actual: Path, expected: Path, label: str) -> str | None:
    if actual.resolve() != expected.resolve():
        return f"{label} must be written to canonical path {expected} (got {actual})."
    return None


def _validate_run_cycle_writer_boundaries(ctx: Any) -> str | None:
    expected_context_dir = (ctx.repo_root / APPROVED_CONTEXT_RELATIVE).resolve()
    checks = [
        (ctx.context_dir, expected_context_dir, "--context-dir"),
        (ctx.output_json, expected_context_dir / "loop_cycle_summary_latest.json", "--output-json"),
        (ctx.output_md, expected_context_dir / "loop_cycle_summary_latest.md", "--output-md"),
        (
            ctx.closure_output_json,
            expected_context_dir / "loop_closure_status_latest.json",
            "--closure-output-json",
        ),
        (
            ctx.closure_output_md,
            expected_context_dir / "loop_closure_status_latest.md",
            "--closure-output-md",
        ),
        (
            ctx.exec_memory_latest_json,
            expected_context_dir / "exec_memory_packet_latest.json",
            "--exec-memory-json",
        ),
        (
            ctx.exec_memory_latest_md,
            expected_context_dir / "exec_memory_packet_latest.md",
            "--exec-memory-md",
        ),
        (
            ctx.exec_memory_current_json,
            expected_context_dir / "exec_memory_packet_latest_current.json",
            "exec-memory current JSON staging output",
        ),
        (
            ctx.exec_memory_current_md,
            expected_context_dir / "exec_memory_packet_latest_current.md",
            "exec-memory current Markdown staging output",
        ),
        (
            ctx.exec_memory_build_status_json,
            expected_context_dir / "exec_memory_packet_build_status_current.json",
            "exec-memory build-status output",
        ),
        (
            ctx.compaction_state_json,
            expected_context_dir / "context_compaction_state_latest.json",
            "--compaction-state-json",
        ),
        (
            ctx.compaction_status_json,
            expected_context_dir / "context_compaction_status_latest.json",
            "--compaction-status-json",
        ),
    ]
    for actual, expected, label in checks:
        error = _validate_exact_path(actual, expected, label)
        if error is not None:
            return error
    return None


def _load_closure_result(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return ""
    if not isinstance(payload, dict):
        return ""
    result = payload.get("result")
    if not isinstance(result, str):
        return ""
    return result.strip()


def _load_exec_memory_build_status(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _apply_hold_semantics(
    *,
    steps: list[dict[str, Any]],
    allow_hold: bool,
    closure_output_json: Path,
) -> None:
    if not allow_hold:
        return

    refresh_dossier_step = next((s for s in steps if s.get("name") == "refresh_dossier"), None)
    if (
        refresh_dossier_step is not None
        and refresh_dossier_step.get("status") == "FAIL"
        and refresh_dossier_step.get("exit_code") == 1
        and DOSSIER_HOLD_MARKER in str(refresh_dossier_step.get("stderr", ""))
    ):
        refresh_dossier_step["status"] = "HOLD"
        refresh_dossier_step["message"] = "Expected dossier criteria shortfall; marked HOLD."

    closure_step = next((s for s in steps if s.get("name") == "validate_loop_closure"), None)
    closure_result = _load_closure_result(closure_output_json)
    if (
        closure_step is not None
        and closure_step.get("status") == "FAIL"
        and closure_step.get("exit_code") == 1
        and closure_result == "NOT_READY"
    ):
        closure_step["status"] = "HOLD"
        closure_step["message"] = "Loop closure result NOT_READY; marked HOLD."


def _scan_disagreement_sla(path: Path, now_utc: datetime) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "total_entries": 0,
        "unresolved_entries": 0,
        "overdue_unresolved_count": 0,
        "overdue_unresolved": [],
        "parse_errors": [],
    }
    if not path.exists():
        return result

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for line_no, raw_line in enumerate(lines, start=1):
        text = raw_line.strip()
        if not text:
            continue
        result["total_entries"] += 1
        try:
            payload = json.loads(text)
        except Exception as exc:
            result["parse_errors"].append(f"line {line_no}: {exc}")
            continue
        if not isinstance(payload, dict):
            result["parse_errors"].append(f"line {line_no}: JSON entry is not an object")
            continue

        resolved = payload.get("resolved") is True
        if resolved:
            continue
        result["unresolved_entries"] += 1

        due_raw = payload.get("due_utc")
        due_text = due_raw if isinstance(due_raw, str) else ""
        due_utc = _parse_iso8601_utc(due_text)
        if due_utc is None:
            continue
        if due_utc < now_utc:
            result["overdue_unresolved_count"] += 1
            result["overdue_unresolved"].append(
                {
                    "line": line_no,
                    "round_id": str(payload.get("round_id", "")),
                    "task_id": str(payload.get("task_id", "")),
                    "code": str(payload.get("code", "")),
                    "severity": str(payload.get("severity", "")),
                    "owner": str(payload.get("owner", "")),
                    "due_utc": due_text,
                }
            )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one deterministic loop cycle: refresh artifacts, run truth checks, "
            "run closure validation, and emit loop cycle summary artifacts."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--context-dir", type=Path, default=Path("docs/context"))
    parser.add_argument("--scripts-dir", type=Path, default=None)
    parser.add_argument("--python-exe", type=str, default=sys.executable)
    parser.add_argument("--repo-id", type=str, default="")
    parser.add_argument("--skip-phase-end", action="store_true")
    parser.add_argument("--phase-end-script", type=Path, default=None)
    parser.add_argument("--phase-end-audit-mode", type=str, default="shadow")
    parser.add_argument("--logs-dir", type=Path, default=None)
    parser.add_argument("--fp-ledger-json", type=Path, default=None)
    parser.add_argument("--weekly-report-json", type=Path, default=None)
    parser.add_argument("--weekly-report-md", type=Path, default=None)
    parser.add_argument("--dossier-json", type=Path, default=None)
    parser.add_argument("--dossier-md", type=Path, default=None)
    parser.add_argument("--go-signal-md", type=Path, default=None)
    parser.add_argument("--weekly-summary-md", type=Path, default=None)
    parser.add_argument("--weekly-summary-gen-script", type=Path, default=None)
    parser.add_argument("--go-truth-script", type=Path, default=None)
    parser.add_argument("--weekly-truth-script", type=Path, default=None)
    parser.add_argument("--memory-packet-script", type=Path, default=None)
    parser.add_argument("--compaction-trigger-script", type=Path, default=None)
    parser.add_argument("--memory-truth-script", type=Path, default=None)
    parser.add_argument("--exec-memory-json", type=Path, default=None)
    parser.add_argument("--exec-memory-md", type=Path, default=None)
    parser.add_argument("--exec-memory-build-status-json", type=Path, default=None)
    parser.add_argument("--compaction-state-json", type=Path, default=None)
    parser.add_argument("--compaction-status-json", type=Path, default=None)
    parser.add_argument("--compaction-pm-warn", type=float, default=0.75)
    parser.add_argument("--compaction-ceo-warn", type=float, default=0.70)
    parser.add_argument("--compaction-force", type=float, default=0.90)
    parser.add_argument("--compaction-max-age-hours", type=float, default=24.0)
    parser.add_argument("--pm-budget-tokens", type=int, default=3000)
    parser.add_argument("--ceo-budget-tokens", type=int, default=1800)
    parser.add_argument("--closure-script", type=Path, default=None)
    parser.add_argument("--closure-output-json", type=Path, default=None)
    parser.add_argument("--closure-output-md", type=Path, default=None)
    parser.add_argument("--freshness-hours", type=float, default=72.0)
    parser.add_argument("--allow-hold", type=_parse_bool, default=True)
    parser.add_argument("--disagreement-ledger-jsonl", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--force", action="store_true", default=False, help="Force run even if prior state shows blocked=true.")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Evaluate gates without executing steps or writing artifacts.")
    parser.add_argument("--step-sla-seconds", type=float, default=300.0, help="SLA threshold in seconds for step duration (default: 300).")
    parser.add_argument("--skip-integrity-check", action="store_true", default=False, help="Skip artifact integrity check on checkpoint resume.")
    # Phase 5.3: artifact lifecycle flags
    parser.add_argument("--prune", action="store_true", default=False, help="Archive superseded/orphaned artifacts from docs/context/ (dry-run without this flag).")
    parser.add_argument("--max-context-artifacts", type=int, default=50, dest="max_context_artifacts", help="Warn when docs/context/ exceeds this many artifacts (default: 50).")
    return parser.parse_args(argv)


def run_cycle(args: argparse.Namespace) -> tuple[int, dict[str, Any], str]:
    repo_root_error = _validate_repo_root_argument(args.repo_root)
    if repo_root_error is not None:
        return _error_result(repo_root_error)

    # Build immutable context from args
    ctx = build_loop_cycle_context(args)

    writer_boundary_error = _validate_run_cycle_writer_boundaries(ctx)
    if writer_boundary_error is not None:
        return _error_result(writer_boundary_error)

    # Create directories before building runtime (runtime writes lesson stubs immediately)
    ctx.context_dir.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Phase 1.3 — Load checkpoint BEFORE runtime (before any side effects)
    # ------------------------------------------------------------------
    _checkpoint_path = ctx.context_dir / "loop_cycle_checkpoint_latest.json"
    _current_cycle_id = getattr(args, "cycle_id", None)
    _max_checkpoint_age = getattr(args, "max_checkpoint_age_hours", 24.0)
    _checkpoint = _load_checkpoint(
        path=_checkpoint_path,
        max_age_hours=_max_checkpoint_age,
        current_cycle_id=_current_cycle_id,
    )
    _resume_steps: set[str] = _resolve_resume_steps(_checkpoint)

    # Build mutable runtime state (writes lesson stubs — always, even on resume)
    runtime = build_loop_cycle_runtime(ctx)

    # Apply exec_memory_cycle_ready from checkpoint when resuming
    if "exec_memory" in _resume_steps and _checkpoint is not None:
        runtime.exec_memory_cycle_ready = bool(
            _checkpoint.get("exec_memory_cycle_ready", False)
        )

    # ------------------------------------------------------------------
    # Phase 1.1 — Instantiate Workers with role-filtered skills
    # Phase 1.2 — Derive project_name from .sop_config.yaml
    # ------------------------------------------------------------------
    _project_name = "quant_current_scope"  # default
    try:
        _sop_config_path = ctx.repo_root / ".sop_config.yaml"
        if _sop_config_path.exists():
            import yaml as _yaml
            with _sop_config_path.open("r", encoding="utf-8") as _f:
                _sop_cfg = _yaml.safe_load(_f)
                if isinstance(_sop_cfg, dict):
                    _project_name = _sop_cfg.get("project_name", _project_name)
    except Exception:
        pass

    _worker_skills = resolve_skills_for_role(ctx.repo_root, _project_name, "worker")
    _auditor_skills = resolve_skills_for_role(ctx.repo_root, _project_name, "auditor")

    # H-5: distinguish broken install from legitimately empty-skill repo
    if not _SKILL_RESOLVER_AVAILABLE:
        _skills_status = "RESOLVER_UNAVAILABLE"
    else:
        _skills_result = resolve_active_skills(ctx.repo_root, _project_name)
        if _skills_result["status"] == "failed":
            _skills_status = "RESOLVER_UNAVAILABLE"
        else:
            _skills_status = "EMPTY_BY_DESIGN" if not _worker_skills else "OK"
    runtime.skills_status = _skills_status  # H-5: stored as metadata, not a pipeline step

    _worker = WorkerRole(repo_root=ctx.repo_root, skills=_worker_skills)
    _auditor = AuditorRole(repo_root=ctx.repo_root, skills=_auditor_skills)
    _planner = PlannerRole(repo_root=ctx.repo_root, skills=[])

    def build_summary_payload(
        *,
        disagreement_sla: dict[str, Any],
    ) -> dict[str, Any]:
        status_counts = {
            "pass_count": sum(1 for step in runtime.steps if step["status"] == "PASS"),
            "hold_count": sum(1 for step in runtime.steps if step["status"] == "HOLD"),
            "fail_count": sum(1 for step in runtime.steps if step["status"] == "FAIL"),
            "error_count": sum(1 for step in runtime.steps if step["status"] == "ERROR"),
            "skip_count": sum(1 for step in runtime.steps if step["status"] == "SKIP"),
            "total_steps": len(runtime.steps),
        }

        fail_exit_codes = [
            step["exit_code"]
            for step in runtime.steps
            if step["status"] == "FAIL" and isinstance(step.get("exit_code"), int)
        ]
        has_error = status_counts["error_count"] > 0
        if has_error:
            final_exit_code = 2
            final_result = "ERROR"
        elif any(code == 2 for code in fail_exit_codes):
            final_exit_code = 2
            final_result = "ERROR"
        elif fail_exit_codes:
            final_exit_code = 1
            final_result = "FAIL"
        elif status_counts["hold_count"] > 0:
            final_exit_code = 0
            final_result = "HOLD"
        else:
            final_exit_code = 0
            final_result = "PASS"

        repo_root_convenience = runtime.repo_root_convenience or {}
        compaction_step = next(
            (
                step
                for step in runtime.steps
                if step.get("name") == "evaluate_context_compaction_trigger"
            ),
            None,
        )
        compaction = _load_compaction_status_summary(
            step=compaction_step,
            status_json=ctx.compaction_status_json,
        )

        return {
            "schema_version": "1.0.0",
            "generated_at_utc": runtime.generated_at_utc,
            "repo_root": str(ctx.repo_root),
            "context_dir": str(ctx.context_dir),
            "scripts_dir": str(ctx.script_dir),
            "skip_phase_end": ctx.skip_phase_end,
            "allow_hold": ctx.allow_hold,
            "freshness_hours": ctx.freshness_hours,
            "step_summary": status_counts,
            "steps": runtime.steps,
            "disagreement_ledger_sla": disagreement_sla,
            "lessons": {
                "worker": str(runtime.lessons_paths["worker"]),
                "auditor": str(runtime.lessons_paths["auditor"]),
            },
            "artifacts": {
                "weekly_report_json": str(ctx.weekly_report_json),
                "weekly_report_md": str(ctx.weekly_report_md),
                "dossier_json": str(ctx.dossier_json),
                "dossier_md": str(ctx.dossier_md),
                "go_signal_md": str(ctx.go_signal_md),
                "weekly_summary_md": str(ctx.weekly_summary_md),
                "review_checklist_md": str(ctx.review_checklist_md),
                "interface_contract_manifest_json": str(ctx.interface_contract_manifest_json),
                "exec_memory_json": str(ctx.exec_memory_latest_json),
                "exec_memory_md": str(ctx.exec_memory_latest_md),
                "exec_memory_current_json": str(ctx.exec_memory_current_json),
                "exec_memory_current_md": str(ctx.exec_memory_current_md),
                "exec_memory_build_status_json": str(ctx.exec_memory_build_status_json),
                "exec_memory_latest_promoted": runtime.exec_memory_cycle_ready,
                "next_round_handoff_json": str(ctx.next_round_handoff_json),
                "next_round_handoff_md": str(ctx.next_round_handoff_md),
                "expert_request_json": str(ctx.expert_request_json),
                "expert_request_md": str(ctx.expert_request_md),
                "pm_ceo_research_brief_json": str(ctx.pm_ceo_research_brief_json),
                "pm_ceo_research_brief_md": str(ctx.pm_ceo_research_brief_md),
                "board_decision_brief_json": str(ctx.board_decision_brief_json),
                "board_decision_brief_md": str(ctx.board_decision_brief_md),
                "compaction_state_json": str(ctx.compaction_state_json),
                "compaction_status_json": str(ctx.compaction_status_json),
                "closure_output_json": str(ctx.closure_output_json),
                "closure_output_md": str(ctx.closure_output_md),
                "summary_output_json": str(ctx.output_json),
                "summary_output_md": str(ctx.output_md),
            },
            "compaction": compaction,
            "next_round_handoff": (
                {
                    "status": runtime.next_round_handoff_artifacts["status"],
                    "json": str(runtime.next_round_handoff_artifacts["json"]),
                    "md": str(runtime.next_round_handoff_artifacts["md"]),
                }
                if runtime.next_round_handoff_artifacts is not None
                else None
            ),
            "expert_request": (
                {
                    "status": runtime.expert_request_artifacts["status"],
                    "json": str(runtime.expert_request_artifacts["json"]),
                    "md": str(runtime.expert_request_artifacts["md"]),
                    "target_expert": str(runtime.expert_request_artifacts["payload"].get("target_expert", "")).strip(),
                }
                if runtime.expert_request_artifacts is not None
                else None
            ),
            "pm_ceo_research_brief": (
                {
                    "status": runtime.pm_ceo_research_brief_artifacts["status"],
                    "json": str(runtime.pm_ceo_research_brief_artifacts["json"]),
                    "md": str(runtime.pm_ceo_research_brief_artifacts["md"]),
                    "delegated_to": str(runtime.pm_ceo_research_brief_artifacts["payload"].get("delegated_to", "")).strip(),
                }
                if runtime.pm_ceo_research_brief_artifacts is not None
                else None
            ),
            "board_decision_brief": (
                {
                    "status": runtime.board_decision_brief_artifacts["status"],
                    "json": str(runtime.board_decision_brief_artifacts["json"]),
                    "md": str(runtime.board_decision_brief_artifacts["md"]),
                    "decision_topic": str(runtime.board_decision_brief_artifacts["payload"].get("decision_topic", "")).strip(),
                    "recommended_option": str(runtime.board_decision_brief_artifacts["payload"].get("recommended_option", "")).strip(),
                }
                if runtime.board_decision_brief_artifacts is not None
                else None
            ),
            "skill_activation": (
                {
                    "status": runtime.skill_activation_artifacts["status"],
                    "skill_count": len(runtime.skill_activation_artifacts["payload"].get("skills", [])),
                    "warnings": runtime.skill_activation_artifacts["payload"].get("warnings", []),
                }
                if runtime.skill_activation_artifacts is not None
                else None
            ),
            "repo_root_convenience": {
                key: str(path)
                for key, path in repo_root_convenience.items()
            },
            "skills_status": getattr(runtime, "skills_status", "RESOLVER_UNAVAILABLE"),
            "final_result": final_result,
            "final_exit_code": final_exit_code,
        }

    def run_python_step(step_name: str, script_path: Path, script_args: list[str]) -> None:
        _ndjson_path = ctx.context_dir / "loop_run_steps_latest.ndjson"
        if not script_path.exists():
            _missing_step = {
                "name": step_name,
                "status": "ERROR",
                "exit_code": None,
                "command": [],
                "started_utc": runtime.generated_at_utc,
                "ended_utc": runtime.generated_at_utc,
                "duration_seconds": 0.0,
                "stdout": "",
                "stderr": "",
                "message": f"Missing script: {script_path}",
            }
            runtime.steps.append(_missing_step)
            _append_step_ndjson(_ndjson_path, runtime.trace_id, _missing_step)
            return
        command = [ctx.python_exe, str(script_path)] + script_args
        _step_result = _run_command(step_name=step_name, command=command, cwd=ctx.repo_root)
        runtime.steps.append(_step_result)
        _append_step_ndjson(_ndjson_path, runtime.trace_id, _step_result)

    def _step_by_name(step_name: str) -> dict[str, Any] | None:
        return next((step for step in runtime.steps if step.get("name") == step_name), None)

    def _remove_if_exists(path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    def _promote_exec_memory_outputs(
        memory_step: dict[str, Any] | None,
        build_status: dict[str, Any] | None,
    ) -> bool:
        if memory_step is None:
            return False
        for actual, expected, label in (
            (
                ctx.exec_memory_current_json,
                ctx.context_dir / "exec_memory_packet_latest_current.json",
                "exec-memory current JSON staging output",
            ),
            (
                ctx.exec_memory_current_md,
                ctx.context_dir / "exec_memory_packet_latest_current.md",
                "exec-memory current Markdown staging output",
            ),
            (
                ctx.exec_memory_latest_json,
                ctx.context_dir / "exec_memory_packet_latest.json",
                "exec-memory latest JSON output",
            ),
            (
                ctx.exec_memory_latest_md,
                ctx.context_dir / "exec_memory_packet_latest.md",
                "exec-memory latest Markdown output",
            ),
        ):
            error = _validate_exact_path(actual, expected, label)
            if error is not None:
                memory_step["status"] = "FAIL"
                memory_step["exit_code"] = 2
                memory_step["message"] = error
                return False
        if build_status is None:
            memory_step["status"] = "FAIL"
            memory_step["exit_code"] = 2
            memory_step["message"] = "Exec memory build status missing or invalid."
            return False
        if not bool(build_status.get("authoritative_latest_written")):
            reason = str(build_status.get("reason", "")).strip() or "not_authoritative"
            if memory_step.get("status") == "PASS":
                memory_step["status"] = "FAIL"
                memory_step["exit_code"] = 2
            memory_step["message"] = (
                "Exec memory build did not produce authoritative current-cycle outputs "
                f"({reason})."
            )
            return False
        if memory_step.get("status") not in {"PASS", "FAIL"}:
            return False
        if not ctx.exec_memory_current_json.exists() or not ctx.exec_memory_current_md.exists():
            memory_step["status"] = "FAIL"
            memory_step["exit_code"] = 2
            memory_step["message"] = (
                "Current-cycle exec memory outputs were not produced."
            )
            return False
        try:
            _atomic_write_text(
                ctx.exec_memory_latest_json,
                ctx.exec_memory_current_json.read_text(encoding="utf-8-sig"),
            )
            _atomic_write_text(
                ctx.exec_memory_latest_md,
                ctx.exec_memory_current_md.read_text(encoding="utf-8-sig"),
            )
        except OSError as exc:
            memory_step["status"] = "FAIL"
            memory_step["exit_code"] = 2
            memory_step["message"] = f"Failed to promote exec memory outputs: {exc}"
            return False
        return True

    def _execute_exec_memory_stage() -> ExecMemoryStageResult:
        """Execute exec-memory stage and return explicit result bundle."""
        # Pre-build cleanup: Remove stale current-cycle artifacts
        _remove_if_exists(ctx.exec_memory_current_json)
        _remove_if_exists(ctx.exec_memory_current_md)
        _remove_if_exists(ctx.exec_memory_build_status_json)

        # Script existence check: Return early with cycle_ready=False if missing
        if not ctx.memory_packet_script.exists():
            runtime.steps.append(
                _skip_step(
                    "build_exec_memory_packet",
                    f"Script not found: {ctx.memory_packet_script}",
                )
            )
            return ExecMemoryStageResult(
                cycle_ready=False,
                build_status=None,
                promotion_result="script_missing",
                advisory_note=f"Script not found: {ctx.memory_packet_script}",
            )

        # Temp summary check: Return early if snapshot unavailable
        if not _write_temp_summary_snapshot():
            runtime.steps.append(
                _skip_step(
                    "build_exec_memory_packet",
                    f"Current-cycle summary snapshot unavailable: {runtime.temp_summary_path}",
                )
            )
            return ExecMemoryStageResult(
                cycle_ready=False,
                build_status=None,
                promotion_result="snapshot_unavailable",
                advisory_note=f"Current-cycle summary snapshot unavailable: {runtime.temp_summary_path}",
            )

        # Execute build: Call run_python_step for build_exec_memory_packet
        run_python_step(
            step_name="build_exec_memory_packet",
            script_path=ctx.memory_packet_script,
            script_args=[
                "--loop-summary-json",
                str(runtime.temp_summary_path),
                "--output-json",
                str(ctx.exec_memory_current_json),
                "--output-md",
                str(ctx.exec_memory_current_md),
                "--status-json",
                str(ctx.exec_memory_build_status_json),
                "--pm-budget-tokens",
                str(ctx.pm_budget_tokens),
                "--ceo-budget-tokens",
                str(ctx.ceo_budget_tokens),
            ],
        )

        # Load build status: Parse exec_memory_build_status_json
        exec_memory_build_status = _load_exec_memory_build_status(ctx.exec_memory_build_status_json)

        # Promote outputs: Call _promote_exec_memory_outputs
        cycle_ready = _promote_exec_memory_outputs(
            _step_by_name("build_exec_memory_packet"),
            exec_memory_build_status,
        )

        # Determine promotion result
        if cycle_ready:
            promotion_result = "promoted"
            advisory_note = "Exec memory outputs promoted successfully."
        elif exec_memory_build_status is None:
            promotion_result = "build_failed"
            advisory_note = "Exec memory build status missing or invalid."
        elif not bool(exec_memory_build_status.get("authoritative_latest_written")):
            promotion_result = "not_authoritative"
            reason = str(exec_memory_build_status.get("reason", "")).strip() or "not_authoritative"
            advisory_note = f"Exec memory build did not produce authoritative outputs ({reason})."
        else:
            promotion_result = "build_failed"
            advisory_note = "Exec memory build failed or outputs missing."

        # Return ExecMemoryStageResult with explicit bundle
        return ExecMemoryStageResult(
            cycle_ready=cycle_ready,
            build_status=exec_memory_build_status,
            promotion_result=promotion_result,
            advisory_note=advisory_note,
        )

    def _write_temp_summary_snapshot() -> bool:
        temp_summary_dict = build_summary_payload(
            disagreement_sla=_scan_disagreement_sla(path=ctx.disagreement_ledger_jsonl, now_utc=_utc_now())
        )
        temp_summary_error = _validate_exact_path(
            runtime.temp_summary_path,
            ctx.context_dir / "loop_cycle_summary_current.json",
            "loop-cycle current summary snapshot",
        )
        if temp_summary_error is not None:
            runtime.steps.append(
                {
                    "name": "write_temp_summary",
                    "status": "ERROR",
                    "exit_code": None,
                    "command": [],
                    "started_utc": runtime.generated_at_utc,
                    "ended_utc": runtime.generated_at_utc,
                    "duration_seconds": 0.0,
                    "stdout": "",
                    "stderr": temp_summary_error,
                    "message": temp_summary_error,
                }
            )
            return False
        try:
            _atomic_write_text(runtime.temp_summary_path, json.dumps(temp_summary_dict, indent=2))
        except OSError as exc:
            runtime.steps.append(
                {
                    "name": "write_temp_summary",
                    "status": "ERROR",
                    "exit_code": None,
                    "command": [],
                    "started_utc": runtime.generated_at_utc,
                    "ended_utc": runtime.generated_at_utc,
                    "duration_seconds": 0.0,
                    "stdout": "",
                    "stderr": str(exc),
                    "message": f"Failed to write temp summary: {exc}",
                }
            )
            return False
        return True

    def _write_round_contract_summary_snapshot() -> bool:
        round_contract_summary = build_summary_payload(
            disagreement_sla=_scan_disagreement_sla(path=ctx.disagreement_ledger_jsonl, now_utc=_utc_now())
        )
        try:
            _atomic_write_text(ctx.output_json, json.dumps(round_contract_summary, indent=2) + "\n")
        except OSError as exc:
            runtime.steps.append(
                {
                    "name": "write_round_contract_summary",
                    "status": "ERROR",
                    "exit_code": None,
                    "command": [],
                    "started_utc": runtime.generated_at_utc,
                    "ended_utc": runtime.generated_at_utc,
                    "duration_seconds": 0.0,
                    "stdout": "",
                    "stderr": str(exc),
                    "message": f"Failed to write round-contract summary: {exc}",
                }
            )
            return False
        return True

    if ctx.skip_phase_end:
        runtime.steps.append(_skip_step("phase_end_handover", "Skipped by --skip-phase-end."))
    else:
        if not ctx.phase_end_script.exists():
            runtime.steps.append(
                {
                    "name": "phase_end_handover",
                    "status": "ERROR",
                    "exit_code": None,
                    "command": [],
                    "started_utc": runtime.generated_at_utc,
                    "ended_utc": runtime.generated_at_utc,
                    "duration_seconds": 0.0,
                    "stdout": "",
                    "stderr": "",
                    "message": f"Missing phase-end script: {ctx.phase_end_script}",
                }
            )
        else:
            phase_end_command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ctx.phase_end_script),
                "-RepoRoot",
                str(ctx.repo_root),
                "-AuditMode",
                str(ctx.phase_end_audit_mode),
            ]
            runtime.steps.append(
                _run_command(
                    step_name="phase_end_handover",
                    command=phase_end_command,
                    cwd=ctx.repo_root,
                )
            )

    run_python_step(
        step_name="refresh_weekly_calibration",
        script_path=ctx.auditor_script,
        script_args=[
            "--logs-dir",
            str(ctx.logs_dir),
            "--repo-id",
            ctx.repo_id,
            "--ledger",
            str(ctx.fp_ledger_json),
            "--output-json",
            str(ctx.weekly_report_json),
            "--output-md",
            str(ctx.weekly_report_md),
            "--mode",
            "weekly",
        ],
    )
    run_python_step(
        step_name="refresh_dossier",
        script_path=ctx.auditor_script,
        script_args=[
            "--logs-dir",
            str(ctx.logs_dir),
            "--repo-id",
            ctx.repo_id,
            "--ledger",
            str(ctx.fp_ledger_json),
            "--output-json",
            str(ctx.dossier_json),
            "--output-md",
            str(ctx.dossier_md),
            "--mode",
            "dossier",
        ],
    )
    run_python_step(
        step_name="generate_ceo_go_signal",
        script_path=ctx.go_signal_script,
        script_args=[
            "--calibration-json",
            str(ctx.weekly_report_json),
            "--dossier-json",
            str(ctx.dossier_json),
            "--output",
            str(ctx.go_signal_md),
        ],
    )
    if ctx.weekly_summary_gen_script.exists():
        run_python_step(
            step_name="refresh_ceo_weekly_summary",
            script_path=ctx.weekly_summary_gen_script,
            script_args=[
                "--dossier-json",
                str(ctx.dossier_json),
                "--calibration-json",
                str(ctx.weekly_report_json),
                "--go-signal-md",
                str(ctx.go_signal_md),
                "--output",
                str(ctx.weekly_summary_md),
            ],
        )
    else:
        runtime.steps.append(
            _skip_step(
                "refresh_ceo_weekly_summary",
                f"Script not found: {ctx.weekly_summary_gen_script}",
            )
        )

    # Phase 1.3 — Resume: skip exec_memory stage if already completed
    if "exec_memory" in _resume_steps:
        runtime.steps.append(
            _skip_step(
                "build_exec_memory_packet",
                "Resumed from checkpoint: exec_memory already completed.",
            )
        )
    else:
        exec_memory_result = _execute_exec_memory_stage()
        runtime.exec_memory_cycle_ready = exec_memory_result.cycle_ready

        # Phase 1.3 — Checkpoint write 1: after exec memory promotion
        if runtime.exec_memory_cycle_ready:
            _write_checkpoint(
                path=_checkpoint_path,
                cycle_id=_current_cycle_id or runtime.generated_at_utc,
                completed_steps=["exec_memory"],
                exec_memory_cycle_ready=True,
                partial=True,
            )
    if runtime.exec_memory_cycle_ready:
        _write_checkpoint(
            path=_checkpoint_path,
            cycle_id=_current_cycle_id or runtime.generated_at_utc,
            completed_steps=["exec_memory"],
            exec_memory_cycle_ready=True,
            partial=True,
        )


    if ctx.compaction_trigger_script.exists():
        if runtime.exec_memory_cycle_ready:
            run_python_step(
                step_name="evaluate_context_compaction_trigger",
                script_path=ctx.compaction_trigger_script,
                script_args=[
                    "--memory-json",
                    str(ctx.exec_memory_current_json),
                    "--dossier-json",
                    str(ctx.dossier_json),
                    "--go-signal-md",
                    str(ctx.go_signal_md),
                    "--state-json",
                    str(ctx.compaction_state_json),
                    "--output-json",
                    str(ctx.compaction_status_json),
                    "--pm-warn",
                    str(ctx.compaction_pm_warn),
                    "--ceo-warn",
                    str(ctx.compaction_ceo_warn),
                    "--force",
                    str(ctx.compaction_force),
                    "--max-age-hours",
                    str(ctx.compaction_max_age_hours),
                ],
            )
        else:
            runtime.steps.append(
                _skip_step(
                    "evaluate_context_compaction_trigger",
                    (
                        "Current-cycle exec memory packet unavailable: "
                        f"{ctx.exec_memory_current_json}"
                    ),
                )
            )
    else:
        runtime.steps.append(
            _skip_step(
                "evaluate_context_compaction_trigger",
                f"Script not found: {ctx.compaction_trigger_script}",
            )
        )

    if ctx.go_truth_script.exists():
        run_python_step(
            step_name="validate_ceo_go_signal_truth",
            script_path=ctx.go_truth_script,
            script_args=[
                "--dossier-json",
                str(ctx.dossier_json),
                "--calibration-json",
                str(ctx.weekly_report_json),
                "--go-signal-md",
                str(ctx.go_signal_md),
            ],
        )
    else:
        runtime.steps.append(
            _skip_step(
                "validate_ceo_go_signal_truth",
                f"Script not found: {ctx.go_truth_script}",
            )
        )

    if ctx.weekly_summary_md.exists() and ctx.weekly_truth_script.exists():
        run_python_step(
            step_name="validate_ceo_weekly_summary_truth",
            script_path=ctx.weekly_truth_script,
            script_args=[
                "--dossier-json",
                str(ctx.dossier_json),
                "--calibration-json",
                str(ctx.weekly_report_json),
                "--weekly-md",
                str(ctx.weekly_summary_md),
            ],
        )
    elif not ctx.weekly_summary_md.exists():
        runtime.steps.append(
            _skip_step(
                "validate_ceo_weekly_summary_truth",
                f"Weekly summary not found: {ctx.weekly_summary_md}",
            )
        )
    else:
        runtime.steps.append(
            _skip_step(
                "validate_ceo_weekly_summary_truth",
                f"Script not found: {ctx.weekly_truth_script}",
            )
        )

    if runtime.exec_memory_cycle_ready and ctx.memory_truth_script.exists():
        run_python_step(
            step_name="validate_exec_memory_truth",
            script_path=ctx.memory_truth_script,
            script_args=[
                "--memory-json",
                str(ctx.exec_memory_current_json),
                "--repo-root",
                str(ctx.repo_root),
            ],
        )
    elif not runtime.exec_memory_cycle_ready:
        runtime.steps.append(
            _skip_step(
                "validate_exec_memory_truth",
                (
                    "Current-cycle exec memory packet not available: "
                    f"{ctx.exec_memory_current_json}"
                ),
            )
        )
    else:
        runtime.steps.append(
            _skip_step(
                "validate_exec_memory_truth",
                f"Script not found: {ctx.memory_truth_script}",
            )
        )

    # Skip round contract validations if the file doesn't exist
    round_contract_md = ctx.context_dir / "round_contract_latest.md"
    if round_contract_md.exists():
        run_python_step(
            step_name="validate_counterexample_gate",
            script_path=ctx.counterexample_script,
            script_args=[
                "--round-contract-md",
                str(round_contract_md),
            ],
        )

        run_python_step(
            step_name="validate_dual_judge_gate",
            script_path=ctx.dual_judge_script,
            script_args=[
                "--round-contract-md",
                str(round_contract_md),
            ],
        )

        run_python_step(
            step_name="validate_refactor_mock_policy",
            script_path=ctx.refactor_mock_policy_script,
            script_args=[
                "--round-contract-md",
                str(round_contract_md),
            ],
        )
    else:
        runtime.steps.append(
            _skip_step(
                "validate_counterexample_gate",
                f"Round contract not found: {round_contract_md}",
            )
        )
        runtime.steps.append(
            _skip_step(
                "validate_dual_judge_gate",
                f"Round contract not found: {round_contract_md}",
            )
        )
        runtime.steps.append(
            _skip_step(
                "validate_refactor_mock_policy",
                f"Round contract not found: {round_contract_md}",
            )
        )

    if ctx.review_checklist_md.exists():
        run_python_step(
            step_name="validate_review_checklist",
            script_path=ctx.review_checklist_script,
            script_args=[
                "--input",
                str(ctx.review_checklist_md),
            ],
        )
    else:
        runtime.steps.append(
            _skip_step(
                "validate_review_checklist",
                f"Review checklist not found: {ctx.review_checklist_md}",
            )
        )

    if ctx.interface_contract_manifest_json.exists():
        run_python_step(
            step_name="validate_interface_contracts",
            script_path=ctx.interface_contracts_script,
            script_args=[
                "--manifest-json",
                str(ctx.interface_contract_manifest_json),
            ],
        )
    else:
        runtime.steps.append(
            _skip_step(
                "validate_interface_contracts",
                f"Interface contract manifest not found: {ctx.interface_contract_manifest_json}",
            )
        )

    run_python_step(
        step_name="validate_parallel_fanin",
        script_path=ctx.parallel_fanin_script,
        script_args=[
            "--context-dir",
            str(ctx.context_dir),
        ],
    )

    run_python_step(
        step_name="validate_loop_closure",
        script_path=ctx.closure_script,
        script_args=[
            "--repo-root",
            str(ctx.repo_root),
            "--context-dir",
            str(ctx.context_dir),
            "--dossier-json",
            str(ctx.dossier_json),
            "--calibration-json",
            str(ctx.weekly_report_json),
            "--go-signal-md",
            str(ctx.go_signal_md),
            "--weekly-summary-md",
            str(ctx.weekly_summary_md),
            "--go-truth-script",
            str(ctx.go_truth_script),
            "--weekly-truth-script",
            str(ctx.weekly_truth_script),
            "--memory-json",
            str(ctx.exec_memory_current_json),
            "--memory-truth-script",
            str(ctx.memory_truth_script),
            "--refactor-mock-policy-script",
            str(ctx.refactor_mock_policy_script),
            "--review-checklist-script",
            str(ctx.review_checklist_script),
            "--interface-contracts-script",
            str(ctx.interface_contracts_script),
            "--freshness-hours",
            str(ctx.freshness_hours),
            "--output-json",
            str(ctx.closure_output_json),
            "--output-md",
            str(ctx.closure_output_md),
        ],
    )

    if _write_round_contract_summary_snapshot() and round_contract_md.exists():
        run_python_step(
            step_name="validate_round_contract_checks",
            script_path=ctx.round_contract_checks_script,
            script_args=[
                "--round-contract-md",
                str(round_contract_md),
                "--loop-summary-json",
                str(ctx.output_json),
                "--closure-json",
                str(ctx.closure_output_json),
            ],
        )
    else:
        skip_reason = (
            f"Round contract not found: {round_contract_md}"
            if not round_contract_md.exists()
            else f"Round-contract summary snapshot unavailable: {ctx.output_json}"
        )
        runtime.steps.append(
            _skip_step(
                "validate_round_contract_checks",
                skip_reason,
            )
        )

    _apply_hold_semantics(
        steps=runtime.steps,
        allow_hold=ctx.allow_hold,
        closure_output_json=ctx.closure_output_json,
    )

    # Phase 2.2 — Gate A: before advisory artifact generation
    _gate_a_hold = False
    _gate_b_hold = False   # H-3
    _gate_decisions: list[dict] = []
    # F.1 — artifact reference paths for gate integrity tracking
    # sha256 for drift detection and equivalence.
    # hash=None if artifact absent or unreadable at gate time (non-fatal).
    _GATE_ARTIFACT_PATHS = [
        ctx.context_dir / "loop_run_trace_latest.json",
    ]
    _gate_a = PhaseGate(from_phase="exec_memory", to_phase="advisory", repo_root=ctx.repo_root)
    _gate_a_result = _gate_a.evaluate(runtime)
    # H-3: record gate_a decision
    _gate_decisions.append({
        "name": "gate_a",
        "decision": _gate_a_result.decision,
        "gate_executed": True,
        "gate_impl": type(_gate_a).__module__ + "." + type(_gate_a).__qualname__,
        "evaluated_at_utc": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        "artifact_refs": _build_artifact_refs(_GATE_ARTIFACT_PATHS),  # F.1 addition
    })
    try:
        _gate_a.emit(
            _gate_a_result,
            runtime.trace_id,
            output_path=ctx.context_dir / "phase_gate_a_latest.json",
        )
    except Exception as e:
        runtime.steps.append({"name": "gate_a_emit", "status": "WARN", "exit_code": None, "message": str(e)})
    if _gate_a_result.decision == "HOLD":
        _gate_a_hold = True
        _write_checkpoint(
            path=_checkpoint_path,
            cycle_id=_current_cycle_id or runtime.generated_at_utc,
            completed_steps=["exec_memory"],
            exec_memory_cycle_ready=runtime.exec_memory_cycle_ready,
            partial=True,
        )

    # Phase 1.3 — Resume: skip advisory step if already completed
    if _gate_a_hold:
        # Gate A HOLD: skip advisory, leave artifact fields as None
        runtime.next_round_handoff_artifacts = None
        runtime.expert_request_artifacts = None
        runtime.pm_ceo_research_brief_artifacts = None
        runtime.board_decision_brief_artifacts = None
        runtime.skill_activation_artifacts = None
        runtime.repo_root_convenience = {}
    elif "advisory" in _resume_steps:
        # Advisory already completed — leave runtime artifact fields as None;
        # loop will still write the final summary using existing artifacts.
        pass
    elif runtime.exec_memory_cycle_ready:
        advisory_artifacts = persist_advisory_sections(
            context_dir=ctx.context_dir,
            exec_memory_json=ctx.exec_memory_latest_json,
        )
        runtime.next_round_handoff_artifacts = advisory_artifacts["next_round_handoff"]
        runtime.expert_request_artifacts = advisory_artifacts["expert_request"]
        runtime.pm_ceo_research_brief_artifacts = advisory_artifacts["pm_ceo_research_brief"]
        runtime.board_decision_brief_artifacts = advisory_artifacts["board_decision_brief"]
        runtime.skill_activation_artifacts = advisory_artifacts["skill_activation"]
        runtime.repo_root_convenience = mirror_repo_root_convenience(
            repo_root=ctx.repo_root,
            context_dir=ctx.context_dir,
            advisory_artifacts=advisory_artifacts,
        )
        # Phase 1.3 — Checkpoint write 2: after advisory artifacts written
        _write_checkpoint(
            path=_checkpoint_path,
            cycle_id=_current_cycle_id or runtime.generated_at_utc,
            completed_steps=["exec_memory", "advisory"],
            exec_memory_cycle_ready=True,
            partial=True,
        )
    else:
        runtime.next_round_handoff_artifacts = None
        runtime.expert_request_artifacts = None
        runtime.pm_ceo_research_brief_artifacts = None
        runtime.board_decision_brief_artifacts = None
        runtime.skill_activation_artifacts = None
        runtime.repo_root_convenience = {}

    # Phase 2.2 — Gate B: before loop summary build
    # _gate_a_hold is set exclusively by Gate A evaluation above.
    if not _gate_a_hold:
        _gate_b = PhaseGate(from_phase="advisory", to_phase="summary", repo_root=ctx.repo_root)
        _gate_b_result = _gate_b.evaluate(runtime)
        # H-3: record gate_b decision
        _gate_decisions.append({
            "name": "gate_b",
            "decision": _gate_b_result.decision,
            "gate_executed": True,
            "gate_impl": type(_gate_b).__module__ + "." + type(_gate_b).__qualname__,
            "evaluated_at_utc": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            "artifact_refs": _build_artifact_refs(_GATE_ARTIFACT_PATHS),  # F.1 addition
        })
        try:
            _gate_b.emit(
                _gate_b_result,
                runtime.trace_id,
                output_path=ctx.context_dir / "phase_gate_b_latest.json",
            )
        except Exception as e:
            runtime.steps.append({"name": "gate_b_emit", "status": "WARN", "exit_code": None, "message": str(e)})
        if _gate_b_result.decision == "PROCEED":
            try:
                _gate_b.emit_handoff(
                    runtime.trace_id,
                    output_path=ctx.context_dir / "phase_handoff_latest.json",
                )
            except Exception as e:
                runtime.steps.append({"name": "gate_b_handoff_emit", "status": "WARN", "exit_code": None, "message": str(e)})
        elif _gate_b_result.decision == "HOLD":
            _gate_b_hold = True  # H-3
            _write_checkpoint(
                path=_checkpoint_path,
                cycle_id=_current_cycle_id or runtime.generated_at_utc,
                completed_steps=["exec_memory", "advisory"],
                exec_memory_cycle_ready=runtime.exec_memory_cycle_ready,
                partial=True,
            )
    else:
        # Gate A already held — record gate_b as skipped
        _gate_decisions.append({
            "name": "gate_b",
            "decision": "HOLD",
            "gate_executed": False,
            "skipped_reason": "gate_a_hold=True",
            "evaluated_at_utc": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            "artifact_refs": {},  # gate not executed, no artifacts to ref
        })

    _any_gate_hold = _gate_a_hold or _gate_b_hold
    disagreement_sla = _scan_disagreement_sla(path=ctx.disagreement_ledger_jsonl, now_utc=_utc_now())
    # H-3: gate HOLD only applies when no ERROR/critical-FAIL steps exist.
    # If exec_memory or another step produced ERROR/FAIL(exit_code=2), ERROR wins.
    _has_critical_error = any(
        s.get("status") == "ERROR" or
        (s.get("status") == "FAIL" and s.get("exit_code") == 2)
        for s in runtime.steps
    )
    if _any_gate_hold and not _has_critical_error:
        _hold_artifacts = {
            "weekly_report_json": str(ctx.weekly_report_json),
            "dossier_json": str(ctx.dossier_json),
            "exec_memory_latest_promoted": runtime.exec_memory_cycle_ready,
            "closure_output_json": str(ctx.closure_output_json),
            "summary_output_json": str(ctx.output_json),
        }
        _hold_ctx_fields = {
            "repo_root": str(ctx.repo_root),
            "context_dir": str(ctx.context_dir),
            "skip_phase_end": ctx.skip_phase_end,
            "allow_hold": ctx.allow_hold,
            "freshness_hours": ctx.freshness_hours,
            "lessons": {
                "worker": str(runtime.lessons_paths["worker"]),
                "auditor": str(runtime.lessons_paths["auditor"]),
            },
        }
        payload = _build_hold_summary_payload(
            gate_a_hold=_gate_a_hold,
            gate_b_hold=_gate_b_hold,
            gate_decisions=_gate_decisions,
            steps=list(runtime.steps),
            artifacts=_hold_artifacts,
            ctx_fields=_hold_ctx_fields,
        )
    else:
        _base_payload = build_summary_payload(
            disagreement_sla=disagreement_sla,
        )
        # H-3: inject gate_decisions into healthy-path payload
        _base_payload["gate_decisions"] = _gate_decisions
        payload = _base_payload
    final_result = str(payload["final_result"])
    final_exit_code = int(payload["final_exit_code"])

    # Phase 2.1 — emit run trace artifact
    _run_start = runtime.generated_at
    _run_end = _utc_now()
    _duration = round((_run_end - _run_start).total_seconds(), 3)
    _step_summary = payload.get("step_summary", {})
    _trace_payload = {
        "schema_version": "1.0",
        "trace_id": runtime.trace_id,
        "generated_at_utc": _utc_iso(_run_end),
        "repo_id": ctx.repo_id,
        "duration_seconds": _duration,
        "steps": [
            {
                "name": s["name"],
                "status": s["status"],
                "exit_code": s.get("exit_code"),
                "started_utc": s.get("started_utc", ""),
                "ended_utc": s.get("ended_utc", ""),
                "duration_seconds": s.get("duration_seconds", 0.0),
            }
            for s in runtime.steps
        ],
        "metrics": {
            "pass_count": _step_summary.get("pass_count", 0),
            "hold_count": _step_summary.get("hold_count", 0),
            "fail_count": _step_summary.get("fail_count", 0),
            "error_count": _step_summary.get("error_count", 0),
            "skip_count": _step_summary.get("skip_count", 0),
            "total_steps": _step_summary.get("total_steps", 0),
            "artifact_count": len(payload.get("artifacts", {})),
        },
        "final_result": final_result,
        "final_exit_code": final_exit_code,
    }
    _trace_path = ctx.context_dir / "loop_run_trace_latest.json"
    try:
        atomic_write_json(_trace_path, _trace_payload)
    except Exception as e:
        runtime.steps.append({
            "name": "trace_write",
            "status": "WARN",
            "exit_code": None,
            "message": str(e),
            "reason": str(e),
        })  # Trace write failure must never abort the loop
    # Rolling NDJSON compaction
    try:
        _compact_ndjson_rolling(ctx.context_dir / "loop_run_steps_latest.ndjson", max_records=500)
        _compact_ndjson_rolling(ctx.context_dir / "loop_run_steps_rolling.ndjson", max_records=500)
    except Exception:
        pass
    # Append all steps to rolling NDJSON
    _rolling_path = ctx.context_dir / "loop_run_steps_rolling.ndjson"
    for _rs in runtime.steps:
        _append_step_ndjson(_rolling_path, runtime.trace_id, _rs)

    md_lines: list[str] = [
        "# Loop Cycle Summary",
        "",
        f"- GeneratedAtUTC: {runtime.generated_at_utc}",
        f"- FinalResult: {final_result}",
        f"- FinalExitCode: {final_exit_code}",
        f"- SkipPhaseEnd: {bool(ctx.skip_phase_end)}",
        "",
        "| Step | Status | Exit | Message |",
        "|---|---|---:|---|",
    ]
    for step in runtime.steps:
        exit_value = step["exit_code"]
        exit_text = "N/A" if exit_value is None else str(exit_value)
        message = str(step.get("message", "")).replace("|", "\\|")
        md_lines.append(f"| {step['name']} | {step['status']} | {exit_text} | {message} |")

    md_lines.extend(
        [
            "",
            "## Disagreement SLA",
            "",
            f"- LedgerExists: {disagreement_sla['exists']}",
            f"- TotalEntries: {disagreement_sla['total_entries']}",
            f"- UnresolvedEntries: {disagreement_sla['unresolved_entries']}",
            f"- OverdueUnresolved: {disagreement_sla['overdue_unresolved_count']}",
            f"- ParseErrors: {len(disagreement_sla['parse_errors'])}",
            "",
        ]
    )
    if disagreement_sla["overdue_unresolved_count"] > 0:
        md_lines.extend(
            [
                "### Overdue Unresolved Entries",
                "",
                "| Line | Round | Task | Code | Severity | Owner | DueUTC |",
                "|---:|---|---|---|---|---|---|",
            ]
        )
        for item in disagreement_sla["overdue_unresolved"]:
            md_lines.append(
                "| {line} | {round_id} | {task_id} | {code} | {severity} | {owner} | {due_utc} |".format(
                    line=item.get("line", ""),
                    round_id=item.get("round_id", ""),
                    task_id=item.get("task_id", ""),
                    code=item.get("code", ""),
                    severity=item.get("severity", ""),
                    owner=item.get("owner", ""),
                    due_utc=item.get("due_utc", ""),
                )
            )
        md_lines.append("")

    md_lines.extend(
        [
            "## Lesson Stubs",
            "",
            f"- Worker: {runtime.lessons_paths['worker']}",
            f"- Auditor: {runtime.lessons_paths['auditor']}",
            "",
        ]
    )
    if runtime.next_round_handoff_artifacts is not None:
        md_lines.extend(
            [
                "## Next Round Handoff",
                "",
                f"- Status: {runtime.next_round_handoff_artifacts['status']}",
                f"- JSON: {runtime.next_round_handoff_artifacts['json']}",
                f"- Markdown: {runtime.next_round_handoff_artifacts['md']}",
                "",
            ]
        )
    if runtime.expert_request_artifacts is not None:
        md_lines.extend(
            [
                "## Expert Request",
                "",
                f"- Status: {runtime.expert_request_artifacts['status']}",
                f"- TargetExpert: {runtime.expert_request_artifacts['payload'].get('target_expert', '')}",
                f"- JSON: {runtime.expert_request_artifacts['json']}",
                f"- Markdown: {runtime.expert_request_artifacts['md']}",
                "",
            ]
        )
    if runtime.pm_ceo_research_brief_artifacts is not None:
        md_lines.extend(
            [
                "## PM/CEO Research Brief",
                "",
                f"- Status: {runtime.pm_ceo_research_brief_artifacts['status']}",
                f"- DelegatedTo: {runtime.pm_ceo_research_brief_artifacts['payload'].get('delegated_to', '')}",
                f"- JSON: {runtime.pm_ceo_research_brief_artifacts['json']}",
                f"- Markdown: {runtime.pm_ceo_research_brief_artifacts['md']}",
                "",
            ]
        )
    if runtime.board_decision_brief_artifacts is not None:
        md_lines.extend(
            [
                "## Board Decision Brief",
                "",
                f"- Status: {runtime.board_decision_brief_artifacts['status']}",
                f"- DecisionTopic: {runtime.board_decision_brief_artifacts['payload'].get('decision_topic', '')}",
                f"- RecommendedOption: {runtime.board_decision_brief_artifacts['payload'].get('recommended_option', '')}",
                f"- JSON: {runtime.board_decision_brief_artifacts['json']}",
                f"- Markdown: {runtime.board_decision_brief_artifacts['md']}",
                "",
            ]
        )
    if runtime.skill_activation_artifacts is not None:
        skill_count = len(runtime.skill_activation_artifacts['payload'].get('skills', []))
        md_lines.extend(
            [
                "## Skill Activation",
                "",
                f"- Status: {runtime.skill_activation_artifacts['status']}",
                f"- ActiveSkills: {skill_count}",
            ]
        )
        # Expanded visibility: show each skill's key fields
        for skill in runtime.skill_activation_artifacts['payload'].get('skills', []):
            skill_name = skill.get('name', 'unknown')
            skill_version = skill.get('version', 'unknown')
            skill_category = skill.get('category', 'unknown')
            skill_risk = skill.get('risk_level', 'UNKNOWN')
            skill_desc = skill.get('description', '')
            skill_approval = skill.get('approval_decision_id', 'N/A')
            # Truncate description for readability
            desc_short = skill_desc[:60] + "..." if len(skill_desc) > 60 else skill_desc
            md_lines.extend(
                [
                    f"  - {skill_name} (v{skill_version})",
                    f"    - Category: {skill_category}",
                    f"    - Risk: {skill_risk}",
                    f"    - Description: {desc_short}",
                    f"    - ApprovedBy: {skill_approval}",
                ]
            )
        # Show warnings/errors if present
        warnings = runtime.skill_activation_artifacts['payload'].get('warnings', [])
        errors = runtime.skill_activation_artifacts['payload'].get('errors', [])
        if warnings:
            md_lines.append(f"- Warnings: {len(warnings)}")
            for w in warnings[:3]:  # Show first 3
                md_lines.append(f"  - {w[:80]}")
        if errors:
            md_lines.append(f"- Errors: {len(errors)}")
            for e in errors[:3]:
                md_lines.append(f"  - {e[:80]}")
        md_lines.extend(
            [
                f"- JSON: {runtime.skill_activation_artifacts['json']}",
                "",
            ]
        )
    if runtime.repo_root_convenience:
        md_lines.extend(
            [
                "## Repo-Root Convenience Files",
                "",
                f"- SourceOfTruth: {ctx.context_dir}",
            ]
        )
        for section_key, _, title in REPO_ROOT_CONVENIENCE_SPECS:
            mirror_path = runtime.repo_root_convenience.get(section_key)
            if mirror_path is None:
                continue
            md_lines.append(f"- {title}: {mirror_path}")
        takeover_path = runtime.repo_root_convenience.get("takeover")
        if takeover_path is not None:
            md_lines.append(f"- Takeover Index: {takeover_path}")
        md_lines.append("")
    markdown = "\n".join(md_lines)

    try:
        _atomic_write_text(ctx.output_json, json.dumps(payload, indent=2) + "\n")
        _atomic_write_text(ctx.output_md, markdown)
    except OSError as e:
        _write_hard_failure("EXECUTION_ERROR", "output_write", str(e), "RETRYABLE")
        payload["final_result"] = "ERROR"
        payload["final_exit_code"] = 2
        return 2, payload, markdown

    # Phase 1.3 — Checkpoint write 3: terminal — loop completed cleanly
    _write_checkpoint(
        path=_checkpoint_path,
        cycle_id=_current_cycle_id or runtime.generated_at_utc,
        completed_steps=["exec_memory", "advisory", "loop_summary"],
        exec_memory_cycle_ready=runtime.exec_memory_cycle_ready,
        partial=False,
    )

    # K.2: observability pack drift marker check
    _obs_pack_path = ctx.context_dir / "observability_pack_current.md"
    if _obs_pack_path.exists():
        runtime.steps.append({
            "name": "observability_pack",
            "status": "OK",
            "exit_code": 0,
            "message": "",
        })
    else:
        runtime.steps.append({
            "name": "observability_pack",
            "status": "WARN",
            "exit_code": None,
            "message": "observability_pack_current.md not found — drift markers unavailable",
        })

    return final_exit_code, payload, markdown




def run_cycle_int(args: argparse.Namespace) -> int:
    """Phase 2.3 thin wrapper: run one loop cycle and return the exit code as int.

    Delegates to run_cycle() which returns (exit_code, payload, markdown).
    """
    exit_code, _payload, _md = run_cycle(args)
    return exit_code

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        exit_code, payload, _ = run_cycle(args)
        print(payload["final_result"])
        # Debug output for CI failures
        if payload["final_result"] in ("ERROR", "FAIL"):
            print(f"DEBUG: message={payload.get('message', 'N/A')}", file=sys.stderr)
            if payload.get("steps"):
                print(f"DEBUG: total_steps={len(payload['steps'])}", file=sys.stderr)
                for step in payload["steps"]:
                    print(f"DEBUG: step={step.get('name')} status={step.get('status')} exit_code={step.get('exit_code')} message={step.get('message', '')[:100]}", file=sys.stderr)
        return exit_code
    except Exception as e:
        # Only fires if exception escapes run_cycle() entirely.
        # run_failure_latest.json has NOT been written on this path.
        # Do NOT call _write_hard_failure if run_cycle() returned normally with ERROR.
        _write_hard_failure("EXECUTION_ERROR", "run_cycle", str(e), "REQUIRES_FIX")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
