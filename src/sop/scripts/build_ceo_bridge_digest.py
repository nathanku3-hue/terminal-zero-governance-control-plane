from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path
import yaml

EXPERT_ORDER = ["system_eng", "architect", "principal", "riskops", "devsecops", "qa"]

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _emoji(val: str | None) -> str:
    if not val:
        return "-"
    v = val.upper()
    if v == "PASS":
        return "\u2705"
    elif v == "WARNING":
        return "\u26a0\ufe0f"
    elif v == "BLOCK":
        return "\u274c"
    return "-"

def _sanitize(text: str) -> str:
    if not text:
        return "\u2014"
    t = text.replace("\n", " ").replace("\r", "").replace("|", "\\|")
    return t.strip() or "\u2014"

def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Worker reply normalization and confidence resolution
# ---------------------------------------------------------------------------

def _normalize_worker_reply_items(reply_data: dict | list | None) -> list[dict]:
    if isinstance(reply_data, dict):
        items = reply_data.get("items")
        if isinstance(items, list):
            worker_id = reply_data.get("worker_id", "Unknown")
            out: list[dict] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                merged = dict(item)
                merged.setdefault("worker_id", worker_id)
                out.append(merged)
            return out
    if isinstance(reply_data, list):
        out = []
        for item in reply_data:
            if isinstance(item, dict):
                out.append(item)
        return out
    return []


def _resolve_confidence(item: dict) -> dict | None:
    """Read confidence from v2 canonical location, fall back to v1 location."""
    mo = item.get("machine_optimized")
    if isinstance(mo, dict):
        cl = mo.get("confidence_level")
        if isinstance(cl, dict):
            return cl
    # v1 fallback
    return item.get("confidence")


def _resolve_response_views(item: dict) -> dict | None:
    response_views = item.get("response_views")
    if isinstance(response_views, dict):
        return response_views
    return None


def _resolve_worker_human_brief(item: dict) -> str | None:
    response_views = _resolve_response_views(item)
    if response_views is not None:
        human_brief = response_views.get("human_brief")
        if isinstance(human_brief, str) and human_brief.strip():
            return human_brief.strip()
    decision = item.get("decision")
    if isinstance(decision, str) and decision.strip():
        return decision.strip()
    return None


def _resolve_worker_paste_ready_block(item: dict) -> str | None:
    response_views = _resolve_response_views(item)
    if response_views is None:
        return None
    paste_ready_block = response_views.get("paste_ready_block")
    if isinstance(paste_ready_block, str) and paste_ready_block.strip():
        return paste_ready_block.strip()
    return None


def _format_confidence(item: dict) -> str:
    confidence = _resolve_confidence(item)
    if not isinstance(confidence, dict):
        return "-"
    score = confidence.get("score")
    band = str(confidence.get("band", "")).upper().strip()
    if isinstance(score, (int, float)):
        return f"{float(score):.2f} ({band or '-'})"
    if band:
        return band
    return "-"


def _format_citations(citations: list) -> str:
    if not isinstance(citations, list) or not citations:
        return "-"
    view = []
    for citation in citations[:2]:
        if not isinstance(citation, dict):
            continue
        c_path = _sanitize(str(citation.get("path", "")))
        c_locator = _sanitize(str(citation.get("locator", "")))
        if c_path == "\u2014":
            continue
        view.append(f"{c_path}@{c_locator}")
    if not view:
        return f"{len(citations)} ref"
    suffix = f" (+{len(citations) - len(view)} more)" if len(citations) > len(view) else ""
    return _sanitize("; ".join(view) + suffix)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def render_first_principles(reply_data: dict | list | None) -> str:
    lines = [
        "## I. First Principles Engineering Summary",
    ]
    items = _normalize_worker_reply_items(reply_data)
    has_fp = False
    for item in items:
        fp = item.get("pm_first_principles")
        if isinstance(fp, dict) and any(fp.get(k) for k in ("problem", "constraints", "logic", "solution")):
            has_fp = True
            break

    if not items or not has_fp:
        lines.append("\u2014 Not available (v1 packet)")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Worker | Task | Problem | Constraints | Logic | Solution |")
    lines.append("|--------|------|---------|-------------|-------|----------|")
    for item in items:
        fp = item.get("pm_first_principles", {})
        if not isinstance(fp, dict):
            fp = {}
        worker_id = _sanitize(str(item.get("worker_id", "Unknown")))
        task_id = _sanitize(str(item.get("task_id", "-")))
        problem = _sanitize(str(fp.get("problem", "")))
        constraints = _sanitize(str(fp.get("constraints", "")))
        logic = _sanitize(str(fp.get("logic", "")))
        solution = _sanitize(str(fp.get("solution", "")))
        lines.append(f"| {worker_id} | {task_id} | {problem} | {constraints} | {logic} | {solution} |")
    lines.append("")
    return "\n".join(lines)


