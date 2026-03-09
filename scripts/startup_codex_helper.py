from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReadinessSpec:
    key: str
    label: str
    rel_path: str
    max_age_hours: float | None


READINESS_SPECS: tuple[ReadinessSpec, ...] = (
    ReadinessSpec(
        key="loop_contract",
        label="Loop Operating Contract",
        rel_path="docs/loop_operating_contract.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="round_contract",
        label="Round Contract Template",
        rel_path="docs/round_contract_template.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="expert_policy",
        label="Expert Invocation Policy",
        rel_path="docs/expert_invocation_policy.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="authority_matrix",
        label="Decision Authority Matrix",
        rel_path="docs/decision_authority_matrix.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="disagreement_taxonomy",
        label="Disagreement Taxonomy",
        rel_path="docs/disagreement_taxonomy.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="disagreement_runbook",
        label="Disagreement Runbook",
        rel_path="docs/disagreement_runbook.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="rollback_protocol",
        label="Rollback Protocol",
        rel_path="docs/rollback_protocol.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="transition_playbook",
        label="Phase24C Transition Playbook",
        rel_path="docs/phase24c_transition_playbook.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="comms_protocol",
        label="W11 Comms Protocol",
        rel_path="docs/w11_comms_protocol.md",
        max_age_hours=None,
    ),
    ReadinessSpec(
        key="current_context",
        label="Current Context Packet",
        rel_path="docs/context/current_context.json",
        max_age_hours=48.0,
    ),
    ReadinessSpec(
        key="promotion_dossier",
        label="Promotion Dossier",
        rel_path="docs/context/auditor_promotion_dossier.json",
        max_age_hours=48.0,
    ),
    ReadinessSpec(
        key="ceo_go_signal",
        label="CEO GO Signal",
        rel_path="docs/context/ceo_go_signal.md",
        max_age_hours=48.0,
    ),
)

DEFAULT_MANDATORY_EXPERT_DOMAINS: tuple[str, ...] = ("principal", "riskops", "qa")
DEFAULT_OPTIONAL_EXPERT_DOMAINS: tuple[str, ...] = (
    "math_stats",
    "portfolio_risk",
    "market_microstructure",
    "data_eng",
    "infra_perf",
)
DEFAULT_BOARD_REENTRY_TRIGGERS: tuple[str, ...] = (
    "unknown_domain",
    "expert_conflict",
    "one_way_or_high_risk",
    "milestone_gate",
)
DEFAULT_PROJECT_PROFILE = "quant_default"
PROJECT_PROFILE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "quant_default": {
        "description": "Quant research and delivery baseline profile.",
        "mandatory_domains": DEFAULT_MANDATORY_EXPERT_DOMAINS,
        "optional_domains": DEFAULT_OPTIONAL_EXPERT_DOMAINS,
        "board_reentry_triggers": DEFAULT_BOARD_REENTRY_TRIGGERS,
        "domain_buckets": {
            "core_delivery": ["principal", "riskops", "qa"],
            "quant_research": ["math_stats", "portfolio_risk", "market_microstructure"],
            "platform_ops": ["data_eng", "infra_perf"],
        },
    },
    "general_software": {
        "description": "General software delivery profile for product, platform, and service work.",
        "mandatory_domains": DEFAULT_MANDATORY_EXPERT_DOMAINS,
        "optional_domains": ("product_ux", "data_eng", "infra_perf"),
        "board_reentry_triggers": DEFAULT_BOARD_REENTRY_TRIGGERS,
        "domain_buckets": {
            "core_delivery": ["principal", "riskops", "qa"],
            "product_and_user": ["product_ux"],
            "platform_ops": ["data_eng", "infra_perf"],
        },
    },
    "data_platform": {
        "description": "Data and platform engineering profile for pipelines, interfaces, and runtime reliability.",
        "mandatory_domains": DEFAULT_MANDATORY_EXPERT_DOMAINS,
        "optional_domains": ("data_eng", "infra_perf", "interface_arch"),
        "board_reentry_triggers": DEFAULT_BOARD_REENTRY_TRIGGERS,
        "domain_buckets": {
            "core_delivery": ["principal", "riskops", "qa"],
            "data_runtime": ["data_eng", "infra_perf"],
            "interfaces": ["interface_arch"],
        },
    },
}
ALLOWED_UNKNOWN_EXPERT_DOMAIN_POLICIES: tuple[str, ...] = (
    "ESCALATE_TO_BOARD",
    "ESCALATE_TO_PM",
    "HOLD_AND_REQUEST_CLARIFICATION",
)
PROFILE_SELECTION_RANKING_REL_PATH = "docs/context/profile_selection_ranking_latest.json"


def _normalize_csv_values(raw: str | None, *, fallback: tuple[str, ...] = ()) -> list[str]:
    values: list[str] = []
    source = raw if isinstance(raw, str) and raw.strip() else ",".join(fallback)
    for item in source.split(","):
        text = item.strip()
        if text and text not in values:
            values.append(text)
    return values


def _normalize_optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if text else None


def _normalize_optional_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return round(float(text), 4)
        except ValueError:
            return None
    return None


def _build_milestone_expert_roster(
    *,
    milestone_id: str,
    mandatory_domains: list[str],
    optional_domains: list[str],
    board_reentry_triggers: list[str],
    unknown_expert_domain_policy: str,
    generated_at_utc: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "milestone_id": milestone_id.strip() or "unspecified_milestone",
        "mandatory_domains": mandatory_domains,
        "optional_domains": optional_domains,
        "board_reentry_triggers": board_reentry_triggers,
        "unknown_expert_domain_policy": unknown_expert_domain_policy,
    }


