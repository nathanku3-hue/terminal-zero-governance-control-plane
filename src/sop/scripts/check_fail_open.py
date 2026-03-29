#!/usr/bin/env python3
"""scripts/check_fail_open.py

Ph5-G — Bare-except/pass scanner (AST-based).

Scans src/ and scripts/ for bare ``except: pass`` patterns that swallow
errors silently (fail-open anti-pattern).  Exits 0 when no findings,
exits 1 when one or more findings are reported.

Usage:
    python scripts/check_fail_open.py [--root <repo-root>]
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


_SCAN_DIRS = ["src", "scripts"]


def _is_bare_except_pass(handler: ast.ExceptHandler) -> bool:
    """Return True if the handler is a bare ``except: pass`` (or bare except with only pass)."""
    # Bare except has type=None
    if handler.type is not None:
        return False
    # Body must be exactly [pass] or contain only Pass nodes
    return all(isinstance(stmt, ast.Pass) for stmt in handler.body)


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, message) findings for a single Python file."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                if _is_bare_except_pass(handler):
                    findings.append(
                        (handler.lineno, "bare except: pass (fail-open anti-pattern)")
                    )
    return findings


def scan_dirs(root: Path, dirs: list[str]) -> dict[str, list[tuple[int, str]]]:
    """Scan all .py files under each directory in dirs. Returns {rel_path: findings}."""
    results: dict[str, list[tuple[int, str]]] = {}
    for dir_name in dirs:
        scan_root = root / dir_name
        if not scan_root.is_dir():
            continue
        for py_file in sorted(scan_root.rglob("*.py")):
            findings = scan_file(py_file)
            if findings:
                rel = str(py_file.relative_to(root))
                results[rel] = findings
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan src/ and scripts/ for bare except: pass (fail-open anti-pattern)."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root directory (default: auto-detected from script location).",
    )
    args = parser.parse_args(argv)

    if args.root is not None:
        root = Path(args.root).resolve()
    else:
        # Script lives at <repo>/scripts/ or <repo>/src/sop/scripts/
        _here = Path(__file__).resolve()
        root = None
        for ancestor in [_here.parent, _here.parent.parent,
                         _here.parent.parent.parent,
                         _here.parent.parent.parent.parent]:
            if (ancestor / "src").is_dir() or (ancestor / "scripts").is_dir():
                root = ancestor
                break
        if root is None:
            print("ERROR: could not locate repo root. Pass --root explicitly.", file=sys.stderr)
            return 1

    results = scan_dirs(root, _SCAN_DIRS)

    if not results:
        total = sum(
            1
            for d in _SCAN_DIRS
            for _ in (root / d).rglob("*.py")
            if (root / d).is_dir()
        )
        print(
            f"CHECK_FAIL_OPEN: PASS — scanned {total} file(s) in "
            + ", ".join(_SCAN_DIRS)
            + ", no bare except:pass findings."
        )
        return 0

    total_findings = sum(len(v) for v in results.values())
    print(
        f"CHECK_FAIL_OPEN: FAIL — {total_findings} finding(s) in {len(results)} file(s):",
        file=sys.stderr,
    )
    for rel_path, findings in sorted(results.items()):
        for lineno, msg in findings:
            print(f"  {rel_path}:{lineno}: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
