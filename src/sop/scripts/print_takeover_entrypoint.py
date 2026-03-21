from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    from sop.scripts.utils.path_validator import validate_artifact_path
except ModuleNotFoundError:
    # Fallback for direct script execution (development mode)
    from scripts.utils.path_validator import validate_artifact_path
            if ".." in path_parts:
                return False, f"Parent directory escape (..) not allowed: {path}"
            if path_parts[0] == repo_root.resolve().name:
                return False, (
                    f"Path must not start with repo root name '{repo_root.resolve().name}'"
                )
            try:
                artifact_path = (repo_root / path).resolve()
                artifact_path.relative_to(repo_root.resolve())
            except ValueError:
                return False, f"Path escapes repository root: {path}"
            except Exception as exc:  # pragma: no cover - defensive fallback
                return False, f"Path resolution error: {path} ({exc})"
            return True, ""

from print_takeover_workflow_overlay_models import (
    ArtifactInput,
    WorkflowNode,
    WorkflowOverlayMetadata,
    WorkflowStatusOverlay,
    WorkflowStatusOverlayPayload,
    coerce_workflow_overlay_payload_dict,
    render_workflow_overlay_payload,
)


NEXT_ROUND_HANDOFF_PATH = "docs/context/next_round_handoff_latest.md"
EXPERT_REQUEST_PATH = "docs/context/expert_request_latest.md"
PM_CEO_RESEARCH_BRIEF_PATH = "docs/context/pm_ceo_research_brief_latest.md"
BOARD_DECISION_BRIEF_PATH = "docs/context/board_decision_brief_latest.md"
APPROVED_WORKFLOW_STATUS_JSON = Path("docs/context/workflow_status_latest.json")
APPROVED_WORKFLOW_STATUS_MD = Path("docs/context/workflow_status_latest.md")

ROOT_CONVENIENCE_MIRRORS = [
    "NEXT_ROUND_HANDOFF_LATEST.md",
    "EXPERT_REQUEST_LATEST.md",
    "PM_CEO_RESEARCH_BRIEF_LATEST.md",
    "BOARD_DECISION_BRIEF_LATEST.md",
]

ARTIFACT_PATHS = [
    "docs/context/ceo_weekly_summary_latest.md",
    "docs/context/ceo_go_signal.md",
    "docs/context/exec_memory_packet_latest.json",
    "docs/context/loop_cycle_summary_latest.json",
    "docs/context/loop_closure_status_latest.json",
    EXPERT_REQUEST_PATH,
    PM_CEO_RESEARCH_BRIEF_PATH,
    BOARD_DECISION_BRIEF_PATH,
]

ADVISORY_HANDOFFS: list[tuple[str, str]] = [
    ("advisory_next_round_handoff", NEXT_ROUND_HANDOFF_PATH),
    ("advisory_expert_request", EXPERT_REQUEST_PATH),
    ("advisory_pm_ceo_research_brief", PM_CEO_RESEARCH_BRIEF_PATH),
    ("advisory_board_decision_brief", BOARD_DECISION_BRIEF_PATH),
]

STATUS_EMOJI = {
    "green": "🟢",
    "yellow": "🟡",
    "blue": "🔵",
    "gray": "⚪",  # White circle emoji - visible neutral marker
    "red": "🔴",
}

MACHINE_VIEW_MARKERS: dict[str, tuple[str, ...]] = {
    "advisory_expert_request": (
        "REQUESTED_DOMAIN",
        "ROSTER_FIT",
        "MILESTONE_ID",
        "BOARD_REENTRY_REQUIRED",
        "BOARD_REENTRY_REASON_CODES",
        "EXPERT_MEMORY_STATUS",
        "BOARD_MEMORY_STATUS",
        "MEMORY_REASON_CODES",
    ),
    "advisory_board_decision_brief": (
        "LINEUP_DECISION_NEEDED",
        "LINEUP_GAP_DOMAINS",
        "APPROVED_ROSTER_SNAPSHOT",
        "REINTRODUCE_BOARD_WHEN",
        "BOARD_REENTRY_REQUIRED",
        "BOARD_REENTRY_REASON_CODES",
        "EXPERT_MEMORY_STATUS",
        "BOARD_MEMORY_STATUS",
        "MEMORY_REASON_CODES",
    ),
}

def _atomic_write_text(path: Path, content: str) -> None:
    """Atomically write text content to a file using temp file + rename."""
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


def _resolve_approved_overlay_output(
    *,
    repo_root: Path,
    candidate: Path,
    expected_relative: Path,
) -> Path:
    expected_path = (repo_root / expected_relative).resolve()
    if candidate.is_absolute():
        resolved_path = candidate.resolve()
        try:
            resolved_path.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError(
                f"Workflow status overlay must stay under repo root: {candidate}"
            ) from exc
    else:
        is_valid, error = validate_artifact_path(candidate.as_posix(), repo_root)
        if not is_valid:
            raise ValueError(error)
        resolved_path = (repo_root / candidate).resolve()

    if resolved_path != expected_path:
        raise ValueError(
            f"Workflow status overlay path must be '{expected_relative.as_posix()}' "
            f"(got '{candidate.as_posix()}')."
        )
    return resolved_path


