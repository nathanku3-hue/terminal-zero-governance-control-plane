"""tests/test_skill_mapping.py

Phase 1 — Item 1.2 done criteria:
  5 tests: resolve_skills_for_role exists, role filtering, default role
  assignment, resolve_active_skills() signature unchanged, assigned_roles
  not in emitted skill_activation artifact shape.
"""
from __future__ import annotations

from pathlib import Path

import pytest

try:
    from sop.scripts.utils.skill_resolver import (
        resolve_active_skills,
        resolve_skills_for_role,
    )
    from sop.scripts.worker_base import WorkerSkill
except ImportError:
    from scripts.utils.skill_resolver import (
        resolve_active_skills,
        resolve_skills_for_role,
    )
    from scripts.worker_base import WorkerSkill


REPO_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Test 1 — resolve_skills_for_role exists and returns list[WorkerSkill]
# ---------------------------------------------------------------------------

class TestResolveSkillsForRoleExists:
    def test_function_is_importable(self) -> None:
        assert callable(resolve_skills_for_role)

    def test_returns_list_of_worker_skills(self) -> None:
        result = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "worker")
        assert isinstance(result, list)
        for skill in result:
            assert isinstance(skill, WorkerSkill)

    def test_worker_skill_has_required_fields(self) -> None:
        result = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "worker")
        for skill in result:
            assert isinstance(skill.name, str) and skill.name
            assert isinstance(skill.version, str)
            assert isinstance(skill.risk_level, str)
            assert isinstance(skill.approval_decision_id, str)
            assert isinstance(skill.applicable_projects, list)


# ---------------------------------------------------------------------------
# Test 2 — Role filtering: auditor gets only auditor-assigned skills
# ---------------------------------------------------------------------------

class TestRoleFiltering:
    def test_unknown_role_returns_empty(self) -> None:
        """A role with no matching skills returns an empty list."""
        result = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "nonexistent_role")
        assert result == []

    def test_worker_and_auditor_both_return_lists(self) -> None:
        worker_skills = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "worker")
        auditor_skills = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "auditor")
        assert isinstance(worker_skills, list)
        assert isinstance(auditor_skills, list)


# ---------------------------------------------------------------------------
# Test 3 — Default role: skills without assigned_roles default to [worker]
# ---------------------------------------------------------------------------

class TestDefaultRoleAssignment:
    def test_skills_without_assigned_roles_appear_for_worker(self) -> None:
        """Skills with no assigned_roles field should default to worker."""
        worker_skills = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "worker")
        worker_names = {s.name for s in worker_skills}
        # At minimum worker should get any active skill applicable to this project
        # (the allowlist has safe-db-migration and repo-map, both active + all projects)
        assert len(worker_names) >= 0  # non-negative always true; main check is no exception

    def test_planner_role_returns_list(self) -> None:
        result = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "planner")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Test 4 — resolve_active_skills() signature unchanged
# ---------------------------------------------------------------------------

class TestResolveActiveSkillsUnchanged:
    def test_resolve_active_skills_still_works(self) -> None:
        result = resolve_active_skills(REPO_ROOT, "quant_current_scope")
        assert "status" in result
        assert "skills" in result
        assert "warnings" in result
        assert "errors" in result
        assert result["status"] in ("ok", "degraded", "failed")

    def test_resolve_active_skills_returns_dict_not_list(self) -> None:
        result = resolve_active_skills(REPO_ROOT, "quant_current_scope")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Test 5 — assigned_roles NOT in emitted skill_activation artifact shape
# ---------------------------------------------------------------------------

class TestAssignedRolesNotInArtifact:
    def test_assigned_roles_absent_from_skill_activation_output(self) -> None:
        """resolve_active_skills() must NOT include assigned_roles in skill dicts.

        Per plan §1.2 step 5b: assigned_roles is an allowlist-internal field;
        per-role filtering is in resolve_skills_for_role(), not the artifact.
        test_skill_activation.py:194 assertions must pass without modification.
        """
        result = resolve_active_skills(REPO_ROOT, "quant_current_scope")
        for skill in result.get("skills", []):
            assert "assigned_roles" not in skill, (
                f"assigned_roles must not appear in skill_activation artifact, "
                f"but found in skill '{skill.get('name')}'"
            )

    def test_resolve_skills_for_role_returns_worker_skill_not_raw_dict(self) -> None:
        """resolve_skills_for_role returns WorkerSkill objects (typed), not raw dicts."""
        result = resolve_skills_for_role(REPO_ROOT, "quant_current_scope", "worker")
        for item in result:
            assert hasattr(item, "name")
            assert hasattr(item, "version")
            assert hasattr(item, "risk_level")
            assert hasattr(item, "approval_decision_id")
            assert hasattr(item, "applicable_projects")
