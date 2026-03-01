---
name: context-bootstrap
description: Load prior milestone state and next TODOs at session start using deterministic context artifacts.
allow_implicit_invocation: true
---

# Context Bootstrap Skill

Use this skill on `/new`, explicit `$context-bootstrap`, or prompts like "boot/start session/what's next".
Do not trigger for narrow code-edit requests.

## Scope
1. Ensure artifacts are fresh:
   - run `.venv\Scripts\python scripts/build_context_packet.py`
   - run `.venv\Scripts\python scripts/build_context_packet.py --validate`
2. Load:
   - `docs/context/current_context.json`
   - `docs/context/current_context.md`
3. Emit startup packet with exactly 4 sections:
   - `What Was Done`
   - `What Is Locked`
   - `What Is Next`
   - `First Command`

## Default Run
```powershell
.\.venv\Scripts\python scripts/build_context_packet.py
.\.venv\Scripts\python scripts/build_context_packet.py --validate
```

## Default Outputs
- `docs/context/current_context.json`
- `docs/context/current_context.md`

## Notes
- JSON schema key order is fixed by `PACKET_KEYS` in `scripts/build_context_packet.py`.
- Validation fails non-zero when artifacts are stale/missing or schema contract drifts.
