from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHECKS: tuple[dict[str, Any], ...] = (
    {
        "name": "validate_loop_closure",
        "args": [
            "scripts/validate_loop_closure.py",
            "--repo-root",
            ".",
            "--freshness-hours",
            "72",
        ],
    },
    {
        "name": "run_loop_cycle",
        "args": [
            "scripts/run_loop_cycle.py",
            "--repo-root",
            ".",
            "--skip-phase-end",
            "--allow-hold",
            "true",
        ],
    },
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_text(value: str) -> str:
    return value.strip().upper()


def _status_for_check(name: str, exit_code: int, stdout: str, stderr: str) -> str:
    combined = f"{stdout}\n{stderr}".upper()
    if name == "validate_loop_closure":
        if exit_code == 0 and "READY_TO_ESCALATE" in combined:
            return "PASS"
        if exit_code == 1 and "NOT_READY" in combined:
            return "HOLD"
        return "FAIL"

    if name == "run_loop_cycle":
        if exit_code == 0:
            if "HOLD" in combined:
                return "HOLD"
            if "PASS" in combined:
                return "PASS"
            return "PASS"
        return "FAIL"

    return "FAIL"


def _run_check(
    *,
    repo_root: Path,
    python_exe: str,
    name: str,
    args: list[str],
) -> dict[str, Any]:
    command = [python_exe, *args]
    result = subprocess.run(
        command,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    status = _status_for_check(name=name, exit_code=result.returncode, stdout=stdout, stderr=stderr)
    return {
        "name": name,
        "status": status,
        "exit_code": result.returncode,
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic fast checks for loop closure and loop cycle. "
            "Exit 0 when overall PASS/HOLD by default, 1 when FAIL. "
            "Use --fail-on-hold to make HOLD exit 1."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--python-exe", type=str, default=sys.executable)
    parser.add_argument(
        "--fail-on-hold",
        action="store_true",
        help="Exit 1 when overall status is HOLD instead of allowing a zero exit code.",
    )
    return parser.parse_args(argv)


def run_fast_checks(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_root = args.repo_root.resolve()
    results = [
        _run_check(
            repo_root=repo_root,
            python_exe=args.python_exe,
            name=spec["name"],
            args=list(spec["args"]),
        )
        for spec in CHECKS
    ]

    if any(item["status"] == "FAIL" for item in results):
        overall = "FAIL"
        exit_code = 1
        exit_reason = "fail_detected"
    elif any(item["status"] == "HOLD" for item in results):
        overall = "HOLD"
        exit_code = 1 if args.fail_on_hold else 0
        exit_reason = "hold_detected_fail_on_hold" if args.fail_on_hold else "hold_detected_allowed"
    else:
        overall = "PASS"
        exit_code = 0
        exit_reason = "all_checks_passed"

    payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": _utc_now_iso(),
        "repo_root": str(repo_root),
        "overall_status": overall,
        "hold_detected": overall == "HOLD",
        "fail_on_hold": bool(args.fail_on_hold),
        "exit_reason": exit_reason,
        "checks": results,
    }
    return exit_code, payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, payload = run_fast_checks(args)

    print(f"overall_status: {_normalize_text(payload['overall_status'])}")
    print(f"hold_detected: {str(payload['hold_detected']).lower()}")
    print(f"fail_on_hold: {str(payload['fail_on_hold']).lower()}")
    print(f"exit_reason: {_normalize_text(payload['exit_reason'])}")
    for check in payload["checks"]:
        print(
            f"- {check['name']}: {_normalize_text(check['status'])} "
            f"(exit={check['exit_code']})"
        )

    if payload["overall_status"] == "HOLD" and not payload["fail_on_hold"]:
        print("note: HOLD is distinct from PASS and is non-failing unless --fail-on-hold is set")

    if args.json_out is not None:
        _write_json(args.json_out, payload)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
