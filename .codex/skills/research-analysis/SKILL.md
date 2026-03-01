---
name: research-analysis
description: Analyze domain research evidence from PDFs in docs/research and convert it into planning-grade conclusions. Use when work needs scientific, financial, medical, or law evidence; confirm project hierarchy at init, extract methodology/findings, cross-reference existing researches*.md files, and output one-line logic-chain and formula summaries.
---

# Research Analysis Skill

Use this skill to produce evidence-backed planning support.

## 0. Project Init Hierarchy Confirmation (Hard Stop)
1. At project init, load:
   - `../_shared/hierarchy_template.md`
   - `../_shared/field_templates/<domain>.md`
2. Render hierarchy with locked columns:
   - `Field | Expertise Level | Rationale`
3. Ask user for explicit confirmation:
   - `approve`
   - `edit: <change>`
   - `reject`
4. Do not continue to evidence extraction until explicit approval is received.
5. Session policy:
   - Session definition: current chat/thread.
   - Confirm once per project session.
   - Retrigger only when:
     - a new domain appears outside confirmed hierarchy, or
     - user says `change hierarchy` or `new scope`.
6. Before each research output, re-check that hierarchy confirmation exists in current thread.
7. Required audit stamp in each output:
   - `Hierarchy Confirmation: Approved | Session: <current-thread> | Trigger: <project-init|new-domain|change-scope> | Domains: <list>`

## 1. Collect Inputs
1. Read relevant PDFs from `docs/research/`.
2. Determine domain: `scientific`, `financial`, `medical`, or `law`.
3. Load existing markdown notes matching `researches*.md`.
4. If a PDF is unreadable/corrupted/password-locked:
   - mark it as `unreadable source`,
   - do not infer findings from it,
   - continue with readable sources or return `insufficient evidence` when coverage is inadequate.

## 2. Extract Core Evidence
1. Summarize methodology in one line (sample/design/assumptions).
2. Summarize key finding in one line.
3. Record constraints or external-validity caveats in one line.
4. For each high-confidence claim, assign `ClaimID` (`CLM-01`, `CLM-02`, ...).
5. For each high-confidence claim, attach:
   - `SupportStrength` = `Direct` or `Indirect`,
   - `EvidenceSnippet` (<= 20 words if quoted; <= 30 words if paraphrased).

## 3. Cross-Reference Novelty
1. Compare each new finding against existing `researches*.md` files.
2. Classify delta as `new`, `confirming`, or `conflicting`.
3. If conflicting, state what extra data is needed to resolve conflict.
4. Loop-close rule for unresolved conflicts:
   - if conflicts remain unresolved with current evidence, set `Verdict: BLOCK` for decision closure and carry required data/actions in `Open Risks`.

## 4. Output Contract
1. High-confidence claims:
   - `ClaimID` + one-line claim
   - one-line reason (`industry standard`, `repo constraint`, or `research evidence`)
   - source locator (`SourceID` + page/section) for the claim
   - source text path (`source_text_path`) used for grounding
   - `SupportStrength`, `EvidenceSnippet`, and `snippet_type` (`quoted`/`paraphrased`)
2. Low-certainty items:
   - one-line uncertainty
   - one-line reason
3. Boundary/needs-help items:
   - one-line item
   - one-line reason
4. End with:
   - Closure packet (one line, machine-check format):
     - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
   - Closure count definitions:
     - `ChecksTotal` = number of closure predicates evaluated for this output.
     - `ChecksPassed` = predicates satisfied; `ChecksFailed` = predicates failed or not evaluable.
   - Closure validation:
     - run `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
     - emit `ClosureValidation: PASS/BLOCK`
   - Claim validation:
     - write high-confidence claims to `<claims_json_path>` (JSON list).
     - run `python .codex/skills/_shared/scripts/validate_research_claims.py --claims-json "<claims_json_path>"`.
     - emit `ClaimValidation: PASS/BLOCK`.
   - Confirmed hierarchy snapshot and audit stamp (one line)
   - Logic chain (one line): `if <condition> and <condition> then <implication>`
   - Formula (one line): explicit equation from source or `N/A` if unavailable
   - Closure verdict (one line): `Verdict: PASS/BLOCK`.
   - Closure metrics (one line):
     - `unresolved_conflicts=<int>`, `unreadable_sources=<int>`, `total_sources=<int>`, `claims_total=<int>`, `claims_cited=<int>`.
   - Hard close gate:
     - missing any required closure packet field (`RoundID`, `ScopeID`, `Checks*`) => `BLOCK`.
     - failed closure validation => `BLOCK`.
     - missing `<claims_json_path>` or failed claim validation => `BLOCK`.
     - if `total_sources=0`, force `BLOCK` (`insufficient evidence`) and include missing-source request.
     - any high-confidence claim without `ClaimID` or source locator (`SourceID` + page/section) => `BLOCK`.
     - any high-confidence claim without `SupportStrength=Direct` => downgrade claim to low-certainty or `BLOCK` if claim remains in high-confidence set.
     - any high-confidence claim without `EvidenceSnippet` or with snippet length above cap => `BLOCK`.
     - `PASS` only if `unresolved_conflicts=0`, `claims_total=claims_cited`, and (`unreadable_sources/total_sources`) <= `0.20`.
     - otherwise `BLOCK` with `Open Risks` and `Next verification step`.

## 5. Safety Rules
1. Do not fabricate citations or formulas.
2. If no relevant PDF exists, return `insufficient evidence` and request the missing source.
