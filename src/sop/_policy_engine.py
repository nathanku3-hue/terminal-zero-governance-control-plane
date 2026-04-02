from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


class PolicyLoadError(Exception):
    """Raised when a policy file cannot be loaded or fails schema validation."""


@dataclass
class PolicyResult:
    """Outcome of a single policy evaluation."""

    decision: str
    rule_id: str
    reason: str
    shadow: bool = field(default=False)


_REQUIRED_RULE_FIELDS = {"rule_id", "decision", "match", "scope"}
_VALID_DECISIONS = {"ALLOW", "BLOCK", "WARN"}
_REQUIRED_MATCH_FIELDS = {"field", "operator", "value"}
_VALID_OPERATORS = {"eq"}
_RBAC_SCHEMA_VERSION = "1.0"


def _validate_rule_roles(rule: dict[str, Any], index: int) -> None:
    roles = rule.get("roles")
    if roles is None:
        return
    if not isinstance(roles, list) or len(roles) == 0:
        raise PolicyLoadError(
            f"Rule at index {index} (rule_id={rule.get('rule_id', '<unknown>')!r}): "
            "roles must be a non-empty array of non-empty strings"
        )
    for role in roles:
        if not isinstance(role, str) or not role.strip():
            raise PolicyLoadError(
                f"Rule at index {index} (rule_id={rule.get('rule_id', '<unknown>')!r}): "
                "roles entries must be non-empty strings"
            )


def _validate_rule_permissions(rule: dict[str, Any], index: int) -> None:
    permissions = rule.get("permissions")
    if permissions is None:
        return
    if not isinstance(permissions, list) or len(permissions) == 0:
        raise PolicyLoadError(
            f"Rule at index {index} (rule_id={rule.get('rule_id', '<unknown>')!r}): "
            "permissions must be a non-empty array of non-empty strings"
        )
    for permission in permissions:
        if not isinstance(permission, str) or not permission.strip():
            raise PolicyLoadError(
                f"Rule at index {index} (rule_id={rule.get('rule_id', '<unknown>')!r}): "
                "permissions entries must be non-empty strings"
            )


def _validate_rule_tenant(rule: dict[str, Any], index: int) -> None:
    tenant_id = rule.get("tenant_id")
    if tenant_id is None:
        return
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise PolicyLoadError(
            f"Rule at index {index} (rule_id={rule.get('rule_id', '<unknown>')!r}): "
            "tenant_id must be a non-empty string"
        )


def _validate_rule(rule: Any, index: int) -> None:
    if not isinstance(rule, dict):
        raise PolicyLoadError(
            f"Rule at index {index} must be a JSON object, got {type(rule).__name__}"
        )

    missing = _REQUIRED_RULE_FIELDS - set(rule.keys())
    if missing:
        raise PolicyLoadError(
            f"Rule at index {index} (rule_id={rule.get('rule_id', '<unknown>')!r}) "
            f"is missing required fields: {sorted(missing)}"
        )

    if rule["decision"] not in _VALID_DECISIONS:
        raise PolicyLoadError(
            f"Rule {rule['rule_id']!r}: decision must be one of "
            f"{sorted(_VALID_DECISIONS)}, got {rule['decision']!r}"
        )

    match = rule["match"]
    if not isinstance(match, dict):
        raise PolicyLoadError(f"Rule {rule['rule_id']!r}: 'match' must be a JSON object")

    missing_match = _REQUIRED_MATCH_FIELDS - set(match.keys())
    if missing_match:
        raise PolicyLoadError(
            f"Rule {rule['rule_id']!r}: 'match' is missing fields: {sorted(missing_match)}"
        )

    if match["operator"] not in _VALID_OPERATORS:
        raise PolicyLoadError(
            f"Rule {rule['rule_id']!r}: match.operator must be one of "
            f"{sorted(_VALID_OPERATORS)}, got {match['operator']!r}"
        )

    if not isinstance(rule["rule_id"], str) or not rule["rule_id"].strip():
        raise PolicyLoadError(f"Rule at index {index}: rule_id must be a non-empty string")

    if not isinstance(rule["scope"], str) or not rule["scope"].strip():
        raise PolicyLoadError(f"Rule {rule['rule_id']!r}: scope must be a non-empty string")

    _validate_rule_roles(rule, index)
    _validate_rule_permissions(rule, index)
    _validate_rule_tenant(rule, index)


