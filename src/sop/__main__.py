#!/usr/bin/env python
"""
sop - Terminal Zero Governance Control Plane CLI

Unified entrypoint for governance loop operations.

Usage:
    sop --help
    sop startup --repo-root .
    sop run --repo-root . --skip-phase-end
    sop validate --repo-root .
    sop takeover --repo-root .
    sop supervise --max-cycles 1
    sop init <target-dir>
"""

import argparse
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import List, Optional


def _get_scripts_dir() -> Path:
    """Get the scripts directory.

    Priority:
    1. Development: repo-root/scripts/ (if this file is in src/sop/)
    2. Installed: package data sop/scripts/
    """
    # Try development path first (repo-root/scripts/)
    dev_scripts = Path(__file__).parent.parent.parent / "scripts"
    if dev_scripts.exists():
        return dev_scripts

    # Fall back to package data
    try:
        # Python 3.12+
        return Path(str(resources.files("sop.scripts")))
    except (TypeError, ModuleNotFoundError):
        # Fallback for older Python or missing package data
        pass

    # Last resort: try to find adjacent to package
    pkg_scripts = Path(__file__).parent / "scripts"
    if pkg_scripts.exists():
        return pkg_scripts

    raise FileNotFoundError(
        "Could not locate sop scripts directory.\n"
        "  If installed: try reinstalling with 'pip install --force-reinstall terminal-zero-governance'\n"
        "  If in dev: ensure you're running from the repository root"
    )


def _run_script(script_name: str, args: List[str]) -> int:
    """Run a script from the scripts directory with given args."""
    try:
        scripts_dir = _get_scripts_dir()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    script_path = scripts_dir / script_name

    if not script_path.exists():
        print(
            f"Error: Script not found: {script_path}\n"
            f"  This may indicate a corrupted installation.\n"
            f"  Try: pip install --force-reinstall terminal-zero-governance",
            file=sys.stderr,
        )
        return 2

    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd)
    return result.returncode


def _add_repo_root_arg(parser: argparse.ArgumentParser, required: bool = True) -> None:
    """Add --repo-root argument to a parser."""
    parser.add_argument(
        "--repo-root",
        required=required,
        help="Repository root directory (default: current directory)",
        default="." if not required else None,
        nargs="?" if not required else None,
    )


def cmd_startup(args: argparse.Namespace) -> int:
    """Run startup interrogation."""
    cli_args = ["--repo-root", args.repo_root]

    # Pass through any additional args
    if args.output_md:
        cli_args.extend(["--output-md", args.output_md])
    if args.output_json:
        cli_args.extend(["--output-json", args.output_json])
    if args.no_interactive:
        cli_args.append("--no-interactive")
    if args.summary:
        cli_args.append("--summary")

    return _run_script("startup_codex_helper.py", cli_args)


def cmd_run(args: argparse.Namespace) -> int:
    """Run one loop cycle."""
    cli_args = ["--repo-root", args.repo_root]

    if args.skip_phase_end:
        cli_args.append("--skip-phase-end")
    if args.allow_hold:
        cli_args.extend(["--allow-hold", args.allow_hold])
    if args.context_dir:
        cli_args.extend(["--context-dir", args.context_dir])
    if getattr(args, "force", False):
        cli_args.append("--force")
    if getattr(args, "dry_run", False):
        cli_args.append("--dry-run")
    if getattr(args, "step_sla_seconds", None) is not None:
        cli_args.extend(["--step-sla-seconds", str(args.step_sla_seconds)])
    # Phase 5.3: forward lifecycle flags
    if getattr(args, "prune", False):
        cli_args.append("--prune")
    if getattr(args, "max_context_artifacts", 50) != 50:  # non-default
        cli_args.extend(["--max-context-artifacts", str(args.max_context_artifacts)])

    return _run_script("run_loop_cycle.py", cli_args)


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate closure readiness."""
    cli_args = ["--repo-root", args.repo_root]

    if args.context_dir:
        cli_args.extend(["--context-dir", args.context_dir])
    if args.output_json:
        cli_args.extend(["--output-json", args.output_json])
    if args.output_md:
        cli_args.extend(["--output-md", args.output_md])

    return _run_script("validate_loop_closure.py", cli_args)


def cmd_takeover(args: argparse.Namespace) -> int:
    """Print takeover entrypoint."""
    cli_args = ["--repo-root", args.repo_root]

    if args.workflow_status_json_out:
        cli_args.extend(["--workflow-status-json-out", args.workflow_status_json_out])
    if args.workflow_status_md_out:
        cli_args.extend(["--workflow-status-md-out", args.workflow_status_md_out])

    return _run_script("print_takeover_entrypoint.py", cli_args)


def cmd_supervise(args: argparse.Namespace) -> int:
    """Run loop supervision."""
    cli_args = ["--repo-root", args.repo_root]

    if args.max_cycles is not None:
        cli_args.extend(["--max-cycles", str(args.max_cycles)])
    if args.check_interval_seconds is not None:
        cli_args.extend(["--check-interval-seconds", str(args.check_interval_seconds)])
    if args.context_dir:
        cli_args.extend(["--context-dir", args.context_dir])

    return _run_script("supervise_loop.py", cli_args)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new governed repository structure."""
    from .init_cmd import do_init
    return do_init(args)


