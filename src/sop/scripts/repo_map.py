"""Repo Map Compression — Phase 5C.1

Builds a deterministic, compressed map of a repository's Python source files:
    file -> symbols -> dependencies

Design constraints (D-188 / ADR-001 §4):
- Output is a plain data structure (dict); no executable code is emitted.
- Operates read-only on the file tree; never modifies any file.
- Fail-closed: any file that cannot be parsed is recorded as an error entry
  rather than silently skipped, so callers can decide how to handle it.
- The output contract is stable: consumers may depend on the keys defined in
  RepoMapEntry and RepoMap.

Output contract
---------------
RepoMapEntry (per file):
    path       : str   — repo-root-relative POSIX path
    symbols    : list[str] — top-level names (classes, functions, async functions)
    imports    : list[str] — imported module names (first segment only for packages)
    error      : str | None — parse error message if the file could not be analysed

RepoMap (top-level):
    repo_root  : str   — absolute path of the scanned root
    generated_at_utc : str — ISO-8601 UTC timestamp
    file_count : int   — number of files included in `files`
    files      : list[RepoMapEntry]
    errors     : list[str] — paths of files that could not be parsed
"""

from __future__ import annotations

import ast
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict


# ---------------------------------------------------------------------------
# Output contract types
# ---------------------------------------------------------------------------

class RepoMapEntry(TypedDict):
    """Per-file entry in the repo map."""
    path: str          # repo-root-relative POSIX path
    symbols: list      # top-level symbol names (str)
    imports: list      # imported module names, first segment (str)
    error: object      # str if parse failed, None otherwise


class RepoMap(TypedDict):
    """Top-level repo map output."""
    repo_root: str
    generated_at_utc: str
    file_count: int
    files: list        # list[RepoMapEntry]
    errors: list       # list[str] — rel paths of unparseable files


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DEFAULT_EXCLUDES = frozenset({
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".tox",
    "node_modules",
    "dist",
    "build",
    ".eggs",
})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_excluded(path: Path, excludes: frozenset[str]) -> bool:
    """Return True if any component of path matches an excluded directory name."""
    return any(part in excludes for part in path.parts)


def _extract_symbols(tree: ast.Module) -> list[str]:
    """Return top-level class and function names from a parsed AST."""
    symbols: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(node.name)
    return symbols


def _extract_imports(tree: ast.Module) -> list[str]:
    """Return the first-segment module names from all import statements."""
    seen: set[str] = set()
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in seen:
                    seen.add(root)
                    imports.append(root)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root not in seen:
                    seen.add(root)
                    imports.append(root)
    return imports


def _analyse_file(py_file: Path, repo_root: Path) -> RepoMapEntry:
    """Parse a single Python file and return its RepoMapEntry.

    Returns an entry with error set (and empty symbols/imports) if the file
    cannot be parsed, so the caller always gets a valid entry.
    """
    rel_path = py_file.relative_to(repo_root).as_posix()
    try:
        source = py_file.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(py_file))
        return RepoMapEntry(
            path=rel_path,
            symbols=_extract_symbols(tree),
            imports=_extract_imports(tree),
            error=None,
        )
    except SyntaxError as exc:
        return RepoMapEntry(
            path=rel_path,
            symbols=[],
            imports=[],
            error=f"SyntaxError: {exc}",
        )
    except Exception as exc:  # noqa: BLE001
        return RepoMapEntry(
            path=rel_path,
            symbols=[],
            imports=[],
            error=f"{type(exc).__name__}: {exc}",
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_repo_map(
    repo_root: Path,
    *,
    include_tests: bool = True,
    extra_excludes: frozenset[str] | None = None,
    path_filter: list[str] | None = None,
) -> RepoMap:
    """Scan *repo_root* for Python files and return a compressed repo map.

    Args:
        repo_root: Absolute path to the repository root.
        include_tests: When False, directories named ``tests`` are excluded.
        extra_excludes: Additional directory-name patterns to exclude on top of
            the built-in set.
        path_filter: When provided, only files whose repo-root-relative POSIX
            path starts with one of these prefixes are included.  Useful for
            focusing the map on a single package (e.g. ``["src/sop/scripts/"]``).

    Returns:
        A :class:`RepoMap` dict with the stable output contract.
    """
    repo_root = repo_root.resolve()
    excludes = _DEFAULT_EXCLUDES
    if not include_tests:
        excludes = excludes | {"tests", "test"}
    if extra_excludes:
        excludes = excludes | extra_excludes

    entries: list[RepoMapEntry] = []
    error_paths: list[str] = []

    for py_file in sorted(repo_root.rglob("*.py")):
        # Skip files inside excluded directories.
        try:
            rel = py_file.relative_to(repo_root)
        except ValueError:
            continue
        if _is_excluded(rel, excludes):
            continue

        # Apply optional prefix filter.
        if path_filter is not None:
            rel_posix = rel.as_posix()
            if not any(rel_posix.startswith(prefix) for prefix in path_filter):
                continue

        entry = _analyse_file(py_file, repo_root)
        entries.append(entry)
        if entry["error"] is not None:
            error_paths.append(entry["path"])

    return RepoMap(
        repo_root=str(repo_root),
        generated_at_utc=_utc_now_iso(),
        file_count=len(entries),
        files=entries,
        errors=error_paths,
    )


def format_repo_map_text(repo_map: RepoMap, *, max_symbols: int = 20) -> str:
    """Render a repo map as compact human-readable text for worker context injection.

    Each file is rendered as::

        src/sop/scripts/repo_map.py
          symbols: build_repo_map, format_repo_map_text
          imports: ast, argparse, json

    Files with errors are annotated.  This is the surface that workers consume
    to get compressed context instead of raw file contents.
    """
    lines: list[str] = []
    lines.append(f"# Repo map — {repo_map['file_count']} files — {repo_map['generated_at_utc']}")
    for entry in repo_map["files"]:
        lines.append(entry["path"])
        if entry["error"]:
            lines.append(f"  ERROR: {entry['error']}")
            continue
        symbols = entry["symbols"][:max_symbols]
        if symbols:
            lines.append(f"  symbols: {', '.join(symbols)}")
        imports = entry["imports"]
        if imports:
            lines.append(f"  imports: {', '.join(imports)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a compressed repo map for worker context shaping (Phase 5C.1)."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repository root to scan (default: three levels above this script).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON output to this path instead of stdout.",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Emit compact text format instead of JSON.",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Exclude test directories from the map.",
    )
    parser.add_argument(
        "--path-filter",
        nargs="+",
        metavar="PREFIX",
        help="Only include files whose path starts with one of these prefixes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_map = build_repo_map(
        repo_root=args.repo_root,
        include_tests=not args.no_tests,
        path_filter=args.path_filter,
    )

    if args.text:
        output_str = format_repo_map_text(repo_map)
    else:
        output_str = json.dumps(repo_map, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_str, encoding="utf-8")
        error_count = len(repo_map["errors"])
        print(f"REPO_MAP_FILES: {repo_map['file_count']}")
        print(f"REPO_MAP_ERRORS: {error_count}")
        print(f"REPO_MAP_OUTPUT: {args.output}")
    else:
        print(output_str)

    # Exit non-zero only if every file failed — partial success is still useful.
    if repo_map["file_count"] == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