def _validate_single_role(role: Any, index: int) -> dict[str, Any]:
    if not isinstance(role, dict):
        raise PolicyLoadError(
            f"Role at index {index} must be a JSON object, got {type(role).__name__}"
        )

    for field_name in ("role_id", "permissions", "scope"):
        if field_name not in role:
            raise PolicyLoadError(
                f"Role at index {index} is missing required field: {field_name}"
            )

    role_id = role["role_id"]
    if not isinstance(role_id, str) or not role_id.strip():
        raise PolicyLoadError(f"Role at index {index}: role_id must be a non-empty string")

    permissions = role["permissions"]
    if not isinstance(permissions, list):
        raise PolicyLoadError(f"Role {role_id!r}: permissions must be an array of strings")
    for permission in permissions:
        if not isinstance(permission, str):
            raise PolicyLoadError(f"Role {role_id!r}: permissions entries must be strings")

    scope = role["scope"]
    if not isinstance(scope, str) or not scope.strip():
        raise PolicyLoadError(f"Role {role_id!r}: scope must be a non-empty string")

    return role


def load_policy_rules(rule_file: str | os.PathLike) -> list[dict]:
    try:
        with open(rule_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise PolicyLoadError(f"Policy rule file not found: {rule_file}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyLoadError(f"Policy rule file is not valid JSON ({rule_file}): {exc}") from exc

    if not isinstance(data, dict):
        raise PolicyLoadError(
            f"Policy rule file must be a JSON object with a 'rules' key, got {type(data).__name__}"
        )

    rules = data.get("rules")
    if rules is None:
        raise PolicyLoadError(f"Policy rule file is missing the 'rules' key: {rule_file}")
    if not isinstance(rules, list):
        raise PolicyLoadError(f"'rules' must be a JSON array, got {type(rules).__name__}")

    for idx, rule in enumerate(rules):
        _validate_rule(rule, idx)

    return rules


def load_role_config(role_file: str | os.PathLike) -> list[dict]:
    try:
        with open(role_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise PolicyLoadError(f"Role config file not found: {role_file}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyLoadError(f"Role config file is not valid JSON ({role_file}): {exc}") from exc

    if not isinstance(data, dict):
        raise PolicyLoadError(f"Role config file must be a JSON object, got {type(data).__name__}")

    schema_version = data.get("schema_version")
    if schema_version != _RBAC_SCHEMA_VERSION:
        raise PolicyLoadError(
            f"Role config schema_version must be {_RBAC_SCHEMA_VERSION!r}, got {schema_version!r}"
        )

    roles = data.get("roles")
    if not isinstance(roles, list) or len(roles) == 0:
        raise PolicyLoadError("Role config 'roles' must be a non-empty array")

    validated_roles: list[dict] = []
    seen_role_ids: set[str] = set()
    for idx, role in enumerate(roles):
        validated = _validate_single_role(role, idx)
        role_id = str(validated["role_id"])
        if role_id in seen_role_ids:
            raise PolicyLoadError(f"Duplicate role_id found: {role_id!r}")
        seen_role_ids.add(role_id)
        validated_roles.append(validated)

    return validated_roles


def _normalize_permissions(value: Any) -> set[str]:
    if isinstance(value, str) and value.strip():
        return {value.strip()}
    if not isinstance(value, list):
        return set()
    normalized: set[str] = set()
    for item in value:
        if isinstance(item, str) and item.strip():
            normalized.add(item.strip())
    return normalized


def evaluate_policy(action: dict[str, Any], rules: list[dict]) -> PolicyResult:
    action_role_id = action.get("role_id")
    has_role_context = isinstance(action_role_id, str) and bool(action_role_id.strip())

    action_scope = action.get("scope")
    has_scope_context = isinstance(action_scope, str) and bool(action_scope.strip())

    action_permissions = _normalize_permissions(action.get("permissions"))
    if not action_permissions:
        action_permissions = _normalize_permissions(action.get("permission"))

    action_tenant_id = action.get("tenant_id")
    has_tenant_context = isinstance(action_tenant_id, str) and bool(action_tenant_id.strip())

    for rule in rules:
        rule_id = str(rule["rule_id"])

        rule_scope = str(rule["scope"]).strip()
        if rule_scope != "global":
            if not has_scope_context:
                return PolicyResult(
                    decision="BLOCK",
                    rule_id=rule_id,
                    reason=f"Rule {rule_id!r} requires scope context but action.scope is missing.",
                    shadow=False,
                )
            if str(action_scope).strip() != rule_scope:
                continue

        rule_roles = rule.get("roles")
        if rule_roles is not None:
            if not has_role_context:
                return PolicyResult(
                    decision="BLOCK",
                    rule_id=rule_id,
                    reason=f"Rule {rule_id!r} requires role context but action.role_id is missing.",
                    shadow=False,
                )
            if action_role_id not in rule_roles:
                continue

        rule_permissions = rule.get("permissions")
        if rule_permissions is not None:
            if not action_permissions:
                return PolicyResult(
                    decision="BLOCK",
                    rule_id=rule_id,
                    reason=f"Rule {rule_id!r} requires permissions context but action.permissions is missing.",
                    shadow=False,
                )
            missing_permissions = [p for p in rule_permissions if p not in action_permissions]
            if missing_permissions:
                return PolicyResult(
                    decision="BLOCK",
                    rule_id=rule_id,
                    reason=(
                        f"Rule {rule_id!r} requires permissions {missing_permissions!r} "
                        "not granted to action context."
                    ),
                    shadow=False,
                )

        rule_tenant_id = rule.get("tenant_id")
        if rule_tenant_id is not None:
            if not has_tenant_context:
                return PolicyResult(
                    decision="BLOCK",
                    rule_id=rule_id,
                    reason=f"Rule {rule_id!r} requires tenant context but action.tenant_id is missing.",
                    shadow=False,
                )
            if str(action_tenant_id).strip() != str(rule_tenant_id).strip():
                return PolicyResult(
                    decision="BLOCK",
                    rule_id=rule_id,
                    reason=(
                        f"Rule {rule_id!r} tenant boundary violation: "
                        f"action tenant {action_tenant_id!r} != rule tenant {rule_tenant_id!r}."
                    ),
                    shadow=False,
                )

        match_spec = rule["match"]
        field_name: str = match_spec["field"]
        expected_value = match_spec["value"]
        actual_value = action.get(field_name)
        if actual_value != expected_value:
            continue

        base_decision: str = rule["decision"]
        is_shadow: bool = bool(rule.get("shadow", False))

        if is_shadow and base_decision == "BLOCK":
            effective_decision = "SHADOW_BLOCK"
        elif is_shadow and base_decision == "WARN":
            effective_decision = "SHADOW_WARN"
        else:
            effective_decision = base_decision

        description = rule.get("description", "")
        reason = (
            f"Rule {rule['rule_id']!r} matched: "
            f"{field_name}=={expected_value!r} -> {base_decision}"
            + (f" ({description})" if description else "")
            + (" [shadow mode: no enforcement]" if is_shadow else "")
        )
        return PolicyResult(
            decision=effective_decision,
            rule_id=rule["rule_id"],
            reason=reason,
            shadow=is_shadow,
        )

    return PolicyResult(
        decision="ALLOW",
        rule_id="default",
        reason="No matching rule found; default ALLOW applied.",
        shadow=False,
    )


def build_policy_result(
    decision: str,
    rule_id: str,
    reason: str,
    shadow: bool = False,
) -> PolicyResult:
    return PolicyResult(decision=decision, rule_id=rule_id, reason=reason, shadow=shadow)
