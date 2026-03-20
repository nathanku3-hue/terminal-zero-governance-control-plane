from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


VALIDATOR_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_exec_memory_truth.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _past_utc_iso(hours_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return dt.isoformat().replace("+00:00", "Z")


def _valid_packet(generated_at: str | None = None) -> dict:
    """Create a valid exec memory packet."""
    existing_source = str(Path(__file__).resolve())
    return {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at or _now_utc_iso(),
        "token_budget": {
            "pm_budget": 3000,
            "ceo_budget": 1800,
            "pm_actual": 2500,
            "ceo_actual": 1600,
            "pm_budget_ok": True,
            "ceo_budget_ok": True,
        },
        "hierarchical_summary": {
            "working_summary": "Final result: HOLD\nSteps total: 3",
            "issue_summary": "No issues",
            "daily_pm_summary": "PM summary",
            "weekly_ceo_summary": "CEO summary",
        },
        "retrieval_namespaces": {
            "governance": [],
            "operations": [],
            "risk": [],
            "roadmap": [],
        },
        "source_bindings": [existing_source],
        "semantic_claims": [
            {
                "claim_id": "SC001",
                "text": "Final result: HOLD",
                "source_path": existing_source,
            }
        ],
    }


def _run_validator(
    *,
    memory_path: Path,
    freshness_hours: int = 72,
    repo_root: Path | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(VALIDATOR_SCRIPT_PATH),
        "--memory-json",
        str(memory_path),
        "--freshness-hours",
        str(freshness_hours),
    ]
    if repo_root:
        cmd.extend(["--repo-root", str(repo_root)])
    if output_json:
        cmd.extend(["--output-json", str(output_json)])
    if output_md:
        cmd.extend(["--output-md", str(output_md)])

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_validation_passes_for_valid_packet(tmp_path: Path) -> None:
    """Test that a valid packet passes validation."""
    memory_path = tmp_path / "exec_memory_packet.json"
    _write_json(memory_path, _valid_packet())

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] Exec memory packet validation passed" in result.stdout


def test_validation_fails_for_missing_field(tmp_path: Path) -> None:
    """Test that validation fails when required field is missing."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    del packet["token_budget"]
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Missing required field: token_budget" in combined


def test_validation_fails_for_stale_packet(tmp_path: Path) -> None:
    """Test that validation fails when packet is stale."""
    memory_path = tmp_path / "exec_memory_packet.json"
    stale_timestamp = _past_utc_iso(hours_ago=100)
    _write_json(memory_path, _valid_packet(generated_at=stale_timestamp))

    result = _run_validator(memory_path=memory_path, freshness_hours=72, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Packet is stale" in combined


def test_validation_returns_exit_2_for_malformed_packet(tmp_path: Path) -> None:
    """Test that validation returns exit code 2 for malformed input."""
    memory_path = tmp_path / "exec_memory_packet.json"
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text("not valid json", encoding="utf-8")

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "Invalid JSON" in combined


def test_validation_returns_exit_2_for_missing_file(tmp_path: Path) -> None:
    """Test that validation returns exit code 2 when input file is missing."""
    memory_path = tmp_path / "missing_exec_memory_packet.json"

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "Missing input file" in combined


def test_validation_fails_for_missing_namespace(tmp_path: Path) -> None:
    """Test that validation fails when required namespace is missing."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    del packet["retrieval_namespaces"]["governance"]
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Missing retrieval_namespaces" in combined
    assert "governance" in combined


def test_validation_fails_for_token_budget_incoherence(tmp_path: Path) -> None:
    """Test that validation fails when token budget flags are incoherent."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    # Set pm_actual > pm_budget but pm_budget_ok = True (incoherent)
    packet["token_budget"]["pm_actual"] = 3500
    packet["token_budget"]["pm_budget"] = 3000
    packet["token_budget"]["pm_budget_ok"] = True
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "pm_budget_ok" in combined
    assert "inconsistent" in combined


def test_validation_fails_for_nonexistent_source_binding(tmp_path: Path) -> None:
    """Test that validation fails when source_binding path does not exist."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    packet["source_bindings"] = ["nonexistent/file.json"]
    packet["semantic_claims"][0]["source_path"] = "nonexistent/file.json"
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "source_binding path does not exist" in combined


