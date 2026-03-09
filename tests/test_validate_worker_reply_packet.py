from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_worker_reply_packet.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _make_v1_packet(**overrides: object) -> dict:
    base = {
        "schema_version": "1.0.0",
        "worker_id": "@backend-1",
        "phase": "phase24",
        "generated_at_utc": "2026-03-01T12:00:00Z",
        "items": [
            {
                "task_id": "T-101",
                "decision": "implemented confidence/citation packet",
                "dod_result": "PASS",
                "evidence_ids": ["EV-101"],
                "open_risks": [],
                "confidence": {
                    "score": 0.93,
                    "band": "HIGH",
                    "rationale": "unit tests and schema validation passed",
                },
                "citations": [
                    {
                        "type": "code",
                        "path": "scripts/sample.py",
                        "locator": "L1",
                        "claim": "contains implementation entrypoint",
                    }
                ],
            }
        ],
    }
    base.update(overrides)
    return base


def _make_v2_packet(**overrides: object) -> dict:
    base = {
        "schema_version": "2.0.0",
        "worker_id": "@backend-1",
        "phase": "phase24",
        "generated_at_utc": "2026-03-01T12:00:00Z",
        "items": [
            {
                "task_id": "T-201",
                "decision": "implemented first principles packet",
                "dod_result": "PASS",
                "evidence_ids": ["EV-201"],
                "open_risks": [],
                "citations": [
                    {
                        "type": "code",
                        "path": "scripts/sample.py",
                        "locator": "L1",
                        "claim": "contains implementation entrypoint",
                    }
                ],
                "machine_optimized": {
                    "confidence_level": {
                        "score": 0.90,
                        "band": "HIGH",
                        "rationale": "all checks passed",
                    },
                    "problem_solving_alignment_score": 0.85,
                    "expertise_coverage": [
                        {
                            "domain": "system_eng",
                            "verdict": "APPLIED",
                            "rationale": "boundary checks verified",
                        },
                        {
                            "domain": "qa",
                            "verdict": "APPLIED",
                            "rationale": "unit tests pass",
                        },
                    ],
                },
                "pm_first_principles": {
                    "problem": "worker output lacks reasoning structure",
                    "constraints": "fail-closed pipeline, no migration infra",
                    "logic": "additive schema with version-gated enforcement",
                    "solution": "dual-version validator with cutover schedule",
                },
            }
        ],
    }
    base.update(overrides)
    return base


def _make_response_views(**overrides: object) -> dict:
    base = {
        "machine_view": {
            "status": "READY",
            "decision_summary": "machine-readable summary",
            "primary_evidence_ids": ["EV-201"],
        },
        "human_brief": "Human summary for quick review.",
        "paste_ready_block": (
            "Task T-201\n"
            "Decision: implemented first principles packet\n"
            "DoD: PASS\n"
            "Evidence: EV-201\n"
            "Open risks: none"
        ),
    }
    base.update(overrides)
    return base


def _make_bootstrap_v2_packet() -> dict:
    return {
        "schema_version": "2.0.0",
        "worker_id": "@bootstrap",
        "phase": "phase_bootstrap",
        "generated_at_utc": "2026-03-01T17:16:15Z",
        "items": [
            {
                "task_id": "T-BOOTSTRAP",
                "decision": "Bootstrap scaffold created. Replace this packet with real worker output before phase-end.",
                "dod_result": "PARTIAL",
                "evidence_ids": ["BOOTSTRAP"],
                "open_risks": [
                    "bootstrap placeholder must be replaced with real task evidence"
                ],
                "citations": [
                    {
                        "type": "doc",
                        "path": "docs/context/worker_reply_packet.json",
                        "locator": "items[0]",
                        "claim": "bootstrap placeholder exists and should be replaced before handover",
                    }
                ],
                "machine_optimized": {
                    "confidence_level": {
                        "score": 0.30,
                        "band": "LOW",
                        "rationale": "placeholder scaffold, not execution evidence",
                    },
                    "problem_solving_alignment_score": 0.0,
                    "expertise_coverage": [
                        {
                            "domain": "principal",
                            "verdict": "SKIPPED",
                            "rationale": "bootstrap placeholder - replace before phase-end",
                        },
                        {
                            "domain": "riskops",
                            "verdict": "SKIPPED",
                            "rationale": "bootstrap placeholder - replace before phase-end",
                        },
                        {
                            "domain": "qa",
                            "verdict": "SKIPPED",
                            "rationale": "bootstrap placeholder - replace before phase-end",
                        },
                    ],
                },
                "pm_first_principles": {
                    "problem": "bootstrap placeholder - replace before phase-end",
                    "constraints": "bootstrap placeholder - replace before phase-end",
                    "logic": "bootstrap placeholder - replace before phase-end",
                    "solution": "bootstrap placeholder - replace before phase-end",
                },
            }
        ],
    }


