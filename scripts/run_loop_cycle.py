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

DOSSIER_HOLD_MARKER = "DOSSIER CRITERIA NOT MET"
REPO_ROOT_CONVENIENCE_SPECS: tuple[tuple[str, str, str], ...] = (
    ("next_round_handoff", "NEXT_ROUND_HANDOFF_LATEST.md", "Next Round Handoff"),
    ("expert_request", "EXPERT_REQUEST_LATEST.md", "Expert Request"),
    ("pm_ceo_research_brief", "PM_CEO_RESEARCH_BRIEF_LATEST.md", "PM/CEO Research Brief"),
    ("board_decision_brief", "BOARD_DECISION_BRIEF_LATEST.md", "Board Decision Brief"),
)
REPO_ROOT_TAKEOVER_FILENAME = "TAKEOVER_LATEST.md"


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


def _write_lessons_stubs(context_dir: Path, generated_at_utc: str) -> dict[str, Path]:
    worker_path = context_dir / "lessons_worker_latest.md"
    auditor_path = context_dir / "lessons_auditor_latest.md"

    worker_stub = "\n".join(
        [
            "# Worker Lessons Stub",
            "",
            f"- GeneratedAtUTC: {generated_at_utc}",
            "- Cycle: latest loop run",
            "",
            "## Prompt",
            "1. What delivery decision had the highest impact this cycle?",
            "2. What caused avoidable rework and how will you prevent it next cycle?",
            "3. Which evidence artifact was missing or weak and needs automation?",
            "4. What should be stopped, started, and continued next cycle?",
            "",
            "## Notes",
            "- Fill with concrete examples and artifact paths.",
            "",
        ]
    )
    auditor_stub = "\n".join(
        [
            "# Auditor Lessons Stub",
            "",
            f"- GeneratedAtUTC: {generated_at_utc}",
            "- Cycle: latest loop run",
            "",
            "## Prompt",
            "1. Which gate caught the highest-risk issue this cycle?",
            "2. Which check produced noise or false positives and why?",
            "3. What additional guardrail or threshold change is needed?",
            "4. Which unresolved risk needs explicit CEO/PM follow-up next cycle?",
            "",
            "## Notes",
            "- Include rule IDs, artifact paths, and concrete follow-up actions.",
            "",
        ]
    )

    _atomic_write_text(worker_path, worker_stub)
    _atomic_write_text(auditor_path, auditor_stub)
    return {"worker": worker_path, "auditor": auditor_path}


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _append_split_sections(
    lines: list[str],
    *,
    human_brief: str,
    machine_view: str,
    paste_ready_block: str,
) -> None:
    if human_brief:
        lines.extend(["## Human Brief", "", human_brief, ""])
    if machine_view:
        lines.extend(["## Machine View", "", "```text", machine_view, "```", ""])
    if paste_ready_block:
        lines.extend(["## Paste-Ready Block", "", "```text", paste_ready_block, "```", ""])


def _stringify_optional_value(value: Any) -> str:
    if isinstance(value, dict):
        rendered_parts: list[str] = []
        for key, item in value.items():
            item_text = _stringify_optional_value(item)
            if item_text:
                rendered_parts.append(f"{key}={item_text}")
        return "; ".join(rendered_parts)
    if isinstance(value, list):
        rendered_items = [item for item in (_stringify_optional_value(item) for item in value) if item]
        return ", ".join(rendered_items)
    text = str(value).strip()
    return text


def _append_optional_detail_section(
    lines: list[str],
    *,
    heading: str,
    items: list[tuple[str, Any]],
) -> None:
    rendered_items: list[tuple[str, str]] = []
    for label, value in items:
        text = _stringify_optional_value(value)
        if text:
            rendered_items.append((label, text))
    if not rendered_items:
        return
    lines.extend([f"## {heading}", ""])
    for label, text in rendered_items:
        lines.append(f"- {label}: {text}")
    lines.append("")


def _render_next_round_handoff_markdown(payload: dict[str, Any]) -> str:
    status = str(payload.get("status", "UNKNOWN")).strip() or "UNKNOWN"
    recommended_intent = str(payload.get("recommended_intent", "")).strip() or "N/A"
    recommended_scope = str(payload.get("recommended_scope", "")).strip() or "N/A"
    non_goals = str(payload.get("non_goals", "")).strip() or "N/A"
    done_when = str(payload.get("done_when", "")).strip() or "N/A"
    done_when_checks = _coerce_string_list(
        payload.get("recommended_done_when_checks") or payload.get("done_when_checks")
    )
    artifacts_to_refresh = _coerce_string_list(payload.get("artifacts_to_refresh"))
    primary_blockers = _coerce_string_list(
        payload.get("primary_blockers") or payload.get("blocking_gap_codes")
    )
    human_brief = str(payload.get("human_brief", "")).strip()
    machine_view = str(payload.get("machine_view", "")).strip()
    paste_ready_block = str(payload.get("paste_ready_block", "")).strip()

    lines: list[str] = [
        "# Next Round Handoff",
        "",
        f"- Status: {status}",
        f"- RecommendedIntent: {recommended_intent}",
        f"- RecommendedScope: {recommended_scope}",
        f"- NonGoals: {non_goals}",
        f"- DoneWhen: {done_when}",
        "",
    ]

    if done_when_checks:
        lines.extend(["## Done-When Checks", ""])
        for check in done_when_checks:
            lines.append(f"- {check}")
        lines.append("")

    if primary_blockers:
        lines.extend(["## Primary Blockers", ""])
        for code in primary_blockers:
            lines.append(f"- {code}")
        lines.append("")

    if artifacts_to_refresh:
        lines.extend(["## Artifacts To Refresh", ""])
        for path in artifacts_to_refresh:
            lines.append(f"- `{path}`")
        lines.append("")

    _append_split_sections(
        lines,
        human_brief=human_brief,
        machine_view=machine_view,
        paste_ready_block=paste_ready_block,
    )

    return "\n".join(lines)