def test_validation_passes_with_existing_source_binding(tmp_path: Path) -> None:
    """Test that validation passes when source_binding paths exist."""
    memory_path = tmp_path / "exec_memory_packet.json"
    source_file = tmp_path / "docs" / "context" / "test.json"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text('{"final_result":"HOLD"}', encoding="utf-8")

    packet = _valid_packet()
    packet["source_bindings"] = ["docs/context/test.json"]
    packet["semantic_claims"] = [
        {
            "claim_id": "SC001",
            "text": "Final result: HOLD",
            "source_path": "docs/context/test.json",
        }
    ]
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK]" in result.stdout


def test_validation_passes_for_json_backed_aligned_semantic_claim(tmp_path: Path) -> None:
    """JSON-backed supported claim should pass when source value aligns."""
    memory_path = tmp_path / "exec_memory_packet.json"
    loop_summary_path = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    loop_summary_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(loop_summary_path, {"final_result": "HOLD"})

    packet = _valid_packet()
    packet["source_bindings"] = ["docs/context/loop_cycle_summary_latest.json"]
    packet["semantic_claims"] = [
        {
            "claim_id": "SC001",
            "text": "Final result: HOLD",
            "source_path": "docs/context/loop_cycle_summary_latest.json",
        }
    ]
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK]" in result.stdout


def test_validation_passes_for_valid_semantic_claims(tmp_path: Path) -> None:
    """Test that semantic claims pass when fields/source/text are valid."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK]" in result.stdout


def test_validation_fails_for_semantic_claim_missing_field(tmp_path: Path) -> None:
    """Test semantic claim required field validation."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    packet["semantic_claims"] = [{"claim_id": "SC001", "text": "Final result: HOLD"}]
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "semantic_claims[0].source_path must be a non-empty string" in combined


def test_validation_fails_for_semantic_claim_unknown_source_path(tmp_path: Path) -> None:
    """Test semantic claim source_path must map to source_bindings."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    packet["semantic_claims"][0]["source_path"] = "docs/context/unknown.json"
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "semantic_claims[0].source_path not found in source_bindings" in combined


def test_validation_fails_for_semantic_claim_text_mismatch(tmp_path: Path) -> None:
    """Test semantic claim text must appear in a hierarchical summary section."""
    memory_path = tmp_path / "exec_memory_packet.json"
    packet = _valid_packet()
    packet["semantic_claims"][0]["text"] = "This text does not exist in any summary"
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "semantic_claims[0].text not found in hierarchical_summary sections" in combined


def test_validation_fails_for_semantic_claim_json_contradiction_final_result(
    tmp_path: Path,
) -> None:
    """Supported JSON-backed claim should fail when source contradicts claim text."""
    memory_path = tmp_path / "exec_memory_packet.json"
    loop_summary_path = tmp_path / "docs" / "context" / "loop_cycle_summary_latest.json"
    loop_summary_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(loop_summary_path, {"final_result": "PASS"})

    packet = _valid_packet()
    packet["source_bindings"] = ["docs/context/loop_cycle_summary_latest.json"]
    packet["semantic_claims"] = [
        {
            "claim_id": "SC001",
            "text": "Final result: HOLD",
            "source_path": "docs/context/loop_cycle_summary_latest.json",
        }
    ]
    _write_json(memory_path, packet)

    result = _run_validator(memory_path=memory_path, repo_root=tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "semantic_claims[0] contradiction (Final result)" in combined
    assert "expected='PASS'" in combined
    assert "actual='HOLD'" in combined


def test_validation_writes_output_files(tmp_path: Path) -> None:
    """Test that validation writes output JSON and markdown when requested."""
    memory_path = tmp_path / "exec_memory_packet.json"
    output_json = tmp_path / "validation_status.json"
    output_md = tmp_path / "validation_status.md"
    _write_json(memory_path, _valid_packet())

    result = _run_validator(
        memory_path=memory_path,
        repo_root=tmp_path,
        output_json=output_json,
        output_md=output_md,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_json.exists()
    assert output_md.exists()

    status = json.loads(output_json.read_text(encoding="utf-8"))
    assert status["valid"] is True
    assert "validated_at_utc" in status

    md_content = output_md.read_text(encoding="utf-8")
    assert "[OK] PASS" in md_content
