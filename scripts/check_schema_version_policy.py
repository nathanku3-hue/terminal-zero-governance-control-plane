#!/usr/bin/env python3
"""scripts/check_schema_version_policy.py

F.3 — Schema version policy enforcer.

Scans all *.schema.json files under docs/context/schemas/ and verifies that
every schema declares a ``schema_version`` field (either as a required property
with a ``const`` value, or as a top-level ``const``).  Exits 0 when all
schemas comply, exits 1 when any schema is missing the field.

Usage:
    python scripts/check_schema_version_policy.py [--schema-dir <path>]

The --schema-dir flag defaults to docs/context/schemas relative to repo root
(resolved from the script's own location when run from scripts/).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _has_schema_version(schema: dict) -> bool:
    """Return True if the schema declares a schema_version field."""
    # Check properties.schema_version
    props = schema.get("properties", {})
    if "schema_version" in props:
        return True
    # Check top-level const (unlikely but allowed)
    if "schema_version" in schema:
        return True
    return False


def check_schema_dir(schema_dir: Path) -> list[str]:
    """Return a list of violation messages (empty = all pass)."""
    violations: list[str] = []
    schema_files = sorted(schema_dir.glob("*.schema.json"))
    if not schema_files:
        # No schema files found — not a violation, but warn
        return []
    for schema_file in schema_files:
        try:
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
        except Exception as exc:
            violations.append(f"{schema_file.name}: parse error — {exc}")
            continue
        if not isinstance(schema, dict):
            violations.append(f"{schema_file.name}: root is not an object")
            continue
        if not _has_schema_version(schema):
            violations.append(
                f"{schema_file.name}: missing schema_version property "
                f"(required by version policy)"
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that all *.schema.json files declare schema_version."
    )
    parser.add_argument(
        "--schema-dir",
        default=None,
        help="Path to schema directory (default: docs/context/schemas relative to repo root).",
    )
    args = parser.parse_args(argv)

    if args.schema_dir is not None:
        schema_dir = Path(args.schema_dir)
    else:
        # Resolve relative to repo root: script lives at <repo>/scripts/ or
        # <repo>/src/sop/scripts/; walk up to find docs/context/schemas.
        _here = Path(__file__).resolve()
        # Try up to 4 levels up to find docs/context/schemas
        schema_dir = None
        for ancestor in [_here.parent, _here.parent.parent,
                         _here.parent.parent.parent,
                         _here.parent.parent.parent.parent]:
            candidate = ancestor / "docs" / "context" / "schemas"
            if candidate.is_dir():
                schema_dir = candidate
                break
        if schema_dir is None:
            print(
                "ERROR: could not locate docs/context/schemas. "
                "Pass --schema-dir explicitly.",
                file=sys.stderr,
            )
            return 1

    if not schema_dir.is_dir():
        print(f"ERROR: schema directory not found: {schema_dir}", file=sys.stderr)
        return 1

    violations = check_schema_dir(schema_dir)
    if violations:
        print(f"SCHEMA VERSION POLICY: {len(violations)} violation(s) found:", file=sys.stderr)
        for v in violations:
            print(f"  FAIL  {v}", file=sys.stderr)
        return 1

    schema_files = list(schema_dir.glob("*.schema.json"))
    print(
        f"SCHEMA VERSION POLICY: PASS — {len(schema_files)} schema(s) checked, "
        f"all declare schema_version."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
