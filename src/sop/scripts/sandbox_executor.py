"""Sandbox Executor — Phase 5C.3

Executes commands inside a Docker container for isolated, fail-closed
worker execution. Never falls back to host execution.

Design constraints (D-188 / ADR-001 §4):
- Fail-closed on Docker unavailable: if Docker cannot be reached or the
  image cannot be used, SandboxUnavailableError is raised immediately.
  There is NO silent fallback to host execution — that would violate the
  isolation guarantee.
- Fail-closed on container errors: non-zero container exit codes are
  treated as execution failures and surfaced in SandboxResult.
- No new authority paths: this module performs mechanical command
  execution only. It cannot approve changes or bypass auditor/CEO-GO gates.
- The caller supplies the image and command; this module supplies the
  containment and evidence.

Output contract
---------------
SandboxResult:
    command         : list[str] — the command that was run
    image           : str       — Docker image used
    exit_code       : int       — container exit code
    stdout          : str
    stderr          : str
    success         : bool      — True only when exit_code == 0
    error           : str | None — set when sandbox infrastructure failed

SandboxUnavailableError:
    Raised when Docker is not reachable or the executor cannot guarantee
    isolation. Callers MUST NOT swallow this and fall back to host execution.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SandboxUnavailableError(Exception):
    """Raised when Docker is not available or sandbox cannot be guaranteed.

    Callers MUST NOT catch this and fall back to host execution.
    Doing so would silently remove the isolation guarantee.
    """


class SandboxExecutionError(Exception):
    """Raised when the sandbox infrastructure itself fails (not the command)."""


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------

@dataclass
class SandboxResult:
    command: list
    image: str
    exit_code: int
    stdout: str
    stderr: str
    success: bool
    error: object = None  # str | None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Docker availability check
# ---------------------------------------------------------------------------

DEFAULT_IMAGE = "python:3.12-slim"


def _docker_exe() -> str:
    """Return the Docker executable path or raise SandboxUnavailableError."""
    exe = shutil.which("docker")
    if exe is None:
        raise SandboxUnavailableError(
            "Docker executable not found on PATH. "
            "Install Docker and ensure it is reachable before using the sandbox executor. "
            "Host-execution fallback is not permitted."
        )
    return exe


def check_docker_available() -> None:
    """Verify Docker daemon is reachable. Raises SandboxUnavailableError if not."""
    exe = _docker_exe()
    try:
        result = subprocess.run(
            [exe, "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError as exc:
        raise SandboxUnavailableError(f"Docker executable not found: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise SandboxUnavailableError(
            "Docker daemon did not respond within 10 seconds. "
            "Ensure the Docker daemon is running."
        ) from exc
    except Exception as exc:
        raise SandboxUnavailableError(f"Unexpected error checking Docker: {exc}") from exc

    if result.returncode != 0:
        raise SandboxUnavailableError(
            f"Docker daemon is not reachable (exit {result.returncode}). "
            f"stderr: {result.stderr.strip()!r}. "
            "Ensure the Docker daemon is running."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_in_sandbox(
    command: Sequence[str],
    *,
    image: str = DEFAULT_IMAGE,
    workdir: str = "/workspace",
    mount: tuple[str, str] | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
    check_docker: bool = True,
) -> SandboxResult:
    """Execute *command* inside a Docker container.

    Args:
        command: The command and arguments to run inside the container.
        image: Docker image to use. Defaults to ``python:3.12-slim``.
        workdir: Working directory inside the container.
        mount: Optional ``(host_path, container_path)`` bind-mount tuple.
            The host path is mounted read-write at the container path.
        env: Optional environment variables to pass into the container.
        timeout: Maximum seconds to wait for the container. Default 300.
        check_docker: When True (default), verify Docker availability before
            running. Set False only in tests that mock subprocess directly.

    Returns:
        :class:`SandboxResult` with the command output.

    Raises:
        SandboxUnavailableError: Docker is not available. No fallback.
        SandboxExecutionError: Container could not be started (infrastructure
            failure, not a command failure).
    """
    if check_docker:
        check_docker_available()

    exe = _docker_exe()
    cmd: list[str] = [
        exe, "run",
        "--rm",
        "--network", "none",
        "--workdir", workdir,
    ]

    if mount is not None:
        host_path, container_path = mount
        cmd += ["-v", f"{host_path}:{container_path}"]

    if env:
        for k, v in env.items():
            cmd += ["-e", f"{k}={v}"]

    cmd.append(image)
    cmd.extend(list(command))

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SandboxExecutionError(
            f"Container timed out after {timeout}s running {list(command)}"
        ) from exc
    except FileNotFoundError as exc:
        raise SandboxUnavailableError(
            f"Docker executable not found during execution: {exc}"
        ) from exc
    except Exception as exc:
        raise SandboxExecutionError(
            f"Unexpected error starting container: {exc}"
        ) from exc

    return SandboxResult(
        command=list(command),
        image=image,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        success=proc.returncode == 0,
    )


def run_repair_in_sandbox(
    repair_cmd: Sequence[str],
    *,
    image: str = DEFAULT_IMAGE,
    repo_root: Path | None = None,
    timeout: int = 120,
    check_docker: bool = True,
) -> SandboxResult:
    """Run a repair command (lint fix or test fix) inside the sandbox.

    Convenience wrapper used by the 5C.2 repair loops. Mounts *repo_root*
    at ``/workspace`` when provided so the repair command operates on the
    actual source tree.

    Args:
        repair_cmd: The repair command to run (e.g. ``["ruff", "check", "--fix", "."]``).
        image: Docker image.
        repo_root: Local repository root to mount at ``/workspace``.
        timeout: Maximum seconds.
        check_docker: Passed through to :func:`run_in_sandbox`.

    Returns:
        :class:`SandboxResult`.

    Raises:
        SandboxUnavailableError: Docker not available. No fallback.
        SandboxExecutionError: Container infrastructure failure.
    """
    mount: tuple[str, str] | None = None
    if repo_root is not None:
        mount = (str(repo_root.resolve()), "/workspace")

    return run_in_sandbox(
        command=repair_cmd,
        image=image,
        workdir="/workspace",
        mount=mount,
        timeout=timeout,
        check_docker=check_docker,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a command inside a Docker sandbox (Phase 5C.3)."
    )
    parser.add_argument(
        "command",
        nargs="+",
        help="Command and arguments to run inside the container.",
    )
    parser.add_argument(
        "--image",
        default=DEFAULT_IMAGE,
        help=f"Docker image to use (default: {DEFAULT_IMAGE}).",
    )
    parser.add_argument(
        "--workdir",
        default="/workspace",
        help="Working directory inside the container (default: /workspace).",
    )
    parser.add_argument(
        "--mount",
        metavar="HOST:CONTAINER",
        help="Bind-mount as host_path:container_path.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum seconds to wait (default: 300).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON result to this path.",
    )
    parser.add_argument(
        "--check-docker",
        action="store_true",
        default=True,
        help="Verify Docker availability before running (default: True).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    mount: tuple[str, str] | None = None
    if args.mount:
        parts = args.mount.split(":", 1)
        if len(parts) != 2:
            print("ERROR: --mount must be HOST:CONTAINER", file=sys.stderr)
            return 2
        mount = (parts[0], parts[1])

    try:
        result = run_in_sandbox(
            command=args.command,
            image=args.image,
            workdir=args.workdir,
            mount=mount,
            timeout=args.timeout,
            check_docker=args.check_docker,
        )
    except SandboxUnavailableError as exc:
        print(f"SANDBOX_UNAVAILABLE: {exc}", file=sys.stderr)
        return 3
    except SandboxExecutionError as exc:
        print(f"SANDBOX_ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result.to_dict(), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"SANDBOX_STATUS: {'success' if result.success else 'failed'}")
        print(f"SANDBOX_EXIT_CODE: {result.exit_code}")
        print(f"SANDBOX_IMAGE: {result.image}")
    else:
        print(payload)

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
