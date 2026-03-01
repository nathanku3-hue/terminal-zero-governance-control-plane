# Canonical Skill Layout

This is the canonical agent-skill root for this project.

## Structure
- `_shared/`: shared hierarchy templates
- `saw/`: SAW execution/review skill
- `research-analysis/`: research evidence skill
- `se-executor/`: trigger-based software-engineering execution rigor skill
- `architect-review/`: trigger-based architecture review skill
- `context-bootstrap/`: deterministic context packet generation for `/new` bootstrap

## Activation Policy
- `saw` and `research-analysis`: mandatory when their corresponding workflow is invoked.
- `se-executor` and `architect-review`: available + trigger-based by default (not mandatory hooks on day 1).
- If the same trigger repeats for `>= 2` rounds in the same milestone/session, propose upgrading to mandatory for that milestone and request explicit user approval before enforcing.

## Shared Hierarchy Assets
- `_shared/hierarchy_template.md`
- `_shared/field_templates/scientific.md`
- `_shared/field_templates/financial.md`
- `_shared/field_templates/medical.md`
- `_shared/field_templates/law.md`

## Shared Validators
- `_shared/scripts/validate_closure_packet.py`
  - Validates `ClosurePacket` fields and checks arithmetic (`ChecksPassed + ChecksFailed = ChecksTotal`).
  - Supports required `OpenRisks` and `NextAction` checks when `Verdict=BLOCK`.
- `_shared/scripts/validate_saw_report_blocks.py`
  - Validates required SAW report blocks and required scope-split tokens.
- `_shared/scripts/validate_se_evidence.py`
  - Validates `TaskID->EvidenceID` mapping, `run_id` consistency, and evidence freshness.
- `_shared/scripts/validate_research_claims.py`
  - Validates high-confidence claim citation completeness and snippet grounding to source text.
- `_shared/scripts/validate_architect_calibration.py`
  - Validates active architect profile against historical outcome calibration.
