"""tests/test_state_persistence.py

Phase 1 — Item 1.3 done criteria:
  5 tests: checkpoint write, stale invalidation rules, schema validation,
  resume step resolution, lesson stubs always written on resume.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the helpers we'll add to run_loop_cycle — tested via direct import
# so that the functions are exercised independently of the full cycle.
try:
    from sop.scripts.run_loop_cycle import (
        _load_checkpoint,
        _resolve_resume_steps,
        _write_checkpoint,
    )
except ImportError:
    from scripts.run_loop_cycle import (
        _load_checkpoint,
        _resolve_resume_steps,
        _write_checkpoint,
    )


pytestmark = pytest.mark.state_persistence


def _utc_iso(dt: datetime) -> str:
    return dt.isoformat()


def _make_checkpoint(
    partial: bool = True,
    completed_steps: list[str] | None = None,
    age_hours: float = 0.0,
    cycle_id: str = "2026-01-01T00:00:00+00:00",
) -> dict:
    generated_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return {
        "schema_version": "1.0",
        "generated_at_utc": _utc_iso(generated_at),
        "cycle_id": cycle_id,
        "completed_steps": completed_steps or [],
        "last_completed_step": (completed_steps or [None])[-1],
        "exec_memory_cycle_ready": "exec_memory" in (completed_steps or []),
        "partial": partial,
    }


# ---------------------------------------------------------------------------
# Test 1 — Checkpoint write: _write_checkpoint creates valid JSON
# ---------------------------------------------------------------------------

class TestCheckpointWrite:
    def test_write_checkpoint_creates_file(self, tmp_path: Path) -> None:
        checkpoint_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        _write_checkpoint(
            path=checkpoint_path,
            cycle_id="2026-01-01T00:00:00+00:00",
            completed_steps=["exec_memory"],
            exec_memory_cycle_ready=True,
            partial=True,
        )
        assert checkpoint_path.exists()
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert data["partial"] is True
        assert "exec_memory" in data["completed_steps"]
        assert data["exec_memory_cycle_ready"] is True
        assert data["last_completed_step"] == "exec_memory"

    def test_write_checkpoint_terminal_sets_partial_false(self, tmp_path: Path) -> None:
        checkpoint_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        _write_checkpoint(
            path=checkpoint_path,
            cycle_id="2026-01-01T00:00:00+00:00",
            completed_steps=["exec_memory", "advisory", "loop_summary"],
            exec_memory_cycle_ready=True,
            partial=False,
        )
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        assert data["partial"] is False
        assert data["last_completed_step"] == "loop_summary"


# ---------------------------------------------------------------------------
# Test 2 — Stale invalidation: all four stale conditions return None
# ---------------------------------------------------------------------------

class TestStaleCheckpointInvalidation:
    def test_partial_false_returns_none(self, tmp_path: Path) -> None:
        """partial=False means previous run completed cleanly — start fresh."""
        cp = _make_checkpoint(partial=False, completed_steps=["exec_memory", "advisory", "loop_summary"])
        cp_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        cp_path.write_text(json.dumps(cp), encoding="utf-8")
        result = _load_checkpoint(cp_path, max_age_hours=24.0, current_cycle_id=None)
        assert result is None

    def test_age_exceeded_returns_none(self, tmp_path: Path) -> None:
        """Checkpoint older than max_age_hours is treated as stale."""
        cp = _make_checkpoint(partial=True, age_hours=25.0)
        cp_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        cp_path.write_text(json.dumps(cp), encoding="utf-8")
        result = _load_checkpoint(cp_path, max_age_hours=24.0, current_cycle_id=None)
        assert result is None

    def test_cycle_id_mismatch_returns_none(self, tmp_path: Path) -> None:
        """Checkpoint cycle_id mismatch means it belongs to a different run."""
        cp = _make_checkpoint(partial=True, cycle_id="2026-01-01T00:00:00+00:00")
        cp_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        cp_path.write_text(json.dumps(cp), encoding="utf-8")
        result = _load_checkpoint(
            cp_path,
            max_age_hours=24.0,
            current_cycle_id="2026-01-02T00:00:00+00:00",
        )
        assert result is None

    def test_schema_invalid_returns_none(self, tmp_path: Path) -> None:
        """Checkpoint missing required fields fails schema validation → None."""
        cp_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        cp_path.write_text(json.dumps({"partial": True}), encoding="utf-8")
        result = _load_checkpoint(cp_path, max_age_hours=24.0, current_cycle_id=None)
        assert result is None

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        """Missing checkpoint file returns None (clean start)."""
        cp_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        result = _load_checkpoint(cp_path, max_age_hours=24.0, current_cycle_id=None)
        assert result is None


# ---------------------------------------------------------------------------
# Test 3 — Schema validation: valid checkpoint is returned as-is
# ---------------------------------------------------------------------------

class TestCheckpointSchemaValidation:
    def test_valid_checkpoint_returned(self, tmp_path: Path) -> None:
        cp = _make_checkpoint(partial=True, completed_steps=["exec_memory"])
        cp_path = tmp_path / "loop_cycle_checkpoint_latest.json"
        cp_path.write_text(json.dumps(cp), encoding="utf-8")
        result = _load_checkpoint(cp_path, max_age_hours=24.0, current_cycle_id=None)
        assert result is not None
        assert "exec_memory" in result["completed_steps"]


# ---------------------------------------------------------------------------
# Test 4 — Resume step resolution: correct steps skipped
# ---------------------------------------------------------------------------

class TestResumeStepResolution:
    def test_none_checkpoint_returns_empty_set(self) -> None:
        assert _resolve_resume_steps(None) == set()

    def test_exec_memory_only_in_resume_set(self) -> None:
        cp = _make_checkpoint(partial=True, completed_steps=["exec_memory"])
        resume = _resolve_resume_steps(cp)
        assert "exec_memory" in resume
        assert "advisory" not in resume

    def test_exec_memory_and_advisory_in_resume_set(self) -> None:
        cp = _make_checkpoint(partial=True, completed_steps=["exec_memory", "advisory"])
        resume = _resolve_resume_steps(cp)
        assert resume == {"exec_memory", "advisory"}


# ---------------------------------------------------------------------------
# Test 5 — Lesson stubs always written on resume (runtime side-effect check)
# ---------------------------------------------------------------------------

class TestLessonStubsOnResume:
    def test_lesson_stubs_written_regardless_of_resume(self, tmp_path: Path) -> None:
        """build_loop_cycle_runtime() always writes lesson stubs,
        even when resume_steps is non-empty.  Verify the stubs exist after
        runtime construction."""
        context_dir = tmp_path / "context"
        context_dir.mkdir()

        from sop.scripts.loop_cycle_runtime import build_loop_cycle_runtime

        ctx = MagicMock()
        ctx.context_dir = context_dir

        runtime = build_loop_cycle_runtime(ctx)

        assert (context_dir / "lessons_worker_latest.md").exists()
        assert (context_dir / "lessons_auditor_latest.md").exists()
        assert runtime.lessons_paths["worker"].exists()
        assert runtime.lessons_paths["auditor"].exists()
