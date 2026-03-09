from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from scripts.utils.time_utils import utc_now
from scripts.utils.time_utils import utc_iso

# Default settings from the plan
DEFAULT_TTL_SECONDS = 300
DEFAULT_ESCALATION_MINUTES = 90
DEFAULT_MAX_DEPTH = 4

def _parse_iso(iso_str: str) -> datetime | None:
    try:
        # replace Z with +00:00 for python 3.10- compatibility if needed
        s = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise

def _escalation_dedupe_key(event: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(event.get("worker_id", "")),
        str(event.get("task_id", "")),
        str(event.get("stale_since_utc", "")),
        str(event.get("recommended_action", "")),
    )

def _append_deduped_escalations(
    existing_events: list[Any], new_events: list[dict[str, Any]]
) -> list[Any]:
    merged: list[Any] = list(existing_events)
    active_keys: set[tuple[str, str, str, str]] = set()

    for event in merged:
        if not isinstance(event, dict):
            continue
        if event.get("resolved") is True:
            continue
        active_keys.add(_escalation_dedupe_key(event))

    for event in new_events:
        key = _escalation_dedupe_key(event)
        if key in active_keys:
            continue
        merged.append(event)
        if event.get("resolved") is not True:
            active_keys.add(key)

    return merged

def _find_worker_files(scan_root: Path, max_depth: int) -> list[Path]:
    results = []
    
    def walk(directory: Path, current_depth: int):
        if current_depth > max_depth:
            return
            
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    # skip typical ignores
                    if item.name in (".git", ".venv", "node_modules", "__pycache__"):
                        continue
                    walk(item, current_depth + 1)
                elif item.name == "worker_status.json" and item.parent.name == "context" and item.parent.parent.name == "docs":
                    results.append(item)
                elif item.name == "worker_status.json":
                    # allow finding it at other structures if named correctly
                    results.append(item)
        except PermissionError:
            pass
            
    walk(scan_root, 0)
    
    # Deduplicate in case of symlinks
    return list(set(results))

def _evaluate_staleness(heartbeat_node: dict, now: datetime, global_ttl_sec: int, global_esc_min: int) -> tuple[str, bool]:
    last_write_str = heartbeat_node.get("last_write_utc")
    if not last_write_str:
        return "STALE", False
        
    last_write = _parse_iso(last_write_str)
    if not last_write:
        return "STALE", False
        
    ttl = heartbeat_node.get("ttl_seconds", global_ttl_sec)
    grace = heartbeat_node.get("clock_skew_grace_seconds", 30)
    escalation_threshold = (global_esc_min * 60)
    
    effective_fresh = ttl + grace
    
    wall_clock_elapsed = (now - last_write).total_seconds()
    
    # Diagnostic flag
    mono = heartbeat_node.get("monotonic_elapsed_seconds")
    clock_skew_suspect = False
    if mono is not None and wall_clock_elapsed > effective_fresh and mono < effective_fresh:
        clock_skew_suspect = True

    if wall_clock_elapsed <= effective_fresh:
        return "FRESH", clock_skew_suspect
    elif wall_clock_elapsed > escalation_threshold:
        return "ESCALATED", clock_skew_suspect
    else:
        return "STALE", clock_skew_suspect

