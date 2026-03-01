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
        return "✅"
    elif v == "WARNING":
        return "⚠️"
    elif v == "BLOCK":
        return "❌"
    return "-"
    
def _sanitize(text: str) -> str:
    if not text:
        return "—"
    t = text.replace("\n", " ").replace("\r", "").replace("|", "\\|")
    return t.strip() or "—"

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

def render_health(summary: dict, workers: list) -> str:
    lines = [
        "## I. System Health",
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
            # Format SLA
            sla_mark = "✅ " + sla_ok if sla_ok == "OK" else ("⚠️ " + sla_ok if sla_ok == "WARNING" else "❌ " + sla_ok)
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
        "## II. Expert Verdict Matrix",
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
        "## III. Traceability Summary",
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
        src = d.get("source", "-").split("#")[0]  # truncate for table display
        status = d.get("status", "UNMAPPED")
        d_count = len(d.get("traceability", {}).get("code_diffs", []))
        v_count = len(d.get("traceability", {}).get("validators", []))
        
        stat_mark = "✅ " + status if status == "VERIFIED" else ("❌ " + status if status == "UNMAPPED" else "⚠️ " + status)
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

    # Completions
    lines.append("## IV. Recent Completions")
    comps = []
    for w in workers:
        for cl in w.get("completion_log", []):
            if cl.get("status") == "completed":
                # simplistic inclusion
                comps.append(f"{cl.get('task_id')} — SAW {cl.get('saw_verdict', 'UNKNOWN')} ({w.get('worker_id')})")

    if not comps:
        lines.append("- None")
    else:
        for i, c in enumerate(comps[-10:]):
            lines.append(f"{i+1}. {c}")
    lines.append("")

    # Escalations
    lines.append("## V. Active Escalations")
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


def _format_confidence(confidence: dict | None) -> str:
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
        if c_path == "—":
            continue
        view.append(f"{c_path}@{c_locator}")
    if not view:
        return f"{len(citations)} ref"
    suffix = f" (+{len(citations) - len(view)} more)" if len(citations) > len(view) else ""
    return _sanitize("; ".join(view) + suffix)


def render_worker_confidence(reply_data: dict | list | None) -> str:
    lines = [
        "## VI. Worker Confidence and Citations",
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

    for item in items:
        worker_id = _sanitize(str(item.get("worker_id", "Unknown")))
        task_id = _sanitize(str(item.get("task_id", "-")))
        dod_result = _sanitize(str(item.get("dod_result", "-")).upper())
        confidence = _format_confidence(item.get("confidence"))
        citations = _format_citations(item.get("citations", []))
        lines.append(
            f"| {worker_id} | {task_id} | {dod_result} | {_sanitize(confidence)} | {citations} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_pm_actions() -> str:
    lines = [
        "## VII. Recommended PM Actions",
        "*Please review active escalations, traceability score, and confidence/citation completeness before dispatching new plans.*",
        "",
    ]
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sources",
        type=str,
        required=True,
        help=(
            "Comma separated: worker_status_aggregate.json,"
            "pm_to_code_traceability.yaml[,escalation_events.json[,worker_reply_packet.json]]"
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

    now = _now_utc()
    b_lines = [
        "# CEO Bridge Digest",
        f"Generated: {now.isoformat().replace('+00:00', 'Z')}",
        "Digest Version: 1.0.0",
        ""
    ]

    summary = agg_data.get("summary", {})
    workers = agg_data.get("workers", [])

    b_lines.append(render_health(summary, workers))
    b_lines.append(render_matrix(workers))
    b_lines.append(render_traceability(trace_data))
    b_lines.append(render_completions_and_escalations(workers, esc_data))
    b_lines.append(render_worker_confidence(reply_data))
    b_lines.append(render_pm_actions())

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
