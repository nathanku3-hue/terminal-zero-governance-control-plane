from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Mapping


MEMORY_TIER_SCHEMA_VERSION = "1.0.0"
MEMORY_TIER_SOURCE_PATH = "scripts/utils/memory_tiers.py"
MEMORY_TIER_CONTRACT_DOC_PATH = "docs/context/MEMORY_TIER_CONTRACT.md"


_MEMORY_TIER_FAMILIES: dict[str, dict[str, Any]] = {
    "loop_cycle_summary": {
        "tier": "hot",
        "access": "default_input",
        "description": "Current loop execution state and blocker summary.",
        "artifact_paths": (
            "docs/context/loop_cycle_summary_latest.json",
            "docs/context/loop_cycle_summary_latest.md",
            "docs/context/loop_cycle_summary_current.json",
        ),
    },
    "auditor_promotion_dossier": {
        "tier": "warm",
        "access": "default_input",
        "description": "Latest promotion criteria, FP analysis, and per-rule summary.",
        "artifact_paths": (
            "docs/context/auditor_promotion_dossier.json",
            "docs/context/auditor_promotion_dossier.md",
        ),
    },
    "auditor_calibration_report": {
        "tier": "warm",
        "access": "default_input",
        "description": "Latest auditor calibration totals and weekly report summary.",
        "artifact_paths": (
            "docs/context/auditor_calibration_report.json",
            "docs/context/auditor_calibration_report.md",
        ),
    },
    "ceo_go_signal": {
        "tier": "warm",
        "access": "default_input",
        "description": "Latest CEO go-signal and blocking-reason markdown.",
        "artifact_paths": (
            "docs/context/ceo_go_signal.md",
        ),
    },
    "decision_log": {
        "tier": "warm",
        "access": "default_input",
        "description": "Governance decision log summarized into PM memory.",
        "artifact_paths": (
            "docs/decision log.md",
        ),
    },
    "milestone_expert_roster": {
        "tier": "warm",
        "access": "default_input",
        "description": "Current approved milestone expert roster for lineup decisions.",
        "artifact_paths": (
            "docs/context/milestone_expert_roster_latest.json",
        ),
    },
    "project_skill_config": {
        "tier": "warm",
        "access": "default_input",
        "description": "Project-local skill activation configuration used to derive skill context.",
        "artifact_paths": (
            ".sop_config.yaml",
        ),
    },
    "extension_allowlist": {
        "tier": "warm",
        "access": "default_input",
        "description": "Global allowlist that constrains skill activation visibility.",
        "artifact_paths": (
            "extension_allowlist.yaml",
        ),
    },
    "skill_registry": {
        "tier": "warm",
        "access": "default_input",
        "description": "Registry metadata used to describe active skills in memory outputs.",
        "artifact_paths": (
            "skills/registry.yaml",
        ),
    },
    "exec_memory_packet": {
        "tier": "hot",
        "access": "derived_output",
        "description": "Current exec-memory packet consumed by later loop stages and compaction checks.",
        "artifact_paths": (
            "docs/context/exec_memory_packet_latest.json",
            "docs/context/exec_memory_packet_latest.md",
            "docs/context/exec_memory_packet_latest_current.json",
            "docs/context/exec_memory_packet_latest_current.md",
        ),
    },
    "exec_memory_build_status": {
        "tier": "hot",
        "access": "derived_output",
        "description": "Build-status machine state for the current exec-memory packet.",
        "artifact_paths": (
            "docs/context/exec_memory_packet_build_status_latest.json",
            "docs/context/exec_memory_packet_build_status_current.json",
        ),
    },
    "next_round_handoff": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Latest bounded next-round handoff surface derived from current loop artifacts.",
        "artifact_paths": (
            "docs/context/next_round_handoff_latest.json",
            "docs/context/next_round_handoff_latest.md",
        ),
    },
    "expert_request": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Latest specialist request surface derived from current loop artifacts.",
        "artifact_paths": (
            "docs/context/expert_request_latest.json",
            "docs/context/expert_request_latest.md",
        ),
    },
    "pm_ceo_research_brief": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Latest PM/CEO research brief derived from current loop artifacts.",
        "artifact_paths": (
            "docs/context/pm_ceo_research_brief_latest.json",
            "docs/context/pm_ceo_research_brief_latest.md",
        ),
    },
    "board_decision_brief": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Latest board decision brief derived from current loop artifacts.",
        "artifact_paths": (
            "docs/context/board_decision_brief_latest.json",
            "docs/context/board_decision_brief_latest.md",
        ),
    },
    "skill_activation": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Current skill-activation view derived from project config and allowlist inputs.",
        "artifact_paths": (
            "docs/context/skill_activation_latest.json",
        ),
    },
    "context_compaction_state": {
        "tier": "hot",
        "access": "default_input",
        "description": "Rolling compaction state used by the next trigger evaluation.",
        "artifact_paths": (
            "docs/context/context_compaction_state_latest.json",
        ),
    },
    "context_compaction_status": {
        "tier": "hot",
        "access": "derived_output",
        "description": "Latest compaction-trigger verdict for the current loop state.",
        "artifact_paths": (
            "docs/context/context_compaction_status_latest.json",
        ),
    },
    "auditor_fp_ledger": {
        "tier": "cold",
        "access": "manual_fallback",
        "description": "Ledger-level auditor deep-dive evidence reserved for manual fallback review.",
        "artifact_paths": (
            "docs/context/auditor_fp_ledger.json",
        ),
    },
    # --- Phase 2-4 families (added Phase 5) ---
    # Hot tier
    "loop_run_trace": {
        "tier": "hot",
        "access": "derived_output",
        "description": "Per-run execution trace written after every loop cycle.",
        "artifact_paths": (
            "docs/context/loop_run_trace_latest.json",
        ),
    },
    "loop_cycle_checkpoint": {
        "tier": "hot",
        "access": "derived_output",
        "description": "Checkpoint state enabling resume after partial loop cycle.",
        "artifact_paths": (
            "docs/context/loop_cycle_checkpoint_latest.json",
        ),
    },
    "orchestrator_state": {
        "tier": "hot",
        "access": "derived_output",
        "description": "Authoritative orchestrator self-state; loaded on every startup.",
        "artifact_paths": (
            "docs/context/orchestrator_state_latest.json",
        ),
    },
    # Warm tier
    "phase_gate_a": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Phase gate A evaluation result (exec_memory -> advisory).",
        "artifact_paths": (
            "docs/context/phase_gate_a_latest.json",
        ),
    },
    "phase_gate_b": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Phase gate B evaluation result (advisory -> summary).",
        "artifact_paths": (
            "docs/context/phase_gate_b_latest.json",
        ),
    },
    "phase_handoff": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Phase handoff artifact emitted on gate B PROCEED.",
        "artifact_paths": (
            "docs/context/phase_handoff_latest.json",
        ),
    },
    "run_drift": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Run-to-baseline drift detection result for current loop cycle.",
        "artifact_paths": (
            "docs/context/run_drift_latest.json",
        ),
    },
    "rollback": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Rollback state artifact written when a HOLD triggers revert.",
        "artifact_paths": (
            "docs/context/rollback_latest.json",
        ),
    },
    "bridge_contract": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Bridge contract translating execution truth to PM/planner language.",
        "artifact_paths": (
            "docs/context/bridge_contract_current.md",
            "docs/context/bridge_contract_current.json",
        ),
    },
    "planner_packet": {
        "tier": "warm",
        "access": "derived_output",
        "description": "Compact fresh-context packet; planner enters from it alone.",
        "artifact_paths": (
            "docs/context/planner_packet_current.md",
            "docs/context/planner_packet_current.json",
        ),
    },
    # Cold tier
    "loop_run_steps": {
        "tier": "cold",
        "access": "manual_fallback",
        "description": "Rolling NDJSON log of all step records for the current loop run.",
        "artifact_paths": (
            "docs/context/loop_run_steps_latest.ndjson",
        ),
    },
    "run_regression_baseline": {
        "tier": "cold",
        "access": "manual_fallback",
        "description": "Rolling NDJSON baseline used for drift detection across runs.",
        "artifact_paths": (
            "docs/context/run_regression_baseline.ndjson",
        ),
    },
    "worker_merge": {
        "tier": "cold",
        "access": "manual_fallback",
        "description": "Parallel worker merge result from run_parallel() coordination.",
        "artifact_paths": (
            "docs/context/worker_merge_latest.json",
        ),
    },
    "loop_run_trace_master": {
        "tier": "cold",
        "access": "manual_fallback",
        "description": "Master trace aggregating all parallel worker traces.",
        "artifact_paths": (
            "docs/context/loop_run_trace_master_latest.json",
        ),
    },
}


