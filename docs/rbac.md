# RBAC v2 (Permission + Scope + Tenant Enforcement)

Phase 2 now enforces role, permission, scope, and tenant boundaries during policy evaluation.

## Enforcement Contracts

### Permission contract

- Canonical action fields: `permissions` (preferred list) or `permission` (single string fallback).
- Rule field: optional `permissions` (non-empty list of strings).
- Enforcement: when a rule declares `permissions`, action context must include all required permissions.
- Missing or insufficient permissions: immediate `BLOCK` with explicit reason.

### Scope contract

- Canonical action field: `scope`.
- Rule field: required `scope`.
- Matching behavior:
  - Rule `scope="global"`: no scope equality check.
  - Other scopes: action must include `scope` and match exactly.
- Missing scope for scoped rules: `BLOCK`.

### Tenant contract

- Canonical action field: `tenant_id`.
- Rule field: optional `tenant_id`.
- Enforcement:
  - If rule has `tenant_id`, action must include `tenant_id` and match exactly.
  - Cross-tenant mismatch: `BLOCK`.

### Missing-context behavior

- Missing required context (`role_id`, `scope`, `permissions`, `tenant_id` where required): `BLOCK`.

### Backward compatibility policy

- Existing role files remain `schema_version: "1.0"` (no schema bump).
- Existing policy rules without `permissions` and `tenant_id` continue to work.
- Non-global rules now require action `scope` context.

## Rule File Schema

Top-level object:

```json
{
  "schema_version": "1.0",
  "rules": [
    {
      "rule_id": "gate-a-admin",
      "decision": "BLOCK",
      "scope": "gate",
      "roles": ["admin"],
      "permissions": ["policy.evaluate.gate_a"],
      "tenant_id": "tenant-alpha",
      "match": { "field": "actor", "operator": "eq", "value": "gate_a" }
    }
  ]
}
```

## Role File Schema

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

Validation rules unchanged for role files:

- `schema_version` required and must be `"1.0"`
- `roles` required non-empty array
- role fields required: `role_id`, `permissions`, `scope`
- unique `role_id`

## Evaluator Semantics Summary

Evaluation order per rule:

1. Scope gate
2. Role gate
3. Permission gate
4. Tenant gate
5. Match expression (`eq`)
6. Decision/shadow transformation

Default behavior: if no rule matches after gating, return `ALLOW`.

## Examples

- `docs/examples/rbac/admin-role.json`
- `docs/examples/rbac/engineer-role.json`
