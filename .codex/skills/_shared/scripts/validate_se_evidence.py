#!/usr/bin/env python3
"""Validate SE task->evidence mapping, run-id match, and evidence freshness."""

from __future__ import annotations

import argparse
import datetime as dt
import sys


def parse_iso_utc(value: str) -> dt.datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp missing timezone: {value}")
    return parsed.astimezone(dt.timezone.utc)


def parse_task_map(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in [x.strip() for x in raw.split(",") if x.strip()]:
        if ":" not in item:
            raise ValueError(f"Invalid task mapping: {item}")
        task_id, evidence_id = [x.strip() for x in item.split(":", 1)]
        if not task_id or not evidence_id:
            raise ValueError(f"Invalid task mapping: {item}")
        out[task_id] = evidence_id
    if not out:
        raise ValueError("TaskEvidenceMap is empty")
    return out


def parse_evidence_map(raw: str) -> dict[str, tuple[str, dt.datetime]]:
    out: dict[str, tuple[str, dt.datetime]] = {}
    for item in [x.strip() for x in raw.split(";") if x.strip()]:
        parts = [x.strip() for x in item.split("|")]
        if len(parts) != 3:
            raise ValueError(f"Invalid evidence row: {item}")
        evidence_id, run_id, evidence_utc = parts
        if not evidence_id or not run_id:
            raise ValueError(f"Invalid evidence row: {item}")
        out[evidence_id] = (run_id, parse_iso_utc(evidence_utc))
    if not out:
        raise ValueError("EvidenceRows is empty")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-id", required=True)
    parser.add_argument("--round-exec-utc", required=True)
    parser.add_argument("--task-map", required=True, help="TSK-01:EVD-01,TSK-02:EVD-02")
    parser.add_argument(
        "--evidence-map",
        required=True,
        help="EVD-01|R1|2026-01-01T00:00:00Z;EVD-02|R1|2026-01-01T00:01:00Z",
    )
    parser.add_argument("--max-age-hours", type=float, default=24.0)
    args = parser.parse_args()

    try:
        round_exec = parse_iso_utc(args.round_exec_utc)
        task_map = parse_task_map(args.task_map)
        evidence_map = parse_evidence_map(args.evidence_map)

        max_age_seconds = args.max_age_hours * 3600.0

        for task_id, evidence_id in task_map.items():
            if evidence_id not in evidence_map:
                raise ValueError(f"{task_id} references missing evidence_id: {evidence_id}")
            run_id, evidence_utc = evidence_map[evidence_id]
            if run_id != args.round_id:
                raise ValueError(
                    f"{task_id}/{evidence_id} run_id mismatch: {run_id} != {args.round_id}"
                )

            delta = (round_exec - evidence_utc).total_seconds()
            if delta < -300:
                raise ValueError(f"{task_id}/{evidence_id} evidence timestamp is in the future")
            if delta > max_age_seconds:
                raise ValueError(
                    f"{task_id}/{evidence_id} evidence is older than {args.max_age_hours} hours"
                )

        print("VALID")
        return 0
    except ValueError as err:
        print(f"INVALID: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

