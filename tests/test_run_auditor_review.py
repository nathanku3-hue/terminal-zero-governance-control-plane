"""Tests for scripts/run_auditor_review.py"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_auditor_review.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_auditor(
    tmp_path: Path,
    *,
    packet: dict,
    mode: str = "shadow",
    repo_root: Path | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict]:
    input_path = tmp_path / "worker_reply_packet.json"
    output_path = tmp_path / "auditor_findings.json"
    _write_json(input_path, packet)
    rr = str(repo_root) if repo_root else str(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input", str(input_path),
            "--repo-root", rr,
            "--output", str(output_path),
            "--mode", mode,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    findings = {}
    if output_path.exists():
        findings = json.loads(output_path.read_text(encoding="utf-8"))
    return result, findings


# ---------------------------------------------------------------------------
# Helpers: packet builders
# ---------------------------------------------------------------------------

def _make_v2_packet(
    *,
    confidence: float = 0.88,
    relatability: float = 0.85,
    dod_result: str = "PASS",
    open_risks: list | None = None,
    citations: list | None = None,
    triad_verdicts: dict | None = None,
    fp_problem: str = "real problem statement",
) -> dict:
    if open_risks is None:
        open_risks = []
    if citations is None:
        citations = [
            {"type": "code", "path": "scripts/a.py", "locator": "L1", "claim": "claim1"},
            {"type": "test", "path": "tests/test_a.py", "locator": "L5", "claim": "claim2"},
        ]
    if triad_verdicts is None:
        triad_verdicts = {"principal": "APPLIED", "riskops": "APPLIED", "qa": "APPLIED"}

    expertise = [
        {"domain": d, "verdict": v, "rationale": f"{d} check"}
        for d, v in triad_verdicts.items()
    ]

    return {
        "schema_version": "2.0.0",
        "worker_id": "@test-worker",
        "phase": "phase24c",
        "generated_at_utc": "2026-03-02T12:00:00Z",
        "items": [
            {
                "task_id": "T-TEST",
                "decision": "test decision",
                "dod_result": dod_result,
                "evidence_ids": ["EV-TEST"],
                "open_risks": open_risks,
                "citations": citations,
                "machine_optimized": {
                    "confidence_level": {
                        "score": confidence,
                        "band": "HIGH" if confidence >= 0.70 else "LOW",
                        "rationale": "test rationale",
                    },
                    "problem_solving_alignment_score": relatability,
                    "expertise_coverage": expertise,
                },
                "pm_first_principles": {
                    "problem": fp_problem,
                    "constraints": "test constraints",
                    "logic": "test logic",
                    "solution": "test solution",
                },
            }
        ],
    }


def _make_v1_packet() -> dict:
    return {
        "schema_version": "1.0.0",
        "worker_id": "@test-v1",
        "phase": "phase24c",
        "generated_at_utc": "2026-03-02T12:00:00Z",
        "items": [
            {
                "task_id": "T-V1",
                "decision": "v1 decision",
                "dod_result": "PASS",
                "evidence_ids": ["EV-V1"],
                "open_risks": [],
                "confidence": {"score": 0.9, "band": "HIGH", "rationale": "v1 test"},
                "citations": [
                    {"type": "code", "path": "scripts/a.py", "locator": "L1", "claim": "v1 claim"}
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Core behavior tests
# ---------------------------------------------------------------------------

def test_shadow_mode_passes_with_canonical_severity(tmp_path: Path) -> None:
    """Shadow mode: exit 0, findings have canonical severity, blocking=false."""
    packet = _make_v2_packet(confidence=0.30, relatability=0.50)
    result, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    assert result.returncode == 0
    assert findings["summary"]["gate_verdict"] == "PASS"
    assert findings["summary"]["critical"] >= 1  # confidence < 0.70
    assert findings["summary"]["high"] >= 1  # relatability < 0.75
    for f in findings["findings"]:
        assert f["blocking"] is False


def test_enforce_mode_blocks_on_critical(tmp_path: Path) -> None:
    """Enforce mode: exit 1 when Critical findings exist."""
    packet = _make_v2_packet(confidence=0.30)
    result, findings = _run_auditor(tmp_path, packet=packet, mode="enforce")
    assert result.returncode == 1
    assert findings["summary"]["gate_verdict"] == "BLOCK"
    critical_findings = [f for f in findings["findings"] if f["severity"] == "CRITICAL"]
    assert len(critical_findings) >= 1
    assert all(f["blocking"] is True for f in critical_findings)


def test_enforce_mode_passes_clean_packet(tmp_path: Path) -> None:
    """Enforce mode: exit 0 when all scores are above threshold."""
    # Create citation files so AUD-R006 doesn't fire
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "a.py").write_text("# stub", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("# stub", encoding="utf-8")

    packet = _make_v2_packet(confidence=0.88, relatability=0.85)
    result, findings = _run_auditor(tmp_path, packet=packet, mode="enforce")
    assert result.returncode == 0
    assert findings["summary"]["gate_verdict"] == "PASS"
    assert findings["summary"]["critical"] == 0
    assert findings["summary"]["high"] == 0


def test_canonical_severity_identical_across_modes(tmp_path: Path) -> None:
    """Same packet produces same severity counts in shadow and enforce."""
    packet = _make_v2_packet(confidence=0.50, relatability=0.50)

    _, shadow_f = _run_auditor(tmp_path / "shadow", packet=packet, mode="shadow")
    _, enforce_f = _run_auditor(tmp_path / "enforce", packet=packet, mode="enforce")

    for key in ("critical", "high", "medium", "low", "info"):
        assert shadow_f["summary"][key] == enforce_f["summary"][key], (
            f"severity count mismatch for {key}: "
            f"shadow={shadow_f['summary'][key]}, enforce={enforce_f['summary'][key]}"
        )


# ---------------------------------------------------------------------------
# Infra error tests
# ---------------------------------------------------------------------------

def test_infra_error_missing_input(tmp_path: Path) -> None:
    """Exit 2 when input file doesn't exist."""
    output_path = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input", str(tmp_path / "nonexistent.json"),
            "--repo-root", str(tmp_path),
            "--output", str(output_path),
            "--mode", "shadow",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2


