from __future__ import annotations

import json
from pathlib import Path

from sop.phase8_ga_readiness import validate_ga_verdict
from sop.scripts.phase8_ga_readiness import main as phase8_main


def test_phase8_script_generates_required_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "tests" / "fixtures" / "repos").mkdir(parents=True)

    fixture_defs = {
        "phase8_healthy_pass_path": "PASS",
        "phase8_policy_shadow_block_path": "PASS",
        "phase8_gate_hold_path": "HOLD",
        "phase8_plugin_warn_path": "PASS",
        "phase8_failure_artifact_path": "FAIL",
    }

    for fixture_name, final_result in fixture_defs.items():
        context_dir = repo_root / "tests" / "fixtures" / "repos" / fixture_name / "docs" / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        (context_dir / "loop_cycle_summary_latest.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "final_result": final_result,
                }
            ),
            encoding="utf-8",
        )
        (context_dir / "loop_closure_status_latest.json").write_text(
            json.dumps({"schema_version": "1.0.0", "result": "READY"}),
            encoding="utf-8",
        )
        (context_dir / "audit_log.ndjson").write_text("", encoding="utf-8")

    policy_audit = repo_root / "tests" / "fixtures" / "repos" / "phase8_policy_shadow_block_path" / "docs" / "context" / "audit_log.ndjson"
    policy_audit.write_text(
        '{"decision":"SHADOW_BLOCK","actor":"policy:gate_a"}\n',
        encoding="utf-8",
    )
    plugin_audit = repo_root / "tests" / "fixtures" / "repos" / "phase8_plugin_warn_path" / "docs" / "context" / "audit_log.ndjson"
    plugin_audit.write_text(
        '{"decision":"WARN","actor":"plugin:example"}\n',
        encoding="utf-8",
    )

    rc = phase8_main([
        "--repo-root",
        str(repo_root),
        "--burnin-report",
        "docs/context/burnin_report_latest.json",
        "--slo-baseline",
        "docs/context/slo_baseline_latest.json",
        "--ga-signoff",
        "docs/context/ga_signoff_packet_latest.md",
    ])
    assert rc == 0

    burnin = repo_root / "docs" / "context" / "burnin_report_latest.json"
    slo = repo_root / "docs" / "context" / "slo_baseline_latest.json"
    signoff = repo_root / "docs" / "context" / "ga_signoff_packet_latest.md"

    assert burnin.exists()
    assert slo.exists()
    assert signoff.exists()

    burnin_payload = json.loads(burnin.read_text(encoding="utf-8"))
    assert burnin_payload["total_runs"] == 30
    assert set(burnin_payload["scenario_fixture_mapping"].keys()) == {
        "healthy-pass-path",
        "policy-shadow-block-path",
        "gate-hold-path",
        "plugin-warn-path",
        "failure-artifact-path",
    }

    signoff_text = signoff.read_text(encoding="utf-8")
    assert "## Final GA Verdict" in signoff_text
    verdict_line = signoff_text.split("## Final GA Verdict", 1)[1].strip().splitlines()[0].strip()
    assert validate_ga_verdict(verdict_line) in {"PASS", "FAIL"}
