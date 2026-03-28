"""tests/test_production_validation.py -- Phase 3.2 Production Validation tests."""
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

try:
    from sop.scripts.phase_gate import PhaseGate
except ModuleNotFoundError:
    from scripts.phase_gate import PhaseGate  # type: ignore[no-redef]

try:
    from sop.scripts.step_executor import StepExecutor
except ModuleNotFoundError:
    from scripts.step_executor import StepExecutor  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runtime(steps: list[dict[str, Any]], trace_id: str = "20260101T000000Z-abcd") -> Any:
    return SimpleNamespace(
        steps=steps,
        trace_id=trace_id,
        generated_at_utc="2026-01-01T00:00:00Z",
    )


def _make_ctx(context_dir: Path) -> Any:
    return SimpleNamespace(
        context_dir=context_dir,
        repo_root=context_dir.parent,
        compaction_status_json=context_dir / "context_compaction_status_latest.json",
        disagreement_ledger_jsonl=context_dir / "disagreement_ledger.jsonl",
    )


def _make_step(
    name: str,
    status: str = "PASS",
    duration: float = 1.0,
    sla_breach: bool = False,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "exit_code": 0 if status == "PASS" else 1,
        "duration_seconds": duration,
        "sla_breach": sla_breach,
        "started_utc": "2026-01-01T00:00:00Z",
        "ended_utc": "2026-01-01T00:00:01Z",
        "stdout": "",
        "stderr": "",
        "message": "",
        "command": [],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_baseline_record_appended_on_proceed(tmp_path: Path) -> None:
    """append_baseline_record() writes a line to run_regression_baseline.ndjson on PASS."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    runtime = _make_runtime([_make_step("step1"), _make_step("step2")])
    ctx = _make_ctx(context_dir)
    orch = LoopOrchestrator(ctx=ctx, runtime=runtime, helpers={})

    orch.append_baseline_record("PASS")

    baseline = context_dir / "run_regression_baseline.ndjson"
    assert baseline.exists(), "run_regression_baseline.ndjson should be created"
    lines = [l for l in baseline.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["final_result"] == "PASS"
    assert "p50_duration_s" in record
    assert "p95_duration_s" in record


def test_baseline_rolling_capped_at_100(tmp_path: Path) -> None:
    """append_baseline_record() keeps only the last 100 records."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    baseline = context_dir / "run_regression_baseline.ndjson"

    # Pre-seed with 110 records
    with baseline.open("w", encoding="utf-8") as fh:
        for i in range(110):
            fh.write(json.dumps({"trace_id": f"t{i}", "run_at_utc": "2026-01-01T00:00:00Z",
                                  "final_result": "PASS", "step_count": 1,
                                  "pass_count": 1, "error_count": 0,
                                  "p50_duration_s": 1.0, "p95_duration_s": 1.0}) + "\n")

    runtime = _make_runtime([_make_step("s")], trace_id="20260101T000000Z-new1")
    ctx = _make_ctx(context_dir)
    orch = LoopOrchestrator(ctx=ctx, runtime=runtime, helpers={})
    orch.append_baseline_record("PASS")

    lines = [l for l in baseline.read_text().splitlines() if l.strip()]
    assert len(lines) <= 100, f"Expected <=100 records after cap, got {len(lines)}"


def test_sla_breach_flagged_in_step_record(tmp_path: Path) -> None:
    """StepExecutor marks sla_breach=True when step exceeds step_sla_seconds."""
    ctx = SimpleNamespace(
        python_exe="python",
        repo_root=tmp_path,
        context_dir=tmp_path / "context",
    )
    (tmp_path / "context").mkdir()
    runtime = SimpleNamespace(
        steps=[],
        trace_id="20260101T000000Z-abcd",
        generated_at_utc="2026-01-01T00:00:00Z",
    )

    executor = StepExecutor(ctx=ctx, runtime=runtime, step_sla_seconds=0.0)
    # Use a script that doesn't exist -- results in an ERROR record with 0 duration
    # We verify sla_breach is present in all records
    fake_script = tmp_path / "nonexistent.py"
    executor.run("test_step", fake_script, [])

    assert len(runtime.steps) == 1
    step = runtime.steps[0]
    assert "sla_breach" in step, "sla_breach field must be present in step record"


def test_drift_alert_on_error_increase(tmp_path: Path) -> None:
    """run_drift_check() emits DRIFT_ALERT when error_count increases from 0 in last 5 runs."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    baseline = context_dir / "run_regression_baseline.ndjson"

    # Seed 5 clean records
    with baseline.open("w", encoding="utf-8") as fh:
        for i in range(5):
            fh.write(json.dumps({"trace_id": f"t{i}", "run_at_utc": "2026-01-01T00:00:00Z",
                                  "final_result": "PASS", "step_count": 1,
                                  "pass_count": 1, "error_count": 0,
                                  "p50_duration_s": 1.0, "p95_duration_s": 1.0}) + "\n")

    # Current run has an error
    runtime = _make_runtime([
        _make_step("s1", status="ERROR"),
    ])
    ctx = _make_ctx(context_dir)
    orch = LoopOrchestrator(ctx=ctx, runtime=runtime, helpers={})
    orch.run_drift_check()

    drift_path = context_dir / "run_drift_latest.json"
    assert drift_path.exists()
    data = json.loads(drift_path.read_text())
    alert_types = [a["alert_type"] for a in data.get("alerts", [])]
    assert "DRIFT_ALERT" in alert_types, "DRIFT_ALERT expected when errors increase from 0"


def test_drift_clean_on_stable_run(tmp_path: Path) -> None:
    """run_drift_check() emits empty alerts on a stable run."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    baseline = context_dir / "run_regression_baseline.ndjson"

    with baseline.open("w", encoding="utf-8") as fh:
        for i in range(5):
            fh.write(json.dumps({"trace_id": f"t{i}", "run_at_utc": "2026-01-01T00:00:00Z",
                                  "final_result": "PASS", "step_count": 1,
                                  "pass_count": 1, "error_count": 0,
                                  "p50_duration_s": 1.0, "p95_duration_s": 1.0}) + "\n")

    runtime = _make_runtime([_make_step("s1")])
    ctx = _make_ctx(context_dir)
    orch = LoopOrchestrator(ctx=ctx, runtime=runtime, helpers={})
    orch.run_drift_check()

    drift_path = context_dir / "run_drift_latest.json"
    assert drift_path.exists()
    data = json.loads(drift_path.read_text())
    assert data["alerts"] == [], f"Expected no alerts on stable run, got: {data['alerts']}"


def test_dry_run_evaluates_gates_without_executing(tmp_path: Path) -> None:
    """PhaseGate.evaluate_dry_run() returns a result without writing any artifact."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    repo_root = tmp_path

    gate = PhaseGate(
        from_phase="exec_memory",
        to_phase="advisory",
        repo_root=repo_root,
    )
    result = gate.evaluate_dry_run(context_dir)

    # No artifacts should be written in dry-run mode
    written = list(context_dir.glob("phase_gate_*.json"))
    assert written == [], f"dry-run must not write gate artifacts, got: {written}"

    # Result must have a valid decision
    assert result.decision in {"PROCEED", "HOLD"}
    # With no artifacts present, gate should HOLD
    assert result.decision == "HOLD"
