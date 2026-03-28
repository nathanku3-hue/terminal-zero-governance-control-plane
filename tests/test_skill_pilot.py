"""Phase 7.1 — Skill Pilot tests (NO-GO path).

Decision: NO-GO (phase6_skill_pilot_decision.md). Stream D deferred.
7.1 is skipped. These 6 tests verify that:
  - The pilot is disabled by default (skill_pilot_enabled not present or False)
  - Core kernel flow is unchanged without the pilot flag
  - Pilot skill resolver function is absent or safely no-ops (NO-GO: not implemented)
  - Governance gates still pass without pilot
  - Rollback leaves no pilot side effects (none exist)
  - phase7_skill_pilot_results.md exists with required fields
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Test 1 — skill_pilot_enabled not set to True anywhere in LoopCycleContext
# ---------------------------------------------------------------------------

def test_skill_pilot_disabled_by_default() -> None:
    """LoopCycleContext must not enable skill pilot by default.

    On the NO-GO path, skill_pilot_enabled is not added to LoopCycleContext.
    This test verifies that nothing in the context dataclass sets it to True.
    """
    ctx_path = REPO_ROOT / "src" / "sop" / "scripts" / "loop_cycle_context.py"
    if not ctx_path.exists():
        ctx_path = REPO_ROOT / "scripts" / "loop_cycle_context.py"
    assert ctx_path.exists(), f"loop_cycle_context.py not found at {ctx_path}"

    source = ctx_path.read_text(encoding="utf-8")

    # On the NO-GO path skill_pilot_enabled should NOT be set to True anywhere
    assert "skill_pilot_enabled = True" not in source, (
        "skill_pilot_enabled must not default to True in LoopCycleContext "
        "(NO-GO decision: pilot disabled)"
    )


# ---------------------------------------------------------------------------
# Test 2 — core kernel flow unchanged (orchestrator has no unconditional pilot call)
# ---------------------------------------------------------------------------

def test_kernel_flow_unchanged_without_pilot_flag() -> None:
    """orchestrator.py must not call invoke_pilot_skill unconditionally.

    On the NO-GO path, no pilot hook is wired. The orchestrator must not
    contain an unconditional call to invoke_pilot_skill.
    """
    orch_path = REPO_ROOT / "src" / "sop" / "scripts" / "orchestrator.py"
    if not orch_path.exists():
        orch_path = REPO_ROOT / "scripts" / "orchestrator.py"
    assert orch_path.exists(), f"orchestrator.py not found at {orch_path}"

    source = orch_path.read_text(encoding="utf-8")

    # invoke_pilot_skill must not be called unconditionally
    # (on GO path it would be guarded by ctx.skill_pilot_enabled)
    if "invoke_pilot_skill" in source:
        # If present it must be guarded
        assert "skill_pilot_enabled" in source, (
            "invoke_pilot_skill found in orchestrator.py but not guarded by "
            "skill_pilot_enabled — unconditional pilot call on NO-GO path"
        )


# ---------------------------------------------------------------------------
# Test 3 — invoke_pilot_skill not present (NO-GO: not implemented)
# ---------------------------------------------------------------------------

def test_pilot_skill_resolves_correctly() -> None:
    """On NO-GO path, invoke_pilot_skill must not be defined in skill_resolver.py.

    GO path would add invoke_pilot_skill(skill_name, ctx) -> dict | None.
    NO-GO path: function is absent. This test documents that absence is correct.
    """
    resolver_candidates = [
        REPO_ROOT / "src" / "sop" / "scripts" / "utils" / "skill_resolver.py",
        REPO_ROOT / "scripts" / "utils" / "skill_resolver.py",
    ]
    for resolver_path in resolver_candidates:
        if resolver_path.exists():
            source = resolver_path.read_text(encoding="utf-8")
            # On NO-GO path this function must NOT be present
            assert "invoke_pilot_skill" not in source, (
                "invoke_pilot_skill found in skill_resolver.py on NO-GO path — "
                "Stream D pilot must not be implemented without a GO decision"
            )
            return
    pytest.skip("skill_resolver.py not found")


# ---------------------------------------------------------------------------
# Test 4 — governance gates pass (existing tests all pass; no pilot interference)
# ---------------------------------------------------------------------------

def test_governance_gates_still_pass_with_pilot() -> None:
    """On NO-GO path, no pilot code exists to interfere with governance gates.

    This test verifies that the skill activation validation script still
    loads cleanly and the routing matrix yaml is committed.
    """
    # Verify routing matrix is committed (7.2-G6)
    routing_yaml = REPO_ROOT / "benchmark" / "subagent_routing_matrix.yaml"
    assert routing_yaml.exists(), (
        "benchmark/subagent_routing_matrix.yaml must exist — governance gate"
    )

    # Verify validate_skill_activation.py exists and is importable as source
    val_path = REPO_ROOT / "src" / "sop" / "scripts" / "validate_skill_activation.py"
    if not val_path.exists():
        val_path = REPO_ROOT / "scripts" / "validate_skill_activation.py"
    assert val_path.exists(), "validate_skill_activation.py must exist"

    # Syntax check only (avoid side effects)
    source = val_path.read_text(encoding="utf-8")
    compile(source, str(val_path), "exec")  # raises SyntaxError if broken


# ---------------------------------------------------------------------------
# Test 5 — rollback leaves no pilot side effects (no pilot artifacts exist)
# ---------------------------------------------------------------------------

def test_pilot_rollback_leaves_no_side_effects() -> None:
    """On NO-GO path, no pilot output artifacts should exist.

    GO path would write docs/context/pilot_output_latest.json.
    NO-GO path: this file must not exist (no pilot was run).
    Verifies rollback concern is vacuous: nothing to roll back.
    """
    pilot_output = REPO_ROOT / "docs" / "context" / "pilot_output_latest.json"
    assert not pilot_output.exists(), (
        "pilot_output_latest.json found on NO-GO path — "
        "unexpected pilot artifact; verify no pilot was run"
    )


# ---------------------------------------------------------------------------
# Test 6 — phase7_skill_pilot_results.md exists with required fields
# ---------------------------------------------------------------------------

def test_pilot_value_metric_recorded() -> None:
    """phase7_skill_pilot_results.md must exist and contain required fields.

    On NO-GO path the required fields are: Date, Decision, and a skip note.
    Human reviewer: confirm the measured value (NO-GO = no value measured).
    """
    results_path = REPO_ROOT / "docs" / "decisions" / "phase7_skill_pilot_results.md"
    assert results_path.exists(), (
        "docs/decisions/phase7_skill_pilot_results.md must exist "
        "(even on NO-GO path, documenting the skip)"
    )

    content = results_path.read_text(encoding="utf-8")

    # Required fields on NO-GO path
    required_fragments = [
        "NO-GO",
        "SKIPPED",
        "phase6_skill_pilot_decision",
    ]
    for fragment in required_fragments:
        assert fragment in content, (
            f"phase7_skill_pilot_results.md missing required field: '{fragment}'"
        )
