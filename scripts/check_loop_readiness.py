#!/usr/bin/env python3
"""src/sop/scripts/check_loop_readiness.py

Phase 3 Stream C -- Checklist Matrix: Loop Readiness Check.

Reads ``skills_status`` from ``loop_cycle_summary_latest.json`` (top-level key
``summary["skills_status"]``) and projects loop readiness into
``docs/context/loop_readiness_latest.json``.

Phase A (stub mode): accepts ``--skills-status`` argument for static input
so the artifact can be produced and tested without running the live loop.

Phase B integration: reads from loop_cycle_summary_latest.json when
``--skills-status`` is not supplied (wired after Stream B Day 4 H-5 merge).

Routing table:
  RESOLVER_UNAVAILABLE -> broken_install  (loop_ready=false)
  EMPTY_BY_DESIGN      -> empty_by_design (loop_ready=true)
  ACTIVE or OK         -> skills_active   (loop_ready=true)
  (absent/unknown)     -> unknown         (loop_ready=true, fail-open)

Hard invariant: RESOLVER_UNAVAILABLE must NEVER produce routing=empty_by_design.

Exits 0 on success, 1 on unrecoverable error.

Usage:
    python scripts/check_loop_readiness.py [--repo-root <path>]
    python scripts/check_loop_readiness.py [--skills-status <value>]
    python scripts/check_loop_readiness.py [--output <path>]
    python scripts/check_loop_readiness.py --help
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


_SCHEMA_VERSION = "1.0"
_SUMMARY_PATH = Path("docs") / "context" / "loop_cycle_summary_latest.json"
_OUTPUT_PATH = Path("docs") / "context" / "loop_readiness_latest.json"
_VALIDATE_SKILL_ACTIVATION_SCRIPT = "scripts/validate_skill_activation.py"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _route(skills_status: str | None) -> dict:
    """Apply routing logic and return routing payload dict.

    Hard invariant: RESOLVER_UNAVAILABLE must never produce routing=empty_by_design.
    """
    if skills_status == "RESOLVER_UNAVAILABLE":
        return {
            "routing": "broken_install",
            "loop_ready": False,
            "operator_action": (
                "Skill resolver import failed. Run: pip install -e . then rerun sop."
            ),
            "readiness_checks": [
                {
                    "check": "skill_resolver_available",
                    "result": "FAIL",
                    "reason": "Skill resolver import failed (RESOLVER_UNAVAILABLE).",
                },
            ],
        }
    elif skills_status == "EMPTY_BY_DESIGN":
        return {
            "routing": "empty_by_design",
            "loop_ready": True,
            "operator_action": None,
            "readiness_checks": [
                {
                    "check": "skill_resolver_available",
                    "result": "PASS",
                    "reason": "Resolver loaded successfully.",
                },
                {
                    "check": "skills_configured",
                    "result": "SKIP",
                    "reason": "No skills in active_skills; empty-by-design repo.",
                },
            ],
        }
    elif skills_status in ("ACTIVE", "OK"):
        # skills_active: run validate_skill_activation.py to confirm
        activation_result, activation_reason = _check_skill_activation()
        loop_ready = activation_result == "PASS"
        return {
            "routing": "skills_active",
            "loop_ready": loop_ready,
            "operator_action": (
                None
                if loop_ready
                else "Skill activation validation failed. Check validate_skill_activation.py output."
            ),
            "readiness_checks": [
                {
                    "check": "skill_resolver_available",
                    "result": "PASS",
                    "reason": "Resolver loaded successfully.",
                },
                {
                    "check": "skills_configured",
                    "result": "PASS",
                    "reason": "Active skills present.",
                },
                {
                    "check": "skill_activation_valid",
                    "result": activation_result,
                    "reason": activation_reason,
                },
            ],
        }
    else:
        # Absent or unrecognised -- fail-open, routing=unknown
        return {
            "routing": "unknown",
            "loop_ready": True,
            "operator_action": "Upgrade to post-H-5 build",
            "readiness_checks": [
                {
                    "check": "skill_resolver_available",
                    "result": "SKIP",
                    "reason": (
                        "skills_status field absent or unrecognised; "
                        "pre-H-5 build assumed. Fail-open."
                    ),
                },
            ],
        }


def _check_skill_activation() -> tuple[str, str]:
    """Run validate_skill_activation.py; return (result, reason).

    Returns ("PASS", ...) if exits 0, ("FAIL", ...) otherwise.
    Imported lazily so the module can be used without subprocess in test stubs.
    """
    import subprocess  # noqa: PLC0415

    try:
        proc = subprocess.run(
            [sys.executable, _VALIDATE_SKILL_ACTIVATION_SCRIPT],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode == 0:
            return "PASS", "validate_skill_activation.py exited 0."
        return (
            "FAIL",
            f"validate_skill_activation.py exited {proc.returncode}: {proc.stderr[:200]}",
        )
    except FileNotFoundError:
        return (
            "FAIL",
            f"validate_skill_activation.py not found at {_VALIDATE_SKILL_ACTIVATION_SCRIPT}.",
        )
    except Exception as exc:  # noqa: BLE001
        return "FAIL", f"validate_skill_activation.py error: {exc}"


def _read_skills_status(repo_root: Path) -> str | None:
    """Read skills_status from loop_cycle_summary_latest.json top-level key.

    Phase B integration: summary["skills_status"] -- NOT summary["runtime"]["steps"][-1].
    Returns None if the file does not exist or the key is absent.
    """
    summary_path = repo_root / _SUMMARY_PATH
    if not summary_path.exists():
        return None
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        return data.get("skills_status")  # top-level key; None if absent
    except Exception:  # noqa: BLE001
        return None


def _build_artifact(skills_status: str | None) -> dict:
    """Build the full loop_readiness artifact dict."""
    routing_payload = _route(skills_status)
    artifact = {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "skills_status": skills_status,
        **routing_payload,
    }
    return artifact


def _write_artifact(artifact: dict, output_path: Path) -> None:
    """Atomically write artifact JSON using temp-file + os.replace."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=output_path.parent, prefix=".loop_readiness_tmp_", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_path, output_path)
    except Exception:
        # Best-effort cleanup of temp file on write failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3 Stream C: Checklist Matrix -- Loop Readiness Check. "
            "Reads skills_status and emits loop_readiness_latest.json."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repo root directory (default: auto-detected from script location).",
    )
    parser.add_argument(
        "--skills-status",
        default=None,
        help=(
            "Override skills_status value for stub/test mode. "
            "If not supplied, reads from loop_cycle_summary_latest.json (Phase B)."
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Output path for loop_readiness_latest.json. "
            "Default: <repo-root>/docs/context/loop_readiness_latest.json"
        ),
    )
    args = parser.parse_args(argv)

    # Resolve repo root
    if args.repo_root is not None:
        repo_root = Path(args.repo_root).resolve()
    else:
        _here = Path(__file__).resolve()
        repo_root = _here.parent
        # Walk up looking for pyproject.toml or scripts/ as repo root markers
        for ancestor in [_here.parent, _here.parent.parent,
                         _here.parent.parent.parent,
                         _here.parent.parent.parent.parent,
                         _here.parent.parent.parent.parent.parent]:
            if (ancestor / "pyproject.toml").exists() or (ancestor / "scripts").is_dir():
                repo_root = ancestor
                break

    # Resolve output path
    if args.output is not None:
        output_path = Path(args.output).resolve()
    else:
        output_path = repo_root / _OUTPUT_PATH

    # Determine skills_status
    if args.skills_status is not None:
        # Stub/test mode: use supplied value
        skills_status: str | None = args.skills_status if args.skills_status != "" else None
    else:
        # Phase B: read from live summary artifact
        skills_status = _read_skills_status(repo_root)

    # Build and write artifact
    artifact = _build_artifact(skills_status)
    try:
        _write_artifact(artifact, output_path)
    except Exception as exc:
        print(
            f"FATAL failure_class=artifact_write_error failed_component=check_loop_readiness "
            f"recoverability=manual artifact_write_failed=true error={exc}",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(artifact, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
