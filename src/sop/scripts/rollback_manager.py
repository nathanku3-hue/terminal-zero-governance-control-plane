"""Phase 3.1 -- RollbackManager: pre-run snapshot and artifact revert.

Captures a snapshot of docs/context/ *_latest.{json,md} files before the
first step runs, then restores them on Gate HOLD or unhandled exception.

D-183: scripts/rollback_manager.py must be byte-identical to this file.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_rb_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(data, indent=2) + "\n")
        os.replace(tmp, path)
    except Exception:
        try:
            Path(tmp).unlink(missing_ok=True)
        except Exception:
            pass
        raise


@dataclass
class RollbackResult:
    """Result bundle from RollbackManager.revert()."""

    rollback_result: str  # CLEAN | PARTIAL | FAILED
    artifacts_reverted: list[dict[str, str]] = field(default_factory=list)
    artifacts_not_found: list[str] = field(default_factory=list)


class RollbackManager:
    """Manages pre-run snapshot and artifact revert for Gate HOLD / exception.

    Lifecycle:
        rm = RollbackManager(context_dir)
        rm.snapshot()          # before first step
        ...execute loop...
        if hold:
            rm.revert(trace_id, trigger="gate_hold")  # exit code 5
        else:
            rm.cleanup()       # on clean PROCEED

    Snapshot scope: all *_latest.json and *_latest.md in context_dir (not subdirs).
    Snapshot strategy: copy each file to context_dir/.rollback_tmp/ before first step.
    .rollback_tmp/ is dot-prefixed and excluded from snapshot scope.
    """

    SNAPSHOT_DIR_NAME = ".rollback_tmp"

    def __init__(self, context_dir: Path) -> None:
        self._context_dir = context_dir
        self._snapshot_dir = context_dir / self.SNAPSHOT_DIR_NAME
        # in-memory metadata: path -> {mtime, size}
        self._snapshot_meta: dict[str, dict[str, Any]] = {}
        self._snapshotted = False

    def _scoped_files(self) -> list[Path]:
        """Return all *_latest.json and *_latest.md in context_dir (not subdirs)."""
        files: list[Path] = []
        if not self._context_dir.exists():
            return files
        for pattern in ("*_latest.json", "*_latest.md"):
            for p in self._context_dir.glob(pattern):
                if p.is_file() and not p.name.startswith("."):
                    files.append(p)
        return files

    def snapshot(self) -> None:
        """Capture snapshot of scoped artifacts before first step."""
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._snapshot_meta = {}
        for src in self._scoped_files():
            try:
                stat = src.stat()
                self._snapshot_meta[str(src)] = {
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                }
                dest = self._snapshot_dir / src.name
                shutil.copy2(str(src), str(dest))
            except Exception:
                pass  # best-effort
        self._snapshotted = True

    def revert(self, trace_id: str, trigger: str) -> RollbackResult:
        """Restore snapshot; write rollback_latest.json; remove temp dir.

        Returns RollbackResult with CLEAN / PARTIAL / FAILED.
        """
        artifacts_reverted: list[dict[str, str]] = []
        artifacts_not_found: list[str] = []
        failed = False

        for src_path_str, _meta in self._snapshot_meta.items():
            src = Path(src_path_str)
            backup = self._snapshot_dir / src.name
            if not backup.exists():
                artifacts_not_found.append(src_path_str)
                continue
            try:
                shutil.copy2(str(backup), str(src))
                artifacts_reverted.append(
                    {
                        "path": src_path_str,
                        "restored_from": str(backup),
                        "status": "restored",
                    }
                )
            except Exception as exc:
                failed = True
                artifacts_reverted.append(
                    {
                        "path": src_path_str,
                        "restored_from": str(backup),
                        "status": f"error: {exc}",
                    }
                )

        if failed:
            rollback_result = "FAILED"
        elif artifacts_not_found:
            rollback_result = "PARTIAL"
        else:
            rollback_result = "CLEAN"

        result = RollbackResult(
            rollback_result=rollback_result,
            artifacts_reverted=artifacts_reverted,
            artifacts_not_found=artifacts_not_found,
        )

        # Write rollback_latest.json
        rollback_path = self._context_dir / "rollback_latest.json"
        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "trace_id": trace_id,
            "triggered_at_utc": _utc_now_iso(),
            "trigger": trigger,
            "artifacts_reverted": artifacts_reverted,
            "artifacts_not_found": artifacts_not_found,
            "rollback_result": rollback_result,
        }
        try:
            _atomic_write_json(rollback_path, payload)
        except Exception:
            pass  # must not mask original error

        # Remove temp dir
        self._cleanup_snapshot_dir()
        return result

    def cleanup(self) -> None:
        """Remove snapshot dir on clean PROCEED exit (no revert)."""
        self._cleanup_snapshot_dir()

    def _cleanup_snapshot_dir(self) -> None:
        try:
            if self._snapshot_dir.exists():
                shutil.rmtree(str(self._snapshot_dir), ignore_errors=True)
        except Exception:
            pass
