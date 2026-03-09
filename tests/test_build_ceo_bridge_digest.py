from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_ceo_bridge_digest.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _make_agg_data() -> dict:
    return {
        "summary": {"overall_health": "OK"},
        "workers": [
            {
                "worker_id": "@backend-1",
                "lane": "backend",
                "heartbeat": {
                    "status": "idle",
                    "current_task": {"task_id": "IDLE"},
                },
                "sla": {"escalation_status": "OK"},
                "expert_gate": {
                    "system_eng": "PASS",
                    "architect": "PASS",
                    "principal": "PASS",
                    "riskops": "PASS",
                    "devsecops": "PASS",
                    "qa": "PASS",
                },
                "completion_log": [],
                "blockers": [],
            }
        ],
    }


def _make_trace_data() -> dict:
    return {
        "directives": [
            {
                "directive_id": "PM-001",
                "source": "top_level_PM.md#x",
                "status": "VERIFIED",
                "traceability": {
                    "code_diffs": [{"file": "scripts/a.py"}],
                    "validators": [{"path": "tests/test_a.py::test_a"}],
                },
            }
        ]
    }


def _make_v1_reply() -> dict:
    return {
        "schema_version": "1.0.0",
        "worker_id": "@backend-1",
        "phase": "phase24",
        "generated_at_utc": "2026-03-01T12:00:00Z",
        "items": [
            {
                "task_id": "T-101",
                "decision": "done",
                "dod_result": "PASS",
                "evidence_ids": ["EV-101"],
                "open_risks": [],
                "confidence": {
                    "score": 0.9,
                    "band": "HIGH",
                    "rationale": "validated",
                },
                "citations": [
                    {
                        "type": "code",
                        "path": "scripts/a.py",
                        "locator": "L1",
                        "claim": "implemented",
                    }
                ],
            }
        ],
    }


def _make_v2_reply() -> dict:
    return {
        "schema_version": "2.0.0",
        "worker_id": "@backend-1",
        "phase": "phase24",
        "generated_at_utc": "2026-03-01T12:00:00Z",
        "items": [
            {
                "task_id": "T-201",
                "decision": "first principles packet",
                "dod_result": "PASS",
                "evidence_ids": ["EV-201"],
                "open_risks": [],
                "citations": [
                    {
                        "type": "code",
                        "path": "scripts/a.py",
                        "locator": "L1",
                        "claim": "implemented",
                    }
                ],
                "machine_optimized": {
                    "confidence_level": {
                        "score": 0.88,
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
                    "problem": "worker output lacks reasoning",
                    "constraints": "fail-closed pipeline",
                    "logic": "additive schema with version gate",
                    "solution": "dual-version validator",
                },
                "response_views": {
                    "machine_view": {
                        "status": "ACTION_REQUIRED",
                        "owner": "worker",
                    },
                    "human_brief": "Patch the validator and keep the fail-closed path intact.",
                    "paste_ready_block": "TASK: patch validator\nOWNER: @backend-1",
                },
            }
        ],
    }


def _make_exec_memory_packet() -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-08T00:00:00Z",
        "expert_request": {
            "requested_domain": "qa",
            "roster_fit": "APPROVED_MANDATORY",
            "milestone_id": "milestone-1",
            "board_reentry_required": "false",
            "board_reentry_reason_codes": ["none"],
            "expert_memory_status": "FRESH",
            "board_memory_status": "FRESH",
            "memory_reason_codes": ["none"],
        },
        "board_decision_brief": {
            "lineup_decision_needed": "false",
            "lineup_gap_domains": ["none"],
            "approved_roster_snapshot": {
                "mandatory": ["principal", "qa"],
                "optional": ["riskops"],
            },
            "reintroduce_board_when": "when milestone scope changes",
            "board_reentry_required": "false",
            "board_reentry_reason_codes": ["none"],
        },
        "automation_uncertainty_status": {
            "expert_memory_status": "FRESH",
            "board_memory_status": "FRESH",
            "memory_reason_codes": ["none"],
        },
        "milestone_expert_roster_status": "ACTIVE",
    }


