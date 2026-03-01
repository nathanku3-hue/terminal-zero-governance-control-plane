from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path
import fnmatch
import yaml

def git_diff_files(since_commit: str, cwd: Path) -> list[str]:
    # Using relative paths
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", since_commit],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return [f.strip() for f in res.stdout.split() if f.strip()]
    except Exception as e:
        print(f"Error running git diff: {e}")
        return []

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traceability", type=str, required=True)
    parser.add_argument("--since-commit", type=str, required=True)
    parser.add_argument("--include", type=str, action="append", default=[])
    parser.add_argument("--exclude", type=str, action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    tr_path = Path(args.traceability).resolve()
    repo_root = tr_path.parent
    
    if not tr_path.exists():
        print(f"Error: {tr_path} not found")
        return 1
        
    try:
        with open(tr_path, "r", encoding="utf-8") as f:
            tr_data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading yaml: {e}")
        return 1
        
    directives = tr_data.get("directives", [])
    covered_files = set()
    for d in directives:
        for diff in d.get("traceability", {}).get("code_diffs", []):
            if diff.get("file"):
                # normalize path separators
                covered_files.add(diff["file"].replace("\\", "/"))
                
    changed_raw = git_diff_files(args.since_commit, repo_root)
    
    # Filter includes
    changed_filtered = []
    if args.include:
        for f in changed_raw:
            if any(fnmatch.fnmatch(f, p) for p in args.include):
                changed_filtered.append(f)
    else:
        # Default include everything
        changed_filtered = changed_raw
        
    # Filter excludes
    if args.exclude:
        changed_filtered = [f for f in changed_filtered if not any(fnmatch.fnmatch(f, e) for e in args.exclude)]
        
    orphans = []
    for cf in changed_filtered:
        if cf not in covered_files:
            orphans.append(cf)
            
    if args.dry_run:
        print(f"[DRY-RUN] Found {len(orphans)} orphans out of {len(changed_filtered)} filtered changed files.")
        if orphans:
             for o in orphans:
                  print(f"  - {o}")
        return 0
        
    if orphans:
        print(f"[ERROR] Found {len(orphans)} unmapped orphan changes:")
        for o in orphans:
             print(f"  - {o}")
        print("\nThese files were changed but are not mapped to any PM directive in traceability yaml.")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
