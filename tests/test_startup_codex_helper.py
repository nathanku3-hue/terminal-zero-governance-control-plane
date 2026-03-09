from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "startup_codex_helper.py"
)

REQUIRED_PATHS = (
    "docs/loop_operating_contract.md",
    "docs/round_contract_template.md",
    "docs/expert_invocation_policy.md",
    "docs/decision_authority_matrix.md",
    "docs/disagreement_taxonomy.md",
    "docs/disagreement_runbook.md",
    "docs/rollback_protocol.md",
    "docs/phase24c_transition_playbook.md",
    "docs/w11_comms_protocol.md",
    "docs/context/current_context.json",
    "docs/context/auditor_promotion_dossier.json",
    "docs/context/ceo_go_signal.md",
)


def _touch_files(repo_root: Path) -> None:
    for rel in REQUIRED_PATHS:
        path = repo_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")


def _run(
    repo_root: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_startup_helper_writes_outputs_and_reports_full_readiness(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    output_md = tmp_path / "docs/context/startup_intake_latest.md"
    output_json = tmp_path / "docs/context/startup_intake_latest.json"
    output_round_seed = tmp_path / "docs/context/round_contract_seed_latest.md"
    output_expert_roster = tmp_path / "docs/context/milestone_expert_roster_latest.json"
    output_domain_bootstrap = tmp_path / "docs/context/domain_bucket_bootstrap_latest.json"

    result = _run(
        tmp_path,
        "--output-md",
        str(output_md),
        "--output-json",
        str(output_json),
        "--output-round-seed",
        str(output_round_seed),
        "--no-interactive",
        "--original-intent",
        "Close C3 by W11 qualification with no scope creep.",
        "--deliverable-this-scope",
        "One audited cycle update with refreshed dossier and GO signal.",
        "--non-goals",
        "No new architecture, no prompt redesign.",
        "--done-when",
        "All per-cycle artifacts refreshed and auditor verdict recorded.",
        "--positioning-lock",
        "Keep execution constrained to startup intake and readiness artifacts.",
        "--task-granularity-limit",
        "2",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "MACHINE_DEFAULT",
        "--intuition-gate-rationale",
        "Cycle work is procedural and should default to machine-led execution.",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STARTUP_HELPER: CODEX" in result.stdout
    assert "WORKER_HEADER: (paste to sonnet web)" in result.stdout
    assert "HANDOFF_TARGET: SONNET_WEB" in result.stdout
    assert "READINESS_PROGRESS: 12/12 (100.0%)" in result.stdout
    assert output_md.exists()
    assert output_json.exists()
    assert output_round_seed.exists()
    assert output_expert_roster.exists()
    assert output_domain_bootstrap.exists()

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["readiness_summary"]["ready_docs"] == 12
    assert payload["readiness_summary"]["status"] == "READY"
    assert payload["interrogation"]["original_intent"].startswith("Close C3")
    assert payload["interrogation"]["positioning_lock"].startswith("Keep execution constrained")
    assert payload["interrogation"]["task_granularity_limit"] == 2
    assert payload["interrogation"]["intuition_gate"] == "MACHINE_DEFAULT"
    assert payload["interrogation"]["intuition_gate_rationale"].startswith("Cycle work is procedural")
    assert payload["interrogation"]["decision_class"] == "TWO_WAY"
    assert payload["interrogation"]["execution_lane"] == "STANDARD"
    assert payload["handoff"]["target"] == "SONNET_WEB"
    assert payload["handoff"]["worker_header"] == "(paste to sonnet web)"
    assert payload["profile_selection_advisory"]["status"] == "RANKING_MISSING"
    assert payload["profile_selection_advisory"]["recommended_profile"] is None
    assert payload["profile_selection_advisory"]["source_path"] == (
        "docs/context/profile_selection_ranking_latest.json"
    )
    assert payload["profile_selection_advisory"]["advisory_only"] is True
    assert payload["milestone_expert_roster"]["milestone_id"] == "unspecified_milestone"
    assert payload["milestone_expert_roster"]["mandatory_domains"] == [
        "principal",
        "riskops",
        "qa",
    ]
    assert payload["milestone_expert_roster"]["unknown_expert_domain_policy"] == "ESCALATE_TO_BOARD"
    assert payload["domain_bucket_bootstrap"]["project_profile"] == "quant_default"

    roster_payload = json.loads(output_expert_roster.read_text(encoding="utf-8"))
    assert roster_payload["milestone_id"] == "unspecified_milestone"
    assert roster_payload["mandatory_domains"] == ["principal", "riskops", "qa"]
    assert roster_payload["optional_domains"] == [
        "math_stats",
        "portfolio_risk",
        "market_microstructure",
        "data_eng",
        "infra_perf",
    ]
    assert roster_payload["unknown_expert_domain_policy"] == "ESCALATE_TO_BOARD"
    bootstrap_payload = json.loads(output_domain_bootstrap.read_text(encoding="utf-8"))
    assert bootstrap_payload == payload["domain_bucket_bootstrap"]
    assert bootstrap_payload["mandatory_domains"] == ["principal", "riskops", "qa"]
    assert bootstrap_payload["domain_buckets"]["core_delivery"] == [
        "principal",
        "riskops",
        "qa",
    ]
    assert bootstrap_payload["domain_buckets"]["quant_research"] == [
        "math_stats",
        "portfolio_risk",
        "market_microstructure",
    ]
    output_text = output_md.read_text(encoding="utf-8")
    assert "Paste-Ready Worker Kickoff" in output_text
    assert "WORKER_HEADER: (paste to sonnet web)" in output_text

    seed_text = output_round_seed.read_text(encoding="utf-8")
    assert "Round Contract Seed" in seed_text
    assert "ORIGINAL_INTENT: Close C3 by W11 qualification with no scope creep." in seed_text
    assert "DELIVERABLE_THIS_SCOPE: One audited cycle update with refreshed dossier and GO signal." in seed_text
    assert "TASK_GRANULARITY_LIMIT: 2" in seed_text
    assert "INTUITION_GATE: MACHINE_DEFAULT" in seed_text
    assert "RISK_TIER: TODO(LOW|MEDIUM|HIGH)" in seed_text
    assert "DONE_WHEN_CHECKS: TODO(comma-separated check IDs from loop/closure outputs)" in seed_text
    assert "COUNTEREXAMPLE_TEST_COMMAND: TODO(use N/A only if TDD_MODE=NOT_APPLICABLE)" in seed_text
    assert "COUNTEREXAMPLE_TEST_RESULT: TODO(use N/A only if TDD_MODE=NOT_APPLICABLE)" in seed_text
    assert "REFACTOR_BUDGET_MINUTES: 0" in seed_text
    assert "REFACTOR_SPEND_MINUTES: 0" in seed_text
    assert "REFACTOR_BUDGET_EXCEEDED_REASON: N/A" in seed_text
    assert "MOCK_POLICY_MODE: NOT_APPLICABLE" in seed_text
    assert "MOCKED_DEPENDENCIES: N/A" in seed_text
    assert "INTEGRATION_COVERAGE_FOR_MOCKS: N/A" in seed_text
    assert "OWNED_FILES: TODO(comma-separated repo-relative paths)" in seed_text
    assert "INTERFACE_INPUTS: TODO(explicit inbound artifacts/params)" in seed_text
    assert "INTERFACE_OUTPUTS: TODO(explicit outbound artifacts/outputs)" in seed_text
    assert "PARALLEL_SHARD_ID: TODO(optional; use none if single-worker)" in seed_text
    assert "PROJECT_PROFILE: quant_default" in seed_text
    assert "EVIDENCE_PROFILE_RECOMMENDATION_STATUS: RANKING_MISSING" in seed_text
    assert "EVIDENCE_PROFILE_RECOMMENDATION: none" in seed_text
    assert "EVIDENCE_PROFILE_SELECTION_USAGE: advisory_only_no_authority_change" in seed_text
    assert "MILESTONE_ID: unspecified_milestone" in seed_text
    assert "APPROVED_MANDATORY_EXPERT_DOMAINS: principal,riskops,qa" in seed_text
    assert "UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_BOARD" in seed_text
    assert "TDD_MODE: TODO(REQUIRED|NOT_APPLICABLE)" in seed_text
    assert "RED_TEST_COMMAND: TODO" in seed_text
    assert "RED_TEST_RESULT: TODO" in seed_text
    assert "GREEN_TEST_COMMAND: TODO" in seed_text
    assert "GREEN_TEST_RESULT: TODO" in seed_text
    assert "REFACTOR_NOTE: TODO" in seed_text
    assert "TDD_NOT_APPLICABLE_REASON: TODO(if NOT_APPLICABLE)" in seed_text


def test_startup_helper_surfaces_profile_selection_recommendation_when_present(
    tmp_path: Path,
) -> None:
    _touch_files(tmp_path)

    ranking_path = tmp_path / "docs/context/profile_selection_ranking_latest.json"
    ranking_path.parent.mkdir(parents=True, exist_ok=True)
    ranking_payload = {
        "schema_version": "1.0.0",
        "generated_at_utc": "2026-03-07T00:00:00Z",
        "recommended_profile": "general_software",
        "confidence": 0.82,
        "evidence_summary": "Recent rounds show dominant product/interface tradeoff workload.",
    }
    ranking_path.write_text(json.dumps(ranking_payload, indent=2) + "\n", encoding="utf-8")

    output_json = tmp_path / "docs/context/startup_intake_latest.json"
    output_md = tmp_path / "docs/context/startup_intake_latest.md"
    output_round_seed = tmp_path / "docs/context/round_contract_seed_latest.md"

    result = _run(
        tmp_path,
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
        "--output-round-seed",
        str(output_round_seed),
        "--no-interactive",
        "--original-intent",
        "Use startup evidence to shape initial profile selection discussion.",
        "--deliverable-this-scope",
        "Emit startup artifacts with profile-selection advisory surfaced.",
        "--non-goals",
        "No automatic project profile override.",
        "--done-when",
        "Recommendation is visible in startup artifacts as advisory only.",
        "--positioning-lock",
        "Keep startup behavior additive and non-authoritative.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "MACHINE_DEFAULT",
        "--intuition-gate-rationale",
        "Startup recommendation surfacing is deterministic.",
        "--project-profile",
        "quant_default",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PROFILE_SELECTION_STATUS: PROFILE_RECOMMENDED" in result.stdout
    assert "PROFILE_SELECTION_RECOMMENDED: general_software" in result.stdout

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    advisory_payload = payload["profile_selection_advisory"]
    assert advisory_payload["status"] == "PROFILE_RECOMMENDED"
    assert advisory_payload["recommended_profile"] == "general_software"
    assert advisory_payload["recommended_profile_known"] is True
    assert advisory_payload["confidence"] == 0.82
    assert advisory_payload["source_path"] == "docs/context/profile_selection_ranking_latest.json"
    assert advisory_payload["advisory_only"] is True
    assert payload["domain_bucket_bootstrap"]["project_profile"] == "quant_default"

    output_text = output_md.read_text(encoding="utf-8")
    assert "PROFILE_SELECTION_STATUS: PROFILE_RECOMMENDED" in output_text
    assert "EVIDENCE_RECOMMENDED_PROFILE: general_software" in output_text

    seed_text = output_round_seed.read_text(encoding="utf-8")
    assert "PROJECT_PROFILE: quant_default" in seed_text
    assert "EVIDENCE_PROFILE_RECOMMENDATION_STATUS: PROFILE_RECOMMENDED" in seed_text
    assert "EVIDENCE_PROFILE_RECOMMENDATION: general_software" in seed_text
    assert "EVIDENCE_PROFILE_SELECTION_USAGE: advisory_only_no_authority_change" in seed_text


def test_startup_helper_writes_custom_milestone_expert_roster(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    output_json = tmp_path / "docs/context/startup_intake_latest.json"
    output_round_seed = tmp_path / "docs/context/round_contract_seed_latest.md"
    output_expert_roster = tmp_path / "docs/context/custom_milestone_expert_roster_latest.json"
    output_domain_bootstrap = tmp_path / "docs/context/custom_domain_bucket_bootstrap_latest.json"

    result = _run(
        tmp_path,
        "--output-json",
        str(output_json),
        "--output-round-seed",
        str(output_round_seed),
        "--output-expert-roster-json",
        str(output_expert_roster),
        "--output-domain-bootstrap-json",
        str(output_domain_bootstrap),
        "--no-interactive",
        "--original-intent",
        "Scope expert lineup before implementation starts.",
        "--deliverable-this-scope",
        "Emit startup artifacts with milestone expert roster fields.",
        "--non-goals",
        "No control-plane authority changes.",
        "--done-when",
        "Roster fields and artifact are generated and linked.",
        "--positioning-lock",
        "Keep this run additive and startup-only.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "MACHINE_DEFAULT",
        "--intuition-gate-rationale",
        "Startup roster initialization is deterministic.",
        "--project-profile",
        "quant_default",
        "--milestone-id",
        "quant_milestone_01",
        "--mandatory-expert-domains",
        "principal,qa,principal,riskops",
        "--optional-expert-domains",
        "math_stats, market_microstructure,math_stats",
        "--board-reentry-triggers",
        "unknown_domain, expert_conflict,unknown_domain",
        "--unknown-expert-domain-policy",
        "ESCALATE_TO_PM",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_expert_roster.exists()
    assert output_domain_bootstrap.exists()

    roster_payload = json.loads(output_expert_roster.read_text(encoding="utf-8"))
    assert roster_payload["milestone_id"] == "quant_milestone_01"
    assert roster_payload["mandatory_domains"] == ["principal", "qa", "riskops"]
    assert roster_payload["optional_domains"] == ["math_stats", "market_microstructure"]
    assert roster_payload["board_reentry_triggers"] == ["unknown_domain", "expert_conflict"]
    assert roster_payload["unknown_expert_domain_policy"] == "ESCALATE_TO_PM"
    bootstrap_payload = json.loads(output_domain_bootstrap.read_text(encoding="utf-8"))
    assert bootstrap_payload["project_profile"] == "quant_default"
    assert bootstrap_payload["mandatory_domains"] == ["principal", "qa", "riskops"]
    assert bootstrap_payload["unknown_expert_domain_policy"] == "ESCALATE_TO_PM"
    assert bootstrap_payload["domain_buckets"]["platform_ops"] == ["data_eng", "infra_perf"]

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["milestone_expert_roster"] == roster_payload
    assert payload["domain_bucket_bootstrap"] == bootstrap_payload

    seed_text = output_round_seed.read_text(encoding="utf-8")
    assert "PROJECT_PROFILE: quant_default" in seed_text
    assert "MILESTONE_ID: quant_milestone_01" in seed_text
    assert "APPROVED_MANDATORY_EXPERT_DOMAINS: principal,qa,riskops" in seed_text
    assert "APPROVED_OPTIONAL_EXPERT_DOMAINS: math_stats,market_microstructure" in seed_text
    assert "BOARD_REENTRY_TRIGGERS: unknown_domain,expert_conflict" in seed_text
    assert "UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_PM" in seed_text


def test_startup_helper_supports_general_software_profile_defaults(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    output_json = tmp_path / "docs/context/startup_intake_latest.json"
    output_domain_bootstrap = tmp_path / "docs/context/domain_bucket_bootstrap_latest.json"

    result = _run(
        tmp_path,
        "--output-json",
        str(output_json),
        "--output-domain-bootstrap-json",
        str(output_domain_bootstrap),
        "--no-interactive",
        "--original-intent",
        "Bootstrap a non-quant software project.",
        "--deliverable-this-scope",
        "Emit startup bootstrap artifacts for a general software profile.",
        "--non-goals",
        "No quant-specific defaults in this run.",
        "--done-when",
        "General software profile defaults are emitted deterministically.",
        "--positioning-lock",
        "Keep the bootstrap additive and profile-driven.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "MACHINE_DEFAULT",
        "--intuition-gate-rationale",
        "Profile bootstrap is deterministic.",
        "--project-profile",
        "general_software",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    bootstrap_payload = json.loads(output_domain_bootstrap.read_text(encoding="utf-8"))

    assert payload["domain_bucket_bootstrap"]["project_profile"] == "general_software"
    assert payload["milestone_expert_roster"]["optional_domains"] == [
        "product_ux",
        "data_eng",
        "infra_perf",
    ]
    assert bootstrap_payload["domain_buckets"]["product_and_user"] == ["product_ux"]
    assert bootstrap_payload["domain_buckets"]["platform_ops"] == ["data_eng", "infra_perf"]


def test_startup_helper_fails_when_interrogation_fields_missing(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    result = _run(
        tmp_path,
        "--no-interactive",
        "--original-intent",
        "Close C3 with W11 evidence.",
    )

    assert result.returncode == 1
    assert "Missing or invalid interrogation fields" in result.stderr


def test_startup_helper_marks_stale_artifact(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    stale_path = tmp_path / "docs/context/auditor_promotion_dossier.json"
    old = datetime.now(timezone.utc) - timedelta(hours=96)
    os.utime(stale_path, (old.timestamp(), old.timestamp()))

    output_json = tmp_path / "docs/context/startup_intake_latest.json"
    result = _run(
        tmp_path,
        "--output-json",
        str(output_json),
        "--no-interactive",
        "--original-intent",
        "Close C3 with W11 evidence.",
        "--deliverable-this-scope",
        "Refresh cycle artifacts.",
        "--non-goals",
        "No architecture changes.",
        "--done-when",
        "Cycle status packet delivered.",
        "--positioning-lock",
        "Keep change scope pinned to refresh artifacts.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "MACHINE_DEFAULT",
        "--intuition-gate-rationale",
        "No escalation required for this bounded refresh run.",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "READINESS_STATUS: NEEDS_ATTENTION" in result.stdout
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["readiness_summary"]["stale_docs"] == 1
    stale_rows = [row for row in payload["readiness_docs"] if row["status"] == "STALE"]
    assert stale_rows
    assert stale_rows[0]["path"] == "docs/context/auditor_promotion_dossier.json"


def test_startup_helper_local_cli_handoff_uses_skills_header(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    output_json = tmp_path / "docs/context/startup_intake_latest.json"
    output_md = tmp_path / "docs/context/startup_intake_latest.md"
    result = _run(
        tmp_path,
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
        "--handoff-target",
        "local_cli",
        "--no-interactive",
        "--original-intent",
        "Run local worker/auditor loop.",
        "--deliverable-this-scope",
        "Init packet ready for local skill handoff.",
        "--non-goals",
        "No web handoff in this run.",
        "--done-when",
        "Kickoff block shows skill-call header.",
        "--positioning-lock",
        "Limit this run to local CLI handoff formatting.",
        "--task-granularity-limit",
        "2",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "HUMAN_REQUIRED",
        "--intuition-gate-rationale",
        "Human review is mandatory before starting the local loop.",
        "--intuition-gate-ack",
        "PM_ACK",
        "--intuition-gate-ack-at-utc",
        "2026-03-05T12:00:00Z",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "WORKER_HEADER: (skills call upon worker)" in result.stdout
    assert "HANDOFF_TARGET: LOCAL_CLI" in result.stdout
    assert "STARTUP_GATE_STATUS: READY_TO_EXECUTE" in result.stdout

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["handoff"]["target"] == "LOCAL_CLI"
    assert payload["handoff"]["handoff_mode"] == "SKILL_CALL"
    assert payload["handoff"]["worker_header"] == "(skills call upon worker)"
    assert payload["startup_gate"]["status"] == "READY_TO_EXECUTE"
    assert payload["startup_gate"]["intuition_gate_ack"] == "PM_ACK"
    assert payload["startup_gate"]["intuition_gate_ack_at_utc"] == "2026-03-05T12:00:00Z"
    output_text = output_md.read_text(encoding="utf-8")
    assert "WORKER_HEADER: (skills call upon worker)" in output_text


def test_startup_helper_fails_for_invalid_task_granularity_limit(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    result = _run(
        tmp_path,
        "--no-interactive",
        "--original-intent",
        "Close C3 with W11 evidence.",
        "--deliverable-this-scope",
        "Refresh cycle artifacts.",
        "--non-goals",
        "No architecture changes.",
        "--done-when",
        "Cycle status packet delivered.",
        "--positioning-lock",
        "Keep execution pinned to startup helper output.",
        "--task-granularity-limit",
        "3",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "MACHINE_DEFAULT",
        "--intuition-gate-rationale",
        "This run should proceed with machine defaults unless blocked.",
    )

    assert result.returncode == 1
    assert "task_granularity_limit(invalid; use 1|2)" in result.stderr


def test_startup_helper_human_required_without_ack_fails(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    result = _run(
        tmp_path,
        "--no-interactive",
        "--original-intent",
        "Close C3 with W11 evidence.",
        "--deliverable-this-scope",
        "Refresh cycle artifacts.",
        "--non-goals",
        "No architecture changes.",
        "--done-when",
        "Cycle status packet delivered.",
        "--positioning-lock",
        "Keep execution pinned to startup helper output.",
        "--task-granularity-limit",
        "2",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "HUMAN_REQUIRED",
        "--intuition-gate-rationale",
        "Human validation required before kickoff.",
    )

    assert result.returncode == 1
    assert "Startup gate validation failed:" in result.stderr
    assert "intuition_gate_ack(required for HUMAN_REQUIRED; use PM_ACK|CEO_ACK)" in result.stderr
    assert "intuition_gate_ack_at_utc(required for HUMAN_REQUIRED" in result.stderr


def test_startup_helper_human_required_with_ack_passes_and_writes_card(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    output_card = tmp_path / "docs/context/init_execution_card_latest.md"
    result = _run(
        tmp_path,
        "--output-card",
        str(output_card),
        "--no-interactive",
        "--original-intent",
        "Close C3 with W11 evidence.",
        "--deliverable-this-scope",
        "Refresh cycle artifacts.",
        "--non-goals",
        "No architecture changes.",
        "--done-when",
        "Cycle status packet delivered.",
        "--positioning-lock",
        "Keep execution pinned to startup helper output.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "HUMAN_REQUIRED",
        "--intuition-gate-rationale",
        "Human validation required before kickoff.",
        "--intuition-gate-ack",
        "PM_ACK",
        "--intuition-gate-ack-at-utc",
        "2026-03-05T12:00:00Z",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_card.exists()
    card_text = output_card.read_text(encoding="utf-8")
    assert "StartupGateStatus: READY_TO_EXECUTE" in card_text
    assert "AckStatus: PM_ACK @ 2026-03-05T12:00:00Z" in card_text


def test_startup_helper_human_required_with_ack_writes_seed_ack_fields(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    output_round_seed = tmp_path / "docs/context/round_contract_seed_latest.md"
    result = _run(
        tmp_path,
        "--output-round-seed",
        str(output_round_seed),
        "--no-interactive",
        "--original-intent",
        "Close C3 with W11 evidence.",
        "--deliverable-this-scope",
        "Refresh cycle artifacts.",
        "--non-goals",
        "No architecture changes.",
        "--done-when",
        "Cycle status packet delivered.",
        "--positioning-lock",
        "Keep execution pinned to startup helper output.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "HUMAN_REQUIRED",
        "--intuition-gate-rationale",
        "Human validation required before kickoff.",
        "--intuition-gate-ack",
        "CEO_ACK",
        "--intuition-gate-ack-at-utc",
        "2026-03-05T13:00:00Z",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert output_round_seed.exists()
    seed_text = output_round_seed.read_text(encoding="utf-8")
    assert "INTUITION_GATE: HUMAN_REQUIRED" in seed_text
    assert "INTUITION_GATE_ACK: CEO_ACK" in seed_text
    assert "ACK_AT_UTC: 2026-03-05T13:00:00Z" in seed_text


def test_startup_helper_fails_for_invalid_intuition_gate(tmp_path: Path) -> None:
    _touch_files(tmp_path)

    result = _run(
        tmp_path,
        "--no-interactive",
        "--original-intent",
        "Close C3 with W11 evidence.",
        "--deliverable-this-scope",
        "Refresh cycle artifacts.",
        "--non-goals",
        "No architecture changes.",
        "--done-when",
        "Cycle status packet delivered.",
        "--positioning-lock",
        "Keep execution pinned to startup helper output.",
        "--task-granularity-limit",
        "1",
        "--decision-class",
        "TWO_WAY",
        "--execution-lane",
        "STANDARD",
        "--intuition-gate",
        "AUTO",
        "--intuition-gate-rationale",
        "Testing enum validation path.",
    )

    assert result.returncode == 1
    assert "intuition_gate(invalid; use MACHINE_DEFAULT|HUMAN_REQUIRED)" in result.stderr