def check_self_signoff(completion_log: list) -> bool:
    for task in completion_log:
        implementer = task.get("implementer_id")
        if not implementer:
            continue
        actual_signoffs = task.get("expert_signoffs", {}).get("actual", [])
        for block in actual_signoffs:
            sb = block.get("signoff_by")
            if sb and sb == implementer:
                return True
    return False

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-root", type=str, required=True, help="Root directory to scan for worker_status.json")
    parser.add_argument("--output", type=str, required=True, help="Output path for the aggregate JSON")
    parser.add_argument("--escalation-output", type=str, required=False, help="Output path for escalation events")
    parser.add_argument("--ttl-seconds", type=int, default=DEFAULT_TTL_SECONDS)
    parser.add_argument("--escalation-threshold-minutes", type=int, default=DEFAULT_ESCALATION_MINUTES)
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writes, exit 0")
    
    args = parser.parse_args()
    
    scan_root = Path(args.scan_root).resolve()
    if not scan_root.is_dir():
        print(f"Error: scan_root={scan_root} is not a valid directory.", file=sys.stderr)
        return 1
        
    out_path = Path(args.output).resolve()
    esc_out = Path(args.escalation_output).resolve() if args.escalation_output else None

    now = utc_now()

    worker_files = _find_worker_files(scan_root, DEFAULT_MAX_DEPTH)

    has_self_signoff = False
    has_escalated = False
    has_stale = False

    aggregate_payload = {
        "generated_utc": utc_iso(now),
        "workers": [],
        "summary": {
            "total_workers": 0,
            "executing": 0,
            "idle": 0,
            "stale": 0,
            "escalated": 0,
            "overall_health": "OK"
        },
        "parse_failures": []
    }

    escalations = []
    
    for wf in worker_files:
        try:
            with open(wf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {wf}: {e}", file=sys.stderr)
            aggregate_payload["parse_failures"].append({
                "file": str(wf),
                "error": str(e),
                "timestamp_utc": utc_iso(now)
            })
            continue
            
        worker_id = data.get("worker_id", "Unknown")
        heartbeat = data.get("heartbeat", {})
        sla = data.get("sla", {})
        
        status, skew_suspect = _evaluate_staleness(
            heartbeat, now, args.ttl_seconds, args.escalation_threshold_minutes
        )
        
        if status == "STALE":
            has_stale = True
            sla["escalation_status"] = "WARNING"
            aggregate_payload["summary"]["stale"] += 1
        elif status == "ESCALATED":
            has_escalated = True
            sla["escalation_status"] = "ESCALATED"
            aggregate_payload["summary"]["escalated"] += 1
            
            task_id = heartbeat.get("current_task", {}).get("task_id", "Unknown")
            stale_since = None # We cannot know exact stale_since without history, fallback to last_write
            last_write = _parse_iso(heartbeat.get("last_write_utc", ""))
            
            esc_event = {
                "event_id": f"ESC-{now.strftime('%Y%m%d%H%M%S')}-{worker_id}",
                "worker_id": worker_id,
                "task_id": task_id,
                "stale_since_utc": heartbeat.get("last_write_utc"),
                "stale_duration_minutes": ((now - last_write).total_seconds() / 60) if last_write else 0,
                "clock_skew_suspect": skew_suspect,
                "escalated_utc": utc_iso(now),
                "recommended_action": "CHECK_WORKER_ALIVE",
                "action_taken": None,
                "resolved": False
            }
            escalations.append(esc_event)
            
        elif status == "FRESH":
            sla["escalation_status"] = "OK"
            
        if check_self_signoff(data.get("completion_log", [])):
            has_self_signoff = True
            
        hb_status = heartbeat.get("status", "unknown")
        if hb_status == "executing":
            aggregate_payload["summary"]["executing"] += 1
        elif hb_status == "idle":
            aggregate_payload["summary"]["idle"] += 1
            
        data["sla"] = sla
        aggregate_payload["workers"].append(data)
        aggregate_payload["summary"]["total_workers"] += 1
        
    # Health derivation
    if has_escalated:
        aggregate_payload["summary"]["overall_health"] = "ESCALATED"
    elif has_stale:
         aggregate_payload["summary"]["overall_health"] = "WARNING"
         
    # Dry-run handling
    if args.dry_run:
        print("[DRY-RUN] Aggregate output:")
        print(json.dumps(aggregate_payload, indent=2))
        
        if escalations:
            print("\n[DRY-RUN] Escalation Events generated:")
            print(json.dumps({"events": escalations}, indent=2))
            
        if has_self_signoff:
            print("\n[DRY-RUN] ⚠️ Self-signoff detected.")
        sys.exit(0)
        
    # Writing outputs
    _atomic_write_json(out_path, aggregate_payload)
    
    if escalations and esc_out:
        if esc_out.exists():
            try:
                with open(esc_out, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    overall_esc = existing.get("events", [])
            except Exception:
                overall_esc = []
        else:
            overall_esc = []

        if not isinstance(overall_esc, list):
            overall_esc = []

        overall_esc = _append_deduped_escalations(overall_esc, escalations)
            
        _atomic_write_json(esc_out, {"events": overall_esc})
        
    # Exit codes
    if has_self_signoff:
        return 3
    elif has_escalated:
        return 2
    elif has_stale:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