def _run_digest(
    tmp_path: Path,
    *,
    agg_data: dict | None = None,
    trace_data: dict | None = None,
    esc_data: dict | None = None,
    reply_data: dict | None = None,
    auditor_data: dict | None = None,
    exec_memory_data: dict | None = None,
) -> tuple[subprocess.CompletedProcess[str], str]:
    agg_path = tmp_path / "worker_status_aggregate.json"
    trace_path = tmp_path / "pm_to_code_traceability.yaml"
    out_path = tmp_path / "ceo_bridge_digest.md"

    _write_json(agg_path, agg_data or {"summary": {}, "workers": []})
    _write_yaml(trace_path, trace_data or {"directives": []})

    source_parts = [str(agg_path), str(trace_path)]

    needs_escalation_slot = any(
        value is not None for value in (esc_data, reply_data, auditor_data, exec_memory_data)
    )
    if needs_escalation_slot:
        esc_path = tmp_path / "escalation_events.json"
        _write_json(esc_path, esc_data or {"events": []})
        source_parts.append(str(esc_path))

    needs_reply_slot = any(value is not None for value in (reply_data, auditor_data, exec_memory_data))
    if needs_reply_slot:
        reply_path = tmp_path / "worker_reply_packet.json"
        _write_json(reply_path, reply_data or {})
        source_parts.append(str(reply_path))

    if auditor_data is not None:
        auditor_path = tmp_path / "auditor_findings.json"
        _write_json(auditor_path, auditor_data)
        source_parts.append(str(auditor_path))

    if exec_memory_data is not None:
        exec_memory_path = tmp_path / "exec_memory_packet_latest.json"
        _write_json(exec_memory_path, exec_memory_data)
        source_parts.append(str(exec_memory_path))

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--sources",
            ",".join(source_parts),
            "--output",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    digest = ""
    if out_path.exists():
        digest = out_path.read_text(encoding="utf-8")
    return result, digest


# ---------------------------------------------------------------------------
# Existing tests (updated for v2 section numbering)
# ---------------------------------------------------------------------------


def test_digest_includes_worker_confidence_section_when_reply_packet_provided(
    tmp_path: Path,
) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        esc_data={"events": []},
        reply_data=_make_v1_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## VIII. Worker Confidence and Citations" in digest
    assert "| @backend-1 | T-101 | PASS | 0.90 (HIGH) |" in digest
    assert "## XI. Recommended PM Actions" in digest


