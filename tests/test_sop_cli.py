"""Tests for sop CLI."""

import subprocess
import sys
from pathlib import Path

import pytest


CLI_ROOT = Path(__file__).parent.parent / "src" / "sop"


class TestSopCLI:
    """Test the unified sop CLI."""

    def test_help_no_subcommand(self):
        """sop --help shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "startup" in result.stdout
        assert "run" in result.stdout
        assert "validate" in result.stdout
        assert "takeover" in result.stdout
        assert "supervise" in result.stdout
        assert "ops" in result.stdout
        assert "init" in result.stdout

    def test_version(self):
        """sop version prints version."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "version"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "sop" in result.stdout
        assert "0.2" in result.stdout

    def test_startup_help(self):
        """sop startup --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "startup", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "--repo-root" in result.stdout

    def test_run_help(self):
        """sop run --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "run", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "--repo-root" in result.stdout
        assert "--skip-phase-end" in result.stdout

    def test_validate_help(self):
        """sop validate --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "validate", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "--repo-root" in result.stdout

    def test_takeover_help(self):
        """sop takeover --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "takeover", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "--repo-root" in result.stdout

    def test_supervise_help(self):
        """sop supervise --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "supervise", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "--max-cycles" in result.stdout

    def test_init_help(self):
        """sop init --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "init", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "target_dir" in result.stdout
        assert "--minimal" in result.stdout
    def test_ops_help(self):
        """sop ops --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "ops", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "nightly-audit" in result.stdout

    def test_ops_nightly_audit_help(self):
        """sop ops nightly-audit --help works."""
        result = subprocess.run(
            [sys.executable, "-m", "sop", "ops", "nightly-audit", "--help"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )
        assert result.returncode == 0
        assert "--repo-root" in result.stdout
        assert "--format" in result.stdout


class TestSopInit:
    """Test sop init command."""

    def test_init_creates_structure(self, tmp_path):
        """sop init creates expected directory structure."""
        target = tmp_path / "new-project"

        result = subprocess.run(
            [sys.executable, "-m", "sop", "init", str(target)],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )

        assert result.returncode == 0
        assert target.exists()
        assert (target / "docs" / "context").exists()
        assert (target / "docs" / "templates").exists()
        assert (target / ".sop" / "config.yaml").exists()
        assert (target / "README.md").exists()
        assert (target / ".gitignore").exists()

    def test_init_fails_if_exists(self, tmp_path):
        """sop init fails if target directory exists."""
        target = tmp_path / "existing"
        target.mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "sop", "init", str(target)],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )

        assert result.returncode == 1
        assert "already exists" in result.stderr

    def test_init_minimal(self, tmp_path):
        """sop init --minimal skips templates."""
        target = tmp_path / "minimal-project"

        result = subprocess.run(
            [sys.executable, "-m", "sop", "init", str(target), "--minimal"],
            capture_output=True,
            text=True,
            cwd=CLI_ROOT.parent.parent,
        )

        assert result.returncode == 0
        assert target.exists()
        assert (target / "docs" / "context").exists()
        # minimal should not copy templates
        assert not (target / "docs" / "templates").exists()
        assert (target / ".sop" / "config.yaml").exists()
