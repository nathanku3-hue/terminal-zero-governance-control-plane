---
name: role-injection
description: Shared primitive to instantiate expert role personas with authority boundaries, attach domain expertise context, assign a model, and emit a role stamp for audit.
---

# Role Injection Skill

Use this when a confidence gate or expert invocation requires a role-specific persona.

## 0. Inputs
1. `role_name`: one of `socratic_investigator`, `principal`, `system_eng`, `riskops`, `qa`, `devsecops`, `architect`.
2. `domain`: current domain (must map to `../field_templates/<domain>.md`).
3. `confidence_threshold`: integer 0-100 (default 80).
4. `task_summary`: one-line description of what the expert is asked to address.
5. `invoking_skill`: skill requesting the role injection.

## 1. Load Domain Expertise
1. Load `../field_templates/<domain>.md`.
2. Extract the `Field | Expertise Level | Rationale` rows for the injected persona.
3. If the template is missing, stop and request it before proceeding.

## 2. Load Role Policy
1. Read `docs/expert_invocation_policy.md`.
2. Use the role's `Scope` and `NOT in Scope` text as the authority boundary.
3. Authority boundary rules:
   - `socratic_investigator` and `qa` are advisory-only and cannot veto execution.
   - Other roles are advisory unless explicitly granted decision authority by PM/CEO.

## 3. Model Assignment
1. Attempt to resolve a role-specific model by reading `agents/openai.yaml` from the mapped skill folder below.
2. If `model` is missing or the skill does not exist, set `Model=UNASSIGNED` and require manual selection.

Role to skill mapping for model lookup:
- `socratic_investigator` -> `../../project-guider/agents/openai.yaml`
- `principal` -> `../../architect-review/agents/openai.yaml`
- `system_eng` -> `../../se-executor/agents/openai.yaml`
- `riskops` -> `../../saw/agents/openai.yaml`
- `qa` -> `../../se-executor/agents/openai.yaml`
- `devsecops` -> `../../architect-review/agents/openai.yaml`
- `architect` -> `../../architect-review/agents/openai.yaml`

## 4. Persona Injection (Required)
Emit the persona block using this structure:
- `Role: <role_name>`
- `Domain: <domain>`
- `Expertise Context: <summary of template rows>`
- `Authority Boundary: <scope + not-in-scope + advisory status>`
- `Assigned Model: <model or UNASSIGNED>`

## 5. Role Stamp (Required)
Emit a single-line audit stamp:
- `RoleStamp: role=<role_name>; domain=<domain>; confidence_threshold=<int>; model=<model>; invoking_skill=<invoking_skill>`
