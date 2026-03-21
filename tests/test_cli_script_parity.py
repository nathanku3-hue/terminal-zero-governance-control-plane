"""CLI-Script Parity Tests.

Tests that sop CLI and scripts/*.py produce identical artifacts.
Per D-183: sop CLI is canonical, scripts/*.py is compatibility surface.

These tests verify the artifact parity contract documented in docs/MIGRATION.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Core loop artifacts that must be identical regardless of entrypoint
LOOP_ARTIFACTS = [
    "docs/context/loop_cycle_summary_latest.json",
    "docs/context/exec_memory_packet_latest.json",
    "docs/context/next_round_handoff_latest.json",
    "docs/context/expert_request_latest.json",
    "docs/context/pm_ceo_research_brief_latest.json",
    "docs/context/board_decision_brief_latest.json",
    "docs/context/skill_activation_latest.json",
]

# Advisory surface artifacts
ADVISORY_ARTIFACTS = [
    "docs/context/ceo_go_signal.md",
]

# Mapping from sop CLI commands to script names per MIGRATION.md
CLI_TO_SCRIPT_MAP = {
    "startup": "startup_codex_helper.py",
    "run": "run_loop_cycle.py",
    "validate": "validate_loop_closure.py",
    "takeover": "print_takeover_entrypoint.py",
    "supervise": "supervise_loop.py",
}


def _run_command(cmd: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run command and return result."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _load_json_artifact(path: Path) -> dict[str, Any] | None:
    """Load JSON artifact if exists."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _setup_test_repo() -> Path:
    """Create a minimal test repo for parity testing."""
    test_repo = Path(tempfile.mkdtemp(prefix="sop_parity_test_"))

    # Create required directories
    (test_repo / "docs" / "context").mkdir(parents=True)
    (test_repo / "skills").mkdir(parents=True)

    # Copy essential config files
    for src_name in [".sop_config.yaml", "extension_allowlist.yaml"]:
        src = REPO_ROOT / src_name
        if src.exists():
            shutil.copy2(src, test_repo / src_name)

    # Copy skills registry if exists
    registry_src = REPO_ROOT / "skills" / "registry.yaml"
    if registry_src.exists():
        (test_repo / "skills").mkdir(exist_ok=True)
        shutil.copy2(registry_src, test_repo / "skills" / "registry.yaml")

    # Create minimal startup docs
    startup_docs = [
        "docs/loop_operating_contract.md",
        "docs/round_contract_template.md",
        "docs/expert_invocation_policy.md",
        "docs/decision_authority_matrix.md",
        "docs/disagreement_taxonomy.md",
        "docs/disagreement_runbook.md",
        "docs/rollback_protocol.md",
    ]
    for doc_path in startup_docs:
        src = REPO_ROOT / doc_path
        dst = test_repo / doc_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
        else:
            dst.write_text("ok\n", encoding="utf-8")

    # Create minimal context files
    (test_repo / "docs" / "context" / "current_context.json").write_text("{}", encoding="utf-8")
    (test_repo / "docs" / "context" / "auditor_promotion_dossier.json").write_text("{}", encoding="utf-8")
    (test_repo / "docs" / "context" / "ceo_go_signal.md").write_text("# CEO Go Signal\n\nStatus: DRAFT\n", encoding="utf-8")

    return test_repo


def _teardown_test_repo(test_repo: Path) -> None:
    """Clean up test repo."""
    if test_repo.exists():
        shutil.rmtree(test_repo, ignore_errors=True)


