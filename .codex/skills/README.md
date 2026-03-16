# Canonical Skill Layout

This is the canonical agent-skill root for this project.

## Hard Stop
- Always load skills from `.codex/skills/`.
- Do not execute workflow logic from `skills/` mirror paths.
- If both paths contain similar names, `.codex/skills/` is source of truth.

## Path Resolution Rule
- All paths in skill files are **repo-root relative** (root = `E:\Code\SOP\quant_current_scope`).
- When executing validator scripts, ensure working directory is repo root.
- Example: `python .codex/skills/_shared/scripts/validate_closure_packet.py` assumes `pwd` is repo root.

## Structure
- `_shared/`: shared hierarchy templates, confidence gate, role injection, field templates
- `saw/`: SAW execution/review skill
- `research-analysis/`: research evidence skill
- `se-executor/`: trigger-based software-engineering execution rigor skill
- `architect-review/`: trigger-based architecture review skill
- `context-bootstrap/`: deterministic context packet generation for `/new` bootstrap
- `expert-researcher/`: forward-looking domain expert guidance with confidence gate
- `project-guider/`: session orchestration, hierarchy confirmation, and skill routing
- `workflow-status/`: phase status aggregation by workflow type (frontend/backend/governance/data/research)
- `web-search/`: web search and external content fetching for current information
- `quick-gate/`: fast validation gate for pre-commit checks (schema, tests, files)
- `doc-draft/`: structured documentation generation from templates and context

## Activation Policy
- `saw` and `research-analysis`: mandatory when their corresponding workflow is invoked.
- `se-executor` and `architect-review`: available + trigger-based by default (not mandatory hooks on day 1).
- `expert-researcher`: invoked when confidence < 80 or explicit expert guidance needed.
- `project-guider`: invoked at session start or when coordinating multi-step work.
- `workflow-status`: invoked by project-guider at session start and before task routing.
- `web-search`: invoked when local context is insufficient or user requests external information.
- `quick-gate`: invoked before git commit/push or when user requests validation.
- `doc-draft`: invoked when user requests documentation creation (phase briefs, decision logs, specs).
- If the same trigger repeats for `>= 2` rounds in the same milestone/session, propose upgrading to mandatory for that milestone and request explicit user approval before enforcing.

## Shared Primitives
- `_shared/hierarchy-init/`: shared Section 0 for hierarchy confirmation (deduped from saw/research-analysis)
- `_shared/confidence-gate/`: routing primitive for confidence-based escalation
- `_shared/role-injection/`: expert role persona instantiation with authority boundaries

## Shared Hierarchy Assets
- `_shared/hierarchy_template.md`
- `_shared/field_templates/scientific.md`
- `_shared/field_templates/financial.md`
- `_shared/field_templates/medical.md`
- `_shared/field_templates/law.md`
- `_shared/field_templates/software_engineering.md`

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

## Model Routing
Each skill declares its model in `agents/openai.yaml`:
- `codex-5.2`: workers (se-executor, context-bootstrap, workflow-status, quick-gate)
- `codex-5.4`: audit/review (saw)
- `claude`: reasoning/sensitive domains (research-analysis, architect-review, expert-researcher, project-guider, web-search, doc-draft)
