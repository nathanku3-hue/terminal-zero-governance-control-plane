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
import json
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


# ---------------------------------------------------------------------------
# H-NEW-1 Stage 1 — Preflight: spec check (importlib.util.find_spec)
# ---------------------------------------------------------------------------

_CRITICAL_MODULES = [
    "sop.scripts.phase_gate",
    "sop.scripts.worker_role",
    "sop.scripts.auditor_role",
    "sop.scripts.utils.skill_resolver",
    "sop.scripts.utils.atomic_io",
]


# Phase 4 Stream I — Retry constants
MAX_RETRIES = 1  # Phase 4: single retry on RETRYABLE failures only


def _should_retry(failure_artifact: dict) -> bool:
    """I: Return True only for RETRYABLE failures that have not yet been retried."""
    return (
        failure_artifact.get("recoverability") == "RETRYABLE"
        and failure_artifact.get("attempt_id") is None
    )


def _write_preflight_failure(
    failure_class: str,
    failed_component: str,
    reason: str,
    recoverability: str,
    repo_root: str = ".",
    attempt_id: "str | None" = "0",
) -> None:
    """Write run_failure_latest.json and emit FATAL envelope to stderr."""
    try:
        from sop._failure_reporter import write_run_failure, build_failure_payload
        import uuid as _uuid
        _run_id = str(_uuid.uuid4())
        payload = build_failure_payload(
            failure_class=failure_class,
            run_id=_run_id,
            entrypoint="sop run",
            execution_mode="cli",
            failed_component=failed_component,
            reason=reason,
            recoverability=recoverability,
            repo_root=repo_root,
            attempt_id=attempt_id,
        )
        _dest = Path(repo_root) / "docs" / "context"
        write_ok = write_run_failure(_dest, payload)
    except Exception:
        write_ok = False
    # Always emit FATAL envelope regardless of artifact write outcome
    print(
        f"FATAL failure_class={failure_class}"
        f" failed_component={failed_component}"
        f" recoverability={recoverability}"
        f" artifact_write_failed={str(not write_ok).lower()}",
        file=sys.stderr,
    )


def _run_preflight_spec_check(repo_root: str = ".") -> Optional[str]:
    """H-NEW-1 Stage 1: verify critical modules are findable via importlib.

    Returns None on success, or an error message string on failure.
    """
    import importlib.util
    missing = []
    for mod in _CRITICAL_MODULES:
        spec = importlib.util.find_spec(mod)
        if spec is None:
            missing.append(mod)
    if missing:
        return f"Critical modules not found: {', '.join(missing)}"
    return None


def _run_provenance_check(repo_root: str = ".") -> Optional[str]:
    """H-NEW-1 Stage 2: verify critical modules resolve from expected package root.

    Derives the expected root from importlib.util.find_spec("sop").submodule_search_locations
    at runtime — NOT hardcoded — so it works across editable, wheel, and source installs.

    Returns None on success, or an error message string on failure (ENTRYPOINT_DIVERGENCE).
    """
    import importlib.util

    sop_spec = importlib.util.find_spec("sop")
    if sop_spec is None or not sop_spec.submodule_search_locations:
        return "sop package not findable — cannot check provenance"

    pkg_root = Path(list(sop_spec.submodule_search_locations)[0])

    diverged: list[str] = []
    module_origins: dict[str, str] = {}
    for mod_name in _CRITICAL_MODULES:
        spec = importlib.util.find_spec(mod_name)
        if spec is None or spec.origin is None:
            continue
        mod_path = Path(spec.origin)
        module_origins[mod_name] = str(mod_path)
        try:
            mod_path.relative_to(pkg_root)
        except ValueError:
            diverged.append(f"{mod_name}: {mod_path}")

    if diverged:
        diverged_list = "; ".join(diverged)
        return (
            f"ENTRYPOINT_DIVERGENCE: compatibility-path divergence detected. "
            f"use sop run instead of python scripts/run_loop_cycle.py. "
            f"Conflicting paths: {diverged_list} (expected under {pkg_root})"
        )
    return None


def _get_module_origins() -> dict[str, str]:
    """Return actual __file__ paths of all resolved critical modules."""
    import importlib.util
    origins: dict[str, str] = {}
    for mod_name in _CRITICAL_MODULES:
        spec = importlib.util.find_spec(mod_name)
        if spec is not None and spec.origin is not None:
            origins[mod_name] = str(spec.origin)
    return origins


