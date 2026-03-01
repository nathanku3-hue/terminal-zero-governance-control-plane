#!/usr/bin/env python3
"""Validate a machine-checkable closure packet line.

Expected packet format:
ClosurePacket: RoundID=<id>; ScopeID=<id>; ChecksTotal=<int>; ChecksPassed=<int>; ChecksFailed=<int>; Verdict=<PASS|BLOCK>; OpenRisks=<text>; NextAction=<text>
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import Dict


REQUIRED_KEYS = (
    "RoundID",
    "ScopeID",
    "ChecksTotal",
    "ChecksPassed",
    "ChecksFailed",
    "Verdict",
)

OPTIONAL_KEYS = (
    "OpenRisks",
    "NextAction",
)


def parse_packet(packet: str) -> Dict[str, str]:
    line = packet.strip()
    if line.startswith("ClosurePacket:"):
        line = line[len("ClosurePacket:") :].strip()

    pairs = [part.strip() for part in line.split(";") if part.strip()]
    data: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid token (missing '='): {pair}")
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid token (empty key): {pair}")
        data[key] = value
    return data


def validate_id(name: str, value: str) -> None:
    if not value:
        raise ValueError(f"{name} is empty")
    if not re.match(r"^[A-Za-z0-9._:-]+$", value):
        raise ValueError(f"{name} contains unsupported characters: {value}")


def validate_int(name: str, value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} is not an integer: {value}") from exc
    if parsed < 0:
        raise ValueError(f"{name} must be >= 0: {value}")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, help="ClosurePacket line to validate")
    parser.add_argument(
        "--require-open-risks-when-block",
        action="store_true",
        help="Require non-empty OpenRisks if Verdict=BLOCK",
    )
    parser.add_argument(
        "--require-next-action-when-block",
        action="store_true",
        help="Require non-empty NextAction if Verdict=BLOCK",
    )
    args = parser.parse_args()

    try:
        data = parse_packet(args.packet)
        missing = [k for k in REQUIRED_KEYS if k not in data]
        if missing:
            raise ValueError(f"Missing required key(s): {', '.join(missing)}")

        validate_id("RoundID", data["RoundID"])
        validate_id("ScopeID", data["ScopeID"])

        total = validate_int("ChecksTotal", data["ChecksTotal"])
        passed = validate_int("ChecksPassed", data["ChecksPassed"])
        failed = validate_int("ChecksFailed", data["ChecksFailed"])

        if passed + failed != total:
            raise ValueError(
                f"Checks math mismatch: ChecksPassed ({passed}) + "
                f"ChecksFailed ({failed}) != ChecksTotal ({total})"
            )

        verdict = data["Verdict"].upper()
        if verdict not in {"PASS", "BLOCK"}:
            raise ValueError(f"Verdict must be PASS or BLOCK, got: {data['Verdict']}")

        if verdict == "BLOCK":
            if args.require_open_risks_when_block:
                if not data.get("OpenRisks", "").strip():
                    raise ValueError("OpenRisks is required when Verdict=BLOCK")
            if args.require_next_action_when_block:
                if not data.get("NextAction", "").strip():
                    raise ValueError("NextAction is required when Verdict=BLOCK")

        unknown = sorted(set(data.keys()) - set(REQUIRED_KEYS) - set(OPTIONAL_KEYS))
        if unknown:
            # Unknown keys are allowed for forward compatibility; print note.
            print(f"WARN unknown key(s): {', '.join(unknown)}")

        print("VALID")
        return 0
    except ValueError as err:
        print(f"INVALID: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

