"""tests/test_script_surface_sync.py

Phase 0 hard gate: SHA-256 byte-identical comparison between
  scripts/<name>.py  (legacy surface, backward-compat entrypoint)
and
  src/sop/scripts/<name>.py  (installed package surface)

Any intentional divergence must be:
  1. Documented in docs/MIGRATION.md under the "Script Surface Exemptions" section.
  2. Exempted here with a narrowly scoped pytest.skip() carrying a justification
     string referencing the docs/MIGRATION.md entry.

Do NOT weaken the whole guard (e.g., do not convert this module to a warning).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

# Repository root is two levels above this file: tests/ -> repo root
REPO_ROOT = Path(__file__).parent.parent

SCRIPTS_DIR = REPO_ROOT / "scripts"
PKG_SCRIPTS_DIR = REPO_ROOT / "src" / "sop" / "scripts"

# All scripts that must remain byte-identical across both surfaces.
# Phase 0 = original four hard-gate scripts.
# Extended coverage = all other paired surfaces that were found drifted after
# the ruff auto-fix pass and are now synced (added 2026-03-28).
# If a future intentional divergence is needed, add a narrow exemption below
# (see EXEMPTIONS dict) and document it in docs/MIGRATION.md.
PHASE_0_SCRIPTS = [
    # Phase 0 originals
    "startup_codex_helper.py",
    "run_loop_cycle.py",
    "validate_loop_closure.py",
    "supervise_loop.py",
    # Extended coverage
    "__init__.py",
    "aggregate_worker_status.py",
    "auditor_calibration_report.py",
    "build_exec_memory_packet.py",
    "evaluate_context_compaction_trigger.py",
    "generate_ceo_go_signal.py",
    "loop_cycle_runtime.py",
    "measure_context_reduction.py",
    "print_takeover_entrypoint.py",
    "run_fast_checks.py",
    "validate_ceo_weekly_summary_truth.py",
    "validate_exec_memory_truth.py",
    "validate_extension_allowlist.py",
    "validate_routing_matrix.py",
    "validate_skill_activation.py",
    "validate_skill_manifest.py",
    "validate_skill_registry.py",
    # Phase 1.1 -- Worker / Role Abstraction (D-183 dual-surface)
    "worker_base.py",
    "worker_role.py",
    "auditor_role.py",
    "planner_role.py",
    # Phase 1.2 -- Skill Mapping utils (D-183 dual-surface)
    "utils/skill_resolver.py",
    # Phase 2.2 -- PhaseGate (D-183 dual-surface)
    "phase_gate.py",
    # Phase 2.3 -- Orchestrator layer (D-183 dual-surface)
    "step_executor.py",
    "orchestrator.py",
    # Phase 3.1 -- RollbackManager (D-183 dual-surface)
    "rollback_manager.py",
    # Phase 4.1 -- BridgeContractWriter (D-183 dual-surface)
    "bridge_contract_writer.py",
    # Phase 4.2 -- PlannerPacketWriter (D-183 dual-surface)
    "planner_packet_writer.py",
    # Phase 4.3 -- OrchestratorStateWriter (D-183 dual-surface)
    "orchestrator_state_writer.py",
    # Phase 5.2 -- TierAwareCompactor (D-183 dual-surface)
    "tier_aware_compactor.py",
    # Phase 5.3 -- ArtifactLifecycleManager (D-183 dual-surface)
    "artifact_lifecycle_manager.py",
]

# Exemption registry.  Key = script name, value = justification string.
# Only add entries here when docs/MIGRATION.md has been updated.
EXEMPTIONS: dict[str, str] = {
    # Example (do not uncomment without a MIGRATION.md entry):
    # "some_script.py": "D-NNN: intentional API change documented in docs/MIGRATION.md §Script Surface Exemptions",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("script_name", PHASE_0_SCRIPTS)
def test_script_surface_byte_identical(script_name: str) -> None:
    """scripts/<name>.py and src/sop/scripts/<name>.py must be byte-identical.

    This is the Phase 0 drift detector.  pytest -m parity does NOT cover this
    because dev mode resolves scripts/ directly; only this test catches drift
    between the two surfaces.
    """
    if script_name in EXEMPTIONS:
        pytest.skip(
            f"Exempted: {EXEMPTIONS[script_name]}  "
            "(see docs/MIGRATION.md \u00a7Script Surface Exemptions)"
        )

    legacy_path = SCRIPTS_DIR / script_name
    pkg_path = PKG_SCRIPTS_DIR / script_name

    assert legacy_path.exists(), (
        f"Legacy script missing: {legacy_path}\n"
        f"Either add it or remove '{script_name}' from PHASE_0_SCRIPTS."
    )
    assert pkg_path.exists(), (
        f"Package script missing: {pkg_path}\n"
        f"Either add it or remove '{script_name}' from PHASE_0_SCRIPTS."
    )

    legacy_hash = _sha256(legacy_path)
    pkg_hash = _sha256(pkg_path)

    assert legacy_hash == pkg_hash, (
        f"Script surface drift detected for '{script_name}':\n"
        f"  scripts/{script_name}          SHA-256: {legacy_hash}\n"
        f"  src/sop/scripts/{script_name}  SHA-256: {pkg_hash}\n"
        "\n"
        "To fix: copy the authoritative version to the other location so both "
        "files are byte-identical.\n"
        "If divergence is intentional, document it in docs/MIGRATION.md "
        "(\u00a7Script Surface Exemptions) and add a narrow exemption entry to "
        "EXEMPTIONS in this file."
    )