SECTION_MARKER_FALLBACKS: dict[str, dict[str, dict[str, str]]] = {
    "advisory_expert_request": {
        "## Lineup": {
            "RequestedDomain": "REQUESTED_DOMAIN",
            "RosterFit": "ROSTER_FIT",
            "MilestoneId": "MILESTONE_ID",
            "BoardReentryRequired": "BOARD_REENTRY_REQUIRED",
            "BoardReentryReasonCodes": "BOARD_REENTRY_REASON_CODES",
        },
        "## Memory": {
            "ExpertMemoryStatus": "EXPERT_MEMORY_STATUS",
            "BoardMemoryStatus": "BOARD_MEMORY_STATUS",
            "MemoryReasonCodes": "MEMORY_REASON_CODES",
        },
    },
    "advisory_board_decision_brief": {
        "## Lineup": {
            "LineupDecisionNeeded": "LINEUP_DECISION_NEEDED",
            "LineupGapDomains": "LINEUP_GAP_DOMAINS",
            "ApprovedRosterSnapshot": "APPROVED_ROSTER_SNAPSHOT",
            "ReintroduceBoardWhen": "REINTRODUCE_BOARD_WHEN",
            "BoardReentryRequired": "BOARD_REENTRY_REQUIRED",
            "BoardReentryReasonCodes": "BOARD_REENTRY_REASON_CODES",
        },
        "## Memory": {
            "ExpertMemoryStatus": "EXPERT_MEMORY_STATUS",
            "BoardMemoryStatus": "BOARD_MEMORY_STATUS",
            "MemoryReasonCodes": "MEMORY_REASON_CODES",
        },
    },
}


def _load_closure_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing closure status file: {path}")
    raw = path.read_text(encoding="utf-8-sig")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Closure status JSON root must be an object.")
    return payload


def _extract_startup_gate_status(payload: dict[str, Any]) -> str | None:
    checks = payload.get("checks")
    if not isinstance(checks, list):
        return None
    for check in checks:
        if not isinstance(check, dict):
            continue
        if check.get("name") != "startup_gate_status":
            continue
        status = check.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip()
        return None
    return None


def _result_to_exit_code(result: str) -> int:
    normalized = result.strip().upper()
    if normalized == "READY_TO_ESCALATE":
        return 0
    if normalized == "NOT_READY":
        return 1
    return 2


def _load_optional_handoff(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8-sig")
    stripped = raw.strip()
    if not stripped:
        return None
    return stripped


def _extract_markdown_section(markdown: str, heading: str) -> str | None:
    lines = markdown.splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            collecting = True
            continue
        if collecting and stripped.startswith("#"):
            break
        if collecting:
            collected.append(line)
    section = "\n".join(collected).strip()
    return section or None


def _extract_fenced_block(markdown: str, *headings: str) -> str | None:
    section: str | None = None
    for heading in headings:
        section = _extract_markdown_section(markdown, heading)
        if section is not None:
            break
    if section is None:
        return None

    lines = section.splitlines()
    in_fence = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```"):
                in_fence = True
            continue
        if stripped == "```":
            break
        collected.append(line)

    fenced_block = "\n".join(collected).strip()
    return fenced_block or None


def _extract_paste_ready_block(markdown: str) -> str | None:
    return _extract_fenced_block(markdown, "### Paste-Ready Block", "## Paste-Ready Block")


def _extract_machine_view_block(markdown: str) -> str | None:
    return _extract_fenced_block(markdown, "### Machine View", "## Machine View")


def _extract_human_brief(markdown: str) -> str | None:
    section = _extract_markdown_section(markdown, "### Human Brief")
    if section is None:
        section = _extract_markdown_section(markdown, "## Human Brief")
    if section is None:
        return None
    return " ".join(section.split()) or None


def _normalize_marker_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _extract_section_markers(markdown: str, heading: str, key_map: dict[str, str]) -> dict[str, str]:
    section = _extract_markdown_section(markdown, heading)
    if section is None:
        return {}

    normalized_key_map = {
        _normalize_marker_key(source_key): marker_name
        for source_key, marker_name in key_map.items()
    }
    markers: dict[str, str] = {}
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        item = stripped[1:].strip()
        key, separator, value = item.partition(":")
        if not separator:
            continue
        marker_name = normalized_key_map.get(_normalize_marker_key(key))
        marker_value = value.strip()
        if marker_name and marker_value:
            markers[marker_name] = marker_value
    return markers


def _extract_machine_view_markers(markdown: str, label: str) -> dict[str, str]:
    machine_view = _extract_machine_view_block(markdown)
    markers: dict[str, str] = {}
    if machine_view is not None:
        for line in machine_view.splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                continue
            normalized_key = key.strip().upper()
            normalized_value = value.strip()
            if normalized_key and normalized_value:
                markers[normalized_key] = normalized_value

    for heading, key_map in SECTION_MARKER_FALLBACKS.get(label, {}).items():
        fallback_markers = _extract_section_markers(markdown, heading, key_map)
        for marker_name, marker_value in fallback_markers.items():
            markers.setdefault(marker_name, marker_value)
    return markers


def _load_json_object(path: Path) -> dict[str, Any]:
    """Load JSON object from file, raise if not a dict."""
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    raw = path.read_text(encoding="utf-8-sig")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    """Safely load JSON, return None if missing or invalid."""
    try:
        return _load_json_object(path)
    except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError):
        return None


