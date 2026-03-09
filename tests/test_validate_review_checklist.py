from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "validate_review_checklist.py"
)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(input_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--input", str(input_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _valid_checklist() -> str:
    return "\n".join(
        [
            "# PR Review Checklist",
            "",
            "## Problem/Intent",
            "- PROBLEM_INTENT: Prevent loop closure from escalating with stale metrics.",
            "",
            "## Scope Boundaries",
            "- SCOPE_BOUNDARIES: Script-only validation gate; no runtime behavior changes.",
            "",
            "## Evidence/Tests",
            "- EVIDENCE_TESTS: python -m pytest tests/test_validate_review_checklist.py -q (pass).",
            "",
            "## Risks/Rollback",
            "- RISKS_ROLLBACK: Low risk; rollback by reverting validator and checklist usage.",
            "",
            "## Reviewer Decision",
            "- REVIEWER_DECISION: APPROVE",
            "",
        ]
    )


def test_passes_with_complete_checklist(tmp_path: Path) -> None:
    checklist = tmp_path / "pr_review_checklist.md"
    _write_text(checklist, _valid_checklist())

    result = _run(checklist)

    assert result.returncode == 0
    assert "validation passed" in (result.stdout + result.stderr).lower()


def test_fails_when_required_section_missing(tmp_path: Path) -> None:
    checklist = tmp_path / "pr_review_checklist.md"
    content = _valid_checklist().replace("## Risks/Rollback\n- RISKS_ROLLBACK: Low risk; rollback by reverting validator and checklist usage.\n\n", "")
    _write_text(checklist, content)

    result = _run(checklist)

    assert result.returncode == 1
    assert "Missing required section: Risks/Rollback" in (result.stdout + result.stderr)


def test_fails_when_required_field_placeholder(tmp_path: Path) -> None:
    checklist = tmp_path / "pr_review_checklist.md"
    content = _valid_checklist().replace(
        "- EVIDENCE_TESTS: python -m pytest tests/test_validate_review_checklist.py -q (pass).",
        "- EVIDENCE_TESTS: TODO(add test evidence)",
    )
    _write_text(checklist, content)

    result = _run(checklist)

    assert result.returncode == 1
    assert "Missing or placeholder field: EVIDENCE_TESTS" in (result.stdout + result.stderr)


def test_fails_when_reviewer_decision_is_not_explicit(tmp_path: Path) -> None:
    checklist = tmp_path / "pr_review_checklist.md"
    content = _valid_checklist().replace(
        "- REVIEWER_DECISION: APPROVE",
        "- REVIEWER_DECISION: MAYBE",
    )
    _write_text(checklist, content)

    result = _run(checklist)

    assert result.returncode == 1
    assert "Invalid REVIEWER_DECISION: MAYBE" in (result.stdout + result.stderr)


def test_returns_exit_2_when_input_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing_checklist.md"

    result = _run(missing)

    assert result.returncode == 2
    assert "Missing input file" in (result.stdout + result.stderr)
