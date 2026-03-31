# Plugin API v1 (Phase 5 Final Final Locked)

## Interface contract

Each plugin file exports `plugin` and plugin implements:

- `evaluate(action: dict, context: dict) -> dict | None`
- `min_sop_version` as `MAJOR.MINOR.PATCH`
- recommended: `name`, `version`

Runtime context keys (exact, flat):

- `repo_root: str`
- `trace_id: str`
- `gate: str`
- `policy_shadow_mode: bool`

Result contract:

- `None`, or
- `{ "decision": "ALLOW|BLOCK|WARN", "reason": "non-empty", "metadata"?: <json-serializable> }`

## Discovery

- Non-recursive from plugin directory
- Load `*.py` only
- Ignore `_*.py`
- One plugin per file
- Module must export `plugin`

Default plugin directory on `sop run`:

- `<repo_root>/.sop/plugins/`

Override:

- `sop run --plugin-dir <path>`

## Compatibility

Plugin executes only when:

- `sop.__version__ >= plugin.min_sop_version` using numeric semver compare

Invalid semver format is treated as incompatible:

- plugin skipped
- audit warning emitted (`plugin_status=skipped_incompatible`)

## Execution order and chain semantics

Compatible plugins execute in deterministic lexical filename order.

For a gate:

- `BLOCK` -> short-circuit remaining plugins for that gate
- `ALLOW` -> continue
- `WARN` -> continue
- first `BLOCK` wins

## Enforcement semantics

- Plugin `BLOCK` is enforced like built-in policy block at that gate
- Plugin `WARN` is non-blocking
- Plugin `ALLOW` is advisory/audit-visible and does not override prior terminal built-in outcomes

## Shadow mode semantics

- `policy_shadow_mode` is only passed in plugin context
- runtime does not rewrite plugin decisions in v1
- plugins may self-adjust behavior using `context["policy_shadow_mode"]`

## Audit log contract

Each plugin event appends audit entry with:

- `actor: plugin:<plugin_name>`
- `gate: <current gate>`
- `plugin_name`
- `plugin_version`
- `plugin_status ∈ {executed, skipped_incompatible, error}`

Decision mapping:

- plugin `ALLOW` -> audit `decision=ALLOW`
- plugin `BLOCK` -> audit `decision=BLOCK`
- plugin `WARN` -> audit `decision=WARN`
- exception -> audit `decision=WARN`, `plugin_status=error`, run continues

## Example plugin

See `.sop/plugins/example_warn.py`.

- Returns `WARN` on `advisory->summary`
- Returns `None` otherwise
