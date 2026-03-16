from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT_CONVENIENCE_SPECS: tuple[tuple[str, str, str], ...] = (
    ("next_round_handoff", "NEXT_ROUND_HANDOFF_LATEST.md", "Next Round Handoff"),
    ("expert_request", "EXPERT_REQUEST_LATEST.md", "Expert Request"),
    ("pm_ceo_research_brief", "PM_CEO_RESEARCH_BRIEF_LATEST.md", "PM/CEO Research Brief"),
    ("board_decision_brief", "BOARD_DECISION_BRIEF_LATEST.md", "Board Decision Brief"),
)
REPO_ROOT_TAKEOVER_FILENAME = "TAKEOVER_LATEST.md"
APPROVED_CONTEXT_ARTIFACT_FILENAMES = frozenset(
    {
        "next_round_handoff_latest.json",
        "next_round_handoff_latest.md",
        "expert_request_latest.json",
        "expert_request_latest.md",
        "pm_ceo_research_brief_latest.json",
        "pm_ceo_research_brief_latest.md",
        "board_decision_brief_latest.json",
        "board_decision_brief_latest.md",
        "skill_activation_latest.json",
    }
)
APPROVED_REPO_ROOT_CONVENIENCE_FILENAMES = frozenset(
    {filename for _, filename, _ in REPO_ROOT_CONVENIENCE_SPECS} | {REPO_ROOT_TAKEOVER_FILENAME}
)


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


def _approved_context_output_path(context_dir: Path, filename: str) -> Path:
    if filename not in APPROVED_CONTEXT_ARTIFACT_FILENAMES:
        raise ValueError(f"Unapproved context artifact filename: {filename}")
    output_path = context_dir / filename
    if output_path.parent != context_dir:
        raise ValueError(f"Context artifact must be written directly under {context_dir}: {output_path}")
    return output_path


def _approved_repo_root_output_path(repo_root: Path, filename: str) -> Path:
    if filename not in APPROVED_REPO_ROOT_CONVENIENCE_FILENAMES:
        raise ValueError(f"Unapproved repo-root convenience filename: {filename}")
    output_path = repo_root / filename
    if output_path.parent != repo_root:
        raise ValueError(f"Repo-root convenience artifact must be written directly under {repo_root}: {output_path}")
    return output_path


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
    return str(value).strip()


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

    output_json = _approved_context_output_path(context_dir, f"{output_prefix}_latest.json")
    output_md = _approved_context_output_path(context_dir, f"{output_prefix}_latest.md")
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


def _persist_skill_activation(
    *,
    context_dir: Path,
    exec_memory_json: Path,
) -> dict[str, Any] | None:
    """Persist skill_activation section as standalone JSON artifact."""
    if not exec_memory_json.exists():
        return None

    try:
        memory_payload = json.loads(exec_memory_json.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None

    skill_activation = memory_payload.get("skill_activation")
    if not isinstance(skill_activation, dict) or not skill_activation:
        return None

    output_json = _approved_context_output_path(context_dir, "skill_activation_latest.json")
    artifact_payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": str(memory_payload.get("generated_at_utc", "")).strip(),
        "source_exec_memory_json": str(exec_memory_json),
        "skill_activation": skill_activation,
    }
    _atomic_write_text(output_json, json.dumps(artifact_payload, indent=2) + "\n")
    return {
        "json": output_json,
        "status": str(skill_activation.get("status", "")).strip() or "UNKNOWN",
        "payload": skill_activation,
    }


def persist_advisory_sections(
    context_dir: Path, exec_memory_json: Path
) -> dict[str, dict[str, Any] | None]:
    return {
        "next_round_handoff": _persist_next_round_handoff(
            context_dir=context_dir,
            exec_memory_json=exec_memory_json,
        ),
        "expert_request": _persist_expert_request(
            context_dir=context_dir,
            exec_memory_json=exec_memory_json,
        ),
        "pm_ceo_research_brief": _persist_pm_ceo_research_brief(
            context_dir=context_dir,
            exec_memory_json=exec_memory_json,
        ),
        "board_decision_brief": _persist_board_decision_brief(
            context_dir=context_dir,
            exec_memory_json=exec_memory_json,
        ),
        "skill_activation": _persist_skill_activation(
            context_dir=context_dir,
            exec_memory_json=exec_memory_json,
        ),
    }


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
            target_path = _approved_repo_root_output_path(repo_root, filename)
            _atomic_write_text(target_path, content)
        except OSError:
            continue
        mirrored_files[section_key] = target_path

    if not mirrored_files:
        return mirrored_files

    takeover_path = _approved_repo_root_output_path(repo_root, REPO_ROOT_TAKEOVER_FILENAME)
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


def mirror_repo_root_convenience(
    repo_root: Path,
    context_dir: Path,
    advisory_artifacts: dict[str, dict[str, Any] | None],
) -> dict[str, Path]:
    return _mirror_repo_root_convenience_files(
        repo_root=repo_root,
        context_dir=context_dir,
        advisory_artifacts=advisory_artifacts,
    )
