from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

from scripts.build_context_packet import PACKET_KEYS
from scripts.build_context_packet import build_context_packet
from scripts.build_context_packet import render_context_markdown


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_context_packet.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_repo_fixture(root: Path, *, include_locked: bool) -> Path:
    repo = root / "repo"
    _write(
        repo / "docs/phase_brief/phase7-brief.md",
        "\n".join(
            [
                "# Phase 7 Brief",
                "",
                "## Status",
                "- Active",
            ]
        ),
    )

    handover_lines = [
        "# Phase 7 Handover",
        "",
        "## New Context Packet",
        "- What was done:",
        "  - Implemented context bootstrap.",
    ]
    if include_locked:
        handover_lines.extend(
            [
                "- What is locked:",
                "  - Schema key order is fixed.",
            ]
        )
    handover_lines.extend(
        [
            "- What remains:",
            "  - Add CI smoke command.",
            "- Immediate first step: .venv\\Scripts\\python scripts/build_context_packet.py",
            "- Next-phase roadmap summary:",
            "  - Add context packet smoke check in CI.",
            "",
            "ConfirmationRequired: YES",
        ]
    )
    _write(repo / "docs/handover/phase7_handover.md", "\n".join(handover_lines))
    _write(repo / "docs/decision log.md", "Decision Log\n")
    _write(repo / "docs/lessonss.md", "Lessons\n")
    _write(
        repo / "top_level_PM.md",
        "\n".join(
            [
                "# Top Level PM",
                "",
                "## 6. Theory of Constraints",
                "- Constraint-first optimization.",
                "",
                "## 7. Cynefin Framework",
                "- Domain-aware decisions.",
                "",
                "## 8. Ergodicity and Survival",
                "- Survival before growth.",
            ]
        ),
    )
    return repo


def test_successful_generation_in_temp_repo_fixture(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    json_out = repo / "docs/context/current_context.json"
    md_out = repo / "docs/context/current_context.md"
    gemini_out = repo / "docs/handover/gemini/phase7_gemini_handover.md"
    assert json_out.exists()
    assert md_out.exists()
    assert gemini_out.exists()

    packet = json.loads(json_out.read_text(encoding="utf-8"))
    assert packet["active_phase"] == 7
    assert packet["what_was_done"] == ["Implemented context bootstrap."]

    markdown = md_out.read_text(encoding="utf-8")
    headers = [line.strip() for line in markdown.splitlines() if line.startswith("## ")]
    assert headers == [
        "## What Was Done",
        "## What Is Locked",
        "## What Is Next",
        "## First Command",
    ]
    gemini_text = gemini_out.read_text(encoding="utf-8")
    assert "## Top Level PM" in gemini_text
    assert "## Source Context Files" in gemini_text


def test_missing_required_section_returns_non_zero(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=False)

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "missing required sections" in result.stderr.lower()


def test_schema_keys_present_and_first_command_non_empty(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    assert tuple(packet.keys()) == PACKET_KEYS
    assert str(packet["first_command"]).strip()


def test_active_phase_prefers_selected_context_source(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    _write(
        repo / "docs/phase_brief/phase99-brief.md",
        "\n".join(
            [
                "# Phase 99 Brief",
                "",
                "## Status",
                "- Placeholder high-number brief.",
            ]
        ),
    )
    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert int(packet["active_phase"]) == 7


def test_markdown_first_command_uses_fenced_block_when_backticks_present() -> None:
    packet = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_files": ["docs/handover/phase20_handover.md"],
        "active_phase": 20,
        "what_was_done": ["Done"],
        "what_is_locked": ["Locked"],
        "what_is_next": ["Next"],
        "first_command": "Fix in `tests/test_x.py` then rerun.",
        "next_todos": ["Todo"],
    }
    markdown = render_context_markdown(packet)
    assert "## First Command" in markdown
    assert "```text" in markdown


def test_validate_mode_passes_after_build_and_fails_when_missing(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    build = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr

    validate = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stderr

    (repo / "docs/context/current_context.md").unlink()
    validate_missing = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate_missing.returncode != 0
    assert "missing context markdown artifact" in validate_missing.stderr.lower()


def test_parser_accepts_markdown_style_new_context_packet(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "docs/phase_brief/phase8-brief.md", "# Phase 8 Brief\n")
    _write(
        repo / "docs/handover/phase8_handover.md",
        "\n".join(
            [
                "# Phase 8 Handover",
                "",
                "## New Context Packet",
                "## What Was Done",
                "- Completed A",
                "## What Is Locked",
                "- Locked B",
                "## What Is Next",
                "- Do C",
                "## First Command",
                "```text",
                ".venv\\Scripts\\python scripts/build_context_packet.py",
                "```",
                "## Confirmation",
                "ConfirmationRequired: YES",
            ]
        ),
    )
    _write(repo / "docs/decision log.md", "Decision Log\n")
    _write(repo / "docs/lessonss.md", "Lessons\n")
    _write(
        repo / "top_level_PM.md",
        "\n".join(
            [
                "# Top Level PM",
                "## 6. Theory of Constraints",
                "- x",
                "## 7. Cynefin Framework",
                "- y",
                "## 8. Ergodicity",
                "- z",
            ]
        ),
    )

    packet = build_context_packet(
        repo_root=repo,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    assert packet["what_was_done"] == ["Completed A"]
    assert packet["what_is_locked"] == ["Locked B"]
    assert packet["what_is_next"] == ["Do C"]
    assert str(packet["first_command"]).strip() == ".venv\\Scripts\\python scripts/build_context_packet.py"


def test_validate_mode_fails_on_markdown_json_drift(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    build = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr

    md_path = repo / "docs/context/current_context.md"
    drifted = md_path.read_text(encoding="utf-8").replace("Implemented context bootstrap.", "Drifted text.")
    md_path.write_text(drifted, encoding="utf-8")

    validate = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode != 0
    assert "markdown artifact drifted" in validate.stderr.lower()


def test_validate_mode_fails_on_gemini_handover_drift(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    build = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr

    gemini_path = repo / "docs/handover/gemini/phase7_gemini_handover.md"
    drifted = gemini_path.read_text(encoding="utf-8").replace("## Top Level PM", "## Top Level PM Drift")
    gemini_path.write_text(drifted, encoding="utf-8")

    validate = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode != 0
    assert "gemini handover artifact drifted" in validate.stderr.lower()


def test_missing_top_level_pm_returns_non_zero(tmp_path: Path) -> None:
    repo = _make_repo_fixture(tmp_path, include_locked=True)
    (repo / "top_level_PM.md").unlink()

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo-root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "missing required top level pm file" in result.stderr.lower()
