#!/usr/bin/env python3
"""tests/test_checklist_matrix.py

Phase 3 Stream C -- Checklist Matrix Tests (stub mode).

All 7 tests operate on static skills_status input via check_loop_readiness.py
--skills-status flag. No live loop execution is required.

Test coverage:
  1. test_resolver_unavailable_routes_broken_install
  2. test_empty_by_design_routes_correctly
  3. test_resolver_unavailable_never_maps_to_empty_by_design
  4. test_active_skills_routes_skills_active
  5. test_loop_readiness_artifact_schema_valid
  6. test_loop_readiness_readable_without_running_loop
  7. test_absent_skills_status_routes_unknown
"""
from __future__ import annotations

import importlib.resources
import json
import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

# Import the check_loop_readiness module from the canonical sop package path.
# Per D-183 / Implementation Review Rule: new logic lives in sop/ first.
sys.path.insert(0, str(REPO_ROOT / "src"))
import importlib
_clr = importlib.import_module("sop.scripts.check_loop_readiness")
_route = _clr._route
_build_artifact = _clr._build_artifact


def _load_schema() -> dict[str, Any]:
    """Load loop_readiness.schema.json from src/sop/schemas/."""
    schema_path = REPO_ROOT / "src" / "sop" / "schemas" / "loop_readiness.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validate_against_schema(artifact: dict, schema: dict) -> list[str]:
    """Minimal JSON Schema draft-07 validator for required fields and enum values.

    Returns a list of violation strings; empty list means valid.
    Uses jsonschema if available; falls back to manual required-field check.
    """
    try:
        import jsonschema  # type: ignore[import]
        validator = jsonschema.Draft7Validator(schema)
        errors = sorted(validator.iter_errors(artifact), key=lambda e: list(e.path))
        return [e.message for e in errors]
    except ImportError:
        pass

    # Manual fallback: check required fields and enum values
    violations: list[str] = []
    required = schema.get("required", [])
    for field in required:
        if field not in artifact:
            violations.append(f"Missing required field: '{field}'")

    # Check routing enum
    routing_enum = schema.get("properties", {}).get("routing", {}).get("enum", [])
    if routing_enum and artifact.get("routing") not in routing_enum:
        violations.append(
            f"routing '{artifact.get('routing')}' not in allowed values {routing_enum}"
        )

    # Check schema_version const
    schema_const = schema.get("properties", {}).get("schema_version", {}).get("const")
    if schema_const and artifact.get("schema_version") != schema_const:
        violations.append(
            f"schema_version '{artifact.get('schema_version')}' != expected '{schema_const}'"
        )

    # Check readiness_checks items
    result_enum = (
        schema.get("properties", {})
        .get("readiness_checks", {})
        .get("items", {})
        .get("properties", {})
        .get("result", {})
        .get("enum", [])
    )
    for check in artifact.get("readiness_checks", []):
        if result_enum and check.get("result") not in result_enum:
            violations.append(
                f"readiness_check result '{check.get('result')}' not in {result_enum}"
            )
        if "check" not in check:
            violations.append("readiness_check item missing 'check' field")

    return violations


# ---------------------------------------------------------------------------
# Test 1
# ---------------------------------------------------------------------------

def test_resolver_unavailable_routes_broken_install():
    """RESOLVER_UNAVAILABLE -> routing=broken_install, loop_ready=false."""
    payload = _route("RESOLVER_UNAVAILABLE")
    assert payload["routing"] == "broken_install", (
        f"Expected routing=broken_install, got {payload['routing']!r}"
    )
    assert payload["loop_ready"] is False, (
        f"Expected loop_ready=False, got {payload['loop_ready']!r}"
    )
    assert payload["operator_action"] is not None, "operator_action must be set for broken_install"
    # Verify the resolver check is FAIL
    resolver_check = next(
        (c for c in payload["readiness_checks"] if c["check"] == "skill_resolver_available"),
        None,
    )
    assert resolver_check is not None, "readiness_checks must include skill_resolver_available"
    assert resolver_check["result"] == "FAIL", (
        f"skill_resolver_available should be FAIL for broken_install, got {resolver_check['result']!r}"
    )


# ---------------------------------------------------------------------------
# Test 2
# ---------------------------------------------------------------------------

def test_empty_by_design_routes_correctly():
    """EMPTY_BY_DESIGN -> routing=empty_by_design, loop_ready=true."""
    payload = _route("EMPTY_BY_DESIGN")
    assert payload["routing"] == "empty_by_design", (
        f"Expected routing=empty_by_design, got {payload['routing']!r}"
    )
    assert payload["loop_ready"] is True, (
        f"Expected loop_ready=True, got {payload['loop_ready']!r}"
    )
    assert payload["operator_action"] is None, (
        f"operator_action should be None for empty_by_design, got {payload['operator_action']!r}"
    )
    # skill_resolver_available must be PASS
    resolver_check = next(
        (c for c in payload["readiness_checks"] if c["check"] == "skill_resolver_available"),
        None,
    )
    assert resolver_check is not None, "readiness_checks must include skill_resolver_available"
    assert resolver_check["result"] == "PASS", (
        f"skill_resolver_available should be PASS for empty_by_design, got {resolver_check['result']!r}"
    )
    # skills_configured must be SKIP
    configured_check = next(
        (c for c in payload["readiness_checks"] if c["check"] == "skills_configured"),
        None,
    )
    assert configured_check is not None, "readiness_checks must include skills_configured"
    assert configured_check["result"] == "SKIP", (
        f"skills_configured should be SKIP for empty_by_design, got {configured_check['result']!r}"
    )


