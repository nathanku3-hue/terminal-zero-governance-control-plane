from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_digest_freshness.py"
)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_digest(path: Path, generated_at: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# CEO Bridge Digest",
                "",
                f"Generated: {_iso_utc(generated_at)}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _run_validator(digest_path: Path, ttl_minutes: int) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--input",
        str(digest_path),
        "--ttl-minutes",
        str(ttl_minutes),
    ]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_validate_digest_freshness_passes_for_recent_digest(tmp_path: Path) -> None:
    digest_path = tmp_path / "ceo_bridge_digest.md"
    _write_digest(digest_path, datetime.now(timezone.utc))

    result = _run_validator(digest_path, ttl_minutes=60)
    assert result.returncode == 0, result.stdout + result.stderr


def test_validate_digest_freshness_fails_for_stale_digest(tmp_path: Path) -> None:
    digest_path = tmp_path / "ceo_bridge_digest.md"
    _write_digest(digest_path, datetime.now(timezone.utc) - timedelta(minutes=120))

    result = _run_validator(digest_path, ttl_minutes=60)
    assert result.returncode == 1
    assert "Digest STALE" in (result.stdout + result.stderr)


def test_validate_digest_freshness_fails_when_generated_timestamp_missing(
    tmp_path: Path,
) -> None:
    digest_path = tmp_path / "ceo_bridge_digest.md"
    digest_path.write_text(
        "\n".join(
            [
                "# CEO Bridge Digest",
                "",
                "Digest Version: 2.0.0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _run_validator(digest_path, ttl_minutes=60)
    assert result.returncode == 1
    assert "Could not find Generated timestamp" in (result.stdout + result.stderr)