def _render_expert_request_markdown(payload: dict[str, Any]) -> str:
    status = str(payload.get("status", "UNKNOWN")).strip() or "UNKNOWN"
    target_expert = str(payload.get("target_expert", "")).strip() or "N/A"
    trigger_reason = str(payload.get("trigger_reason", "")).strip() or "N/A"
    question = str(payload.get("question", "")).strip() or "N/A"
    source_artifacts = _coerce_string_list(payload.get("source_artifacts"))
    human_brief = str(payload.get("human_brief", "")).strip()
    machine_view = str(payload.get("machine_view", "")).strip()
    paste_ready_block = str(payload.get("paste_ready_block", "")).strip()

    lines: list[str] = [
        "# Expert Request",
        "",
        f"- Status: {status}",
        f"- TargetExpert: {target_expert}",
        f"- TriggerReason: {trigger_reason}",
        f"- Question: {question}",
        "",
    ]
    if source_artifacts:
        lines.extend(["## Source Artifacts", ""])
        for path in source_artifacts:
            lines.append(f"- `{path}`")
        lines.append("")

    _append_optional_detail_section(
        lines,
        heading="Lineup",
        items=[
            ("RequestedDomain", payload.get("requested_domain")),
            ("RosterFit", payload.get("roster_fit")),
            ("MilestoneId", payload.get("milestone_id")),
            ("BoardReentryRequired", payload.get("board_reentry_required")),
            ("BoardReentryReasonCodes", payload.get("board_reentry_reason_codes")),
        ],
    )
    _append_optional_detail_section(
        lines,
        heading="Memory",
        items=[
            ("ExpertMemoryStatus", payload.get("expert_memory_status")),
            ("BoardMemoryStatus", payload.get("board_memory_status")),
            ("MemoryReasonCodes", payload.get("memory_reason_codes")),
        ],
    )

    _append_split_sections(
        lines,
        human_brief=human_brief,
        machine_view=machine_view,
        paste_ready_block=paste_ready_block,
    )
    return "\n".join(lines)


def _render_pm_ceo_research_brief_markdown(payload: dict[str, Any]) -> str:
    status = str(payload.get("status", "UNKNOWN")).strip() or "UNKNOWN"
    delegated_to = str(payload.get("delegated_to", "")).strip() or "N/A"
    question = str(payload.get("question", "")).strip() or "N/A"
    tradeoff_dimensions = _coerce_string_list(payload.get("required_tradeoff_dimensions"))
    evidence_required = _coerce_string_list(payload.get("evidence_required"))
    human_brief = str(payload.get("human_brief", "")).strip()
    machine_view = str(payload.get("machine_view", "")).strip()
    paste_ready_block = str(payload.get("paste_ready_block", "")).strip()

    lines: list[str] = [
        "# PM/CEO Research Brief",
        "",
        f"- Status: {status}",
        f"- DelegatedTo: {delegated_to}",
        f"- Question: {question}",
        "",
    ]
    if tradeoff_dimensions:
        lines.extend(["## Tradeoff Dimensions", ""])
        for item in tradeoff_dimensions:
            lines.append(f"- {item}")
        lines.append("")
    if evidence_required:
        lines.extend(["## Evidence Required", ""])
        for path in evidence_required:
            lines.append(f"- `{path}`")
        lines.append("")

    _append_split_sections(
        lines,
        human_brief=human_brief,
        machine_view=machine_view,
        paste_ready_block=paste_ready_block,
    )
    return "\n".join(lines)