# ---------------------------------------------------------------------------
# Test 3 -- Hard invariant
# ---------------------------------------------------------------------------

def test_resolver_unavailable_never_maps_to_empty_by_design():
    """RESOLVER_UNAVAILABLE must NEVER produce routing=empty_by_design.

    This is the hard invariant specified in the plan.
    Verifies the invariant cannot be violated for any plausible input.
    """
    # Direct check
    payload = _route("RESOLVER_UNAVAILABLE")
    assert payload["routing"] != "empty_by_design", (
        "INVARIANT VIOLATED: RESOLVER_UNAVAILABLE routed to empty_by_design"
    )

    # Exhaustive check of all known routing inputs -- none of the non-RESOLVER_UNAVAILABLE
    # inputs should be confused with RESOLVER_UNAVAILABLE semantics
    all_inputs = ["RESOLVER_UNAVAILABLE", "EMPTY_BY_DESIGN", "ACTIVE", None, "", "UNKNOWN_FUTURE"]
    for inp in all_inputs:
        p = _route(inp)
        if inp == "RESOLVER_UNAVAILABLE":
            assert p["routing"] != "empty_by_design", (
                f"INVARIANT VIOLATED for input {inp!r}: routing={p['routing']!r}"
            )
        # Also assert RESOLVER_UNAVAILABLE never yields loop_ready=True
        if inp == "RESOLVER_UNAVAILABLE":
            assert p["loop_ready"] is False, (
                f"INVARIANT VIOLATED: RESOLVER_UNAVAILABLE produced loop_ready=True"
            )


# ---------------------------------------------------------------------------
# Test 4
# ---------------------------------------------------------------------------

def test_active_skills_routes_skills_active(monkeypatch):
    """ACTIVE -> routing=skills_active, loop_ready=true (mocked activation check)."""
    # Monkeypatch _check_skill_activation to return PASS without running subprocess
    monkeypatch.setattr(_clr, "_check_skill_activation", lambda: ("PASS", "mocked"))

    payload = _route("ACTIVE")
    assert payload["routing"] == "skills_active", (
        f"Expected routing=skills_active, got {payload['routing']!r}"
    )
    assert payload["loop_ready"] is True, (
        f"Expected loop_ready=True, got {payload['loop_ready']!r}"
    )
    # All three checks must be present
    check_names = {c["check"] for c in payload["readiness_checks"]}
    assert "skill_resolver_available" in check_names
    assert "skills_configured" in check_names
    assert "skill_activation_valid" in check_names
    activation_check = next(
        c for c in payload["readiness_checks"] if c["check"] == "skill_activation_valid"
    )
    assert activation_check["result"] == "PASS"


# ---------------------------------------------------------------------------
# Test 5
# ---------------------------------------------------------------------------

def test_loop_readiness_artifact_schema_valid(monkeypatch, tmp_path):
    """Emitted artifact validates against loop_readiness.schema.json; all required fields present."""
    monkeypatch.setattr(_clr, "_check_skill_activation", lambda: ("PASS", "mocked"))

    schema = _load_schema()
    required_fields = schema.get("required", [])

    for skills_status in ["RESOLVER_UNAVAILABLE", "EMPTY_BY_DESIGN", "ACTIVE", None]:
        artifact = _build_artifact(skills_status)

        # All required fields must be present
        for field in required_fields:
            assert field in artifact, (
                f"Required field '{field}' missing from artifact for skills_status={skills_status!r}"
            )

        # Validate against schema
        violations = _validate_against_schema(artifact, schema)
        assert not violations, (
            f"Schema violations for skills_status={skills_status!r}: {violations}"
        )


# ---------------------------------------------------------------------------
# Test 6
# ---------------------------------------------------------------------------

def test_loop_readiness_readable_without_running_loop(monkeypatch, tmp_path):
    """Valid artifact produced from static input -- no live loop execution required."""
    monkeypatch.setattr(_clr, "_check_skill_activation", lambda: ("PASS", "mocked"))

    output_path = tmp_path / "loop_readiness_latest.json"

    # Run main() with static --skills-status arg; no live loop, no summary file needed
    ret = _clr.main([
        "--skills-status", "EMPTY_BY_DESIGN",
        "--output", str(output_path),
    ])
    assert ret == 0, f"main() returned non-zero: {ret}"
    assert output_path.exists(), "loop_readiness_latest.json was not written"

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "1.0"
    assert artifact["routing"] == "empty_by_design"
    assert artifact["loop_ready"] is True
    assert "generated_at_utc" in artifact
    assert "readiness_checks" in artifact
    assert isinstance(artifact["readiness_checks"], list)


# ---------------------------------------------------------------------------
# Test 7
# ---------------------------------------------------------------------------

def test_absent_skills_status_routes_unknown():
    """Absent skills_status field -> routing=unknown, loop_ready=true (fail-open fallback)."""
    # None represents an absent key
    payload = _route(None)
    assert payload["routing"] == "unknown", (
        f"Expected routing=unknown for absent skills_status, got {payload['routing']!r}"
    )
    assert payload["loop_ready"] is True, (
        f"Expected loop_ready=True (fail-open) for absent skills_status, got {payload['loop_ready']!r}"
    )
    assert payload["operator_action"] is not None, (
        "operator_action should suggest upgrade for unknown routing"
    )