def render_expertise_coverage(reply_data: dict | list | None) -> str:
    lines = [
        "## II. Strategic Expertise Coverage",
    ]
    items = _normalize_worker_reply_items(reply_data)
    has_coverage = False
    for item in items:
        mo = item.get("machine_optimized")
        if isinstance(mo, dict):
            ec = mo.get("expertise_coverage")
            if isinstance(ec, list) and ec:
                has_coverage = True
                break

    if not items or not has_coverage:
        lines.append("\u2014 Not available (v1 packet)")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Worker | Task | Domain | Verdict | Rationale |")
    lines.append("|--------|------|--------|---------|-----------|")
    for item in items:
        worker_id = _sanitize(str(item.get("worker_id", "Unknown")))
        task_id = _sanitize(str(item.get("task_id", "-")))
        mo = item.get("machine_optimized", {})
        if not isinstance(mo, dict):
            continue
        coverage = mo.get("expertise_coverage", [])
        if not isinstance(coverage, list):
            continue
        for entry in coverage:
            if not isinstance(entry, dict):
                continue
            domain = _sanitize(str(entry.get("domain", "")))
            verdict = _sanitize(str(entry.get("verdict", "")))
            rationale = _sanitize(str(entry.get("rationale", "")))
            lines.append(f"| {worker_id} | {task_id} | {domain} | {verdict} | {rationale} |")
    lines.append("")
    return "\n".join(lines)


def render_health(summary: dict, workers: list) -> str:
    lines = [
        "## III. System Health",
        "| Worker | Lane | Status | Current Task | SLA |",
        "|--------|------|--------|-------------|-----|"
    ]
    if not workers:
        lines.append("| NO_WORKERS | - | - | - | - |")
    else:
        for w in workers:
            w_id = w.get("worker_id", "Unknown")
            lane = w.get("lane", "-")
            status = w.get("heartbeat", {}).get("status", "-")
            task = w.get("heartbeat", {}).get("current_task", {}).get("task_id", "IDLE")
            sla_ok = w.get("sla", {}).get("escalation_status", "OK")
            sla_mark = "\u2705 " + sla_ok if sla_ok == "OK" else ("\u26a0\ufe0f " + sla_ok if sla_ok == "WARNING" else "\u274c " + sla_ok)
            lines.append(f"| {w_id} | {lane} | {status} | {task} | {sla_mark} |")

    lines.append("")
    overall = summary.get("overall_health", "OK")
    olines = f"**Overall Health: {overall}**"
    if overall != "OK":
        olines += f" ({summary.get('stale', 0)} stale, {summary.get('escalated', 0)} escalated)"
    lines.append(olines)
    lines.append("")
    return "\n".join(lines)

def render_matrix(workers: list) -> str:
    lines = [
        "## IV. Expert Verdict Matrix",
        "| Worker | Task | SysEng | Architect | Principal | RiskOps | DevSecOps | QA | Blockers |",
        "|--------|------|--------|-----------|-----------|---------|-----------|----|----------|"
    ]
    if not workers:
        lines.append("| NO_WORKERS | - | - | - | - | - | - | - | - |")
    else:
        for w in workers:
            gate = w.get("expert_gate", {})
            task = w.get("heartbeat", {}).get("current_task", {}).get("task_id", "IDLE")
            w_id = w.get("worker_id", "Unknown")
            blockers = w.get("blockers", [])
            b_text = _sanitize(", ".join(blockers))

            row = [w_id, task]
            for exp in EXPERT_ORDER:
                row.append(_emoji(gate.get(exp)))
            row.append(b_text)
            lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)

