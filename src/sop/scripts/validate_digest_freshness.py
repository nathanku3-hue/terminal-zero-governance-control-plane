from __future__ import annotations

import argparse
import sys
import re
from datetime import datetime
from datetime import timezone
from pathlib import Path

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="Path to ceo_bridge_digest.md")
    parser.add_argument("--ttl-minutes", type=int, default=60, help="Freshness threshold")
    parser.add_argument("--dry-run", action="store_true", help="Print findings without exiting non-zero")
    args = parser.parse_args()
    
    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Error: Digest not found at {in_path}", file=sys.stderr)
        return 1
        
    with open(in_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    m = re.search(r"Generated:\s*([0-9T:.\-Z]+)", content)
    if not m:
        print(f"Error: Could not find Generated timestamp in {in_path}", file=sys.stderr)
        return 1
        
    date_str = m.group(1).replace("Z", "+00:00")
    try:
        gen_time = datetime.fromisoformat(date_str)
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
        return 1
        
    now = _now_utc()
    elapsed = (now - gen_time).total_seconds() / 60.0
    
    if args.dry_run:
        print(f"[DRY-RUN] File elapsed: {elapsed:.1f} min / TTL: {args.ttl_minutes} min")
        return 0
        
    if elapsed > args.ttl_minutes:
        print(f"Digest STALE. Generated {elapsed:.1f} min ago (> {args.ttl_minutes})")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
