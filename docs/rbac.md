# RBAC v1 (Multi-tenant Groundwork)

Phase 2 ships role-based rule matching only.

## Scope (v1)

- Enforced now: rule matching by `action["role_id"]` against optional `roles` on policy rules.
- Validated only (not enforced yet): role-file `permissions` and `scope` fields.
- Deferred: tenant scoping enforcement.

## Role File Schema

Top-level object:

```json
{
  "schema_version": "1.0",
  "roles": [
    {
      "role_id": "admin",
      "permissions": ["policy.validate"],
      "scope": "global"
    }
  ]
}
```

Validation rules:

- `schema_version`: required, must equal `"1.0"`
- `roles`: required non-empty array
- each role requires:
  - `role_id`: non-empty string
  - `permissions`: required array of strings (may be empty)
  - `scope`: non-empty string
- `role_id` must be unique within the file

CLI:

- `sop policy rbac validate --role-file <path>`

## Policy Rule Extension

Rules may include optional `roles`:

```json
{
  "rule_id": "block-admin-gate-a",
  "decision": "BLOCK",
  "scope": "gate",
  "match": { "field": "actor", "operator": "eq", "value": "gate_a" },
  "roles": ["admin"]
}
```

Validation:

- if present, `roles` must be a non-empty array of non-empty strings
- if absent, rule is global
- no wildcards/regex/inheritance in v1

## Evaluator Semantics

Role context source:

- `action["role_id"]`

Matching behavior:

- if a rule has `roles`, it matches only when `action["role_id"]` exists and is included in that list
- if `action["role_id"]` is missing, treat as no role context:
  - role-scoped rules do not match
  - rules without `roles` continue to evaluate normally

## Examples

- `docs/examples/rbac/admin-role.json`
- `docs/examples/rbac/engineer-role.json`
