from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports when run as script
if __name__ == "__main__":
    _script_dir = Path(__file__).resolve().parent
    _project_root = _script_dir.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

try:
    from sop.scripts.utils.json_utils import safe_load_json_object
    from sop.scripts.utils.compaction_retention import build_compaction_policy_snapshot
    from sop.scripts.utils.memory_tiers import bind_memory_tier_paths
    from sop.scripts.utils.memory_tiers import build_memory_tier_snapshot
    from sop.scripts.utils.skill_resolver import resolve_active_skills
except ModuleNotFoundError:
    # Fallback for direct script execution (development mode)
    from scripts.utils.json_utils import safe_load_json_object
    from scripts.utils.compaction_retention import build_compaction_policy_snapshot
    from scripts.utils.memory_tiers import bind_memory_tier_paths
    from scripts.utils.memory_tiers import build_memory_tier_snapshot
    from scripts.utils.skill_resolver import resolve_active_skills


AUTOMATION_BOUNDARY_REGISTRY_PATH = "docs/automation_boundary_registry.md"
MILESTONE_EXPERT_ROSTER_PATH = "docs/context/milestone_expert_roster_latest.json"
CRITICAL_INPUTS = frozenset({"loop_cycle_summary_latest.json", "ceo_go_signal.md"})
IMPORTANT_INPUTS = frozenset({"auditor_promotion_dossier.json", "auditor_calibration_report.json"})
BUILD_PACKET_MEMORY_FAMILIES = (
    "loop_cycle_summary",
    "auditor_promotion_dossier",
    "auditor_calibration_report",
    "ceo_go_signal",
    "decision_log",
    "milestone_expert_roster",
    "project_skill_config",
    "extension_allowlist",
    "skill_registry",
    "exec_memory_packet",
    "exec_memory_build_status",
    "next_round_handoff",
    "expert_request",
    "pm_ceo_research_brief",
    "board_decision_brief",
    "skill_activation",
)
BUILD_PACKET_COLD_FALLBACK_FAMILIES = ("auditor_fp_ledger",)


def _resolve_input_category(input_name: str) -> str:
    if input_name in CRITICAL_INPUTS:
        return "critical"
    if input_name in IMPORTANT_INPUTS:
        return "important"
    return "optional"


def _append_input_status(
    input_status: dict[str, list[dict[str, str]]],
    *,
    path: Path,
    loaded: bool,
) -> None:
    input_name = path.name
    category = _resolve_input_category(input_name)
    status = "loaded" if loaded else "missing_or_invalid"
    input_status[category].append(
        {
            "file": input_name,
            "path": str(path),
            "status": status,
        }
    )

    if loaded:
        return

    if category == "critical":
        print(f"ERROR: Critical input missing or invalid: {path}", file=sys.stderr)
    elif category == "important":
        print(f"WARNING: Important input degraded: {path}", file=sys.stderr)


def _critical_input_failures(
    input_status: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    return [
        item
        for item in input_status["critical"]
        if item["status"] == "missing_or_invalid"
    ]


def _is_authoritative_latest_path(path: Path) -> bool:
    return path.stem.endswith("_latest")


def _write_build_status(
    *,
    path: Path,
    generated_at_utc: str,
    output_json_path: Path,
    output_md_path: Path,
    input_status: dict[str, list[dict[str, str]]],
    critical_failures: list[dict[str, str]],
    authoritative_latest_written: bool,
    degraded_preview_written: bool,
    exit_code: int,
    reason: str,
) -> None:
    payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "output_json": str(output_json_path),
        "output_md": str(output_md_path),
        "authoritative_latest_written": authoritative_latest_written,
        "degraded_preview_written": degraded_preview_written,
        "critical_failures": [item["file"] for item in critical_failures],
        "critical_inputs_ok": len(critical_failures) == 0,
        "input_status": input_status,
        "exit_code": exit_code,
        "reason": reason,
    }
    _atomic_write_text(path, json.dumps(payload, indent=2) + "\n")


def _coerce_domain_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item).strip().lower()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _load_milestone_expert_roster(context_dir: Path) -> dict[str, Any]:
    roster_path = context_dir / "milestone_expert_roster_latest.json"
    payload, error = safe_load_json_object(roster_path)

    default_reentry_triggers = [
        "UNKNOWN_EXPERT_DOMAIN",
        "ROSTER_MISSING",
        "EXPERT_DISAGREEMENT",
        "MILESTONE_GATE_REVIEW",
    ]
    if payload is None:
        return {
            "path": MILESTONE_EXPERT_ROSTER_PATH,
            "present": False,
            "status": "ROSTER_MISSING",
            "milestone_id": "unknown",
            "mandatory_domains": [],
            "optional_domains": [],
            "all_domains": [],
            "board_reentry_triggers": default_reentry_triggers,
            "unknown_domain_policy": "BOARD_LINEUP_REVIEW_REQUIRED",
        }

    mandatory_domains = _coerce_domain_list(payload.get("mandatory_domains"))
    optional_domains = _coerce_domain_list(payload.get("optional_domains"))
    all_domains: list[str] = []
    for domain in [*mandatory_domains, *optional_domains]:
        if domain not in all_domains:
            all_domains.append(domain)

    status = "ROSTER_READY" if all_domains else "ROSTER_MISSING"
    milestone_id = str(payload.get("milestone_id", "unknown")).strip() or "unknown"
    board_reentry_triggers = _coerce_domain_list(payload.get("board_reentry_triggers"))
    if not board_reentry_triggers:
        board_reentry_triggers = default_reentry_triggers
    unknown_domain_policy = (
        str(
            payload.get(
                "unknown_expert_domain_policy",
                payload.get("unknown_domain_policy", "BOARD_LINEUP_REVIEW_REQUIRED"),
            )
        ).strip().upper()
        or "BOARD_LINEUP_REVIEW_REQUIRED"
    )

    return {
        "path": MILESTONE_EXPERT_ROSTER_PATH,
        "present": True,
        "status": status,
        "milestone_id": milestone_id,
        "mandatory_domains": mandatory_domains,
        "optional_domains": optional_domains,
        "all_domains": all_domains,
        "board_reentry_triggers": board_reentry_triggers,
        "unknown_domain_policy": unknown_domain_policy,
    }


def _resolve_lineup_fit(
    *,
    requested_domain: str,
    roster_context: dict[str, Any],
    require_assignment: bool,
) -> dict[str, Any]:
    normalized_domain = str(requested_domain).strip().lower()
    roster_status = str(roster_context.get("status", "ROSTER_MISSING")).strip().upper()
    all_domains = {
        str(domain).strip().lower()
        for domain in roster_context.get("all_domains", [])
        if str(domain).strip()
    }

    board_reentry_reason_codes: list[str] = []
    board_reentry_required = False

    if roster_status != "ROSTER_READY":
        roster_fit = "ROSTER_MISSING"
        if require_assignment:
            board_reentry_required = True
            board_reentry_reason_codes = ["ROSTER_MISSING", "BOARD_LINEUP_REVIEW_REQUIRED"]
    elif normalized_domain and normalized_domain in all_domains:
        roster_fit = "IN_ROSTER"
    else:
        roster_fit = "UNKNOWN_EXPERT_DOMAIN"
        if require_assignment:
            board_reentry_required = True
            board_reentry_reason_codes = [
                "UNKNOWN_EXPERT_DOMAIN",
                "BOARD_LINEUP_REVIEW_REQUIRED",
            ]

    target_expert = normalized_domain
    if require_assignment and roster_fit in {"ROSTER_MISSING", "UNKNOWN_EXPERT_DOMAIN"}:
        target_expert = "unknown"

    return {
        "requested_domain": normalized_domain or "unknown",
        "target_expert": target_expert or "unknown",
        "roster_fit": roster_fit,
        "board_reentry_required": board_reentry_required,
        "board_reentry_reason_codes": board_reentry_reason_codes,
    }


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_text(path: Path, content: str) -> None:
    """Atomic write via temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".tmp_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(content)
            tmp = Path(handle.name)
        os.replace(tmp, path)
    except Exception:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
        raise


def _estimate_tokens(text: str) -> int:
    """Deterministic simple token estimate: ~4 chars per token."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _load_text_safe(path: Path) -> str:
    """Load text file, return empty string if missing."""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception:
        return ""


def _build_advisory_split_surface(
    *,
    surface_name: str,
    status: str,
    human_brief: str,
    machine_view_lines: list[str],
) -> dict[str, str]:
    """Build additive machine/human response surfaces for advisory artifacts."""
    machine_view = "\n".join(
        [
            f"SURFACE: {surface_name}",
            f"STATUS: {status}",
            *[line for line in machine_view_lines if line],
        ]
    )
    return {
        "machine_view": machine_view,
        "human_brief": human_brief.strip(),
    }


def _append_advisory_split_markdown(
    md_lines: list[str],
    *,
    human_brief: str,
    machine_view: str,
    paste_ready_block: str,
) -> None:
    """Append human, machine, and paste-ready advisory views to markdown output."""
    md_lines.extend(
        [
            "### Human Brief",
            "",
            human_brief,
            "",
            "### Machine View",
            "",
            "```text",
            machine_view,
            "```",
            "",
            "### Paste-Ready Block",
            "",
            "```text",
            paste_ready_block,
            "```",
            "",
        ]
    )


def _truncate_to_budget(text: str, budget: int) -> tuple[str, int]:
    """Truncate text to fit token budget, return (truncated_text, actual_tokens)."""
    tokens = _estimate_tokens(text)
    if tokens <= budget:
        return text, tokens
    # Truncate to budget (chars = tokens * 4)
    char_limit = budget * 4
    truncated = text[:char_limit] + "... [TRUNCATED]"
    return truncated, budget


