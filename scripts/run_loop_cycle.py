from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
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
        import os
        def validate_artifact_path(path: str, repo_root: Path) -> tuple[bool, str]:
            """Simplified fallback matching scripts/utils/path_validator.py."""
            path = str(path).strip()
            if not path:
                return False, "Empty path"
            if path.startswith("/") or (len(path) >= 2 and path[1] == ":"):
                return False, f"Absolute path not allowed: {path}"
            if ".." in path.split(os.sep):
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


class ExecMemoryStageResult:
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


def _error_result(message: str) -> tuple[int, dict[str, Any], str]:
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

    # Build mutable runtime state
    runtime = build_loop_cycle_runtime(ctx)

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
            "final_result": final_result,
            "final_exit_code": final_exit_code,
        }

    def run_python_step(step_name: str, script_path: Path, script_args: list[str]) -> None:
        if not script_path.exists():
            runtime.steps.append(
                {
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
            )
            return
        command = [ctx.python_exe, str(script_path)] + script_args
        runtime.steps.append(_run_command(step_name=step_name, command=command, cwd=ctx.repo_root))

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

    exec_memory_result = _execute_exec_memory_stage()
    runtime.exec_memory_cycle_ready = exec_memory_result.cycle_ready


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

    run_python_step(
        step_name="validate_counterexample_gate",
        script_path=ctx.counterexample_script,
        script_args=[
            "--round-contract-md",
            str(ctx.context_dir / "round_contract_latest.md"),
        ],
    )

    run_python_step(
        step_name="validate_dual_judge_gate",
        script_path=ctx.dual_judge_script,
        script_args=[
            "--round-contract-md",
            str(ctx.context_dir / "round_contract_latest.md"),
        ],
    )

    run_python_step(
        step_name="validate_refactor_mock_policy",
        script_path=ctx.refactor_mock_policy_script,
        script_args=[
            "--round-contract-md",
            str(ctx.context_dir / "round_contract_latest.md"),
        ],
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

    if _write_round_contract_summary_snapshot():
        run_python_step(
            step_name="validate_round_contract_checks",
            script_path=ctx.round_contract_checks_script,
            script_args=[
                "--round-contract-md",
                str(ctx.context_dir / "round_contract_latest.md"),
                "--loop-summary-json",
                str(ctx.output_json),
                "--closure-json",
                str(ctx.closure_output_json),
            ],
        )
    else:
        runtime.steps.append(
            _skip_step(
                "validate_round_contract_checks",
                f"Round-contract summary snapshot unavailable: {ctx.output_json}",
            )
        )

    _apply_hold_semantics(
        steps=runtime.steps,
        allow_hold=ctx.allow_hold,
        closure_output_json=ctx.closure_output_json,
    )

    if runtime.exec_memory_cycle_ready:
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
    else:
        runtime.next_round_handoff_artifacts = None
        runtime.expert_request_artifacts = None
        runtime.pm_ceo_research_brief_artifacts = None
        runtime.board_decision_brief_artifacts = None
        runtime.skill_activation_artifacts = None
        runtime.repo_root_convenience = {}

    disagreement_sla = _scan_disagreement_sla(path=ctx.disagreement_ledger_jsonl, now_utc=_utc_now())

    payload = build_summary_payload(
        disagreement_sla=disagreement_sla,
    )
    final_result = str(payload["final_result"])
    final_exit_code = int(payload["final_exit_code"])

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
    except OSError:
        payload["final_result"] = "ERROR"
        payload["final_exit_code"] = 2
        return 2, payload, markdown

    return final_exit_code, payload, markdown


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, payload, _ = run_cycle(args)
    print(payload["final_result"])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