def render_traceability(trace_data: dict) -> str:
    lines = [
        "## V. Traceability Summary",
        "| Directive | Source | Status | Evidence |",
        "|-----------|--------|--------|----------|"
    ]
    dirs = trace_data.get("directives", [])
    if not dirs:
        lines.append("| NO_DIRECTIVES | - | - | - |")
        return "\n".join(lines) + "\n"

    verified = 0
    for d in dirs:
        d_id = d.get("directive_id", "-")
        src = d.get("source", "-").split("#")[0]
        status = d.get("status", "UNMAPPED")
        d_count = len(d.get("traceability", {}).get("code_diffs", []))
        v_count = len(d.get("traceability", {}).get("validators", []))

        stat_mark = "\u2705 " + status if status == "VERIFIED" else ("\u274c " + status if status == "UNMAPPED" else "\u26a0\ufe0f " + status)
        ev_str = f"{d_count} diff, {v_count} tests"

        if status == "VERIFIED":
            verified += 1

        lines.append(f"| {d_id} | {src} | {stat_mark} | {ev_str} |")

    lines.append("")
    score = (verified / len(dirs)) * 100 if dirs else 100
    lines.append(f"**Traceability Score: {verified}/{len(dirs)} ({score:.1f}%)**")
    lines.append("")
    return "\n".join(lines)


def render_completions_and_escalations(workers: list, escalations_node: dict = None) -> str:
    lines = []

    lines.append("## VI. Recent Completions")
    comps = []
    for w in workers:
        for cl in w.get("completion_log", []):
            if cl.get("status") == "completed":
                comps.append(f"{cl.get('task_id')} \u2014 SAW {cl.get('saw_verdict', 'UNKNOWN')} ({w.get('worker_id')})")

    if not comps:
        lines.append("- None")
    else:
        for i, c in enumerate(comps[-10:]):
            lines.append(f"{i+1}. {c}")
    lines.append("")

    lines.append("## VII. Active Escalations")
    active_esc = []
    if escalations_node:
        for e in escalations_node.get("events", []):
            if not e.get("resolved"):
                active_esc.append(e)

    if not active_esc:
        lines.append("- None active")
    else:
        lines.append("| Worker | Task | Stale Since | Duration | Action |")
        lines.append("|--------|------|-------------|----------|--------|")
        for e in active_esc:
            w_id = e.get("worker_id", "-")
            task = e.get("task_id", "-")
            since = e.get("stale_since_utc", "-")
            dur = f"{e.get('stale_duration_minutes', 0):.1f}m"
            act = e.get("recommended_action", "-")
            if bool(e.get("clock_skew_suspect")):
                act = "(SKEW SUSPECT) " + act
            lines.append(f"| {w_id} | {task} | {since} | {dur} | {act} |")
    lines.append("")

    return "\n".join(lines)


