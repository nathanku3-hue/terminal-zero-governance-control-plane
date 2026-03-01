---
name: research-analysis
description: Analyze domain research evidence from PDFs in docs/research and convert it into planning-grade conclusions. Use when work needs scientific, financial, medical, or law evidence; extract methodology/findings, cross-reference existing researches*.md files, and output one-line logic-chain and formula summaries.
---

# Research Analysis Skill

Deprecated mirror.

## Hard Stop
1. Do not execute from this path.
2. Redirect to canonical skill: `.codex/skills/research-analysis/SKILL.md`.
3. If canonical skill is readable, auto-redirect immediately and do not execute mirror logic.
4. Fallback behavior:
   - if canonical skill is missing/unreadable, enter emergency mirror mode from this file,
   - state `MirrorFallback: skills/research-analysis/SKILL.md`,
   - request user approval to continue before evidence processing,
   - in mirror mode, run canonical-minimum research blocks:
     - claim-level rows (`ClaimID`, `SourceID`, `source_text_path`, page/section, `SupportStrength`, `EvidenceSnippet`, `snippet_type`),
     - closure metrics (`claims_total`, `claims_cited`, `total_sources`, `unreadable_sources`, `unresolved_conflicts`),
     - `ClosurePacket` line + `ClosureValidation`,
     - `ClaimValidation`,
     - `Verdict: PASS/BLOCK`, `Open Risks`, `Next verification step`.
   - validate closure packet with:
     - `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
   - validate claims with:
     - `python .codex/skills/_shared/scripts/validate_research_claims.py --claims-json "<claims_json_path>"`
5. Mirror close rule:
   - if canonical is missing/unreadable and user declines mirror mode, return `Verdict: BLOCK`.
   - if mirror mode is used and any required research block is missing, return `Verdict: BLOCK`.
   - if mirror mode is used and closure validation fails, return `Verdict: BLOCK`.
   - if mirror mode is used and `ClaimValidation=BLOCK`, return `Verdict: BLOCK`.
   - if mirror mode is used and `claims_total != claims_cited`, return `Verdict: BLOCK`.
   - for any `BLOCK`, include one-line `Next verification step`.
