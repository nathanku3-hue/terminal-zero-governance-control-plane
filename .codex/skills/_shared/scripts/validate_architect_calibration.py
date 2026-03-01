#!/usr/bin/env python3
"""Validate architect profile calibration using historical outcomes."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history-csv", required=True)
    parser.add_argument("--active-profile", required=True)
    parser.add_argument("--min-rows", type=int, default=5)
    parser.add_argument("--tolerance", type=float, default=0.10)
    args = parser.parse_args()

    try:
        stats: dict[str, list[float]] = defaultdict(list)
        with open(args.history_csv, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                profile = str(row.get("profile", "")).strip()
                outcome_raw = str(row.get("outcome", "")).strip()
                if not profile or outcome_raw == "":
                    continue
                try:
                    outcome = float(outcome_raw)
                except ValueError:
                    continue
                stats[profile].append(outcome)

        total_rows = sum(len(v) for v in stats.values())
        if total_rows < args.min_rows:
            print(f"INSUFFICIENT: rows={total_rows} min_rows={args.min_rows}")
            return 0

        if args.active_profile not in stats:
            print(f"INVALID: active_profile not found in history: {args.active_profile}")
            return 1

        rates = {k: sum(v) / len(v) for k, v in stats.items()}
        best_profile = max(rates, key=rates.get)
        best_rate = rates[best_profile]
        active_rate = rates[args.active_profile]

        if (best_rate - active_rate) > args.tolerance:
            print(
                "DRIFT: "
                f"active_profile={args.active_profile} active_rate={active_rate:.3f} "
                f"best_profile={best_profile} best_rate={best_rate:.3f}"
            )
            return 2

        print(
            "PASS: "
            f"active_profile={args.active_profile} active_rate={active_rate:.3f} "
            f"best_profile={best_profile} best_rate={best_rate:.3f}"
        )
        return 0
    except OSError as err:
        print(f"INVALID: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