def test_infra_error_invalid_json(tmp_path: Path) -> None:
    """Exit 2 when input is not valid JSON."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not json {{{{", encoding="utf-8")
    output_path = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input", str(bad_file),
            "--repo-root", str(tmp_path),
            "--output", str(output_path),
            "--mode", "shadow",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2


def test_infra_error_unknown_schema_version(tmp_path: Path) -> None:
    """Exit 2 when schema_version is not supported."""
    packet = {"schema_version": "99.0.0", "worker_id": "@x", "phase": "p",
              "generated_at_utc": "2026-01-01T00:00:00Z", "items": []}
    result, _ = _run_auditor(tmp_path, packet=packet, mode="shadow")
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# Rule-specific tests
# ---------------------------------------------------------------------------

def test_aud_r000_v1_packet_high_severity(tmp_path: Path) -> None:
    """AUD-R000: v1 packet emits HIGH finding in both modes."""
    packet = _make_v1_packet()
    _, shadow_f = _run_auditor(tmp_path / "shadow", packet=packet, mode="shadow")
    _, enforce_f = _run_auditor(tmp_path / "enforce", packet=packet, mode="enforce")

    # Both produce one HIGH finding
    shadow_r000 = [f for f in shadow_f["findings"] if f["rule_id"] == "AUD-R000"]
    enforce_r000 = [f for f in enforce_f["findings"] if f["rule_id"] == "AUD-R000"]
    assert len(shadow_r000) == 1
    assert len(enforce_r000) == 1
    assert shadow_r000[0]["severity"] == "HIGH"
    assert enforce_r000[0]["severity"] == "HIGH"
    assert shadow_r000[0]["blocking"] is False
    assert enforce_r000[0]["blocking"] is True


def test_aud_r001_confidence_below_070(tmp_path: Path) -> None:
    """AUD-R001: confidence < 0.70 produces CRITICAL finding."""
    packet = _make_v2_packet(confidence=0.50)
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r001 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R001"]
    assert len(r001) == 1
    assert r001[0]["severity"] == "CRITICAL"
    assert r001[0]["category"] == "confidence"


def test_aud_r002_relatability_below_075(tmp_path: Path) -> None:
    """AUD-R002: relatability < 0.75 produces HIGH finding."""
    packet = _make_v2_packet(relatability=0.50)
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r002 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R002"]
    assert len(r002) == 1
    assert r002[0]["severity"] == "HIGH"
    assert r002[0]["category"] == "relatability"


def test_aud_r003_triad_missing(tmp_path: Path) -> None:
    """AUD-R003: missing triad domains produces HIGH finding."""
    packet = _make_v2_packet(triad_verdicts={"qa": "APPLIED"})
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r003 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R003"]
    assert len(r003) == 1
    assert r003[0]["severity"] == "HIGH"
    assert "principal" in r003[0]["description"] or "riskops" in r003[0]["description"]


def test_aud_r004_triad_all_skipped(tmp_path: Path) -> None:
    """AUD-R004: all triad SKIPPED produces HIGH finding."""
    packet = _make_v2_packet(triad_verdicts={
        "principal": "SKIPPED", "riskops": "SKIPPED", "qa": "SKIPPED"
    })
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r004 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R004"]
    assert len(r004) == 1
    assert r004[0]["severity"] == "HIGH"


def test_aud_r005_citations_below_2(tmp_path: Path) -> None:
    """AUD-R005: < 2 citations produces MEDIUM finding."""
    packet = _make_v2_packet(citations=[
        {"type": "code", "path": "scripts/a.py", "locator": "L1", "claim": "one"}
    ])
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r005 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R005"]
    assert len(r005) == 1
    assert r005[0]["severity"] == "MEDIUM"


def test_aud_r006_citation_path_missing(tmp_path: Path) -> None:
    """AUD-R006: nonexistent citation path produces HIGH finding."""
    packet = _make_v2_packet(citations=[
        {"type": "code", "path": "nonexistent/file.py", "locator": "L1", "claim": "claim"},
        {"type": "test", "path": "also_missing.py", "locator": "L2", "claim": "claim2"},
    ])
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r006 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R006"]
    assert len(r006) >= 1
    assert all(f["severity"] == "HIGH" for f in r006)


def test_aud_r007_placeholder_text(tmp_path: Path) -> None:
    """AUD-R007: placeholder text in pm_first_principles produces MEDIUM finding."""
    packet = _make_v2_packet(fp_problem="bootstrap placeholder - replace before phase-end")
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r007 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R007"]
    assert len(r007) == 1
    assert r007[0]["severity"] == "MEDIUM"
    assert r007[0]["category"] == "placeholder_text"


def test_aud_r008_dod_fail_is_medium(tmp_path: Path) -> None:
    """AUD-R008: dod_result=FAIL is MEDIUM, not CRITICAL."""
    packet = _make_v2_packet(dod_result="FAIL")
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r008 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R008"]
    assert len(r008) == 1
    assert r008[0]["severity"] == "MEDIUM"
    assert r008[0]["category"] == "dod_fail"


def test_aud_r009_open_risks_sentinel_normalized(tmp_path: Path) -> None:
    """AUD-R009: sentinel risks (none, n/a, placeholder) are filtered out."""
    packet = _make_v2_packet(
        dod_result="PASS",
        open_risks=["none", "n/a", "placeholder", ""],
    )
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r009 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R009"]
    assert len(r009) == 0, "sentinel risks should not trigger AUD-R009"


def test_aud_r009_substantive_risk_fires(tmp_path: Path) -> None:
    """AUD-R009: substantive open_risks with PASS trigger MEDIUM finding."""
    packet = _make_v2_packet(
        dod_result="PASS",
        open_risks=["real unresolved risk: data pipeline may fail under load"],
    )
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    r009 = [f for f in findings["findings"] if f["rule_id"] == "AUD-R009"]
    assert len(r009) == 1
    assert r009[0]["severity"] == "MEDIUM"


# ---------------------------------------------------------------------------
# Rule ID and schema tests
# ---------------------------------------------------------------------------

def test_all_findings_have_rule_id(tmp_path: Path) -> None:
    """Every finding must have a rule_id field."""
    packet = _make_v2_packet(confidence=0.30, relatability=0.50)
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    for f in findings["findings"]:
        assert "rule_id" in f, f"finding {f['finding_id']} missing rule_id"
        assert f["rule_id"].startswith("AUD-R"), f"unexpected rule_id: {f['rule_id']}"


def test_output_write_contract_exit_0(tmp_path: Path) -> None:
    """Exit 0 must write valid JSON output."""
    packet = _make_v2_packet(confidence=0.88, relatability=0.85)
    result, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    assert result.returncode == 0
    assert findings.get("schema_version") == "1.0.0"
    assert findings.get("auditor_id") == "auditor-v1"


def test_output_write_contract_exit_1(tmp_path: Path) -> None:
    """Exit 1 must write valid JSON output."""
    packet = _make_v2_packet(confidence=0.30)
    result, findings = _run_auditor(tmp_path, packet=packet, mode="enforce")
    assert result.returncode == 1
    assert findings.get("schema_version") == "1.0.0"
    assert findings.get("auditor_id") == "auditor-v1"
    assert findings["summary"]["gate_verdict"] == "BLOCK"


# ---------------------------------------------------------------------------
# Calibration field tests
# ---------------------------------------------------------------------------

def test_summary_includes_items_reviewed(tmp_path: Path) -> None:
    """Summary output includes items_reviewed count."""
    packet = _make_v2_packet()
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    assert "items_reviewed" in findings["summary"]
    assert findings["summary"]["items_reviewed"] == 1  # one item in packet


def test_output_includes_reviewed_packet_schema_version(tmp_path: Path) -> None:
    """Output includes reviewed_packet_schema_version at top level."""
    packet = _make_v2_packet()
    _, findings = _run_auditor(tmp_path, packet=packet, mode="shadow")
    assert findings.get("reviewed_packet_schema_version") == "2.0.0"

    # Also test v1 packets
    v1_packet = _make_v1_packet()
    _, v1_findings = _run_auditor(tmp_path / "v1", packet=v1_packet, mode="shadow")
    assert v1_findings.get("reviewed_packet_schema_version") == "1.0.0"