def _render_board_decision_brief_markdown(payload: dict[str, Any]) -> str:
    status = str(payload.get("status", "UNKNOWN")).strip() or "UNKNOWN"
    decision_topic = str(payload.get("decision_topic", "")).strip() or "N/A"
    recommended_option = str(payload.get("recommended_option", "")).strip() or "N/A"
    source_artifacts = _coerce_string_list(payload.get("source_artifacts"))
    open_risks = _coerce_string_list(payload.get("open_risks"))
    human_brief = str(payload.get("human_brief", "")).strip()
    machine_view = str(payload.get("machine_view", "")).strip()
    paste_ready_block = str(payload.get("paste_ready_block", "")).strip()

    lines: list[str] = [
        "# Board Decision Brief",
        "",
        f"- Status: {status}",
        f"- DecisionTopic: {decision_topic}",
        f"- RecommendedOption: {recommended_option}",
        "",
    ]

    lens_sections = (
        ("CEO Lens", payload.get("ceo_lens")),
        ("CTO Lens", payload.get("cto_lens")),
        ("COO Lens", payload.get("coo_lens")),
        ("Expert Lens", payload.get("expert_lens")),
    )
    for title, value in lens_sections:
        if isinstance(value, str):
            text = value.strip()
            if text:
                lines.extend([f"## {title}", "", text, ""])
        elif isinstance(value, dict) and value:
            lines.extend([f"## {title}", ""])
            for key, item in value.items():
                item_text = str(item).strip()
                if item_text:
                    lines.append(f"- {key}: {item_text}")
            lines.append("")

    if source_artifacts:
        lines.extend(["## Source Artifacts", ""])
        for path in source_artifacts:
            lines.append(f"- `{path}`")
        lines.append("")

    _append_optional_detail_section(
        lines,
        heading="Lineup",
        items=[
            ("LineupDecisionNeeded", payload.get("lineup_decision_needed")),
            ("LineupGapDomains", payload.get("lineup_gap_domains")),
            ("ApprovedRosterSnapshot", payload.get("approved_roster_snapshot")),
            ("ReintroduceBoardWhen", payload.get("reintroduce_board_when")),
            ("BoardReentryRequired", payload.get("board_reentry_required")),
            ("BoardReentryReasonCodes", payload.get("board_reentry_reason_codes")),
        ],
    )
    _append_optional_detail_section(
        lines,
        heading="Memory",
        items=[
            ("ExpertMemoryStatus", payload.get("expert_memory_status")),
            ("BoardMemoryStatus", payload.get("board_memory_status")),
            ("MemoryReasonCodes", payload.get("memory_reason_codes")),
        ],
    )

    if open_risks:
        lines.extend(["## Open Risks", ""])
        for risk in open_risks:
            lines.append(f"- {risk}")
        lines.append("")

    _append_split_sections(
        lines,
        human_brief=human_brief,
        machine_view=machine_view,
        paste_ready_block=paste_ready_block,
    )

    return "\n".join(lines)


def _persist_exec_memory_section(
    *,
    context_dir: Path,
    exec_memory_json: Path,
    section_key: str,
    output_prefix: str,
    renderer: Any,
) -> dict[str, Any] | None:
    if not exec_memory_json.exists():
        return None

    try:
        memory_payload = json.loads(exec_memory_json.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None

    section_payload = memory_payload.get(section_key)
    if not isinstance(section_payload, dict) or not section_payload:
        return None

    output_json = context_dir / f"{output_prefix}_latest.json"
    output_md = context_dir / f"{output_prefix}_latest.md"
    artifact_payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": str(memory_payload.get("generated_at_utc", "")).strip(),
        "source_exec_memory_json": str(exec_memory_json),
        section_key: section_payload,
    }
    markdown = renderer(section_payload)
    _atomic_write_text(output_json, json.dumps(artifact_payload, indent=2) + "\n")
    _atomic_write_text(output_md, markdown)
    return {
        "json": output_json,
        "md": output_md,
        "status": str(section_payload.get("status", "")).strip() or "UNKNOWN",
        "payload": section_payload,
    }


def _persist_next_round_handoff(
    *,
    context_dir: Path,
    exec_memory_json: Path,
) -> dict[str, Any] | None:
    return _persist_exec_memory_section(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
        section_key="next_round_handoff",
        output_prefix="next_round_handoff",
        renderer=_render_next_round_handoff_markdown,
    )


def _persist_expert_request(
    *,
    context_dir: Path,
    exec_memory_json: Path,
) -> dict[str, Any] | None:
    return _persist_exec_memory_section(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
        section_key="expert_request",
        output_prefix="expert_request",
        renderer=_render_expert_request_markdown,
    )


def _persist_pm_ceo_research_brief(
    *,
    context_dir: Path,
    exec_memory_json: Path,
) -> dict[str, Any] | None:
    return _persist_exec_memory_section(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
        section_key="pm_ceo_research_brief",
        output_prefix="pm_ceo_research_brief",
        renderer=_render_pm_ceo_research_brief_markdown,
    )


def _persist_board_decision_brief(
    *,
    context_dir: Path,
    exec_memory_json: Path,
) -> dict[str, Any] | None:
    return _persist_exec_memory_section(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
        section_key="board_decision_brief",
        output_prefix="board_decision_brief",
        renderer=_render_board_decision_brief_markdown,
    )


def _render_takeover_latest_markdown(
    *,
    context_dir: Path,
    mirrored_files: dict[str, Path],
    advisory_artifacts: dict[str, dict[str, Any] | None],
) -> str:
    lines: list[str] = [
        "# Takeover Latest",
        "",
        "- Purpose: repo-root convenience mirrors for the latest paste-ready advisory artifacts.",
        f"- SourceOfTruth: `{context_dir}`",
        "",
        "| Artifact | Status | RepoRootMirror | SourceMarkdown |",
        "|---|---|---|---|",
    ]
    for section_key, _, title in REPO_ROOT_CONVENIENCE_SPECS:
        mirror_path = mirrored_files.get(section_key)
        artifact = advisory_artifacts.get(section_key)
        if mirror_path is None or not isinstance(artifact, dict):
            continue
        source_md = artifact.get("md")
        if not isinstance(source_md, Path):
            continue
        lines.append(
            f"| {title} | {artifact.get('status', 'UNKNOWN')} | `{mirror_path.name}` | `{source_md}` |"
        )
    lines.extend(
        [
            "",
            "- These repo-root files are convenience mirrors only; `docs/context` remains canonical.",
            "",
        ]
    )
    return "\n".join(lines)


