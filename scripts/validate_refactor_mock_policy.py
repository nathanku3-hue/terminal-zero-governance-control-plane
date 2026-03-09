from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


KEY_VALUE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")
MOCK_POLICY_STRICT = "STRICT"
MOCK_POLICY_NOT_APPLICABLE = "NOT_APPLICABLE"
INTEGRATION_COVERAGE_ALLOWED = {"YES", "NO", "N/A"}
PLACEHOLDER_VALUES = {"", "N/A", "NONE", "[]"}


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


def _parse_non_negative_number(label: str, raw: str) -> tuple[float | None, str | None]:
    try:
        number = float(raw)
    except Exception:
        return None, f"{label} must be numeric (actual={raw or 'MISSING'})."
    if number < 0:
        return None, f"{label} must be >= 0 (actual={number})."
    return number, None


def _is_non_empty_list_like(raw: str) -> bool:
    return raw.strip().upper() not in PLACEHOLDER_VALUES


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate refactor-budget and mock-policy fields in round contract. "
            "Exit 0=pass, 1=validation fail, 2=input/infra error."
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
    errors: list[str] = []
    notes: list[str] = []

    required_fields = (
        "REFACTOR_BUDGET_MINUTES",
        "REFACTOR_SPEND_MINUTES",
        "MOCK_POLICY_MODE",
        "MOCKED_DEPENDENCIES",
        "INTEGRATION_COVERAGE_FOR_MOCKS",
    )
    for field in required_fields:
        if field not in fields:
            errors.append(f"Missing {field} field.")

    if errors:
        for err in errors:
            print(f"[ERROR] {err}")
        return 1

    budget_raw = fields.get("REFACTOR_BUDGET_MINUTES", "").strip()
    spend_raw = fields.get("REFACTOR_SPEND_MINUTES", "").strip()
    budget, budget_error = _parse_non_negative_number("REFACTOR_BUDGET_MINUTES", budget_raw)
    spend, spend_error = _parse_non_negative_number("REFACTOR_SPEND_MINUTES", spend_raw)
    if budget_error:
        errors.append(budget_error)
    if spend_error:
        errors.append(spend_error)

    if budget is not None and spend is not None and spend > budget:
        reason = fields.get("REFACTOR_BUDGET_EXCEEDED_REASON", "").strip()
        if reason == "" or reason.upper() in {"N/A", "NONE"}:
            errors.append(
                "REFACTOR_SPEND_MINUTES exceeds REFACTOR_BUDGET_MINUTES and "
                "REFACTOR_BUDGET_EXCEEDED_REASON is missing."
            )
        else:
            notes.append(
                "Refactor spend exceeds budget with explicit reason "
                "(REFACTOR_BUDGET_EXCEEDED_REASON)."
            )

    mode = fields.get("MOCK_POLICY_MODE", "").strip().upper()
    if mode not in {MOCK_POLICY_STRICT, MOCK_POLICY_NOT_APPLICABLE}:
        errors.append(
            "MOCK_POLICY_MODE must be STRICT or NOT_APPLICABLE "
            f"(actual={mode or 'MISSING'})."
        )

    coverage = fields.get("INTEGRATION_COVERAGE_FOR_MOCKS", "").strip().upper()
    if coverage not in INTEGRATION_COVERAGE_ALLOWED:
        errors.append(
            "INTEGRATION_COVERAGE_FOR_MOCKS must be YES, NO, or N/A "
            f"(actual={coverage or 'MISSING'})."
        )

    mocked_dependencies = fields.get("MOCKED_DEPENDENCIES", "").strip()

    if mode == MOCK_POLICY_STRICT:
        if not _is_non_empty_list_like(mocked_dependencies):
            errors.append(
                "MOCKED_DEPENDENCIES must be non-empty when MOCK_POLICY_MODE=STRICT."
            )
        if coverage != "YES":
            errors.append(
                "INTEGRATION_COVERAGE_FOR_MOCKS must be YES when MOCK_POLICY_MODE=STRICT."
            )

    if mode == MOCK_POLICY_NOT_APPLICABLE and coverage != "N/A":
        errors.append(
            "INTEGRATION_COVERAGE_FOR_MOCKS must be N/A when MOCK_POLICY_MODE=NOT_APPLICABLE."
        )

    if errors:
        for err in errors:
            print(f"[ERROR] {err}")
        return 1

    for note in notes:
        print(f"[NOTE] {note}")
    print("[OK] Refactor/mock policy gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