def _run_script(script_name: str, args: List[str], repo_root: str = ".") -> int:
    """Run a script from the scripts directory with given args."""
    # H-NEW-1 Stage 1: preflight spec check before any script execution
    preflight_error = _run_preflight_spec_check(repo_root=repo_root)
    if preflight_error is not None:
        _write_preflight_failure(
            failure_class="INSTALL_ERROR",
            failed_component="preflight_spec_check",
            reason=preflight_error,
            recoverability="REQUIRES_FIX",
            repo_root=repo_root,
        )
        sys.exit(1)

    # H-NEW-1 Stage 2: provenance check — module origins must resolve under package
    provenance_error = _run_provenance_check(repo_root=repo_root)
    if provenance_error is not None:
        _write_preflight_failure(
            failure_class="ENTRYPOINT_DIVERGENCE",
            failed_component="provenance_check",
            reason=provenance_error,
            recoverability="REQUIRES_FIX",
            repo_root=repo_root,
        )
        sys.exit(1)

    try:
        scripts_dir = _get_scripts_dir()
    except FileNotFoundError as e:
        _write_preflight_failure(
            failure_class="INSTALL_ERROR",
            failed_component="scripts_dir",
            reason=str(e),
            recoverability="REQUIRES_FIX",
            repo_root=repo_root,
        )
        sys.exit(2)

    script_path = scripts_dir / script_name

    if not script_path.exists():
        _write_preflight_failure(
            failure_class="INSTALL_ERROR",
            failed_component=script_name,
            reason=(
                f"Script not found: {script_path}. "
                "This may indicate a corrupted installation. "
                "Try: pip install --force-reinstall terminal-zero-governance"
            ),
            recoverability="REQUIRES_FIX",
            repo_root=repo_root,
        )
        sys.exit(2)

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


def _escape_prometheus_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _load_audit_entries_for_metrics(audit_log_path: Path) -> list[dict]:
    if not audit_log_path.exists():
        return []
    entries: list[dict] = []
    with audit_log_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                entries.append(parsed)
    return entries


def _render_prometheus_metrics(entries: list[dict]) -> str:
    policy_counts: dict[tuple[str, str], int] = {}
    gate_duration_totals: dict[str, float] = {}
    failure_count_total = 0

    for entry in entries:
        decision = str(entry.get("decision", "")).strip() or "UNKNOWN"
        actor = str(entry.get("actor", "")).strip() or "UNKNOWN"
        policy_key = (decision, actor)
        policy_counts[policy_key] = policy_counts.get(policy_key, 0) + 1

        if decision in {"FAIL", "ERROR"}:
            failure_count_total += 1

        gate = str(entry.get("gate", "")).strip()
        duration = entry.get("duration_seconds")
        if gate and isinstance(duration, (int, float)):
            gate_duration_totals[gate] = gate_duration_totals.get(gate, 0.0) + float(duration)

    lines: list[str] = [
        "# HELP policy_decisions_total Total audit policy decisions by decision and actor.",
        "# TYPE policy_decisions_total counter",
    ]
    for (decision, actor), count in sorted(policy_counts.items()):
        lines.append(
            "policy_decisions_total{decision=\""
            + _escape_prometheus_label(decision)
            + "\",actor=\""
            + _escape_prometheus_label(actor)
            + "\"} "
            + str(count)
        )

    lines.extend(
        [
            "# HELP gate_evaluation_duration_seconds Aggregate gate duration in seconds by gate.",
            "# TYPE gate_evaluation_duration_seconds gauge",
        ]
    )
    for gate, total in sorted(gate_duration_totals.items()):
        lines.append(
            "gate_evaluation_duration_seconds{gate=\""
            + _escape_prometheus_label(gate)
            + "\"} "
            + str(total)
        )

    lines.extend(
        [
            "# HELP failure_count_total Total count of FAIL/ERROR audit decisions.",
            "# TYPE failure_count_total counter",
            f"failure_count_total {failure_count_total}",
        ]
    )

    # Compatibility alias window (C5): deprecated aliases mirror canonical values.
    lines.extend(
        [
            "# HELP policy_decision_total DEPRECATED alias for policy_decisions_total.",
            "# TYPE policy_decision_total counter",
        ]
    )
    for (decision, actor), count in sorted(policy_counts.items()):
        lines.append(
            "policy_decision_total{decision=\""
            + _escape_prometheus_label(decision)
            + "\",actor=\""
            + _escape_prometheus_label(actor)
            + "\"} "
            + str(count)
        )

    lines.extend(
        [
            "# HELP gate_duration_seconds_total DEPRECATED alias for gate_evaluation_duration_seconds.",
            "# TYPE gate_duration_seconds_total gauge",
        ]
    )
    for gate, total in sorted(gate_duration_totals.items()):
        lines.append(
            "gate_duration_seconds_total{gate=\""
            + _escape_prometheus_label(gate)
            + "\"} "
            + str(total)
        )

    lines.extend(
        [
            "# HELP failures_total DEPRECATED alias for failure_count_total.",
            "# TYPE failures_total counter",
            f"failures_total {failure_count_total}",
        ]
    )

    return "\n".join(lines) + "\n"