def _parse_markdown_key_values(raw: str) -> dict[str, str]:
    """Parse markdown key-value pairs (e.g., '- KEY: value')."""
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        item = stripped[1:].strip()
        key, separator, value = item.partition(":")
        if not separator:
            continue
        normalized_key = key.strip().upper()
        normalized_value = value.strip()
        if normalized_key and normalized_value:
            fields[normalized_key] = normalized_value
    return fields


def _derive_startup_node(repo_root: Path) -> WorkflowNode:
    """Derive startup node from startup_intake_latest.json."""
    intake_path = repo_root / "docs" / "context" / "startup_intake_latest.json"
    intake = _load_optional_json(intake_path)

    status_color = "gray"
    status_label = "NOT_STARTED"
    blockers: list[str] = []
    startup_status = "UNKNOWN"

    if intake is not None:
        startup_gate = intake.get("startup_gate", {})
        gate_status = startup_gate.get("status", "").strip().upper()
        startup_status = gate_status

        if gate_status == "READY_TO_EXECUTE":
            status_color = "green"
            status_label = "READY"
        elif gate_status:
            status_color = "yellow"
            status_label = "BLOCKED"
            blockers.append(f"Startup gate blocked: {gate_status}")

    return WorkflowNode(
        node_id="Startup",
        title="Startup Intake",
        status_color=status_color,
        progress_state=status_label,
        owner_role="PM",
        blockers=blockers,
        source_of_truth=str(intake_path.relative_to(repo_root)),
        updated_at_utc=intake.get("generated_at_utc") if intake else None,
        advisory_roles=["Worker", "Auditor"],
        complexity_band="LOW",
        rigor_mode="STANDARD",
        capability_band="agent_plus_review",
        supporting_artifacts=["docs/context/init_execution_card_latest.md"],
        key_signals=[f"startup_gate.status={startup_status}"],
        next_action="Proceed to execution" if startup_status == "READY_TO_EXECUTE" else "Fix startup blockers",
    )


def _derive_execution_node(repo_root: Path) -> WorkflowNode:
    """Derive execution node from loop_cycle_summary_latest.json."""
    cycle_path = repo_root / "docs" / "context" / "loop_cycle_summary_latest.json"
    cycle = _load_optional_json(cycle_path)

    status_color = "gray"
    status_label = "NOT_STARTED"
    blockers: list[str] = []
    final_result = "UNKNOWN"

    if cycle is not None:
        final_result = cycle.get("final_result", "").strip().upper()

        if final_result == "PASS":
            status_color = "green"
            status_label = "READY"
        elif final_result == "HOLD":
            status_color = "yellow"
            status_label = "BLOCKED"
            blockers.append("Execution on hold")
        elif final_result in ("FAIL", "ERROR"):
            status_color = "red"
            status_label = "BLOCKED"
            blockers.append(f"Execution {final_result.lower()}")

    return WorkflowNode(
        node_id="Execution",
        title="Loop Execution",
        status_color=status_color,
        progress_state=status_label,
        owner_role="Worker",
        blockers=blockers,
        source_of_truth=str(cycle_path.relative_to(repo_root)),
        updated_at_utc=cycle.get("generated_at_utc") if cycle else None,
        advisory_roles=["PM", "QA"],
        complexity_band="HIGH",
        rigor_mode="STANDARD",
        capability_band="agent_ok",
        supporting_artifacts=["docs/context/round_contract_latest.md"],
        key_signals=[f"final_result={final_result}"],
        next_action="Proceed to validation" if final_result == "PASS" else "Review execution issues",
    )


def _derive_validation_closure_node(repo_root: Path) -> WorkflowNode:
    """Derive validation/closure node from loop_closure_status_latest.json."""
    closure_path = repo_root / "docs" / "context" / "loop_closure_status_latest.json"
    closure = _load_optional_json(closure_path)

    status_color = "gray"
    status_label = "NOT_STARTED"
    blockers: list[str] = []
    result = "UNKNOWN"

    if closure is not None:
        result = closure.get("result", "").strip().upper()

        if result == "READY_TO_ESCALATE":
            status_color = "green"
            status_label = "READY"
        elif result == "NOT_READY":
            status_color = "yellow"
            status_label = "BLOCKED"
            # Extract blockers from failed checks
            checks = closure.get("checks", [])
            for check in checks:
                if isinstance(check, dict) and check.get("status") == "FAIL":
                    check_name = check.get("name", "unknown")
                    blockers.append(f"Check failed: {check_name}")
        elif result in ("INPUT_OR_INFRA_ERROR", "ERROR"):
            status_color = "red"
            status_label = "BLOCKED"
            blockers.append("Input or infrastructure error")

    return WorkflowNode(
        node_id="ValidationClosure",
        title="Validation & Closure",
        status_color=status_color,
        progress_state=status_label,
        owner_role="Auditor",
        blockers=blockers,
        source_of_truth=str(closure_path.relative_to(repo_root)),
        updated_at_utc=closure.get("generated_at_utc") if closure else None,
        advisory_roles=["PM", "CEO"],
        complexity_band="MEDIUM",
        rigor_mode="HIGH_RIGOR",
        capability_band="agent_plus_review",
        supporting_artifacts=["docs/context/loop_cycle_summary_latest.json"],
        key_signals=[f"closure_result={result}"],
        next_action="Escalate to PM/CEO" if result == "READY_TO_ESCALATE" else "Fix validation issues",
    )


