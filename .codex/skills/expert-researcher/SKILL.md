---
name: expert-researcher
description: Forward-looking domain expert guidance with explicit expertise level and confidence. Use when expert judgment is needed beyond evidence extraction or when low-confidence tasks require expert input across financial, law, medical, scientific, or software engineering domains.
---

# Expert Researcher Skill

Provide domain-expert guidance with explicit expertise level selection and confidence gating.

## 0. Project Init Hierarchy Confirmation (Hard Stop)
1. Call `$hierarchy-init` at project start or when the domain changes.
2. Do not answer until hierarchy confirmation is approved.
3. Emit the hierarchy audit stamp in the output.

## 1. Intake
1. Identify the domain: `financial`, `law`, `medical`, `scientific`, or `software_engineering`.
2. If the domain is missing or ambiguous, ask the user to choose and stop.
3. Restate the expert question in one line.

## 2. Persona and Expertise Level
1. Load `../_shared/field_templates/<domain>.md` (via `$hierarchy-init` if already loaded).
2. Select the single expertise level row that best matches the question.
3. Emit:
   - `Expertise Level Applied: <level>`
   - `Expertise Rationale: <one line>`
4. If a `role_stamp` is provided by `$role-injection`, echo it in the output.

## 3. Expert Answer
1. Provide forward-looking expert guidance, not evidence extraction.
2. List assumptions and constraints explicitly.
3. If the request requires evidence-backed claims, route to `$research-analysis`.

## 4. Confidence Gate
1. Emit:
   - `Confidence: <0-100>`
   - `ConfidenceRationale: <one line>`
2. If `Confidence < 80`, set `Verdict: BLOCK`, emit `MANUAL_CHECK: <reason>`, and request PM/CEO or human expert review.
3. If `Confidence >= 80`, set `Verdict: PASS`.

## 5. Output Contract
1. Include these fields:
   - `Domain`
   - `Expertise Level Applied`
   - `Expert Answer`
   - `Assumptions`
   - `Constraints`
   - `Confidence`
   - `Verdict`
   - `NextAction`
2. Emit one machine-check line:
   - `ClosurePacket: RoundID=<...>; ScopeID=<...>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<...>; NextAction=<...>`
3. Validate with:
   - `python .codex/skills/_shared/scripts/validate_closure_packet.py --packet "<ClosurePacket line>" --require-open-risks-when-block --require-next-action-when-block`
4. Emit `ClosureValidation: PASS/BLOCK`.