def cmd_metrics(args: argparse.Namespace) -> int:
    """Export observability metrics to stdout."""
    repo_root = Path(args.repo_root)
    audit_log_path = repo_root / "docs" / "context" / "audit_log.ndjson"

    try:
        entries = _load_audit_entries_for_metrics(audit_log_path)
    except (OSError, PermissionError) as exc:
        print(f"ERROR: unable to read audit log: {exc}", file=sys.stderr)
        return 1

    output = _render_prometheus_metrics(entries)
    sys.stdout.write(output)
    return 0


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

    return _run_script("startup_codex_helper.py", cli_args, repo_root=args.repo_root)


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
    # Phase 2 Policy Engine flags
    if not getattr(args, "policy_shadow_mode", True):  # non-default (shadow=False = enforce)
        cli_args.extend(["--policy-shadow-mode", "false"])
    if getattr(args, "policy_rule_file", None) is not None:
        cli_args.extend(["--policy-rule-file", str(args.policy_rule_file)])
    if getattr(args, "plugin_dir", None) is not None:
        cli_args.extend(["--plugin-dir", str(args.plugin_dir)])

    # Phase 4 Stream I — single retry on RETRYABLE failures only
    repo_root_str = str(args.repo_root)
    exit_code = _run_script("run_loop_cycle.py", cli_args, repo_root=repo_root_str)
    if exit_code != 0:
        try:
            import json as _json
            _artifact = Path(repo_root_str) / "docs" / "context" / "run_failure_latest.json"
            if _artifact.exists():
                _failure = _json.loads(_artifact.read_text(encoding="utf-8"))
                if _should_retry(_failure):
                    exit_code = _run_script("run_loop_cycle.py", cli_args, repo_root=repo_root_str)
        except Exception:
            pass
    return exit_code


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate closure readiness."""
    cli_args = ["--repo-root", args.repo_root]

    if args.context_dir:
        cli_args.extend(["--context-dir", args.context_dir])
    if args.output_json:
        cli_args.extend(["--output-json", args.output_json])
    if args.output_md:
        cli_args.extend(["--output-md", args.output_md])

    return _run_script("validate_loop_closure.py", cli_args, repo_root=args.repo_root)


def cmd_takeover(args: argparse.Namespace) -> int:
    """Print takeover entrypoint."""
    cli_args = ["--repo-root", args.repo_root]

    if args.workflow_status_json_out:
        cli_args.extend(["--workflow-status-json-out", args.workflow_status_json_out])
    if args.workflow_status_md_out:
        cli_args.extend(["--workflow-status-md-out", args.workflow_status_md_out])

    return _run_script("print_takeover_entrypoint.py", cli_args, repo_root=args.repo_root)


def cmd_supervise(args: argparse.Namespace) -> int:
    """Run loop supervision."""
    cli_args = ["--repo-root", args.repo_root]

    if args.max_cycles is not None:
        cli_args.extend(["--max-cycles", str(args.max_cycles)])
    if args.check_interval_seconds is not None:
        cli_args.extend(["--check-interval-seconds", str(args.check_interval_seconds)])
    if args.context_dir:
        cli_args.extend(["--context-dir", args.context_dir])

    return _run_script("supervise_loop.py", cli_args, repo_root=args.repo_root)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new governed repository structure."""
    from .init_cmd import do_init
    return do_init(args)


