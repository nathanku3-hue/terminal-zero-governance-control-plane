"""Test Repair Loop — Phase 5C.2

Runs a test suite (default: pytest) against a target path and iteratively
applies fixes up to a hard maximum of MAX_ITERATIONS (5). If test failures
are not resolved within the iteration cap, raises HumanEscalationRequired.

Design constraints (D-188 / ADR-001 §4):
- Hard iteration cap: MAX_ITERATIONS = 5. Enforced in code; cannot be
  overridden by callers without a decision log entry and code review.
- Fail-closed on fix-command errors: nonzero fix exit raises LintCommandError
  immediately instead of deferring until cap exhaustion.
- No authority to approve changes or bypass auditor/CEO-GO gates.

Output contract
---------------
TestRepairResult:
    target          : str
    iterations_used : int
    max_iterations  : int   — always MAX_ITERATIONS (5)
    final_status    : str   — "passing" | "escalated" | "error"
    failures        : list[str]
    iteration_log   : list[TestIterationRecord]
    error           : str | None

TestIterationRecord:
    iteration, test_output, failure_count, fix_applied, fix_output

HumanEscalationRequired (re-exported from lint_repair_loop):
    Raised when MAX_ITERATIONS exhausted with remaining failures.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Sequence

from sop.scripts.lint_repair_loop import (
    HumanEscalationRequired, LintCommandError, MAX_ITERATIONS, _run,
)
try:
    from sop.scripts.sandbox_executor import run_repair_in_sandbox as _sandbox_repair
except ModuleNotFoundError:
    _sandbox_repair = None  # type: ignore


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TestIterationRecord:
    iteration: int
    test_output: str
    failure_count: int
    fix_applied: bool
    fix_output: str | None = None


@dataclass
class TestRepairResult:
    target: str
    iterations_used: int
    max_iterations: int
    final_status: str
    failures: list[str]
    iteration_log: list[TestIterationRecord] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Failure detection
# ---------------------------------------------------------------------------

_FAILURE_MARKERS = (
    "FAILED", "ERROR", "error:", "ERRORS", "failed", "AssertionError", "Traceback",
)


def _parse_failures(raw_output: str) -> list[str]:
    """Return lines from test output that indicate failures."""
    return [
        line for line in raw_output.splitlines()
        if line.strip() and any(m in line for m in _FAILURE_MARKERS)
    ]


def _is_passing(exit_code: int, failures: list[str]) -> bool:
    """Return True only when exit code is 0 AND no failure markers found."""
    return exit_code == 0 and len(failures) == 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_test_repair(
    target: str | Path | Sequence[str],
    *,
    test_cmd: Sequence[str] | None = None,
    fix_cmd: Sequence[str] | None = None,
    cwd: Path | None = None,
    repo_root: Path | None = None,
    use_sandbox: bool = False,
) -> TestRepairResult:
    """Run the test-repair loop against *target*.

    The iteration cap is fixed at MAX_ITERATIONS (5) and cannot be overridden.

    Args:
        target: Path, directory, or sequence of pytest args.
        test_cmd: Full test command. Defaults to
            ``[sys.executable, "-m", "pytest", <target>, "-x", "-q"]``.
        fix_cmd: Repair command. None or [] = observation-only mode.
        cwd: Working directory.
        repo_root: Used when use_sandbox=True.
        use_sandbox: Route fix commands through Docker sandbox.

    Returns:
        :class:`TestRepairResult` with final_status ``"passing"``.

    Raises:
        LintCommandError: Fix command exited nonzero (fixer crashed).
        HumanEscalationRequired: Failures remain after MAX_ITERATIONS.
    """
    if isinstance(target, (str, Path)):
        target_str = str(target)
        target_args = [target_str]
    else:
        target_args = list(target)
        target_str = " ".join(target_args)

    if test_cmd is None:
        test_cmd = [sys.executable, "-m", "pytest"] + target_args + ["-x", "-q"]

    iteration_log: list[TestIterationRecord] = []
    failures: list[str] = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        test_exit, test_output = _run(test_cmd, cwd=cwd)
        failures = _parse_failures(test_output)

        fix_applied = False
        fix_output: str | None = None

        if _is_passing(test_exit, failures):
            iteration_log.append(TestIterationRecord(
                iteration=iteration,
                test_output=test_output,
                failure_count=0,
                fix_applied=False,
            ))
            return TestRepairResult(
                target=target_str,
                iterations_used=iteration,
                max_iterations=MAX_ITERATIONS,
                final_status="passing",
                failures=[],
                iteration_log=iteration_log,
            )

        # --- fix pass ---
        if fix_cmd:
            if use_sandbox and _sandbox_repair is not None:
                sr = _sandbox_repair(fix_cmd, repo_root=repo_root, check_docker=True)
                fix_output = (sr.stdout + sr.stderr).strip()
                if not sr.success:
                    raise LintCommandError(
                        f"Sandbox fix command failed (exit {sr.exit_code}) on iteration {iteration}. "
                        f"Output: {fix_output!r}. Command: {list(fix_cmd)}"
                    )
                fix_applied = True
            else:
                fix_exit, fix_output = _run(fix_cmd, cwd=cwd)
                if fix_exit != 0:
                    raise LintCommandError(
                        f"Fix command exited {fix_exit} on iteration {iteration}. "
                        f"Output: {fix_output!r}. Command: {list(fix_cmd)}"
                    )
                fix_applied = True

        iteration_log.append(TestIterationRecord(
            iteration=iteration,
            test_output=test_output,
            failure_count=len(failures),
            fix_applied=fix_applied,
            fix_output=fix_output,
        ))

    result = TestRepairResult(
        target=target_str,
        iterations_used=MAX_ITERATIONS,
        max_iterations=MAX_ITERATIONS,
        final_status="escalated",
        failures=failures,
        iteration_log=iteration_log,
    )
    raise HumanEscalationRequired(
        f"Test repair exhausted {MAX_ITERATIONS} iterations with "
        f"{len(failures)} remaining failure(s) for {target_str!r}. "
        "Human review required before proceeding.",
        result=result,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Iterative test repair loop with hard iteration cap (Phase 5C.2)."
    )
    parser.add_argument("target", help="Test path or directory.")
    parser.add_argument("--test-cmd", nargs="+", metavar="ARG",
                        help="Full test command (default: python -m pytest <target> -x -q).")
    parser.add_argument("--fix-cmd", nargs="+", metavar="ARG",
                        help="Fix command to run after each failing iteration.")
    parser.add_argument("--cwd", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None,
                        help="Write JSON result to this path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        result = run_test_repair(
            target=args.target,
            test_cmd=args.test_cmd or None,
            fix_cmd=args.fix_cmd or None,
            cwd=args.cwd,
        )
    except HumanEscalationRequired as exc:
        result = exc.result
        print(
            f"ESCALATION_REQUIRED: {len(result.failures)} failure(s) remain after "
            f"{result.iterations_used} iteration(s). Human review required.",
            file=sys.stderr,
        )
    except LintCommandError as exc:
        print(f"TEST_COMMAND_ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result.to_dict(), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"TEST_REPAIR_STATUS: {result.final_status}")
        print(f"TEST_REPAIR_ITERATIONS: {result.iterations_used}/{result.max_iterations}")
        print(f"TEST_REPAIR_FAILURES: {len(result.failures)}")
    else:
        print(payload)

    return 0 if result.final_status == "passing" else 1


if __name__ == "__main__":
    raise SystemExit(main())
