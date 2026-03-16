---
name: confidence-gate
description: Shared routing primitive that converts a self-reported confidence score into proceed/escalate/manual-check decisions and routes to role injection or orchestration.
---

# Confidence Gate Skill

Use this after a self-reported confidence score is provided.
This skill decides whether to proceed, escalate to an expert role, or require manual check.

## 0. Inputs
1. `confidence_score`: integer 0-100.
2. `task_summary`: one-line description of the current task.
3. `domain`: current domain for the task.
4. `invoking_skill`: skill requesting the gate decision.
5. `current_role`: optional; set when already in an expert role context.
6. `role_target`: optional; preferred expert role to invoke when escalating.

## 1. Validate
1. Require `confidence_score` in the range 0-100.
2. If missing or invalid, stop and request a corrected score.

## 2. Decision Rules
1. If `confidence_score >= 80`:
   - Emit `ConfidenceGate: PROCEED`.
   - Emit `RouteTo: orchestrator`.
2. If `confidence_score < 80` and `current_role` is empty:
   - Emit `ConfidenceGate: ESCALATE`.
   - Emit `RouteTo: $role-injection`.
   - If `role_target` is missing, select one using `docs/expert_invocation_policy.md`.
3. If `confidence_score < 80` and `current_role` is already set (expert context):
   - Emit `ConfidenceGate: MANUAL_CHECK`.
   - Emit `RouteTo: PM/CEO`.
   - Flag for manual review before proceeding.

## 3. Output Contract (Required)
Emit these lines in the decision output:
- `ConfidenceGate: <PROCEED|ESCALATE|MANUAL_CHECK>`
- `ConfidenceScore: <0-100>`
- `RouteTo: <orchestrator|$role-injection|PM/CEO>`
- `InvokingSkill: <invoking_skill>`
- `Domain: <domain>`
- `RoleTarget: <role_target|none>`
- `ConfidenceStamp: confidence_score=<int>; route_decision=<...>; invoking_skill=<...>; domain=<...>; role_target=<...>`
