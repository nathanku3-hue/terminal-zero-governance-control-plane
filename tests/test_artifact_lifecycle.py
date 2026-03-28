"""tests/test_artifact_lifecycle.py

Phase 5.3 -- Artifact Pruning & Lifecycle tests (6 tests).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from sop.scripts.artifact_lifecycle_manager import (
    ArtifactLifecycleManager,
    check_context_overflow,
)
from sop.scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES


# ---------------------------------------------------------------------------
# Test 1: scan classifies known artifacts as active, unknowns as orphaned
# ---------------------------------------------------------------------------
def test_scan_classifies_all_artifacts(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    # Known file
    (context_dir / "loop_run_trace_latest.json").write_text("{}", encoding="utf-8")
    # Unknown file
    (context_dir / "old_unknown_artifact.json").write_text("{}", encoding="utf-8")

    mgr = ArtifactLifecycleManager(context_dir, _MEMORY_TIER_FAMILIES)
    result = mgr.scan()

    assert "loop_run_trace_latest.json" in result.active
    assert "old_unknown_artifact.json" in result.orphaned
    assert "loop_run_trace_latest.json" not in result.orphaned


# ---------------------------------------------------------------------------
# Test 2: superseded (orphaned) artifact identified correctly
# ---------------------------------------------------------------------------
def test_superseded_artifact_identified(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    # Simulate a stale artifact not in any family
    (context_dir / "stale_phase3_output.json").write_text("{}", encoding="utf-8")
    (context_dir / "orchestrator_state_latest.json").write_text("{}", encoding="utf-8")

    mgr = ArtifactLifecycleManager(context_dir, _MEMORY_TIER_FAMILIES)
    result = mgr.scan()

    assert "stale_phase3_output.json" in result.orphaned
    assert "orchestrator_state_latest.json" in result.active


# ---------------------------------------------------------------------------
# Test 3: archive_superseded dry_run=True moves nothing
# ---------------------------------------------------------------------------
def test_archive_superseded_dry_run_no_files_moved(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    orphan = context_dir / "old_mystery_file.json"
    orphan.write_text("{}", encoding="utf-8")

    mgr = ArtifactLifecycleManager(context_dir, _MEMORY_TIER_FAMILIES)
    result = mgr.archive_superseded(dry_run=True)

    assert result.dry_run is True
    assert "old_mystery_file.json" in result.would_move
    assert result.moved == []
    # File must still be in context_dir
    assert orphan.exists()
    # archive/ must NOT have been created
    assert not (context_dir / "archive").exists()


# ---------------------------------------------------------------------------
# Test 4: archive_superseded dry_run=False (--prune) actually moves files
# ---------------------------------------------------------------------------
def test_archive_superseded_moves_files_with_prune_flag(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    orphan = context_dir / "old_stale_output.json"
    orphan.write_text("{}", encoding="utf-8")

    mgr = ArtifactLifecycleManager(context_dir, _MEMORY_TIER_FAMILIES)
    result = mgr.archive_superseded(dry_run=False)

    assert result.dry_run is False
    assert "old_stale_output.json" in result.moved
    assert result.errors == []
    # File must no longer be in context_dir root
    assert not orphan.exists()
    # File must be in archive/
    assert (context_dir / "archive" / "old_stale_output.json").exists()


# ---------------------------------------------------------------------------
# Test 5: context overflow warning logged to stderr
# ---------------------------------------------------------------------------
def test_context_overflow_warning_logged(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    # Create 6 files with max_artifacts=5
    for i in range(6):
        (context_dir / f"artifact_{i}.json").write_text("{}", encoding="utf-8")

    count, overflow = check_context_overflow(context_dir, max_artifacts=5, emit_to_stderr=True)

    assert overflow is True
    assert count == 6
    captured = capsys.readouterr()
    assert "CONTEXT_OVERFLOW" in captured.err
    assert "6" in captured.err
    assert "5" in captured.err


# ---------------------------------------------------------------------------
# Test 6: orphaned artifact reported by scan
# ---------------------------------------------------------------------------
def test_orphaned_artifact_reported(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    # Write several files: some known, some unknown
    (context_dir / "loop_run_trace_latest.json").write_text("{}", encoding="utf-8")
    (context_dir / "orphan_a.json").write_text("{}", encoding="utf-8")
    (context_dir / "orphan_b.ndjson").write_text("", encoding="utf-8")

    mgr = ArtifactLifecycleManager(context_dir, _MEMORY_TIER_FAMILIES)
    result = mgr.scan()

    assert "orphan_a.json" in result.orphaned
    assert "orphan_b.ndjson" in result.orphaned
    assert len(result.orphaned) == 2
    assert "loop_run_trace_latest.json" in result.active
