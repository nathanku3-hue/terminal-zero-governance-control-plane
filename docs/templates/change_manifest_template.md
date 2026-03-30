# Change Manifest Template

> **Canonical source:** src/sop/templates/change_manifest_template.md
> This copy in docs/templates/ is a workspace mirror. Do not edit here — edit the canonical source instead.

Use this template for big changes before coding.

## Header
- ManifestID: `<YYYYMMDD-short-id>`
- Author/Operator: `<name>`
- DateUTC: `<ISO8601>`
- TriggerType: `<cross_module|architecture|high_risk_one_way|other>`

## Scope
- Objective: `<what changes>`
- In Scope Modules: `<explicit module/file boundaries>`
- Out of Scope / Non-Goals: `<explicit exclusions>`

## Product Frame
- ProductStageNow: `<current product/maturity stage>`
- ProductStageIntent: `<target stage this change supports>`
- ProductStageOutOfScope: `<stage change explicitly out of scope>`
- ProductProblemThisRound: `<product/user/system problem this change addresses>`
- WhyNow: `<why this change matters now>`
- IfWeSkipThis: `<cost of skipping this change>`

## Planned Surface Lifecycle
- PlannedSurfaceName: `<primary surface/artifact/component this change shapes>`
- PlannedSurfaceType: `<core|temporary|replacement>`
- ReplacesOrMergesWith: `<existing surface replaced/merged, or none>`
- RetireTrigger: `<condition that retires the temporary/replacement surface>`
- MVPNextStageGate: `<what proves this slice is sufficient to advance the MVP>`
- NextSimplificationStep: `<how this change reduces complexity later>`

## Logic Spine Mapping
- SpineID: `<LS-xxx from docs/logic_spine_index.md>`
- Canonical Docs Impacted: `<paths>`

## Ownership and Role Split
- Orchestrator (governance only): `<owner>`
- Implementer(s): `<owner list>`
- Reviewer(s): `<owner list>`

## Risks and Checks
- Main Risks: `<top 3>`
- Acceptance Checks: `<tests/validation/docs checks>`
- Rollback Note: `<one-line rollback approach>`

## Review Decision
- Manifest Review Verdict: `<APPROVE|REVISE|HOLD>`
- Approved By: `<name/role>`
- Approved At UTC: `<ISO8601>`