def _coerce_count(value: Any, fallback: int) -> int:
    """Parse an integer count, falling back deterministically."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(0, parsed)


def _resolve_summary_count(
    summary: dict[str, Any],
    *,
    canonical_key: str,
    legacy_key: str,
    computed_fallback: int,
) -> tuple[int, bool]:
    """Resolve count with canonical-first, then legacy, then computed fallback."""
    if canonical_key in summary:
        return _coerce_count(summary.get(canonical_key), 0), True
    if legacy_key in summary:
        return _coerce_count(summary.get(legacy_key), 0), True
    return computed_fallback, False


def _count_step_outcomes(steps: list[dict[str, Any]]) -> dict[str, int]:
    """Count outcomes from loop summary steps with tolerant status normalization."""
    counts = {
        "PASS": 0,
        "HOLD": 0,
        "FAIL": 0,
        "ERROR": 0,
        "SKIP": 0,
    }
    for step in steps:
        raw_status = step.get("status", step.get("result", ""))
        status = str(raw_status).strip().upper()
        if status in {"PASS", "PASSED", "OK", "COMPLETE", "COMPLETED"}:
            counts["PASS"] += 1
        elif status in {"HOLD", "ON_HOLD"}:
            counts["HOLD"] += 1
        elif status in {"FAIL", "FAILED", "BLOCK", "BLOCKED"}:
            counts["FAIL"] += 1
        elif status in {"ERROR", "ERR"}:
            counts["ERROR"] += 1
        elif status in {"SKIP", "SKIPPED"}:
            counts["SKIP"] += 1
    return counts


def _build_working_summary(loop_summary: dict | None) -> str:
    """Extract working-level summary from loop schema: final_result/step_summary/steps."""
    if not loop_summary:
        return "No loop cycle summary available."

    lines = []
    run_id = str(loop_summary.get("run_id", "")).strip()
    if run_id:
        lines.append(f"Run ID: {run_id}")

    final_result = str(loop_summary.get("final_result", "")).strip().upper() or "UNKNOWN"

    steps_raw = loop_summary.get("steps")
    steps = [step for step in steps_raw if isinstance(step, dict)] if isinstance(steps_raw, list) else []
    computed_counts = _count_step_outcomes(steps)

    step_summary = loop_summary.get("step_summary")
    summary = step_summary if isinstance(step_summary, dict) else {}

    pass_count, _ = _resolve_summary_count(
        summary,
        canonical_key="pass_count",
        legacy_key="pass",
        computed_fallback=computed_counts["PASS"],
    )
    hold_count, _ = _resolve_summary_count(
        summary,
        canonical_key="hold_count",
        legacy_key="hold",
        computed_fallback=computed_counts["HOLD"],
    )
    fail_count, _ = _resolve_summary_count(
        summary,
        canonical_key="fail_count",
        legacy_key="fail",
        computed_fallback=computed_counts["FAIL"],
    )
    error_count, _ = _resolve_summary_count(
        summary,
        canonical_key="error_count",
        legacy_key="error",
        computed_fallback=computed_counts["ERROR"],
    )
    skip_count, _ = _resolve_summary_count(
        summary,
        canonical_key="skip_count",
        legacy_key="skip",
        computed_fallback=computed_counts["SKIP"],
    )
    total_count, total_from_summary = _resolve_summary_count(
        summary,
        canonical_key="total_steps",
        legacy_key="total",
        computed_fallback=len(steps),
    )
    if not total_from_summary and total_count == 0 and steps:
        total_count = len(steps)

    lines.append(f"Final result: {final_result}")
    lines.append(f"Steps total: {total_count}")
    lines.append(
        "Step outcomes: "
        f"PASS={pass_count}, HOLD={hold_count}, FAIL={fail_count}, ERROR={error_count}, SKIP={skip_count}"
    )

    blocking_steps: list[str] = []
    for step in steps:
        raw_status = step.get("status", step.get("result", ""))
        status = str(raw_status).strip().upper()
        if status in {"HOLD", "ON_HOLD", "FAIL", "FAILED", "BLOCK", "BLOCKED", "ERROR", "ERR"}:
            step_id = str(step.get("step_id", step.get("name", "unknown_step"))).strip() or "unknown_step"
            blocking_steps.append(step_id)
    if blocking_steps:
        lines.append(f"Blocking steps: {', '.join(blocking_steps)}")

    return "\n".join(lines)


def _build_issue_summary(dossier: dict | None, calibration: dict | None) -> str:
    """Extract issue-level summary from auditor reports."""
    lines = []

    if calibration:
        totals = calibration.get("totals", {})
        critical = totals.get("critical", 0)
        high = totals.get("high", 0)
        if critical > 0 or high > 0:
            lines.append(f"Auditor findings: {critical} critical, {high} high")

    if dossier:
        criteria = dossier.get("promotion_criteria", {})
        unmet = [k for k, v in criteria.items() if isinstance(v, dict) and v.get("met") is False]
        if unmet:
            lines.append(f"Promotion blockers: {', '.join(unmet)}")

    if not lines:
        lines.append("No critical issues detected.")

    return "\n".join(lines)


def _extract_markdown_section_lines(text: str, heading: str) -> list[str]:
    """Extract non-empty bullet/numbered lines beneath a markdown heading."""
    if not text:
        return []

    target = heading.strip().lower()
    in_section = False
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = line[3:].strip().lower()
            if current == target:
                in_section = True
                continue
            if in_section:
                break
        if not in_section or not line:
            continue
        if line.startswith(("- ", "* ")):
            lines.append(line[2:].strip())
            continue
        if line[:2].isdigit() and ". " in line:
            lines.append(line.split(". ", 1)[1].strip())
            continue
    return lines


def _build_replanning_summary(
    loop_summary: dict | None,
    dossier: dict | None,
    calibration: dict | None,
    go_signal_text: str,
) -> dict[str, Any]:
    """Build a deterministic, artifact-bound replanning packet."""
    blocking_gaps: list[dict[str, str]] = []
    recommended_artifacts_to_refresh: list[str] = []

    final_result = ""
    go_action = ""

    if loop_summary:
        final_result = str(loop_summary.get("final_result", "")).strip().upper()
        if final_result and final_result != "PASS":
            blocking_gaps.append(
                {
                    "source": "loop_cycle_summary",
                    "source_path": "docs/context/loop_cycle_summary_latest.json",
                    "code": f"final_result:{final_result}",
                    "detail": f"Loop cycle final_result is {final_result}.",
                }
            )

        steps_raw = loop_summary.get("steps")
        if isinstance(steps_raw, list):
            for step in steps_raw:
                if not isinstance(step, dict):
                    continue
                status = str(step.get("status", "")).strip().upper()
                if status not in {"HOLD", "FAIL", "ERROR"}:
                    continue
                step_name = str(step.get("name", step.get("step_id", "unknown"))).strip()
                message = str(step.get("message", "")).strip() or "No step message recorded."
                blocking_gaps.append(
                    {
                        "source": "loop_cycle_summary",
                        "source_path": "docs/context/loop_cycle_summary_latest.json",
                        "code": f"step:{step_name}",
                        "detail": f"{status}: {message}",
                    }
                )

    if dossier:
        criteria = dossier.get("promotion_criteria", {})
        if isinstance(criteria, dict):
            for criterion, payload in criteria.items():
                if not isinstance(payload, dict):
                    continue
                if payload.get("met") is False:
                    value = str(payload.get("value", "")).strip() or "criterion not met"
                    blocking_gaps.append(
                        {
                            "source": "auditor_promotion_dossier",
                            "source_path": "docs/context/auditor_promotion_dossier.json",
                            "code": criterion,
                            "detail": value,
                        }
                    )
                elif payload.get("met") == "MANUAL_CHECK":
                    value = str(payload.get("value", "")).strip() or "manual signoff required"
                    blocking_gaps.append(
                        {
                            "source": "auditor_promotion_dossier",
                            "source_path": "docs/context/auditor_promotion_dossier.json",
                            "code": criterion,
                            "detail": f"Manual check required: {value}",
                        }
                    )

    if calibration:
        totals = calibration.get("totals", {})
        if isinstance(totals, dict):
            critical = int(totals.get("critical", 0) or 0)
            high = int(totals.get("high", 0) or 0)
            if critical > 0 or high > 0:
                blocking_gaps.append(
                    {
                        "source": "auditor_calibration_report",
                        "source_path": "docs/context/auditor_calibration_report.json",
                        "code": "auditor_findings",
                        "detail": f"Auditor totals include {critical} critical and {high} high findings.",
                    }
                )
        fp_analysis = calibration.get("fp_analysis", {})
        if isinstance(fp_analysis, dict):
            unannotated = int(fp_analysis.get("ch_unannotated", 0) or 0)
            if unannotated > 0:
                blocking_gaps.append(
                    {
                        "source": "auditor_calibration_report",
                        "source_path": "docs/context/auditor_calibration_report.json",
                        "code": "fp_unannotated",
                        "detail": f"Critical/High findings still need annotation ({unannotated} remaining).",
                    }
                )

    for line in go_signal_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("- recommended action:"):
            go_action = stripped.split(":", 1)[1].strip().upper()
            break

    if go_action in {"HOLD", "REFRAME"}:
        blocking_gaps.append(
            {
                "source": "ceo_go_signal",
                "source_path": "docs/context/ceo_go_signal.md",
                "code": "recommended_action",
                "detail": f"CEO go signal action is {go_action}.",
            }
        )

    for reason in _extract_markdown_section_lines(go_signal_text, "Blocking Reasons"):
        blocking_gaps.append(
            {
                "source": "ceo_go_signal",
                "source_path": "docs/context/ceo_go_signal.md",
                "code": "blocking_reason",
                "detail": reason,
            }
        )

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for gap in blocking_gaps:
        key = (
            gap["source"],
            gap.get("source_path", ""),
            gap["code"],
            gap["detail"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(gap)

    for gap in deduped:
        source_path = gap.get("source_path", "")
        if source_path and source_path not in recommended_artifacts_to_refresh:
            recommended_artifacts_to_refresh.append(source_path)

    next_steps = _extract_markdown_section_lines(go_signal_text, "Next Steps")
    if any(gap["code"] == "fp_unannotated" for gap in deduped):
        next_replan_recommendation = "Annotate the remaining Critical/High findings, regenerate calibration and dossier artifacts, then rerun closure."
    elif any(gap["detail"].startswith("Manual check required:") for gap in deduped):
        next_replan_recommendation = "Capture the required manual signoff in the decision log after automated criteria are satisfied, then rerun closure."
    elif next_steps:
        next_replan_recommendation = next_steps[0]
    elif deduped:
        first_gap = deduped[0]
        next_replan_recommendation = (
            f"Address {first_gap['code']} from {first_gap['source']} and rerun the loop cycle."
        )
    else:
        next_replan_recommendation = "No blocking gaps detected; continue with the next planned execution slice."

    return {
        "status": "ACTION_REQUIRED" if deduped else "CLEAR",
        "observed_loop_final_result": final_result or "UNKNOWN",
        "observed_go_action": go_action or "UNKNOWN",
        "blocking_gaps": deduped,
        "blocking_gap_count": len(deduped),
        "next_replan_recommendation": next_replan_recommendation,
        "recommended_artifacts_to_refresh": recommended_artifacts_to_refresh,
    }


def _build_next_round_handoff(replanning: dict[str, Any]) -> dict[str, Any]:
    """Convert replanning state into an advisory, paste-ready next-round handoff."""
    status = str(replanning.get("status", "CLEAR")).strip().upper() or "CLEAR"
    blocking_gaps = [
        gap for gap in replanning.get("blocking_gaps", []) if isinstance(gap, dict)
    ]
    artifacts_to_refresh = [
        str(path).strip()
        for path in replanning.get("recommended_artifacts_to_refresh", [])
        if str(path).strip()
    ]
    next_replan_recommendation = str(
        replanning.get("next_replan_recommendation", "")
    ).strip() or "Continue with the next planned execution slice."
    observed_go_action = (
        str(replanning.get("observed_go_action", "UNKNOWN")).strip().upper()
        or "UNKNOWN"
    )

    unique_gap_codes: list[str] = []
    for gap in blocking_gaps:
        code = str(gap.get("code", "")).strip()
        if code and code not in unique_gap_codes:
            unique_gap_codes.append(code)

    has_unannotated = "fp_unannotated" in unique_gap_codes
    has_manual_check = any(
        str(gap.get("detail", "")).startswith("Manual check required:")
        for gap in blocking_gaps
    )
    has_dossier_gap = any(
        str(gap.get("source", "")) == "auditor_promotion_dossier"
        and str(gap.get("code", "")) != "fp_unannotated"
        for gap in blocking_gaps
    )
    has_loop_gap = any(
        str(gap.get("source", "")) == "loop_cycle_summary" for gap in blocking_gaps
    )

    if status == "CLEAR":
        recommended_intent = "Advance the next planned execution slice with current gates green."
        recommended_scope = (
            "Continue normal execution using the existing round workflow and evidence discipline."
        )
        non_goals = "Do not widen scope or change promotion policy without new evidence."
        done_when = (
            "The next planned slice is executed and the resulting artifacts remain closure-ready."
        )
    elif has_unannotated:
        recommended_intent = (
            "Close annotation-driven promotion blockers before the next escalation attempt."
        )
        recommended_scope = (
            "Annotate remaining Critical/High findings, refresh calibration and dossier artifacts, "
            "regenerate the CEO go signal, and rerun closure."
        )
        non_goals = (
            "Do not introduce new architecture or widen scope beyond clearing the current evidence blockers."
        )
        done_when = (
            "Critical/High findings are fully annotated, refreshed artifacts are written, and closure is rerun with updated evidence."
        )
    elif has_manual_check:
        recommended_intent = (
            "Complete the remaining manual signoff path after automated criteria are satisfied."
        )
        recommended_scope = (
            "Refresh any stale promotion artifacts, capture the required manual signoff in the decision log, "
            "and rerun closure."
        )
        non_goals = (
            "Do not claim escalation readiness before both automated and manual criteria are evidenced."
        )
        done_when = (
            "Manual signoff is captured with refreshed artifacts and closure is rerun against the latest evidence."
        )
    elif has_dossier_gap or observed_go_action in {"HOLD", "REFRAME"}:
        recommended_intent = (
            "Resolve the current promotion-readiness blockers surfaced by governance artifacts."
        )
        recommended_scope = (
            "Refresh the blocked governance artifacts, address the highest-priority blocker, "
            "and rerun the loop cycle and closure checks."
        )
        non_goals = (
            "Do not start unrelated feature work until the current promotion blockers are reduced or cleared."
        )
        done_when = (
            "Top governance blockers are addressed and the refreshed closure result reflects the new evidence."
        )
    elif has_loop_gap:
        recommended_intent = (
            "Resolve the active loop-cycle execution blockers before the next handoff."
        )
        recommended_scope = (
            "Address the failing or held loop step, refresh affected artifacts, and rerun the loop cycle."
        )
        non_goals = "Do not widen scope beyond the currently blocked execution path."
        done_when = (
            "The held or failing loop step is resolved and the loop cycle is rerun with updated artifacts."
        )
    else:
        recommended_intent = "Stabilize the current execution slice using the latest artifact evidence."
        recommended_scope = (
            "Address the first blocking gap, refresh linked artifacts, and rerun the loop cycle."
        )
        non_goals = "Do not change control-plane behavior while resolving the current slice."
        done_when = "The leading blocking gap is addressed and rerun evidence is available."

    recommended_done_when_checks: list[str] = ["startup_gate_status"]
    if status == "ACTION_REQUIRED":
        recommended_done_when_checks.extend(["go_signal_action_gate", "freshness_gate"])
    if has_loop_gap:
        recommended_done_when_checks.append("done_when_checks_gate")
    if has_unannotated or has_dossier_gap:
        recommended_done_when_checks.append("go_signal_truth_gate")

    deduped_checks: list[str] = []
    for check in recommended_done_when_checks:
        if check not in deduped_checks:
            deduped_checks.append(check)

    blocker_priority = {
        "fp_unannotated": 0,
        "recommended_action": 1,
        "blocking_reason": 2,
        "auditor_findings": 3,
    }
    top_blockers = sorted(
        unique_gap_codes,
        key=lambda code: (blocker_priority.get(code, 10), unique_gap_codes.index(code)),
    )[:4]
    refresh_line = ", ".join(artifacts_to_refresh) if artifacts_to_refresh else "none"
    blockers_line = ", ".join(top_blockers) if top_blockers else "none"
    paste_ready_block = "\n".join(
        [
            "HANDOFF_MODE: ADVISORY_EXEC_MEMORY_PACKET",
            f"HANDOFF_STATUS: {status}",
            f"ORIGINAL_INTENT: {recommended_intent}",
            f"DELIVERABLE_THIS_SCOPE: {recommended_scope}",
            f"NON_GOALS: {non_goals}",
            f"DONE_WHEN: {done_when}",
            f"DONE_WHEN_CHECKS: {','.join(deduped_checks)}",
            f"PRIMARY_BLOCKERS: {blockers_line}",
            f"ARTIFACTS_TO_REFRESH: {refresh_line}",
            f"NEXT_REPLAN_RECOMMENDATION: {next_replan_recommendation}",
            "ADVISORY_NOTE: Generated from current exec memory artifacts; startup interrogation remains authoritative before execution.",
        ]
    )
    human_brief = (
        f"Status {status}. {recommended_intent} Focus this scope on {recommended_scope} "
        f"Done when {done_when} Required checks: {', '.join(deduped_checks)}. "
        f"Primary blockers: {blockers_line}. Artifacts to refresh: {refresh_line}. "
        "This handoff is advisory only; startup interrogation remains authoritative before execution."
    )
    split_surface = _build_advisory_split_surface(
        surface_name="next_round_handoff",
        status=status,
        human_brief=human_brief,
        machine_view_lines=[
            f"RECOMMENDED_INTENT: {recommended_intent}",
            f"RECOMMENDED_SCOPE: {recommended_scope}",
            f"DONE_WHEN: {done_when}",
            f"DONE_WHEN_CHECKS: {','.join(deduped_checks)}",
            f"PRIMARY_BLOCKERS: {blockers_line}",
            f"ARTIFACTS_TO_REFRESH: {refresh_line}",
            f"OBSERVED_GO_ACTION: {observed_go_action}",
            f"NEXT_REPLAN_RECOMMENDATION: {next_replan_recommendation}",
        ],
    )

    return {
        "advisory": True,
        "status": status,
        "recommended_intent": recommended_intent,
        "recommended_scope": recommended_scope,
        "non_goals": non_goals,
        "done_when": done_when,
        "recommended_done_when_checks": deduped_checks,
        "primary_blockers": top_blockers,
        "artifacts_to_refresh": artifacts_to_refresh,
        "observed_go_action": observed_go_action,
        "next_replan_recommendation": next_replan_recommendation,
        **split_surface,
        "paste_ready_block": paste_ready_block,
    }


def _build_expert_request(
    *,
    replanning: dict[str, Any],
    next_round_handoff: dict[str, Any],
    roster_context: dict[str, Any],
) -> dict[str, Any]:
    """Build an advisory expert request packet from current blockers."""
    status = str(next_round_handoff.get("status", "CLEAR")).strip().upper() or "CLEAR"
    blockers = [str(code).strip() for code in next_round_handoff.get("primary_blockers", []) if str(code).strip()]
    recommended_checks = [
        str(check).strip()
        for check in next_round_handoff.get("recommended_done_when_checks", [])
        if str(check).strip()
    ]
    refresh_paths = [
        str(path).strip()
        for path in next_round_handoff.get("artifacts_to_refresh", [])
        if str(path).strip()
    ]
    source_paths: list[str] = []
    for gap in replanning.get("blocking_gaps", []):
        if not isinstance(gap, dict):
            continue
        path = str(gap.get("source_path", "")).strip()
        if path and path not in source_paths:
            source_paths.append(path)

    target_expert = "qa"
    trigger_reason = "optional_quality_review"
    if "fp_unannotated" in blockers:
        target_expert = "riskops"
        trigger_reason = "annotation_gap_or_fail_closed_risk"
    elif any(code.startswith("step:") for code in blockers):
        target_expert = "qa"
        trigger_reason = "execution_blocker_or_validation_gap"
    elif any(code in {"c1_24b_close", "recommended_action", "blocking_reason"} for code in blockers):
        target_expert = "principal"
        trigger_reason = "promotion_tradeoff_or_manual_decision_path"

    if status == "ACTION_REQUIRED":
        question = (
            f"What is the minimum-correct next move to resolve the active blockers ({', '.join(blockers) if blockers else 'none'}) "
            f"and satisfy the required checks ({', '.join(recommended_checks) if recommended_checks else 'none'}) "
            f"without widening scope beyond the current execution slice?"
        )
        why_blocked = (
            next_round_handoff.get("next_replan_recommendation")
            or "Current blockers require specialist clarification before the next escalation attempt."
        )
    else:
        question = (
            "What lightweight review or validation would most improve confidence in the next planned execution slice "
            "without adding unnecessary process?"
        )
        why_blocked = "No hard blocker is active; this is an optional confidence-raising expert review."

    requested_output_format = (
        "Return: verdict, key findings, top 1-3 risks, recommended next action, and artifact/path references."
    )
    source_artifacts = refresh_paths or source_paths
    decision_depends_on = (
        str(next_round_handoff.get("recommended_scope", "")).strip() or "N/A"
    )
    if recommended_checks:
        decision_depends_on = (
            f"{decision_depends_on} | required_checks={','.join(recommended_checks)}"
        )
    lineup_resolution = _resolve_lineup_fit(
        requested_domain=target_expert,
        roster_context=roster_context,
        require_assignment=status == "ACTION_REQUIRED",
    )
    requested_domain = lineup_resolution["requested_domain"]
    target_expert = lineup_resolution["target_expert"]
    roster_fit = lineup_resolution["roster_fit"]
    board_reentry_required = lineup_resolution["board_reentry_required"]
    board_reentry_reason_codes = list(lineup_resolution["board_reentry_reason_codes"])
    milestone_id = str(roster_context.get("milestone_id", "unknown")).strip() or "unknown"
    if board_reentry_required and not any(
        code == "BOARD_LINEUP_REVIEW_REQUIRED" for code in board_reentry_reason_codes
    ):
        board_reentry_reason_codes.append("BOARD_LINEUP_REVIEW_REQUIRED")
    paste_ready_block = "\n".join(
        [
            "EXPERT_REQUEST_MODE: ADVISORY_EXEC_MEMORY_PACKET",
            f"EXPERT_REQUEST_STATUS: {'ACTION_REQUIRED' if status == 'ACTION_REQUIRED' else 'OPTIONAL'}",
            f"TARGET_EXPERT: {target_expert}",
            f"REQUESTED_DOMAIN: {requested_domain}",
            f"ROSTER_FIT: {roster_fit}",
            f"BOARD_REENTRY_REQUIRED: {'YES' if board_reentry_required else 'NO'}",
            f"BOARD_REENTRY_REASON_CODES: {','.join(board_reentry_reason_codes) if board_reentry_reason_codes else 'none'}",
            f"MILESTONE_ID: {milestone_id}",
            f"TRIGGER_REASON: {trigger_reason}",
            f"QUESTION: {question}",
            f"WHY_BLOCKED: {why_blocked}",
            f"DECISION_DEPENDS_ON: {decision_depends_on}",
            f"SOURCE_ARTIFACTS: {','.join(source_artifacts) if source_artifacts else 'none'}",
            f"REQUESTED_OUTPUT_FORMAT: {requested_output_format}",
            "ADVISORY_NOTE: Generated from current exec memory artifacts; expert input informs Worker/PM judgment and does not override the authority model.",
        ]
    )
    human_brief = (
        f"Status {'ACTION_REQUIRED' if status == 'ACTION_REQUIRED' else 'OPTIONAL'}. "
        f"Requested domain: {requested_domain}. Assigned expert: {target_expert}. "
        f"Roster fit: {roster_fit}. Trigger reason: {trigger_reason}. Question: {question} "
        f"Decision depends on {decision_depends_on}. "
        f"Source artifacts: {','.join(source_artifacts) if source_artifacts else 'none'}. "
        "This request is advisory only and informs Worker/PM judgment without changing decision authority."
    )
    split_surface = _build_advisory_split_surface(
        surface_name="expert_request",
        status="ACTION_REQUIRED" if status == "ACTION_REQUIRED" else "OPTIONAL",
        human_brief=human_brief,
        machine_view_lines=[
            f"TARGET_EXPERT: {target_expert}",
            f"REQUESTED_DOMAIN: {requested_domain}",
            f"ROSTER_FIT: {roster_fit}",
            f"BOARD_REENTRY_REQUIRED: {'YES' if board_reentry_required else 'NO'}",
            f"BOARD_REENTRY_REASON_CODES: {','.join(board_reentry_reason_codes) if board_reentry_reason_codes else 'none'}",
            f"MILESTONE_ID: {milestone_id}",
            f"TRIGGER_REASON: {trigger_reason}",
            f"QUESTION: {question}",
            f"WHY_BLOCKED: {why_blocked}",
            f"DECISION_DEPENDS_ON: {decision_depends_on}",
            f"SOURCE_ARTIFACTS: {','.join(source_artifacts) if source_artifacts else 'none'}",
            f"REQUESTED_OUTPUT_FORMAT: {requested_output_format}",
        ],
    )
    return {
        "advisory": True,
        "status": "ACTION_REQUIRED" if status == "ACTION_REQUIRED" else "OPTIONAL",
        "target_expert": target_expert,
        "requested_domain": requested_domain,
        "roster_fit": roster_fit,
        "board_reentry_required": board_reentry_required,
        "board_reentry_reason_codes": board_reentry_reason_codes,
        "milestone_id": milestone_id,
        "trigger_reason": trigger_reason,
        "question": question,
        "why_blocked": why_blocked,
        "decision_depends_on": decision_depends_on,
        "source_artifacts": source_artifacts,
        "requested_output_format": requested_output_format,
        **split_surface,
        "paste_ready_block": paste_ready_block,
    }


def _build_pm_ceo_research_brief(
    *,
    replanning: dict[str, Any],
    next_round_handoff: dict[str, Any],
    expert_request: dict[str, Any],
    roster_context: dict[str, Any],
) -> dict[str, Any]:
    """Build an advisory PM/CEO delegation brief for tradeoff research."""
    del replanning
    status = str(next_round_handoff.get("status", "CLEAR")).strip().upper() or "CLEAR"
    blockers = [str(code).strip() for code in next_round_handoff.get("primary_blockers", []) if str(code).strip()]
    recommended_checks = [
        str(check).strip()
        for check in next_round_handoff.get("recommended_done_when_checks", [])
        if str(check).strip()
    ]
    delegated_to = "principal"
    supporting_experts: list[str] = []
    target_expert = str(expert_request.get("target_expert", "")).strip()
    if target_expert and target_expert != delegated_to:
        supporting_experts.append(target_expert)

    if status == "ACTION_REQUIRED":
        question = (
            f"What are the top-level tradeoffs, options, and recommended path to address the current blockers ({', '.join(blockers) if blockers else 'none'}) "
            f"and required checks ({', '.join(recommended_checks) if recommended_checks else 'none'}) while preserving the fail-closed control plane?"
        )
        decision_deadline = "Before the next escalation attempt."
        options_required = 3
    else:
        question = (
            "What tradeoffs should PM/CEO review before approving the next planned execution slice, assuming current gates remain green?"
        )
        decision_deadline = "Before the next round kickoff."
        options_required = 2

    required_tradeoff_dimensions = ["impact", "risk", "effort", "maintainability"]
    evidence_required = [
        str(path).strip()
        for path in next_round_handoff.get("artifacts_to_refresh", [])
        if str(path).strip()
    ]
    if not evidence_required:
        evidence_required = [
            str(path).strip()
            for path in expert_request.get("source_artifacts", [])
            if str(path).strip()
        ]
    decision_depends_on = str(expert_request.get("decision_depends_on", "")).strip() or (
        str(next_round_handoff.get("recommended_scope", "")).strip() or "N/A"
    )
    source_artifacts = evidence_required
    lineup_review_reason_codes = [
        str(code).strip().upper()
        for code in expert_request.get("board_reentry_reason_codes", [])
        if str(code).strip()
    ]
    lineup_review_required = bool(expert_request.get("board_reentry_required", False))
    requested_domain = str(expert_request.get("requested_domain", "")).strip().lower()
    candidate_new_domains: list[str] = []
    if requested_domain and requested_domain not in {"unknown", "none"}:
        if "UNKNOWN_EXPERT_DOMAIN" in lineup_review_reason_codes:
            candidate_new_domains.append(requested_domain)
    approved_roster_snapshot = {
        "milestone_id": str(roster_context.get("milestone_id", "unknown")).strip() or "unknown",
        "mandatory_domains": list(roster_context.get("mandatory_domains", [])),
        "optional_domains": list(roster_context.get("optional_domains", [])),
    }

    paste_ready_block = "\n".join(
        [
            "PM_CEO_RESEARCH_BRIEF_MODE: ADVISORY_EXEC_MEMORY_PACKET",
            f"PM_CEO_RESEARCH_STATUS: {'ACTION_REQUIRED' if status == 'ACTION_REQUIRED' else 'OPTIONAL'}",
            f"DELEGATED_TO: {delegated_to}",
            f"SUPPORTING_EXPERTS: {','.join(supporting_experts) if supporting_experts else 'none'}",
            f"QUESTION: {question}",
            f"DECISION_DEPENDS_ON: {decision_depends_on}",
            f"SOURCE_ARTIFACTS: {','.join(source_artifacts) if source_artifacts else 'none'}",
            f"REQUIRED_TRADEOFF_DIMENSIONS: {','.join(required_tradeoff_dimensions)}",
            f"OPTIONS_REQUIRED: {options_required}",
            f"DECISION_DEADLINE: {decision_deadline}",
            f"EVIDENCE_REQUIRED: {','.join(evidence_required) if evidence_required else 'none'}",
            f"LINEUP_REVIEW_REQUIRED: {'YES' if lineup_review_required else 'NO'}",
            f"LINEUP_REVIEW_REASON_CODES: {','.join(lineup_review_reason_codes) if lineup_review_reason_codes else 'none'}",
            f"CANDIDATE_NEW_DOMAINS: {','.join(candidate_new_domains) if candidate_new_domains else 'none'}",
            f"APPROVED_ROSTER_MILESTONE_ID: {approved_roster_snapshot['milestone_id']}",
            "REQUESTED_OUTPUT_FORMAT: Return options, tradeoffs, recommendation, open risks, and artifact references.",
            "ADVISORY_NOTE: Delegated research informs PM/CEO synthesis; PM/CEO retains final decision authority.",
        ]
    )
    human_brief = (
        f"Status {'ACTION_REQUIRED' if status == 'ACTION_REQUIRED' else 'OPTIONAL'}. Delegate to {delegated_to} with question: {question} "
        f"Support from experts: {','.join(supporting_experts) if supporting_experts else 'none'}. "
        f"Decision depends on {decision_depends_on} and requires {options_required} options scored across {', '.join(required_tradeoff_dimensions)}. "
        f"Evidence required: {','.join(evidence_required) if evidence_required else 'none'}. "
        f"Lineup review required: {'YES' if lineup_review_required else 'NO'} "
        f"({','.join(lineup_review_reason_codes) if lineup_review_reason_codes else 'none'}). "
        "This brief is advisory only and informs PM/CEO synthesis without changing decision authority."
    )
    split_surface = _build_advisory_split_surface(
        surface_name="pm_ceo_research_brief",
        status="ACTION_REQUIRED" if status == "ACTION_REQUIRED" else "OPTIONAL",
        human_brief=human_brief,
        machine_view_lines=[
            f"DELEGATED_TO: {delegated_to}",
            f"SUPPORTING_EXPERTS: {','.join(supporting_experts) if supporting_experts else 'none'}",
            f"QUESTION: {question}",
            f"DECISION_DEPENDS_ON: {decision_depends_on}",
            f"SOURCE_ARTIFACTS: {','.join(source_artifacts) if source_artifacts else 'none'}",
            f"REQUIRED_TRADEOFF_DIMENSIONS: {','.join(required_tradeoff_dimensions)}",
            f"OPTIONS_REQUIRED: {options_required}",
            f"DECISION_DEADLINE: {decision_deadline}",
            f"EVIDENCE_REQUIRED: {','.join(evidence_required) if evidence_required else 'none'}",
            f"LINEUP_REVIEW_REQUIRED: {'YES' if lineup_review_required else 'NO'}",
            f"LINEUP_REVIEW_REASON_CODES: {','.join(lineup_review_reason_codes) if lineup_review_reason_codes else 'none'}",
            f"CANDIDATE_NEW_DOMAINS: {','.join(candidate_new_domains) if candidate_new_domains else 'none'}",
            f"APPROVED_ROSTER_MILESTONE_ID: {approved_roster_snapshot['milestone_id']}",
        ],
    )
    return {
        "advisory": True,
        "status": "ACTION_REQUIRED" if status == "ACTION_REQUIRED" else "OPTIONAL",
        "delegated_to": delegated_to,
        "supporting_experts": supporting_experts,
        "question": question,
        "decision_depends_on": decision_depends_on,
        "source_artifacts": source_artifacts,
        "required_tradeoff_dimensions": required_tradeoff_dimensions,
        "options_required": options_required,
        "decision_deadline": decision_deadline,
        "evidence_required": evidence_required,
        "lineup_review_required": lineup_review_required,
        "lineup_review_reason_codes": lineup_review_reason_codes,
        "candidate_new_domains": candidate_new_domains,
        "approved_roster_snapshot": approved_roster_snapshot,
        **split_surface,
        "paste_ready_block": paste_ready_block,
    }


def _build_board_decision_brief(
    *,
    replanning: dict[str, Any],
    next_round_handoff: dict[str, Any],
    expert_request: dict[str, Any],
    pm_ceo_research_brief: dict[str, Any],
    roster_context: dict[str, Any],
) -> dict[str, Any]:
    """Build an advisory board-style decision brief from existing handoff evidence."""
    status = str(pm_ceo_research_brief.get("status", "OPTIONAL")).strip().upper() or "OPTIONAL"
    blockers = [
        str(code).strip()
        for code in next_round_handoff.get("primary_blockers", [])
        if str(code).strip()
    ]
    replanning_gaps = [
        gap for gap in replanning.get("blocking_gaps", []) if isinstance(gap, dict)
    ]

    source_artifacts: list[str] = []
    for path in replanning.get("recommended_artifacts_to_refresh", []):
        text = str(path).strip()
        if text and text not in source_artifacts:
            source_artifacts.append(text)
    for gap in replanning_gaps:
        text = str(gap.get("source_path", "")).strip()
        if text and text not in source_artifacts:
            source_artifacts.append(text)
    for path in pm_ceo_research_brief.get("source_artifacts", []):
        text = str(path).strip()
        if text and text not in source_artifacts:
            source_artifacts.append(text)
    for path in expert_request.get("source_artifacts", []):
        text = str(path).strip()
        if text and text not in source_artifacts:
            source_artifacts.append(text)

    observed_go_action = str(next_round_handoff.get("observed_go_action", "UNKNOWN")).strip().upper() or "UNKNOWN"
    decision_topic = str(pm_ceo_research_brief.get("question", "")).strip() or (
        str(next_round_handoff.get("recommended_intent", "")).strip() or "Review current execution direction."
    )
    decision_deadline = str(pm_ceo_research_brief.get("decision_deadline", "")).strip() or "Before the next round kickoff."

    if observed_go_action in {"HOLD", "REFRAME"} or any(code.startswith("c") for code in blockers):
        decision_class = "ONE_WAY"
        risk_tier = "HIGH"
    elif blockers:
        decision_class = "TWO_WAY"
        risk_tier = "MEDIUM"
    else:
        decision_class = "TWO_WAY"
        risk_tier = "LOW"

    ceo_lens = {
        "business_upside": str(next_round_handoff.get("recommended_intent", "")).strip() or "Maintain delivery confidence and protect escalation quality.",
        "strategic_risk": "High" if risk_tier == "HIGH" else "Moderate" if risk_tier == "MEDIUM" else "Low",
        "reversibility": "Harder to reverse" if decision_class == "ONE_WAY" else "Reversible with bounded blast radius",
        "timing_priority": decision_deadline,
    }
    cto_lens = {
        "architecture_coherence": "Prefer minimal change that preserves the fail-closed control plane.",
        "interface_stability": "Do not widen interfaces or contracts until current blockers are resolved.",
        "maintenance_impact": "Choose the option with the smallest long-term control-plane complexity increase.",
        "platform_debt_impact": "Avoid new architecture or policy layers for this decision path.",
    }
    coo_lens = {
        "execution_load": "Focused remediation" if blockers else "Normal execution load",
        "dependency_coordination": "Requires PM coordination across Worker, Auditor, and expert lanes" if blockers else "No additional coordination required",
        "rollout_readiness": "Not rollout-ready" if observed_go_action in {"HOLD", "REFRAME"} else "Operationally ready for next slice",
        "operational_burden": "Elevated due to blocker resolution and evidence refresh" if blockers else "Routine",
    }

    open_risks: list[str] = []
    for gap in replanning_gaps:
        source = str(gap.get("source", "unknown")).strip() or "unknown"
        code = str(gap.get("code", "unknown")).strip() or "unknown"
        detail = str(gap.get("detail", "pending clarification")).strip() or "pending clarification"
        risk = f"[{source}] {code}: {detail}"
        if risk not in open_risks:
            open_risks.append(risk)
    if not open_risks:
        open_risks = blockers or ["none"]

    expert_lens = {
        "target_expert": str(expert_request.get("target_expert", "")).strip() or "none",
        "supporting_experts": list(pm_ceo_research_brief.get("supporting_experts", [])),
        "specialist_question": str(expert_request.get("question", "")).strip() or "none",
        "unknowns": open_risks if open_risks != ["none"] else [],
    }
    lineup_decision_needed = bool(pm_ceo_research_brief.get("lineup_review_required", False))
    board_reentry_reason_codes = [
        str(code).strip().upper()
        for code in pm_ceo_research_brief.get("lineup_review_reason_codes", [])
        if str(code).strip()
    ]
    lineup_gap_domains = [
        str(domain).strip().lower()
        for domain in pm_ceo_research_brief.get("candidate_new_domains", [])
        if str(domain).strip()
    ]
    approved_roster_snapshot = {
        "milestone_id": str(roster_context.get("milestone_id", "unknown")).strip() or "unknown",
        "mandatory_domains": list(roster_context.get("mandatory_domains", [])),
        "optional_domains": list(roster_context.get("optional_domains", [])),
    }
    reintroduce_board_when = [
        str(trigger).strip().upper()
        for trigger in roster_context.get("board_reentry_triggers", [])
        if str(trigger).strip()
    ] or [
        "UNKNOWN_EXPERT_DOMAIN",
        "ROSTER_MISSING",
        "EXPERT_DISAGREEMENT",
        "MILESTONE_GATE_REVIEW",
    ]

    if status == "ACTION_REQUIRED":
        recommended_option = str(next_round_handoff.get("next_replan_recommendation", "")).strip() or (
            "Refresh the cited artifacts, use the PM/CEO research brief and expert input to narrow options, and prepare the CEO decision before the next escalation attempt."
        )
    else:
        recommended_option = (
            "Proceed with the next planned execution slice while keeping this board brief as an advisory review packet."
        )

    paste_ready_block = "\n".join(
        [
            "BOARD_DECISION_BRIEF_MODE: ADVISORY_EXEC_MEMORY_PACKET",
            f"BOARD_DECISION_STATUS: {status}",
            f"DECISION_TOPIC: {decision_topic}",
            f"DECISION_DEADLINE: {decision_deadline}",
            f"DECISION_CLASS: {decision_class}",
            f"RISK_TIER: {risk_tier}",
            f"CEO_LENS: business_upside={ceo_lens['business_upside']} | strategic_risk={ceo_lens['strategic_risk']} | reversibility={ceo_lens['reversibility']} | timing_priority={ceo_lens['timing_priority']}",
            f"CTO_LENS: architecture_coherence={cto_lens['architecture_coherence']} | interface_stability={cto_lens['interface_stability']} | maintenance_impact={cto_lens['maintenance_impact']} | platform_debt_impact={cto_lens['platform_debt_impact']}",
            f"COO_LENS: execution_load={coo_lens['execution_load']} | dependency_coordination={coo_lens['dependency_coordination']} | rollout_readiness={coo_lens['rollout_readiness']} | operational_burden={coo_lens['operational_burden']}",
            f"EXPERT_LENS: target_expert={expert_lens['target_expert']} | supporting_experts={','.join(expert_lens['supporting_experts']) if expert_lens['supporting_experts'] else 'none'} | unknowns={','.join(expert_lens['unknowns']) if expert_lens['unknowns'] else 'none'}",
            f"LINEUP_DECISION_NEEDED: {'YES' if lineup_decision_needed else 'NO'}",
            f"LINEUP_GAP_DOMAINS: {','.join(lineup_gap_domains) if lineup_gap_domains else 'none'}",
            f"BOARD_REENTRY_REASON_CODES: {','.join(board_reentry_reason_codes) if board_reentry_reason_codes else 'none'}",
            f"APPROVED_ROSTER_MILESTONE_ID: {approved_roster_snapshot['milestone_id']}",
            f"REINTRODUCE_BOARD_WHEN: {','.join(reintroduce_board_when)}",
            f"RECOMMENDED_OPTION: {recommended_option}",
            f"OPEN_RISKS: {' || '.join(open_risks) if open_risks else 'none'}",
            f"SOURCE_ARTIFACTS: {','.join(source_artifacts) if source_artifacts else 'none'}",
            "ADVISORY_NOTE: Generated from existing exec memory artifacts; board-style lenses are advisory only and do not change decision authority.",
        ]
    )
    human_brief = (
        f"Status {status}. Decision topic: {decision_topic} Deadline: {decision_deadline}. "
        f"Treat this as a {decision_class} decision at {risk_tier} risk. Recommended option: {recommended_option} "
        f"Lineup decision needed: {'YES' if lineup_decision_needed else 'NO'}. "
        f"Open risks: {' | '.join(open_risks) if open_risks else 'none'}. "
        "This board-style brief is advisory only and does not change the existing decision authority model."
    )
    split_surface = _build_advisory_split_surface(
        surface_name="board_decision_brief",
        status=status,
        human_brief=human_brief,
        machine_view_lines=[
            f"DECISION_TOPIC: {decision_topic}",
            f"DECISION_DEADLINE: {decision_deadline}",
            f"DECISION_CLASS: {decision_class}",
            f"RISK_TIER: {risk_tier}",
            f"RECOMMENDED_OPTION: {recommended_option}",
            f"TARGET_EXPERT: {expert_lens['target_expert']}",
            f"SUPPORTING_EXPERTS: {','.join(expert_lens['supporting_experts']) if expert_lens['supporting_experts'] else 'none'}",
            f"LINEUP_DECISION_NEEDED: {'YES' if lineup_decision_needed else 'NO'}",
            f"LINEUP_GAP_DOMAINS: {','.join(lineup_gap_domains) if lineup_gap_domains else 'none'}",
            f"BOARD_REENTRY_REASON_CODES: {','.join(board_reentry_reason_codes) if board_reentry_reason_codes else 'none'}",
            f"APPROVED_ROSTER_MILESTONE_ID: {approved_roster_snapshot['milestone_id']}",
            f"REINTRODUCE_BOARD_WHEN: {','.join(reintroduce_board_when)}",
            f"SOURCE_ARTIFACTS: {','.join(source_artifacts) if source_artifacts else 'none'}",
            f"OPEN_RISKS: {' || '.join(open_risks) if open_risks else 'none'}",
        ],
    )
    return {
        "advisory": True,
        "status": status,
        "decision_topic": decision_topic,
        "decision_deadline": decision_deadline,
        "decision_class": decision_class,
        "risk_tier": risk_tier,
        "source_artifacts": source_artifacts,
        "ceo_lens": ceo_lens,
        "cto_lens": cto_lens,
        "coo_lens": coo_lens,
        "expert_lens": expert_lens,
        "lineup_decision_needed": lineup_decision_needed,
        "lineup_gap_domains": lineup_gap_domains,
        "board_reentry_reason_codes": board_reentry_reason_codes,
        "approved_roster_snapshot": approved_roster_snapshot,
        "reintroduce_board_when": reintroduce_board_when,
        "recommended_option": recommended_option,
        "open_risks": open_risks,
        **split_surface,
        "paste_ready_block": paste_ready_block,
    }


def _build_automation_uncertainty_status(
    *,
    replanning: dict[str, Any],
    next_round_handoff: dict[str, Any],
    expert_request: dict[str, Any],
    pm_ceo_research_brief: dict[str, Any],
    board_decision_brief: dict[str, Any],
    roster_context: dict[str, Any],
) -> dict[str, Any]:
    """Build a lean advisory summary of where machine-only execution should stop."""
    replanning_status = str(replanning.get("status", "CLEAR")).strip().upper() or "CLEAR"
    handoff_status = str(next_round_handoff.get("status", "CLEAR")).strip().upper() or "CLEAR"
    expert_status = str(expert_request.get("status", "OPTIONAL")).strip().upper() or "OPTIONAL"
    research_status = str(pm_ceo_research_brief.get("status", "OPTIONAL")).strip().upper() or "OPTIONAL"
    decision_class = str(board_decision_brief.get("decision_class", "TWO_WAY")).strip().upper() or "TWO_WAY"
    risk_tier = str(board_decision_brief.get("risk_tier", "LOW")).strip().upper() or "LOW"
    roster_status = str(roster_context.get("status", "ROSTER_MISSING")).strip().upper() or "ROSTER_MISSING"
    roster_fit = str(expert_request.get("roster_fit", "ROSTER_MISSING")).strip().upper() or "ROSTER_MISSING"
    board_reentry_reason_codes = [
        str(code).strip().upper()
        for code in expert_request.get("board_reentry_reason_codes", [])
        if str(code).strip()
    ]
    board_reentry_required = bool(
        expert_request.get("board_reentry_required", False)
        or pm_ceo_research_brief.get("lineup_review_required", False)
        or board_decision_brief.get("lineup_decision_needed", False)
    )

    if roster_status != "ROSTER_READY":
        expert_lineup_status = "ROSTER_MISSING"
        expert_memory_status = "MISSING"
    elif roster_fit == "UNKNOWN_EXPERT_DOMAIN":
        expert_lineup_status = "UNKNOWN_EXPERT_DOMAIN"
        expert_memory_status = "DRIFT"
    else:
        expert_lineup_status = "ROSTER_READY"
        expert_memory_status = "CONSISTENT"

    board_memory_status = (
        "BOARD_LINEUP_REVIEW_REQUIRED" if board_reentry_required else "CONSISTENT"
    )

    blocking_gaps = [
        gap for gap in replanning.get("blocking_gaps", []) if isinstance(gap, dict)
    ]
    has_manual_check = any(
        str(gap.get("detail", "")).startswith("Manual check required:")
        for gap in blocking_gaps
    )

    reason_codes: list[str] = []
    reason_details: list[str] = []

    if replanning_status == "ACTION_REQUIRED":
        reason_codes.append("ACTIVE_BLOCKERS")
        reason_details.append(
            f"Replanning still shows {replanning.get('blocking_gap_count', 0)} blocking gaps."
        )
    if has_manual_check:
        reason_codes.append("MANUAL_EVIDENCE_REQUIRED")
        reason_details.append(
            "Manual UX or signoff evidence is still required before machine-only continuation."
        )
    if handoff_status == "ACTION_REQUIRED":
        reason_codes.append("HUMAN_REVIEW_RECOMMENDED")
        reason_details.append(
            "Next-round handoff is not yet clear enough for machine-only continuation."
        )
    if research_status == "ACTION_REQUIRED":
        reason_codes.append("TRADEOFF_RESEARCH_REQUIRED")
        reason_details.append(
            "PM/CEO tradeoff synthesis is still required before relying on machine-only advice."
        )
    if expert_status == "ACTION_REQUIRED":
        reason_codes.append("EXPERT_INPUT_REQUIRED")
        reason_details.append(
            f"Specialist input is requested from {expert_request.get('target_expert', 'the named expert')}."
        )
    if expert_lineup_status == "ROSTER_MISSING":
        reason_codes.append("ROSTER_MISSING")
        reason_details.append(
            "Milestone expert roster file is missing or empty; lineup assignment cannot be verified."
        )
    if expert_lineup_status == "UNKNOWN_EXPERT_DOMAIN":
        reason_codes.append("UNKNOWN_EXPERT_DOMAIN")
        reason_details.append(
            f"Requested domain {expert_request.get('requested_domain', 'unknown')} is not present in the approved milestone roster."
        )
    if board_reentry_required:
        reason_codes.append("BOARD_LINEUP_REVIEW_REQUIRED")
        reason_details.append(
            "Board reentry is required to approve lineup changes before escalation-critical expert assignment."
        )

    deduped_reason_codes: list[str] = []
    for code in reason_codes:
        if code not in deduped_reason_codes:
            deduped_reason_codes.append(code)
    reason_codes = deduped_reason_codes

    human_help_needed = (
        has_manual_check
        or handoff_status == "ACTION_REQUIRED"
        or research_status == "ACTION_REQUIRED"
        or board_reentry_required
    )
    expert_help_needed = expert_status == "ACTION_REQUIRED"

    if human_help_needed or expert_help_needed:
        status = "ACTION_REQUIRED"
        machine_confidence = "LIMITED"
        evidence_status = "INSUFFICIENT"
    else:
        status = "CLEAR"
        machine_confidence = "SUFFICIENT"
        evidence_status = "SUFFICIENT"

    if board_reentry_required or research_status == "ACTION_REQUIRED" or has_manual_check:
        human_help_lane = "PM_CEO"
    elif handoff_status == "ACTION_REQUIRED" or (risk_tier == "HIGH" and decision_class == "ONE_WAY"):
        human_help_lane = "PM"
    else:
        human_help_lane = "NONE"

    target_expert = str(expert_request.get("target_expert", "none")).strip() or "none"
    if not expert_help_needed:
        target_expert = "none"

    retirement_criteria = [
        "replanning.status=CLEAR",
        "next_round_handoff.status=CLEAR",
        "pm_ceo_research_brief.status=OPTIONAL",
        "expert_request.status=OPTIONAL",
        "manual evidence or UX confirmation captured when required",
    ]

    machine_safe_to_continue = (
        status == "CLEAR"
        and not human_help_needed
        and not expert_help_needed
    )

    return {
        "advisory": True,
        "status": status,
        "machine_confidence": machine_confidence,
        "evidence_status": evidence_status,
        "machine_safe_to_continue": machine_safe_to_continue,
        "human_help_needed": human_help_needed,
        "human_help_lane": human_help_lane,
        "expert_help_needed": expert_help_needed,
        "target_expert": target_expert,
        "expert_lineup_status": expert_lineup_status,
        "expert_memory_status": expert_memory_status,
        "board_memory_status": board_memory_status,
        "board_reentry_required": board_reentry_required,
        "board_reentry_reason_codes": board_reentry_reason_codes,
        "memory_reason_codes": [
            code
            for code in ["ROSTER_MISSING", "UNKNOWN_EXPERT_DOMAIN", "BOARD_LINEUP_REVIEW_REQUIRED"]
            if code in reason_codes
        ],
        "reason_codes": reason_codes,
        "reason_details": reason_details,
        "decision_class": decision_class,
        "risk_tier": risk_tier,
        "boundary_registry": AUTOMATION_BOUNDARY_REGISTRY_PATH,
        "retirement_criteria": retirement_criteria,
    }


def _build_daily_pm_summary(
    loop_summary: dict | None,
    dossier: dict | None,
    calibration: dict | None,
    decision_log_text: str,
) -> str:
    """Build PM-level daily summary."""
    lines = []

    # Working context
    lines.append("## Working Context")
    lines.append(_build_working_summary(loop_summary))
    lines.append("")

    # Issues
    lines.append("## Issues")
    lines.append(_build_issue_summary(dossier, calibration))
    lines.append("")

    # Recent decisions (last 500 chars)
    if decision_log_text:
        recent = decision_log_text[-500:] if len(decision_log_text) > 500 else decision_log_text
        lines.append("## Recent Decisions")
        lines.append(recent)

    return "\n".join(lines)


def _build_weekly_ceo_summary(
    go_signal_text: str,
    dossier: dict | None,
    calibration: dict | None,
) -> str:
    """Build CEO-level weekly summary."""
    lines = []

    # Go signal (last 300 chars)
    if go_signal_text:
        recent = go_signal_text[-300:] if len(go_signal_text) > 300 else go_signal_text
        lines.append("## CEO Go Signal")
        lines.append(recent)
        lines.append("")

    # Promotion status
    if dossier:
        criteria = dossier.get("promotion_criteria", {})
        met_count = sum(1 for v in criteria.values() if isinstance(v, dict) and v.get("met") is True)
        total_count = len([k for k in criteria.keys() if k != "c1_24b_close"])
        lines.append("## Promotion Status")
        lines.append(f"Criteria met: {met_count}/{total_count}")
        lines.append("")

    # Calibration summary
    if calibration:
        totals = calibration.get("totals", {})
        items = totals.get("items_reviewed", 0)
        lines.append("## Auditor Calibration")
        lines.append(f"Items reviewed: {items}")

    return "\n".join(lines)


def _build_retrieval_namespaces(
    context_dir: Path,
    loop_summary: dict | None,
    dossier: dict | None,
    calibration: dict | None,
    go_signal_path: Path,
    decision_log_path: Path,
    roster_context: dict[str, Any],
    skill_activation: dict[str, Any] | None,
) -> dict[str, list[dict]]:
    """Build retrieval namespaces with source bindings."""
    namespaces: dict[str, list[dict]] = {
        "governance": [],
        "operations": [],
        "risk": [],
        "roadmap": [],
    }

    # Governance: decision log, go signal, skill activation
    if decision_log_path.exists():
        namespaces["governance"].append({
            "source": str(decision_log_path.relative_to(context_dir.parent)),
            "type": "markdown",
            "description": "Decision log"
        })
    if go_signal_path.exists():
        namespaces["governance"].append({
            "source": str(go_signal_path.relative_to(context_dir.parent)),
            "type": "markdown",
            "description": "CEO go signal"
        })
    if bool(roster_context.get("present", False)):
        namespaces["governance"].append({
            "source": str(roster_context.get("path", MILESTONE_EXPERT_ROSTER_PATH)),
            "type": "json",
            "description": "Milestone expert roster"
        })
    if skill_activation and skill_activation.get("status") in {"ok", "degraded"}:
        namespaces["governance"].append({
            "source": ".sop_config.yaml",
            "type": "yaml",
            "description": "Project skill configuration"
        })
        namespaces["governance"].append({
            "source": "extension_allowlist.yaml",
            "type": "yaml",
            "description": "Global skill allowlist"
        })
        namespaces["governance"].append({
            "source": "skills/registry.yaml",
            "type": "yaml",
            "description": "Skills registry"
        })

    # Operations: loop summary
    if loop_summary:
        namespaces["operations"].append({
            "source": "docs/context/loop_cycle_summary_latest.json",
            "type": "json",
            "description": "Loop cycle summary"
        })

    # Risk: auditor reports
    if calibration:
        namespaces["risk"].append({
            "source": "docs/context/auditor_calibration_report.json",
            "type": "json",
            "description": "Auditor calibration report"
        })
    if dossier:
        namespaces["risk"].append({
            "source": "docs/context/auditor_promotion_dossier.json",
            "type": "json",
            "description": "Auditor promotion dossier"
        })

    # Roadmap: promotion dossier (also roadmap-relevant)
    if dossier:
        namespaces["roadmap"].append({
            "source": "docs/context/auditor_promotion_dossier.json",
            "type": "json",
            "description": "Promotion criteria"
        })

    return namespaces


def _build_semantic_claims(
    working_summary: str,
    issue_summary: str,
    weekly_ceo_summary: str,
    loop_summary_path: Path,
    dossier_path: Path,
    calibration_path: Path,
    source_bindings: list[str],
) -> list[dict[str, str]]:
    """Build deterministic claim-to-source bindings for semantic fidelity checks."""
    claims: list[dict[str, str]] = []
    claim_index = 1

    loop_source = str(loop_summary_path)
    dossier_source = str(dossier_path)
    calibration_source = str(calibration_path)

    def add_claim(text: str, source_path: str) -> None:
        nonlocal claim_index
        if not text or source_path not in source_bindings:
            return
        claims.append(
            {
                "claim_id": f"SC{claim_index:03d}",
                "text": text,
                "source_path": source_path,
            }
        )
        claim_index += 1

    for line in working_summary.splitlines():
        if line.startswith("Final result:") or line.startswith("Steps total:"):
            add_claim(line, loop_source)

    for line in issue_summary.splitlines():
        if line.startswith("Auditor findings:"):
            add_claim(line, calibration_source)
        elif line.startswith("Promotion blockers:"):
            add_claim(line, dossier_source)

    for line in weekly_ceo_summary.splitlines():
        if line.startswith("Items reviewed:"):
            add_claim(line, calibration_source)

    return claims


def main() -> int:
    parser = argparse.ArgumentParser(description="Build exec memory packet")
    parser.add_argument("--context-dir", default="docs/context", help="Context directory")
    parser.add_argument(
        "--loop-summary-json",
        default="docs/context/loop_cycle_summary_latest.json",
        help="Loop cycle summary JSON"
    )
    parser.add_argument(
        "--dossier-json",
        default="docs/context/auditor_promotion_dossier.json",
        help="Auditor promotion dossier JSON"
    )
    parser.add_argument(
        "--calibration-json",
        default="docs/context/auditor_calibration_report.json",
        help="Auditor calibration report JSON"
    )
    parser.add_argument(
        "--go-signal-md",
        default="docs/context/ceo_go_signal.md",
        help="CEO go signal markdown"
    )
    parser.add_argument(
        "--decision-log-md",
        default="docs/decision log.md",
        help="Decision log markdown"
    )
    parser.add_argument("--pm-budget-tokens", type=int, default=3000, help="PM context token budget")
    parser.add_argument("--ceo-budget-tokens", type=int, default=1800, help="CEO context token budget")
    parser.add_argument(
        "--output-json",
        default="docs/context/exec_memory_packet_latest.json",
        help="Output JSON path"
    )
    parser.add_argument(
        "--output-md",
        default="docs/context/exec_memory_packet_latest.md",
        help="Output markdown path"
    )
    parser.add_argument(
        "--status-json",
        default="docs/context/exec_memory_packet_build_status_latest.json",
        help="Build status JSON path",
    )
    parser.add_argument(
        "--allow-degraded-output",
        action="store_true",
        help=(
            "When critical inputs are missing or invalid, still write the requested "
            "outputs as a non-authoritative degraded preview and return exit code 2."
        ),
    )
    args = parser.parse_args()

    # Resolve paths
    context_dir = Path(args.context_dir)
    loop_summary_path = Path(args.loop_summary_json)
    dossier_path = Path(args.dossier_json)
    calibration_path = Path(args.calibration_json)
    go_signal_path = Path(args.go_signal_md)
    decision_log_path = Path(args.decision_log_md)
    output_json_path = Path(args.output_json)
    output_md_path = Path(args.output_md)
    status_json_path = Path(args.status_json)
    generated_at_utc = _now_utc_iso()

    # Resolve repo root from decision_log_path
    repo_root = decision_log_path.parent.parent.resolve()

    input_status: dict[str, list[dict[str, str]]] = {
        "critical": [],
        "important": [],
        "optional": [],
    }

    try:
        loop_summary, error = safe_load_json_object(loop_summary_path)
        _append_input_status(input_status, path=loop_summary_path, loaded=loop_summary is not None)

        dossier, error = safe_load_json_object(dossier_path)
        _append_input_status(input_status, path=dossier_path, loaded=dossier is not None)

        calibration, error = safe_load_json_object(calibration_path)
        _append_input_status(input_status, path=calibration_path, loaded=calibration is not None)

        go_signal_text = _load_text_safe(go_signal_path)
        _append_input_status(input_status, path=go_signal_path, loaded=bool(go_signal_text))

        decision_log_text = _load_text_safe(decision_log_path)
        _append_input_status(input_status, path=decision_log_path, loaded=bool(decision_log_text))

        # Load skill activation inputs (fail-soft)
        sop_config_path = repo_root / ".sop_config.yaml"
        allowlist_path = repo_root / "extension_allowlist.yaml"
        registry_path = repo_root / "skills" / "registry.yaml"
        _append_input_status(input_status, path=sop_config_path, loaded=sop_config_path.exists())
        _append_input_status(input_status, path=allowlist_path, loaded=allowlist_path.exists())
        _append_input_status(input_status, path=registry_path, loaded=registry_path.exists())
    except Exception as e:
        print(f"ERROR: Failed to load inputs: {e}", file=sys.stderr)
        return 2

    critical_failures = _critical_input_failures(input_status)
    degraded_output_allowed = (
        args.allow_degraded_output
        and not _is_authoritative_latest_path(output_json_path)
        and not _is_authoritative_latest_path(output_md_path)
    )
    if critical_failures and not degraded_output_allowed:
        failed_names = ", ".join(item["file"] for item in critical_failures)
        try:
            _write_build_status(
                path=status_json_path,
                generated_at_utc=generated_at_utc,
                output_json_path=output_json_path,
                output_md_path=output_md_path,
                input_status=input_status,
                critical_failures=critical_failures,
                authoritative_latest_written=False,
                degraded_preview_written=False,
                exit_code=2,
                reason="critical_inputs_failed",
            )
        except Exception as exc:
            print(f"ERROR: Failed to write build status: {exc}", file=sys.stderr)
        print(f"ERROR: Critical inputs failed to load: {failed_names}", file=sys.stderr)
        return 2

    # Resolve active skills (fail-soft)
    project_name = "quant_current_scope"  # Default, could be read from config
    try:
        sop_config_path = repo_root / ".sop_config.yaml"
        if sop_config_path.exists():
            import yaml
            with sop_config_path.open("r", encoding="utf-8") as f:
                sop_config = yaml.safe_load(f)
                if isinstance(sop_config, dict):
                    project_name = sop_config.get("project_name", project_name)
    except Exception:
        pass  # Use default project_name

    skill_activation = None
    try:
        skill_activation = resolve_active_skills(repo_root, project_name)
    except Exception as e:
        print(f"WARNING: Failed to resolve active skills: {e}", file=sys.stderr)
        skill_activation = {
            "status": "failed",
            "skills": [],
            "warnings": [],
            "errors": [str(e)],
        }

    # Build hierarchical summaries
    working_summary = _build_working_summary(loop_summary)
    issue_summary = _build_issue_summary(dossier, calibration)
    daily_pm_summary = _build_daily_pm_summary(
        loop_summary, dossier, calibration, decision_log_text
    )
    weekly_ceo_summary = _build_weekly_ceo_summary(
        go_signal_text, dossier, calibration
    )
    milestone_expert_roster = _load_milestone_expert_roster(context_dir)
    replanning = _build_replanning_summary(
        loop_summary=loop_summary,
        dossier=dossier,
        calibration=calibration,
        go_signal_text=go_signal_text,
    )
    next_round_handoff = _build_next_round_handoff(replanning)
    expert_request = _build_expert_request(
        replanning=replanning,
        next_round_handoff=next_round_handoff,
        roster_context=milestone_expert_roster,
    )
    pm_ceo_research_brief = _build_pm_ceo_research_brief(
        replanning=replanning,
        next_round_handoff=next_round_handoff,
        expert_request=expert_request,
        roster_context=milestone_expert_roster,
    )
    board_decision_brief = _build_board_decision_brief(
        replanning=replanning,
        next_round_handoff=next_round_handoff,
        expert_request=expert_request,
        pm_ceo_research_brief=pm_ceo_research_brief,
        roster_context=milestone_expert_roster,
    )

    # Build retrieval namespaces
    retrieval_namespaces = _build_retrieval_namespaces(
        context_dir,
        loop_summary,
        dossier,
        calibration,
        go_signal_path,
        decision_log_path,
        milestone_expert_roster,
        skill_activation,
    )
    memory_tier_contract = build_memory_tier_snapshot(
        family_ids=BUILD_PACKET_MEMORY_FAMILIES,
        cold_fallback_ids=BUILD_PACKET_COLD_FALLBACK_FAMILIES,
    )
    compaction_retention_contract = build_compaction_policy_snapshot()
    memory_tier_bindings = {
        "inputs": bind_memory_tier_paths(
            {
                "loop_cycle_summary": loop_summary_path,
                "auditor_promotion_dossier": dossier_path,
                "auditor_calibration_report": calibration_path,
                "ceo_go_signal": go_signal_path,
                "decision_log": decision_log_path,
                "milestone_expert_roster": context_dir / "milestone_expert_roster_latest.json",
                "project_skill_config": repo_root / ".sop_config.yaml",
                "extension_allowlist": repo_root / "extension_allowlist.yaml",
                "skill_registry": repo_root / "skills" / "registry.yaml",
            }
        ),
        "outputs": bind_memory_tier_paths(
            {
                "exec_memory_packet": output_json_path,
                "exec_memory_build_status": status_json_path,
                "next_round_handoff": context_dir / "next_round_handoff_latest.json",
                "expert_request": context_dir / "expert_request_latest.json",
                "pm_ceo_research_brief": context_dir / "pm_ceo_research_brief_latest.json",
                "board_decision_brief": context_dir / "board_decision_brief_latest.json",
                "skill_activation": context_dir / "skill_activation_latest.json",
            }
        ),
    }

    # Token budget calculation
    pm_context = daily_pm_summary
    ceo_context = weekly_ceo_summary

    pm_tokens = _estimate_tokens(pm_context)
    ceo_tokens = _estimate_tokens(ceo_context)

    pm_budget_ok = pm_tokens <= args.pm_budget_tokens
    ceo_budget_ok = ceo_tokens <= args.ceo_budget_tokens

    # Truncate if over budget
    if not pm_budget_ok:
        pm_context, pm_tokens = _truncate_to_budget(pm_context, args.pm_budget_tokens)
    if not ceo_budget_ok:
        ceo_context, ceo_tokens = _truncate_to_budget(ceo_context, args.ceo_budget_tokens)

    # Build source bindings
    source_bindings = []
    if loop_summary_path.exists():
        source_bindings.append(str(loop_summary_path))
    if dossier_path.exists():
        source_bindings.append(str(dossier_path))
    if calibration_path.exists():
        source_bindings.append(str(calibration_path))
    if go_signal_path.exists():
        source_bindings.append(str(go_signal_path))
    if decision_log_path.exists():
        source_bindings.append(str(decision_log_path))
    if bool(milestone_expert_roster.get("present", False)):
        source_bindings.append(str(milestone_expert_roster["path"]))
    if skill_activation and skill_activation.get("status") in {"ok", "degraded"}:
        source_bindings.append(str(repo_root / ".sop_config.yaml"))
        source_bindings.append(str(repo_root / "extension_allowlist.yaml"))
        source_bindings.append(str(repo_root / "skills" / "registry.yaml"))

    semantic_claims = _build_semantic_claims(
        working_summary=working_summary,
        issue_summary=issue_summary,
        weekly_ceo_summary=weekly_ceo_summary,
        loop_summary_path=loop_summary_path,
        dossier_path=dossier_path,
        calibration_path=calibration_path,
        source_bindings=source_bindings,
    )
    automation_uncertainty_status = _build_automation_uncertainty_status(
        replanning=replanning,
        next_round_handoff=next_round_handoff,
        expert_request=expert_request,
        pm_ceo_research_brief=pm_ceo_research_brief,
        board_decision_brief=board_decision_brief,
        roster_context=milestone_expert_roster,
    )

    # Build JSON packet
    packet = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "inputs": {
            "loop_summary": str(loop_summary_path) if loop_summary_path.exists() else None,
            "dossier": str(dossier_path) if dossier_path.exists() else None,
            "calibration": str(calibration_path) if calibration_path.exists() else None,
            "go_signal": str(go_signal_path) if go_signal_path.exists() else None,
            "decision_log": str(decision_log_path) if decision_log_path.exists() else None,
            "milestone_expert_roster": milestone_expert_roster["path"],
            "sop_config": str(repo_root / ".sop_config.yaml") if (repo_root / ".sop_config.yaml").exists() else None,
            "extension_allowlist": str(repo_root / "extension_allowlist.yaml") if (repo_root / "extension_allowlist.yaml").exists() else None,
            "skill_registry": str(repo_root / "skills" / "registry.yaml") if (repo_root / "skills" / "registry.yaml").exists() else None,
        },
        "input_status": input_status,
        "token_budget": {
            "pm_budget": args.pm_budget_tokens,
            "ceo_budget": args.ceo_budget_tokens,
            "pm_actual": pm_tokens,
            "ceo_actual": ceo_tokens,
            "pm_budget_ok": pm_budget_ok,
            "ceo_budget_ok": ceo_budget_ok,
        },
        "memory_tier_contract": memory_tier_contract,
        "compaction_retention_contract": compaction_retention_contract,
        "memory_tier_bindings": memory_tier_bindings,
        "hierarchical_summary": {
            "working_summary": working_summary,
            "issue_summary": issue_summary,
            "daily_pm_summary": pm_context,
            "weekly_ceo_summary": ceo_context,
        },
        "replanning": replanning,
        "next_round_handoff": next_round_handoff,
        "expert_request": expert_request,
        "pm_ceo_research_brief": pm_ceo_research_brief,
        "board_decision_brief": board_decision_brief,
        "automation_uncertainty_status": automation_uncertainty_status,
        "milestone_expert_roster_status": milestone_expert_roster,
        "skill_activation": skill_activation,
        "retrieval_namespaces": retrieval_namespaces,
        "source_bindings": source_bindings,
        "semantic_claims": semantic_claims,
    }

    # Write JSON
    try:
        _atomic_write_text(output_json_path, json.dumps(packet, indent=2))
    except Exception as e:
        try:
            _write_build_status(
                path=status_json_path,
                generated_at_utc=generated_at_utc,
                output_json_path=output_json_path,
                output_md_path=output_md_path,
                input_status=input_status,
                critical_failures=critical_failures,
                authoritative_latest_written=False,
                degraded_preview_written=False,
                exit_code=2,
                reason="write_json_failed",
            )
        except Exception as status_exc:
            print(f"ERROR: Failed to write build status: {status_exc}", file=sys.stderr)
        print(f"ERROR: Failed to write JSON: {e}", file=sys.stderr)
        return 2

    # Build markdown companion
    md_lines = [
        "# Exec Memory Packet",
        "",
        f"**Generated:** {packet['generated_at_utc']}",
        f"**Schema:** {packet['schema_version']}",
        "",
        "## Token Budget",
        "",
        "| Context | Budget | Actual | Status |",
        "|---------|--------|--------|--------|",
        f"| PM | {args.pm_budget_tokens} | {pm_tokens} | {'[OK] OK' if pm_budget_ok else '[FAIL] OVER'} |",
        f"| CEO | {args.ceo_budget_tokens} | {ceo_tokens} | {'[OK] OK' if ceo_budget_ok else '[FAIL] OVER'} |",
        "",
        "## Source Bindings",
        "",
    ]

    for src in source_bindings:
        md_lines.append(f"- {src}")

    md_lines.extend([
        "",
        "## Automation Uncertainty Status",
        "",
        f"- Status: {automation_uncertainty_status['status']}",
        f"- MachineConfidence: {automation_uncertainty_status['machine_confidence']}",
        f"- EvidenceStatus: {automation_uncertainty_status['evidence_status']}",
        f"- MachineSafeToContinue: {'YES' if automation_uncertainty_status['machine_safe_to_continue'] else 'NO'}",
        f"- HumanHelpNeeded: {'YES' if automation_uncertainty_status['human_help_needed'] else 'NO'}",
        f"- HumanHelpLane: {automation_uncertainty_status['human_help_lane']}",
        f"- ExpertHelpNeeded: {'YES' if automation_uncertainty_status['expert_help_needed'] else 'NO'}",
        f"- TargetExpert: {automation_uncertainty_status['target_expert']}",
        f"- ExpertLineupStatus: {automation_uncertainty_status['expert_lineup_status']}",
        f"- ExpertMemoryStatus: {automation_uncertainty_status['expert_memory_status']}",
        f"- BoardMemoryStatus: {automation_uncertainty_status['board_memory_status']}",
        f"- BoardReentryRequired: {'YES' if automation_uncertainty_status['board_reentry_required'] else 'NO'}",
        f"- BoundaryRegistry: {automation_uncertainty_status['boundary_registry']}",
        f"- ReasonCodes: {', '.join(automation_uncertainty_status['reason_codes']) if automation_uncertainty_status['reason_codes'] else 'none'}",
        "",
        "```text",
        f"AUTOMATION_UNCERTAINTY_STATUS: {automation_uncertainty_status['status']}",
        f"MACHINE_CONFIDENCE: {automation_uncertainty_status['machine_confidence']}",
        f"EVIDENCE_STATUS: {automation_uncertainty_status['evidence_status']}",
        f"MACHINE_SAFE_TO_CONTINUE: {'YES' if automation_uncertainty_status['machine_safe_to_continue'] else 'NO'}",
        f"HUMAN_HELP_NEEDED: {'YES' if automation_uncertainty_status['human_help_needed'] else 'NO'}",
        f"HUMAN_HELP_LANE: {automation_uncertainty_status['human_help_lane']}",
        f"EXPERT_HELP_NEEDED: {'YES' if automation_uncertainty_status['expert_help_needed'] else 'NO'}",
        f"TARGET_EXPERT: {automation_uncertainty_status['target_expert']}",
        f"EXPERT_LINEUP_STATUS: {automation_uncertainty_status['expert_lineup_status']}",
        f"EXPERT_MEMORY_STATUS: {automation_uncertainty_status['expert_memory_status']}",
        f"BOARD_MEMORY_STATUS: {automation_uncertainty_status['board_memory_status']}",
        f"BOARD_REENTRY_REQUIRED: {'YES' if automation_uncertainty_status['board_reentry_required'] else 'NO'}",
        f"BOARD_REENTRY_REASON_CODES: {','.join(automation_uncertainty_status['board_reentry_reason_codes']) if automation_uncertainty_status['board_reentry_reason_codes'] else 'none'}",
        f"MEMORY_REASON_CODES: {','.join(automation_uncertainty_status['memory_reason_codes']) if automation_uncertainty_status['memory_reason_codes'] else 'none'}",
        f"REASON_CODES: {','.join(automation_uncertainty_status['reason_codes']) if automation_uncertainty_status['reason_codes'] else 'none'}",
        f"BOUNDARY_REGISTRY: {automation_uncertainty_status['boundary_registry']}",
        f"RETIRE_WHEN: {' && '.join(automation_uncertainty_status['retirement_criteria'])}",
        "```",
        "",
        "## Replanning",
        "",
        f"- BlockingGapCount: {replanning['blocking_gap_count']}",
        f"- NextReplanRecommendation: {replanning['next_replan_recommendation']}",
        "",
    ])

    for detail in automation_uncertainty_status["reason_details"]:
        md_lines.append(f"- {detail}")

    if automation_uncertainty_status["reason_details"]:
        md_lines.append("")

    for gap in replanning["blocking_gaps"]:
        md_lines.append(
            f"- [{gap['source']}] {gap['code']}: {gap['detail']}"
        )

    md_lines.extend([
        "",
        "## Next Round Handoff",
        "",
        f"- Status: {next_round_handoff['status']}",
        f"- RecommendedIntent: {next_round_handoff['recommended_intent']}",
        f"- RecommendedScope: {next_round_handoff['recommended_scope']}",
        f"- DoneWhenChecks: {', '.join(next_round_handoff['recommended_done_when_checks'])}",
        f"- ArtifactsToRefresh: {', '.join(next_round_handoff['artifacts_to_refresh']) if next_round_handoff['artifacts_to_refresh'] else 'none'}",
        "",
    ])
    _append_advisory_split_markdown(
        md_lines,
        human_brief=next_round_handoff["human_brief"],
        machine_view=next_round_handoff["machine_view"],
        paste_ready_block=next_round_handoff["paste_ready_block"],
    )
    md_lines.extend([
        "## Expert Request",
        "",
        f"- Status: {expert_request['status']}",
        f"- TargetExpert: {expert_request['target_expert']}",
        f"- Question: {expert_request['question']}",
        f"- DecisionDependsOn: {expert_request['decision_depends_on']}",
        f"- SourceArtifacts: {', '.join(expert_request['source_artifacts']) if expert_request['source_artifacts'] else 'none'}",
        "",
    ])
    _append_advisory_split_markdown(
        md_lines,
        human_brief=expert_request["human_brief"],
        machine_view=expert_request["machine_view"],
        paste_ready_block=expert_request["paste_ready_block"],
    )
    md_lines.extend([
        "## PM/CEO Research Brief",
        "",
        f"- Status: {pm_ceo_research_brief['status']}",
        f"- DelegatedTo: {pm_ceo_research_brief['delegated_to']}",
        f"- Question: {pm_ceo_research_brief['question']}",
        f"- DecisionDependsOn: {pm_ceo_research_brief['decision_depends_on']}",
        f"- SourceArtifacts: {', '.join(pm_ceo_research_brief['source_artifacts']) if pm_ceo_research_brief['source_artifacts'] else 'none'}",
        "",
    ])
    _append_advisory_split_markdown(
        md_lines,
        human_brief=pm_ceo_research_brief["human_brief"],
        machine_view=pm_ceo_research_brief["machine_view"],
        paste_ready_block=pm_ceo_research_brief["paste_ready_block"],
    )
    md_lines.extend([
        "## Board Decision Brief",
        "",
        f"- Status: {board_decision_brief['status']}",
        f"- DecisionTopic: {board_decision_brief['decision_topic']}",
        f"- DecisionClass: {board_decision_brief['decision_class']}",
        f"- RiskTier: {board_decision_brief['risk_tier']}",
        f"- SourceArtifacts: {', '.join(board_decision_brief['source_artifacts']) if board_decision_brief['source_artifacts'] else 'none'}",
        "",
    ])
    _append_advisory_split_markdown(
        md_lines,
        human_brief=board_decision_brief["human_brief"],
        machine_view=board_decision_brief["machine_view"],
        paste_ready_block=board_decision_brief["paste_ready_block"],
    )
    md_lines.extend([
        "## Retrieval Namespaces",
        "",
    ])

    for ns_name, ns_sources in retrieval_namespaces.items():
        md_lines.append(f"### {ns_name}")
        if ns_sources:
            for src in ns_sources:
                md_lines.append(f"- {src['source']} ({src['type']}): {src['description']}")
        else:
            md_lines.append("- No sources")
        md_lines.append("")

    # Write markdown
    try:
        _atomic_write_text(output_md_path, "\n".join(md_lines))
    except Exception as e:
        try:
            _write_build_status(
                path=status_json_path,
                generated_at_utc=generated_at_utc,
                output_json_path=output_json_path,
                output_md_path=output_md_path,
                input_status=input_status,
                critical_failures=critical_failures,
                authoritative_latest_written=False,
                degraded_preview_written=bool(critical_failures),
                exit_code=2,
                reason="write_markdown_failed",
            )
        except Exception as status_exc:
            print(f"ERROR: Failed to write build status: {status_exc}", file=sys.stderr)
        print(f"ERROR: Failed to write markdown: {e}", file=sys.stderr)
        return 2

    # Check for critical input failures before final return
    if critical_failures:
        failed_names = ", ".join(item["file"] for item in critical_failures)
        try:
            _write_build_status(
                path=status_json_path,
                generated_at_utc=generated_at_utc,
                output_json_path=output_json_path,
                output_md_path=output_md_path,
                input_status=input_status,
                critical_failures=critical_failures,
                authoritative_latest_written=False,
                degraded_preview_written=True,
                exit_code=2,
                reason="critical_inputs_failed_degraded_preview_only",
            )
        except Exception as status_exc:
            print(f"ERROR: Failed to write build status: {status_exc}", file=sys.stderr)
        print(f"ERROR: Critical inputs failed to load: {failed_names}", file=sys.stderr)
        return 2

    # Exit with validation status
    if not pm_budget_ok or not ceo_budget_ok:
        try:
            _write_build_status(
                path=status_json_path,
                generated_at_utc=generated_at_utc,
                output_json_path=output_json_path,
                output_md_path=output_md_path,
                input_status=input_status,
                critical_failures=critical_failures,
                authoritative_latest_written=True,
                degraded_preview_written=False,
                exit_code=1,
                reason="token_budget_exceeded",
            )
        except Exception as status_exc:
            print(f"ERROR: Failed to write build status: {status_exc}", file=sys.stderr)
            return 2
        print("WARNING: Token budget exceeded", file=sys.stderr)
        return 1

    try:
        _write_build_status(
            path=status_json_path,
            generated_at_utc=generated_at_utc,
            output_json_path=output_json_path,
            output_md_path=output_md_path,
            input_status=input_status,
            critical_failures=critical_failures,
            authoritative_latest_written=True,
            degraded_preview_written=False,
            exit_code=0,
            reason="ok",
        )
    except Exception as status_exc:
        print(f"ERROR: Failed to write build status: {status_exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