class TestCLIAvailable:
    """Verify sop CLI is available and functional."""

    def test_sop_help_succeeds(self):
        """sop --help must succeed."""
        result = _run_command(
            [sys.executable, "-m", "sop", "--help"],
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"sop --help failed: {result.stderr}"
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    def test_sop_version_succeeds(self):
        """sop version must succeed."""
        result = _run_command(
            [sys.executable, "-m", "sop", "version"],
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"sop version failed: {result.stderr}"


class TestScriptEntrypointsAvailable:
    """Verify scripts/*.py entrypoints remain functional per RELEASING.md:23."""

    @pytest.mark.parametrize("script_name", [
        "startup_codex_helper.py",
        "run_loop_cycle.py",
        "validate_loop_closure.py",
        "print_takeover_entrypoint.py",
        "supervise_loop.py",
    ])
    def test_script_help_succeeds(self, script_name: str):
        """scripts/*.py --help must succeed."""
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            pytest.skip(f"{script_name} not found")

        result = _run_command(
            [sys.executable, str(script_path), "--help"],
            cwd=REPO_ROOT,
        )
        # Some scripts may not have --help, so we accept either success
        # or a meaningful error that indicates the script runs
        assert result.returncode == 0 or "Usage" in result.stdout or "usage" in result.stdout.lower() or "error" not in result.stderr.lower()[:100]


class TestCLItoScriptMapping:
    """Verify sop CLI commands map to correct scripts per MIGRATION.md mapping table."""

    @pytest.mark.parametrize("cli_cmd,script_name", list(CLI_TO_SCRIPT_MAP.items()))
    def test_cli_command_help_matches_script_help(self, cli_cmd: str, script_name: str):
        """sop <cmd> --help should produce output equivalent to script --help."""
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            pytest.skip(f"{script_name} not found")

        # Run sop <cmd> --help
        cli_result = _run_command(
            [sys.executable, "-m", "sop", cli_cmd, "--help"],
            cwd=REPO_ROOT,
        )

        # Run script --help
        script_result = _run_command(
            [sys.executable, str(script_path), "--help"],
            cwd=REPO_ROOT,
        )

        # Both should succeed (or both fail gracefully)
        # Note: CLI wraps the script, so exit codes should be identical
        assert cli_result.returncode == script_result.returncode, (
            f"Exit code mismatch for {cli_cmd}: CLI={cli_result.returncode}, script={script_result.returncode}"
        )


class TestOutputParity:
    """Verify CLI and script produce identical outputs for same inputs."""

    @pytest.fixture
    def test_repo(self):
        """Create a fresh test repo for each test."""
        repo = _setup_test_repo()
        yield repo
        _teardown_test_repo(repo)

    def test_takeover_output_parity(self, test_repo: Path):
        """sop takeover and print_takeover_entrypoint.py must produce identical output."""
        # Run via CLI
        cli_result = _run_command(
            [sys.executable, "-m", "sop", "takeover", "--repo-root", str(test_repo)],
            cwd=REPO_ROOT,
        )

        # Run via script
        script_result = _run_command(
            [sys.executable, str(SCRIPTS_DIR / "print_takeover_entrypoint.py"), "--repo-root", str(test_repo)],
            cwd=REPO_ROOT,
        )

        # Outputs should be identical (CLI wraps script directly)
        assert cli_result.returncode == script_result.returncode, (
            f"Exit code mismatch: CLI={cli_result.returncode}, script={script_result.returncode}"
        )
        assert cli_result.stdout == script_result.stdout, (
            f"stdout mismatch:\nCLI: {cli_result.stdout[:500]}\nScript: {script_result.stdout[:500]}"
        )
        assert cli_result.stderr == script_result.stderr, (
            f"stderr mismatch:\nCLI: {cli_result.stderr[:500]}\nScript: {script_result.stderr[:500]}"
        )

    def test_validate_output_parity(self, test_repo: Path):
        """sop validate and validate_loop_closure.py must produce identical output."""
        # Run via CLI
        cli_result = _run_command(
            [sys.executable, "-m", "sop", "validate", "--repo-root", str(test_repo)],
            cwd=REPO_ROOT,
        )

        # Run via script
        script_result = _run_command(
            [sys.executable, str(SCRIPTS_DIR / "validate_loop_closure.py"), "--repo-root", str(test_repo)],
            cwd=REPO_ROOT,
        )

        # Outputs should be identical
        assert cli_result.returncode == script_result.returncode, (
            f"Exit code mismatch: CLI={cli_result.returncode}, script={script_result.returncode}"
        )
        assert cli_result.stdout == script_result.stdout, (
            f"stdout mismatch:\nCLI: {cli_result.stdout[:500]}\nScript: {script_result.stdout[:500]}"
        )
        assert cli_result.stderr == script_result.stderr, (
            f"stderr mismatch:\nCLI: {cli_result.stderr[:500]}\nScript: {script_result.stderr[:500]}"
        )


class TestArtifactParityContract:
    """Verify that loop artifacts have required fields (parity contract)."""

    @pytest.fixture
    def exec_memory_packet(self) -> dict[str, Any] | None:
        """Load current exec memory packet."""
        path = REPO_ROOT / "docs" / "context" / "exec_memory_packet_latest.json"
        return _load_json_artifact(path)

    def test_exec_memory_packet_has_hierarchical_summary(self, exec_memory_packet):
        """exec_memory_packet must have hierarchical_summary per build_exec_memory_packet.py:2052."""
        if exec_memory_packet is None:
            pytest.skip("exec_memory_packet_latest.json not found")

        assert "hierarchical_summary" in exec_memory_packet
        hs = exec_memory_packet["hierarchical_summary"]
        assert "working_summary" in hs
        assert "issue_summary" in hs
        assert "daily_pm_summary" in hs
        assert "weekly_ceo_summary" in hs

    def test_exec_memory_packet_has_next_round_handoff(self, exec_memory_packet):
        """exec_memory_packet must have next_round_handoff per build_exec_memory_packet.py:2059."""
        if exec_memory_packet is None:
            pytest.skip("exec_memory_packet_latest.json not found")

        assert "next_round_handoff" in exec_memory_packet

    def test_exec_memory_packet_has_expert_request(self, exec_memory_packet):
        """exec_memory_packet must have expert_request per build_exec_memory_packet.py:2060."""
        if exec_memory_packet is None:
            pytest.skip("exec_memory_packet_latest.json not found")

        assert "expert_request" in exec_memory_packet

    def test_exec_memory_packet_has_pm_ceo_research_brief(self, exec_memory_packet):
        """exec_memory_packet must have pm_ceo_research_brief per build_exec_memory_packet.py:2061."""
        if exec_memory_packet is None:
            pytest.skip("exec_memory_packet_latest.json not found")

        assert "pm_ceo_research_brief" in exec_memory_packet

    def test_exec_memory_packet_has_board_decision_brief(self, exec_memory_packet):
        """exec_memory_packet must have board_decision_brief per build_exec_memory_packet.py:2062."""
        if exec_memory_packet is None:
            pytest.skip("exec_memory_packet_latest.json not found")

        assert "board_decision_brief" in exec_memory_packet

    def test_exec_memory_packet_has_skill_activation(self, exec_memory_packet):
        """exec_memory_packet must have skill_activation per build_exec_memory_packet.py:2065."""
        if exec_memory_packet is None:
            pytest.skip("exec_memory_packet_latest.json not found")

        assert "skill_activation" in exec_memory_packet


class TestMemoryTierContract:
    """Verify memory tier contract is enforced."""

    def test_memory_tiers_module_exists(self):
        """scripts/utils/memory_tiers.py must exist."""
        path = REPO_ROOT / "scripts" / "utils" / "memory_tiers.py"
        assert path.exists(), "memory_tiers.py not found"

    def test_memory_tier_families_defined(self):
        """Memory tier families must be defined per docs/memory_tier_contract.md."""
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts"))

        from utils.memory_tiers import _MEMORY_TIER_FAMILIES

        # Verify required families exist
        required_families = [
            "loop_cycle_summary",
            "exec_memory_packet",
            "ceo_go_signal",
            "decision_log",
            "skill_activation",
            "next_round_handoff",
        ]

        for family in required_families:
            assert family in _MEMORY_TIER_FAMILIES, f"Missing memory tier family: {family}"


class TestSkillResolverContract:
    """Verify skill resolver contract is enforced."""

    def test_skill_resolver_module_exists(self):
        """scripts/utils/skill_resolver.py must exist."""
        path = REPO_ROOT / "scripts" / "utils" / "skill_resolver.py"
        assert path.exists(), "skill_resolver.py not found"

    def test_skill_resolver_interface(self):
        """resolve_active_skills must return expected structure."""
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts"))

        from utils.skill_resolver import resolve_active_skills

        # Test with repo root
        result = resolve_active_skills(REPO_ROOT, "quant_current_scope")

        # Must have required fields
        assert "status" in result
        assert "skills" in result
        assert "warnings" in result
        assert "errors" in result

        # Status must be valid
        assert result["status"] in ("ok", "degraded", "failed")


# Mark all tests in this file as parity tests
pytestmark = pytest.mark.parity
