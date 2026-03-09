from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


KEY_VALUE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")
TDD_REQUIRED = "REQUIRED"
TDD_NOT_APPLICABLE = "NOT_APPLICABLE"


def _read_text(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, f"Missing input file: {path}"
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except Exception as exc:
        return None, f"Failed to read file {path}: {exc}"


def _parse_markdown_fields(markdown: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in markdown.splitlines():
        match = KEY_VALUE_PATTERN.match(line)
        if match is None:
            continue
        key = match.group(1).strip().upper()
        value = match.group(2).strip()
        if key:
            fields[key] = value
    return fields


def _is_placeholder(value: str) -> bool:
    return value.strip().upper() in {"N/A", "TODO"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate counterexample-first fields in round contract. "
            "Exit 0=pass, 1=validation fail, 2=infra/input error."
        )
    )
    parser.add_argument(
        "--round-contract-md",
        default="docs/context/round_contract_latest.md",
        help="Round contract markdown path.",
    )
    args = parser.parse_args()

    round_contract_path = Path(args.round_contract_md)
    markdown, read_error = _read_text(round_contract_path)
    if read_error:
        print(f"[ERROR] {read_error}")
        return 2

    fields = _parse_markdown_fields(markdown or "")
    mode = fields.get("TDD_MODE", "").strip().upper()
    cmd_present = "COUNTEREXAMPLE_TEST_COMMAND" in fields
    result_present = "COUNTEREXAMPLE_TEST_RESULT" in fields
    cmd_value = fields.get("COUNTEREXAMPLE_TEST_COMMAND", "").strip()
    result_value = fields.get("COUNTEREXAMPLE_TEST_RESULT", "").strip()

    errors: list[str] = []
    if mode not in {TDD_REQUIRED, TDD_NOT_APPLICABLE}:
        errors.append(
            f"TDD_MODE must be {TDD_REQUIRED} or {TDD_NOT_APPLICABLE} (actual={mode or 'MISSING'})."
        )

    if not cmd_present:
        errors.append("Missing COUNTEREXAMPLE_TEST_COMMAND field.")
    if not result_present:
        errors.append("Missing COUNTEREXAMPLE_TEST_RESULT field.")

    if mode == TDD_REQUIRED:
        if cmd_value == "":
            errors.append("COUNTEREXAMPLE_TEST_COMMAND must be non-empty when TDD_MODE=REQUIRED.")
        elif _is_placeholder(cmd_value):
            errors.append(
                "COUNTEREXAMPLE_TEST_COMMAND cannot be N/A or TODO when TDD_MODE=REQUIRED."
            )

        if result_value == "":
            errors.append("COUNTEREXAMPLE_TEST_RESULT must be non-empty when TDD_MODE=REQUIRED.")
        elif _is_placeholder(result_value):
            errors.append(
                "COUNTEREXAMPLE_TEST_RESULT cannot be N/A or TODO when TDD_MODE=REQUIRED."
            )

    if mode == TDD_NOT_APPLICABLE:
        if cmd_value == "":
            errors.append(
                "COUNTEREXAMPLE_TEST_COMMAND must be present (N/A allowed) when TDD_MODE=NOT_APPLICABLE."
            )
        if result_value == "":
            errors.append(
                "COUNTEREXAMPLE_TEST_RESULT must be present (N/A allowed) when TDD_MODE=NOT_APPLICABLE."
            )

    if errors:
        for err in errors:
            print(f"[ERROR] {err}")
        return 1

    print("[OK] Counterexample gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

