from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _parse_iso_utc(s: str) -> datetime:
    """Parse ISO 8601 UTC timestamp."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def _iso_week(dt: datetime) -> str:
    """Return ISO week string YYYY-Www."""
    return dt.strftime("%G-W%V")

def _is_next_week(week1: str, week2: str) -> bool:
    """Check if week2 immediately follows week1 in ISO week sequence."""
    from datetime import date
    y1, w1 = int(week1[:4]), int(week1[6:])
    y2, w2 = int(week2[:4]), int(week2[6:])
    if y1 == y2:
        return w2 == w1 + 1
    elif y2 == y1 + 1:
        last_week = date(y1, 12, 28).isocalendar()[1]
        return w1 == last_week and w2 == 1
    return False

def _atomic_write_text(path: Path, content: str) -> None:
    """Atomic write via temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mktemp(dir=path.parent, prefix=".tmp_"))
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

def _load_json(path: Path) -> dict:
    """Load JSON file, exit 2 on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"ERROR: Failed to load {path}: {e}", file=sys.stderr)
        sys.exit(2)

def _extract_run_id(filename: str) -> str | None:
    """Extract run_id from auditor_findings_RUNID.json or phase_end_handover_status_RUNID.json."""
    if filename.startswith("auditor_findings_") and filename.endswith(".json"):
        return filename[len("auditor_findings_"):-len(".json")]
    if filename.startswith("phase_end_handover_status_") and filename.endswith(".json"):
        return filename[len("phase_end_handover_status_"):-len(".json")]
    return None

def _parse_mode_from_status(status: dict, run_id: str) -> str | None:
    """Parse --mode from G11 gate command args in status file."""
    gates = status.get("gates", [])
    for gate in gates:
        if gate.get("gate") == "G11_auditor_review" and gate.get("status") != "SKIPPED":
            cmd = gate.get("command", "")
            if "--mode shadow" in cmd or "-AuditMode shadow" in cmd:
                return "shadow"
            if "--mode enforce" in cmd or "-AuditMode enforce" in cmd:
                return "enforce"
    return None

def _check_infra_failure_in_status(status: dict) -> bool:
    """Check if status file indicates infra failure (C0 criterion)."""
    gates = status.get("gates", [])
    for gate in gates:
        gate_id = gate.get("gate", "")
        # G11 exit_code=2 is infra error (exit_code=1 is policy block, not infra)
        if gate_id == "G11_auditor_review" and gate.get("exit_code") == 2:
            return True
        # Finalize gate failures (G09b/G10b BLOCK)
        if (gate_id in ("G09b_rebuild_ceo_digest", "G10b_digest_freshness_revalidation") and
                gate.get("status") == "BLOCK"):
            return True
    return False

def main() -> None:
    parser = argparse.ArgumentParser(description="Auditor calibration report generator")
    parser.add_argument("--logs-dir", required=True, help="Directory with phase_end_logs")
    parser.add_argument("--repo-id", required=True, help="Repository ID for ledger matching")
    parser.add_argument("--ledger", help="Path to auditor_fp_ledger.json")
    parser.add_argument("--output-json", required=True, help="Output JSON report path")
    parser.add_argument("--output-md", required=True, help="Output Markdown report path")
    parser.add_argument("--mode", choices=["weekly", "dossier"], default="weekly", help="Report mode")
    parser.add_argument("--from-utc", help="Start timestamp (ISO 8601 UTC)")
    parser.add_argument("--to-utc", help="End timestamp (ISO 8601 UTC)")
    parser.add_argument("--min-items", type=int, default=30, help="Min items for dossier C2")
    parser.add_argument("--min-items-per-week", type=int, default=10, help="Min items per week for C3")
    parser.add_argument("--min-weeks", type=int, default=2, help="Min consecutive weeks for C3")
    parser.add_argument("--max-fp-rate", type=float, default=0.05, help="Max FP rate for C4")
    args = parser.parse_args()

    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_dir():
        print(f"ERROR: Logs directory not found: {logs_dir}", file=sys.stderr)
        sys.exit(2)

    # Parse and validate time filters
    from_dt = None
    to_dt = None
    if args.from_utc:
        try:
            from_dt = _parse_iso_utc(args.from_utc)
        except Exception as e:
            print(f"ERROR: Invalid --from-utc timestamp: {e}", file=sys.stderr)
            sys.exit(2)
    if args.to_utc:
        try:
            to_dt = _parse_iso_utc(args.to_utc)
        except Exception as e:
            print(f"ERROR: Invalid --to-utc timestamp: {e}", file=sys.stderr)
            sys.exit(2)

    # Load ledger
    ledger_annotations: dict[tuple[str, str, str], dict] = {}
    ledger_loaded = False
    if args.ledger:
        ledger_path = Path(args.ledger)
        if ledger_path.exists():
            ledger = _load_json(ledger_path)
            ledger_loaded = True

            # Validate annotations is a list
            annotations = ledger.get("annotations", [])
            if not isinstance(annotations, list):
                print(f"ERROR: Ledger 'annotations' must be a list, got {type(annotations).__name__}", file=sys.stderr)
                sys.exit(2)

            seen_keys = set()
            for i, ann in enumerate(annotations):
                # Validate annotation is a dict
                if not isinstance(ann, dict):
                    print(f"ERROR: Ledger annotation at index {i} must be a dict, got {type(ann).__name__}", file=sys.stderr)
                    sys.exit(2)

                # Validate provenance
                if not ann.get("annotated_by") or not ann.get("annotated_at_utc"):
                    print(f"WARNING: Annotation missing provenance, ignoring: {ann}", file=sys.stderr)
                    continue
                # Validate verdict
                verdict = ann.get("verdict")
                if verdict not in ("TP", "FP"):
                    print(f"WARNING: Annotation has invalid verdict '{verdict}', ignoring: {ann}", file=sys.stderr)
                    continue
                # Validate composite key fields
                try:
                    key = (ann["repo_id"], ann["run_id"], ann["finding_id"])
                except KeyError as e:
                    print(f"ERROR: Annotation missing required key field {e}: {ann}", file=sys.stderr)
                    sys.exit(2)
                if key in seen_keys:
                    print(f"ERROR: Duplicate ledger key: {key}", file=sys.stderr)
                    sys.exit(2)
                seen_keys.add(key)
                ledger_annotations[key] = ann

    # Scan for findings and status files
    findings_files = list(logs_dir.glob("auditor_findings_*.json"))
    status_files = list(logs_dir.glob("phase_end_handover_status_*.json"))

    findings_by_run: dict[str, Path] = {}
    for f in findings_files:
        run_id = _extract_run_id(f.name)
        if run_id:
            findings_by_run[run_id] = f

    status_by_run: dict[str, Path] = {}
    for s in status_files:
        run_id = _extract_run_id(s.name)
        if run_id:
            status_by_run[run_id] = s

    # Build shadow-only run cohort
    runs: list[dict] = []
    infra_failures = 0
    unpaired_warnings = []

    for run_id, findings_path in findings_by_run.items():
        findings = _load_json(findings_path)
        mode = findings.get("mode")
        timestamp_str = findings.get("audit_timestamp_utc")

        # Check if status file exists
        if run_id not in status_by_run:
            msg = f"Findings file without matching status: {findings_path.name}"
            unpaired_warnings.append(msg)
            if args.mode == "dossier":
                infra_failures += 1
            continue

        status = _load_json(status_by_run[run_id])

        # Check if G11 was executed
        g11_executed = False
        for gate in status.get("gates", []):
            if gate.get("gate") == "G11_auditor_review" and gate.get("status") != "SKIPPED":
                g11_executed = True
                break

        if not g11_executed:
            continue  # Exclude from cohort

        # Determine mode (from findings or status)
        if not mode:
            mode = _parse_mode_from_status(status, run_id)

        # Shadow-only cohort
        if mode != "shadow":
            continue

        # Time filtering
        if timestamp_str:
            try:
                ts = _parse_iso_utc(timestamp_str)
                if from_dt and ts < from_dt:
                    continue
                if to_dt and ts >= to_dt:
                    continue
            except Exception:
                pass

        # Check infra failures
        if findings.get("summary", {}).get("infra_error"):
            infra_failures += 1
        if _check_infra_failure_in_status(status):
            infra_failures += 1

        runs.append({
            "run_id": run_id,
            "findings": findings,
            "timestamp": timestamp_str,
            "status": status
        })

    # Check for unpaired status files (G11 shadow executed but no findings)
    for run_id, status_path in status_by_run.items():
        if run_id in findings_by_run:
            continue

        status = _load_json(status_path)
        g11_executed = False
        for gate in status.get("gates", []):
            if gate.get("gate") == "G11_auditor_review" and gate.get("status") != "SKIPPED":
                g11_executed = True
                break

        if not g11_executed:
            continue

        mode = _parse_mode_from_status(status, run_id)
        if mode == "shadow":
            # Time filtering for status-only runs
            started_utc = status.get("started_utc")
            if started_utc:
                try:
                    ts = _parse_iso_utc(started_utc)
                    if from_dt and ts < from_dt:
                        continue
                    if to_dt and ts >= to_dt:
                        continue
                except Exception:
                    pass

            msg = f"Status with G11 shadow executed but no findings: {status_path.name}"
            unpaired_warnings.append(msg)
            if args.mode == "dossier":
                infra_failures += 1

    # Print warnings
    for w in unpaired_warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    # Aggregate findings
    total_items = 0
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    per_rule: dict[str, dict] = defaultdict(lambda: {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0, "fp_count": 0})
    weekly_buckets: dict[str, dict] = defaultdict(lambda: {"items": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0})

    ch_total = 0
    ch_annotated = 0
    ch_fp_count = 0
    all_schema_versions = set()

    for run in runs:
        findings = run["findings"]
        run_id = run["run_id"]
        timestamp_str = run["timestamp"]

        # Track schema version
        schema_ver = findings.get("reviewed_packet_schema_version", "UNKNOWN")
        all_schema_versions.add(schema_ver)

        # Track items reviewed (ONCE per run)
        items_reviewed = findings.get("summary", {}).get("items_reviewed", 0)
        total_items += items_reviewed

        # ISO week bucketing
        week_key = "UNKNOWN"
        if timestamp_str:
            try:
                ts = _parse_iso_utc(timestamp_str)
                week_key = _iso_week(ts)
            except Exception:
                pass

        # Add items to weekly bucket ONCE per run
        weekly_buckets[week_key]["items"] += items_reviewed

        # Loop through findings for severity counts only
        for finding in findings.get("findings", []):
            finding_id = finding.get("finding_id")
            rule_id = finding.get("rule_id")
            severity = finding.get("severity", "").lower()

            if severity in severity_counts:
                severity_counts[severity] += 1
                per_rule[rule_id][severity] += 1
                per_rule[rule_id]["total"] += 1
                weekly_buckets[week_key][severity] += 1

            # FP analysis (C/H only)
            if severity in ("critical", "high"):
                ch_total += 1
                key = (args.repo_id, run_id, finding_id)
                if key in ledger_annotations:
                    ch_annotated += 1
                    if ledger_annotations[key].get("verdict") == "FP":
                        ch_fp_count += 1
                        per_rule[rule_id]["fp_count"] += 1

    # Compute FP rate and coverage
    fp_rate = None
    annotation_coverage_ch = 1.0  # Auto-pass when no C/H
    if ch_total > 0:
        annotation_coverage_ch = ch_annotated / ch_total
        if ch_annotated > 0:
            fp_rate = ch_fp_count / ch_total

    # Warn about missing schema version in both modes
    if "UNKNOWN" in all_schema_versions:
        print("WARNING: Some findings missing reviewed_packet_schema_version field", file=sys.stderr)

    # Check promotion criteria (dossier mode)
    criteria = {}
    if args.mode == "dossier":
        c0_met = (infra_failures == 0)
        c1_met = "MANUAL_CHECK"
        c2_met = (total_items >= args.min_items)

        # C3: consecutive weeks with min items per week
        sorted_weeks = sorted([w for w in weekly_buckets.keys() if w != "UNKNOWN"])
        consecutive_count = 0
        max_consecutive = 0
        prev_week = None
        for week in sorted_weeks:
            if weekly_buckets[week]["items"] >= args.min_items_per_week:
                if prev_week is None or _is_next_week(prev_week, week):
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 1
                prev_week = week
            else:
                consecutive_count = 0
                prev_week = None

        c3_met = (max_consecutive >= args.min_weeks)

        # C4: FP rate
        c4_met = (fp_rate is None or fp_rate < args.max_fp_rate)

        # C4b: annotation coverage
        c4b_met = (annotation_coverage_ch == 1.0)

        # C5: all v2 packets
        c5_met = (all_schema_versions == {"2.0.0"} or len(all_schema_versions) == 0)
        if "UNKNOWN" in all_schema_versions:
            c5_met = False

        criteria = {
            "c0_infra_health": {"met": c0_met, "value": f"{infra_failures} failures"},
            "c1_24b_close": {"met": c1_met, "value": "MANUAL_CHECK"},
            "c2_min_items": {"met": c2_met, "value": f"{total_items} >= {args.min_items}"},
            "c3_min_weeks": {"met": c3_met, "value": f"{max_consecutive} consecutive weeks >= {args.min_weeks}"},
            "c4_fp_rate": {"met": c4_met, "value": f"{fp_rate:.2%}" if fp_rate is not None else "N/A"},
            "c4b_annotation_coverage": {"met": c4b_met, "value": f"{annotation_coverage_ch:.2%}"},
            "c5_all_v2": {"met": c5_met, "value": f"{len(all_schema_versions)} versions: {sorted(all_schema_versions)}"}
        }

        # Exit 1 if any automated criterion not met
        automated_not_met = [k for k, v in criteria.items() if k != "c1_24b_close" and v["met"] is False]
        if automated_not_met:
            print(f"DOSSIER CRITERIA NOT MET: {automated_not_met}", file=sys.stderr)

    # Build JSON report
    report = {
        "schema_version": "1.0.0",
        "report_type": args.mode,
        "generated_at_utc": _now_utc_iso(),
        "data_range": {
            "from_utc": args.from_utc,
            "to_utc": args.to_utc,
            "runs_included": len(runs)
        },
        "totals": {
            "items_reviewed": total_items,
            **severity_counts
        },
        "fp_analysis": {
            "ledger_loaded": ledger_loaded,
            "ch_total": ch_total,
            "ch_annotated": ch_annotated,
            "ch_unannotated": ch_total - ch_annotated,
            "ch_fp_count": ch_fp_count,
            "fp_rate": fp_rate,
            "annotation_coverage_ch": annotation_coverage_ch
        },
        "per_rule_breakdown": dict(per_rule),
        "weekly_windows": dict(weekly_buckets)
    }

    if args.mode == "dossier":
        report["promotion_criteria"] = criteria

    # Write JSON
    _atomic_write_text(Path(args.output_json), json.dumps(report, indent=2))

    # Build Markdown report
    md_lines = [
        f"# Auditor Calibration Report ({args.mode.upper()})",
        f"",
        f"**Generated:** {report['generated_at_utc']}",
        f"**Runs included:** {len(runs)}",
        f"**Time range:** {args.from_utc or 'N/A'} to {args.to_utc or 'N/A'}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Items reviewed | {total_items} |",
        f"| CRITICAL | {severity_counts['critical']} |",
        f"| HIGH | {severity_counts['high']} |",
        f"| MEDIUM | {severity_counts['medium']} |",
        f"| LOW | {severity_counts['low']} |",
        f"| INFO | {severity_counts['info']} |",
        f"",
        f"## FP Analysis",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Ledger loaded | {ledger_loaded} |",
        f"| C/H total | {ch_total} |",
        f"| C/H annotated | {ch_annotated} |",
        f"| C/H unannotated | {ch_total - ch_annotated} |",
        f"| C/H FP count | {ch_fp_count} |",
        f"| FP rate | {f'{fp_rate:.2%}' if fp_rate is not None else 'N/A'} |",
        f"| Annotation coverage | {annotation_coverage_ch:.2%} |",
        f"",
    ]

    if per_rule:
        md_lines.extend([
            f"## Per-Rule Breakdown",
            f"",
            f"| Rule ID | Total | C | H | M | L | I | FP |",
            f"|---------|-------|---|---|---|---|---|-----|"
        ])
        for rule_id in sorted(per_rule.keys()):
            r = per_rule[rule_id]
            md_lines.append(f"| {rule_id} | {r['total']} | {r['critical']} | {r['high']} | {r['medium']} | {r['low']} | {r['info']} | {r['fp_count']} |")
        md_lines.append("")

    if weekly_buckets:
        md_lines.extend([
            f"## Weekly Windows",
            f"",
            f"| Week | Items | C | H | M | L | I |",
            f"|------|-------|---|---|---|---|---|"
        ])
        for week in sorted(weekly_buckets.keys()):
            w = weekly_buckets[week]
            md_lines.append(f"| {week} | {w['items']} | {w['critical']} | {w['high']} | {w['medium']} | {w['low']} | {w['info']} |")
        md_lines.append("")

    if args.mode == "dossier":
        md_lines.extend([
            f"## Promotion Dossier",
            f"",
            f"| Criterion | Met | Value |",
            f"|-----------|-----|-------|"
        ])
        for crit_id, crit in criteria.items():
            met_str = "✅" if crit["met"] is True else ("❌" if crit["met"] is False else "⚠️")
            md_lines.append(f"| {crit_id} | {met_str} | {crit['value']} |")
        md_lines.append("")

    _atomic_write_text(Path(args.output_md), "\n".join(md_lines))

    # Exit logic
    if args.mode == "dossier" and automated_not_met:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
