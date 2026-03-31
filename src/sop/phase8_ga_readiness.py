from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCENARIO_FIXTURE_MAP: dict[str, Path] = {
    "healthy-pass-path": Path("tests/fixtures/repos/phase8_healthy_pass_path"),
    "policy-shadow-block-path": Path("tests/fixtures/repos/phase8_policy_shadow_block_path"),
    "gate-hold-path": Path("tests/fixtures/repos/phase8_gate_hold_path"),
    "plugin-warn-path": Path("tests/fixtures/repos/phase8_plugin_warn_path"),
    "failure-artifact-path": Path("tests/fixtures/repos/phase8_failure_artifact_path"),
}

EXPECTED_FINAL_RESULTS: dict[str, str] = {
    "healthy-pass-path": "PASS",
    "policy-shadow-block-path": "PASS",
    "gate-hold-path": "HOLD",
    "plugin-warn-path": "PASS",
    "failure-artifact-path": "FAIL",
}

VALID_GA_VERDICTS = {"PASS", "FAIL"}
RUNS_PER_SCENARIO = 6


@dataclass(frozen=True)
class ScenarioContract:
    expected_final_result: str
    expects_normal_completion: bool
    expected_exit_code: int
    requires_shadow_block_evidence: bool = False
    requires_plugin_warn_evidence: bool = False


SCENARIO_CONTRACTS: dict[str, ScenarioContract] = {
    "healthy-pass-path": ScenarioContract("PASS", True, 0),
    "policy-shadow-block-path": ScenarioContract("PASS", True, 0, requires_shadow_block_evidence=True),
    "gate-hold-path": ScenarioContract("HOLD", False, 0),
    "plugin-warn-path": ScenarioContract("PASS", True, 0, requires_plugin_warn_evidence=True),
    "failure-artifact-path": ScenarioContract("FAIL", False, 1),
}


PINNED_DRIFT_FIELDS = (
    "scenario_id",
    "expected_final_result",
    "actual_final_result",
    "unexpected_failure",
    "has_loop_summary",
    "has_closure_or_status_artifact",
    "has_terminal_decision_artifact",
)

