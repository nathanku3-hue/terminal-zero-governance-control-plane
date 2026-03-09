from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_parallel_fanin.py"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run(context_dir: Path, manifest_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT_PATH), "--context-dir", str(context_dir)]
    if manifest_path is not None:
        command.extend(["--manifest-json", str(manifest_path)])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_passes_when_manifest_missing(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"

    result = _run(context_dir)

    assert result.returncode == 0
    assert "no active parallel shards" in (result.stdout + result.stderr).lower()


def test_passes_for_valid_non_overlapping_manifest(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    manifest = context_dir / "parallel_shard_manifest_latest.json"
    _write_json(
        manifest,
        [
            {
                "shard_id": "backend",
                "owned_files": ["src/api/a.py", "src/api/b.py"],
                "status": "PASS",
                "evidence_ok": True,
            },
            {
                "shard_id": "frontend",
                "owned_files": ["src/ui/a.tsx"],
                "status": "PASS",
                "evidence_ok": True,
            },
        ],
    )

    result = _run(context_dir)

    assert result.returncode == 0
    assert "gate passed" in (result.stdout + result.stderr).lower()


def test_fails_when_owned_files_overlap(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    manifest = context_dir / "parallel_shard_manifest_latest.json"
    _write_json(
        manifest,
        [
            {
                "shard_id": "shard_a",
                "owned_files": ["shared/file.py"],
                "status": "PASS",
                "evidence_ok": True,
            },
            {
                "shard_id": "shard_b",
                "owned_files": ["shared/file.py"],
                "status": "PASS",
                "evidence_ok": True,
            },
        ],
    )

    result = _run(context_dir)

    assert result.returncode == 1
    assert "Overlap:" in (result.stdout + result.stderr)


def test_fails_when_shard_not_pass_or_evidence_missing(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    manifest = context_dir / "parallel_shard_manifest_latest.json"
    _write_json(
        manifest,
        [
            {
                "shard_id": "backend",
                "owned_files": ["src/api/a.py"],
                "status": "HOLD",
                "evidence_ok": True,
            },
            {
                "shard_id": "frontend",
                "owned_files": ["src/ui/a.tsx"],
                "status": "PASS",
                "evidence_ok": False,
            },
        ],
    )

    result = _run(context_dir)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "status=HOLD" in combined
    assert "evidence_ok=false" in combined


def test_returns_exit_2_for_invalid_manifest_schema(tmp_path: Path) -> None:
    context_dir = tmp_path / "docs" / "context"
    manifest = context_dir / "parallel_shard_manifest_latest.json"
    _write_json(manifest, {"not": "a list"})

    result = _run(context_dir)

    assert result.returncode == 2
    assert "Manifest root must be a list" in (result.stdout + result.stderr)
