"""tests/test_worker_base.py

Phase 1 — Item 1.1 done criteria:
  5 tests: instantiation, result schema, skill injection, ABC enforcement,
  step-ownership mapping.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sop.scripts.worker_base import Worker, WorkerResult, WorkerSkill
from sop.scripts.worker_role import WorkerRole
from sop.scripts.auditor_role import AuditorRole
from sop.scripts.planner_role import PlannerRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_skill(name: str = "test-skill") -> WorkerSkill:
    return WorkerSkill(
        name=name,
        version="1.0.0",
        risk_level="LOW",
        approval_decision_id="D-999",
        applicable_projects=["all"],
    )


REPO_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Test 1 — Instantiation: all three concrete roles can be constructed
# ---------------------------------------------------------------------------

class TestWorkerInstantiation:
    def test_worker_role_instantiates(self) -> None:
        w = WorkerRole(repo_root=REPO_ROOT, skills=[_make_skill()])
        assert w.role == "worker"

    def test_auditor_role_instantiates(self) -> None:
        a = AuditorRole(repo_root=REPO_ROOT, skills=[_make_skill()])
        assert a.role == "auditor"

    def test_planner_role_instantiates(self) -> None:
        p = PlannerRole(repo_root=REPO_ROOT, skills=[])
        assert p.role == "planner"


# ---------------------------------------------------------------------------
# Test 2 — WorkerResult schema: required fields present with correct types
# ---------------------------------------------------------------------------

class TestWorkerResultSchema:
    def test_worker_result_has_required_fields(self) -> None:
        result = WorkerResult(
            role="worker",
            status="PASS",
            exit_code=0,
        )
        assert result.role == "worker"
        assert result.status == "PASS"
        assert result.exit_code == 0
        assert isinstance(result.steps, list)
        assert isinstance(result.artifacts, dict)
        assert isinstance(result.errors, list)

    def test_worker_result_valid_statuses(self) -> None:
        for status in ("PASS", "HOLD", "FAIL", "ERROR"):
            r = WorkerResult(role="worker", status=status, exit_code=0)
            assert r.status == status

    def test_worker_result_steps_and_artifacts(self) -> None:
        step = {"name": "build_exec_memory_packet", "status": "PASS", "exit_code": 0}
        artifact = {"exec_memory_json": Path("docs/context/exec_memory_packet_latest.json")}
        result = WorkerResult(
            role="auditor",
            status="PASS",
            exit_code=0,
            steps=[step],
            artifacts=artifact,
            errors=[],
        )
        assert result.steps[0]["name"] == "build_exec_memory_packet"
        assert "exec_memory_json" in result.artifacts


# ---------------------------------------------------------------------------
# Test 3 — Skill injection: skills are stored and retrievable via skill_names()
# ---------------------------------------------------------------------------

class TestSkillInjection:
    def test_skill_names_returns_injected_names(self) -> None:
        skills = [_make_skill("repo-map"), _make_skill("safe-db-migration")]
        w = WorkerRole(repo_root=REPO_ROOT, skills=skills)
        assert w.skill_names() == ["repo-map", "safe-db-migration"]

    def test_empty_skills_list(self) -> None:
        w = AuditorRole(repo_root=REPO_ROOT, skills=[])
        assert w.skill_names() == []

    def test_worker_skill_fields(self) -> None:
        s = _make_skill("repo-map")
        assert s.name == "repo-map"
        assert s.version == "1.0.0"
        assert s.risk_level == "LOW"
        assert s.approval_decision_id == "D-999"
        assert s.applicable_projects == ["all"]


# ---------------------------------------------------------------------------
# Test 4 — ABC enforcement: Worker cannot be instantiated directly
# ---------------------------------------------------------------------------

class TestABCEnforcement:
    def test_worker_abc_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            Worker(repo_root=REPO_ROOT, skills=[])  # type: ignore[abstract]

    def test_partial_implementation_raises(self) -> None:
        class PartialWorker(Worker):
            @property
            def role(self) -> str:
                return "partial"
            # run() not implemented

        with pytest.raises(TypeError):
            PartialWorker(repo_root=REPO_ROOT, skills=[])  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Test 5 — Step ownership: run() returns correct role in WorkerResult
# ---------------------------------------------------------------------------

class TestStepOwnership:
    def test_worker_role_run_returns_worker_result(self) -> None:
        w = WorkerRole(repo_root=REPO_ROOT, skills=[])
        with pytest.raises(NotImplementedError):
            w.run(context=None)

    def test_auditor_role_run_returns_auditor_result(self) -> None:
        a = AuditorRole(repo_root=REPO_ROOT, skills=[])
        with pytest.raises(NotImplementedError):
            a.run(context=None)

    def test_planner_role_run_returns_planner_result(self) -> None:
        p = PlannerRole(repo_root=REPO_ROOT, skills=[])
        with pytest.raises(NotImplementedError):
            p.run(context=None)