def _mirror_repo_root_convenience_files(
    *,
    repo_root: Path,
    context_dir: Path,
    advisory_artifacts: dict[str, dict[str, Any] | None],
) -> dict[str, Path]:
    mirrored_files: dict[str, Path] = {}
    for section_key, filename, _ in REPO_ROOT_CONVENIENCE_SPECS:
        artifact = advisory_artifacts.get(section_key)
        if not isinstance(artifact, dict):
            continue
        source_md = artifact.get("md")
        if not isinstance(source_md, Path):
            continue
        try:
            content = source_md.read_text(encoding="utf-8-sig")
            target_path = repo_root / filename
            _atomic_write_text(target_path, content)
        except OSError:
            continue
        mirrored_files[section_key] = target_path

    if not mirrored_files:
        return mirrored_files

    takeover_path = repo_root / REPO_ROOT_TAKEOVER_FILENAME
    try:
        _atomic_write_text(
            takeover_path,
            _render_takeover_latest_markdown(
                context_dir=context_dir,
                mirrored_files=mirrored_files,
                advisory_artifacts=advisory_artifacts,
            ),
        )
    except OSError:
        return mirrored_files

    mirrored_files["takeover"] = takeover_path
    return mirrored_files


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
    generated_at = _utc_now()
    generated_at_utc = _utc_iso(generated_at)
    repo_root = args.repo_root.resolve()
    context_dir = _resolve_path(repo_root=repo_root, candidate=args.context_dir)
    script_dir = (
        _resolve_path(repo_root=repo_root, candidate=args.scripts_dir)
        if args.scripts_dir is not None
        else Path(__file__).resolve().parent
    )

    logs_dir = _resolve_with_default(
        repo_root=repo_root,
        value=args.logs_dir,
        default_path=context_dir / "phase_end_logs",
    )
    weekly_report_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_report_json,
        default_path=context_dir / "auditor_calibration_report.json",
    )
    weekly_report_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_report_md,
        default_path=context_dir / "auditor_calibration_report.md",
    )
    dossier_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.dossier_json,
        default_path=context_dir / "auditor_promotion_dossier.json",
    )
    dossier_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.dossier_md,
        default_path=context_dir / "auditor_promotion_dossier.md",
    )
    go_signal_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.go_signal_md,
        default_path=context_dir / "ceo_go_signal.md",
    )
    weekly_summary_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_summary_md,
        default_path=context_dir / "ceo_weekly_summary_latest.md",
    )
    review_checklist_md = context_dir / "pr_review_checklist_latest.md"
    interface_contract_manifest_json = context_dir / "interface_contract_manifest_latest.json"
    fp_ledger_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.fp_ledger_json,
        default_path=context_dir / "auditor_fp_ledger.json",
    )
    disagreement_ledger_jsonl = _resolve_with_default(
        repo_root=repo_root,
        value=args.disagreement_ledger_jsonl,
        default_path=context_dir / "disagreement_ledger.jsonl",
    )

    output_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.output_json,
        default_path=context_dir / "loop_cycle_summary_latest.json",
    )
    output_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.output_md,
        default_path=context_dir / "loop_cycle_summary_latest.md",
    )
    closure_output_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.closure_output_json,
        default_path=context_dir / "loop_closure_status_latest.json",
    )
    closure_output_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.closure_output_md,
        default_path=context_dir / "loop_closure_status_latest.md",
    )

    phase_end_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.phase_end_script,
        default_path=script_dir / "phase_end_handover.ps1",
    )
    auditor_script = script_dir / "auditor_calibration_report.py"
    go_signal_script = script_dir / "generate_ceo_go_signal.py"
    go_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.go_truth_script,
        default_path=script_dir / "validate_ceo_go_signal_truth.py",
    )
    weekly_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_truth_script,
        default_path=script_dir / "validate_ceo_weekly_summary_truth.py",
    )
    weekly_summary_gen_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_summary_gen_script,
        default_path=script_dir / "generate_ceo_weekly_summary.py",
    )
    round_contract_checks_script = script_dir / "validate_round_contract_checks.py"
    counterexample_script = script_dir / "validate_counterexample_gate.py"
    dual_judge_script = script_dir / "validate_dual_judge_gate.py"
    refactor_mock_policy_script = script_dir / "validate_refactor_mock_policy.py"
    review_checklist_script = script_dir / "validate_review_checklist.py"
    interface_contracts_script = script_dir / "validate_interface_contracts.py"
    parallel_fanin_script = script_dir / "validate_parallel_fanin.py"
    memory_packet_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.memory_packet_script,
        default_path=script_dir / "build_exec_memory_packet.py",
    )
    compaction_trigger_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.compaction_trigger_script,
        default_path=script_dir / "evaluate_context_compaction_trigger.py",
    )
    memory_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.memory_truth_script,
        default_path=script_dir / "validate_exec_memory_truth.py",
    )
    exec_memory_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.exec_memory_json,
        default_path=context_dir / "exec_memory_packet_latest.json",
    )
    exec_memory_md = _resolve_with_default(
        repo_root=repo_root,
        value=args.exec_memory_md,
        default_path=context_dir / "exec_memory_packet_latest.md",
    )
    next_round_handoff_json = context_dir / "next_round_handoff_latest.json"
    next_round_handoff_md = context_dir / "next_round_handoff_latest.md"
    expert_request_json = context_dir / "expert_request_latest.json"
    expert_request_md = context_dir / "expert_request_latest.md"
    pm_ceo_research_brief_json = context_dir / "pm_ceo_research_brief_latest.json"
    pm_ceo_research_brief_md = context_dir / "pm_ceo_research_brief_latest.md"
    board_decision_brief_json = context_dir / "board_decision_brief_latest.json"
    board_decision_brief_md = context_dir / "board_decision_brief_latest.md"
    compaction_state_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.compaction_state_json,
        default_path=context_dir / "context_compaction_state_latest.json",
    )
    compaction_status_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.compaction_status_json,
        default_path=context_dir / "context_compaction_status_latest.json",
    )
    closure_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.closure_script,
        default_path=script_dir / "validate_loop_closure.py",
    )

    context_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    lessons_paths = _write_lessons_stubs(context_dir=context_dir, generated_at_utc=generated_at_utc)

    repo_id = args.repo_id.strip() or repo_root.name or "repo"
    steps: list[dict[str, Any]] = []

    def build_summary_payload(
        *,
        disagreement_sla: dict[str, Any],
        next_round_handoff_artifacts: dict[str, Any] | None = None,
        expert_request_artifacts: dict[str, Any] | None = None,
        pm_ceo_research_brief_artifacts: dict[str, Any] | None = None,
        board_decision_brief_artifacts: dict[str, Any] | None = None,
        repo_root_convenience: dict[str, Path] | None = None,
    ) -> dict[str, Any]:
        status_counts = {
            "pass_count": sum(1 for step in steps if step["status"] == "PASS"),
            "hold_count": sum(1 for step in steps if step["status"] == "HOLD"),
            "fail_count": sum(1 for step in steps if step["status"] == "FAIL"),
            "error_count": sum(1 for step in steps if step["status"] == "ERROR"),
            "skip_count": sum(1 for step in steps if step["status"] == "SKIP"),
            "total_steps": len(steps),
        }

        fail_exit_codes = [
            step["exit_code"]
            for step in steps
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

        repo_root_convenience = repo_root_convenience or {}

        return {
            "schema_version": "1.0.0",
            "generated_at_utc": generated_at_utc,
            "repo_root": str(repo_root),
            "context_dir": str(context_dir),
            "scripts_dir": str(script_dir),
            "skip_phase_end": bool(args.skip_phase_end),
            "allow_hold": bool(args.allow_hold),
            "freshness_hours": args.freshness_hours,
            "step_summary": status_counts,
            "steps": steps,
            "disagreement_ledger_sla": disagreement_sla,
            "lessons": {
                "worker": str(lessons_paths["worker"]),
                "auditor": str(lessons_paths["auditor"]),
            },
            "artifacts": {
                "weekly_report_json": str(weekly_report_json),
                "weekly_report_md": str(weekly_report_md),
                "dossier_json": str(dossier_json),
                "dossier_md": str(dossier_md),
                "go_signal_md": str(go_signal_md),
                "weekly_summary_md": str(weekly_summary_md),
                "review_checklist_md": str(review_checklist_md),
                "interface_contract_manifest_json": str(interface_contract_manifest_json),
                "exec_memory_json": str(exec_memory_json),
                "exec_memory_md": str(exec_memory_md),
                "next_round_handoff_json": str(next_round_handoff_json),
                "next_round_handoff_md": str(next_round_handoff_md),
                "expert_request_json": str(expert_request_json),
                "expert_request_md": str(expert_request_md),
                "pm_ceo_research_brief_json": str(pm_ceo_research_brief_json),
                "pm_ceo_research_brief_md": str(pm_ceo_research_brief_md),
                "board_decision_brief_json": str(board_decision_brief_json),
                "board_decision_brief_md": str(board_decision_brief_md),
                "compaction_state_json": str(compaction_state_json),
                "compaction_status_json": str(compaction_status_json),
                "closure_output_json": str(closure_output_json),
                "closure_output_md": str(closure_output_md),
                "summary_output_json": str(output_json),
                "summary_output_md": str(output_md),
            },
            "next_round_handoff": (
                {
                    "status": next_round_handoff_artifacts["status"],
                    "json": str(next_round_handoff_artifacts["json"]),
                    "md": str(next_round_handoff_artifacts["md"]),
                }
                if next_round_handoff_artifacts is not None
                else None
            ),
            "expert_request": (
                {
                    "status": expert_request_artifacts["status"],
                    "json": str(expert_request_artifacts["json"]),
                    "md": str(expert_request_artifacts["md"]),
                    "target_expert": str(expert_request_artifacts["payload"].get("target_expert", "")).strip(),
                }
                if expert_request_artifacts is not None
                else None
            ),
            "pm_ceo_research_brief": (
                {
                    "status": pm_ceo_research_brief_artifacts["status"],
                    "json": str(pm_ceo_research_brief_artifacts["json"]),
                    "md": str(pm_ceo_research_brief_artifacts["md"]),
                    "delegated_to": str(pm_ceo_research_brief_artifacts["payload"].get("delegated_to", "")).strip(),
                }
                if pm_ceo_research_brief_artifacts is not None
                else None
            ),
            "board_decision_brief": (
                {
                    "status": board_decision_brief_artifacts["status"],
                    "json": str(board_decision_brief_artifacts["json"]),
                    "md": str(board_decision_brief_artifacts["md"]),
                    "decision_topic": str(board_decision_brief_artifacts["payload"].get("decision_topic", "")).strip(),
                    "recommended_option": str(board_decision_brief_artifacts["payload"].get("recommended_option", "")).strip(),
                }
                if board_decision_brief_artifacts is not None
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
            steps.append(
                {
                    "name": step_name,
                    "status": "ERROR",
                    "exit_code": None,
                    "command": [],
                    "started_utc": generated_at_utc,
                    "ended_utc": generated_at_utc,
                    "duration_seconds": 0.0,
                    "stdout": "",
                    "stderr": "",
                    "message": f"Missing script: {script_path}",
                }
            )
            return
        command = [args.python_exe, str(script_path)] + script_args
        steps.append(_run_command(step_name=step_name, command=command, cwd=repo_root))

    if args.skip_phase_end:
        steps.append(_skip_step("phase_end_handover", "Skipped by --skip-phase-end."))
    else:
        if not phase_end_script.exists():
            steps.append(
                {
                    "name": "phase_end_handover",
                    "status": "ERROR",
                    "exit_code": None,
                    "command": [],
                    "started_utc": generated_at_utc,
                    "ended_utc": generated_at_utc,
                    "duration_seconds": 0.0,
                    "stdout": "",
                    "stderr": "",
                    "message": f"Missing phase-end script: {phase_end_script}",
                }
            )
        else:
            phase_end_command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(phase_end_script),
                "-RepoRoot",
                str(repo_root),
                "-AuditMode",
                str(args.phase_end_audit_mode),
            ]
            steps.append(
                _run_command(
                    step_name="phase_end_handover",
                    command=phase_end_command,
                    cwd=repo_root,
                )
            )

    run_python_step(
        step_name="refresh_weekly_calibration",
        script_path=auditor_script,
        script_args=[
            "--logs-dir",
            str(logs_dir),
            "--repo-id",
            repo_id,
            "--ledger",
            str(fp_ledger_json),
            "--output-json",
            str(weekly_report_json),
            "--output-md",
            str(weekly_report_md),
            "--mode",
            "weekly",
        ],
    )
    run_python_step(
        step_name="refresh_dossier",
        script_path=auditor_script,
        script_args=[
            "--logs-dir",
            str(logs_dir),
            "--repo-id",
            repo_id,
            "--ledger",
            str(fp_ledger_json),
            "--output-json",
            str(dossier_json),
            "--output-md",
            str(dossier_md),
            "--mode",
            "dossier",
        ],
    )
    run_python_step(
        step_name="generate_ceo_go_signal",
        script_path=go_signal_script,
        script_args=[
            "--calibration-json",
            str(weekly_report_json),
            "--dossier-json",
            str(dossier_json),
            "--output",
            str(go_signal_md),
        ],
    )
    if weekly_summary_gen_script.exists():
        run_python_step(
            step_name="refresh_ceo_weekly_summary",
            script_path=weekly_summary_gen_script,
            script_args=[
                "--dossier-json",
                str(dossier_json),
                "--calibration-json",
                str(weekly_report_json),
                "--go-signal-md",
                str(go_signal_md),
                "--output",
                str(weekly_summary_md),
            ],
        )
    else:
        steps.append(
            _skip_step(
                "refresh_ceo_weekly_summary",
                f"Script not found: {weekly_summary_gen_script}",
            )
        )

    if compaction_trigger_script.exists():
        run_python_step(
            step_name="evaluate_context_compaction_trigger",
            script_path=compaction_trigger_script,
            script_args=[
                "--memory-json",
                str(exec_memory_json),
                "--dossier-json",
                str(dossier_json),
                "--go-signal-md",
                str(go_signal_md),
                "--state-json",
                str(compaction_state_json),
                "--output-json",
                str(compaction_status_json),
                "--pm-warn",
                str(args.compaction_pm_warn),
                "--ceo-warn",
                str(args.compaction_ceo_warn),
                "--force",
                str(args.compaction_force),
                "--max-age-hours",
                str(args.compaction_max_age_hours),
            ],
        )
    else:
        steps.append(
            _skip_step(
                "evaluate_context_compaction_trigger",
                f"Script not found: {compaction_trigger_script}",
            )
        )

    if memory_packet_script.exists():
        run_python_step(
            step_name="build_exec_memory_packet",
            script_path=memory_packet_script,
            script_args=[
                "--output-json",
                str(exec_memory_json),
                "--output-md",
                str(exec_memory_md),
                "--pm-budget-tokens",
                str(args.pm_budget_tokens),
                "--ceo-budget-tokens",
                str(args.ceo_budget_tokens),
            ],
        )
    else:
        steps.append(
            _skip_step(
                "build_exec_memory_packet",
                f"Script not found: {memory_packet_script}",
            )
        )

    if go_truth_script.exists():
        run_python_step(
            step_name="validate_ceo_go_signal_truth",
            script_path=go_truth_script,
            script_args=[
                "--dossier-json",
                str(dossier_json),
                "--calibration-json",
                str(weekly_report_json),
                "--go-signal-md",
                str(go_signal_md),
            ],
        )
    else:
        steps.append(
            _skip_step(
                "validate_ceo_go_signal_truth",
                f"Script not found: {go_truth_script}",
            )
        )

    if weekly_summary_md.exists() and weekly_truth_script.exists():
        run_python_step(
            step_name="validate_ceo_weekly_summary_truth",
            script_path=weekly_truth_script,
            script_args=[
                "--dossier-json",
                str(dossier_json),
                "--calibration-json",
                str(weekly_report_json),
                "--weekly-md",
                str(weekly_summary_md),
            ],
        )
    elif not weekly_summary_md.exists():
        steps.append(
            _skip_step(
                "validate_ceo_weekly_summary_truth",
                f"Weekly summary not found: {weekly_summary_md}",
            )
        )
    else:
        steps.append(
            _skip_step(
                "validate_ceo_weekly_summary_truth",
                f"Script not found: {weekly_truth_script}",
            )
        )

    if exec_memory_json.exists() and memory_truth_script.exists():
        run_python_step(
            step_name="validate_exec_memory_truth",
            script_path=memory_truth_script,
            script_args=[
                "--memory-json",
                str(exec_memory_json),
                "--repo-root",
                str(repo_root),
            ],
        )
    elif not exec_memory_json.exists():
        steps.append(
            _skip_step(
                "validate_exec_memory_truth",
                f"Exec memory packet not found: {exec_memory_json}",
            )
        )
    else:
        steps.append(
            _skip_step(
                "validate_exec_memory_truth",
                f"Script not found: {memory_truth_script}",
            )
        )

    run_python_step(
        step_name="validate_counterexample_gate",
        script_path=counterexample_script,
        script_args=[
            "--round-contract-md",
            str(context_dir / "round_contract_latest.md"),
        ],
    )

    run_python_step(
        step_name="validate_dual_judge_gate",
        script_path=dual_judge_script,
        script_args=[
            "--round-contract-md",
            str(context_dir / "round_contract_latest.md"),
        ],
    )

    run_python_step(
        step_name="validate_refactor_mock_policy",
        script_path=refactor_mock_policy_script,
        script_args=[
            "--round-contract-md",
            str(context_dir / "round_contract_latest.md"),
        ],
    )

    if review_checklist_md.exists():
        run_python_step(
            step_name="validate_review_checklist",
            script_path=review_checklist_script,
            script_args=[
                "--input",
                str(review_checklist_md),
            ],
        )
    else:
        steps.append(
            _skip_step(
                "validate_review_checklist",
                f"Review checklist not found: {review_checklist_md}",
            )
        )

    if interface_contract_manifest_json.exists():
        run_python_step(
            step_name="validate_interface_contracts",
            script_path=interface_contracts_script,
            script_args=[
                "--manifest-json",
                str(interface_contract_manifest_json),
            ],
        )
    else:
        steps.append(
            _skip_step(
                "validate_interface_contracts",
                f"Interface contract manifest not found: {interface_contract_manifest_json}",
            )
        )

    run_python_step(
        step_name="validate_parallel_fanin",
        script_path=parallel_fanin_script,
        script_args=[
            "--context-dir",
            str(context_dir),
        ],
    )

    run_python_step(
        step_name="validate_loop_closure",
        script_path=closure_script,
        script_args=[
            "--repo-root",
            str(repo_root),
            "--context-dir",
            str(context_dir),
            "--dossier-json",
            str(dossier_json),
            "--calibration-json",
            str(weekly_report_json),
            "--go-signal-md",
            str(go_signal_md),
            "--weekly-summary-md",
            str(weekly_summary_md),
            "--go-truth-script",
            str(go_truth_script),
            "--weekly-truth-script",
            str(weekly_truth_script),
            "--memory-json",
            str(exec_memory_json),
            "--memory-truth-script",
            str(memory_truth_script),
            "--refactor-mock-policy-script",
            str(refactor_mock_policy_script),
            "--review-checklist-script",
            str(review_checklist_script),
            "--interface-contracts-script",
            str(interface_contracts_script),
            "--freshness-hours",
            str(args.freshness_hours),
            "--output-json",
            str(closure_output_json),
            "--output-md",
            str(closure_output_md),
        ],
    )

    temp_summary_path = context_dir / "loop_cycle_summary_current.json"
    temp_summary_dict = build_summary_payload(
        disagreement_sla=_scan_disagreement_sla(path=disagreement_ledger_jsonl, now_utc=_utc_now())
    )
    try:
        _atomic_write_text(temp_summary_path, json.dumps(temp_summary_dict, indent=2))
    except OSError as exc:
        steps.append(
            {
                "name": "write_temp_summary",
                "status": "ERROR",
                "exit_code": None,
                "command": [],
                "started_utc": generated_at_utc,
                "ended_utc": generated_at_utc,
                "duration_seconds": 0.0,
                "stdout": "",
                "stderr": str(exc),
                "message": f"Failed to write temp summary: {exc}",
            }
        )

    run_python_step(
        step_name="validate_round_contract_checks",
        script_path=round_contract_checks_script,
        script_args=[
            "--round-contract-md",
            str(context_dir / "round_contract_latest.md"),
            "--loop-summary-json",
            str(temp_summary_path),
            "--closure-json",
            str(closure_output_json),
        ],
    )

    if temp_summary_path.exists():
        try:
            temp_summary_path.unlink()
        except OSError:
            pass

    _apply_hold_semantics(
        steps=steps,
        allow_hold=bool(args.allow_hold),
        closure_output_json=closure_output_json,
    )

    next_round_handoff_artifacts = _persist_next_round_handoff(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
    )
    expert_request_artifacts = _persist_expert_request(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
    )
    pm_ceo_research_brief_artifacts = _persist_pm_ceo_research_brief(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
    )
    board_decision_brief_artifacts = _persist_board_decision_brief(
        context_dir=context_dir,
        exec_memory_json=exec_memory_json,
    )
    repo_root_convenience = _mirror_repo_root_convenience_files(
        repo_root=repo_root,
        context_dir=context_dir,
        advisory_artifacts={
            "next_round_handoff": next_round_handoff_artifacts,
            "expert_request": expert_request_artifacts,
            "pm_ceo_research_brief": pm_ceo_research_brief_artifacts,
            "board_decision_brief": board_decision_brief_artifacts,
        },
    )

    disagreement_sla = _scan_disagreement_sla(path=disagreement_ledger_jsonl, now_utc=_utc_now())

    payload = build_summary_payload(
        disagreement_sla=disagreement_sla,
        next_round_handoff_artifacts=next_round_handoff_artifacts,
        expert_request_artifacts=expert_request_artifacts,
        pm_ceo_research_brief_artifacts=pm_ceo_research_brief_artifacts,
        board_decision_brief_artifacts=board_decision_brief_artifacts,
        repo_root_convenience=repo_root_convenience,
    )
    final_result = str(payload["final_result"])
    final_exit_code = int(payload["final_exit_code"])

    md_lines: list[str] = [
        "# Loop Cycle Summary",
        "",
        f"- GeneratedAtUTC: {generated_at_utc}",
        f"- FinalResult: {final_result}",
        f"- FinalExitCode: {final_exit_code}",
        f"- SkipPhaseEnd: {bool(args.skip_phase_end)}",
        "",
        "| Step | Status | Exit | Message |",
        "|---|---|---:|---|",
    ]
    for step in steps:
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
            f"- Worker: {lessons_paths['worker']}",
            f"- Auditor: {lessons_paths['auditor']}",
            "",
        ]
    )
    if next_round_handoff_artifacts is not None:
        md_lines.extend(
            [
                "## Next Round Handoff",
                "",
                f"- Status: {next_round_handoff_artifacts['status']}",
                f"- JSON: {next_round_handoff_artifacts['json']}",
                f"- Markdown: {next_round_handoff_artifacts['md']}",
                "",
            ]
        )
    if expert_request_artifacts is not None:
        md_lines.extend(
            [
                "## Expert Request",
                "",
                f"- Status: {expert_request_artifacts['status']}",
                f"- TargetExpert: {expert_request_artifacts['payload'].get('target_expert', '')}",
                f"- JSON: {expert_request_artifacts['json']}",
                f"- Markdown: {expert_request_artifacts['md']}",
                "",
            ]
        )
    if pm_ceo_research_brief_artifacts is not None:
        md_lines.extend(
            [
                "## PM/CEO Research Brief",
                "",
                f"- Status: {pm_ceo_research_brief_artifacts['status']}",
                f"- DelegatedTo: {pm_ceo_research_brief_artifacts['payload'].get('delegated_to', '')}",
                f"- JSON: {pm_ceo_research_brief_artifacts['json']}",
                f"- Markdown: {pm_ceo_research_brief_artifacts['md']}",
                "",
            ]
        )
    if board_decision_brief_artifacts is not None:
        md_lines.extend(
            [
                "## Board Decision Brief",
                "",
                f"- Status: {board_decision_brief_artifacts['status']}",
                f"- DecisionTopic: {board_decision_brief_artifacts['payload'].get('decision_topic', '')}",
                f"- RecommendedOption: {board_decision_brief_artifacts['payload'].get('recommended_option', '')}",
                f"- JSON: {board_decision_brief_artifacts['json']}",
                f"- Markdown: {board_decision_brief_artifacts['md']}",
                "",
            ]
        )
    if repo_root_convenience:
        md_lines.extend(
            [
                "## Repo-Root Convenience Files",
                "",
                f"- SourceOfTruth: {context_dir}",
            ]
        )
        for section_key, _, title in REPO_ROOT_CONVENIENCE_SPECS:
            mirror_path = repo_root_convenience.get(section_key)
            if mirror_path is None:
                continue
            md_lines.append(f"- {title}: {mirror_path}")
        takeover_path = repo_root_convenience.get("takeover")
        if takeover_path is not None:
            md_lines.append(f"- Takeover Index: {takeover_path}")
        md_lines.append("")
    markdown = "\n".join(md_lines)

    try:
        _atomic_write_text(output_json, json.dumps(payload, indent=2) + "\n")
        _atomic_write_text(output_md, markdown)
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
