"""Lint Repair Loop — Phase 5C.2

Design constraints (D-188 / ADR-001 §4):
- Hard iteration cap: MAX_ITERATIONS = 5. ENFORCED IN CODE; not overridable by callers.
- Fail-closed: nonzero lint exit with no output raises LintCommandError immediately.
- Fail-closed: nonzero fix exit raises LintCommandError immediately.
- No bypass of auditor review or CEO GO signal.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Sequence

try:
    from sop.scripts.sandbox_executor import run_repair_in_sandbox as _sandbox_repair
except ModuleNotFoundError:
    _sandbox_repair = None  # type: ignore


MAX_ITERATIONS: int = 5  # D-188 — enforced in code


class HumanEscalationRequired(Exception):
    def __init__(self, message: str, result: "LintRepairResult") -> None:
        super().__init__(message)
        self.result = result


class LintCommandError(Exception):
    """Raised on infra failures: missing exe, nonzero lint exit with no output, nonzero fix exit."""


@dataclass
class IterationRecord:
    iteration: int
    lint_output: str
    findings_count: int
    fix_applied: bool
    fix_output: str | None = None


@dataclass
class LintRepairResult:
    target: str
    iterations_used: int
    max_iterations: int
    final_status: str
    findings: list[str]
    iteration_log: list[IterationRecord] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _run(cmd: Sequence[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(list(cmd), capture_output=True, text=True,
                              cwd=str(cwd) if cwd else None)
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError as exc:
        raise LintCommandError(f"Executable not found: {cmd[0]!r} — {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise LintCommandError(f"Unexpected error running {cmd[0]!r}: {exc}") from exc


def _parse_findings(raw_output: str) -> list[str]:
    return [line for line in raw_output.splitlines() if line.strip()]


def run_lint_repair(
    target: str | Path,
    *,
    lint_cmd: Sequence[str] | None = None,
    fix_cmd: Sequence[str] | None = None,
    cwd: Path | None = None,
    repo_root: Path | None = None,
    use_sandbox: bool = False,
) -> LintRepairResult:
    """Run lint-repair loop. Cap fixed at MAX_ITERATIONS=5; not caller-overridable.

    Raises:
        LintCommandError: nonzero lint exit with no output, or nonzero fix exit.
        HumanEscalationRequired: findings remain after MAX_ITERATIONS.
    """
    target = Path(target)
    target_str = str(target)

    if lint_cmd is None:
        lint_cmd = ["ruff", "check", target_str]
    if fix_cmd is None:
        fix_cmd = ["ruff", "check", "--fix", target_str]

    iteration_log: list[IterationRecord] = []
    findings: list[str] = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        lint_exit, lint_output = _run(lint_cmd, cwd=cwd)
        findings = _parse_findings(lint_output)

        # Fail-closed: nonzero exit + no output = infra failure, not clean.
        if lint_exit != 0 and not findings:
            raise LintCommandError(
                f"Lint command exited {lint_exit} with no output on iteration {iteration}. "
                "Infrastructure failure — not a clean result. "
                f"Command: {list(lint_cmd)}"
            )

        fix_applied = False
        fix_output: str | None = None

        if not findings:
            iteration_log.append(IterationRecord(
                iteration=iteration, lint_output=lint_output,
                findings_count=0, fix_applied=False))
            return LintRepairResult(
                target=target_str, iterations_used=iteration,
                max_iterations=MAX_ITERATIONS, final_status="clean",
                findings=[], iteration_log=iteration_log)

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

        iteration_log.append(IterationRecord(
            iteration=iteration, lint_output=lint_output,
            findings_count=len(findings), fix_applied=fix_applied,
            fix_output=fix_output))

    result = LintRepairResult(
        target=target_str, iterations_used=MAX_ITERATIONS,
        max_iterations=MAX_ITERATIONS, final_status="escalated",
        findings=findings, iteration_log=iteration_log)
    raise HumanEscalationRequired(
        f"Lint repair exhausted {MAX_ITERATIONS} iterations with "
        f"{len(findings)} remaining finding(s) in {target_str!r}. "
        "Human review required before proceeding.",
        result=result)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint repair loop (Phase 5C.2).")
    p.add_argument("target")
    p.add_argument("--lint-cmd", nargs="+", metavar="ARG")
    p.add_argument("--fix-cmd", nargs="+", metavar="ARG")
    p.add_argument("--cwd", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    fix_cmd = [] if args.dry_run else args.fix_cmd
    try:
        result = run_lint_repair(
            target=args.target, lint_cmd=args.lint_cmd or None,
            fix_cmd=fix_cmd, cwd=args.cwd)
    except HumanEscalationRequired as exc:
        result = exc.result
        print(f"ESCALATION_REQUIRED: {len(result.findings)} finding(s) remain after "
              f"{result.iterations_used} iteration(s). Human review required.",
              file=sys.stderr)
    except LintCommandError as exc:
        print(f"LINT_COMMAND_ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result.to_dict(), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"LINT_REPAIR_STATUS: {result.final_status}")
        print(f"LINT_REPAIR_ITERATIONS: {result.iterations_used}/{result.max_iterations}")
        print(f"LINT_REPAIR_FINDINGS: {len(result.findings)}")
    else:
        print(payload)
    return 0 if result.final_status == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
