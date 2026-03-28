"""planner_role.py

Phase 1 — Item 1.1: Concrete PlannerRole stub.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from sop.scripts.worker_base import Worker, WorkerResult, WorkerSkill
except ModuleNotFoundError:
    try:
        from scripts.worker_base import Worker, WorkerResult, WorkerSkill  # type: ignore[no-redef]
    except ModuleNotFoundError:
        from worker_base import Worker, WorkerResult, WorkerSkill  # type: ignore[no-redef]


class PlannerRole(Worker):
    """Concrete Worker implementation for the 'planner' role."""

    def __init__(self, repo_root: Path, skills: list[WorkerSkill]) -> None:
        super().__init__(repo_root=repo_root, skills=skills)

    @property
    def role(self) -> str:
        return "planner"

    def run(self, context: Any) -> WorkerResult:
        """Phase 1 stub — returns PASS immediately."""
        return WorkerResult(
            role=self.role,
            status="PASS",
            exit_code=0,
        )
