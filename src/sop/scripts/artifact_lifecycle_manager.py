"""Phase 5.3 -- ArtifactLifecycleManager: artifact pruning and lifecycle.

Classifies all files in docs/context/ by lifecycle state and optionally
moves superseded artifacts to docs/context/archive/.

Lifecycle states:
  active      -- currently written/read by the system (in _MEMORY_TIER_FAMILIES)
  superseded  -- a newer version replaces it; still on disk
  orphaned    -- not referenced by any family in _MEMORY_TIER_FAMILIES
  fixture     -- reserved for future phases (vacuous in Phase 5)

D-183: scripts/artifact_lifecycle_manager.py must be byte-identical to this file.
"""
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from sop.scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES
except ModuleNotFoundError:
    try:
        from scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from utils.memory_tiers import _MEMORY_TIER_FAMILIES  # type: ignore[no-redef]


@dataclass
class LifecycleScanResult:
    """Result of ArtifactLifecycleManager.scan()."""
    active: list[str] = field(default_factory=list)
    superseded: list[str] = field(default_factory=list)
    orphaned: list[str] = field(default_factory=list)
    fixture: list[str] = field(default_factory=list)
    unclassified: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "active": list(self.active),
            "superseded": list(self.superseded),
            "orphaned": list(self.orphaned),
            "fixture": list(self.fixture),
            "unclassified": list(self.unclassified),
        }


@dataclass
class ArchiveResult:
    """Result of ArtifactLifecycleManager.archive_superseded()."""
    dry_run: bool = True
    moved: list[str] = field(default_factory=list)
    would_move: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "moved": list(self.moved),
            "would_move": list(self.would_move),
            "errors": list(self.errors),
        }


def _build_known_filenames() -> set[str]:
    """Return the set of all bare filenames registered in _MEMORY_TIER_FAMILIES."""
    names: set[str] = set()
    for family in _MEMORY_TIER_FAMILIES.values():
        for path_str in family["artifact_paths"]:
            names.add(Path(path_str).name)
    return names


class ArtifactLifecycleManager:
    """Classify and optionally archive artifacts in context_dir.

    Orphan detection: any file in context_dir whose name does not appear in
    any family's artifact_paths is classified as orphaned.

    Usage::

        mgr = ArtifactLifecycleManager(context_dir, _MEMORY_TIER_FAMILIES)
        scan = mgr.scan()
        result = mgr.archive_superseded(dry_run=not ctx.prune)
    """

    def __init__(self, context_dir: Path, tier_contract: dict) -> None:
        self.context_dir = context_dir
        self.tier_contract = tier_contract
        self._known_names = _build_known_filenames()

    def scan(self) -> LifecycleScanResult:
        """Classify all files in context_dir by lifecycle state.

        - archive/ subdirectory is skipped entirely.
        - Subdirectories are skipped.
        - Files whose basename is in _MEMORY_TIER_FAMILIES -> active.
        - Files whose basename is NOT in _MEMORY_TIER_FAMILIES -> orphaned.
        """
        result = LifecycleScanResult()

        if not self.context_dir.exists():
            return result

        for entry in sorted(self.context_dir.iterdir()):
            # Skip archive/ subdirectory and all subdirectories
            if entry.is_dir():
                continue
            name = entry.name
            # Skip hidden temp files
            if name.startswith(".tmp_"):
                continue
            if name in self._known_names:
                result.active.append(name)
            else:
                result.orphaned.append(name)

        return result

    def archive_superseded(
        self, dry_run: bool = True
    ) -> ArchiveResult:
        """Move superseded/orphaned artifacts to context_dir/archive/.

        In Phase 5, 'superseded' is equivalent to 'orphaned' -- any file not
        in _MEMORY_TIER_FAMILIES is a candidate for archiving.

        Default dry_run=True prevents accidental moves. Pass dry_run=False
        (via --prune flag) to execute actual moves.
        """
        scan = self.scan()
        archive_dir = self.context_dir / "archive"
        result = ArchiveResult(dry_run=dry_run)

        candidates = scan.orphaned

        for name in candidates:
            src = self.context_dir / name
            dst = archive_dir / name

            if dry_run:
                result.would_move.append(name)
            else:
                try:
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    result.moved.append(name)
                except Exception as exc:
                    result.errors.append(f"{name}: move failed: {exc}")

        return result


def check_context_overflow(
    context_dir: Path,
    max_artifacts: int,
    *,
    emit_to_stderr: bool = True,
) -> tuple[int, bool]:
    """Count all files in context_dir and warn if count exceeds max_artifacts.

    Returns (count, overflow_flag).
    overflow_flag is True when count > max_artifacts.
    Logs CONTEXT_OVERFLOW to stderr when overflow_flag is True and emit_to_stderr.
    """
    if not context_dir.exists():
        return 0, False

    count = sum(
        1 for entry in context_dir.iterdir()
        if entry.is_file() and not entry.name.startswith(".tmp_")
    )
    overflow = count > max_artifacts
    if overflow and emit_to_stderr:
        print(
            f"CONTEXT_OVERFLOW: {count} artifacts > {max_artifacts} limit",
            file=sys.stderr,
        )
    return count, overflow
