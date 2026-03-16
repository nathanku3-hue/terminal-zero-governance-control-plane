"""Tests for skill activation resolver and validation.

Phase 5B.2: Thin Skill-Activation Bridge
"""

import json
import tempfile
from pathlib import Path

import pytest

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from scripts.utils.skill_resolver import resolve_active_skills
from scripts.validate_skill_activation import validate_skill_activation


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create .sop_config.yaml
        sop_config = {
            "project_name": "test_project",
            "guardrail_strength": "tight",
            "active_skills": ["test-skill"],
            "disabled_skills": []
        }
        (repo_root / ".sop_config.yaml").write_text(yaml.dump(sop_config))

        # Create extension_allowlist.yaml
        allowlist = {
            "schema_version": "1.0.0",
            "last_updated": "2026-03-13",
            "skills": [
                {
                    "skill_name": "test-skill",
                    "version": "1.0.0",
                    "approved_by": "PM/CEO",
                    "approval_decision_id": "D-001",
                    "approval_date": "2026-03-13",
                    "status": "active",
                    "risk_level": "LOW",
                    "applicable_projects": ["all"]
                },
                {
                    "skill_name": "deprecated-skill",
                    "version": "1.0.0",
                    "approved_by": "PM/CEO",
                    "approval_decision_id": "D-002",
                    "approval_date": "2026-03-13",
                    "status": "deprecated",
                    "risk_level": "LOW",
                    "applicable_projects": ["all"]
                },
                {
                    "skill_name": "project-specific-skill",
                    "version": "1.0.0",
                    "approved_by": "PM/CEO",
                    "approval_decision_id": "D-003",
                    "approval_date": "2026-03-13",
                    "status": "active",
                    "risk_level": "MEDIUM",
                    "applicable_projects": ["other_project"]
                }
            ]
        }
        (repo_root / "extension_allowlist.yaml").write_text(yaml.dump(allowlist))

        # Create skills/registry.yaml
        skills_dir = repo_root / "skills"
        skills_dir.mkdir()
        registry = {
            "schema_version": "1.0.0",
            "last_updated": "2026-03-13",
            "skills": [
                {
                    "name": "test-skill",
                    "version": "1.0.0",
                    "category": "testing",
                    "description": "Test skill for unit tests",
                    "author": "Test Team",
                    "approval_status": "active",
                    "approval_decision_id": "D-001"
                }
            ]
        }
        (skills_dir / "registry.yaml").write_text(yaml.dump(registry))

        # Create skill manifest
        skill_dir = skills_dir / "test_skill"
        skill_dir.mkdir()
        skill_manifest = {
            "schema_version": "1.0.0",
            "name": "test-skill",
            "version": "1.0.0",
            "category": "testing",
            "description": "Test skill"
        }
        (skill_dir / "skill.yaml").write_text(yaml.dump(skill_manifest))

        yield repo_root


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_resolve_active_skills_success(temp_repo):
    """Test successful skill resolution."""
    result = resolve_active_skills(temp_repo, "test_project")

    assert result["status"] == "ok"
    assert len(result["skills"]) == 1
    assert result["skills"][0]["name"] == "test-skill"
    assert result["skills"][0]["version"] == "1.0.0"
    assert result["skills"][0]["status"] == "active"
    assert result["skills"][0]["manifest_path"] == "skills/test_skill/skill.yaml"
    assert result["skills"][0]["category"] == "testing"
    assert result["skills"][0]["approval_decision_id"] == "D-001"
    assert result["skills"][0]["risk_level"] == "LOW"
    assert len(result["warnings"]) == 0
    assert len(result["errors"]) == 0


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_resolve_active_skills_deprecated(temp_repo):
    """Test that deprecated skills are filtered out with warning."""
    # Add deprecated skill to active_skills
    sop_config = yaml.safe_load((temp_repo / ".sop_config.yaml").read_text())
    sop_config["active_skills"].append("deprecated-skill")
    (temp_repo / ".sop_config.yaml").write_text(yaml.dump(sop_config))

    result = resolve_active_skills(temp_repo, "test_project")

    assert result["status"] == "degraded"
    assert len(result["skills"]) == 1  # Only test-skill
    assert len(result["warnings"]) == 1
    assert "deprecated-skill" in result["warnings"][0]
    assert "deprecated" in result["warnings"][0]


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_resolve_active_skills_wrong_project(temp_repo):
    """Test that project-specific skills are filtered out."""
    # Add project-specific skill to active_skills
    sop_config = yaml.safe_load((temp_repo / ".sop_config.yaml").read_text())
    sop_config["active_skills"].append("project-specific-skill")
    (temp_repo / ".sop_config.yaml").write_text(yaml.dump(sop_config))

    result = resolve_active_skills(temp_repo, "test_project")

    assert result["status"] == "degraded"
    assert len(result["skills"]) == 1  # Only test-skill
    assert len(result["warnings"]) == 1
    assert "project-specific-skill" in result["warnings"][0]
    assert "not applicable" in result["warnings"][0]


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_resolve_active_skills_not_in_allowlist(temp_repo):
    """Test that skills not in allowlist are filtered out."""
    # Add non-existent skill to active_skills
    sop_config = yaml.safe_load((temp_repo / ".sop_config.yaml").read_text())
    sop_config["active_skills"].append("non-existent-skill")
    (temp_repo / ".sop_config.yaml").write_text(yaml.dump(sop_config))

    result = resolve_active_skills(temp_repo, "test_project")

    assert result["status"] == "degraded"
    assert len(result["skills"]) == 1  # Only test-skill
    assert len(result["warnings"]) == 1
    assert "non-existent-skill" in result["warnings"][0]
    assert "not in global allowlist" in result["warnings"][0]


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_resolve_active_skills_missing_config(temp_repo):
    """Test fail-soft behavior when config is missing."""
    (temp_repo / ".sop_config.yaml").unlink()

    result = resolve_active_skills(temp_repo, "test_project")

    assert result["status"] == "failed"
    assert len(result["skills"]) == 0
    assert len(result["errors"]) > 0


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_validate_skill_activation_success(temp_repo):
    """Test successful validation of skill_activation artifact."""
    # Create skill_activation_latest.json
    skill_activation = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-13T12:00:00Z",
        "source_exec_memory_json": "docs/context/exec_memory_packet_latest.json",
        "skill_activation": {
            "status": "ok",
            "skills": [
                {
                    "name": "test-skill",
                    "version": "1.0.0",
                    "status": "active",
                    "manifest_path": "skills/test_skill/skill.yaml",
                    "category": "testing",
                    "description": "Test skill for unit tests",
                    "approval_decision_id": "D-001",
                    "risk_level": "LOW"
                }
            ],
            "warnings": [],
            "errors": []
        }
    }

    skill_activation_path = temp_repo / "skill_activation_latest.json"
    skill_activation_path.write_text(json.dumps(skill_activation, indent=2))

    is_valid, errors = validate_skill_activation(skill_activation_path, temp_repo)

    assert is_valid
    assert len(errors) == 0


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_validate_skill_activation_missing_file(temp_repo):
    """Test validation fails when file is missing."""
    skill_activation_path = temp_repo / "skill_activation_latest.json"

    is_valid, errors = validate_skill_activation(skill_activation_path, temp_repo)

    assert not is_valid
    assert len(errors) > 0


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_validate_skill_activation_invalid_status(temp_repo):
    """Test validation fails with invalid status."""
    skill_activation = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-13T12:00:00Z",
        "source_exec_memory_json": "docs/context/exec_memory_packet_latest.json",
        "skill_activation": {
            "status": "invalid_status",
            "skills": [],
            "warnings": [],
            "errors": []
        }
    }

    skill_activation_path = temp_repo / "skill_activation_latest.json"
    skill_activation_path.write_text(json.dumps(skill_activation, indent=2))

    is_valid, errors = validate_skill_activation(skill_activation_path, temp_repo)

    assert not is_valid
    assert any("Invalid status" in error for error in errors)


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
def test_validate_skill_activation_version_mismatch(temp_repo):
    """Test validation fails when skill version doesn't match allowlist."""
    skill_activation = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-13T12:00:00Z",
        "source_exec_memory_json": "docs/context/exec_memory_packet_latest.json",
        "skill_activation": {
            "status": "ok",
            "skills": [
                {
                    "name": "test-skill",
                    "version": "2.0.0",  # Wrong version
                    "status": "active",
                    "manifest_path": "skills/test_skill/skill.yaml",
                    "category": "testing",
                    "description": "Test skill",
                    "approval_decision_id": "D-001",
                    "risk_level": "LOW"
                }
            ],
            "warnings": [],
            "errors": []
        }
    }

    skill_activation_path = temp_repo / "skill_activation_latest.json"
    skill_activation_path.write_text(json.dumps(skill_activation, indent=2))

    is_valid, errors = validate_skill_activation(skill_activation_path, temp_repo)

    assert not is_valid
    assert any("version mismatch" in error for error in errors)
