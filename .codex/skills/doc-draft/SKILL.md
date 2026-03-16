---
name: doc-draft
description: Generate structured documentation drafts from templates, evidence, and context. Use when creating phase briefs, decision logs, or technical documentation.
---

# Doc-Draft Skill

Generate high-quality documentation drafts following project templates and conventions.

## 0. Activation Triggers
- User requests documentation creation (phase brief, decision log, technical spec)
- User says "draft a doc", "create documentation", "write a brief"
- Project-guider routes documentation tasks here

## 1. Input Requirements
1. Document type (phase_brief, decision_log, technical_spec, runbook, etc.)
2. Template path (if available in docs/templates/)
3. Context sources:
   - Relevant artifacts from docs/context/
   - Related phase briefs from docs/phase_brief/
   - Decision log entries from docs/decision_log.md
4. Key content requirements from user

## 2. Draft Generation Process
1. Load template if available
2. Gather context from specified sources
3. Extract relevant data:
   - Phase metadata (ID, name, dates, owner)
   - Deliverables and success criteria
   - Dependencies and risks
   - Evidence paths and validation results
4. Generate draft following template structure
5. Validate completeness:
   - All required sections present
   - Evidence paths exist
   - Cross-references valid
   - Workflow profile sums to 100% (for phase briefs)

## 3. Validation Checks
For phase briefs:
- Workflow weight sums to 100%
- All deliverables have workflow_type
- All success criteria have workflow_type
- Realm-specific criteria match declared realm
- Evidence paths are valid

For decision logs:
- Decision ID follows format (D-XXX)
- Date in ISO format
- Status is valid (proposed, approved, rejected, superseded)
- Impact assessment present

## 4. Output Contract
1. Emit draft to specified path
2. Include validation results:
   - `DraftValidation: PASS/FAIL`
   - List any missing sections or validation errors
3. Suggest next actions:
   - Review and edit draft
   - Run validators
   - Request PM approval

## 5. Model Routing
Use `claude` model for reasoning and structured generation.