def render_worker_confidence(reply_data: dict | list | None) -> str:
    lines = [
        "## VIII. Worker Confidence and Citations",
        "| Worker | Task | DoD | Confidence | Citations |",
        "|--------|------|-----|------------|-----------|",
    ]
    items = _normalize_worker_reply_items(reply_data)
    if not items:
        lines.append("| - | - | - | - | - |")
        lines.append("")
        lines.append("- No worker reply packet provided.")
        lines.append("")
        return "\n".join(lines)

    pm_summaries: list[str] = []
    paste_ready_blocks: list[tuple[str, str]] = []
    for item in items:
        worker_id = _sanitize(str(item.get("worker_id", "Unknown")))
        task_id = _sanitize(str(item.get("task_id", "-")))
        dod_result = _sanitize(str(item.get("dod_result", "-")).upper())
        confidence = _format_confidence(item)
        citations = _format_citations(item.get("citations", []))
        lines.append(
            f"| {worker_id} | {task_id} | {dod_result} | {_sanitize(confidence)} | {citations} |"
        )

        human_brief = _resolve_worker_human_brief(item)
        if human_brief is not None:
            pm_summaries.append(f"- {worker_id} / {task_id}: {_sanitize(human_brief)}")

        paste_ready_block = _resolve_worker_paste_ready_block(item)
        if paste_ready_block is not None:
            paste_ready_blocks.append((f"{worker_id} / {task_id}", paste_ready_block))

    lines.append("")

    if pm_summaries:
        lines.append("### PM-Style Worker Summaries")
        lines.append("")
        lines.extend(pm_summaries)
        lines.append("")

    if paste_ready_blocks:
        lines.append("### Paste-Ready Worker Blocks")
        lines.append("")
        for label, paste_ready_block in paste_ready_blocks:
            lines.append(f"#### {label}")
            lines.append("")
            lines.append("```text")
            lines.append(paste_ready_block)
            lines.append("```")
            lines.append("")

    return "\n".join(lines)


def render_auditor_findings(auditor_data: dict | None) -> str:
    lines = [
        "## IX. Auditor Review Findings",
    ]
    if not isinstance(auditor_data, dict) or "auditor_id" not in auditor_data:
        lines.append("Auditor review not available.")
        lines.append("")
        return "\n".join(lines)

    mode = auditor_data.get("mode", "unknown")
    summary = auditor_data.get("summary", {})
    verdict = summary.get("gate_verdict", "UNKNOWN")
    total = summary.get("total_findings", 0)

    lines.append(f"**Mode:** {mode} | **Verdict:** {verdict} | **Total findings:** {total}")
    lines.append("")

    # Note about shadow mode verdict interpretation
    if mode == "shadow" and (summary.get("critical", 0) > 0 or summary.get("high", 0) > 0):
        lines.append("_Note: Verdict is PASS in shadow mode because blocking is mode-driven, not severity-driven._")
        lines.append("")

    findings = auditor_data.get("findings", [])
    if findings:
        lines.append("| ID | Rule | Task | Severity | Category | Description | Blocking |")
        lines.append("|----|------|------|----------|----------|-------------|----------|")
        for f in findings:
            fid = _sanitize(str(f.get("finding_id", "-")))
            rid = _sanitize(str(f.get("rule_id", "-")))
            tid = _sanitize(str(f.get("task_id", "-")))
            sev = _sanitize(str(f.get("severity", "-")))
            cat = _sanitize(str(f.get("category", "-")))
            desc = _sanitize(str(f.get("description", "-")))
            blk = "\u2705" if not f.get("blocking") else "\u274c"
            lines.append(f"| {fid} | {rid} | {tid} | {sev} | {cat} | {desc} | {blk} |")
    else:
        lines.append("No findings.")

    lines.append("")
    return "\n".join(lines)


def render_score_gates(reply_data: dict | list | None) -> str:
    lines = [
        "## X. Per-Round Score Gates",
        "| Worker | Task | Confidence | Relatability | Gate |",
        "|--------|------|------------|--------------|------|",
    ]
    items = _normalize_worker_reply_items(reply_data)
    if not items:
        lines.append("| - | - | - | - | - |")
        lines.append("")
        lines.append("- No worker reply packet provided.")
        lines.append("")
        return "\n".join(lines)

    for item in items:
        worker_id = _sanitize(str(item.get("worker_id", "Unknown")))
        task_id = _sanitize(str(item.get("task_id", "-")))

        mo = item.get("machine_optimized")
        conf_score = None
        psa_score = None
        if isinstance(mo, dict):
            cl = mo.get("confidence_level")
            if isinstance(cl, dict):
                conf_score = cl.get("score")
            psa_score = mo.get("problem_solving_alignment_score")

        conf_str = f"{float(conf_score):.2f}" if isinstance(conf_score, (int, float)) else "-"
        psa_str = f"{float(psa_score):.2f}" if isinstance(psa_score, (int, float)) else "-"

        gate = "GO"
        if isinstance(conf_score, (int, float)) and float(conf_score) < 0.70:
            gate = "HOLD"
        if isinstance(psa_score, (int, float)) and float(psa_score) < 0.75:
            gate = "REFRAME" if gate == "GO" else gate + "/REFRAME"

        lines.append(f"| {worker_id} | {task_id} | {conf_str} | {psa_str} | {gate} |")

    lines.append("")
    return "\n".join(lines)