def _build_domain_bucket_bootstrap(
    *,
    project_profile: str,
    profile_definition: dict[str, Any],
    milestone_expert_roster: dict[str, Any],
    generated_at_utc: str,
) -> dict[str, Any]:
    raw_buckets = profile_definition.get("domain_buckets", {})
    normalized_buckets: dict[str, list[str]] = {}
    if isinstance(raw_buckets, dict):
        for key, value in raw_buckets.items():
            bucket_name = str(key).strip()
            if not bucket_name:
                continue
            normalized_buckets[bucket_name] = _normalize_csv_values(
                ",".join(str(item).strip() for item in value) if isinstance(value, list) else "",
            )

    return {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "project_profile": project_profile,
        "mandatory_domains": list(milestone_expert_roster.get("mandatory_domains", [])),
        "optional_domains": list(milestone_expert_roster.get("optional_domains", [])),
        "board_reentry_triggers": list(
            milestone_expert_roster.get("board_reentry_triggers", [])
        ),
        "unknown_expert_domain_policy": str(
            milestone_expert_roster.get("unknown_expert_domain_policy", "")
        ).strip(),
        "domain_buckets": normalized_buckets,
        "advisory_note": (
            "Curated project-profile bootstrap for domain buckets; advisory only and does not "
            "change authority paths."
        ),
    }


def _extract_profile_selection_recommendation(
    ranking_payload: dict[str, Any],
) -> tuple[str | None, float | None, str | None, str | None]:
    recommended_profile = None
    for key in (
        "recommended_profile",
        "top_profile",
        "selected_profile",
        "project_profile",
    ):
        candidate = _normalize_optional_text(ranking_payload.get(key))
        if candidate is not None:
            recommended_profile = candidate
            break

    ranking_nodes = ranking_payload.get("ranking")
    if recommended_profile is None and isinstance(ranking_nodes, list):
        for entry in ranking_nodes:
            if not isinstance(entry, dict):
                continue
            candidate = _normalize_optional_text(
                entry.get("profile") or entry.get("project_profile")
            )
            if candidate is not None:
                recommended_profile = candidate
                break

    confidence = _normalize_optional_float(
        ranking_payload.get("confidence")
        or ranking_payload.get("recommended_confidence")
        or ranking_payload.get("score")
    )
    if confidence is None and isinstance(ranking_nodes, list) and ranking_nodes:
        first = ranking_nodes[0]
        if isinstance(first, dict):
            confidence = _normalize_optional_float(
                first.get("confidence") or first.get("score")
            )

    evidence_summary = None
    for key in ("evidence_summary", "rationale", "reason", "justification"):
        candidate = _normalize_optional_text(ranking_payload.get(key))
        if candidate is not None:
            evidence_summary = candidate
            break

    as_of_utc = None
    for key in ("generated_at_utc", "as_of_utc", "updated_at_utc"):
        candidate = _normalize_optional_text(ranking_payload.get(key))
        if candidate is not None:
            as_of_utc = candidate
            break

    return recommended_profile, confidence, evidence_summary, as_of_utc


def _load_profile_selection_advisory(
    *, repo_root: Path, now_utc: datetime
) -> dict[str, Any]:
    ranking_path = repo_root / PROFILE_SELECTION_RANKING_REL_PATH
    base_payload: dict[str, Any] = {
        "status": "RANKING_MISSING",
        "source_path": PROFILE_SELECTION_RANKING_REL_PATH,
        "recommended_profile": None,
        "recommended_profile_known": None,
        "confidence": None,
        "evidence_summary": None,
        "as_of_utc": None,
        "ranking_age_hours": None,
        "advisory_only": True,
        "usage_note": (
            "Evidence-learned profile recommendation is advisory only; active startup/project "
            "profile remains authoritative."
        ),
    }

    if not ranking_path.exists():
        return base_payload

    try:
        raw = ranking_path.read_text(encoding="utf-8-sig")
        ranking_payload = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {
            **base_payload,
            "status": "RANKING_INVALID",
            "ranking_age_hours": round(_age_hours(ranking_path, now_utc), 2),
        }

    if not isinstance(ranking_payload, dict):
        return {
            **base_payload,
            "status": "RANKING_INVALID",
            "ranking_age_hours": round(_age_hours(ranking_path, now_utc), 2),
        }

    (
        recommended_profile,
        confidence,
        evidence_summary,
        as_of_utc,
    ) = _extract_profile_selection_recommendation(ranking_payload)

    if recommended_profile is None:
        return {
            **base_payload,
            "status": "RANKING_PRESENT_NO_RECOMMENDATION",
            "ranking_age_hours": round(_age_hours(ranking_path, now_utc), 2),
            "as_of_utc": as_of_utc,
            "evidence_summary": evidence_summary,
            "confidence": confidence,
        }

    known_profile = recommended_profile in PROJECT_PROFILE_DEFINITIONS
    return {
        **base_payload,
        "status": "PROFILE_RECOMMENDED" if known_profile else "PROFILE_RECOMMENDED_UNKNOWN",
        "recommended_profile": recommended_profile,
        "recommended_profile_known": known_profile,
        "confidence": confidence,
        "evidence_summary": evidence_summary,
        "as_of_utc": as_of_utc,
        "ranking_age_hours": round(_age_hours(ranking_path, now_utc), 2),
    }


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _age_hours(path: Path, now_utc: datetime) -> float:
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    elapsed = now_utc - modified
    return max(0.0, elapsed.total_seconds() / 3600.0)


