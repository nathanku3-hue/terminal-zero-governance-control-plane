from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_profile_selection_ranking.py"
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_script(
    *,
    repo_root: Path | None = None,
    corpus_dir: Path,
    output_json: Path,
    output_md: Path,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT_PATH)]
    if repo_root is not None:
        command.extend(["--repo-root", str(repo_root)])
    command.extend(
        [
            "--corpus-dir",
            str(corpus_dir),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def test_profile_selection_ranking_happy_path(tmp_path: Path) -> None:
    repo_root = tmp_path
    corpus_dir = Path("docs/context/profile_outcomes_corpus")
    output_json = Path("docs/context/profile_selection_ranking_latest.json")
    output_md = Path("docs/context/profile_selection_ranking_latest.md")

    _write_json(
        repo_root / corpus_dir / "cycle_a.json",
        [
            {"project_profile": "quant_default", "shipped": True, "ready": True},
            {"project_profile": "quant_default", "shipped": "yes", "ready": "pass"},
            {
                "project_profile": "data_platform",
                "shipped": True,
                "ready": False,
                "board_reentry_required": True,
            },
        ],
    )
    _write_json(
        repo_root / corpus_dir / "cycle_b.json",
        {
            "records": [
                {"project_profile": "data_platform", "shipped": True, "ready": True},
                {
                    "project_profile": "general_software",
                    "shipped": True,
                    "ready": True,
                    "board_reentry_required": True,
                    "unknown_domain_triggered": True,
                },
                {"project_profile": "general_software", "shipped": False, "ready": False},
            ]
        },
    )

    result = _run_script(
        repo_root=repo_root,
        corpus_dir=corpus_dir,
        output_json=output_json,
        output_md=output_md,
    )
    output_json_path = repo_root / output_json
    output_md_path = repo_root / output_md
    assert result.returncode == 0, result.stdout + result.stderr
    assert output_json_path.exists()
    assert output_md_path.exists()

    payload = json.loads(output_json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "RANKED"
    assert payload["advisory_only"] is True
    assert payload["control_plane_impact"] == "none"
    assert payload["recommended_profile"] == "quant_default"
    assert payload["score"] == 90.0
    assert payload["confidence"] == 0.9
    assert payload["evidence_summary"].startswith("Top profile quant_default")
    assert payload["ranking"] == payload["profile_rankings"]
    assert payload["scoring"]["formula"].startswith("score_0_100")
    assert payload["corpus"]["files_scanned"] == 2
    assert payload["corpus"]["records_used"] == 6
    assert payload["corpus"]["records_malformed"] == 0

    rankings = payload["profile_rankings"]
    assert [row["project_profile"] for row in rankings] == [
        "quant_default",
        "data_platform",
        "general_software",
    ]
    assert rankings[0]["score"] == 90.0
    assert rankings[1]["score"] == 69.0
    assert rankings[2]["score"] == 40.0

    md_text = output_md_path.read_text(encoding="utf-8")
    assert "# Profile Selection Ranking (Advisory)" in md_text
    assert "## Ranking" in md_text
    assert "RECOMMENDED_PROFILE: quant_default" in md_text


def test_profile_selection_ranking_empty_corpus(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "docs/context/profile_outcomes_corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    output_json = tmp_path / "docs/context/profile_selection_ranking_latest.json"
    output_md = tmp_path / "docs/context/profile_selection_ranking_latest.md"

    result = _run_script(
        corpus_dir=corpus_dir,
        output_json=output_json,
        output_md=output_md,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["status"] == "NO_DATA"
    assert payload["recommended_profile"] is None
    assert payload["profile_rankings"] == []
    assert payload["corpus"]["files_scanned"] == 0
    assert payload["corpus"]["records_used"] == 0
    assert payload["corpus"]["records_malformed"] == 0

    md_text = output_md.read_text(encoding="utf-8")
    assert "No valid profile outcome records were found." in md_text
    assert "PROFILE_SELECTION_STATUS: NO_DATA" in md_text


def test_profile_selection_ranking_handles_malformed_records(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "docs/context/profile_outcomes_corpus"
    output_json = tmp_path / "docs/context/profile_selection_ranking_latest.json"
    output_md = tmp_path / "docs/context/profile_selection_ranking_latest.md"

    _write_json(
        corpus_dir / "valid_and_invalid_records.json",
        [
            {"project_profile": "quant_default", "shipped": True, "ready": True},
            {"shipped": True, "ready": True},
        ],
    )
    malformed_file = corpus_dir / "broken_payload.json"
    malformed_file.parent.mkdir(parents=True, exist_ok=True)
    malformed_file.write_text("{not-valid-json", encoding="utf-8")

    result = _run_script(
        corpus_dir=corpus_dir,
        output_json=output_json,
        output_md=output_md,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["status"] == "RANKED"
    assert payload["recommended_profile"] == "quant_default"
    assert payload["corpus"]["files_scanned"] == 2
    assert payload["corpus"]["files_loaded"] == 1
    assert payload["corpus"]["malformed_files"] == ["broken_payload.json"]
    assert payload["corpus"]["records_total"] == 2
    assert payload["corpus"]["records_used"] == 1
    assert payload["corpus"]["records_malformed"] == 1

    ranking = payload["profile_rankings"]
    assert len(ranking) == 1
    assert ranking[0]["project_profile"] == "quant_default"
    assert ranking[0]["score"] == 90.0

    md_text = output_md.read_text(encoding="utf-8")
    assert "## Malformed Files" in md_text
    assert "`broken_payload.json`" in md_text
