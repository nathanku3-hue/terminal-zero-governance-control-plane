from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Check registry
# Each entry is a spec; repo_root and freshness_hours are injected at runtime.
# ---------------------------------------------------------------------------

CHECKS: tuple[dict[str, Any], ...] = (
    {
        "name": "startup_gate",
        "script": "scripts/startup_codex_helper.py",
        "extra_args": ["--summary"],
    },
    {
        "name": "run_loop_cycle",
        "script": "scripts/run_loop_cycle.py",
        "extra_args": ["--skip-phase-end", "--allow-hold", "true"],
    },
    {
        "name": "validate_loop_closure",
        "script": "scripts/validate_loop_closure.py",
        "extra_args": [],          # --freshness-hours injected at runtime if provided
    },
)

ALL_CHECK_NAMES: tuple[str, ...] = tuple(spec["name"] for spec in CHECKS)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_text(value: str) -> str:
    return value.strip().upper()


def _final_status_token(stdout: str, stderr: str) -> str | None:
    for stream in (stdout, stderr):
        lines = [_normalize_text(line) for line in stream.splitlines() if _normalize_text(line)]
        if lines:
            return lines[-1]
    return None


def _status_for_check(name: str, exit_code: int, stdout: str, stderr: str) -> str:
    if name == "startup_gate":
        # Pass only if the summary explicitly reports READINESS_STATUS: READY
        for line in stdout.splitlines():
            if _normalize_text(line) == "READINESS_STATUS: READY":
                return "PASS"
        # Any other non-error outcome (including NEEDS_ATTENTION) → HOLD
        if exit_code == 0:
            return "HOLD"
        return "FAIL"

    if name == "validate_loop_closure":
        token = _final_status_token(stdout=stdout, stderr=stderr)
        if exit_code == 0 and token == "READY_TO_ESCALATE":
            return "PASS"
        if exit_code == 1 and token == "NOT_READY":
            return "HOLD"
        return "FAIL"

    if name == "run_loop_cycle":
        token = _final_status_token(stdout=stdout, stderr=stderr)
        if exit_code == 0 and token == "PASS":
            return "PASS"
        if exit_code == 0 and token == "HOLD":
            return "HOLD"
        return "FAIL"

    return "FAIL"


def _build_command(
    *,
    python_exe: str,
    repo_root: Path,
    spec: dict[str, Any],
    freshness_hours: str | None,
) -> list[str]:
    cmd = [python_exe, spec["script"], "--repo-root", str(repo_root)]
    cmd.extend(spec["extra_args"])
    if spec["name"] == "validate_loop_closure" and freshness_hours is not None:
        cmd.extend(["--freshness-hours", freshness_hours])
    return cmd


def _run_check(
    *,
    repo_root: Path,
    python_exe: str,
    spec: dict[str, Any],
    freshness_hours: str | None,
) -> dict[str, Any]:
    command = _build_command(
        python_exe=python_exe,
        repo_root=repo_root,
        spec=spec,
        freshness_hours=freshness_hours,
    )
    result = subprocess.run(
        command,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    status = _status_for_check(
        name=spec["name"], exit_code=result.returncode, stdout=stdout, stderr=stderr
    )
    return {
        "name": spec["name"],
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
    parser.add_argument(
        "--check",
        dest="checks",
        action="append",
        choices=ALL_CHECK_NAMES,
        metavar="CHECK",
        default=None,
        help=(
            f"Run only the named check(s). Repeatable. "
            f"Choices: {', '.join(ALL_CHECK_NAMES)}. "
            f"Default: run all checks in order."
        ),
    )
    parser.add_argument(
        "--freshness-hours",
        type=str,
        default=None,
        dest="freshness_hours",
        help=(
            "Override the freshness threshold (hours) forwarded to validate_loop_closure. "
            "Default: 72 (as hardcoded in the validate_loop_closure default)."
        ),
    )
    return parser.parse_args(argv)


def run_fast_checks(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_root = args.repo_root.resolve()

    # Filter checks by --check selector; default = all in declaration order
    selected_names: list[str] = args.checks if args.checks else list(ALL_CHECK_NAMES)
    # Preserve declaration order even if --check args arrived in different order
    specs_to_run = [spec for spec in CHECKS if spec["name"] in selected_names]

    freshness_hours: str | None = getattr(args, "freshness_hours", None)

    results = [
        _run_check(
            repo_root=repo_root,
            python_exe=args.python_exe,
            spec=spec,
            freshness_hours=freshness_hours,
        )
        for spec in specs_to_run
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
