"""sop._client

Phase 3 — Formal API Surface & Integration SDK.

Public API::

    from sop import GovernanceClient

    client = GovernanceClient(repo_root=".")
    summary = client.run(skip_phase_end=True)   # -> dict with final_result key
    status  = client.status()                   # -> dict | None
    entries = client.audit(tail=20)             # -> list[dict]
    client.policy_validate("rules.json")        # -> raises RuntimeError if Phase 2 absent

run() delegation:
    Builds an argv list from kwargs and calls parse_args(argv) — robust to future
    parse_args() additions. Never hand-constructs a Namespace.

status() contract:
    Reads docs/context/loop_cycle_summary_latest.json if it exists, returns the
    parsed dict. Returns None if the file is absent. Never runs a cycle.

audit() dest_dir derivation:
    dest_dir = Path(self._repo_root) / "docs" / "context"

policy_validate() Phase 2 dependency:
    Uses best-effort import fallback — raises RuntimeError with a clear message
    if Phase 2 (_policy_engine) is not installed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Phase 2 dependency: best-effort import
# ---------------------------------------------------------------------------
try:
    from sop._policy_engine import load_policy_rules  # type: ignore[assignment]
    _POLICY_ENGINE_AVAILABLE = True
except ModuleNotFoundError:
    _POLICY_ENGINE_AVAILABLE = False

    def load_policy_rules(rule_file: Any) -> list:  # type: ignore[misc]
        raise RuntimeError(
            "Policy engine not available — install Phase 2 before calling policy_validate(). "
            "pip install --upgrade terminal-zero-governance"
        )

# ---------------------------------------------------------------------------
# Audit log dependency: best-effort import
# ---------------------------------------------------------------------------
try:
    from sop._audit_log import query_audit_log as _query_audit_log  # type: ignore[assignment]
    _AUDIT_LOG_AVAILABLE = True
except ModuleNotFoundError:
    _AUDIT_LOG_AVAILABLE = False

    def _query_audit_log(dest_dir: Any, tail: Any = None, filter_outcome: Any = None) -> list:  # type: ignore[misc]
        return []


__all__ = ["GovernanceClient"]


class GovernanceClient:
    """High-level Python SDK for the Terminal Zero governance control plane.

    Parameters
    ----------
    repo_root:
        Path to the governed repository root. Accepts str or Path.
        Defaults to the current working directory.

    Example
    -------
    ::

        from sop import GovernanceClient

        client = GovernanceClient(repo_root=".")
        result = client.run(skip_phase_end=True)
        print(result["final_result"])  # PASS | HOLD | FAIL | ERROR
    """

    def __init__(self, repo_root: str | Path = ".") -> None:
        self._repo_root = Path(repo_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        skip_phase_end: bool = True,
        allow_hold: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run one bounded loop cycle and return the summary payload dict.

        Builds an argv list from the supplied kwargs and delegates to
        ``parse_args(argv)`` — never hand-constructs an argparse.Namespace.
        This ensures robustness against future parse_args() additions.

        Parameters
        ----------
        skip_phase_end:
            Pass ``--skip-phase-end`` to the loop cycle (default: True).
        allow_hold:
            Pass ``--allow-hold false`` when False (default: True).
        **kwargs:
            Currently unused; reserved for future CLI flag forwarding.

        Returns
        -------
        dict
            The full loop cycle summary payload. Always contains
            ``final_result`` (PASS | HOLD | FAIL | ERROR) and
            ``final_exit_code``.
        """
        from sop.scripts.run_loop_cycle import parse_args, run_cycle  # type: ignore[import]

        argv: list[str] = ["--repo-root", str(self._repo_root)]
        if skip_phase_end:
            argv.append("--skip-phase-end")
        if not allow_hold:
            argv.extend(["--allow-hold", "false"])

        args = parse_args(argv)
        _exit_code, payload, _markdown = run_cycle(args)
        return payload

    def status(self) -> dict[str, Any] | None:
        """Return the most recent loop cycle summary dict, or None if absent.

        Reads ``docs/context/loop_cycle_summary_latest.json`` from the repo
        root. Returns None if the file does not exist. Never runs a cycle.

        Returns
        -------
        dict | None
            Parsed JSON dict when the file exists, otherwise None.
        """
        summary_path = self._repo_root / "docs" / "context" / "loop_cycle_summary_latest.json"
        if not summary_path.exists():
            return None
        try:
            return json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def audit(
        self,
        tail: int | None = None,
        filter_outcome: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return audit log entries from this repo's governance audit log.

        Parameters
        ----------
        tail:
            If set, return only the last *tail* entries.
        filter_outcome:
            If set, filter entries by decision value (case-insensitive).
            E.g. ``"BLOCK"`` returns only BLOCK decisions.

        Returns
        -------
        list[dict]
            List of audit log entry dicts. Empty list if the log is absent
            or the audit log module is unavailable.
        """
        dest_dir = self._repo_root / "docs" / "context"
        return _query_audit_log(dest_dir, tail=tail, filter_outcome=filter_outcome)

    def policy_validate(self, rule_file: str | Path) -> list[dict[str, Any]]:
        """Validate a policy rule file and return the loaded rules.

        Requires Phase 2 (_policy_engine) to be installed. Raises
        RuntimeError with a clear message if Phase 2 is absent.

        Parameters
        ----------
        rule_file:
            Path to a JSON policy rule file.

        Returns
        -------
        list[dict]
            Validated list of rule dicts.

        Raises
        ------
        RuntimeError
            When the policy engine is not available.
        sop._policy_engine.PolicyLoadError
            When the rule file is invalid.
        """
        return load_policy_rules(rule_file)  # type: ignore[return-value]
