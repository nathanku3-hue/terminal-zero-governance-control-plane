from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

def _parse_iso(iso_str: str) -> datetime | None:
    try:
        s = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, required=True, help="Path to dispatch_manifest.json")
    parser.add_argument("--scan-root", type=str, required=True, help="Root to scan for dispatch_ack.json")
    parser.add_argument("--timeout-minutes", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    man_path = Path(args.manifest).resolve()
    scan_root = Path(args.scan_root).resolve()
    
    if not man_path.exists():
        print(f"Manifest not found: {man_path}")
        return 1
        
    with open(man_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    expected_tasks = {t["correlation_id"]: dict(t) for t in manifest.get("tasks", [])}
    man_hash = manifest.get("command_plan_hash_sha256")
    deadline = _parse_iso(manifest.get("ack_deadline_utc", ""))
    
    # 1. Gather acks
    found_acks = []
    for p in scan_root.rglob("dispatch_ack.json"):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        try:
             with open(p, "r", encoding="utf-8") as f:
                 ack = json.load(f)
                 found_acks.append(ack)
        except Exception:
             pass
             
    # map ack by correlation_id
    ack_map = {a.get("correlation_id"): a for a in found_acks if a.get("correlation_id")}
    
    issues = {
        "missing": [],
        "hash_mismatch": [],
        "lifecycle_violation": [],
        "unverifiable_completion": [],
        "stuck": []
    }
    
    for cid, task_spec in expected_tasks.items():
        if cid not in ack_map:
            issues["missing"].append(cid)
            continue
            
        ack = ack_map[cid]
        
        # Hash match
        if ack.get("command_plan_hash_sha256") != man_hash:
            issues["hash_mismatch"].append(cid)
            continue
            
        cur_state = ack.get("current_state")
        lifecycle = ack.get("lifecycle", [])
        states_recorded = {s.get("state"): s for s in lifecycle}
        
        # Lifecycle violations
        if "COMPLETED" in states_recorded and "STARTED" not in states_recorded:
            issues["lifecycle_violation"].append(f"{cid}: COMPLETED without STARTED")
            
        if "COMPLETED" in states_recorded:
             c_rec = states_recorded["COMPLETED"]
             # Verify bound artifacts
             if not c_rec.get("bound_artifacts") and not c_rec.get("bound_tests"):
                  issues["unverifiable_completion"].append(f"{cid}: Missing bound artifacts/tests")
                  
        if cur_state == "HEARTBEATING":
            h_rec = states_recorded.get("HEARTBEATING", {})
            h_time = _parse_iso(h_rec.get("utc", ""))
            if h_time:
                elapsed = (datetime.now(timezone.utc) - h_time).total_seconds() / 60.0
                if elapsed > args.timeout_minutes: # Simplified STUCK check
                    issues["stuck"].append(cid)
                    
    if args.dry_run:
        print("[DRY-RUN] Validator results:")
        print(json.dumps(issues, indent=2))
        return 0
        
    if issues["unverifiable_completion"]:
        print("Error: Unverifiable completion (NO BOUND ARTIFACTS):", issues["unverifiable_completion"])
        return 5
        
    if issues["stuck"]:
        print("Error: Tasks stuck in HEARTBEATING:", issues["stuck"])
        return 4
        
    if issues["lifecycle_violation"]:
        print("Error: Lifecycle violations:", issues["lifecycle_violation"])
        return 3
        
    if issues["hash_mismatch"]:
        print("Error: Hash mismatches:", issues["hash_mismatch"])
        return 2
        
    if issues["missing"]:
        now = datetime.now(timezone.utc)
        if deadline and now > deadline:
            print("Error: Acks missing past deadline:", issues["missing"])
            return 1
            
    return 0

if __name__ == "__main__":
    sys.exit(main())
