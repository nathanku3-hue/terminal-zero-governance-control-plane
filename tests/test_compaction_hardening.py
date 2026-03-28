"""tests/test_compaction_hardening.py

Phase 5.2 -- Compaction Hardening tests (6 tests).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

import sys
sys.path.insert(0, str(REPO_ROOT / "src"))

from sop.scripts.tier_aware_compactor import (
    TierAwareCompactor,
    CompactionReport,
    COMPACTION_REPORT_SCHEMA_VERSION,
)
from sop.scripts.utils.memory_tiers import _MEMORY_TIER_FAMILIES


def _make_ndjson(path: Path, n: int) -> None:
    """Write n lines of simple JSON to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for i in range(n):
            fh.write(json.dumps({"i": i}) + "\n")


def _line_count(path: Path) -> int:
    return len([ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()])


# ---------------------------------------------------------------------------
# Test 1: hot artifacts are never compacted
# ---------------------------------------------------------------------------
def test_hot_artifacts_never_compacted(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    hot_file = context_dir / "loop_run_trace_latest.json"
    hot_file.write_text(json.dumps({"data": "hot"}) + "\n", encoding="utf-8")
    mtime_before = hot_file.stat().st_mtime

    compactor = TierAwareCompactor(
        context_dir=context_dir,
        tier_contract=_MEMORY_TIER_FAMILIES,
        blocked=False,
    )
    report = compactor.run()

    assert "docs/context/loop_run_trace_latest.json" not in report.compacted
    assert "docs/context/loop_run_trace_latest.json" in report.skipped_hot
    data = json.loads(hot_file.read_text(encoding="utf-8"))
    assert data["data"] == "hot"


# ---------------------------------------------------------------------------
# Test 2: warm artifact is a no-op (retained, not compacted)
# ---------------------------------------------------------------------------
def test_warm_artifact_superseded_by_newer(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    warm_file = context_dir / "bridge_contract_current.md"
    warm_file.write_text("# Bridge Contract\n", encoding="utf-8")

    compactor = TierAwareCompactor(
        context_dir=context_dir,
        tier_contract=_MEMORY_TIER_FAMILIES,
        blocked=False,
    )
    report = compactor.run()

    assert "docs/context/bridge_contract_current.md" not in report.compacted
    assert "docs/context/bridge_contract_current.md" not in report.skipped_hot
    assert warm_file.exists()
    assert warm_file.read_text(encoding="utf-8") == "# Bridge Contract\n"


# ---------------------------------------------------------------------------
# Test 3: cold NDJSON rolling window applied
# ---------------------------------------------------------------------------
def test_cold_ndjson_rolling_window_applied(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    # run_regression_baseline has max_records=100; write 150 lines
    baseline = context_dir / "run_regression_baseline.ndjson"
    _make_ndjson(baseline, 150)
    assert _line_count(baseline) == 150

    compactor = TierAwareCompactor(
        context_dir=context_dir,
        tier_contract=_MEMORY_TIER_FAMILIES,
        blocked=False,
    )
    report = compactor.run()

    assert _line_count(baseline) == 100, (
        f"Expected 100 records after rolling window; got {_line_count(baseline)}"
    )
    assert "docs/context/run_regression_baseline.ndjson" in report.compacted


# ---------------------------------------------------------------------------
# Test 4: compaction only runs after writers complete (blocked=False)
# ---------------------------------------------------------------------------
def test_compaction_only_after_writers_complete(tmp_path: Path) -> None:
    """When blocked=False, compaction executes normally (writers are done)."""
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    baseline = context_dir / "run_regression_baseline.ndjson"
    _make_ndjson(baseline, 200)

    compactor = TierAwareCompactor(
        context_dir=context_dir,
        tier_contract=_MEMORY_TIER_FAMILIES,
        blocked=False,
    )
    report = compactor.run()

    assert not report.blocked
    assert _line_count(baseline) == 100


# ---------------------------------------------------------------------------
# Test 5: compaction skipped when blocked=True
# ---------------------------------------------------------------------------
def test_compaction_skipped_when_blocked(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()

    baseline = context_dir / "run_regression_baseline.ndjson"
    _make_ndjson(baseline, 200)

    compactor = TierAwareCompactor(
        context_dir=context_dir,
        tier_contract=_MEMORY_TIER_FAMILIES,
        blocked=True,
    )
    report = compactor.run()

    assert report.blocked is True
    assert report.compacted == []
    assert report.skipped_hot == []
    # File must be untouched
    assert _line_count(baseline) == 200


# ---------------------------------------------------------------------------
# Test 6: CompactionReport validates against compaction_report.schema.json
# ---------------------------------------------------------------------------
def test_compaction_report_schema_valid(tmp_path: Path) -> None:
    schema_path = REPO_ROOT / "src" / "sop" / "schemas" / "compaction_report.schema.json"
    assert schema_path.exists(), f"Schema not found: {schema_path}"

    context_dir = tmp_path / "context"
    context_dir.mkdir()

    compactor = TierAwareCompactor(
        context_dir=context_dir,
        tier_contract=_MEMORY_TIER_FAMILIES,
        blocked=False,
    )
    report = compactor.run()
    report_dict = report.to_dict()

    import json as _json
    schema = _json.loads(schema_path.read_text(encoding="utf-8"))

    try:
        import jsonschema
        jsonschema.validate(instance=report_dict, schema=schema)
    except ImportError:
        # jsonschema not installed -- validate structure manually
        assert "schema_version" in report_dict
        assert "generated_at_utc" in report_dict
        assert isinstance(report_dict["blocked"], bool)
        assert isinstance(report_dict["compacted"], list)
        assert isinstance(report_dict["retained"], list)
        assert isinstance(report_dict["skipped_hot"], list)
        assert isinstance(report_dict["errors"], list)