def cmd_version(args: argparse.Namespace) -> int:
    """Print version."""
    from . import __version__
    print(f"sop {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="sop",
        description="Terminal Zero Governance Control Plane - unified CLI for governance loop operations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sop startup --repo-root .           Initialize a round
  sop run --repo-root . --skip-phase-end   Run one loop cycle
  sop validate --repo-root .           Check closure readiness
  sop takeover --repo-root .           Print takeover guidance
  sop supervise --max-cycles 1         One-shot supervision
  sop init my-project                  Bootstrap new governed repo

For subcommand help: sop <command> --help
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # startup
    p_startup = subparsers.add_parser(
        "startup",
        help="Initialize a round and produce startup artifacts",
        description="Run startup interrogation to capture intent before worker loop.",
    )
    _add_repo_root_arg(p_startup)
    p_startup.add_argument("--output-md", help="Markdown output path")
    p_startup.add_argument("--output-json", help="JSON output path")
    p_startup.add_argument("--no-interactive", action="store_true", help="Disable prompts")
    p_startup.add_argument(
        "--summary",
        action="store_true",
        help="Print a thin readiness+phase status block and exit (no interrogation required)",
    )
    p_startup.set_defaults(func=cmd_startup)

    # run
    p_run = subparsers.add_parser(
        "run",
        help="Run one bounded loop cycle",
        description="Execute one loop cycle: refresh artifacts, run truth checks, emit summary.",
    )
    _add_repo_root_arg(p_run)
    p_run.add_argument("--skip-phase-end", action="store_true", help="Skip phase-end processing")
    p_run.add_argument("--allow-hold", help="Allow hold state (true/false)")
    p_run.add_argument("--context-dir", help="Context directory (default: docs/context)")
    p_run.add_argument("--force", action="store_true", default=False, help="Force run even if prior orchestrator state shows blocked=true.")
    p_run.add_argument("--dry-run", action="store_true", default=False, help="Evaluate gates without executing steps or writing artifacts.")
    p_run.add_argument("--step-sla-seconds", type=float, default=None, help="SLA threshold in seconds for step duration.")
    # Phase 5.3: artifact lifecycle flags
    p_run.add_argument("--prune", action="store_true", default=False, help="Archive superseded/orphaned artifacts from docs/context/.")
    p_run.add_argument("--max-context-artifacts", type=int, default=50, dest="max_context_artifacts", help="Warn when docs/context/ exceeds this many files (default: 50).")
    p_run.set_defaults(func=cmd_run)

    # validate
    p_validate = subparsers.add_parser(
        "validate",
        help="Validate closure readiness",
        description="Evaluate readiness / closure state. Exit 0=READY, 1=NOT_READY, 2=error.",
    )
    _add_repo_root_arg(p_validate)
    p_validate.add_argument("--context-dir", help="Context directory")
    p_validate.add_argument("--output-json", help="JSON output path")
    p_validate.add_argument("--output-md", help="Markdown output path")
    p_validate.set_defaults(func=cmd_validate)

    # takeover
    p_takeover = subparsers.add_parser(
        "takeover",
        help="Print takeover entrypoint",
        description="Print deterministic takeover guidance from latest loop artifacts.",
    )
    _add_repo_root_arg(p_takeover)
    p_takeover.add_argument("--workflow-status-json-out", help="Workflow status JSON output")
    p_takeover.add_argument("--workflow-status-md-out", help="Workflow status Markdown output")
    p_takeover.set_defaults(func=cmd_takeover)

    # supervise
    p_supervise = subparsers.add_parser(
        "supervise",
        help="Run loop supervision",
        description="Periodically supervise loop artifacts and emit status/alerts.",
    )
    _add_repo_root_arg(p_supervise, required=False)
    p_supervise.add_argument("--max-cycles", type=int, help="Maximum supervision cycles")
    p_supervise.add_argument("--check-interval-seconds", type=int, help="Seconds between checks")
    p_supervise.add_argument("--context-dir", help="Context directory")
    p_supervise.set_defaults(func=cmd_supervise)

    # init
    p_init = subparsers.add_parser(
        "init",
        help="Bootstrap a new governed repository",
        description="Create skeleton structure with templates for a new governed project.",
    )
    p_init.add_argument("target_dir", help="Target directory to create")
    p_init.add_argument("--minimal", action="store_true", help="Create minimal structure")
    p_init.set_defaults(func=cmd_init)

    # version
    p_version = subparsers.add_parser(
        "version",
        help="Print version",
        description="Print sop CLI version.",
    )
    p_version.set_defaults(func=cmd_version)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