def _derive_round_contract_node(repo_root: Path) -> WorkflowNode:
    """Derive RoundContract node status from round contract artifact."""
    contract_path = repo_root / "docs" / "context" / "round_contract_latest.md"

    if not contract_path.exists():
        return WorkflowNode(
            node_id="RoundContract",
            title="Round Contract",
            status_color="gray",
            progress_state="NOT_STARTED",
            owner_role="Worker",
            advisory_roles=["Auditor", "PM"],
            complexity_band="MEDIUM",
            rigor_mode="STANDARD",
            capability_band="agent_ok",
            blockers=["Round contract not found"],
            source_of_truth="docs/context/round_contract_latest.md",
            supporting_artifacts=[],
            key_signals=[],
            next_action="Create round contract",
            updated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    # Parse contract fields
    try:
        content = contract_path.read_text(encoding="utf-8-sig")
        fields = _parse_markdown_key_values(content)

        # Check required fields
        required_fields = [
            "DECISION_CLASS", "RISK_TIER", "TDD_MODE",
            "DONE_WHEN_CHECKS", "EXECUTION_LANE", "INTUITION_GATE"
        ]
        missing_fields = [f for f in required_fields if not fields.get(f)]

        # Check fail-closed triggers
        fail_closed_blockers = []

        # Parse relevant fields for validation
        decision_class = fields.get("DECISION_CLASS", "").strip().upper()
        risk_tier = fields.get("RISK_TIER", "").strip().upper()
        workflow_lane = fields.get("WORKFLOW_LANE", "").strip().upper()
        intuition_gate = fields.get("INTUITION_GATE", "").strip().upper()

        qa_required = fields.get("QA_PRE_ESCALATION_REQUIRED", "").strip().upper()
        qa_verdict = fields.get("QA_VERDICT", "").strip().upper()
        qa_exception = fields.get("QA_EXCEPTION_APPROVED", "").strip().upper()
        qa_exception_rationale = fields.get("QA_EXCEPTION_RATIONALE", "").strip()

        socratic_required = fields.get("SOCRATIC_CHALLENGE_REQUIRED", "").strip().upper()
        socratic_resolved = fields.get("SOCRATIC_CHALLENGE_RESOLVED", "").strip().upper()
        socratic_exception = fields.get("SOCRATIC_EXCEPTION_APPROVED", "").strip().upper()
        socratic_exception_rationale = fields.get("SOCRATIC_EXCEPTION_RATIONALE", "").strip()

        # Determine if QA/Socratic are required based on triggers
        qa_socratic_required = (
            risk_tier == "HIGH" or
            decision_class == "ONE_WAY" or
            workflow_lane == "HIGH_RISK"
        )

        # Validate QA requirements
        if qa_socratic_required or qa_required == "YES":
            qa_exception_valid = (
                qa_exception == "YES" and
                qa_exception_rationale and
                qa_exception_rationale not in ("N/A", "TBD", "TODO")
            )
            if not qa_exception_valid:
                if qa_required != "YES":
                    fail_closed_blockers.append("QA_PRE_ESCALATION_REQUIRED=YES required by risk triggers")
                elif qa_verdict != "PASS":
                    fail_closed_blockers.append("QA_PRE_ESCALATION_REQUIRED=YES but QA_VERDICT not PASS")

        # Validate Socratic requirements
        if qa_socratic_required or socratic_required == "YES":
            socratic_exception_valid = (
                socratic_exception == "YES" and
                socratic_exception_rationale and
                socratic_exception_rationale not in ("N/A", "TBD", "TODO")
            )
            if not socratic_exception_valid:
                if socratic_required != "YES":
                    fail_closed_blockers.append("SOCRATIC_CHALLENGE_REQUIRED=YES required by risk triggers")
                elif socratic_resolved != "YES":
                    fail_closed_blockers.append("SOCRATIC_CHALLENGE_REQUIRED=YES but not resolved")

        # Validate WORKFLOW_LANE=MILESTONE_REVIEW requirements
        if workflow_lane == "MILESTONE_REVIEW":
            if intuition_gate != "HUMAN_REQUIRED":
                fail_closed_blockers.append("WORKFLOW_LANE=MILESTONE_REVIEW requires INTUITION_GATE=HUMAN_REQUIRED")

        # Combine all blockers
        all_blockers = []
        if missing_fields:
            all_blockers.extend([f"Missing required field: {f}" for f in missing_fields])
        all_blockers.extend(fail_closed_blockers)

        # Determine status
        if all_blockers:
            status_color = "red"
            status_label = "BLOCKED"
            blockers = all_blockers
        else:
            status_color = "green"
            status_label = "READY"
            blockers = []

        mtime = contract_path.stat().st_mtime
        updated_utc = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        key_signals = [f"{k}={v}" for k, v in fields.items() if k in required_fields]

        return WorkflowNode(
            node_id="RoundContract",
            title="Round Contract",
            status_color=status_color,
            progress_state=status_label,
            owner_role="Worker",
            advisory_roles=["Auditor", "PM"],
            complexity_band="MEDIUM",
            rigor_mode="STANDARD",
            capability_band="agent_ok",
            blockers=blockers,
            source_of_truth="docs/context/round_contract_latest.md",
            supporting_artifacts=["docs/round_contract_template.md"],
            key_signals=key_signals,
            next_action="Fix missing fields" if blockers else "Proceed with execution",
            updated_at_utc=updated_utc,
        )
    except Exception as exc:
        return WorkflowNode(
            node_id="RoundContract",
            title="Round Contract",
            status_color="red",
            progress_state="ERROR",
            owner_role="Worker",
            advisory_roles=["Auditor", "PM"],
            complexity_band="MEDIUM",
            rigor_mode="STANDARD",
            capability_band="agent_ok",
            blockers=[f"Failed to parse contract: {exc}"],
            source_of_truth="docs/context/round_contract_latest.md",
            supporting_artifacts=[],
            key_signals=[],
            next_action="Fix contract parsing error",
            updated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )


def _derive_memory_artifacts_node(repo_root: Path) -> WorkflowNode:
    """Derive MemoryArtifacts node status from memory and advisory artifacts."""
    context_dir = repo_root / "docs" / "context"

    # Check all memory artifacts
    artifacts_to_check = [
        "exec_memory_packet_latest.json",
        "next_round_handoff_latest.json",
        "expert_request_latest.json",
        "pm_ceo_research_brief_latest.json",
        "board_decision_brief_latest.json"
    ]

    present = []
    missing = []
    stale = []

    for artifact_name in artifacts_to_check:
        artifact_path = context_dir / artifact_name
        if artifact_path.exists():
            present.append(artifact_name)
            # Check freshness (48 hours)
            mtime = artifact_path.stat().st_mtime
            age_hours = (datetime.now(timezone.utc).timestamp() - mtime) / 3600
            if age_hours > 48:
                stale.append(artifact_name)
        else:
            missing.append(artifact_name)

    # Determine status
    if not present:
        status_color = "gray"
        status_label = "NOT_STARTED"
        blockers = ["No memory artifacts found"]
    elif missing or stale:
        status_color = "yellow"
        status_label = "BLOCKED"
        blockers = []
        if missing:
            blockers.append(f"Missing: {', '.join(missing)}")
        if stale:
            blockers.append(f"Stale (>48h): {', '.join(stale)}")
    else:
        status_color = "green"
        status_label = "READY"
        blockers = []

    source_of_truth = f"docs/context/{present[0]}" if present else "docs/context/exec_memory_packet_latest.json"
    supporting = [f"docs/context/{name}" for name in present[1:]] if len(present) > 1 else []

    return WorkflowNode(
        node_id="MemoryArtifacts",
        title="Memory & Advisory Artifacts",
        status_color=status_color,
        progress_state=status_label,
        owner_role="Worker",
        advisory_roles=["PM", "CEO"],
        complexity_band="LOW",
        rigor_mode="STANDARD",
        capability_band="agent_ok",
        blockers=blockers,
        source_of_truth=source_of_truth,
        supporting_artifacts=supporting,
        key_signals=[f"Present: {len(present)}/{len(artifacts_to_check)}"],
        next_action="Refresh stale artifacts" if stale else "Continue",
        updated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _derive_measurement_node(repo_root: Path) -> WorkflowNode:
    """Derive Measurement node status from phase_c_measurement artifacts."""
    measurement_dir = repo_root / "phase_c_measurement"

    if not measurement_dir.exists():
        return WorkflowNode(
            node_id="Measurement",
            title="Phase C Measurement",
            status_color="gray",
            progress_state="NOT_STARTED",
            owner_role="PM",
            advisory_roles=["CEO", "Worker"],
            complexity_band="LOW",
            rigor_mode="STANDARD",
            capability_band="agent_ok",
            blockers=["Measurement directory not found"],
            source_of_truth="phase_c_measurement/live_rounds.csv",
            supporting_artifacts=[],
            key_signals=[],
            next_action="Initialize measurement collection",
            updated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    # Parse live_rounds.csv
    csv_path = measurement_dir / "live_rounds.csv"
    round_count = 0
    if csv_path.exists():
        try:
            content = csv_path.read_text(encoding="utf-8-sig")
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            # Subtract 1 for header row
            round_count = max(0, len(lines) - 1)
        except Exception:
            pass

    # Parse target threshold from README
    readme_path = measurement_dir / "README.md"
    target_threshold = 10  # Default based on README
    if readme_path.exists():
        try:
            readme_content = readme_path.read_text(encoding="utf-8-sig")
            # Look for "X/Y" pattern or "Y+ rounds" pattern
            # Try fraction pattern first (e.g., "0/10 rounds")
            fraction_match = re.search(r"(\d+)/(\d+)\s+rounds?", readme_content, re.IGNORECASE)
            if fraction_match:
                target_threshold = int(fraction_match.group(2))
            else:
                # Try "N+ rounds" pattern (e.g., "10+ rounds")
                plus_match = re.search(r"(\d+)\+\s+rounds?", readme_content, re.IGNORECASE)
                if plus_match:
                    target_threshold = int(plus_match.group(1))
        except Exception:
            pass

    # Compute progress
    progress_pct = (round_count / target_threshold * 100) if target_threshold > 0 else 0

    # Determine status
    if round_count == 0:
        status_color = "blue"
        status_label = "ACTIVE"
        blockers = []
    elif progress_pct >= 100:
        status_color = "green"
        status_label = "COMPLETE"
        blockers = []
    elif progress_pct >= 80:
        status_color = "yellow"
        status_label = "ACTIVE"
        blockers = []
    else:
        status_color = "blue"
        status_label = "ACTIVE"
        blockers = []

    return WorkflowNode(
        node_id="Measurement",
        title="Phase C Measurement",
        status_color=status_color,
        progress_state=status_label,
        owner_role="PM",
        advisory_roles=["CEO", "Worker"],
        complexity_band="LOW",
        rigor_mode="STANDARD",
        capability_band="agent_ok",
        blockers=blockers,
        source_of_truth="phase_c_measurement/live_rounds.csv",
        supporting_artifacts=["phase_c_measurement/README.md"],
        key_signals=[f"Progress: {round_count}/{target_threshold} ({progress_pct:.1f}%)"],
        next_action="Continue collection" if progress_pct < 100 else "Review results",
        updated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _derive_static_docs_nodes(repo_root: Path) -> list[WorkflowNode]:
    """Derive static documentation nodes."""
    nodes = []

    # PublicEntry node
    readme_path = repo_root / "README.md"
    contributing_path = repo_root / "CONTRIBUTING.md"
    public_entry_status = "green" if readme_path.exists() else "yellow"
    public_entry_label = "READY" if readme_path.exists() else "BLOCKED"
    public_entry_blockers = [] if readme_path.exists() else ["README.md missing"]

    nodes.append(
        WorkflowNode(
            node_id="PublicEntry",
            title="Public Entry Points",
            status_color=public_entry_status,
            progress_state=public_entry_label,
            owner_role="PM",
            blockers=public_entry_blockers,
            source_of_truth="README.md",
            updated_at_utc=None,
            advisory_roles=["CEO"],
            complexity_band="LOW",
            rigor_mode="STANDARD",
            capability_band="agent_plus_review",
            supporting_artifacts=["CONTRIBUTING.md"],
            key_signals=[f"readme_exists={readme_path.exists()}"],
            next_action="Maintain documentation" if readme_path.exists() else "Create README",
        )
    )

    # DocsSpine node
    nodes.append(
        WorkflowNode(
            node_id="DocsSpine",
            title="Documentation Spine",
            status_color="green",
            progress_state="READY",
            owner_role="PM",
            blockers=[],
            source_of_truth="docs/loop_operating_contract.md",
            updated_at_utc=None,
            advisory_roles=["CEO", "Worker"],
            complexity_band="MEDIUM",
            rigor_mode="HIGH_RIGOR",
            capability_band="human_required",
            supporting_artifacts=["docs/round_contract_template.md"],
            key_signals=["docs_spine=PRESENT"],
            next_action="Keep docs current",
        )
    )

    # Authority node
    nodes.append(
        WorkflowNode(
            node_id="Authority",
            title="Authority & Policy",
            status_color="green",
            progress_state="READY",
            owner_role="PM",
            blockers=[],
            source_of_truth="docs/decision_authority_matrix.md",
            updated_at_utc=None,
            advisory_roles=["CEO", "Auditor"],
            complexity_band="HIGH",
            rigor_mode="HIGH_RIGOR",
            capability_band="human_required",
            supporting_artifacts=["docs/expert_invocation_policy.md"],
            key_signals=["authority_docs=PRESENT"],
            next_action="Review policy as needed",
        )
    )

    return nodes


def _compute_overall_summary(nodes: list[WorkflowNode]) -> str:
    """Compute human-readable overall summary from node statuses."""
    blocked_nodes = [node for node in nodes if node.progress_state == "BLOCKED"]
    if not blocked_nodes:
        return "All nodes ready"
    node_names = ", ".join(node.title for node in blocked_nodes)
    return f"Blocked nodes: {node_names}"


def _collect_artifact_inputs(repo_root: Path, nodes: list[WorkflowNode]) -> list[ArtifactInput]:
    """Collect artifact provenance from all nodes."""
    artifacts: list[ArtifactInput] = []
    seen: set[str] = set()
    for node in nodes:
        # Collect from source_of_truth
        source = node.source_of_truth
        if source and source not in seen:
            seen.add(source)
            full_path = repo_root / source
            try:
                mtime = full_path.stat().st_mtime
                updated_utc = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except (OSError, ValueError):
                updated_utc = "unknown"
            artifacts.append(
                ArtifactInput(
                    path=source,
                    updated_at_utc=updated_utc,
                )
            )
        # Collect from supporting_artifacts
        for path_str in node.supporting_artifacts:
            if path_str in seen:
                continue
            seen.add(path_str)
            full_path = repo_root / path_str
            try:
                mtime = full_path.stat().st_mtime
                updated_utc = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except (OSError, ValueError):
                updated_utc = "unknown"
            artifacts.append(
                ArtifactInput(
                    path=path_str,
                    updated_at_utc=updated_utc,
                )
            )
    return artifacts


def _build_role_views(nodes: list[WorkflowNode]) -> dict[str, list[str]]:
    """Group nodes by owner_role."""
    role_views: dict[str, list[str]] = {
        "PM": [],
        "CEO": [],
        "Worker": [],
        "Auditor": [],
        "QA": [],
    }

    for node in nodes:
        role = node.owner_role
        node_id = node.node_id
        if role in role_views and node_id:
            role_views[role].append(node_id)

    return role_views


def _derive_next_action_fallback(node: dict[str, Any]) -> str:
    """Fallback next action derivation when node lacks next_action field."""
    blockers = node.get("blockers", [])
    if blockers:
        return f"Resolve blockers: {', '.join(blockers)}"

    status_color = node.get("status_color", "gray")
    if status_color == "green":
        return "Ready to proceed"
    elif status_color == "gray":
        return "Not started - awaiting prerequisites"
    elif status_color == "blue":
        return "In progress"
    elif status_color == "yellow":
        return "Needs attention"
    elif status_color == "red":
        return "Failed - requires intervention"

    return "Status unclear"


def _render_workflow_status_markdown(
    payload: dict[str, Any] | WorkflowStatusOverlayPayload,
) -> str:
    """Render workflow status payload as human-readable Markdown.

    Args:
        payload: Complete workflow status payload from _assemble_workflow_status_payload

    Returns:
        Formatted Markdown string with trailing newline
    """
    payload_dict = coerce_workflow_overlay_payload_dict(payload)
    lines = []

    # Header section
    lines.append("# Workflow Status Overlay")
    lines.append("")
    lines.append(f"**Generated:** {payload_dict.get('generated_at_utc', 'N/A')}")

    overall_status = payload_dict.get("overall_status", "gray")
    status_emoji = STATUS_EMOJI.get(overall_status, "⚪")
    lines.append(f"**Overall Status:** {overall_status} {status_emoji}")
    lines.append(f"**Summary:** {payload_dict.get('overall_summary', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Legend section
    lines.append("## Status Legend")
    lines.append("")
    lines.append("🟢 Green = Ready | 🟡 Yellow = Blocked | 🔵 Blue = In Progress | ⚪ Gray = Not Started | 🔴 Red = Failed")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Railway section
    lines.append("## Workflow Railway")
    lines.append("")
    nodes = payload_dict.get("nodes", [])
    railway_parts = []
    for node in nodes:
        node_title = node.get("title", node.get("node_id", "Unknown"))
        node_color = node.get("status_color", "gray")
        emoji = STATUS_EMOJI.get(node_color, "⚪")
        railway_parts.append(f"{node_title}{emoji}")
    lines.append(" → ".join(railway_parts))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Node details sections
    lines.append("## Node Details")
    lines.append("")

    for idx, node in enumerate(nodes, 1):
        node_title = node.get("title", "Unknown")
        node_id = node.get("node_id", "unknown")
        status_color = node.get("status_color", "gray")
        progress_state = node.get("progress_state", "UNKNOWN")
        owner_role = node.get("owner_role", "N/A")
        blockers = node.get("blockers", [])
        source_of_truth = node.get("source_of_truth", "N/A")

        # Use next_action from payload first, fallback if missing
        next_action = node.get("next_action")
        if not next_action:
            next_action = _derive_next_action_fallback(node)

        emoji = STATUS_EMOJI.get(status_color, "⚪")

        lines.append(f"### {idx}. {node_title}")
        lines.append("")
        lines.append(f"**Status:** {status_color} {emoji} ({progress_state})")
        lines.append(f"**Owner:** {owner_role}")

        if blockers:
            lines.append(f"**Blockers:** {', '.join(blockers)}")
        else:
            lines.append("**Blockers:** None")

        lines.append(f"**Source of Truth:** `{source_of_truth}`")
        lines.append(f"**Next Action:** {next_action}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Role views section
    lines.append("## Role Views")
    lines.append("")
    role_views = payload_dict.get("role_views", {})
    for role in ["PM", "CEO", "Worker", "Auditor", "QA"]:
        node_ids = role_views.get(role, [])
        if node_ids:
            lines.append(f"**{role}:** {', '.join(node_ids)}")
        else:
            lines.append(f"**{role}:** (none)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Metadata section
    lines.append("## Metadata")
    lines.append("")
    metadata = payload_dict.get("metadata", {})
    lines.append(f"- **Generator:** {metadata.get('generator', 'N/A')}")
    lines.append(f"- **Advisory Only:** {metadata.get('advisory_only', True)}")
    lines.append(f"- **Schema Version:** {payload_dict.get('schema_version', 'N/A')}")
    lines.append(f"- **Source Policy:** {payload_dict.get('source_of_truth_policy', 'N/A')}")
    lines.append("")

    return "\n".join(lines)


def _assemble_workflow_status_payload(repo_root: Path, now_utc: datetime) -> dict[str, Any]:
    """Orchestrate all derivation and assemble complete workflow status payload."""
    # Derive all nodes
    nodes = [
        _derive_startup_node(repo_root),
        _derive_execution_node(repo_root),
        _derive_validation_closure_node(repo_root),
        _derive_round_contract_node(repo_root),
        _derive_memory_artifacts_node(repo_root),
        _derive_measurement_node(repo_root),
    ]
    nodes.extend(_derive_static_docs_nodes(repo_root))

    # Build role views
    role_views = _build_role_views(nodes)

    # Compute overall status (worst status across critical nodes)
    # Only consider Startup, Execution, and ValidationClosure for overall status
    critical_node_ids = {"Startup", "Execution", "ValidationClosure"}
    overall_status = "green"

    for node in nodes:
        if node.node_id in critical_node_ids:
            color = node.status_color
            if color == "red":
                overall_status = "red"
                break
            elif color == "yellow" and overall_status != "red":
                overall_status = "yellow"
            elif color == "blue" and overall_status not in ("red", "yellow"):
                overall_status = "blue"

    typed_payload = WorkflowStatusOverlay(
        schema_version="1.0.0",
        generated_at_utc=now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        repo_root=str(repo_root),
        source_of_truth_policy="docs/loop_operating_contract.md#source-of-truth-hierarchy",
        overall_status=overall_status,
        overall_summary=_compute_overall_summary(nodes),
        artifact_inputs=_collect_artifact_inputs(repo_root, nodes),
        nodes=nodes,
        role_views=role_views,
        metadata=WorkflowOverlayMetadata(
            generator="print_takeover_entrypoint.py",
            advisory_only=True,
            description="Workflow status overlay derived from existing artifacts",
        ),
    )
    return render_workflow_overlay_payload(typed_payload)


def _print_optional_advisory(repo_root: Path, label: str, relative_path: str) -> None:
    advisory_path = repo_root / Path(relative_path)
    try:
        advisory_text = _load_optional_handoff(advisory_path)
    except OSError as exc:
        print(f"WARNING: Unable to read {relative_path}: {exc}", file=sys.stderr)
        return
    if advisory_text is None:
        return
    print(f"{label}: present")
    print(f"{label}_path: {relative_path}")
    human_brief = _extract_human_brief(advisory_text)
    if human_brief is not None:
        print(f"{label}_summary: {human_brief}")
    machine_view_markers = _extract_machine_view_markers(advisory_text, label)
    for marker_name in MACHINE_VIEW_MARKERS.get(label, ()):
        marker_value = machine_view_markers.get(marker_name)
        if marker_value is not None:
            print(f"{label}_{marker_name.lower()}: {marker_value}")
    paste_ready_block = _extract_paste_ready_block(advisory_text)
    if paste_ready_block is not None:
        print(f"{label}_paste_ready_begin")
        print(paste_ready_block)
        print(f"{label}_paste_ready_end")
    print(f"{label}_begin")
    print(advisory_text)
    print(f"{label}_end")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print deterministic PM/CEO takeover entrypoint artifacts from loop closure status."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--workflow-status-json-out",
        type=Path,
        default=None,
        help="Optional path to write workflow status overlay JSON (default: None, no overlay generated)"
    )
    parser.add_argument(
        "--workflow-status-md-out",
        type=Path,
        default=None,
        help="Optional path to write workflow status overlay Markdown (default: None, no overlay generated)"
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    closure_path = repo_root / "docs" / "context" / "loop_closure_status_latest.json"

    try:
        payload = _load_closure_payload(closure_path)
    except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result_raw = payload.get("result")
    if not isinstance(result_raw, str) or not result_raw.strip():
        print("ERROR: Missing or invalid closure result.", file=sys.stderr)
        return 2
    result = result_raw.strip()

    print(f"closure_result: {result}")
    startup_gate_status = _extract_startup_gate_status(payload)
    if startup_gate_status is not None:
        print(f"startup_gate_status: {startup_gate_status}")

    for label, relative_path in ADVISORY_HANDOFFS:
        _print_optional_advisory(repo_root, label, relative_path)

    print("root_convenience_mirrors:")
    for mirror in ROOT_CONVENIENCE_MIRRORS:
        print(f"- {mirror}")

    print("artifacts:")
    for artifact in ARTIFACT_PATHS:
        print(f"- {artifact}")

    # Optional workflow status overlay generation
    payload_overlay = None

    if args.workflow_status_json_out is not None:
        try:
            now_utc = datetime.now(timezone.utc)
            payload_overlay = _assemble_workflow_status_payload(repo_root, now_utc)
            output_path = _resolve_approved_overlay_output(
                repo_root=repo_root,
                candidate=args.workflow_status_json_out,
                expected_relative=APPROVED_WORKFLOW_STATUS_JSON,
            )
            output_json = json.dumps(payload_overlay, indent=2, ensure_ascii=False)
            _atomic_write_text(output_path, output_json + "\n")
        except Exception as exc:
            print(f"WARNING: Failed to generate workflow status overlay: {exc}", file=sys.stderr)
            # Do not change exit code - overlay generation failure is non-fatal

    if args.workflow_status_md_out is not None:
        try:
            if payload_overlay is None:
                now_utc = datetime.now(timezone.utc)
                payload_overlay = _assemble_workflow_status_payload(repo_root, now_utc)
            output_path = _resolve_approved_overlay_output(
                repo_root=repo_root,
                candidate=args.workflow_status_md_out,
                expected_relative=APPROVED_WORKFLOW_STATUS_MD,
            )
            output_md = _render_workflow_status_markdown(payload_overlay)
            _atomic_write_text(output_path, output_md)
        except Exception as exc:
            print(f"WARNING: Failed to generate workflow status Markdown overlay: {exc}", file=sys.stderr)
            # Do not change exit code - overlay generation failure is non-fatal

    return _result_to_exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
