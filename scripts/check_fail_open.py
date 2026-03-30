#!/usr/bin/env python3
"""scripts/check_fail_open.py

Ph5-G — Fail-open pattern scanner (AST-based) with tiered findings.

Tiers:
  BLOCKER   bare ``except: pass`` — swallows all errors silently
  WARN      typed broad-catch with pass body (e.g. ``except Exception: pass``)
             or bare except with non-pass body that may swallow errors
  ALLOWLISTED  entries in fail_open_allowlist.json exempt from BLOCKER

Exits:
  0   PASS — no BLOCKER findings (WARN/ALLOWLISTED do not block)
  1   FAIL — one or more BLOCKER findings

Machine-readable output (one JSON object per line to stdout):
  {"tier": "BLOCKER"|"WARN"|"ALLOWLISTED", "file": "...", "line": N, "message": "..."}

Usage:
    python scripts/check_fail_open.py [--root <repo-root>]
    python scripts/check_fail_open.py [--root <repo-root>] [--allowlist <path>]
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import NamedTuple


_SCAN_DIRS = ["src", "scripts"]
_DEFAULT_ALLOWLIST = "scripts/fail_open_allowlist.json"

# Broad exception types that are treated as WARN-tier even when typed
_BROAD_EXCEPTION_NAMES = frozenset(["Exception", "BaseException"])


class Finding(NamedTuple):
    tier: str          # BLOCKER | WARN | ALLOWLISTED
    file: str
    line: int
    message: str


def _is_bare_except_pass(handler: ast.ExceptHandler) -> bool:
    """True if handler is bare ``except: pass`` (type=None, body=[Pass])."""
    if handler.type is not None:
        return False
    return all(isinstance(stmt, ast.Pass) for stmt in handler.body)


def _is_bare_except_nopass(handler: ast.ExceptHandler) -> bool:
    """True if handler is bare ``except:`` with non-pass body (potential swallow)."""
    if handler.type is not None:
        return False
    return not all(isinstance(stmt, ast.Pass) for stmt in handler.body)


def _is_broad_except_pass(handler: ast.ExceptHandler) -> bool:
    """True if handler catches Exception/BaseException with pass-only body."""
    if handler.type is None:
        return False
    # Get the exception type name
    if isinstance(handler.type, ast.Name):
        name = handler.type.id
    elif isinstance(handler.type, ast.Attribute):
        name = handler.type.attr
    else:
        return False
    if name not in _BROAD_EXCEPTION_NAMES:
        return False
    return all(isinstance(stmt, ast.Pass) for stmt in handler.body)


def _load_allowlist(root: Path, allowlist_path: str | None) -> set[tuple[str, int]]:
    """Load allowlist entries as (rel_file, lineno) set."""
    if allowlist_path is None:
        candidate = root / _DEFAULT_ALLOWLIST
    else:
        candidate = Path(allowlist_path)
        if not candidate.is_absolute():
            candidate = root / candidate
    if not candidate.exists():
        return set()
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
        entries = set()
        for item in data.get("allowlist", []):
            f = item.get("file", "")
            ln = item.get("line", 0)
            if f and ln:
                entries.add((f, int(ln)))
        return entries
    except Exception:
        return set()


def scan_file(path: Path, root: Path) -> list[tuple[int, str, str]]:
    """Return list of (lineno, tier_candidate, message) for a single file."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                if _is_bare_except_pass(handler):
                    findings.append((
                        handler.lineno,
                        "BLOCKER",
                        "bare except: pass (fail-open — swallows all errors silently)",
                    ))
                elif _is_bare_except_nopass(handler):
                    findings.append((
                        handler.lineno,
                        "WARN",
                        "bare except: with non-pass body (potential error swallow)",
                    ))
                elif _is_broad_except_pass(handler):
                    findings.append((
                        handler.lineno,
                        "WARN",
                        "broad except pass (Exception/BaseException swallowed silently)",
                    ))
    return findings


def scan_dirs(
    root: Path,
    dirs: list[str],
    allowlist: set[tuple[str, int]],
) -> list[Finding]:
    """Scan all .py files under each directory. Returns list of Finding."""
    all_findings: list[Finding] = []
    for dir_name in dirs:
        scan_root = root / dir_name
        if not scan_root.is_dir():
            continue
        for py_file in sorted(scan_root.rglob("*.py")):
            raw = scan_file(py_file, root)
            if not raw:
                continue
            rel = str(py_file.relative_to(root)).replace("\\", "/")
            for lineno, tier_candidate, msg in raw:
                key = (rel, lineno)
                if key in allowlist:
                    tier = "ALLOWLISTED"
                else:
                    tier = tier_candidate
                all_findings.append(Finding(
                    tier=tier,
                    file=rel,
                    line=lineno,
                    message=msg,
                ))
    return all_findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan src/ and scripts/ for fail-open patterns (tiered: BLOCKER/WARN/ALLOWLISTED)."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root directory (default: auto-detected from script location).",
    )
    parser.add_argument(
        "--allowlist",
        default=None,
        help=f"Path to allowlist JSON (default: {_DEFAULT_ALLOWLIST} relative to root).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON lines to stdout (always enabled for machine consumers).",
    )
    args = parser.parse_args(argv)

    if args.root is not None:
        root = Path(args.root).resolve()
    else:
        _here = Path(__file__).resolve()
        root = None
        for ancestor in [
            _here.parent,
            _here.parent.parent,
            _here.parent.parent.parent,
            _here.parent.parent.parent.parent,
        ]:
            if (ancestor / "src").is_dir() or (ancestor / "scripts").is_dir():
                root = ancestor
                break
        if root is None:
            print("ERROR: could not locate repo root. Pass --root explicitly.", file=sys.stderr)
            return 1

    allowlist = _load_allowlist(root, args.allowlist)
    findings = scan_dirs(root, _SCAN_DIRS, allowlist)

    blockers = [f for f in findings if f.tier == "BLOCKER"]
    warns = [f for f in findings if f.tier == "WARN"]
    allowlisted = [f for f in findings if f.tier == "ALLOWLISTED"]

    # Always emit machine-readable JSON lines for all findings
    for f in findings:
        print(json.dumps({"tier": f.tier, "file": f.file, "line": f.line, "message": f.message}))

    if not findings:
        total = sum(
            1
            for d in _SCAN_DIRS
            for _ in ((root / d).rglob("*.py") if (root / d).is_dir() else [])
        )
        print(
            f"CHECK_FAIL_OPEN: PASS — scanned {total} file(s) in "
            + ", ".join(_SCAN_DIRS)
            + ", no findings."
        )
        return 0

    summary_parts = []
    if blockers:
        summary_parts.append(f"{len(blockers)} BLOCKER")
    if warns:
        summary_parts.append(f"{len(warns)} WARN")
    if allowlisted:
        summary_parts.append(f"{len(allowlisted)} ALLOWLISTED")

    if blockers:
        print(
            f"CHECK_FAIL_OPEN: FAIL — " + ", ".join(summary_parts) + " finding(s)",
            file=sys.stderr,
        )
        return 1
    else:
        print(
            f"CHECK_FAIL_OPEN: PASS — " + ", ".join(summary_parts) + " finding(s) (no BLOCKER)",
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