def _to_output_path(repo_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _readiness_status(
    path: Path, now_utc: datetime, max_age_hours: float | None
) -> tuple[str, bool, float | None]:
    if not path.exists():
        return "MISSING", False, None
    age = _age_hours(path=path, now_utc=now_utc)
    if max_age_hours is None:
        return "READY", True, age
    if age <= max_age_hours:
        return "READY", True, age
    return "STALE", False, age


def collect_readiness(repo_root: Path, now_utc: datetime) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ready_count = 0
    missing_count = 0
    stale_count = 0

    for spec in READINESS_SPECS:
        abs_path = repo_root / spec.rel_path
        status, is_ready, age = _readiness_status(
            path=abs_path, now_utc=now_utc, max_age_hours=spec.max_age_hours
        )
        if is_ready:
            ready_count += 1
        elif status == "MISSING":
            missing_count += 1
        elif status == "STALE":
            stale_count += 1
        rows.append(
            {
                "key": spec.key,
                "label": spec.label,
                "path": spec.rel_path,
                "status": status,
                "age_hours": None if age is None else round(age, 2),
                "max_age_hours": spec.max_age_hours,
            }
        )

    total = len(READINESS_SPECS)
    ratio = (ready_count / total) if total else 0.0
    summary = {
        "total_docs": total,
        "ready_docs": ready_count,
        "missing_docs": missing_count,
        "stale_docs": stale_count,
        "ready_ratio": round(ratio, 4),
        "ready_percent": round(ratio * 100.0, 1),
        "status": "READY" if ready_count == total else "NEEDS_ATTENTION",
    }
    return rows, summary


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


def _prompt_or_value(
    *, current: str | None, prompt: str, no_interactive: bool
) -> str:
    if isinstance(current, str) and current.strip():
        return current.strip()
    if no_interactive:
        return ""
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def _validate_interrogation(interrogation: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field in (
        "original_intent",
        "deliverable_this_scope",
        "non_goals",
        "done_when",
        "positioning_lock",
        "decision_class",
        "execution_lane",
        "intuition_gate",
        "intuition_gate_rationale",
    ):
        value = interrogation.get(field, "")
        if not isinstance(value, str) or not value.strip():
            errors.append(field)

    decision_class = str(interrogation.get("decision_class", "")).strip()
    if decision_class and decision_class not in {"ONE_WAY", "TWO_WAY"}:
        errors.append("decision_class(invalid; use ONE_WAY|TWO_WAY)")

    execution_lane = str(interrogation.get("execution_lane", "")).strip()
    if execution_lane and execution_lane not in {"STANDARD", "FAST"}:
        errors.append("execution_lane(invalid; use STANDARD|FAST)")

    intuition_gate = str(interrogation.get("intuition_gate", "")).strip()
    if intuition_gate and intuition_gate not in {"MACHINE_DEFAULT", "HUMAN_REQUIRED"}:
        errors.append("intuition_gate(invalid; use MACHINE_DEFAULT|HUMAN_REQUIRED)")

    granularity_raw = interrogation.get("task_granularity_limit", "")
    if granularity_raw is None or (isinstance(granularity_raw, str) and not granularity_raw.strip()):
        errors.append("task_granularity_limit")
    else:
        try:
            granularity = int(str(granularity_raw).strip())
        except ValueError:
            errors.append("task_granularity_limit(invalid; use integer 1|2)")
        else:
            if granularity not in {1, 2}:
                errors.append("task_granularity_limit(invalid; use 1|2)")
            else:
                interrogation["task_granularity_limit"] = granularity

    return errors


def _readiness_line_items(rows: list[dict[str, Any]], *, status: str) -> str:
    selected = [row["path"] for row in rows if row.get("status") == status]
    if not selected:
        return "none"
    return ", ".join(str(path) for path in selected)


def _handoff_policy(target: str) -> dict[str, str]:
    if target == "local_cli":
        return {
            "target": "LOCAL_CLI",
            "worker_header": "(skills call upon worker)",
            "handoff_mode": "SKILL_CALL",
            "instruction": "Both send/receive are local CLI: use skills call upon worker.",
        }
    return {
        "target": "SONNET_WEB",
        "worker_header": "(paste to sonnet web)",
        "handoff_mode": "PASTE",
        "instruction": "Paste Worker Kickoff block to Sonnet web auditor.",
    }


def _relative_or_absolute(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _is_utcish_iso8601(value: str) -> bool:
    raw = value.strip()
    if not raw or raw == "N/A":
        return False
    normalized = raw[:-1] + "+00:00" if raw.endswith(("Z", "z")) else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    if parsed.tzinfo is None:
        return False
    return parsed.utcoffset() == timedelta(0)


def _evaluate_startup_gate(
    *,
    intuition_gate: str,
    intuition_gate_ack: str,
    intuition_gate_ack_at_utc: str,
) -> dict[str, Any]:
    ack = intuition_gate_ack.strip()
    ack_at_utc = intuition_gate_ack_at_utc.strip()
    errors: list[str] = []

    if intuition_gate == "MACHINE_DEFAULT":
        status = "READY_TO_EXECUTE"
    elif intuition_gate == "HUMAN_REQUIRED":
        if ack not in {"PM_ACK", "CEO_ACK"}:
            errors.append("intuition_gate_ack(required for HUMAN_REQUIRED; use PM_ACK|CEO_ACK)")
        if not _is_utcish_iso8601(ack_at_utc):
            errors.append(
                "intuition_gate_ack_at_utc(required for HUMAN_REQUIRED; use ISO8601 UTC, e.g. 2026-03-05T12:00:00Z)"
            )
        status = "READY_TO_EXECUTE" if not errors else "BLOCKED_WAITING_FOR_HUMAN_ACK"
    else:
        status = "BLOCKED_INVALID_GATE"
        errors.append("intuition_gate(invalid; use MACHINE_DEFAULT|HUMAN_REQUIRED)")

    return {
        "status": status,
        "intuition_gate_ack": ack,
        "intuition_gate_ack_at_utc": ack_at_utc,
        "errors": errors,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["readiness_summary"]
    interrogation = payload["interrogation"]
    rows = payload["readiness_docs"]
    handoff = payload["handoff"]
    profile_selection_advisory = payload["profile_selection_advisory"]

    lines: list[str] = [
        "# Codex Startup Intake",
        "",
        f"- GeneratedAtUTC: {payload['generated_at_utc']}",
        f"- StartupHelper: {payload['startup_helper']}",
        f"- ReadinessStatus: {summary['status']}",
        (
            f"- ReadinessProgress: {summary['ready_docs']}/{summary['total_docs']} "
            f"({summary['ready_percent']}%)"
        ),
        "",
        "## Readiness Dashboard",
        "",
        "| Doc | Path | Status | AgeHours | MaxAgeHours |",
        "|---|---|---|---:|---:|",
    ]

    for row in rows:
        age_text = "N/A" if row["age_hours"] is None else str(row["age_hours"])
        max_age_text = "N/A" if row["max_age_hours"] is None else str(row["max_age_hours"])
        lines.append(
            f"| {row['label']} | `{row['path']}` | {row['status']} | {age_text} | {max_age_text} |"
        )

    lines.extend(
        [
            "",
            "## Interrogation Result",
            "",
            f"- ORIGINAL_INTENT: {interrogation['original_intent']}",
            f"- DELIVERABLE_THIS_SCOPE: {interrogation['deliverable_this_scope']}",
            f"- NON_GOALS: {interrogation['non_goals']}",
            f"- DONE_WHEN: {interrogation['done_when']}",
            f"- DECISION_CLASS: {interrogation['decision_class']}",
            f"- EXECUTION_LANE: {interrogation['execution_lane']}",
            f"- POSITIONING_LOCK: {interrogation['positioning_lock']}",
            f"- TASK_GRANULARITY_LIMIT: {interrogation['task_granularity_limit']}",
            f"- INTUITION_GATE: {interrogation['intuition_gate']}",
            f"- INTUITION_GATE_RATIONALE: {interrogation['intuition_gate_rationale']}",
            f"- STARTUP_GATE_STATUS: {payload['startup_gate']['status']}",
            f"- INTUITION_GATE_ACK: {payload['startup_gate']['intuition_gate_ack']}",
            f"- INTUITION_GATE_ACK_AT_UTC: {payload['startup_gate']['intuition_gate_ack_at_utc']}",
            f"- HANDOFF_TARGET: {handoff['target']}",
            f"- WORKER_HEADER: {handoff['worker_header']}",
            f"- HANDOFF_MODE: {handoff['handoff_mode']}",
            f"- PROFILE_SELECTION_STATUS: {profile_selection_advisory['status']}",
            (
                "- EVIDENCE_RECOMMENDED_PROFILE: "
                f"{profile_selection_advisory['recommended_profile'] or 'none'}"
            ),
            (
                "- EVIDENCE_PROFILE_CONFIDENCE: "
                f"{profile_selection_advisory['confidence'] if profile_selection_advisory['confidence'] is not None else 'N/A'}"
            ),
            (
                "- EVIDENCE_PROFILE_SOURCE: "
                f"{profile_selection_advisory['source_path']}"
            ),
            (
                "- EVIDENCE_PROFILE_USAGE_NOTE: "
                f"{profile_selection_advisory['usage_note']}"
            ),
            "",
            "## Paste-Ready Worker Kickoff",
            "",
            "```text",
            f"WORKER_HEADER: {handoff['worker_header']}",
            f"HANDOFF_TARGET: {handoff['target']}",
            f"HANDOFF_MODE: {handoff['handoff_mode']}",
            f"HANDOFF_INSTRUCTION: {handoff['instruction']}",
            f"ROUND_ID: startup_{payload['generated_at_utc'].replace(':', '').replace('-', '')}",
            f"ORIGINAL_INTENT: {interrogation['original_intent']}",
            f"DELIVERABLE_THIS_SCOPE: {interrogation['deliverable_this_scope']}",
            f"NON_GOALS: {interrogation['non_goals']}",
            f"DONE_WHEN: {interrogation['done_when']}",
            f"DECISION_CLASS: {interrogation['decision_class']}",
            f"EXECUTION_LANE: {interrogation['execution_lane']}",
            f"POSITIONING_LOCK: {interrogation['positioning_lock']}",
            f"TASK_GRANULARITY_LIMIT: {interrogation['task_granularity_limit']}",
            f"INTUITION_GATE: {interrogation['intuition_gate']}",
            f"INTUITION_GATE_RATIONALE: {interrogation['intuition_gate_rationale']}",
            f"STARTUP_GATE_STATUS: {payload['startup_gate']['status']}",
            f"INTUITION_GATE_ACK: {payload['startup_gate']['intuition_gate_ack']}",
            f"INTUITION_GATE_ACK_AT_UTC: {payload['startup_gate']['intuition_gate_ack_at_utc']}",
            (
                f"READINESS_PROGRESS: {summary['ready_docs']}/{summary['total_docs']} "
                f"({summary['ready_percent']}%)"
            ),
            f"READINESS_STATUS: {summary['status']}",
            f"MISSING_DOCS: {_readiness_line_items(rows, status='MISSING')}",
            f"STALE_DOCS: {_readiness_line_items(rows, status='STALE')}",
            f"PROFILE_SELECTION_STATUS: {profile_selection_advisory['status']}",
            (
                "EVIDENCE_RECOMMENDED_PROFILE: "
                f"{profile_selection_advisory['recommended_profile'] or 'none'}"
            ),
            (
                "EVIDENCE_PROFILE_CONFIDENCE: "
                f"{profile_selection_advisory['confidence'] if profile_selection_advisory['confidence'] is not None else 'N/A'}"
            ),
            f"EVIDENCE_PROFILE_SOURCE: {profile_selection_advisory['source_path']}",
            "NEXT_STEP: Worker drafts round contract and submits End-of-Round Summary to Auditor.",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _render_init_execution_card(
    *, payload: dict[str, Any], output_md: Path, repo_root: Path
) -> str:
    summary = payload["readiness_summary"]
    interrogation = payload["interrogation"]
    handoff = payload["handoff"]
    startup_gate = payload["startup_gate"]
    profile_selection_advisory = payload["profile_selection_advisory"]

    if interrogation["intuition_gate"] == "HUMAN_REQUIRED":
        ack_status = (
            f"{startup_gate['intuition_gate_ack']} @ {startup_gate['intuition_gate_ack_at_utc']}"
        )
    else:
        ack_status = "N/A (MACHINE_DEFAULT)"

    next_action = (
        "Use the worker kickoff block reference to start execution."
        if startup_gate["status"] == "READY_TO_EXECUTE"
        else "Capture PM_ACK/CEO_ACK with UTC timestamp, then rerun startup helper."
    )

    kickoff_ref = _relative_or_absolute(output_md, repo_root=repo_root)
    required_fields = (
        "ORIGINAL_INTENT, DELIVERABLE_THIS_SCOPE, NON_GOALS, DONE_WHEN, "
        "DECISION_CLASS, EXECUTION_LANE, POSITIONING_LOCK, TASK_GRANULARITY_LIMIT, "
        "INTUITION_GATE, INTUITION_GATE_RATIONALE"
    )

    lines = [
        "# Init Execution Card",
        "",
        f"- GeneratedAtUTC: {payload['generated_at_utc']}",
        f"- StartupGateStatus: {startup_gate['status']}",
        f"- HandoffTarget: {handoff['target']}",
        f"- WorkerHeader: {handoff['worker_header']}",
        (
            "- ProfileSelectionAdvisory: "
            f"{profile_selection_advisory['status']} -> "
            f"{profile_selection_advisory['recommended_profile'] or 'none'}"
        ),
        f"- RequiredContractFields: {required_fields}",
        f"- AckStatus: {ack_status}",
        (
            f"- ReadinessProgress: {summary['ready_docs']}/{summary['total_docs']} "
            f"({summary['ready_percent']}%)"
        ),
        f"- ReadinessStatus: {summary['status']}",
        "",
        "## Worker Kickoff Reference",
        "```text",
        f"OPEN: {kickoff_ref}",
        "SECTION: Paste-Ready Worker Kickoff",
        f"WORKER_HEADER: {handoff['worker_header']}",
        f"HANDOFF_TARGET: {handoff['target']}",
        "```",
        f"- NEXT_ACTION: {next_action}",
        "",
    ]
    return "\n".join(lines)


def _render_round_contract_seed(payload: dict[str, Any]) -> str:
    interrogation = payload["interrogation"]
    startup_gate = payload["startup_gate"]
    milestone_expert_roster = payload["milestone_expert_roster"]
    domain_bucket_bootstrap = payload["domain_bucket_bootstrap"]
    profile_selection_advisory = payload["profile_selection_advisory"]
    ack = startup_gate["intuition_gate_ack"].strip()
    ack_at_utc = startup_gate["intuition_gate_ack_at_utc"].strip()

    lines = [
        "# Round Contract Seed",
        "",
        f"- GENERATED_AT_UTC: {payload['generated_at_utc']}",
        "",
        "## Prefilled Fields",
        "",
        f"- ORIGINAL_INTENT: {interrogation['original_intent']}",
        f"- DELIVERABLE_THIS_SCOPE: {interrogation['deliverable_this_scope']}",
        f"- NON_GOALS: {interrogation['non_goals']}",
        f"- DONE_WHEN: {interrogation['done_when']}",
        f"- POSITIONING_LOCK: {interrogation['positioning_lock']}",
        f"- TASK_GRANULARITY_LIMIT: {interrogation['task_granularity_limit']}",
        f"- DECISION_CLASS: {interrogation['decision_class']}",
        "- RISK_TIER: TODO(LOW|MEDIUM|HIGH)",
        f"- EXECUTION_LANE: {interrogation['execution_lane']}",
        f"- INTUITION_GATE: {interrogation['intuition_gate']}",
        f"- INTUITION_GATE_RATIONALE: {interrogation['intuition_gate_rationale']}",
        f"- PROJECT_PROFILE: {domain_bucket_bootstrap['project_profile']}",
        (
            "- EVIDENCE_PROFILE_RECOMMENDATION_STATUS: "
            f"{profile_selection_advisory['status']}"
        ),
        (
            "- EVIDENCE_PROFILE_RECOMMENDATION: "
            f"{profile_selection_advisory['recommended_profile'] or 'none'}"
        ),
        (
            "- EVIDENCE_PROFILE_RECOMMENDATION_CONFIDENCE: "
            f"{profile_selection_advisory['confidence'] if profile_selection_advisory['confidence'] is not None else 'N/A'}"
        ),
        (
            "- EVIDENCE_PROFILE_SELECTION_SOURCE_ARTIFACT: "
            f"{profile_selection_advisory['source_path']}"
        ),
        "- EVIDENCE_PROFILE_SELECTION_USAGE: advisory_only_no_authority_change",
        f"- MILESTONE_ID: {milestone_expert_roster['milestone_id']}",
        "- APPROVED_MANDATORY_EXPERT_DOMAINS: "
        + ",".join(milestone_expert_roster["mandatory_domains"]),
        "- APPROVED_OPTIONAL_EXPERT_DOMAINS: "
        + ",".join(milestone_expert_roster["optional_domains"]),
        "- BOARD_REENTRY_TRIGGERS: "
        + ",".join(milestone_expert_roster["board_reentry_triggers"]),
        f"- UNKNOWN_EXPERT_DOMAIN_POLICY: {milestone_expert_roster['unknown_expert_domain_policy']}",
        "- BOARD_REENTRY_REQUIRED: TODO(YES|NO)",
        "- BOARD_REENTRY_REASON: TODO(or N/A)",
        "- DONE_WHEN_CHECKS: TODO(comma-separated check IDs from loop/closure outputs)",
        "- COUNTEREXAMPLE_TEST_COMMAND: TODO(use N/A only if TDD_MODE=NOT_APPLICABLE)",
        "- COUNTEREXAMPLE_TEST_RESULT: TODO(use N/A only if TDD_MODE=NOT_APPLICABLE)",
        "- REFACTOR_BUDGET_MINUTES: 0",
        "- REFACTOR_SPEND_MINUTES: 0",
        "- REFACTOR_BUDGET_EXCEEDED_REASON: N/A",
        "- MOCK_POLICY_MODE: NOT_APPLICABLE",
        "- MOCKED_DEPENDENCIES: N/A",
        "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
        "- OWNED_FILES: TODO(comma-separated repo-relative paths)",
        "- INTERFACE_INPUTS: TODO(explicit inbound artifacts/params)",
        "- INTERFACE_OUTPUTS: TODO(explicit outbound artifacts/outputs)",
        "- PARALLEL_SHARD_ID: TODO(optional; use none if single-worker)",
    ]

    if ack and ack != "N/A":
        lines.append(f"- INTUITION_GATE_ACK: {ack}")
    if ack_at_utc and ack_at_utc != "N/A":
        lines.append(f"- ACK_AT_UTC: {ack_at_utc}")

    lines.extend(
        [
            "",
            "## TDD Contract (Proof at Closure)",
            "",
            "- TDD_MODE: TODO(REQUIRED|NOT_APPLICABLE)",
            "- RED_TEST_COMMAND: TODO",
            "- RED_TEST_RESULT: TODO",
            "- GREEN_TEST_COMMAND: TODO",
            "- GREEN_TEST_RESULT: TODO",
            "- REFACTOR_NOTE: TODO",
            "- TDD_NOT_APPLICABLE_REASON: TODO(if NOT_APPLICABLE)",
            "",
            "## TODO (Startup Cannot Infer)",
            "",
            "- EVIDENCE_COMMANDS: TODO(add exact validation and evidence commands).",
            "- EXPERT_PLAN: TODO(list expert consult path and escalation trigger).",
            "- CHANGE_BUDGET_DETAILS: TODO(specify risk, rollback, and time budget constraints).",
            "",
        ]
    )
    return "\n".join(lines)


def _print_terminal_summary(
    *,
    generated_at_utc: str,
    summary: dict[str, Any],
    interrogation: dict[str, str],
    startup_gate: dict[str, Any],
    profile_selection_advisory: dict[str, Any],
    rows: list[dict[str, Any]],
) -> None:
    handoff = _handoff_policy(interrogation["handoff_target"])
    print("STARTUP_HELPER: CODEX")
    print(f"WORKER_HEADER: {handoff['worker_header']}")
    print(f"HANDOFF_TARGET: {handoff['target']}")
    print(f"HANDOFF_MODE: {handoff['handoff_mode']}")
    print(f"GENERATED_AT_UTC: {generated_at_utc}")
    print(
        f"READINESS_PROGRESS: {summary['ready_docs']}/{summary['total_docs']} "
        f"({summary['ready_percent']}%)"
    )
    print(f"READINESS_STATUS: {summary['status']}")
    print(f"MISSING_DOCS: {_readiness_line_items(rows, status='MISSING')}")
    print(f"STALE_DOCS: {_readiness_line_items(rows, status='STALE')}")
    print(f"PROFILE_SELECTION_STATUS: {profile_selection_advisory['status']}")
    print(
        "PROFILE_SELECTION_RECOMMENDED: "
        + str(profile_selection_advisory["recommended_profile"] or "none")
    )
    print(f"ORIGINAL_INTENT: {interrogation['original_intent']}")
    print(f"DELIVERABLE_THIS_SCOPE: {interrogation['deliverable_this_scope']}")
    print(f"NON_GOALS: {interrogation['non_goals']}")
    print(f"DONE_WHEN: {interrogation['done_when']}")
    print(f"DECISION_CLASS: {interrogation['decision_class']}")
    print(f"EXECUTION_LANE: {interrogation['execution_lane']}")
    print(f"POSITIONING_LOCK: {interrogation['positioning_lock']}")
    print(f"TASK_GRANULARITY_LIMIT: {interrogation['task_granularity_limit']}")
    print(f"INTUITION_GATE: {interrogation['intuition_gate']}")
    print(f"INTUITION_GATE_RATIONALE: {interrogation['intuition_gate_rationale']}")
    print(f"INTUITION_GATE_ACK: {startup_gate['intuition_gate_ack']}")
    print(f"INTUITION_GATE_ACK_AT_UTC: {startup_gate['intuition_gate_ack_at_utc']}")
    print(f"STARTUP_GATE_STATUS: {startup_gate['status']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Codex startup helper: show readiness docs progress and capture "
            "intent interrogation before Worker/Auditor loop starts."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root used to resolve readiness docs.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/context/startup_intake_latest.md"),
        help="Markdown output path for startup intake artifact.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/context/startup_intake_latest.json"),
        help="JSON output path for startup intake artifact.",
    )
    parser.add_argument(
        "--output-card",
        type=Path,
        default=Path("docs/context/init_execution_card_latest.md"),
        help="Markdown output path for concise init execution card artifact.",
    )
    parser.add_argument(
        "--output-round-seed",
        type=Path,
        default=Path("docs/context/round_contract_seed_latest.md"),
        help="Markdown output path for prefilled round contract seed artifact.",
    )
    parser.add_argument("--original-intent", type=str, default="")
    parser.add_argument("--deliverable-this-scope", type=str, default="")
    parser.add_argument("--non-goals", type=str, default="")
    parser.add_argument("--done-when", type=str, default="")
    parser.add_argument("--positioning-lock", type=str, default="")
    parser.add_argument("--task-granularity-limit", type=str, default="")
    parser.add_argument("--decision-class", type=str, default="")
    parser.add_argument("--execution-lane", type=str, default="")
    parser.add_argument("--intuition-gate", type=str, default="")
    parser.add_argument("--intuition-gate-rationale", type=str, default="")
    parser.add_argument(
        "--intuition-gate-ack",
        choices=("PM_ACK", "CEO_ACK", "N/A"),
        default="N/A",
    )
    parser.add_argument(
        "--intuition-gate-ack-at-utc",
        type=str,
        default="N/A",
    )
    parser.add_argument(
        "--handoff-target",
        choices=("sonnet_web", "local_cli"),
        default="sonnet_web",
        help=(
            "Worker kickoff handoff target. "
            "sonnet_web emits '(paste to sonnet web)'; "
            "local_cli emits '(skills call upon worker)'."
        ),
    )
    parser.add_argument(
        "--project-profile",
        choices=tuple(PROJECT_PROFILE_DEFINITIONS.keys()),
        default=DEFAULT_PROJECT_PROFILE,
        help="Curated project profile for domain bucket bootstrap defaults.",
    )
    parser.add_argument("--milestone-id", type=str, default="")
    parser.add_argument("--mandatory-expert-domains", type=str, default="")
    parser.add_argument("--optional-expert-domains", type=str, default="")
    parser.add_argument("--board-reentry-triggers", type=str, default="")
    parser.add_argument(
        "--unknown-expert-domain-policy",
        choices=ALLOWED_UNKNOWN_EXPERT_DOMAIN_POLICIES,
        default="ESCALATE_TO_BOARD",
    )
    parser.add_argument(
        "--output-expert-roster-json",
        type=Path,
        default=Path("docs/context/milestone_expert_roster_latest.json"),
        help="JSON output path for additive milestone expert roster artifact.",
    )
    parser.add_argument(
        "--output-domain-bootstrap-json",
        type=Path,
        default=Path("docs/context/domain_bucket_bootstrap_latest.json"),
        help="JSON output path for additive project-profile domain bucket bootstrap artifact.",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable prompts; required interrogation fields must come from CLI args.",
    )
    parser.add_argument(
        "--min-ready-ratio",
        type=float,
        default=0.0,
        help="Optional fail threshold for readiness ratio (0.0-1.0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.min_ready_ratio < 0.0 or args.min_ready_ratio > 1.0:
        print("--min-ready-ratio must be between 0.0 and 1.0", file=sys.stderr)
        return 2

    repo_root = args.repo_root.resolve()
    now_utc = _now_utc()
    generated_at_utc = _utc_iso(now_utc)

    readiness_rows, readiness_summary = collect_readiness(repo_root=repo_root, now_utc=now_utc)

    interrogation = {
        "original_intent": _prompt_or_value(
            current=args.original_intent,
            prompt="ORIGINAL_INTENT: ",
            no_interactive=args.no_interactive,
        ),
        "deliverable_this_scope": _prompt_or_value(
            current=args.deliverable_this_scope,
            prompt="DELIVERABLE_THIS_SCOPE: ",
            no_interactive=args.no_interactive,
        ),
        "non_goals": _prompt_or_value(
            current=args.non_goals,
            prompt="NON_GOALS: ",
            no_interactive=args.no_interactive,
        ),
        "done_when": _prompt_or_value(
            current=args.done_when,
            prompt="DONE_WHEN: ",
            no_interactive=args.no_interactive,
        ),
        "positioning_lock": _prompt_or_value(
            current=args.positioning_lock,
            prompt="POSITIONING_LOCK: ",
            no_interactive=args.no_interactive,
        ),
        "task_granularity_limit": _prompt_or_value(
            current=args.task_granularity_limit,
            prompt="TASK_GRANULARITY_LIMIT (1|2): ",
            no_interactive=args.no_interactive,
        ),
        "decision_class": _prompt_or_value(
            current=args.decision_class,
            prompt="DECISION_CLASS (ONE_WAY|TWO_WAY): ",
            no_interactive=args.no_interactive,
        ),
        "execution_lane": _prompt_or_value(
            current=args.execution_lane,
            prompt="EXECUTION_LANE (STANDARD|FAST): ",
            no_interactive=args.no_interactive,
        ),
        "intuition_gate": _prompt_or_value(
            current=args.intuition_gate,
            prompt="INTUITION_GATE (MACHINE_DEFAULT|HUMAN_REQUIRED): ",
            no_interactive=args.no_interactive,
        ),
        "intuition_gate_rationale": _prompt_or_value(
            current=args.intuition_gate_rationale,
            prompt="INTUITION_GATE_RATIONALE: ",
            no_interactive=args.no_interactive,
        ),
        "handoff_target": args.handoff_target,
    }

    missing_fields = _validate_interrogation(interrogation)
    if missing_fields:
        print(
            "Missing or invalid interrogation fields: "
            + ", ".join(missing_fields)
            + ". Provide args or run interactive mode.",
            file=sys.stderr,
        )
        return 1

    startup_gate = _evaluate_startup_gate(
        intuition_gate=interrogation["intuition_gate"],
        intuition_gate_ack=args.intuition_gate_ack,
        intuition_gate_ack_at_utc=args.intuition_gate_ack_at_utc,
    )
    if startup_gate["errors"]:
        print(
            "Startup gate validation failed: " + ", ".join(startup_gate["errors"]),
            file=sys.stderr,
        )
        return 1

    profile_definition = PROJECT_PROFILE_DEFINITIONS[args.project_profile]
    default_mandatory_domains = tuple(profile_definition.get("mandatory_domains", ()))
    default_optional_domains = tuple(profile_definition.get("optional_domains", ()))
    default_board_reentry_triggers = tuple(
        profile_definition.get("board_reentry_triggers", ())
    )

    milestone_expert_roster = _build_milestone_expert_roster(
        milestone_id=args.milestone_id,
        mandatory_domains=_normalize_csv_values(
            args.mandatory_expert_domains,
            fallback=default_mandatory_domains,
        ),
        optional_domains=_normalize_csv_values(
            args.optional_expert_domains,
            fallback=default_optional_domains,
        ),
        board_reentry_triggers=_normalize_csv_values(
            args.board_reentry_triggers,
            fallback=default_board_reentry_triggers,
        ),
        unknown_expert_domain_policy=args.unknown_expert_domain_policy,
        generated_at_utc=generated_at_utc,
    )
    domain_bucket_bootstrap = _build_domain_bucket_bootstrap(
        project_profile=args.project_profile,
        profile_definition=profile_definition,
        milestone_expert_roster=milestone_expert_roster,
        generated_at_utc=generated_at_utc,
    )
    profile_selection_advisory = _load_profile_selection_advisory(
        repo_root=repo_root,
        now_utc=now_utc,
    )

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "startup_helper": "codex",
        "generated_at_utc": generated_at_utc,
        "readiness_summary": readiness_summary,
        "readiness_docs": readiness_rows,
        "handoff": _handoff_policy(args.handoff_target),
        "startup_gate": startup_gate,
        "interrogation": interrogation,
        "milestone_expert_roster": milestone_expert_roster,
        "domain_bucket_bootstrap": domain_bucket_bootstrap,
        "profile_selection_advisory": profile_selection_advisory,
    }

    try:
        md_out = _to_output_path(repo_root=repo_root, candidate=args.output_md)
        json_out = _to_output_path(repo_root=repo_root, candidate=args.output_json)
        card_out = _to_output_path(repo_root=repo_root, candidate=args.output_card)
        round_seed_out = _to_output_path(repo_root=repo_root, candidate=args.output_round_seed)
        expert_roster_out = _to_output_path(
            repo_root=repo_root,
            candidate=args.output_expert_roster_json,
        )
        domain_bootstrap_out = _to_output_path(
            repo_root=repo_root,
            candidate=args.output_domain_bootstrap_json,
        )
        _atomic_write_text(md_out, _render_markdown(payload))
        _atomic_write_text(
            card_out,
            _render_init_execution_card(payload=payload, output_md=md_out, repo_root=repo_root),
        )
        _atomic_write_text(round_seed_out, _render_round_contract_seed(payload))
        _atomic_write_text(
            expert_roster_out,
            json.dumps(milestone_expert_roster, indent=2, ensure_ascii=True) + "\n",
        )
        _atomic_write_text(
            domain_bootstrap_out,
            json.dumps(domain_bucket_bootstrap, indent=2, ensure_ascii=True) + "\n",
        )
        _atomic_write_text(json_out, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
    except OSError as exc:
        print(f"I/O failure while writing startup artifacts: {exc}", file=sys.stderr)
        return 2

    _print_terminal_summary(
        generated_at_utc=generated_at_utc,
        summary=readiness_summary,
        interrogation=interrogation,
        startup_gate=startup_gate,
        profile_selection_advisory=profile_selection_advisory,
        rows=readiness_rows,
    )

    if readiness_summary["ready_ratio"] < args.min_ready_ratio:
        print(
            (
                "Readiness ratio below threshold: "
                f"{readiness_summary['ready_ratio']} < {args.min_ready_ratio}"
            ),
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
