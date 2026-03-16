---
name: saw
description: Subagents-After-Work execution and review protocol
---

# SAW Skill

## 0. Project Init
**Reference**: For system wiring, see `AGENTS.md` Section 3 and `docs/workflow_wiring_detailed.md`.

## 1. Validation
- Validate closure packet: `python .codex/skills/_shared/scripts/validate_closure_packet.py`
- Validate SAW blocks: `python .codex/skills/_shared/scripts/validate_saw_report_blocks.py`

## 2. Phase-End
- Use template: `references/phase_end_handover_template.md`
- Write handover: `docs/handover/phase<NN>_handover.md`
