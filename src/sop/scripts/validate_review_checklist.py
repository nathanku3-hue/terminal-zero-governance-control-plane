from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADING_PATTERN = re.compile(r"^\s*##\s+(.+?)\s*$")
KEY_VALUE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")

REQUIRED_SECTIONS = {
    "problemintent": "Problem/Intent",
    "scopeboundaries": "Scope Boundaries",
    "evidencetests": "Evidence/Tests",
    "risksrollback": "Risks/Rollback",
    "reviewerdecision": "Reviewer Decision",
}

REQUIRED_FIELDS = (
    "PROBLEM_INTENT",
    "SCOPE_BOUNDARIES",
    "EVIDENCE_TESTS",
    "RISKS_ROLLBACK",
    "REVIEWER_DECISION",
)

ALLOWED_DECISIONS = {"APPROVE", "REQUEST_CHANGES", "BLOCK"}


def _canonical_heading(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _looks_placeholder(value: str) -> bool:
    stripped = value.strip()
    upper = stripped.upper()
    if not stripped:
        return True
    if upper in {"TODO", "TBD", "N/A", "NA"}:
        return True
    return upper.startswith("TODO(") or upper.startswith("TODO")


def _parse_markdown(path: Path) -> tuple[set[str], dict[str, str]]:
    raw = path.read_text(encoding="utf-8-sig")
    headings: set[str] = set()
    fields: dict[str, str] = {}

    for line in raw.splitlines():
        heading_match = HEADING_PATTERN.match(line)
        if heading_match is not None:
            headings.add(_canonical_heading(heading_match.group(1)))

        kv_match = KEY_VALUE_PATTERN.match(line)
        if kv_match is not None:
            key = kv_match.group(1).strip().upper()
            value = kv_match.group(2).strip()
            if key:
                fields[key] = value

    return headings, fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate PR review checklist markdown. "
            "Exit 0=pass, 1=validation fail, 2=input/infra error."
        )
    )
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)

    input_path = args.input
    if not input_path.exists():
        print(f"[ERROR] Missing input file: {input_path}")
        return 2

    try:
        headings, fields = _parse_markdown(input_path)
    except Exception as exc:
        print(f"[ERROR] Failed to read or parse checklist: {exc}")
        return 2

    failures: list[str] = []

    for canonical, label in REQUIRED_SECTIONS.items():
        if canonical not in headings:
            failures.append(f"Missing required section: {label}")

    for field in REQUIRED_FIELDS:
        value = fields.get(field, "")
        if _looks_placeholder(value):
            failures.append(f"Missing or placeholder field: {field}")

    reviewer_decision = fields.get("REVIEWER_DECISION", "").strip().upper()
    if reviewer_decision and reviewer_decision not in ALLOWED_DECISIONS:
        failures.append(
            "Invalid REVIEWER_DECISION: "
            f"{reviewer_decision} (allowed: {', '.join(sorted(ALLOWED_DECISIONS))})"
        )

    if failures:
        for item in failures:
            print(f"[FAIL] {item}")
        return 1

    print("[OK] PR review checklist validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
