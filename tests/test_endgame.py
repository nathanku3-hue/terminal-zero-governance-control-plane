"""Phase 7.2 -- Endgame closure tests.

6 tests:
  test_planner_packet_is_sole_entry_point
  test_bridge_contract_written_after_every_run
  test_context_count_within_max_artifacts_limit
  test_truth_vocabulary_consistent_with_kernel_matrix
  test_no_orphaned_artifacts_in_context_dir
  test_final_release_commands_all_pass
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_DIR = REPO_ROOT / "docs" / "context"
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_memory_tier_families() -> dict:
    """Import _MEMORY_TIER_FAMILIES from the canonical location."""
    candidates = [
        REPO_ROOT / "src" / "sop" / "scripts" / "utils" / "memory_tiers.py",
        REPO_ROOT / "scripts" / "utils" / "memory_tiers.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location("memory_tiers", path)
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod._MEMORY_TIER_FAMILIES  # type: ignore[attr-defined]
    pytest.skip("memory_tiers.py not found")


def _known_filenames(families: dict) -> set:
    names: set[str] = set()
    for fam in families.values():
        for p in fam["artifact_paths"]:
            names.add(Path(p).name)
    return names


# ---------------------------------------------------------------------------
# Test 1 -- planner packet is registered as sole entry point
# ---------------------------------------------------------------------------

def test_planner_packet_is_sole_entry_point() -> None:
    """planner_packet family must be registered in _MEMORY_TIER_FAMILIES.

    The planner packet is the sole entry point for the planning loop.
    Its presence in the tier registry guarantees it is written after every
    run and is never pruned as an orphan.
    """
    families = _load_memory_tier_families()
    assert "planner_packet" in families, (
        "planner_packet family missing from _MEMORY_TIER_FAMILIES -- "
        "planner cannot enter from a small packet"
    )
    pp = families["planner_packet"]
    paths = list(pp["artifact_paths"])
    md_paths = [p for p in paths if p.endswith(".md")]
    assert md_paths, "planner_packet family must have at least one .md artifact path"
    assert pp["tier"] == "warm", (
        f"planner_packet tier should be 'warm', got '{pp['tier']}'"
    )


# ---------------------------------------------------------------------------
# Test 2 -- bridge contract is registered as a derived output written every run
# ---------------------------------------------------------------------------

def test_bridge_contract_written_after_every_run() -> None:
    """bridge_contract family must be registered as a derived output.

    BridgeContractWriter is called unconditionally in orchestrator.run_single(),
    including on HOLD. This test verifies the registry entry is consistent
    with that guarantee.
    """
    families = _load_memory_tier_families()
    assert "bridge_contract" in families, (
        "bridge_contract family missing from _MEMORY_TIER_FAMILIES"
    )
    bc = families["bridge_contract"]
    assert bc["access"] == "derived_output", (
        f"bridge_contract access should be 'derived_output', got '{bc['access']}'"
    )
    paths = list(bc["artifact_paths"])
    json_paths = [p for p in paths if p.endswith(".json")]
    md_paths = [p for p in paths if p.endswith(".md")]
    assert json_paths, "bridge_contract must have a .json artifact path"
    assert md_paths, "bridge_contract must have a .md artifact path"


# ---------------------------------------------------------------------------
# Test 3 -- context count check (warns above default limit)
# ---------------------------------------------------------------------------

def test_context_count_within_max_artifacts_limit() -> None:
    """docs/context/ file count must not silently exceed 2x the default limit.

    The default max_context_artifacts is 50 (LoopCycleContext).
    check_context_overflow() emits CONTEXT_OVERFLOW to stderr but does not
    block. This test warns when above 2x threshold so the operator knows
    pruning is needed.
    """
    if not CONTEXT_DIR.exists():
        pytest.skip("docs/context/ does not exist -- no prior loop run")

    default_max = 50
    files = [
        f for f in CONTEXT_DIR.iterdir()
        if f.is_file() and not f.name.startswith(".tmp_")
    ]
    count = len(files)
    print(f"\ndocs/context/ artifact count: {count} (default limit: {default_max})")

    assert count <= default_max * 2, (
        f"docs/context/ has {count} artifacts -- "
        f"more than 2x the default limit ({default_max}). "
        "Run with --prune to archive orphaned artifacts."
    )


# ---------------------------------------------------------------------------
# Test 4 -- truth vocabulary consistent with KERNEL_ACTIVATION_MATRIX
# ---------------------------------------------------------------------------

def test_truth_vocabulary_consistent_with_kernel_matrix() -> None:
    """Canonical vocabulary terms must be present in _MEMORY_TIER_FAMILIES
    and referenced in KERNEL_ACTIVATION_MATRIX.md.
    """
    families = _load_memory_tier_families()
    required_families = [
        "bridge_contract",
        "planner_packet",
        "orchestrator_state",
        "exec_memory_packet",
    ]
    for name in required_families:
        assert name in families, (
            f"'{name}' missing from _MEMORY_TIER_FAMILIES -- vocabulary drift"
        )

    # Locate KERNEL_ACTIVATION_MATRIX.md (above repo root)
    kernel_matrix: Path | None = None
    for candidate in [
        REPO_ROOT.parent.parent / "KERNEL_ACTIVATION_MATRIX.md",
        REPO_ROOT.parent / "KERNEL_ACTIVATION_MATRIX.md",
        REPO_ROOT / "KERNEL_ACTIVATION_MATRIX.md",
    ]:
        if candidate.exists():
            kernel_matrix = candidate
            break
    if kernel_matrix is None:
        pytest.skip("KERNEL_ACTIVATION_MATRIX.md not found")

    content = kernel_matrix.read_text(encoding="utf-8")
    for term in ["Bridge Contract", "Planner Packet"]:
        assert term in content, (
            f"'{term}' not found in KERNEL_ACTIVATION_MATRIX.md -- vocabulary drift"
        )

    # Also check SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md if reachable
    spec_checklist = Path(__file__).resolve().parent.parent.parent / "SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md"
    if spec_checklist.exists():
        spec_content = spec_checklist.read_text(encoding="utf-8")
        for term in ["bridge", "planner"]:
            assert term.lower() in spec_content.lower(), (
                f"'{term}' not found in SPEC_TO_MULTISTREAM_EXECUTION_CHECKLIST.md"
            )


# ---------------------------------------------------------------------------
# Test 5 -- no orphaned artifacts in clean fixture dir (integration)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_no_orphaned_artifacts_in_context_dir(tmp_path: Path) -> None:
    """ArtifactLifecycleManager must find no orphaned artifacts in a clean fixture dir.

    Uses an isolated tmp_path populated with only registered artifact names.
    Does NOT scan the live docs/context/ directory.
    """
    # Load ArtifactLifecycleManager dynamically
    candidates = [
        REPO_ROOT / "src" / "sop" / "scripts" / "artifact_lifecycle_manager.py",
        REPO_ROOT / "scripts" / "artifact_lifecycle_manager.py",
    ]
    mgr_path = next((p for p in candidates if p.exists()), None)
    if mgr_path is None:
        pytest.skip("artifact_lifecycle_manager.py not found")

    spec = importlib.util.spec_from_file_location("artifact_lifecycle_manager", mgr_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    # Register in sys.modules before exec so @dataclass works on Python 3.14
    sys.modules.setdefault("artifact_lifecycle_manager", mod)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception:
        sys.modules.pop("artifact_lifecycle_manager", None)
        raise
    ArtifactLifecycleManager = mod.ArtifactLifecycleManager  # type: ignore[attr-defined]

    families = _load_memory_tier_families()

    # Populate fixture dir with only known-registered filenames
    fixture_dir = tmp_path / "context"
    fixture_dir.mkdir()
    known = _known_filenames(families)
    for name in list(known)[:5]:
        (fixture_dir / name).write_text("{}", encoding="utf-8")

    mgr = ArtifactLifecycleManager(fixture_dir, families)
    result = mgr.scan()

    assert result.orphaned == [], (
        f"Expected no orphaned artifacts in clean fixture dir, got: {result.orphaned}"
    )
    assert len(result.active) > 0, "Expected at least some active artifacts in fixture dir"


# ---------------------------------------------------------------------------
# Test 6 -- final release commands all pass (integration)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_final_release_commands_all_pass() -> None:
    """All 6 release freeze commands must exit 0.

    Command 4 (run_fast_checks) may return HOLD which is exit 0 per plan.
    Command 5 (pytest -q) is not re-run here to avoid recursion.
    """
    # Ensure supervisor-required artifact exists (may be absent after test isolation cleanup).
    _loop_summary = CONTEXT_DIR / "loop_cycle_summary_latest.json"
    _stub = '{"final_result": "NOT_READY", "phase": "phase-8-stub"}\n'
    _had_content: str | None = None
    if _loop_summary.exists():
        _had_content = _loop_summary.read_text(encoding="utf-8")
    else:
        _loop_summary.write_text(_stub, encoding="utf-8")

    python = sys.executable

    commands_and_labels = [
        (
            [python, str(SCRIPTS_DIR / "startup_codex_helper.py"), "--help"],
            "startup_codex_helper --help",
        ),
        (
            [python, str(SCRIPTS_DIR / "run_loop_cycle.py"), "--help"],
            "run_loop_cycle --help",
        ),
        (
            [python, str(SCRIPTS_DIR / "supervise_loop.py"), "--max-cycles", "1"],
            "supervise_loop --max-cycles 1",
        ),
        (
            [python, str(SCRIPTS_DIR / "run_fast_checks.py"), "--repo-root", str(REPO_ROOT)],
            "run_fast_checks --repo-root .",
        ),
        (
            [
                python,
                str(SCRIPTS_DIR / "validate_routing_matrix.py"),
                str(REPO_ROOT / "benchmark" / "subagent_routing_matrix.yaml"),
                str(REPO_ROOT),
            ],
            "validate_routing_matrix benchmark/subagent_routing_matrix.yaml .",
        ),
    ]

    try:
        for cmd, label in commands_and_labels:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=60,
            )
            assert proc.returncode == 0, (
                f"Release command '{label}' exited {proc.returncode}.\n"
                f"stdout: {proc.stdout[-500:]}\n"
                f"stderr: {proc.stderr[-500:]}"
            )
    finally:
        # Restore loop_cycle_summary_latest.json to its pre-test state.
        if _had_content is None:
            _loop_summary.unlink(missing_ok=True)
        else:
            _loop_summary.write_text(_had_content, encoding="utf-8")
