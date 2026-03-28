"""tests/test_distributed.py -- Phase 3.3 Distributed Coordination tests."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

try:
    from sop.scripts.orchestrator import LoopOrchestrator
except ModuleNotFoundError:
    from scripts.orchestrator import LoopOrchestrator  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runtime(trace_id: str = "20260101T000000Z-abcd") -> Any:
    return SimpleNamespace(
        steps=[],
        trace_id=trace_id,
        generated_at_utc="2026-01-01T00:00:00Z",
    )


def _make_ctx(context_dir: Path) -> Any:
    return SimpleNamespace(
        context_dir=context_dir,
        repo_root=context_dir.parent,
    )


def _make_orchestrator(context_dir: Path, trace_id: str = "20260101T000000Z-abcd") -> LoopOrchestrator:
    ctx = _make_ctx(context_dir)
    runtime = _make_runtime(trace_id)
    return LoopOrchestrator(ctx=ctx, runtime=runtime, helpers={})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_parallel_all_pass_no_conflict(tmp_path: Path) -> None:
    """run_parallel() with quorum='all' and all PASS workers returns 0 and no conflicts."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    orch = _make_orchestrator(context_dir)

    def worker_fn(worker_id: int) -> str:
        return "PASS"

    exit_code = orch.run_parallel(worker_fn, n=2, quorum="all")
    assert exit_code == 0, f"Expected 0 (PASS), got {exit_code}"

    merge = json.loads((context_dir / "worker_merge_latest.json").read_text())
    assert merge["aggregate_result"] == "PASS"
    assert merge["conflicts"] == []


def test_parallel_conflict_detected(tmp_path: Path) -> None:
    """run_parallel() with quorum='all' detects CONFLICT when workers disagree."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    orch = _make_orchestrator(context_dir)

    results_seq = ["PASS", "HOLD"]

    def worker_fn(worker_id: int) -> str:
        return results_seq[worker_id]

    exit_code = orch.run_parallel(worker_fn, n=2, quorum="all")
    assert exit_code == 3, f"Expected 3 (conflict), got {exit_code}"

    merge = json.loads((context_dir / "worker_merge_latest.json").read_text())
    assert merge["aggregate_result"] == "CONFLICT"
    assert len(merge["conflicts"]) > 0


def test_quorum_majority_proceeds(tmp_path: Path) -> None:
    """run_parallel() with quorum='majority': n=3, 2 PASS + 1 HOLD = PROCEED (exit 0)."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    orch = _make_orchestrator(context_dir)

    results_seq = ["PASS", "PASS", "HOLD"]

    def worker_fn(worker_id: int) -> str:
        return results_seq[worker_id]

    exit_code = orch.run_parallel(worker_fn, n=3, quorum="majority")
    assert exit_code == 0, (
        f"Expected 0 (PASS via majority): 2 PASS + 1 HOLD with n=3 should PROCEED, got {exit_code}"
    )

    merge = json.loads((context_dir / "worker_merge_latest.json").read_text())
    assert merge["aggregate_result"] == "PASS"


def test_master_trace_written_to_separate_path(tmp_path: Path) -> None:
    """run_parallel() writes loop_run_trace_master_latest.json separate from loop_run_trace_latest.json."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    # Create Phase 2.1 trace to ensure no collision
    phase2_trace = context_dir / "loop_run_trace_latest.json"
    phase2_trace.write_text(json.dumps({"schema_version": "1.0", "trace_id": "phase2-trace"}), encoding="utf-8")

    orch = _make_orchestrator(context_dir)

    def worker_fn(worker_id: int) -> str:
        return "PASS"

    orch.run_parallel(worker_fn, n=1, quorum="all")

    master_path = context_dir / "loop_run_trace_master_latest.json"
    assert master_path.exists(), "loop_run_trace_master_latest.json must be written"

    # Phase 2.1 trace must not be overwritten
    phase2_data = json.loads(phase2_trace.read_text())
    assert phase2_data["trace_id"] == "phase2-trace", (
        "loop_run_trace_latest.json (Phase 2.1) must not be modified by run_parallel()"
    )

    master_data = json.loads(master_path.read_text())
    assert master_data["trace_id"].startswith("master-"), (
        "Master trace_id must start with 'master-'"
    )


def test_worker_timeout_exits_code_4(tmp_path: Path) -> None:
    """run_parallel() returns exit code 4 when workers exceed timeout."""
    import time
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    orch = _make_orchestrator(context_dir)

    def slow_worker(worker_id: int) -> str:
        time.sleep(10)  # Will be cancelled/timed out
        return "PASS"

    exit_code = orch.run_parallel(slow_worker, n=1, quorum="all", timeout_seconds=0.01)
    assert exit_code == 4, f"Expected 4 (timeout), got {exit_code}"

    merge = json.loads((context_dir / "worker_merge_latest.json").read_text())
    assert merge["aggregate_result"] == "TIMEOUT"


def test_worker_subdirs_isolated_no_collision(tmp_path: Path) -> None:
    """Regression: run_parallel() does not overwrite loop_run_trace_latest.json (Phase 2.1 path)."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    original_content = {"schema_version": "1.0", "trace_id": "original-p2", "final_result": "PASS"}
    phase2_trace = context_dir / "loop_run_trace_latest.json"
    phase2_trace.write_text(json.dumps(original_content), encoding="utf-8")

    orch = _make_orchestrator(context_dir)

    def worker_fn(worker_id: int) -> str:
        return "PASS"

    orch.run_parallel(worker_fn, n=2, quorum="all")

    # Phase 2.1 trace must be untouched
    recovered = json.loads(phase2_trace.read_text())
    assert recovered == original_content, (
        "run_parallel() must not touch loop_run_trace_latest.json"
    )
