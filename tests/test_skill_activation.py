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
from tests.test_skill_taxonomy import KNOWN_SKILL_CATEGORIES, KNOWN_RISK_LEVELS


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


# =============================================================================
# Phase 5B.2b: Skill Visibility and Trigger Coverage Tests
# =============================================================================
# These tests cover skill visibility, trigger predicates, and review sequence
# expectations WITHOUT execution semantics or new config shapes.
# Invariants: no new authority, no runtime hooks, no Phase 5C behavior.


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
class TestSkillVisibility:
    """Tests for skill visibility surface requirements."""

    def test_skill_visibility_includes_required_fields(self, temp_repo):
        """Active skills must expose name, version, category, description, risk_level."""
        result = resolve_active_skills(temp_repo, "test_project")

        assert result["status"] in ("ok", "degraded")
        if len(result["skills"]) > 0:
            skill = result["skills"][0]
            # Required visibility fields
            assert "name" in skill
            assert "version" in skill
            assert "category" in skill
            assert "description" in skill
            assert "risk_level" in skill
            assert "status" in skill
            assert "approval_decision_id" in skill

    def test_skill_visibility_category_taxonomy(self, temp_repo):
        """Skill categories must be from known taxonomy."""
        result = resolve_active_skills(temp_repo, "test_project")

        for skill in result["skills"]:
            # Category should be from known set or prefixed (extensibility)
            category = skill.get("category", "")
            assert category in KNOWN_SKILL_CATEGORIES or "." in category, \
                f"Unknown category '{category}' not in taxonomy"

    def test_skill_visibility_risk_level_taxonomy(self, temp_repo):
        """Risk levels must be from known taxonomy."""
        result = resolve_active_skills(temp_repo, "test_project")

        for skill in result["skills"]:
            risk_level = skill.get("risk_level", "")
            assert risk_level in KNOWN_RISK_LEVELS, \
                f"Unknown risk_level '{risk_level}' not in taxonomy"

    def test_skill_visibility_includes_approval_chain(self, temp_repo):
        """Active skills must show approval decision ID for traceability."""
        result = resolve_active_skills(temp_repo, "test_project")

        for skill in result["skills"]:
            assert "approval_decision_id" in skill
            assert skill["approval_decision_id"].startswith("D-"), \
                f"approval_decision_id must reference decision log"


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
class TestSkillTriggerPredicates:
    """Tests for skill trigger predicate expectations.

    These tests define WHEN a skill SHOULD be triggered based on task context.
    They do NOT execute skills - they only validate trigger expectations.
    """

    def test_database_skill_trigger_on_schema_change(self, temp_repo):
        """Database-category skills should trigger on schema change tasks."""
        result = resolve_active_skills(temp_repo, "test_project")

        # Find database-category skills
        db_skills = [s for s in result["skills"] if s.get("category") == "database"]

        # If database skill is active, it should have expected trigger context
        for skill in db_skills:
            # Trigger expectation: database skills trigger on schema operations
            # This is documentation-only - no execution
            assert "description" in skill
            # Description should hint at trigger context
            desc = skill["description"].lower()
            trigger_keywords = {"schema", "database", "migration", "table", "column"}
            has_trigger_hint = any(kw in desc for kw in trigger_keywords)
            assert has_trigger_hint, \
                f"Database skill '{skill['name']}' lacks trigger context in description"

    def test_skill_trigger_requires_active_status(self, temp_repo):
        """Only 'active' status skills should be triggerable."""
        result = resolve_active_skills(temp_repo, "test_project")

        for skill in result["skills"]:
            # Only active skills should appear in resolved list
            assert skill.get("status") == "active", \
                f"Non-active skill '{skill['name']}' in resolved skills"

    def test_skill_trigger_blocked_for_wrong_project(self, temp_repo):
        """Skills with project restrictions should not trigger for wrong project."""
        # Add project-specific skill to active_skills
        sop_config = yaml.safe_load((temp_repo / ".sop_config.yaml").read_text())
        sop_config["active_skills"].append("project-specific-skill")
        (temp_repo / ".sop_config.yaml").write_text(yaml.dump(sop_config))

        result = resolve_active_skills(temp_repo, "test_project")

        # project-specific-skill should NOT be in resolved skills
        skill_names = [s["name"] for s in result["skills"]]
        assert "project-specific-skill" not in skill_names
        # And there should be a warning about it
        assert any("project-specific-skill" in w for w in result["warnings"])


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not available")
class TestSkillReviewSequenceExpectations:
    """Tests for review sequence expectations tied to skills.

    These tests validate that skills carry enough context for the
    implementer -> spec compliance -> code quality -> continue/close
    review choreography documented in runbook_ops.md.
    """

    def test_skill_carries_approval_for_review_traceability(self, temp_repo):
        """Skills must carry approval_decision_id for review sequence traceability."""
        result = resolve_active_skills(temp_repo, "test_project")

        for skill in result["skills"]:
            # Review sequence requires approval chain visibility
            assert "approval_decision_id" in skill
            assert skill["approval_decision_id"], \
                f"Skill '{skill['name']}' missing approval_decision_id"

    def test_high_risk_skill_requires_explicit_review_notation(self, temp_repo):
        """HIGH-risk skills should have explicit risk_level for review routing."""
        result = resolve_active_skills(temp_repo, "test_project")

        high_risk_skills = [s for s in result["skills"] if s.get("risk_level") == "HIGH"]

        for skill in high_risk_skills:
            # HIGH-risk skills require additional review attention
            # This is visibility-only - no enforcement
            assert skill.get("risk_level") == "HIGH"
            assert "approval_decision_id" in skill
            # HIGH-risk should have CEO-level approval (D-xxx pattern in decision log)
            assert skill["approval_decision_id"].startswith("D-")

    def test_skill_manifest_path_resolvable(self, temp_repo):
        """Skill manifest_path must be resolvable for review inspection."""
        result = resolve_active_skills(temp_repo, "test_project")

        for skill in result["skills"]:
            manifest_path = skill.get("manifest_path")
            assert manifest_path, f"Skill '{skill['name']}' missing manifest_path"
            # Path should be relative and within skills/
            assert manifest_path.startswith("skills/"), \
                f"manifest_path '{manifest_path}' not in skills/ directory"

    def test_review_sequence_invariants_no_new_authority(self, temp_repo):
        """Verify skill resolution does not create new authority path.

        This test documents the invariant that skill resolution is
        advisory-only and does not override PM/CEO approval gates.
        """
        result = resolve_active_skills(temp_repo, "test_project")

        # Resolution result should be purely informational
        # It should not contain any enforcement or authority fields
        assert "authority" not in result
        assert "enforcement" not in result
        assert "override" not in result

        # Status reflects advisory nature
        assert result["status"] in ("ok", "degraded", "failed")