def test_digest_handles_missing_reply_packet_source(tmp_path: Path) -> None:
    result, digest = _run_digest(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## VIII. Worker Confidence and Citations" in digest
    assert "- No worker reply packet provided." in digest


# ---------------------------------------------------------------------------
# v2 digest tests
# ---------------------------------------------------------------------------


def test_digest_renders_first_principles_at_top(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    fp_pos = digest.index("## I. First Principles Engineering Summary")
    health_pos = digest.index("## III. System Health")
    assert fp_pos < health_pos
    assert "worker output lacks reasoning" in digest
    assert "fail-closed pipeline" in digest


def test_digest_renders_expertise_coverage(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## II. Strategic Expertise Coverage" in digest
    assert "system_eng" in digest
    assert "APPLIED" in digest
    assert "boundary checks verified" in digest


def test_digest_graceful_v1_fallback(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v1_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Not available (v1 packet)" in digest
    # Confidence should still render from v1 fallback
    assert "0.90 (HIGH)" in digest


def test_digest_confidence_reads_v2_location(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    # v2 confidence comes from machine_optimized.confidence_level (score: 0.88)
    assert "0.88 (HIGH)" in digest


def test_digest_section_ordering_v2(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    sections = [
        "## I. First Principles Engineering Summary",
        "## II. Strategic Expertise Coverage",
        "## III. System Health",
        "## IV. Expert Verdict Matrix",
        "## V. Traceability Summary",
        "## VI. Recent Completions",
        "## VII. Active Escalations",
        "## VIII. Worker Confidence and Citations",
        "## IX. Auditor Review Findings",
        "## X. Per-Round Score Gates",
        "## XI. Recommended PM Actions",
    ]
    positions = [digest.index(s) for s in sections]
    assert positions == sorted(positions), f"Section ordering mismatch: {positions}"


def test_digest_keeps_worker_machine_and_human_views_aligned(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## I. First Principles Engineering Summary" in digest
    assert "worker output lacks reasoning" in digest
    assert "## II. Strategic Expertise Coverage" in digest
    assert "boundary checks verified" in digest
    assert "## VIII. Worker Confidence and Citations" in digest
    assert "0.88 (HIGH)" in digest
    assert "## X. Per-Round Score Gates" in digest
    assert "| GO |" in digest


def test_digest_renders_split_style_worker_views_when_present(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## VIII. Worker Confidence and Citations" in digest
    assert "### PM-Style Worker Summaries" in digest
    assert "Patch the validator and keep the fail-closed path intact." in digest
    assert "### Paste-Ready Worker Blocks" in digest
    assert "TASK: patch validator" in digest


def test_digest_renders_lineup_and_memory_governance_when_exec_memory_source_is_present(
    tmp_path: Path,
) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
        exec_memory_data=_make_exec_memory_packet(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## XII. Lineup and Memory Governance" in digest
    assert "### Expert Request Governance" in digest
    assert "- Requested domain: qa" in digest
    assert "- Roster fit: APPROVED_MANDATORY" in digest
    assert "### Board Governance" in digest
    assert "- Reintroduce board when: when milestone scope changes" in digest
    assert "### Memory Governance" in digest
    assert "- Expert memory status: FRESH" in digest
    assert "- Milestone expert roster status: ACTIVE" in digest


# ---------------------------------------------------------------------------
# Score gate tests (Phase 24B)
# ---------------------------------------------------------------------------


def _make_v2_reply_with_scores(
    confidence: float = 0.88, relatability: float = 0.85
) -> dict:
    reply = _make_v2_reply()
    reply["items"][0]["machine_optimized"]["confidence_level"]["score"] = confidence
    reply["items"][0]["machine_optimized"]["problem_solving_alignment_score"] = relatability
    return reply


def test_digest_score_gates_go(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply_with_scores(0.90, 0.85),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## X. Per-Round Score Gates" in digest
    assert "| GO |" in digest


def test_digest_score_gates_hold(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply_with_scores(0.50, 0.85),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## X. Per-Round Score Gates" in digest
    assert "HOLD" in digest


def test_digest_score_gates_reframe(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply_with_scores(0.90, 0.50),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## X. Per-Round Score Gates" in digest
    assert "REFRAME" in digest


def test_digest_score_gates_hold_and_reframe(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply_with_scores(0.50, 0.50),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## X. Per-Round Score Gates" in digest
    assert "HOLD/REFRAME" in digest


# ---------------------------------------------------------------------------
# Auditor findings digest tests (Phase 24C)
# ---------------------------------------------------------------------------


def _make_auditor_findings(
    *,
    mode: str = "shadow",
    findings: list | None = None,
    critical: int = 0,
    high: int = 0,
    medium: int = 0,
) -> dict:
    if findings is None:
        findings = [
            {
                "finding_id": "AUD-001",
                "rule_id": "AUD-R001",
                "item_index": 0,
                "task_id": "T-TEST",
                "severity": "CRITICAL",
                "category": "confidence",
                "description": "confidence_level.score=0.30 below 0.70 threshold",
                "blocking": mode == "enforce",
            }
        ]
        critical = 1
    return {
        "schema_version": "1.0.0",
        "auditor_id": "auditor-v1",
        "audit_timestamp_utc": "2026-03-02T12:00:00Z",
        "mode": mode,
        "reviewed_packet_path": "docs/context/worker_reply_packet.json",
        "findings": findings,
        "summary": {
            "total_findings": len(findings),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": 0,
            "info": 0,
            "gate_verdict": "PASS" if mode == "shadow" else ("BLOCK" if critical > 0 or high > 0 else "PASS"),
            "infra_error": False,
        },
    }


def test_digest_renders_auditor_section_with_findings(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
        auditor_data=_make_auditor_findings(mode="shadow"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## IX. Auditor Review Findings" in digest
    assert "shadow" in digest
    assert "AUD-R001" in digest
    assert "confidence" in digest


def test_digest_renders_auditor_not_available_without_source(tmp_path: Path) -> None:
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
        # No auditor_data passed
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "## IX. Auditor Review Findings" in digest
    assert "Auditor review not available." in digest


def test_digest_stale_file_suppression(tmp_path: Path) -> None:
    """When auditor source is not passed, even if old file exists on disk,
    Section IX should show 'not available'."""
    # Pre-create a stale auditor file on disk
    stale_path = tmp_path / "auditor_findings.json"
    _write_json(stale_path, _make_auditor_findings(mode="enforce"))

    # Run digest WITHOUT passing auditor as source
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
        # auditor_data=None — not passed as source
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Auditor review not available." in digest


def test_digest_shadow_note_when_high_findings(tmp_path: Path) -> None:
    """Shadow mode with CRITICAL findings shows explanatory note."""
    result, digest = _run_digest(
        tmp_path,
        agg_data=_make_agg_data(),
        trace_data=_make_trace_data(),
        reply_data=_make_v2_reply(),
        auditor_data=_make_auditor_findings(mode="shadow"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "blocking is mode-driven" in digest
