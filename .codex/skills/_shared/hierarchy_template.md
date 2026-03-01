# Hierarchy Confirmation Template (Locked Structure)

Use this template at project initialization as a hard stop before execution.

## Session Rules
- Session definition: the current chat/thread.
- Confirm hierarchy once per project session.
- Retrigger confirmation only when:
  - a new domain appears that is not in the confirmed hierarchy, or
  - user explicitly says `change hierarchy` or `new scope`.
- Do not continue implementation until user replies with `approve` or equivalent explicit confirmation.
- Audit requirement: each plan/SAW/research output must include:
  - `Hierarchy Confirmation: Approved`
  - `Session: <current-thread>`
  - `Trigger: project-init | new-domain | change-scope`
  - `Domains: <list>`

## Locked Structure
Do not remove or rename these columns.

| Field | Expertise Level | Rationale |
|---|---|---|
| `<field>` | `<level>` | `<one-line why this level is needed>` |

Allowed edits:
- Add/remove rows.
- Change values inside rows.

Not allowed:
- Changing the 3-column structure.

## Confirmation Prompt Template
Use this exact interaction pattern:

1. Print:
   - `Project Init Hierarchy Confirmation (Required)`
   - `Session: <id or current-thread>`
   - `Trigger: project-init | new-domain | change-scope`
2. Render hierarchy table using the locked structure.
3. Ask user to reply with one of:
   - `approve`
   - `edit: <change>`
   - `reject`
4. If not approved, iterate and ask again.
5. After approval, emit the audit stamp in all downstream outputs for this session.