def _serialize_family(family_id: str) -> dict[str, Any]:
    if family_id not in _MEMORY_TIER_FAMILIES:
        raise ValueError(f"Unknown memory tier family: {family_id}")
    payload = dict(_MEMORY_TIER_FAMILIES[family_id])
    payload["family"] = family_id
    payload["artifact_paths"] = list(payload["artifact_paths"])
    return payload


def build_memory_tier_snapshot(
    *,
    family_ids: Iterable[str],
    cold_fallback_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a stable memory-tier snapshot for script outputs."""
    families = [_serialize_family(family_id) for family_id in family_ids]
    cold_fallbacks = [_serialize_family(family_id) for family_id in cold_fallback_ids]
    return {
        "schema_version": MEMORY_TIER_SCHEMA_VERSION,
        "source_of_truth": MEMORY_TIER_SOURCE_PATH,
        "documentation": MEMORY_TIER_CONTRACT_DOC_PATH,
        "families": families,
        "cold_manual_fallbacks": cold_fallbacks,
    }


def bind_memory_tier_paths(family_paths: Mapping[str, str | Path]) -> list[dict[str, str]]:
    """Attach actual script paths to known memory-tier families."""
    bindings: list[dict[str, str]] = []
    for family_id, path in family_paths.items():
        family = _serialize_family(family_id)
        bindings.append(
            {
                "family": family_id,
                "path": str(path),
                "tier": str(family["tier"]),
                "access": str(family["access"]),
            }
        )
    return bindings
