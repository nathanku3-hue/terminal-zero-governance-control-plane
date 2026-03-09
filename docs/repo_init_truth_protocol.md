# Repo-Init Truth Protocol (Lean)

Status: Active  
Scope: Repo-specific governance/process guidance (docs-only; no runtime authority change)

## Why there is no universal “ultimate truth layer”

- Different repos carry different domain assumptions, data constraints, and risk semantics.
- A universal truth engine would over-generalize and create false confidence across domains.
- Therefore, truth protocol must be defined at repo-init and bound to that repo’s canonical artifacts.

## Repo-Specific Truth Protocol (minimum)

1. Define canonical sources for this repo (for example: product intent, decision log, phase scope docs, generated evidence artifacts).
2. Define explicit non-goals and module boundaries for each change.
3. For high-semantic-risk claims, run a falsification pass before coding.

## High-Semantic-Risk Falsification (minimal rollout)

- Use when a claim can be syntactically correct but domain-wrong (for example finance/quant semantics, governance semantics, safety interpretation).
- Use template: `docs/templates/domain_falsification_pack.md`.
- Suggested live working file: `docs/context/domain_falsification_pack_latest.md`.
- This is a planning/review aid bound to the repo-specific truth protocol; it does not create a new decision authority.
- When an active round contract sets `DOMAIN_FALSIFICATION_REQUIRED=YES`, closure validates the pack structurally before escalation.

## Operator Trigger (when to use)

Use the falsification pack if any of these are true:
- claim has high business/decision impact and weak direct artifact evidence,
- multiple plausible domain interpretations exist,
- failure mode is semantic misunderstanding rather than unit-test failure.

## Authority Boundary

- Startup intake, active round contract, and current authority matrix remain authoritative.
- Falsification pack supports better decisions but does not override Worker/Auditor/PM/CEO ownership.
