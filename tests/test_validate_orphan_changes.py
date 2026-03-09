from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_orphan_changes.py"
)


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _run_validator(
    traceability_path: Path,
    since_commit: str,
    *,
    include: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--traceability",
        str(traceability_path),
        "--since-commit",
        since_commit,
    ]
    for pattern in include or []:
        command.extend(["--include", pattern])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _init_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    _run_git(repo_root, "init")
    _run_git(repo_root, "config", "user.name", "Test User")
    _run_git(repo_root, "config", "user.email", "test@example.com")
    return repo_root


def test_validate_orphan_changes_passes_when_changed_files_are_mapped(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    traceability_path = repo_root / "pm_to_code_traceability.yaml"
    covered_file = repo_root / "scripts" / "covered.py"

    _write_text(covered_file, "print('v1')\n")
    _write_yaml(
        traceability_path,
        {
            "directives": [
                {
                    "directive_id": "D-COVERED",
                    "traceability": {
                        "code_diffs": [{"file": "scripts/covered.py"}],
                    },
                }
            ]
        },
    )

    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "baseline")
    since_commit = _run_git(repo_root, "rev-parse", "HEAD").stdout.strip()

    _write_text(covered_file, "print('v2')\n")

    result = _run_validator(traceability_path, since_commit, include=["*.py"])
    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_orphan_changes_fails_for_unmapped_changed_file(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    traceability_path = repo_root / "pm_to_code_traceability.yaml"
    covered_file = repo_root / "scripts" / "covered.py"
    orphan_file = repo_root / "scripts" / "orphan.py"

    _write_text(covered_file, "print('covered v1')\n")
    _write_text(orphan_file, "print('orphan v1')\n")
    _write_yaml(
        traceability_path,
        {
            "directives": [
                {
                    "directive_id": "D-COVERED",
                    "traceability": {
                        "code_diffs": [{"file": "scripts/covered.py"}],
                    },
                }
            ]
        },
    )

    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "baseline")
    since_commit = _run_git(repo_root, "rev-parse", "HEAD").stdout.strip()

    _write_text(orphan_file, "print('orphan v2')\n")

    result = _run_validator(traceability_path, since_commit, include=["*.py"])
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "unmapped orphan changes" in combined
    assert "scripts/orphan.py" in combined


def test_validate_orphan_changes_fails_on_git_command_failure(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    traceability_path = repo_root / "pm_to_code_traceability.yaml"

    _write_yaml(
        traceability_path,
        {"directives": []},
    )

    # Use an invalid commit hash to trigger git failure
    result = _run_validator(traceability_path, "invalid-commit-hash-xyz", include=["*.py"])
    assert result.returncode == 2  # INFRA_ERROR
    combined = result.stdout + result.stderr
    assert "Error running git diff" in combined