IGNORED_DRIFT_FIELDS = (
    "run_id",
    "generated_at_utc",
    "duration_seconds",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_ga_verdict(value: str) -> str:
    verdict = str(value).strip().upper()
    if verdict not in VALID_GA_VERDICTS:
        raise ValueError(f"Invalid GA verdict '{value}'. Expected one of {sorted(VALID_GA_VERDICTS)}")
    return verdict


def is_unexpected_failure(
    *,
    expected_final_result: str,
    actual_final_result: str,
    exit_code: int,
    expects_normal_completion: bool,
    has_loop_summary: bool,
    has_closure_or_status_artifact: bool,
    has_terminal_decision_artifact: bool,
) -> bool:
    if actual_final_result != expected_final_result:
        return True
    if expects_normal_completion and exit_code != 0:
        return True
    if not has_loop_summary:
        return True
    if not has_closure_or_status_artifact:
        return True
    if not has_terminal_decision_artifact:
        return True
    return False


def calculate_unexpected_failure_rate(run_records: list[dict[str, Any]]) -> dict[str, Any]:
    total_runs = len(run_records)
    unexpected_failures = 0
    for run in run_records:
        if is_unexpected_failure(
            expected_final_result=str(run["expected_final_result"]),
            actual_final_result=str(run["actual_final_result"]),
            exit_code=int(run["exit_code"]),
            expects_normal_completion=bool(run["expects_normal_completion"]),
            has_loop_summary=bool(run["has_loop_summary"]),
            has_closure_or_status_artifact=bool(run["has_closure_or_status_artifact"]),
            has_terminal_decision_artifact=bool(run["has_terminal_decision_artifact"]),
        ):
            unexpected_failures += 1

    rate = 0.0 if total_runs == 0 else unexpected_failures / total_runs
    return {
        "total_runs": total_runs,
        "unexpected_failures": unexpected_failures,
        "unexpected_failure_rate": rate,
    }


def compare_drift_records(reference: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    differences: list[dict[str, Any]] = []
    for field in PINNED_DRIFT_FIELDS:
        if reference.get(field) != current.get(field):
            differences.append({
                "field": field,
                "reference": reference.get(field),
                "current": current.get(field),
            })
    return {
        "pinned_fields": list(PINNED_DRIFT_FIELDS),
        "ignored_fields": list(IGNORED_DRIFT_FIELDS),
        "difference_count": len(differences),
        "differences": differences,
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_audit_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def evaluate_scenario_run(*, repo_root: Path, scenario_id: str, run_index: int) -> dict[str, Any]:
    if scenario_id not in SCENARIO_FIXTURE_MAP:
        raise KeyError(f"Unknown scenario_id: {scenario_id}")

    fixture_root = repo_root / SCENARIO_FIXTURE_MAP[scenario_id]
    context_dir = fixture_root / "docs" / "context"

    loop_summary_path = context_dir / "loop_cycle_summary_latest.json"
    closure_status_path = context_dir / "loop_closure_status_latest.json"
    terminal_decision_path = loop_summary_path
    audit_log_path = context_dir / "audit_log.ndjson"

    summary = _read_json(loop_summary_path)
    closure = _read_json(closure_status_path)
    audit_entries = _read_audit_entries(audit_log_path)

    contract = SCENARIO_CONTRACTS[scenario_id]
    actual_final_result = str(summary.get("final_result", "MISSING")).upper() if summary else "MISSING"

    has_shadow_block = any(str(e.get("decision", "")).upper() == "SHADOW_BLOCK" for e in audit_entries)
    has_plugin_warn = any(
        str(e.get("decision", "")).upper() == "WARN" and str(e.get("actor", "")).startswith("plugin:")
        for e in audit_entries
    )

    evidence_ok = True
    evidence_notes: list[str] = []
    if contract.requires_shadow_block_evidence and not has_shadow_block:
        evidence_ok = False
        evidence_notes.append("missing required SHADOW_BLOCK evidence in audit log")
    if contract.requires_plugin_warn_evidence and not has_plugin_warn:
        evidence_ok = False
        evidence_notes.append("missing required plugin WARN evidence in audit log")

    run = {
        "run_id": f"{scenario_id}-run-{run_index}",
        "scenario_id": scenario_id,
        "fixture_path": str(SCENARIO_FIXTURE_MAP[scenario_id]),
        "expected_final_result": contract.expected_final_result,
        "actual_final_result": actual_final_result,
        "exit_code": contract.expected_exit_code,
        "expects_normal_completion": contract.expects_normal_completion,
        "has_loop_summary": summary is not None,
        "has_closure_or_status_artifact": closure is not None,
        "has_terminal_decision_artifact": terminal_decision_path.exists(),
        "evidence_ok": evidence_ok,
        "evidence_notes": evidence_notes,
        "generated_at_utc": utc_now_iso(),
    }

    run["unexpected_failure"] = is_unexpected_failure(
        expected_final_result=run["expected_final_result"],
        actual_final_result=run["actual_final_result"],
        exit_code=run["exit_code"],
        expects_normal_completion=run["expects_normal_completion"],
        has_loop_summary=run["has_loop_summary"],
        has_closure_or_status_artifact=run["has_closure_or_status_artifact"],
        has_terminal_decision_artifact=run["has_terminal_decision_artifact"],
    )
    return run


def run_burnin(repo_root: Path) -> dict[str, Any]:
    scenario_ids = list(SCENARIO_FIXTURE_MAP.keys())
    runs: list[dict[str, Any]] = []

    for scenario_id in scenario_ids:
        for run_idx in range(1, RUNS_PER_SCENARIO + 1):
            runs.append(evaluate_scenario_run(repo_root=repo_root, scenario_id=scenario_id, run_index=run_idx))

    failure_summary = calculate_unexpected_failure_rate(runs)
    contract_failures = [r for r in runs if not r["evidence_ok"]]

    verdict = "PASS"
    if failure_summary["unexpected_failures"] > 0:
        verdict = "FAIL"
    if contract_failures:
        verdict = "FAIL"

    validate_ga_verdict(verdict)

    baseline_run = runs[0] if runs else {}
    drift_checks = [compare_drift_records(baseline_run, run) for run in runs[1:]] if runs else []

    return {
        "schema_version": "1.0.0",
        "generated_at_utc": utc_now_iso(),
        "total_runs": len(runs),
        "scenario_count": len(scenario_ids),
        "runs_per_scenario": RUNS_PER_SCENARIO,
        "scenario_fixture_mapping": {k: str(v) for k, v in SCENARIO_FIXTURE_MAP.items()},
        "runs": runs,
        "unexpected_failure_summary": failure_summary,
        "drift_comparison": {
            "pinned_fields": list(PINNED_DRIFT_FIELDS),
            "ignored_fields": list(IGNORED_DRIFT_FIELDS),
            "comparisons": drift_checks,
        },
        "contract_failures": contract_failures,
        "final_ga_verdict": verdict,
    }
