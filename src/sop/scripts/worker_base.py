"""worker_base.py

Phase 1 — Item 1.1: Worker / Role Abstraction

Defines the Worker ABC, WorkerSkill, and WorkerResult dataclasses that form
the role abstraction layer for the SOP loop cycle.

All role-specific logic lives in concrete subclasses (worker_role.py,
auditor_role.py, planner_role.py).  This module has zero runtime side effects
on import.
"""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


@dataclass
class WorkerSkill:
    """Resolved skill descriptor injected into a Worker at instantiation time.

    Fields mirror the Phase 0 skill-activation artifact shape so that
    WorkerSkill instances can be built directly from resolve_skills_for_role()
    output without a conversion step.
    """

    name: str
    version: str
    risk_level: str
    approval_decision_id: str
    applicable_projects: list[str]


@dataclass
class WorkerResult:
    """Structured result emitted by Worker.run().

    Mirrors the Phase 0 artifact schemas:
    - loop_cycle_summary  → steps + final_result
    - worker_reply_packet → role + status + exit_code + artifacts
    """

    role: str
    status: str  # PASS | HOLD | FAIL | ERROR
    exit_code: int
    steps: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class Worker(ABC):
    """Abstract base class for all loop-cycle roles.

    Concrete subclasses must implement `role` (property) and `run()`.  Skills
    are injected at construction time so that unit tests can supply arbitrary
    skill lists without touching disk.
    """

    def __init__(self, repo_root: Path, skills: list[WorkerSkill]) -> None:
        self._repo_root = repo_root
        self._skills: list[WorkerSkill] = list(skills)

    @property
    @abstractmethod
    def role(self) -> str:
        """Return the role identifier string (e.g. 'worker', 'auditor')."""
        ...

    @abstractmethod
    def run(self, context: Any) -> WorkerResult:
        """Execute role logic and return a structured result.

        Args:
            context: LoopCycleContext (typed as Any to avoid circular imports).

        Returns:
            WorkerResult with role, status, exit_code, steps, artifacts, errors.
        """
        ...

    def skill_names(self) -> list[str]:
        """Return names of all injected skills."""
        return [s.name for s in self._skills]
