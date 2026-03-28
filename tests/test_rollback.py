"""tests/test_rollback.py -- Phase 3.1 Rollback & Recovery tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from sop.scripts.rollback_manager import RollbackManager
except ModuleNotFoundError:
    from scripts.rollback_manager import RollbackManager  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_latest_artifact(context_dir: Path, name: str, payload: dict) -> Path:
    """Write a *_latest.json artifact to context_dir and return its path."""
    p = context_dir / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_snapshot_created_before_steps(tmp_path: Path) -> None:
    """RollbackManager.snapshot() copies *_latest.json files to .rollback_tmp/."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    art = _make_latest_artifact(context_dir, "exec_memory_packet_latest.json", {"v": 1})

    rm = RollbackManager(context_dir)
    rm.snapshot()

    snap_dir = context_dir / ".rollback_tmp"
    assert snap_dir.exists(), ".rollback_tmp should be created by snapshot()"
    snap_copy = snap_dir / art.name
    assert snap_copy.exists(), f"Snapshot copy missing: {snap_copy}"
    assert json.loads(snap_copy.read_text()) == {"v": 1}


def test_revert_on_hold_restores_artifacts(tmp_path: Path) -> None:
    """revert() restores artifact content from snapshot to original path."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    art = _make_latest_artifact(context_dir, "exec_memory_packet_latest.json", {"v": 1})

    rm = RollbackManager(context_dir)
    rm.snapshot()

    # Simulate modification by loop
    art.write_text(json.dumps({"v": 99}), encoding="utf-8")
    assert json.loads(art.read_text()) == {"v": 99}

    result = rm.revert(trace_id="test-trace", trigger="gate_hold")

    assert json.loads(art.read_text()) == {"v": 1}, "Artifact should be restored to pre-run content"
    assert result.rollback_result == "CLEAN"


def test_rollback_artifact_written(tmp_path: Path) -> None:
    """revert() writes rollback_latest.json with correct fields."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    _make_latest_artifact(context_dir, "loop_cycle_summary_latest.json", {"x": 1})

    rm = RollbackManager(context_dir)
    rm.snapshot()
    rm.revert(trace_id="trace-abc", trigger="gate_hold")

    rollback_path = context_dir / "rollback_latest.json"
    assert rollback_path.exists(), "rollback_latest.json should be written"
    data = json.loads(rollback_path.read_text())
    assert data["trace_id"] == "trace-abc"
    assert data["trigger"] == "gate_hold"
    assert data["schema_version"] == "1.0"


def test_rollback_schema_valid(tmp_path: Path) -> None:
    """rollback_latest.json must contain all 7 required fields."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    _make_latest_artifact(context_dir, "exec_memory_packet_latest.json", {})

    rm = RollbackManager(context_dir)
    rm.snapshot()
    rm.revert(trace_id="trace-schema", trigger="exception")

    data = json.loads((context_dir / "rollback_latest.json").read_text())
    required = {
        "schema_version", "trace_id", "triggered_at_utc",
        "trigger", "artifacts_reverted", "artifacts_not_found", "rollback_result",
    }
    missing = required - set(data.keys())
    assert not missing, f"rollback_latest.json missing fields: {missing}"
    assert data["rollback_result"] in {"CLEAN", "PARTIAL", "FAILED"}


def test_corrupt_checkpoint_forces_full_run(tmp_path: Path) -> None:
    """_load_checkpoint() returns None for a corrupt (unparseable) checkpoint."""
    try:
        from sop.scripts.run_loop_cycle import _load_checkpoint
    except ModuleNotFoundError:
        from scripts.run_loop_cycle import _load_checkpoint  # type: ignore[no-redef]

    context_dir = tmp_path / "context"
    context_dir.mkdir()
    cp_path = context_dir / "loop_cycle_checkpoint_latest.json"
    cp_path.write_text("NOT VALID JSON {{{", encoding="utf-8")

    result = _load_checkpoint(cp_path)
    assert result is None, "Corrupt checkpoint should return None (force full re-run)"


def test_cleanup_removes_snapshot_on_proceed(tmp_path: Path) -> None:
    """cleanup() removes .rollback_tmp/ on clean PROCEED exit."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    _make_latest_artifact(context_dir, "exec_memory_packet_latest.json", {"v": 1})

    rm = RollbackManager(context_dir)
    rm.snapshot()

    snap_dir = context_dir / ".rollback_tmp"
    assert snap_dir.exists()

    rm.cleanup()
    assert not snap_dir.exists(), ".rollback_tmp should be removed after cleanup()"