def cmd_audit(args: argparse.Namespace) -> int:
    """Query the governance audit log."""
    import json as _json
    from pathlib import Path as _Path
    try:
        from sop._audit_log import query_audit_log
    except ModuleNotFoundError:
        print("ERROR: sop._audit_log not available", file=__import__("sys").stderr)
        return 1
    repo_root = _Path(getattr(args, "repo_root", "."))
    context_dir = repo_root / "docs" / "context"
    tail = getattr(args, "tail", None)
    filter_val = getattr(args, "filter", None)
    # Accept both "outcome=BLOCK" and bare "BLOCK" formats
    filter_decision: str | None = None
    if filter_val:
        if "=" in filter_val:
            filter_decision = filter_val.split("=", 1)[1].strip()
        else:
            filter_decision = filter_val.strip()
    entries = query_audit_log(context_dir, tail=tail, filter_outcome=filter_decision)
    if not entries:
        print("No audit log entries found.")
        return 0
    for entry in entries:
        print(_json.dumps(entry, separators=(",", ": ")))
    return 0


def cmd_policy_validate(args: argparse.Namespace) -> int:
    """Validate a policy rule file schema."""
    try:
        from sop._policy_engine import load_policy_rules, PolicyLoadError
    except ModuleNotFoundError:
        print("ERROR: sop._policy_engine not available", file=__import__("sys").stderr)
        return 1
    rule_file = args.rule_file
    try:
        rules = load_policy_rules(rule_file)
    except PolicyLoadError as exc:
        print(f"INVALID: {exc}", file=__import__("sys").stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1
    print(f"OK: {len(rules)} rule(s) valid in {rule_file}")
    return 0


def cmd_policy_rbac_validate(args: argparse.Namespace) -> int:
    """Validate an RBAC role config file schema."""
    try:
        from sop._policy_engine import load_role_config, PolicyLoadError
    except ModuleNotFoundError:
        print("ERROR: sop._policy_engine not available", file=__import__("sys").stderr)
        return 1
    role_file = args.role_file
    try:
        roles = load_role_config(role_file)
    except PolicyLoadError as exc:
        print(f"INVALID: {exc}", file=__import__("sys").stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1
    print(f"OK: {len(roles)} role(s) valid in {role_file}")
    return 0


def cmd_healthcheck(args: argparse.Namespace) -> int:
    """Run preflight spec check and exit 0 on success, 1 on failure.

    Takes no required arguments — safe to call as CMD inside a container
    where the package is installed system-wide and CWD is /workspace.
    """
    error = _run_preflight_spec_check(repo_root=".")
    if error is not None:
        print(
            f"FATAL failure_class=INSTALL_ERROR"
            f" failed_component=preflight_spec_check"
            f" recoverability=REQUIRES_FIX"
            f" artifact_write_failed=true",
            file=sys.stderr,
        )
        print(f"healthcheck FAILED: {error}", file=sys.stderr)
        return 1
    print("healthcheck OK: all critical modules found")
    return 0


def cmd_ops_nightly_audit(args: argparse.Namespace) -> int:
    """Run nightly compliance audit."""
    cli_args = ["--repo-root", args.repo_root, "--format", args.format]
    return _run_script("nightly_audit.py", cli_args, repo_root=args.repo_root)


def cmd_version(args: argparse.Namespace) -> int:
    """Print version."""
    from . import __version__
    print(f"sop {__version__}")
    return 0


def cmd_phase8_ga_readiness(args: argparse.Namespace) -> int:
    """Generate Phase 8 GA readiness artifacts."""
    cli_args = [
        "--repo-root",
        args.repo_root,
        "--burnin-report",
        args.burnin_report,
        "--slo-baseline",
        args.slo_baseline,
        "--ga-signoff",
        args.ga_signoff,
    ]
    return _run_script("phase8_ga_readiness.py", cli_args, repo_root=args.repo_root)


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
    # Phase 2 Policy Engine
    p_run.add_argument("--policy-shadow-mode", type=lambda x: x.lower() not in ("false", "0", "no"), default=True, dest="policy_shadow_mode", help="Policy engine shadow mode (default: true). When true, BLOCK decisions are logged but do not block execution.")
    p_run.add_argument("--policy-rule-file", default=None, dest="policy_rule_file", help="Path to a JSON policy rule file. If None, no policy rules are loaded.")
    p_run.add_argument("--plugin-dir", default=None, dest="plugin_dir", help="Plugin directory for sop run only (default: <repo_root>/.sop/plugins/).")
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

    # audit
    p_audit = subparsers.add_parser(
        "audit",
        help="Query the governance audit log",
        description="Print structured audit log entries from docs/context/audit_log.ndjson.",
    )
    _add_repo_root_arg(p_audit, required=False)
    p_audit.add_argument("--tail", type=int, default=None, help="Show last N entries (default: all)")
    p_audit.add_argument("--filter", dest="filter", default=None, metavar="DECISION",
        help="Filter by decision value, e.g. BLOCK or outcome=BLOCK")
    p_audit.set_defaults(func=cmd_audit)

    # metrics
    p_metrics = subparsers.add_parser(
        "metrics",
        help="Export observability metrics",
        description="Export Prometheus text metrics derived from docs/context/audit_log.ndjson.",
    )
    _add_repo_root_arg(p_metrics)
    p_metrics.add_argument(
        "--format",
        required=True,
        choices=["prometheus"],
        help="Output format (v1 supports: prometheus)",
    )
    p_metrics.set_defaults(func=cmd_metrics)

    # ops
    p_ops = subparsers.add_parser(
        "ops",
        help="Operational compliance commands",
        description="Operations commands for compliance and audit workflows.",
    )
    p_ops_sub = p_ops.add_subparsers(dest="ops_command", help="Ops subcommands")

    p_ops_nightly = p_ops_sub.add_parser(
        "nightly-audit",
        help="Run nightly compliance audit",
        description="Evaluate pinned compliance controls and produce compliance snapshot artifacts.",
    )
    _add_repo_root_arg(p_ops_nightly)
    p_ops_nightly.add_argument(
        "--format",
        required=True,
        choices=["json"],
        help="Output format (v1 supports: json)",
    )
    p_ops_nightly.set_defaults(func=cmd_ops_nightly_audit)
    p_ops.set_defaults(func=lambda a: (p_ops.print_help(), 0)[1])

    # policy
    p_policy = subparsers.add_parser(
        "policy",
        help="Policy engine commands",
        description="Commands for the Terminal Zero policy engine.",
    )
    p_policy_sub = p_policy.add_subparsers(dest="policy_command", help="Policy subcommands")
    # policy validate
    p_policy_validate = p_policy_sub.add_parser(
        "validate",
        help="Validate a policy rule file",
        description="Validate the schema of a JSON policy rule file. Exit 0=valid, 1=invalid.",
    )
    p_policy_validate.add_argument(
        "--rule-file",
        required=True,
        dest="rule_file",
        help="Path to the JSON policy rule file to validate.",
    )
    p_policy_validate.set_defaults(func=cmd_policy_validate)

    # policy rbac validate
    p_policy_rbac = p_policy_sub.add_parser(
        "rbac",
        help="RBAC role configuration commands",
        description="Commands for RBAC role-file validation.",
    )
    p_policy_rbac_sub = p_policy_rbac.add_subparsers(dest="policy_rbac_command", help="RBAC subcommands")
    p_policy_rbac_validate = p_policy_rbac_sub.add_parser(
        "validate",
        help="Validate an RBAC role file",
        description="Validate the schema of a JSON RBAC role file. Exit 0=valid, 1=invalid.",
    )
    p_policy_rbac_validate.add_argument(
        "--role-file",
        required=True,
        dest="role_file",
        help="Path to the JSON RBAC role file to validate.",
    )
    p_policy_rbac_validate.set_defaults(func=cmd_policy_rbac_validate)
    # Phase 3: sop policy evaluate — deferred
    p_policy.set_defaults(func=lambda a: (p_policy.print_help(), 0)[1])

    # healthcheck
    p_healthcheck = subparsers.add_parser(
        "healthcheck",
        help="Verify installation health (preflight spec check)",
        description=(
            "Run a preflight check that all critical modules are importable. "
            "Takes no required arguments. Exits 0 on success, 1 on failure. "
            "Used as the Docker HEALTHCHECK CMD and container smoke-test gate."
        ),
    )
    p_healthcheck.set_defaults(func=cmd_healthcheck)

    # phase8-ga-readiness
    p_phase8 = subparsers.add_parser(
        "phase8-ga-readiness",
        help="Generate Phase 8 burn-in artifacts",
        description="Run fixed 5x6 Phase 8 matrix and write burn-in/slo/signoff artifacts.",
    )
    _add_repo_root_arg(p_phase8)
    p_phase8.add_argument("--burnin-report", default="docs/context/burnin_report_latest.json")
    p_phase8.add_argument("--slo-baseline", default="docs/context/slo_baseline_latest.json")
    p_phase8.add_argument("--ga-signoff", default="docs/context/ga_signoff_packet_latest.md")
    p_phase8.set_defaults(func=cmd_phase8_ga_readiness)

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
