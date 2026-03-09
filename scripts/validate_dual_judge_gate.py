from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KEY_VALUE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")
DUAL_REQUIRED = "YES"
DECISION_ONE_WAY = "ONE_WAY"
DECISION_TWO_WAY = "TWO_WAY"
RISK_HIGH = "HIGH"
LOW_MEDIUM_RISKS = {"LOW", "MEDIUM"}


def _parse_contract_fields(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8-sig")
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        match = KEY_VALUE_PATTERN.match(line)
        if match is None:
            continue
        key = match.group(1).strip().upper()
        value = match.group(2).strip()
        if key:
            fields[key] = value
    return fields


def _normalized(fields: dict[str, str], key: str) -> str:
    value = fields.get(key, "")
    return value.strip().upper()


def _require_nonempty(fields: dict[str, str], key: str, failures: list[str]) -> str:
    value = fields.get(key, "").strip()
    if not value:
        failures.append(f"Missing required field: {key}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate dual-judge gate from round contract. "
            "Exit 0=pass, 1=gate fail, 2=input/infra error."
        )
    )
    parser.add_argument(
        "--round-contract-md",
        type=Path,
        default=Path("docs/context/round_contract_latest.md"),
    )
    args = parser.parse_args(argv)

    contract_path = args.round_contract_md
    if not contract_path.exists():
        print(f"[ERROR] Missing input file: {contract_path}")
        return 2

    try:
        fields = _parse_contract_fields(contract_path)
    except Exception as exc:
        print(f"[ERROR] Failed to read or parse contract: {exc}")
        return 2

    decision_class = _normalized(fields, "DECISION_CLASS")
    risk_tier = _normalized(fields, "RISK_TIER")

    classifier_failures: list[str] = []
    if not decision_class:
        classifier_failures.append("Missing required classifier: DECISION_CLASS")
    if not risk_tier:
        classifier_failures.append("Missing required classifier: RISK_TIER")

    if decision_class and decision_class not in {DECISION_ONE_WAY, DECISION_TWO_WAY}:
        classifier_failures.append(f"Invalid DECISION_CLASS: {decision_class}")
    if risk_tier and risk_tier not in {RISK_HIGH, "LOW", "MEDIUM"}:
        classifier_failures.append(f"Invalid RISK_TIER: {risk_tier}")

    if classifier_failures:
        for item in classifier_failures:
            print(f"[FAIL] {item}")
        return 1

    dual_required = decision_class == DECISION_ONE_WAY or risk_tier == RISK_HIGH
    if not dual_required and decision_class == DECISION_TWO_WAY and risk_tier in LOW_MEDIUM_RISKS:
        print("[OK] Dual-judge not required for LOW/MEDIUM TWO_WAY round.")
        return 0

    failures: list[str] = []
    dual_flag = _normalized(fields, "DUAL_JUDGE_REQUIRED")
    if dual_flag != DUAL_REQUIRED:
        failures.append("DUAL_JUDGE_REQUIRED must be YES for high-risk round")

    verdict_1 = _require_nonempty(fields, "DUAL_JUDGE_AUDITOR_1_VERDICT", failures)
    verdict_2 = _require_nonempty(fields, "DUAL_JUDGE_AUDITOR_2_VERDICT", failures)

    if verdict_1 and verdict_2 and verdict_1.strip().upper() != verdict_2.strip().upper():
        resolution = fields.get("DUAL_JUDGE_RESOLUTION", "").strip()
        if not resolution:
            failures.append(
                "DUAL_JUDGE_RESOLUTION is required when auditor verdicts diverge"
            )

    if failures:
        for item in failures:
            print(f"[FAIL] {item}")
        return 1

    print("[OK] Dual-judge gate passed for high-risk round.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
