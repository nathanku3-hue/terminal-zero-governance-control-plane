"""GovernanceClient SDK usage example.

# Run from quant_current_scope/ repo root:
#   python docs/examples/sdk_usage_example.py
#
# This script must be executed from the governed repo root so that
# docs/context/ paths resolve correctly. Running from a subdirectory
# or an arbitrary directory will produce ERROR or empty status.
"""
from __future__ import annotations

if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    # Ensure the src layout is importable when running in dev without install
    _src = Path(__file__).parent.parent.parent / "src"
    if _src.exists() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

    from sop import GovernanceClient

    # --- 1. Instantiate the client pointing at the repo root -----------------
    client = GovernanceClient(repo_root=".")

    # --- 2. Run one loop cycle (skip phase-end for fast dev iterations) -------
    print("[sdk_usage_example] Running loop cycle...")
    summary = client.run(skip_phase_end=True)
    print(f"[sdk_usage_example] final_result = {summary.get('final_result')}")
    print(f"[sdk_usage_example] final_exit_code = {summary.get('final_exit_code')}")

    # --- 3. Read status from the written artifact (no re-run) -----------------
    status = client.status()
    if status is not None:
        print(f"[sdk_usage_example] status().final_result = {status.get('final_result')}")
    else:
        print("[sdk_usage_example] status() returned None (no prior summary on disk)")

    # --- 4. Query the last 5 audit log entries --------------------------------
    entries = client.audit(tail=5)
    print(f"[sdk_usage_example] audit(tail=5) returned {len(entries)} entries")
    for entry in entries:
        actor = entry.get("actor", "?")
        decision = entry.get("decision", "?")
        gate = entry.get("gate", "?")
        print(f"  [{decision}] actor={actor} gate={gate}")

    # --- 5. Optional: policy_validate (requires Phase 2) ---------------------
    # Uncomment and point at a real rule file to test:
    # try:
    #     rules = client.policy_validate("docs/context/policy_rules.json")
    #     print(f"[sdk_usage_example] {len(rules)} policy rule(s) valid")
    # except RuntimeError as exc:
    #     print(f"[sdk_usage_example] policy engine not available: {exc}")

    print("[sdk_usage_example] Done.")
