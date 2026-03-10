from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_loop_closure.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_go_truth_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--dossier-json", required=True)
parser.add_argument("--calibration-json", required=True)
parser.add_argument("--go-signal-md", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_weekly_truth_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--dossier-json", required=True)
parser.add_argument("--calibration-json", required=True)
parser.add_argument("--weekly-md", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_memory_truth_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--memory-json", required=True)
parser.add_argument("--repo-root", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_round_contract_checks_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--round-contract-md", required=True)
parser.add_argument("--loop-summary-json", required=True)
parser.add_argument("--closure-json", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_counterexample_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--round-contract-md", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_dual_judge_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--round-contract-md", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_parallel_fanin_stub(path: Path, exit_code: int, message: str = "") -> None:
    safe_message = message.replace("\\", "\\\\").replace("'", "\\'")
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--context-dir", required=True)
parser.add_argument("--manifest-json")
parser.parse_args()
if '{safe_message}':
    print('{safe_message}')
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_refactor_mock_policy_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--round-contract-md", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_review_checklist_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _write_interface_contracts_stub(path: Path, exit_code: int) -> None:
    script = f"""from __future__ import annotations
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument("--manifest-json", required=True)
parser.parse_args()
sys.exit({exit_code})
"""
    _write_text(path, script)


def _prepare_minimal_context(
    repo_root: Path,
    startup_status: str = "READY_TO_EXECUTE",
    go_action: str = "GO",
    round_contract_text: str | None = None,
    include_startup_intake: bool = True,
) -> Path:
    context = repo_root / "docs" / "context"
    if include_startup_intake:
        _write_json(context / "startup_intake_latest.json", {"startup_gate": {"status": startup_status}})
    _write_json(context / "auditor_promotion_dossier.json", {"promotion_criteria": {}})
    _write_json(context / "auditor_calibration_report.json", {"summary": {}})
    _write_json(
        context / "exec_memory_packet_latest.json",
        {
            "schema_version": "1.0.0",
            "generated_at_utc": "2026-03-07T00:00:00Z",
            "token_budget": {
                "pm_budget": 50000,
                "ceo_budget": 30000,
                "pm_actual": 1000,
                "ceo_actual": 500,
                "pm_budget_ok": True,
                "ceo_budget_ok": True,
            },
            "hierarchical_summary": {"pm_context": {}, "ceo_context": {}},
            "retrieval_namespaces": {
                "governance": [],
                "operations": [],
                "risk": [],
                "roadmap": [],
            },
            "source_bindings": [],
        },
    )
    _write_text(
        context / "ceo_go_signal.md",
        "\n".join(
            [
                "# CEO GO Signal",
                "",
                f"- Recommended Action: {go_action}",
                "",
            ]
        ),
    )
    _write_text(context / "init_execution_card_latest.md", "# Init Execution Card\n")
    if round_contract_text is None:
        round_contract_text = "\n".join(
            [
                "# Round Contract",
                "",
                "- DONE_WHEN_CHECKS: tdd_contract_gate,go_signal_action_gate",
                "- TDD_MODE: NOT_APPLICABLE",
                "- TDD_NOT_APPLICABLE_REASON: Non-code round focused on planning and documentation.",
                "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
                "- COUNTEREXAMPLE_TEST_RESULT: N/A",
                "- REFACTOR_BUDGET_MINUTES: 0",
                "- REFACTOR_SPEND_MINUTES: 0",
                "- REFACTOR_BUDGET_EXCEEDED_REASON: N/A",
                "- MOCK_POLICY_MODE: NOT_APPLICABLE",
                "- MOCKED_DEPENDENCIES: N/A",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
                "- DECISION_CLASS: TWO_WAY",
                "- RISK_TIER: LOW",
                "- DUAL_JUDGE_REQUIRED: NO",
                "- DUAL_JUDGE_AUDITOR_1_VERDICT: N/A",
                "- DUAL_JUDGE_AUDITOR_2_VERDICT: N/A",
                "",
            ]
        )
    _write_text(context / "round_contract_latest.md", round_contract_text)
    _write_json(context / "loop_cycle_summary_latest.json", {"steps": []})
    return context


def _run_validator(
    repo_root: Path,
    go_truth_script: Path,
    weekly_truth_script: Path | None = None,
    memory_truth_script: Path | None = None,
    round_contract_checks_script: Path | None = None,
    counterexample_script: Path | None = None,
    dual_judge_script: Path | None = None,
    refactor_mock_policy_script: Path | None = None,
    review_checklist_script: Path | None = None,
    interface_contracts_script: Path | None = None,
    parallel_fanin_script: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--repo-root",
        str(repo_root),
        "--go-truth-script",
        str(go_truth_script),
    ]
    if weekly_truth_script is not None:
        command.extend(["--weekly-truth-script", str(weekly_truth_script)])
    if memory_truth_script is not None:
        command.extend(["--memory-truth-script", str(memory_truth_script)])
    if round_contract_checks_script is not None:
        command.extend(["--round-contract-checks-script", str(round_contract_checks_script)])
    if counterexample_script is not None:
        command.extend(["--counterexample-script", str(counterexample_script)])
    if dual_judge_script is not None:
        command.extend(["--dual-judge-script", str(dual_judge_script)])
    if refactor_mock_policy_script is not None:
        command.extend(["--refactor-mock-policy-script", str(refactor_mock_policy_script)])
    if review_checklist_script is not None:
        command.extend(["--review-checklist-script", str(review_checklist_script)])
    if interface_contracts_script is not None:
        command.extend(["--interface-contracts-script", str(interface_contracts_script)])
    if parallel_fanin_script is not None:
        command.extend(["--parallel-fanin-script", str(parallel_fanin_script)])
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def test_validate_loop_closure_ready_to_escalate(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    memory_truth_script = repo_root / "memory_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_memory_truth_stub(memory_truth_script, exit_code=0)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        memory_truth_script=memory_truth_script,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "READY_TO_ESCALATE"
    assert payload["exit_code"] == 0
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["required_dossier_json"]["status"] == "PASS"
    assert checks["go_signal_action_gate"]["status"] == "PASS"
    assert checks["go_signal_truth_gate"]["status"] == "PASS"
    assert checks["freshness_gate"]["status"] == "PASS"
    assert checks["tdd_contract_gate"]["status"] == "PASS"
    assert checks["done_when_checks_gate"]["status"] == "PASS"
    assert checks["counterexample_gate"]["status"] == "PASS"
    assert checks["dual_judge_gate"]["status"] == "PASS"
    assert checks["refactor_mock_policy_gate"]["status"] == "PASS"
    assert checks["review_checklist_gate"]["status"] == "SKIP"
    assert checks["interface_contract_gate"]["status"] == "SKIP"
    assert checks["parallel_fanin_gate"]["status"] == "PASS"


def test_validate_loop_closure_skips_domain_falsification_for_non_semantic_round(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    memory_truth_script = repo_root / "memory_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_memory_truth_stub(memory_truth_script, exit_code=0)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        memory_truth_script=memory_truth_script,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["domain_falsification_gate"]["status"] == "SKIP"


def test_validate_loop_closure_domain_falsification_gate_passes_when_pack_complete(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    round_contract_text = "\n".join(
        [
            "# Round Contract",
            "",
            "- DONE_WHEN_CHECKS: tdd_contract_gate,go_signal_action_gate",
            "- TDD_MODE: NOT_APPLICABLE",
            "- TDD_NOT_APPLICABLE_REASON: Non-code round focused on planning and documentation.",
            "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
            "- COUNTEREXAMPLE_TEST_RESULT: N/A",
            "- REFACTOR_BUDGET_MINUTES: 0",
            "- REFACTOR_SPEND_MINUTES: 0",
            "- REFACTOR_BUDGET_EXCEEDED_REASON: N/A",
            "- MOCK_POLICY_MODE: NOT_APPLICABLE",
            "- MOCKED_DEPENDENCIES: N/A",
            "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
            "- DECISION_CLASS: TWO_WAY",
            "- RISK_TIER: LOW",
            "- DUAL_JUDGE_REQUIRED: NO",
            "- DUAL_JUDGE_AUDITOR_1_VERDICT: N/A",
            "- DUAL_JUDGE_AUDITOR_2_VERDICT: N/A",
            "- DOMAIN_FALSIFICATION_REQUIRED: YES",
            "- DOMAIN_FALSIFICATION_ARTIFACT: docs/context/domain_falsification_pack_latest.json",
            "- SEMANTIC_RISK_REASON: Macro interpretation ambiguity under stress regime.",
            "- SEMANTIC_EXPERT_DOMAIN: macro_econ",
            "- UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_BOARD",
            "- BOARD_REENTRY_REQUIRED: NO",
            "- BOARD_REENTRY_REASON: N/A",
            "",
        ]
    )
    context = _prepare_minimal_context(repo_root, round_contract_text=round_contract_text)
    _write_json(
        context / "domain_falsification_pack_latest.json",
        {
            "hypothesis": "Macro assumption can break under rate shock.",
            "falsification_checks": ["counterexample macro shock replay"],
            "status": "COMPLETED",
        },
    )
    go_truth_script = repo_root / "go_truth_stub.py"
    memory_truth_script = repo_root / "memory_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_memory_truth_stub(memory_truth_script, exit_code=0)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        memory_truth_script=memory_truth_script,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["domain_falsification_gate"]["status"] == "PASS"


def test_validate_loop_closure_domain_falsification_gate_fails_when_required_pack_missing(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    round_contract_text = "\n".join(
        [
            "# Round Contract",
            "",
            "- DONE_WHEN_CHECKS: tdd_contract_gate,go_signal_action_gate",
            "- TDD_MODE: NOT_APPLICABLE",
            "- TDD_NOT_APPLICABLE_REASON: Non-code round focused on planning and documentation.",
            "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
            "- COUNTEREXAMPLE_TEST_RESULT: N/A",
            "- REFACTOR_BUDGET_MINUTES: 0",
            "- REFACTOR_SPEND_MINUTES: 0",
            "- REFACTOR_BUDGET_EXCEEDED_REASON: N/A",
            "- MOCK_POLICY_MODE: NOT_APPLICABLE",
            "- MOCKED_DEPENDENCIES: N/A",
            "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
            "- DECISION_CLASS: TWO_WAY",
            "- RISK_TIER: LOW",
            "- DUAL_JUDGE_REQUIRED: NO",
            "- DUAL_JUDGE_AUDITOR_1_VERDICT: N/A",
            "- DUAL_JUDGE_AUDITOR_2_VERDICT: N/A",
            "- DOMAIN_FALSIFICATION_REQUIRED: YES",
            "- DOMAIN_FALSIFICATION_ARTIFACT: docs/context/domain_falsification_pack_latest.json",
            "- SEMANTIC_RISK_REASON: User-facing meaning risk requires falsification.",
            "- SEMANTIC_EXPERT_DOMAIN: product_ux",
            "",
        ]
    )
    context = _prepare_minimal_context(repo_root, round_contract_text=round_contract_text)
    go_truth_script = repo_root / "go_truth_stub.py"
    memory_truth_script = repo_root / "memory_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_memory_truth_stub(memory_truth_script, exit_code=0)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        memory_truth_script=memory_truth_script,
    )
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["domain_falsification_gate"]["status"] == "FAIL"
    assert "missing" in checks["domain_falsification_gate"]["details"].lower()


def test_validate_loop_closure_domain_falsification_gate_fails_for_unknown_domain_without_reentry(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    round_contract_text = "\n".join(
        [
            "# Round Contract",
            "",
            "- DONE_WHEN_CHECKS: tdd_contract_gate,go_signal_action_gate",
            "- TDD_MODE: NOT_APPLICABLE",
            "- TDD_NOT_APPLICABLE_REASON: Non-code round focused on planning and documentation.",
            "- COUNTEREXAMPLE_TEST_COMMAND: N/A",
            "- COUNTEREXAMPLE_TEST_RESULT: N/A",
            "- REFACTOR_BUDGET_MINUTES: 0",
            "- REFACTOR_SPEND_MINUTES: 0",
            "- REFACTOR_BUDGET_EXCEEDED_REASON: N/A",
            "- MOCK_POLICY_MODE: NOT_APPLICABLE",
            "- MOCKED_DEPENDENCIES: N/A",
            "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
            "- DECISION_CLASS: TWO_WAY",
            "- RISK_TIER: LOW",
            "- DUAL_JUDGE_REQUIRED: NO",
            "- DUAL_JUDGE_AUDITOR_1_VERDICT: N/A",
            "- DUAL_JUDGE_AUDITOR_2_VERDICT: N/A",
            "- DOMAIN_FALSIFICATION_REQUIRED: YES",
            "- DOMAIN_FALSIFICATION_ARTIFACT: docs/context/domain_falsification_pack_latest.json",
            "- SEMANTIC_RISK_REASON: Domain ownership is currently unclear.",
            "- SEMANTIC_EXPERT_DOMAIN: unknown",
            "- UNKNOWN_EXPERT_DOMAIN_POLICY: ESCALATE_TO_BOARD",
            "- BOARD_REENTRY_REQUIRED: NO",
            "- BOARD_REENTRY_REASON: N/A",
            "",
        ]
    )
    context = _prepare_minimal_context(repo_root, round_contract_text=round_contract_text)
    _write_json(
        context / "domain_falsification_pack_latest.json",
        {
            "hypothesis": "Unknown domain path",
            "falsification_checks": ["probe"],
            "status": "COMPLETED",
        },
    )
    go_truth_script = repo_root / "go_truth_stub.py"
    memory_truth_script = repo_root / "memory_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_memory_truth_stub(memory_truth_script, exit_code=0)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        memory_truth_script=memory_truth_script,
    )
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["domain_falsification_gate"]["status"] == "FAIL"
    assert "BOARD_REENTRY_REQUIRED" in checks["domain_falsification_gate"]["details"]


def test_validate_loop_closure_runs_optional_review_and_interface_gates_when_artifacts_exist(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    _write_text(context / "pr_review_checklist_latest.md", "# checklist\n")
    _write_json(context / "interface_contract_manifest_latest.json", {"contracts": []})
    go_truth_script = repo_root / "go_truth_stub.py"
    memory_truth_script = repo_root / "memory_truth_stub.py"
    round_contract_checks_script = repo_root / "round_contract_checks_stub.py"
    counterexample_script = repo_root / "counterexample_stub.py"
    dual_judge_script = repo_root / "dual_judge_stub.py"
    refactor_mock_policy_script = repo_root / "refactor_mock_policy_stub.py"
    review_checklist_script = repo_root / "review_checklist_stub.py"
    interface_contracts_script = repo_root / "interface_contracts_stub.py"
    parallel_fanin_script = repo_root / "parallel_fanin_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_memory_truth_stub(memory_truth_script, exit_code=0)
    _write_round_contract_checks_stub(round_contract_checks_script, exit_code=0)
    _write_counterexample_stub(counterexample_script, exit_code=0)
    _write_dual_judge_stub(dual_judge_script, exit_code=0)
    _write_refactor_mock_policy_stub(refactor_mock_policy_script, exit_code=0)
    _write_review_checklist_stub(review_checklist_script, exit_code=0)
    _write_interface_contracts_stub(interface_contracts_script, exit_code=0)
    _write_parallel_fanin_stub(parallel_fanin_script, exit_code=0)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        memory_truth_script=memory_truth_script,
        round_contract_checks_script=round_contract_checks_script,
        counterexample_script=counterexample_script,
        dual_judge_script=dual_judge_script,
        refactor_mock_policy_script=refactor_mock_policy_script,
        review_checklist_script=review_checklist_script,
        interface_contracts_script=interface_contracts_script,
        parallel_fanin_script=parallel_fanin_script,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["review_checklist_gate"]["status"] == "PASS"
    assert checks["interface_contract_gate"]["status"] == "PASS"


def test_validate_loop_closure_not_ready_when_startup_gate_blocked(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root, startup_status="BLOCKED_WAITING_FOR_HUMAN_ACK")
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["startup_gate_status"]["status"] == "FAIL"
    assert checks["go_signal_action_gate"]["status"] == "PASS"


def test_validate_loop_closure_not_ready_when_startup_intake_missing(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root, include_startup_intake=False)
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["startup_gate_status"]["status"] == "FAIL"
    assert checks["startup_gate_status"]["message"] == "Required startup_intake_latest.json not found."


def test_validate_loop_closure_not_ready_when_artifact_is_stale(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    stale_path = context / "auditor_promotion_dossier.json"
    stale_seconds = 80 * 3600
    old_time = stale_path.stat().st_mtime - stale_seconds
    os.utime(stale_path, (old_time, old_time))

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["freshness_gate"]["status"] == "FAIL"
    assert checks["go_signal_action_gate"]["status"] == "PASS"


def test_validate_loop_closure_not_ready_when_exec_memory_artifact_missing(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    memory_artifact = context / "exec_memory_packet_latest.json"
    memory_artifact.unlink()

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["required_exec_memory_json"]["status"] == "FAIL"
    assert checks["exec_memory_truth_gate"]["status"] == "FAIL"


def test_validate_loop_closure_not_ready_when_exec_memory_artifact_is_stale(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    stale_path = context / "exec_memory_packet_latest.json"
    stale_seconds = 80 * 3600
    old_time = stale_path.stat().st_mtime - stale_seconds
    os.utime(stale_path, (old_time, old_time))

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["freshness_gate"]["status"] == "FAIL"
    assert "required_exec_memory_json" in checks["freshness_gate"]["details"]


def test_validate_loop_closure_not_ready_when_go_signal_action_is_hold(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root, go_action="HOLD")
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["go_signal_action_gate"]["status"] == "FAIL"


def test_validate_loop_closure_uses_weekly_md_flag_for_weekly_truth_checker(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    _write_text(context / "ceo_weekly_summary_latest.md", "# Weekly Summary\n")

    go_truth_script = repo_root / "go_truth_stub.py"
    weekly_truth_script = repo_root / "weekly_truth_stub.py"
    memory_truth_script = repo_root / "memory_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_weekly_truth_stub(weekly_truth_script, exit_code=0)
    _write_memory_truth_stub(memory_truth_script, exit_code=0)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        weekly_truth_script=weekly_truth_script,
        memory_truth_script=memory_truth_script,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    checks = {check["name"]: check for check in payload["checks"]}
    weekly_check = checks["weekly_summary_truth_gate"]
    assert weekly_check["status"] == "PASS"
    assert "--weekly-md" in weekly_check["command"]
    assert "--weekly-summary-md" not in weekly_check["command"]


def test_validate_loop_closure_returns_infra_error_for_truth_checker_failure(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=2)

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 2, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "INPUT_OR_INFRA_ERROR"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["go_signal_truth_gate"]["status"] == "ERROR"


def test_validate_loop_closure_not_ready_when_tdd_required_proof_is_missing_or_invalid(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(
        repo_root,
        round_contract_text="\n".join(
            [
                "# Round Contract",
                "",
                "- DONE_WHEN_CHECKS: tdd_contract_gate",
                "- TDD_MODE: REQUIRED",
                "- COUNTEREXAMPLE_TEST_COMMAND: python -m pytest tests/test_example.py -q",
                "- COUNTEREXAMPLE_TEST_RESULT: FAIL (expected)",
                "- DECISION_CLASS: TWO_WAY",
                "- RISK_TIER: LOW",
                "- DUAL_JUDGE_REQUIRED: NO",
                "- DUAL_JUDGE_AUDITOR_1_VERDICT: N/A",
                "- DUAL_JUDGE_AUDITOR_2_VERDICT: N/A",
                "- RED_TEST_RESULT: did not execute tests",
                "- GREEN_TEST_COMMAND: python -m pytest tests/test_example.py -q",
                "- GREEN_TEST_RESULT: uncertain",
                "- REFACTOR_NOTE: N/A",
                "- REFACTOR_BUDGET_MINUTES: 0",
                "- REFACTOR_SPEND_MINUTES: 0",
                "- REFACTOR_BUDGET_EXCEEDED_REASON: N/A",
                "- MOCK_POLICY_MODE: NOT_APPLICABLE",
                "- MOCKED_DEPENDENCIES: N/A",
                "- INTEGRATION_COVERAGE_FOR_MOCKS: N/A",
                "",
            ]
        ),
    )
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    result = _run_validator(repo_root=repo_root, go_truth_script=go_truth_script)
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    tdd_gate = checks["tdd_contract_gate"]
    assert tdd_gate["status"] == "FAIL"
    assert "RED_TEST_COMMAND" in tdd_gate["details"]
    assert "GREEN_TEST_RESULT" in tdd_gate["details"]


def test_validate_loop_closure_not_ready_when_counterexample_gate_fails(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    counterexample_script = repo_root / "counterexample_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)
    _write_counterexample_stub(counterexample_script, exit_code=1)

    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        counterexample_script=counterexample_script,
    )
    assert result.returncode == 1, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "NOT_READY"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["counterexample_gate"]["status"] == "FAIL"


def test_validate_loop_closure_infra_error_when_done_when_script_missing(tmp_path: Path) -> None:
    repo_root = tmp_path
    context = _prepare_minimal_context(repo_root)
    go_truth_script = repo_root / "go_truth_stub.py"
    _write_go_truth_stub(go_truth_script, exit_code=0)

    missing_done_when_script = repo_root / "missing_validate_round_contract_checks.py"
    result = _run_validator(
        repo_root=repo_root,
        go_truth_script=go_truth_script,
        round_contract_checks_script=missing_done_when_script,
    )
    assert result.returncode == 2, result.stdout + result.stderr

    payload = json.loads((context / "loop_closure_status_latest.json").read_text(encoding="utf-8"))
    assert payload["result"] == "INPUT_OR_INFRA_ERROR"
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["done_when_checks_gate"]["status"] == "ERROR"
