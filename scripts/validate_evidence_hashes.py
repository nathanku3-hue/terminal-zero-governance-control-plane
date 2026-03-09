from __future__ import annotations

import argparse
import sys
import hashlib
from pathlib import Path
import yaml

def verify_hash(evidence_dir: Path, declared_hash: str) -> bool:
    if not declared_hash.startswith("sha256:"):
        return False
        
    h_val = declared_hash[7:]
    expected_file = evidence_dir / f"{h_val}.log"
    if not expected_file.exists():
        print(f"Missing evidence backing file: {expected_file.name}", file=sys.stderr)
        return False
        
    try:
        with open(expected_file, "rb") as f:
            content = f.read()
            actual_hash = hashlib.sha256(content).hexdigest()
            return actual_hash == h_val
    except Exception as e:
        print(f"Failed to hash {expected_file.name}: {e}", file=sys.stderr)
        return False

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to pm_to_code_traceability.yaml")
    parser.add_argument("--evidence-dir", type=str, required=True, help="Directory containing evidence hash files")
    parser.add_argument("--dry-run", action="store_true", help="Print findings without exiting non-zero")
    args = parser.parse_args()
    
    in_path = Path(args.input).resolve()
    ev_dir = Path(args.evidence_dir).resolve()
    
    if not in_path.exists():
        print(f"Error: Traceability file not found at {in_path}", file=sys.stderr)
        return 1
        
    try:
        with open(in_path, "r", encoding="utf-8") as f:
            trace_data = yaml.safe_load(f) or {}
    except Exception:
        return 1
        
    directives = trace_data.get("directives", [])
    
    has_hash_mismatch = False
    
    for d in directives:
        d_id = d.get("directive_id", "Unknown")
        
        # Check actual signoff evidence hashes.
        actual_signoffs = d.get("actual_signoff_experts", [])
        for block in actual_signoffs:
            ev_hash = block.get("evidence_hash")
            if ev_hash and not verify_hash(ev_dir, ev_hash):
                print(f"[ERROR] Hash mismatch for {d_id} signature: {ev_hash}")
                has_hash_mismatch = True
                
        # Check validator hashes
        trace = d.get("traceability", {})
        tests = trace.get("validators", [])
        for v in tests:
            ev_hash = v.get("output_hash_sha256")
            if ev_hash and not verify_hash(ev_dir, ev_hash):
                print(f"[ERROR] Hash mismatch for {d_id} validator: {ev_hash}")
                has_hash_mismatch = True
                
    if args.dry_run:
        print("[DRY-RUN] Script complete. Findings printed above. Forcing exit 0.")
        return 0
        
    if has_hash_mismatch:
        return 1

    return 0
    
if __name__ == "__main__":
    sys.exit(main())
