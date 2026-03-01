---
name: saw
description: Subagents-After-Work execution and review protocol for any non-trivial change. Use when a work round finishes and Codex must run implementer/reviewer passes, reconcile findings, and publish a PASS/BLOCK report with document-change visibility and GitHub-optimized doc sorting.
---

# SAW Skill

Deprecated mirror.

## Hard Stop
1. Do not execute from this path.
2. Redirect to canonical skill: `.codex/skills/saw/SKILL.md`.
3. If canonical skill is readable, auto-redirect immediately and do not execute mirror logic.
4. Fallback behavior:
   - if canonical skill is missing/unreadable, enter emergency mirror mode from this file,
   - state `MirrorFallback: skills/saw/SKILL.md`,
   - request user approval to continue before any execution,
   - in mirror mode, run canonical-minimum SAW blocks:
     - findings table,
     - in-scope vs inherited scope split,
     - hierarchy stamp (`Hierarchy Confirmation` + `FallbackSource`),
     - `ClosurePacket` line + `ClosureValidation`,
     - `SAWBlockValidation`,
     - `SAW Verdict: PASS/BLOCK`, `Open Risks`, `Next action`.
   - validate closure packet with:
     - `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
   - validate SAW blocks with:
     - `python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file "<saw_report_path>"`
5. Mirror close rule:
   - if canonical is missing/unreadable and user declines mirror mode, return `Verdict: BLOCK`.
   - if mirror mode is used and any required SAW block is missing, return `Verdict: BLOCK`.
   - if mirror mode is used and closure validation fails, return `Verdict: BLOCK`.
   - if mirror mode is used and `SAWBlockValidation=BLOCK`, return `Verdict: BLOCK`.
   - for any `BLOCK`, include one-line `Next action`.
