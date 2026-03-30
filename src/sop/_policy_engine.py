"""Policy engine for Terminal Zero governance control plane.

Pure evaluation module — no I/O, no audit log calls.
The caller (run_loop_cycle.py) is responsible for emitting audit log entries.

Public API:
    load_policy_rules(rule_file) -> list[dict]
    evaluate_policy(action, rules) -> PolicyResult
    build_policy_result(decision, rule_id, reason, shadow) -> PolicyResult

Rule schema (each element in the JSON rules array)::

    {
        "rule_id": "str",          # required, unique identifier
        "decision": "ALLOW|BLOCK|WARN",  # required
        "match": {                  # required
            "field": "str",         # key in the action dict
            "operator": "eq",       # only "eq" supported in Phase 2
            "value": "str|int|bool" # value to compare against
        },
        "scope": "str",             # required, e.g. "gate"
        "shadow": false,            # optional, default false
        "description": "str"        # optional, human-readable
    }

Action dict (passed by run_loop_cycle.py at Gate A / Gate B)::

    {
        "gate": "exec_memory->advisory" | "advisory->summary",
        "decision": "PROCEED" | "HOLD",
        "trace_id": "<str>",
        "actor": "gate_a" | "gate_b",
    }
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PolicyLoadError(Exception):
    """Raised when a policy rule file cannot be loaded or fails schema validation."""


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PolicyResult:
    """Outcome of a single policy evaluation.

    Attributes:
        decision: Final decision — "ALLOW", "BLOCK", "WARN",
                  "SHADOW_BLOCK", or "SHADOW_WARN".
        rule_id:  The rule_id of the rule that triggered, or "default" if
                  no rule matched (default ALLOW).
        reason:   Human-readable explanation.
        shadow:   True when the result is a shadow simulation (no blocking).
    """

    decision: str
    rule_id: str
    reason: str
    shadow: bool = field(default=False)


# ---------------------------------------------------------------------------
# Schema validation helpers
# ---------------------------------------------------------------------------

_REQUIRED_RULE_FIELDS = {"rule_id", "decision", "match", "scope"}
_VALID_DECISIONS = {"ALLOW", "BLOCK", "WARN"}
_REQUIRED_MATCH_FIELDS = {"field", "operator", "value"}
_VALID_OPERATORS = {"eq"}


def _validate_rule(rule: Any, index: int) -> None:
    """Raise PolicyLoadError if *rule* does not conform to the schema."""
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
        raise PolicyLoadError(
            f"Rule {rule['rule_id']!r}: 'match' must be a JSON object"
        )

    missing_match = _REQUIRED_MATCH_FIELDS - set(match.keys())
    if missing_match:
        raise PolicyLoadError(
            f"Rule {rule['rule_id']!r}: 'match' is missing fields: "
            f"{sorted(missing_match)}"
        )

    if match["operator"] not in _VALID_OPERATORS:
        raise PolicyLoadError(
            f"Rule {rule['rule_id']!r}: match.operator must be one of "
            f"{sorted(_VALID_OPERATORS)}, got {match['operator']!r}"
        )

    if not isinstance(rule["rule_id"], str) or not rule["rule_id"].strip():
        raise PolicyLoadError(
            f"Rule at index {index}: rule_id must be a non-empty string"
        )

    if not isinstance(rule["scope"], str) or not rule["scope"].strip():
        raise PolicyLoadError(
            f"Rule {rule['rule_id']!r}: scope must be a non-empty string"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_policy_rules(rule_file: str | os.PathLike) -> list[dict]:
    """Load and validate a JSON policy rule file.

    Args:
        rule_file: Path to a JSON file containing a ``rules`` array.

    Returns:
        A validated list of rule dicts.

    Raises:
        PolicyLoadError: If the file cannot be read, is not valid JSON,
                         or fails schema validation.
    """
    try:
        with open(rule_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError as exc:
        raise PolicyLoadError(f"Policy rule file not found: {rule_file}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyLoadError(
            f"Policy rule file is not valid JSON ({rule_file}): {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise PolicyLoadError(
            f"Policy rule file must be a JSON object with a 'rules' key, "
            f"got {type(data).__name__}"
        )

    rules = data.get("rules")
    if rules is None:
        raise PolicyLoadError(
            f"Policy rule file is missing the 'rules' key: {rule_file}"
        )
    if not isinstance(rules, list):
        raise PolicyLoadError(
            f"'rules' must be a JSON array, got {type(rules).__name__}"
        )

    for idx, rule in enumerate(rules):
        _validate_rule(rule, idx)

    return rules


def evaluate_policy(
    action: dict[str, Any],
    rules: list[dict],
) -> PolicyResult:
    """Evaluate *action* against *rules* and return a PolicyResult.

    Evaluation semantics:
    - Rules are evaluated in order; the **first matching rule wins**.
    - A rule matches when ``action[match.field] == match.value``
      (only ``eq`` operator is supported in Phase 2).
    - If the matching rule has ``shadow=true``, the decision is prefixed
      with ``SHADOW_`` (e.g. ``SHADOW_BLOCK``) and does not block.
    - If no rule matches, the default decision is **ALLOW**.

    Args:
        action: A dict describing the current gate action (see module docstring).
        rules:  Validated rule list as returned by :func:`load_policy_rules`.

    Returns:
        A :class:`PolicyResult` describing the outcome.
    """
    for rule in rules:
        match_spec = rule["match"]
        field_name: str = match_spec["field"]
        expected_value = match_spec["value"]
        # operator is always "eq" in Phase 2
        actual_value = action.get(field_name)
        if actual_value != expected_value:
            continue

        # Rule matched
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

    # No rule matched — default ALLOW
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
    """Construct a PolicyResult directly (helper for tests and callers).

    Args:
        decision: Decision string (e.g. "ALLOW", "BLOCK", "SHADOW_BLOCK").
        rule_id:  Rule identifier.
        reason:   Human-readable explanation.
        shadow:   Whether this is a shadow (non-enforced) result.

    Returns:
        A :class:`PolicyResult` instance.
    """
    return PolicyResult(decision=decision, rule_id=rule_id, reason=reason, shadow=shadow)
