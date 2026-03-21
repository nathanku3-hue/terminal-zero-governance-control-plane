from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

try:
    from sop.scripts.loop_cycle_context import LoopCycleContext
except ModuleNotFoundError:
    # Fallback for direct script execution (development mode)
    from scripts.loop_cycle_context import LoopCycleContext


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime) -> str:
    """Convert datetime to ISO 8601 UTC string."""
    return dt.isoformat()


def _atomic_write_text(path: Path, content: str) -> None:
    """Write text to a file atomically using a temporary file."""
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, text=True)
    try:
        with open(temp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(temp_path).replace(path)
    except Exception:
        Path(temp_path).unlink(missing_ok=True)
        raise


def _write_lessons_stubs(context_dir: Path, generated_at_utc: str) -> dict[str, Path]:
    """Write lessons stub files for worker and auditor."""
    worker_path = context_dir / "lessons_worker_latest.md"
    auditor_path = context_dir / "lessons_auditor_latest.md"

    worker_stub = "\n".join(
        [
            "# Worker Lessons Stub",
            "",
            f"- GeneratedAtUTC: {generated_at_utc}",
            "- Cycle: latest loop run",
            "",
            "## Prompt",
            "1. What delivery decision had the highest impact this cycle?",
            "2. What caused avoidable rework and how will you prevent it next cycle?",
            "3. Which evidence artifact was missing or weak and needs automation?",
            "4. What should be stopped, started, and continued next cycle?",
            "",
            "## Notes",
            "- Fill with concrete examples and artifact paths.",
            "",
        ]
    )
    auditor_stub = "\n".join(
        [
            "# Auditor Lessons Stub",
            "",
            f"- GeneratedAtUTC: {generated_at_utc}",
            "- Cycle: latest loop run",
            "",
            "## Prompt",
            "1. Which gate caught the highest-risk issue this cycle?",
            "2. Which check produced noise or false positives and why?",
            "3. What additional guardrail or threshold change is needed?",
            "4. Which unresolved risk needs explicit CEO/PM follow-up next cycle?",
            "",
            "## Notes",
            "- Include rule IDs, artifact paths, and concrete follow-up actions.",
            "",
        ]
    )

    _atomic_write_text(worker_path, worker_stub)
    _atomic_write_text(auditor_path, auditor_stub)
    return {"worker": worker_path, "auditor": auditor_path}


@dataclass
class LoopCycleRuntime:
    """Mutable runtime state for loop cycle execution.

    This dataclass holds all state that changes during loop execution:
    - steps: accumulates execution records
    - exec_memory_cycle_ready: set to True after successful exec memory promotion
    - generated_at/generated_at_utc: timestamp for this cycle
    - temp_summary_path: intermediate summary file
    - lessons_paths: written on initialization
    - Advisory artifacts: populated conditionally after exec memory promotion
    - repo_root_convenience: populated conditionally

    NOT frozen - fields are mutable by design.
    """

    # Timestamp
    generated_at: datetime
    generated_at_utc: str

    # Execution tracking
    steps: list[dict[str, Any]] = field(default_factory=list)
    exec_memory_cycle_ready: bool = False

    # Paths
    temp_summary_path: Path = field(default=None)
    lessons_paths: dict[str, Path] = field(default_factory=dict)

    # Advisory artifacts (populated conditionally)
    next_round_handoff_artifacts: dict[str, Any] | None = None
    expert_request_artifacts: dict[str, Any] | None = None
    pm_ceo_research_brief_artifacts: dict[str, Any] | None = None
    board_decision_brief_artifacts: dict[str, Any] | None = None
    skill_activation_artifacts: dict[str, Any] | None = None

    # Convenience paths
    repo_root_convenience: dict[str, Path] | None = None


def build_loop_cycle_runtime(ctx: LoopCycleContext) -> LoopCycleRuntime:
    """Factory function to build runtime state from context.

    Initializes:
    - Timestamp (generated_at, generated_at_utc)
    - Empty steps list
    - exec_memory_cycle_ready = False
    - temp_summary_path derived from context_dir
    - lessons_paths written on init
    - Advisory artifacts set to None
    - repo_root_convenience set to None
    """
    generated_at = _utc_now()
    generated_at_utc = _utc_iso(generated_at)

    lessons_paths = _write_lessons_stubs(
        context_dir=ctx.context_dir,
        generated_at_utc=generated_at_utc,
    )

    temp_summary_path = ctx.context_dir / "loop_cycle_summary_current.json"

    return LoopCycleRuntime(
        generated_at=generated_at,
        generated_at_utc=generated_at_utc,
        steps=[],
        exec_memory_cycle_ready=False,
        temp_summary_path=temp_summary_path,
        lessons_paths=lessons_paths,
        next_round_handoff_artifacts=None,
        expert_request_artifacts=None,
        pm_ceo_research_brief_artifacts=None,
        board_decision_brief_artifacts=None,
        repo_root_convenience=None,
    )
