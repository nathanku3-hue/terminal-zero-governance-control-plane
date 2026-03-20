from __future__ import annotations

import argparse
import sys
from pathlib import Path
import yaml

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to pm_to_code_traceability.yaml")
    parser.add_argument("--strict", action="store_true", help="Fail if any directive is UNMAPPED")
    parser.add_argument("--require-test", action="store_true", help="Fail if code_diffs lack validators")
    parser.add_argument("--dry-run", action="store_true", help="Print findings without exiting non-zero")
    args = parser.parse_args()
    
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Error: Traceability file not found at {in_path}", file=sys.stderr)
        return 1
        
    try:
        with open(in_path, "r", encoding="utf-8") as f:
            trace_data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Failed to load yaml: {e}")
        return 1
        
    directives = trace_data.get("directives", [])
    unmapped = []
    uncovered_diffs = []
    
    for d in directives:
        status = d.get("status", "UNMAPPED")
        d_id = d.get("directive_id", "Unknown")
        
        if status == "UNMAPPED":
            unmapped.append(d_id)
            
        trace = d.get("traceability", {})
        diffs = trace.get("code_diffs", [])
        tests = trace.get("validators", [])
        
        if diffs and not tests:
            uncovered_diffs.append(d_id)
            
    has_unmapped = False
    has_uncovered = False
    
    if args.strict and unmapped:
        print("[ERROR] UNMAPPED directives found:")
        for d in unmapped:
            print(f"  - {d}")
        has_unmapped = True
        
    if args.require_test and uncovered_diffs:
        print("[ERROR] Directives with code diffs but no validators:")
        for d in uncovered_diffs:
            print(f"  - {d}")
        has_uncovered = True
        
    if args.dry_run:
        print("[DRY-RUN] Script complete. Findings printed above. Forcing exit 0.")
        return 0
        
    if has_unmapped:
        return 1
    elif has_uncovered:
        return 2
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
