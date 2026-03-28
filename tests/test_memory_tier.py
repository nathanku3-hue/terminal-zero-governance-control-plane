"""tests/test_memory_tier.py

Phase 5.1 -- Memory Tier Contract tests (6 tests).

All assertions use static data; no runtime docs/context/ scanning.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

import sys
sys.path.insert(0, str(REPO_ROOT / "src"))

from sop.scripts.utils.memory_tiers import (
    _MEMORY_TIER_FAMILIES,
    MEMORY_TIER_CONTRACT_DOC_PATH,
)

# ---------------------------------------------------------------------------
# Static known-artifact list -- every artifact the system writes must appear
# in _MEMORY_TIER_FAMILIES.  Do NOT derive this list from docs/context/ at
# runtime; the test must be environment-independent.
# ---------------------------------------------------------------------------
_KNOWN_ARTIFACTS = [
    # hot
    "docs/context/loop_cycle_summary_latest.json",
    "docs/context/loop_cycle_summary_latest.md",
    "docs/context/loop_cycle_summary_current.json",
    "docs/context/exec_memory_packet_latest.json",
    "docs/context/exec_memory_packet_latest.md",
    "docs/context/exec_memory_packet_latest_current.json",
    "docs/context/exec_memory_packet_latest_current.md",
    "docs/context/exec_memory_packet_build_status_latest.json",
    "docs/context/exec_memory_packet_build_status_current.json",
    "docs/context/context_compaction_state_latest.json",
    "docs/context/context_compaction_status_latest.json",
    "docs/context/loop_run_trace_latest.json",
    "docs/context/loop_cycle_checkpoint_latest.json",
    "docs/context/orchestrator_state_latest.json",
    # warm
    "docs/context/auditor_promotion_dossier.json",
    "docs/context/auditor_promotion_dossier.md",
    "docs/context/auditor_calibration_report.json",
    "docs/context/auditor_calibration_report.md",
    "docs/context/ceo_go_signal.md",
    "docs/context/next_round_handoff_latest.json",
    "docs/context/next_round_handoff_latest.md",
    "docs/context/expert_request_latest.json",
    "docs/context/expert_request_latest.md",
    "docs/context/pm_ceo_research_brief_latest.json",
    "docs/context/pm_ceo_research_brief_latest.md",
    "docs/context/board_decision_brief_latest.json",
    "docs/context/board_decision_brief_latest.md",
    "docs/context/skill_activation_latest.json",
    "docs/context/phase_gate_a_latest.json",
    "docs/context/phase_gate_b_latest.json",
    "docs/context/phase_handoff_latest.json",
    "docs/context/run_drift_latest.json",
    "docs/context/rollback_latest.json",
    "docs/context/bridge_contract_current.md",
    "docs/context/bridge_contract_current.json",
    "docs/context/planner_packet_current.md",
    "docs/context/planner_packet_current.json",
    # cold
    "docs/context/auditor_fp_ledger.json",
    "docs/context/loop_run_steps_latest.ndjson",
    "docs/context/run_regression_baseline.ndjson",
    "docs/context/worker_merge_latest.json",
    "docs/context/loop_run_trace_master_latest.json",
]


def _all_artifact_paths() -> set[str]:
    """Union of all artifact_paths across every family."""
    paths: set[str] = set()
    for family in _MEMORY_TIER_FAMILIES.values():
        for p in family["artifact_paths"]:
            paths.add(p)
    return paths


# ---------------------------------------------------------------------------
# Test 1
# ---------------------------------------------------------------------------
def test_tier_contract_file_exists() -> None:
    contract_path = REPO_ROOT / MEMORY_TIER_CONTRACT_DOC_PATH
    assert contract_path.exists(), (
        f"MEMORY_TIER_CONTRACT.md not found at {contract_path}.\n"
        f"Expected MEMORY_TIER_CONTRACT_DOC_PATH={MEMORY_TIER_CONTRACT_DOC_PATH!r}"
    )


# ---------------------------------------------------------------------------
# Test 2
# ---------------------------------------------------------------------------
def test_all_hot_artifacts_classified() -> None:
    hot_paths = set()
    for family in _MEMORY_TIER_FAMILIES.values():
        if family["tier"] == "hot":
            for p in family["artifact_paths"]:
                hot_paths.add(p)
    expected_hot = {
        "docs/context/loop_cycle_summary_latest.json",
        "docs/context/loop_run_trace_latest.json",
        "docs/context/loop_cycle_checkpoint_latest.json",
        "docs/context/orchestrator_state_latest.json",
        "docs/context/exec_memory_packet_latest.json",
        "docs/context/context_compaction_state_latest.json",
        "docs/context/context_compaction_status_latest.json",
    }
    missing = expected_hot - hot_paths
    assert not missing, f"Hot artifacts missing from _MEMORY_TIER_FAMILIES: {missing}"


# ---------------------------------------------------------------------------
# Test 3
# ---------------------------------------------------------------------------
def test_all_warm_artifacts_classified() -> None:
    warm_paths = set()
    for family in _MEMORY_TIER_FAMILIES.values():
        if family["tier"] == "warm":
            for p in family["artifact_paths"]:
                warm_paths.add(p)
    expected_warm = {
        "docs/context/bridge_contract_current.md",
        "docs/context/bridge_contract_current.json",
        "docs/context/planner_packet_current.md",
        "docs/context/planner_packet_current.json",
        "docs/context/phase_gate_a_latest.json",
        "docs/context/phase_gate_b_latest.json",
        "docs/context/phase_handoff_latest.json",
        "docs/context/run_drift_latest.json",
        "docs/context/rollback_latest.json",
    }
    missing = expected_warm - warm_paths
    assert not missing, f"Warm artifacts missing from _MEMORY_TIER_FAMILIES: {missing}"


# ---------------------------------------------------------------------------
# Test 4: test_tier_assignment_is_exhaustive
# ---------------------------------------------------------------------------
def test_tier_assignment_is_exhaustive() -> None:
    """Every name in the static _KNOWN_ARTIFACTS list appears in _MEMORY_TIER_FAMILIES.

    Uses the static list defined in this test module -- does NOT scan
    docs/context/ at runtime, so the test is environment-independent.
    """
    all_paths = _all_artifact_paths()
    missing = [a for a in _KNOWN_ARTIFACTS if a not in all_paths]
    assert not missing, (
        f"{len(missing)} known artifact(s) are not covered by _MEMORY_TIER_FAMILIES:\n"
        + "\n".join(f"  {m}" for m in missing)
    )


# ---------------------------------------------------------------------------
# Test 5
# ---------------------------------------------------------------------------
def test_evidence_tier_in_orchestrator_state(tmp_path: Path) -> None:
    """OrchestratorStateWriter.write() must include evidence_tier in the output JSON."""
    from sop.scripts.orchestrator_state_writer import OrchestratorStateWriter

    context_dir = tmp_path / "context"
    context_dir.mkdir()
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()

    trace = {
        "trace_id": "test-trace-001",
        "repo_id": "test_repo",
        "final_result": "PASS",
        "generated_at_utc": "2026-03-28T12:00:00Z",
    }
    bridge = {"open_decision": "None"}
    planner_packet = {"active_bottleneck": "None"}

    writer = OrchestratorStateWriter(context_dir, schema_dir)
    out_path = writer.write(
        trace=trace,
        bridge=bridge,
        planner_packet=planner_packet,
        prior_state=None,
    )

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "evidence_tier" in data, (
        f"evidence_tier missing from orchestrator_state output. Keys: {list(data.keys())}"
    )
    tier_map = data["evidence_tier"]
    assert isinstance(tier_map, dict), "evidence_tier must be a dict"
    assert len(tier_map) > 0, "evidence_tier must not be empty"
    valid_tiers = {"hot", "warm", "cold"}
    for artifact, tier in tier_map.items():
        assert tier in valid_tiers, (
            f"Artifact {artifact!r} has invalid tier {tier!r}; expected one of {valid_tiers}"
        )


# ---------------------------------------------------------------------------
# Test 6
# ---------------------------------------------------------------------------
def test_hot_artifacts_have_freshness_entry(tmp_path: Path) -> None:
    """All hot-tier artifacts tracked in _KEY_ARTIFACTS appear in evidence_freshness."""
    from sop.scripts.orchestrator_state_writer import (
        OrchestratorStateWriter,
        _KEY_ARTIFACTS,
        _ARTIFACT_TIERS,
    )

    context_dir = tmp_path / "context"
    context_dir.mkdir()
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()

    trace = {
        "trace_id": "test-trace-002",
        "repo_id": "test_repo",
        "final_result": "PASS",
        "generated_at_utc": "2026-03-28T12:00:00Z",
    }
    bridge = {"open_decision": "None"}
    planner_packet = {"active_bottleneck": "None"}

    writer = OrchestratorStateWriter(context_dir, schema_dir)
    out_path = writer.write(
        trace=trace,
        bridge=bridge,
        planner_packet=planner_packet,
        prior_state=None,
    )

    data = json.loads(out_path.read_text(encoding="utf-8"))
    freshness = data.get("evidence_freshness", {})
    tier_map = data.get("evidence_tier", {})

    # Every hot artifact in _KEY_ARTIFACTS must appear in evidence_freshness
    hot_key_artifacts = [
        a for a in _KEY_ARTIFACTS if _ARTIFACT_TIERS.get(a) == "hot"
    ]
    assert hot_key_artifacts, "_KEY_ARTIFACTS must contain at least one hot artifact"
    for artifact in hot_key_artifacts:
        assert artifact in freshness, (
            f"Hot artifact {artifact!r} missing from evidence_freshness"
        )
        assert artifact in tier_map, (
            f"Hot artifact {artifact!r} missing from evidence_tier"
        )
        assert tier_map[artifact] == "hot", (
            f"Artifact {artifact!r} should be 'hot' in evidence_tier, got {tier_map[artifact]!r}"
        )