def render_pm_actions() -> str:
    lines = [
        "## XI. Recommended PM Actions",
        "*Please review active escalations, traceability score, confidence/citation completeness, and score gates before dispatching new plans.*",
        "",
    ]
    return "\n".join(lines)


def _format_governance_value(value: object) -> str | None:
    if isinstance(value, dict):
        parts: list[str] = []
        for key, item in value.items():
            item_text = _format_governance_value(item)
            if item_text:
                parts.append(f"{key}={item_text}")
        return "; ".join(parts) or None
    if isinstance(value, list):
        items = [item for item in (_format_governance_value(item) for item in value) if item]
        return ", ".join(items) or None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _looks_like_exec_memory_packet(candidate: object) -> bool:
    if not isinstance(candidate, dict):
        return False
    return any(
        key in candidate
        for key in (
            "next_round_handoff",
            "expert_request",
            "pm_ceo_research_brief",
            "board_decision_brief",
            "automation_uncertainty_status",
            "milestone_expert_roster_status",
        )
    )


def render_lineup_and_memory_governance(exec_memory_data: dict | None) -> str:
    if not isinstance(exec_memory_data, dict):
        return ""

    expert_request = exec_memory_data.get("expert_request")
    board_decision_brief = exec_memory_data.get("board_decision_brief")
    automation_uncertainty_status = exec_memory_data.get("automation_uncertainty_status")

    if not isinstance(expert_request, dict):
        expert_request = {}
    if not isinstance(board_decision_brief, dict):
        board_decision_brief = {}
    if not isinstance(automation_uncertainty_status, dict):
        automation_uncertainty_status = {}

    lines = ["## XII. Lineup and Memory Governance"]
    rendered_any = False

    expert_lineup_items = [
        ("Requested domain", expert_request.get("requested_domain")),
        ("Roster fit", expert_request.get("roster_fit")),
        ("Milestone ID", expert_request.get("milestone_id")),
        ("Board re-entry required", expert_request.get("board_reentry_required")),
        ("Board re-entry reasons", expert_request.get("board_reentry_reason_codes")),
    ]
    expert_lines = [
        f"- {label}: {text}"
        for label, value in expert_lineup_items
        if (text := _format_governance_value(value)) is not None
    ]
    if expert_lines:
        rendered_any = True
        lines.extend(["", "### Expert Request Governance", ""])
        lines.extend(expert_lines)

    board_lineup_items = [
        ("Lineup decision needed", board_decision_brief.get("lineup_decision_needed")),
        ("Lineup gap domains", board_decision_brief.get("lineup_gap_domains")),
        ("Approved roster snapshot", board_decision_brief.get("approved_roster_snapshot")),
        ("Reintroduce board when", board_decision_brief.get("reintroduce_board_when")),
        ("Board re-entry required", board_decision_brief.get("board_reentry_required")),
        ("Board re-entry reasons", board_decision_brief.get("board_reentry_reason_codes")),
    ]
    board_lines = [
        f"- {label}: {text}"
        for label, value in board_lineup_items
        if (text := _format_governance_value(value)) is not None
    ]
    if board_lines:
        rendered_any = True
        lines.extend(["", "### Board Governance", ""])
        lines.extend(board_lines)

    memory_items = [
        (
            "Expert memory status",
            automation_uncertainty_status.get("expert_memory_status")
            or expert_request.get("expert_memory_status")
            or board_decision_brief.get("expert_memory_status"),
        ),
        (
            "Board memory status",
            automation_uncertainty_status.get("board_memory_status")
            or expert_request.get("board_memory_status")
            or board_decision_brief.get("board_memory_status"),
        ),
        (
            "Memory reason codes",
            automation_uncertainty_status.get("memory_reason_codes")
            or expert_request.get("memory_reason_codes")
            or board_decision_brief.get("memory_reason_codes"),
        ),
        (
            "Milestone expert roster status",
            exec_memory_data.get("milestone_expert_roster_status"),
        ),
    ]
    memory_lines = [
        f"- {label}: {text}"
        for label, value in memory_items
        if (text := _format_governance_value(value)) is not None
    ]
    if memory_lines:
        rendered_any = True
        lines.extend(["", "### Memory Governance", ""])
        lines.extend(memory_lines)

    if not rendered_any:
        return ""

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sources",
        type=str,
        required=True,
        help=(
            "Comma separated: worker_status_aggregate.json,"
            "pm_to_code_traceability.yaml[,escalation_events.json"
            "[,worker_reply_packet.json[,auditor_findings.json[,exec_memory_packet.json]]]]"
        ),
    )
    parser.add_argument("--output", type=str, required=True, help="Output markdown path")
    parser.add_argument("--dry-run", action="store_true", help="Print digest to stdout, no write")
    args = parser.parse_args()

    sources = args.sources.split(",")
    agg_path = Path(sources[0]) if len(sources) > 0 else None
    trace_path = Path(sources[1]) if len(sources) > 1 else None
    esc_path = Path(sources[2]) if len(sources) > 2 else None
    reply_path = Path(sources[3]) if len(sources) > 3 else None

    agg_data = {}
    if agg_path and agg_path.exists():
        with open(agg_path, "r", encoding="utf-8") as f:
            agg_data = json.load(f)

    trace_data = {}
    if trace_path and trace_path.exists():
        with open(trace_path, "r", encoding="utf-8") as f:
            trace_data = yaml.safe_load(f) or {}

    esc_data = {}
    if esc_path and esc_path.exists():
        with open(esc_path, "r", encoding="utf-8") as f:
            esc_data = json.load(f)

    reply_data: dict | list | None = {}
    if reply_path and reply_path.exists():
        with open(reply_path, "r", encoding="utf-8") as f:
            reply_data = json.load(f)

    auditor_data: dict | None = None
    exec_memory_data: dict | None = None
    for extra_idx in range(4, len(sources)):
        extra_path = Path(sources[extra_idx])
        if not extra_path.exists():
            continue
        try:
            with open(extra_path, "r", encoding="utf-8") as f:
                candidate = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if auditor_data is None and isinstance(candidate, dict) and "auditor_id" in candidate:
            auditor_data = candidate
            continue
        if exec_memory_data is None and _looks_like_exec_memory_packet(candidate):
            exec_memory_data = candidate

    now = _now_utc()
    b_lines = [
        "# CEO Bridge Digest",
        f"Generated: {now.isoformat().replace('+00:00', 'Z')}",
        "Digest Version: 2.0.0",
        ""
    ]

    summary = agg_data.get("summary", {})
    workers = agg_data.get("workers", [])

    b_lines.append(render_first_principles(reply_data))
    b_lines.append(render_expertise_coverage(reply_data))
    b_lines.append(render_health(summary, workers))
    b_lines.append(render_matrix(workers))
    b_lines.append(render_traceability(trace_data))
    b_lines.append(render_completions_and_escalations(workers, esc_data))
    b_lines.append(render_worker_confidence(reply_data))
    b_lines.append(render_auditor_findings(auditor_data))
    b_lines.append(render_score_gates(reply_data))
    b_lines.append(render_pm_actions())
    lineup_and_memory_governance = render_lineup_and_memory_governance(exec_memory_data)
    if lineup_and_memory_governance:
        b_lines.append(lineup_and_memory_governance)

    digest_md = "\n".join(b_lines)

    if args.dry_run:
        print("[DRY-RUN] CEO Bridge Digest Output:\n")
        print(digest_md)
        return 0

    out_path = Path(args.output).resolve()
    _atomic_write_text(out_path, digest_md)
    return 0

if __name__ == "__main__":
    sys.exit(main())
