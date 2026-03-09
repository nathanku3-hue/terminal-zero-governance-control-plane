from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

try:
    from scripts.utils.atomic_io import atomic_write_text
except ModuleNotFoundError:
    # Fallback for direct script execution
    def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding=encoding, newline="\n") as handle:
                handle.write(content)
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
            raise

GO_ACTION_PATTERN = re.compile(
    r"^\s*-\s*Recommended Action:\s*([A-Za-z_]+)\s*$",
    re.IGNORECASE,
)
ROUND_FIELD_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")
GO_CRITERIA_ROW_PATTERN = re.compile(
    r"^\s*\|\s*(C[0-9]+B?)\s*\|\s*(MANUAL_CHECK|PASS|FAIL|TRUE|FALSE|[A-Za-z_]+)\s*\|\s*(.*?)\s*\|\s*$",
    re.IGNORECASE,
)
CRITICAL_CLOSURE_RESULT = "INPUT_OR_INFRA_ERROR"
READY_CLOSURE_RESULT = "READY_TO_ESCALATE"
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}
TODO_PREFIX = "TODO"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_path(repo_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _safe_load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"read_error: {exc}"
    try:
        payload = json.loads(raw)
    except Exception as exc:
        return None, f"json_error: {exc}"
    if not isinstance(payload, dict):
        return None, "json_error: root must be object"
    return payload, None


def _parse_go_action(path: Path) -> tuple[str | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"read_error: {exc}"
    for line in raw.splitlines():
        match = GO_ACTION_PATTERN.match(line)
        if match is None:
            continue
        return match.group(1).strip().upper(), None
    return None, "missing_recommended_action_line"


def _parse_round_contract_fields(path: Path) -> tuple[dict[str, str] | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"read_error: {exc}"
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        match = ROUND_FIELD_PATTERN.match(line)
        if match is None:
            continue
        key = match.group(1).strip().upper()
        value = match.group(2).strip()
        if key:
            fields[key] = value
    return fields, None


def _artifact_age_hours(path: Path, now_utc: datetime) -> float:
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return max(0.0, (now_utc - modified).total_seconds() / 3600.0)


def _event(level: str, code: str, message: str, artifact: str = "", details: str = "") -> dict[str, str]:
    return {
        "level": level,
        "code": code,
        "message": message,
        "artifact": artifact,
        "details": details,
    }


def _extract_markdown_section_lines(text: str, heading: str) -> list[str]:
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
        if len(line) > 3 and line[0].isdigit() and ". " in line:
            lines.append(line.split(". ", 1)[1].strip())
    return lines


def _to_slug(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return token or "unknown"


def _priority_rank(priority: str) -> int:
    return PRIORITY_ORDER.get(priority.upper(), len(PRIORITY_ORDER))


def _extract_go_signal_criteria_statuses(go_signal_text: str) -> dict[str, tuple[str, str]]:
    criteria: dict[str, tuple[str, str]] = {}
    for raw_line in go_signal_text.splitlines():
        match = GO_CRITERIA_ROW_PATTERN.match(raw_line)
        if match is None:
            continue
        criterion = match.group(1).strip().upper()
        status = match.group(2).strip().upper()
        value = match.group(3).strip()
        criteria[criterion] = (status, value)
    return criteria


def _append_manual_action(
    actions: list[dict[str, str]],
    seen: set[str],
    *,
    action_id: str,
    priority: str,
    source: str,
    action: str,
    reason: str,
    trigger: str,
) -> None:
    if action_id in seen:
        return
    seen.add(action_id)
    actions.append(
        {
            "id": action_id,
            "priority": priority,
            "source": source,
            "trigger": trigger,
            "action": action,
            "reason": reason,
        }
    )


def _build_manual_actions(
    *,
    artifacts: dict[str, dict[str, Any]],
    closure_result: str,
    closure_checks: list[dict[str, Any]],
    go_action: str,
    go_signal_text: str,
    round_fields: dict[str, str],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    seen: set[str] = set()

    for artifact_name in sorted(artifacts.keys()):
        artifact = artifacts.get(artifact_name, {})
        artifact_slug = _to_slug(artifact_name)
        if not artifact.get("exists"):
            _append_manual_action(
                actions,
                seen,
                action_id=f"missing_{artifact_slug}",
                priority="P0",
                source=artifact_name,
                action=f"Generate missing artifact `{artifact_name}` and rerun supervision.",
                reason="Required monitoring input is absent.",
                trigger="ARTIFACT_MISSING",
            )
            continue
        if artifact.get("stale"):
            age_hours = artifact.get("age_hours")
            age_note = (
                f" Artifact age is {float(age_hours):.3f}h."
                if isinstance(age_hours, (int, float))
                else ""
            )
            _append_manual_action(
                actions,
                seen,
                action_id=f"stale_{artifact_slug}",
                priority="P1",
                source=artifact_name,
                action=f"Refresh stale artifact `{artifact_name}` before the next promotion decision.",
                reason=f"Freshness threshold exceeded.{age_note}",
                trigger="STALE_ARTIFACT",
            )

    if closure_result == "NOT_READY":
        failed_checks = sorted(
            {
                str(item.get("name", "")).strip()
                for item in closure_checks
                if isinstance(item, dict)
                and str(item.get("status", "")).strip().upper() == "FAIL"
                and str(item.get("name", "")).strip()
            }
        )
        check_suffix = (
            f" Failing checks: {', '.join(failed_checks)}."
            if failed_checks
            else ""
        )
        _append_manual_action(
            actions,
            seen,
            action_id="closure_not_ready",
            priority="P0",
            source="loop_closure_status_latest.json",
            action="Review failing closure gates and rerun `python scripts/validate_loop_closure.py --repo-root . --freshness-hours 72`.",
            reason=f"Closure is NOT_READY.{check_suffix}",
            trigger="CLOSURE_NOT_READY",
        )
    elif closure_result == CRITICAL_CLOSURE_RESULT:
        _append_manual_action(
            actions,
            seen,
            action_id="closure_input_or_infra_error",
            priority="P0",
            source="loop_closure_status_latest.json",
            action="Fix closure input/infra errors before attempting escalation.",
            reason="Closure reported INPUT_OR_INFRA_ERROR.",
            trigger="CLOSURE_INPUT_OR_INFRA_ERROR",
        )

    if go_action in {"HOLD", "REFRAME"}:
        _append_manual_action(
            actions,
            seen,
            action_id="go_signal_not_go",
            priority="P0",
            source="ceo_go_signal.md",
            action="Review CEO blocking reasons and complete the highest-priority next step before rerunning the loop.",
            reason=f"CEO action is {go_action}.",
            trigger="GO_SIGNAL_HOLD",
        )

    criteria_statuses = _extract_go_signal_criteria_statuses(go_signal_text)
    c1_status = criteria_statuses.get("C1", ("", ""))[0]
    if c1_status == "MANUAL_CHECK":
        _append_manual_action(
            actions,
            seen,
            action_id="manual_signoff_c1",
            priority="P0",
            source="ceo_go_signal.md",
            action="Record PM signoff in `docs/decision log.md` once automated criteria are met.",
            reason="Dossier criterion C1 is MANUAL_CHECK.",
            trigger="MANUAL_CHECK",
        )
    c4b_status, c4b_value = criteria_statuses.get("C4B", ("", ""))
    if c4b_status in {"FAIL", "MANUAL_CHECK"}:
        suffix = f" ({c4b_value})" if c4b_value else ""
        _append_manual_action(
            actions,
            seen,
            action_id="annotation_gap_c4b",
            priority="P0",
            source="ceo_go_signal.md",
            action="Annotate outstanding C/H findings in `docs/context/auditor_fp_ledger.json` until annotation coverage is complete.",
            reason=f"Dossier criterion C4b is {c4b_status}{suffix}.",
            trigger="ANNOTATION_GAP",
        )

    for reason in _extract_markdown_section_lines(go_signal_text, "Blocking Reasons"):
        upper_reason = reason.upper()
        if "C4B" in upper_reason or "ANNOTATION" in upper_reason:
            _append_manual_action(
                actions,
                seen,
                action_id="annotation_gap_from_blocking_reason",
                priority="P1",
                source="ceo_go_signal.md",
                action="Annotate outstanding C/H findings in `docs/context/auditor_fp_ledger.json` until annotation coverage is complete.",
                reason=reason,
                trigger="ANNOTATION_GAP",
            )
        if "C1" in upper_reason or "MANUAL" in upper_reason:
            _append_manual_action(
                actions,
                seen,
                action_id="manual_signoff_from_blocking_reason",
                priority="P1",
                source="ceo_go_signal.md",
                action="Record PM signoff in `docs/decision log.md` once automated criteria are met.",
                reason=reason,
                trigger="MANUAL_CHECK",
            )

    if round_fields.get("INTUITION_GATE", "").strip().upper() == "HUMAN_REQUIRED":
        ack = round_fields.get("INTUITION_GATE_ACK", "").strip().upper()
        if ack not in {"PM_ACK", "CEO_ACK"}:
            _append_manual_action(
                actions,
                seen,
                action_id="intuition_gate_ack_missing",
                priority="P0",
                source="round_contract_latest.md",
                action="Capture `INTUITION_GATE_ACK` and `INTUITION_GATE_ACK_AT_UTC` before execution continues.",
                reason="Round contract requires human acknowledgment.",
                trigger="INTUITION_GATE_ACK",
            )

    todo_fields = sorted(
        key for key, value in round_fields.items() if value.strip().upper().startswith(TODO_PREFIX)
    )
    if todo_fields:
        _append_manual_action(
            actions,
            seen,
            action_id="round_contract_todo_fields",
            priority="P1",
            source="round_contract_latest.md",
            action="Replace round-contract TODO placeholders with explicit values before next cycle.",
            reason=f"Fields with TODO placeholders: {', '.join(todo_fields)}.",
            trigger="ROUND_CONTRACT_TODO",
        )

    next_steps = _extract_markdown_section_lines(go_signal_text, "Next Steps")
    if next_steps:
        _append_manual_action(
            actions,
            seen,
            action_id="go_next_step_1",
            priority="P1",
            source="ceo_go_signal.md",
            action=next_steps[0],
            reason="Top recommended next step from CEO GO signal.",
            trigger="GO_SIGNAL_NEXT_STEP",
        )
    if len(next_steps) > 1 and go_action in {"HOLD", "REFRAME"}:
        _append_manual_action(
            actions,
            seen,
            action_id="go_next_step_2",
            priority="P1",
            source="ceo_go_signal.md",
            action=next_steps[1],
            reason="Second recommended step for HOLD/REFRAME recovery.",
            trigger="GO_SIGNAL_NEXT_STEP",
        )

    actions.sort(key=lambda item: (_priority_rank(item.get("priority", "")), item.get("id", "")))
    return actions


def _build_alerts_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Supervisor Alerts",
        "",
        f"- GeneratedAtUTC: {payload['generated_at_utc']}",
        f"- CycleIndex: {payload['cycle_index']}",
        f"- OverallStatus: {payload['overall_status']}",
        f"- CriticalFound: {payload['critical_found']}",
        "",
    ]
    events = payload.get("events", [])
    if not isinstance(events, list) or not events:
        lines.extend(["No alerts.", ""])
    else:
        lines.extend(
            [
                "| Level | Code | Artifact | Message |",
                "|---|---|---|---|",
            ]
        )
        for event in events:
            if not isinstance(event, dict):
                continue
            level = str(event.get("level", "")).replace("|", "\\|")
            code = str(event.get("code", "")).replace("|", "\\|")
            artifact = str(event.get("artifact", "")).replace("|", "\\|")
            message = str(event.get("message", "")).replace("|", "\\|")
            lines.append(f"| {level} | {code} | {artifact} | {message} |")
        lines.append("")

    manual_actions = payload.get("manual_actions", [])
    manual_action_count = payload.get("manual_action_count", 0)
    lines.extend(["## Manual Action Queue", "", f"- PendingActions: {manual_action_count}", ""])
    if not isinstance(manual_actions, list) or not manual_actions:
        lines.extend(["No manual actions queued.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Priority | ActionID | Source | Trigger | Action | Reason |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in manual_actions:
        if not isinstance(item, dict):
            continue
        priority = str(item.get("priority", "")).strip().replace("|", "\\|")
        action_id = str(item.get("id", "")).strip().replace("|", "\\|")
        source = str(item.get("source", "")).strip().replace("|", "\\|")
        trigger = str(item.get("trigger", "")).strip().replace("|", "\\|")
        action = str(item.get("action", "")).strip().replace("|", "\\|")
        reason = str(item.get("reason", "")).strip().replace("|", "\\|")
        lines.append(
            f"| {priority} | {action_id} | {source} | {trigger} | {action} | {reason} |"
        )
    lines.append("")
    return "\n".join(lines)


def _run_supervision_cycle(
    *,
    repo_root: Path,
    context_dir: Path,
    freshness_hours: float,
    cycle_index: int,
) -> tuple[dict[str, Any], bool]:
    now_utc = _utc_now()
    generated_at_utc = _utc_iso(now_utc)
    events: list[dict[str, str]] = []

    loop_summary_path = context_dir / "loop_cycle_summary_latest.json"
    closure_path = context_dir / "loop_closure_status_latest.json"
    go_signal_path = context_dir / "ceo_go_signal.md"
    round_contract_path = context_dir / "round_contract_latest.md"

    artifacts: dict[str, dict[str, Any]] = {}
    for name, path in (
        ("loop_cycle_summary_latest.json", loop_summary_path),
        ("loop_closure_status_latest.json", closure_path),
        ("ceo_go_signal.md", go_signal_path),
        ("round_contract_latest.md", round_contract_path),
    ):
        exists = path.exists()
        entry: dict[str, Any] = {"path": str(path), "exists": exists}
        if exists:
            age_hours = round(_artifact_age_hours(path, now_utc), 3)
            stale = age_hours > freshness_hours
            entry["age_hours"] = age_hours
            entry["stale"] = stale
            if stale:
                events.append(
                    _event(
                        "WARN",
                        "STALE_ARTIFACT",
                        (
                            f"{name} age {age_hours:.3f}h exceeds freshness threshold "
                            f"{freshness_hours:.3f}h"
                        ),
                        artifact=name,
                    )
                )
        else:
            events.append(
                _event(
                    "INFO",
                    "ARTIFACT_MISSING",
                    f"{name} not found",
                    artifact=name,
                )
            )
        artifacts[name] = entry

    closure_result = ""
    closure_checks: list[dict[str, Any]] = []
    if closure_path.exists():
        closure_payload, closure_error = _safe_load_json_object(closure_path)
        if closure_error is not None:
            events.append(
                _event(
                    "WARN",
                    "CLOSURE_PARSE_ERROR",
                    "Unable to parse loop_closure_status_latest.json",
                    artifact="loop_closure_status_latest.json",
                    details=closure_error,
                )
            )
        else:
            raw_result = closure_payload.get("result") if closure_payload else ""
            if isinstance(raw_result, str):
                closure_result = raw_result.strip().upper()
            checks_payload = closure_payload.get("checks") if closure_payload else None
            if isinstance(checks_payload, list):
                closure_checks = [item for item in checks_payload if isinstance(item, dict)]
            if closure_result == CRITICAL_CLOSURE_RESULT:
                events.append(
                    _event(
                        "CRITICAL",
                        "CLOSURE_INPUT_OR_INFRA_ERROR",
                        "loop_closure_status result is INPUT_OR_INFRA_ERROR",
                        artifact="loop_closure_status_latest.json",
                    )
                )

    go_action = ""
    go_signal_text = ""
    if go_signal_path.exists():
        try:
            go_signal_text = go_signal_path.read_text(encoding="utf-8-sig")
        except Exception:
            go_signal_text = ""
        parsed_action, action_error = _parse_go_action(go_signal_path)
        if action_error is not None:
            events.append(
                _event(
                    "WARN",
                    "GO_SIGNAL_PARSE_ERROR",
                    "Unable to parse recommended action from ceo_go_signal.md",
                    artifact="ceo_go_signal.md",
                    details=action_error,
                )
            )
        elif parsed_action is not None:
            go_action = parsed_action
            if go_action in {"HOLD", "REFRAME"}:
                events.append(
                    _event(
                        "INFO",
                        "GO_SIGNAL_HOLD",
                        f"Recommended action is {go_action}",
                        artifact="ceo_go_signal.md",
                    )
                )

    round_fields: dict[str, str] = {}
    if round_contract_path.exists():
        parsed_fields, round_error = _parse_round_contract_fields(round_contract_path)
        if round_error is not None:
            events.append(
                _event(
                    "WARN",
                    "ROUND_CONTRACT_PARSE_ERROR",
                    "Unable to parse round_contract_latest.md",
                    artifact="round_contract_latest.md",
                    details=round_error,
                )
            )
        elif parsed_fields is not None:
            round_fields = parsed_fields

    if go_action == "GO" and closure_result == READY_CLOSURE_RESULT:
        events.append(
            _event(
                "READY",
                "READY_TO_ESCALATE",
                "GO signal and closure status indicate ready-to-escalate",
                artifact="ceo_go_signal.md|loop_closure_status_latest.json",
            )
        )

    manual_actions = _build_manual_actions(
        artifacts=artifacts,
        closure_result=closure_result,
        closure_checks=closure_checks,
        go_action=go_action,
        go_signal_text=go_signal_text,
        round_fields=round_fields,
    )
    manual_action_summary = {
        "total": len(manual_actions),
        "p0": sum(1 for item in manual_actions if item.get("priority") == "P0"),
        "p1": sum(1 for item in manual_actions if item.get("priority") == "P1"),
        "p2": sum(1 for item in manual_actions if item.get("priority") == "P2"),
    }

    critical_found = any(event["level"] == "CRITICAL" for event in events)
    has_ready = any(event["level"] == "READY" for event in events)
    has_hold = any(event["code"] == "GO_SIGNAL_HOLD" for event in events)
    has_warn = any(event["level"] == "WARN" for event in events)
    if critical_found:
        overall_status = "CRITICAL"
    elif has_ready:
        overall_status = "READY"
    elif has_hold:
        overall_status = "HOLD"
    elif has_warn:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "cycle_index": cycle_index,
        "repo_root": str(repo_root),
        "context_dir": str(context_dir),
        "freshness_hours": freshness_hours,
        "overall_status": overall_status,
        "critical_found": critical_found,
        "closure_result": closure_result,
        "go_signal_action": go_action,
        "round_contract": {
            "decision_class": round_fields.get("DECISION_CLASS", ""),
            "risk_tier": round_fields.get("RISK_TIER", ""),
        },
        "manual_action_count": len(manual_actions),
        "manual_action_summary": manual_action_summary,
        "manual_actions": manual_actions,
        "events": events,
        "artifacts": artifacts,
    }
    return payload, critical_found


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Periodically supervise loop artifacts and emit status/alert outputs. "
            "Exit 0=no critical, 1=critical found, 2=input/infra error."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--context-dir", type=Path, default=Path("docs/context"))
    parser.add_argument("--check-interval-seconds", type=int, default=300)
    parser.add_argument("--max-cycles", type=int, default=1)
    parser.add_argument("--freshness-hours", type=float, default=24.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check_interval_seconds < 0:
        print("[ERROR] --check-interval-seconds must be >= 0")
        return 2
    if args.max_cycles < 1:
        print("[ERROR] --max-cycles must be >= 1")
        return 2
    if args.freshness_hours <= 0:
        print("[ERROR] --freshness-hours must be > 0")
        return 2

    repo_root = args.repo_root.resolve()
    context_dir = _resolve_path(repo_root, args.context_dir)
    status_output = context_dir / "supervisor_status_latest.json"
    alerts_output = context_dir / "supervisor_alerts_latest.md"

    any_critical = False
    try:
        for cycle in range(1, args.max_cycles + 1):
            payload, critical_found = _run_supervision_cycle(
                repo_root=repo_root,
                context_dir=context_dir,
                freshness_hours=args.freshness_hours,
                cycle_index=cycle,
            )
            markdown = _build_alerts_markdown(payload)
            atomic_write_text(status_output, json.dumps(payload, indent=2) + "\n")
            atomic_write_text(alerts_output, markdown)
            any_critical = any_critical or critical_found

            if cycle < args.max_cycles and args.check_interval_seconds > 0:
                time.sleep(args.check_interval_seconds)
    except Exception as exc:
        print(f"[ERROR] supervisor infra failure: {exc}")
        return 2

    print("CRITICAL" if any_critical else "OK")
    return 1 if any_critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
