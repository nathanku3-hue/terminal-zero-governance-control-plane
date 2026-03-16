---
name: hierarchy-init
description: Shared project-init hierarchy confirmation. Use when a workflow must load the hierarchy template and a domain field template, render the locked table, and gate execution on explicit user approval.
---

# Hierarchy Init Skill

Use this as the shared Section 0 for hierarchy confirmation before any execution.
Other skills should call `$hierarchy-init` instead of duplicating hierarchy-init steps.

## 0. Inputs
1. `domain`: one of the available field templates (for example `financial`, `law`, `medical`, `scientific`, `software_engineering`).
2. `session_id`: current thread identifier.
3. `trigger`: `project-init`, `new-domain`, or `change-scope`.

## 1. Load Templates
1. Load `../hierarchy_template.md`.
2. Load `../field_templates/<domain>.md`.
3. If the domain template is missing, stop and request it before proceeding.

## 2. Render and Confirm (Hard Stop)
1. Print:
   - `Project Init Hierarchy Confirmation (Required)`
   - `Session: <session_id>`
   - `Trigger: <trigger>`
2. Render the hierarchy table using the locked columns:
   - `Field | Expertise Level | Rationale`
3. Ask the user to reply with one of:
   - `approve`
   - `edit: <change>`
   - `reject`
4. If not approved, update the table and re-prompt until approved.
5. Do not continue execution until approval is explicit.

## 3. Session Policy
1. Confirm once per project session.
2. Retrigger only when:
   - a new domain appears outside the confirmed hierarchy, or
   - the user says `change hierarchy` or `new scope`.

## 4. Audit Stamp (Required)
Include this stamp in all downstream outputs for the session:
- `Hierarchy Confirmation: Approved | Session: <session_id> | Trigger: <trigger> | Domains: <list>`

## 5. Non-Interactive Exception
1. If a parent/orchestrator provides a valid in-thread hierarchy confirmation stamp, do not re-prompt.
2. Echo the provided stamp in the current output.

## 6. Persisted Fallback (Only When In-Thread Stamp Is Missing)
1. Use the latest approved hierarchy snapshot from:
   - `docs/spec.md`
   - active `docs/phase*-brief.md`
2. Mark `FallbackSource` in the audit stamp.
3. Fallback validity checks:
   - both fallback files exist and are readable,
   - both contain recognizable hierarchy fields (`L1`, `L2`, `L3` or stage flow).
4. Fallback staleness checks:
   - if fallback context is stale or ambiguous for the current round, block execution and request explicit reconfirmation.
5. Require explicit user reconfirmation at the next interactive planning step.