def _run_validator(
    packet_path: Path,
    *,
    repo_root: str = ".",
    require_existing_paths: bool = False,
    schema_version_override: str = "",
    enforce_score_thresholds: bool = False,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(SCRIPT_PATH),
        "--input",
        str(packet_path),
        "--repo-root",
        repo_root,
    ]
    if require_existing_paths:
        args.append("--require-existing-paths")
    if schema_version_override:
        args.extend(["--schema-version-override", schema_version_override])
    if enforce_score_thresholds:
        args.append("--enforce-score-thresholds")
    return subprocess.run(args, capture_output=True, text=True, check=False)


# ---------------------------------------------------------------------------
# v1 regression tests (existing, updated)
# ---------------------------------------------------------------------------


def test_worker_reply_packet_passes_with_confidence_and_citations(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    artifact = repo_root / "scripts" / "sample.py"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("print('ok')\n", encoding="utf-8")

    packet_path = repo_root / "docs/context/worker_reply_packet.json"
    _write_json(packet_path, _make_v1_packet())

    result = _run_validator(
        packet_path, repo_root=str(repo_root), require_existing_paths=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_worker_reply_packet_fails_without_confidence_or_citations(
    tmp_path: Path,
) -> None:
    packet = _make_v1_packet()
    packet["items"][0]["confidence"] = {}
    packet["items"][0]["citations"] = []
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "confidence.score" in combined or "confidence.band" in combined
    assert "citations must be a non-empty list" in combined


# ---------------------------------------------------------------------------
# v2 core tests
# ---------------------------------------------------------------------------


def test_v2_packet_passes_with_all_blocks(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    artifact = repo_root / "scripts" / "sample.py"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("print('ok')\n", encoding="utf-8")

    packet_path = repo_root / "docs/context/worker_reply_packet.json"
    _write_json(packet_path, _make_v2_packet())

    result = _run_validator(
        packet_path, repo_root=str(repo_root), require_existing_paths=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_v2_packet_accepts_optional_response_views(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["response_views"] = _make_response_views()
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_v2_packet_rejects_empty_response_views_human_brief(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["response_views"] = _make_response_views(human_brief="")
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    assert "response_views.human_brief is required" in (
        result.stdout + result.stderr
    )


def test_v2_packet_rejects_empty_response_views_paste_ready_block(
    tmp_path: Path,
) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["response_views"] = _make_response_views(paste_ready_block="")
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    assert "response_views.paste_ready_block is required" in (
        result.stdout + result.stderr
    )


def test_v2_packet_rejects_empty_response_views_machine_view(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["response_views"] = _make_response_views(machine_view={})
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    assert "response_views.machine_view must be a non-empty object" in (
        result.stdout + result.stderr
    )


def test_v2_packet_fails_without_machine_optimized(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    del packet["items"][0]["machine_optimized"]
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    assert "machine_optimized is required" in (result.stdout + result.stderr)


def test_v2_packet_fails_without_pm_first_principles(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    del packet["items"][0]["pm_first_principles"]
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    assert "pm_first_principles is required" in (result.stdout + result.stderr)


def test_v2_packet_fails_with_bare_confidence(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["confidence"] = {
        "score": 0.9,
        "band": "HIGH",
        "rationale": "old style",
    }
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    assert "must use machine_optimized.confidence_level" in (
        result.stdout + result.stderr
    )


def test_schema_version_override_forces_v2(tmp_path: Path) -> None:
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, _make_v1_packet())

    result = _run_validator(packet_path, schema_version_override="2.0.0")
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "machine_optimized is required" in combined


def test_unknown_schema_version_rejected(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["schema_version"] = "3.0.0"
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    assert "unsupported schema_version" in (result.stdout + result.stderr)


# ---------------------------------------------------------------------------
# Expertise coverage enum tests
# ---------------------------------------------------------------------------


def test_v2_invalid_expertise_domain_rejected(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["machine_optimized"]["expertise_coverage"] = [
        {"domain": "finance", "verdict": "APPLIED", "rationale": "checked"}
    ]
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "domain must be one of" in combined


def test_v2_invalid_expertise_verdict_rejected(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["machine_optimized"]["expertise_coverage"] = [
        {"domain": "qa", "verdict": "MAYBE", "rationale": "unsure"}
    ]
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "verdict must be one of" in combined


def test_v2_empty_expertise_rationale_rejected(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    packet["items"][0]["machine_optimized"]["expertise_coverage"] = [
        {"domain": "qa", "verdict": "APPLIED", "rationale": ""}
    ]
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "rationale is required" in combined


# ---------------------------------------------------------------------------
# Bootstrap-generated v2 packet test
# ---------------------------------------------------------------------------


def test_bootstrap_v2_packet_passes_validation(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    # Create the cited file so --require-existing-paths can pass
    cited = repo_root / "docs" / "context" / "worker_reply_packet.json"
    cited.parent.mkdir(parents=True, exist_ok=True)
    cited.write_text("{}", encoding="utf-8")

    packet_path = repo_root / "bootstrap_packet.json"
    _write_json(packet_path, _make_bootstrap_v2_packet())

    result = _run_validator(
        packet_path, repo_root=str(repo_root), require_existing_paths=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Integration: real G06 path with v2 packet
# ---------------------------------------------------------------------------


def test_g06_real_execution_v2_packet(tmp_path: Path) -> None:
    """Invoke validator with identical args to G06 in phase_end_handover.ps1."""
    repo_root = tmp_path / "repo"
    artifact = repo_root / "scripts" / "sample.py"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("print('ok')\n", encoding="utf-8")

    packet_path = repo_root / "docs" / "context" / "worker_reply_packet.json"
    _write_json(packet_path, _make_v2_packet())

    # G06 args: --input <path> --repo-root <path> --require-existing-paths
    result = _run_validator(
        packet_path, repo_root=str(repo_root), require_existing_paths=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Helper: v2 packet with full triad coverage (for threshold tests)
# ---------------------------------------------------------------------------


def _make_v2_triad_packet(**overrides: object) -> dict:
    """v2 packet with all 3 triad domains + scores above thresholds."""
    base = _make_v2_packet()
    base["items"][0]["machine_optimized"]["expertise_coverage"] = [
        {"domain": "principal", "verdict": "APPLIED", "rationale": "buildability verified"},
        {"domain": "riskops", "verdict": "APPLIED", "rationale": "fail-closed check passed"},
        {"domain": "qa", "verdict": "APPLIED", "rationale": "unit tests pass"},
    ]
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Threshold enforcement tests (Phase 24B)
# ---------------------------------------------------------------------------


def test_v2_threshold_confidence_below_070_rejected(tmp_path: Path) -> None:
    packet = _make_v2_triad_packet()
    packet["items"][0]["machine_optimized"]["confidence_level"]["score"] = 0.65
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path, enforce_score_thresholds=True)
    assert result.returncode != 0
    assert "below 0.70 threshold (HOLD)" in (result.stdout + result.stderr)


def test_v2_threshold_relatability_below_075_rejected(tmp_path: Path) -> None:
    packet = _make_v2_triad_packet()
    packet["items"][0]["machine_optimized"]["problem_solving_alignment_score"] = 0.60
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path, enforce_score_thresholds=True)
    assert result.returncode != 0
    assert "below 0.75 threshold (REFRAME)" in (result.stdout + result.stderr)


def test_v2_threshold_both_above_passes(tmp_path: Path) -> None:
    packet = _make_v2_triad_packet()
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path, enforce_score_thresholds=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_v2_threshold_off_low_scores_pass(tmp_path: Path) -> None:
    """Without --enforce-score-thresholds, low scores pass (GAP 1 proof)."""
    packet = _make_v2_packet()
    packet["items"][0]["machine_optimized"]["confidence_level"]["score"] = 0.10
    packet["items"][0]["machine_optimized"]["problem_solving_alignment_score"] = 0.05
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Triad structural enforcement tests (Phase 24B)
# ---------------------------------------------------------------------------


def test_v2_triad_missing_principal_rejected_under_threshold(tmp_path: Path) -> None:
    packet = _make_v2_packet()
    # Default v2 packet has system_eng + qa but NOT principal/riskops
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path, enforce_score_thresholds=True)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "missing required triad domains" in combined


def test_v2_triad_present_without_flag_passes(tmp_path: Path) -> None:
    """Without --enforce-score-thresholds, missing triad is fine (GAP 1 proof)."""
    packet = _make_v2_packet()
    # Has system_eng + qa only — no triad, but flag is off
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path)
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Triad substantive tests (Phase 24B)
# ---------------------------------------------------------------------------


def test_v2_triad_all_skipped_rejected_under_threshold(tmp_path: Path) -> None:
    packet = _make_v2_triad_packet()
    for entry in packet["items"][0]["machine_optimized"]["expertise_coverage"]:
        entry["verdict"] = "SKIPPED"
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path, enforce_score_thresholds=True)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "all triad domains are SKIPPED" in combined


def test_v2_triad_one_applied_passes_under_threshold(tmp_path: Path) -> None:
    packet = _make_v2_triad_packet()
    coverage = packet["items"][0]["machine_optimized"]["expertise_coverage"]
    coverage[0]["verdict"] = "APPLIED"
    coverage[1]["verdict"] = "SKIPPED"
    coverage[2]["verdict"] = "SKIPPED"
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path, enforce_score_thresholds=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_v2_triad_not_required_counts_as_substantive(tmp_path: Path) -> None:
    packet = _make_v2_triad_packet()
    coverage = packet["items"][0]["machine_optimized"]["expertise_coverage"]
    coverage[0]["verdict"] = "NOT_REQUIRED"
    coverage[1]["verdict"] = "SKIPPED"
    coverage[2]["verdict"] = "SKIPPED"
    packet_path = tmp_path / "worker_reply_packet.json"
    _write_json(packet_path, packet)

    result = _run_validator(packet_path, enforce_score_thresholds=True)
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Bootstrap triad test (updated for Phase 24B)
# ---------------------------------------------------------------------------


def test_bootstrap_v2_packet_passes_structural_validation(tmp_path: Path) -> None:
    """Bootstrap packet passes without --enforce-score-thresholds."""
    repo_root = tmp_path / "repo"
    cited = repo_root / "docs" / "context" / "worker_reply_packet.json"
    cited.parent.mkdir(parents=True, exist_ok=True)
    cited.write_text("{}", encoding="utf-8")

    packet_path = repo_root / "bootstrap_packet.json"
    _write_json(packet_path, _make_bootstrap_v2_packet())

    result = _run_validator(
        packet_path, repo_root=str(repo_root), require_existing_paths=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_bootstrap_v2_packet_fails_threshold_enforcement(tmp_path: Path) -> None:
    """Bootstrap packet fails WITH --enforce-score-thresholds (expected)."""
    repo_root = tmp_path / "repo"
    cited = repo_root / "docs" / "context" / "worker_reply_packet.json"
    cited.parent.mkdir(parents=True, exist_ok=True)
    cited.write_text("{}", encoding="utf-8")

    packet_path = repo_root / "bootstrap_packet.json"
    _write_json(packet_path, _make_bootstrap_v2_packet())

    result = _run_validator(
        packet_path,
        repo_root=str(repo_root),
        require_existing_paths=True,
        enforce_score_thresholds=True,
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "below 0.70 threshold (HOLD)" in combined
    assert "below 0.75 threshold (REFRAME)" in combined
    assert "all triad domains are SKIPPED" in combined
