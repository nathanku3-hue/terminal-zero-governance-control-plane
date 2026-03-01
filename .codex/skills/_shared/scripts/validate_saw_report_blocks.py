#!/usr/bin/env python3
"""Validate required SAW report blocks and closure packet presence."""

from __future__ import annotations

import argparse
import re
import sys


REQUIRED_TOKENS = (
    "SAW Verdict:",
    "Hierarchy Confirmation:",
    "ClosurePacket:",
    "ClosureValidation:",
    "Open Risks:",
    "Next action:",
)

SCOPE_TOKENS = ("in-scope", "inherited")


def load_report_text(args: argparse.Namespace) -> str:
    if args.report:
        return args.report
    if args.report_file:
        with open(args.report_file, "r", encoding="utf-8") as handle:
            return handle.read()
    raise ValueError("Provide --report or --report-file")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="SAW report text")
    parser.add_argument("--report-file", help="Path to SAW report text file")
    args = parser.parse_args()

    try:
        text = load_report_text(args)
        lowered = text.lower()

        for token in REQUIRED_TOKENS:
            if token.lower() not in lowered:
                raise ValueError(f"Missing required token: {token}")

        for token in SCOPE_TOKENS:
            if token not in lowered:
                raise ValueError(f"Missing scope split token: {token}")

        packet_count = len(re.findall(r"^.*ClosurePacket:.*$", text, flags=re.MULTILINE))
        if packet_count != 1:
            raise ValueError(f"Expected exactly one ClosurePacket line, found {packet_count}")

        print("VALID")
        return 0
    except ValueError as err:
        print(f"INVALID: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

