from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


RESULT_READY = "READY_TO_ESCALATE"
RESULT_NOT_READY = "NOT_READY"
RESULT_INFRA_ERROR = "INPUT_OR_INFRA_ERROR"
GO_SIGNAL_ACTION_PATTERN = re.compile(
    r"^\s*-\s*Recommended Action:\s*([A-Za-z_]+)\s*$",
    re.IGNORECASE,
)
GO_SIGNAL_ALLOWED_ACTIONS = {"GO", "HOLD", "REFRAME"}
MARKDOWN_KEY_VALUE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")
TDD_MODE_REQUIRED = "REQUIRED"
TDD_MODE_NOT_APPLICABLE = "NOT_APPLICABLE"
TDD_REQUIRED_FIELDS = (
    "RED_TEST_COMMAND",
    "RED_TEST_RESULT",
    "GREEN_TEST_COMMAND",
    "GREEN_TEST_RESULT",
    "REFACTOR_NOTE",
)
TDD_RED_RESULT_TOKENS = {"FAIL", "FAILED", "NONZERO"}
TDD_GREEN_RESULT_TOKENS = {"PASS", "PASSED", "0"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_path(repo_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _resolve_with_default(repo_root: Path, value: Path | None, default_path: Path) -> Path:
    if value is None:
        return default_path
    return _resolve_path(repo_root=repo_root, candidate=value)


def _artifact_age_hours(path: Path, now_utc: datetime) -> float:
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age = now_utc - modified
    return max(0.0, age.total_seconds() / 3600.0)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _load_json_object(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _find_weekly_summary(context_dir: Path, explicit: Path | None, repo_root: Path) -> Path:
    if explicit is not None:
        return _resolve_path(repo_root=repo_root, candidate=explicit)

    default_latest = context_dir / "ceo_weekly_summary_latest.md"
    if default_latest.exists():
        return default_latest

    candidates: list[tuple[float, str, Path]] = []
    for path in context_dir.glob("ceo_weekly_summary*.md"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        candidates.append((mtime, path.name, path))
    if not candidates:
        return default_latest

    candidates.sort(reverse=True)
    return candidates[0][2]


def _find_round_contract(
    *, context_dir: Path, explicit: Path | None, repo_root: Path
) -> tuple[Path | None, list[Path]]:
    if explicit is not None:
        resolved = _resolve_path(repo_root=repo_root, candidate=explicit)
        return resolved, [resolved]

    latest_path = context_dir / "round_contract_latest.md"
    seed_path = context_dir / "round_contract_seed_latest.md"
    candidates = [latest_path, seed_path]
    if latest_path.exists():
        return latest_path, candidates
    if seed_path.exists():
        return seed_path, candidates
    return None, candidates


def _parse_markdown_key_values(raw: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        match = MARKDOWN_KEY_VALUE_PATTERN.match(line)
        if match is None:
            continue
        key = match.group(1).strip().upper()
        value = match.group(2).strip()
        if key:
            fields[key] = value
    return fields


def _contains_result_token(value: str, tokens: set[str]) -> bool:
    upper_value = value.upper()
    for token in tokens:
        if token == "0":
            if re.search(r"(?<!\d)0(?!\d)", value):
                return True
            continue
        if re.search(rf"\b{re.escape(token)}\b", upper_value):
            return True
    return False


def _evaluate_tdd_contract_gate(fields: dict[str, str]) -> tuple[str, str, str]:
    missing_fields: list[str] = []
    invalid_fields: list[str] = []

    mode = fields.get("TDD_MODE", "").strip().upper()
    if not mode:
        missing_fields.append("TDD_MODE")
    elif mode not in {TDD_MODE_REQUIRED, TDD_MODE_NOT_APPLICABLE}:
        invalid_fields.append(
            f"TDD_MODE(invalid={mode}; expected {TDD_MODE_REQUIRED}|{TDD_MODE_NOT_APPLICABLE})"
        )

    if mode == TDD_MODE_REQUIRED:
        for field in TDD_REQUIRED_FIELDS:
            if not fields.get(field, "").strip():
                missing_fields.append(field)

        red_result = fields.get("RED_TEST_RESULT", "").strip()
        if red_result and not _contains_result_token(red_result, TDD_RED_RESULT_TOKENS):
            invalid_fields.append("RED_TEST_RESULT(must include FAIL|FAILED|NONZERO)")

        green_result = fields.get("GREEN_TEST_RESULT", "").strip()
        if green_result and not _contains_result_token(green_result, TDD_GREEN_RESULT_TOKENS):
            invalid_fields.append("GREEN_TEST_RESULT(must include PASS|PASSED|0)")

    if mode == TDD_MODE_NOT_APPLICABLE:
        if not fields.get("TDD_NOT_APPLICABLE_REASON", "").strip():
            missing_fields.append("TDD_NOT_APPLICABLE_REASON")

    if missing_fields or invalid_fields:
        details_parts: list[str] = []
        if missing_fields:
            details_parts.append("missing=" + ", ".join(missing_fields))
        if invalid_fields:
            details_parts.append("invalid=" + ", ".join(invalid_fields))
        return "FAIL", "TDD contract gate failed.", "; ".join(details_parts)

    return "PASS", "TDD contract gate passed.", f"TDD_MODE={mode}"


def _run_truth_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _run_gate_command(
    *,
    gate_name: str,
    gate_message: str,
    script_path: Path,
    command: list[str],
) -> dict[str, Any]:
    if not script_path.exists():
        return _check_record(
            name=gate_name,
            status="ERROR",
            message=f"{gate_message} script not found.",
            path=script_path,
            command=command,
            details=f"missing_script={script_path}",
        )

    try:
        result = _run_truth_command(command)
    except Exception as exc:
        return _check_record(
            name=gate_name,
            status="ERROR",
            message=f"Failed to execute {gate_message} script.",
            path=script_path,
            command=command,
            details=str(exc),
        )

    details = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return _check_record(
            name=gate_name,
            status="PASS",
            message=f"{gate_message} passed.",
            path=script_path,
            command=command,
            exit_code=result.returncode,
            details=details,
        )
    if result.returncode == 1:
        return _check_record(
            name=gate_name,
            status="FAIL",
            message=f"{gate_message} failed.",
            path=script_path,
            command=command,
            exit_code=result.returncode,
            details=details,
        )
    return _check_record(
        name=gate_name,
        status="ERROR",
        message=f"{gate_message} had input/infra errors.",
        path=script_path,
        command=command,
        exit_code=result.returncode,
        details=details,
    )


def _extract_go_signal_action(path: Path) -> tuple[str, str]:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception:
        return "", ""
    for line in raw.splitlines():
        match = GO_SIGNAL_ACTION_PATTERN.match(line)
        if match is None:
            continue
        action = match.group(1).strip().upper()
        return action, line.strip()
    return "", ""


def _check_record(
    *,
    name: str,
    status: str,
    message: str,
    path: Path | None = None,
    command: list[str] | None = None,
    exit_code: int | None = None,
    details: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "message": message,
        "path": str(path) if path is not None else "",
        "command": command or [],
        "exit_code": exit_code,
        "details": details,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate closure readiness for escalation. "
            "Exit 0=READY_TO_ESCALATE, 1=NOT_READY, 2=input/infra error."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--context-dir", type=Path, default=Path("docs/context"))
    parser.add_argument("--startup-intake-json", type=Path, default=None)
    parser.add_argument("--dossier-json", type=Path, default=None)
    parser.add_argument("--calibration-json", type=Path, default=None)
    parser.add_argument("--go-signal-md", type=Path, default=None)
    parser.add_argument("--startup-card-md", type=Path, default=None)
    parser.add_argument("--weekly-summary-md", type=Path, default=None)
    parser.add_argument("--round-contract-md", type=Path, default=None)
    parser.add_argument("--go-truth-script", type=Path, default=None)
    parser.add_argument("--weekly-truth-script", type=Path, default=None)
    parser.add_argument("--memory-json", type=Path, default=None)
    parser.add_argument("--memory-truth-script", type=Path, default=None)
    parser.add_argument("--loop-summary-json", type=Path, default=None)
    parser.add_argument("--round-contract-checks-script", type=Path, default=None)
    parser.add_argument("--domain-falsification-script", type=Path, default=None)
    parser.add_argument("--counterexample-script", type=Path, default=None)
    parser.add_argument("--dual-judge-script", type=Path, default=None)
    parser.add_argument("--refactor-mock-policy-script", type=Path, default=None)
    parser.add_argument("--review-checklist-script", type=Path, default=None)
    parser.add_argument("--interface-contracts-script", type=Path, default=None)
    parser.add_argument("--parallel-fanin-script", type=Path, default=None)
    parser.add_argument("--parallel-manifest-json", type=Path, default=None)
    parser.add_argument("--python-exe", type=str, default=sys.executable)
    parser.add_argument("--freshness-hours", type=float, default=72.0)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args(argv)


def run_validation(args: argparse.Namespace) -> tuple[int, dict[str, Any], str]:
    now_utc = _utc_now()
    generated_at_utc = _utc_iso(now_utc)

    repo_root = args.repo_root.resolve()
    context_dir = _resolve_path(repo_root=repo_root, candidate=args.context_dir)
    script_dir = Path(__file__).resolve().parent

    startup_intake_path = _resolve_with_default(
        repo_root=repo_root,
        value=args.startup_intake_json,
        default_path=context_dir / "startup_intake_latest.json",
    )
    dossier_path = _resolve_with_default(
        repo_root=repo_root,
        value=args.dossier_json,
        default_path=context_dir / "auditor_promotion_dossier.json",
    )
    calibration_path = _resolve_with_default(
        repo_root=repo_root,
        value=args.calibration_json,
        default_path=context_dir / "auditor_calibration_report.json",
    )
    go_signal_path = _resolve_with_default(
        repo_root=repo_root,
        value=args.go_signal_md,
        default_path=context_dir / "ceo_go_signal.md",
    )
    startup_card_path = _resolve_with_default(
        repo_root=repo_root,
        value=args.startup_card_md,
        default_path=context_dir / "init_execution_card_latest.md",
    )
    weekly_summary_path = _find_weekly_summary(
        context_dir=context_dir,
        explicit=args.weekly_summary_md,
        repo_root=repo_root,
    )
    review_checklist_path = context_dir / "pr_review_checklist_latest.md"
    interface_contract_manifest_path = context_dir / "interface_contract_manifest_latest.json"
    round_contract_path, round_contract_candidates = _find_round_contract(
        context_dir=context_dir,
        explicit=args.round_contract_md,
        repo_root=repo_root,
    )

    go_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.go_truth_script,
        default_path=script_dir / "validate_ceo_go_signal_truth.py",
    )
    weekly_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.weekly_truth_script,
        default_path=script_dir / "validate_ceo_weekly_summary_truth.py",
    )
    memory_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.memory_json,
        default_path=context_dir / "exec_memory_packet_latest.json",
    )
    memory_truth_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.memory_truth_script,
        default_path=script_dir / "validate_exec_memory_truth.py",
    )
    loop_summary_json = _resolve_with_default(
        repo_root=repo_root,
        value=args.loop_summary_json,
        default_path=context_dir / "loop_cycle_summary_latest.json",
    )
    round_contract_checks_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.round_contract_checks_script,
        default_path=script_dir / "validate_round_contract_checks.py",
    )
    domain_falsification_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.domain_falsification_script,
        default_path=script_dir / "validate_domain_falsification_pack.py",
    )
    counterexample_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.counterexample_script,
        default_path=script_dir / "validate_counterexample_gate.py",
    )
    dual_judge_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.dual_judge_script,
        default_path=script_dir / "validate_dual_judge_gate.py",
    )
    refactor_mock_policy_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.refactor_mock_policy_script,
        default_path=script_dir / "validate_refactor_mock_policy.py",
    )
    review_checklist_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.review_checklist_script,
        default_path=script_dir / "validate_review_checklist.py",
    )
    interface_contracts_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.interface_contracts_script,
        default_path=script_dir / "validate_interface_contracts.py",
    )
    parallel_fanin_script = _resolve_with_default(
        repo_root=repo_root,
        value=args.parallel_fanin_script,
        default_path=script_dir / "validate_parallel_fanin.py",
    )
    parallel_manifest_json = (
        _resolve_path(repo_root=repo_root, candidate=args.parallel_manifest_json)
        if args.parallel_manifest_json is not None
        else None
    )

    output_json_path = _resolve_with_default(
        repo_root=repo_root,
        value=args.output_json,
        default_path=context_dir / "loop_closure_status_latest.json",
    )
    output_md_path = _resolve_with_default(
        repo_root=repo_root,
        value=args.output_md,
        default_path=context_dir / "loop_closure_status_latest.md",
    )

    checks: list[dict[str, Any]] = []

    required_artifacts: list[tuple[str, Path]] = [
        ("required_dossier_json", dossier_path),
        ("required_calibration_json", calibration_path),
        ("required_go_signal_md", go_signal_path),
        ("required_startup_card_md", startup_card_path),
        ("required_exec_memory_json", memory_json),
    ]
    missing_required: list[Path] = []
    for check_name, path in required_artifacts:
        if path.exists():
            checks.append(
                _check_record(
                    name=check_name,
                    status="PASS",
                    message="Required artifact found.",
                    path=path,
                )
            )
        else:
            missing_required.append(path)
            checks.append(
                _check_record(
                    name=check_name,
                    status="FAIL",
                    message="Required artifact missing.",
                    path=path,
                )
            )

    if not go_signal_path.exists():
        checks.append(
            _check_record(
                name="go_signal_action_gate",
                status="FAIL",
                message="Recommended action missing because go-signal artifact is missing.",
                path=go_signal_path,
            )
        )
    else:
        action, matched_line = _extract_go_signal_action(go_signal_path)
        if action == "GO":
            checks.append(
                _check_record(
                    name="go_signal_action_gate",
                    status="PASS",
                    message="Recommended action is GO.",
                    path=go_signal_path,
                    details=matched_line,
                )
            )
        elif action in GO_SIGNAL_ALLOWED_ACTIONS:
            checks.append(
                _check_record(
                    name="go_signal_action_gate",
                    status="FAIL",
                    message=f"Recommended action must be GO (actual={action}).",
                    path=go_signal_path,
                    details=matched_line,
                )
            )
        elif action:
            checks.append(
                _check_record(
                    name="go_signal_action_gate",
                    status="FAIL",
                    message=f"Recommended action is invalid (actual={action}).",
                    path=go_signal_path,
                    details=matched_line,
                )
            )
        else:
            checks.append(
                _check_record(
                    name="go_signal_action_gate",
                    status="FAIL",
                    message="Recommended action line missing in go signal markdown.",
                    path=go_signal_path,
                )
            )

    # Startup gate check only when startup intake artifact exists.
    if startup_intake_path.exists():
        try:
            startup_payload = _load_json_object(startup_intake_path)
        except Exception as exc:
            checks.append(
                _check_record(
                    name="startup_gate_status",
                    status="ERROR",
                    message="Failed to parse startup intake JSON.",
                    path=startup_intake_path,
                    details=str(exc),
                )
            )
        else:
            startup_gate = startup_payload.get("startup_gate")
            status_value = ""
            if isinstance(startup_gate, dict):
                status_raw = startup_gate.get("status")
                if isinstance(status_raw, str):
                    status_value = status_raw.strip()
            if status_value == "READY_TO_EXECUTE":
                checks.append(
                    _check_record(
                        name="startup_gate_status",
                        status="PASS",
                        message="startup_gate.status is READY_TO_EXECUTE.",
                        path=startup_intake_path,
                    )
                )
            else:
                checks.append(
                    _check_record(
                        name="startup_gate_status",
                        status="FAIL",
                        message=(
                            "startup_gate.status is not READY_TO_EXECUTE "
                            f"(actual={status_value or 'MISSING'})."
                        ),
                        path=startup_intake_path,
                    )
                )
    else:
        checks.append(
            _check_record(
                name="startup_gate_status",
                status="SKIP",
                message="startup_intake_latest.json not found; startup gate check skipped.",
                path=startup_intake_path,
            )
        )

    round_contract_for_gate = (
        round_contract_path if round_contract_path is not None else context_dir / "round_contract_latest.md"
    )
    round_contract_fields: dict[str, str] = {}

    # TDD contract gate for end-of-round proof validation.
    if round_contract_path is None or not round_contract_path.exists():
        search_targets = ", ".join(str(path) for path in round_contract_candidates)
        checks.append(
            _check_record(
                name="tdd_contract_gate",
                status="FAIL",
                message="Round contract artifact missing for TDD contract gate.",
                path=round_contract_path,
                details=f"searched={search_targets}",
                )
            )
    else:
        try:
            round_contract_raw = round_contract_path.read_text(encoding="utf-8-sig")
        except Exception as exc:
            checks.append(
                _check_record(
                    name="tdd_contract_gate",
                    status="FAIL",
                    message="Unable to read round contract artifact for TDD contract gate.",
                    path=round_contract_path,
                    details=str(exc),
                )
            )
        else:
            round_contract_fields = _parse_markdown_key_values(round_contract_raw)
            status, message, details = _evaluate_tdd_contract_gate(round_contract_fields)
            checks.append(
                _check_record(
                    name="tdd_contract_gate",
                    status=status,
                    message=message,
                    path=round_contract_path,
                    details=details,
                )
            )

    domain_falsification_required = (
        round_contract_fields.get("DOMAIN_FALSIFICATION_REQUIRED", "NO").strip().upper()
        if round_contract_fields
        else "NO"
    )
    if round_contract_path is None or not round_contract_path.exists():
        checks.append(
            _check_record(
                name="domain_falsification_gate",
                status="SKIP",
                message="Round contract missing; domain falsification gate skipped.",
                path=round_contract_for_gate,
            )
        )
    elif domain_falsification_required in {"", "NO"}:
        checks.append(
            _check_record(
                name="domain_falsification_gate",
                status="SKIP",
                message=(
                    "DOMAIN_FALSIFICATION_REQUIRED is NO (or omitted); "
                    "domain falsification gate skipped for non-semantic round."
                ),
                path=round_contract_for_gate,
            )
        )
    elif domain_falsification_required == "YES":
        domain_falsification_cmd = [
            args.python_exe,
            str(domain_falsification_script),
            "--repo-root",
            str(repo_root),
            "--round-contract-md",
            str(round_contract_for_gate),
        ]
        checks.append(
            _run_gate_command(
                gate_name="domain_falsification_gate",
                gate_message="Domain falsification gate",
                script_path=domain_falsification_script,
                command=domain_falsification_cmd,
            )
        )
    else:
        checks.append(
            _check_record(
                name="domain_falsification_gate",
                status="FAIL",
                message=(
                    "DOMAIN_FALSIFICATION_REQUIRED must be YES or NO "
                    f"(actual={domain_falsification_required})."
                ),
                path=round_contract_for_gate,
            )
        )

    # Round contract DONE_WHEN check binding gate.
    with tempfile.TemporaryDirectory() as gate_tmp_dir:
        gate_tmp = Path(gate_tmp_dir)
        closure_preview_json = gate_tmp / "closure_preview.json"
        loop_summary_for_gate = loop_summary_json
        if not loop_summary_for_gate.exists():
            loop_summary_for_gate = gate_tmp / "loop_summary_preview.json"
            _atomic_write_text(
                loop_summary_for_gate,
                json.dumps({"steps": []}, indent=2) + "\n",
            )
        _atomic_write_text(
            closure_preview_json,
            json.dumps({"checks": checks}, indent=2) + "\n",
        )
        done_when_cmd = [
            args.python_exe,
            str(round_contract_checks_script),
            "--round-contract-md",
            str(round_contract_for_gate),
            "--loop-summary-json",
            str(loop_summary_for_gate),
            "--closure-json",
            str(closure_preview_json),
        ]
        checks.append(
            _run_gate_command(
                gate_name="done_when_checks_gate",
                gate_message="DONE_WHEN checks gate",
                script_path=round_contract_checks_script,
                command=done_when_cmd,
            )
        )

    counterexample_cmd = [
        args.python_exe,
        str(counterexample_script),
        "--round-contract-md",
        str(round_contract_for_gate),
    ]
    checks.append(
        _run_gate_command(
            gate_name="counterexample_gate",
            gate_message="Counterexample gate",
            script_path=counterexample_script,
            command=counterexample_cmd,
        )
    )

    dual_judge_cmd = [
        args.python_exe,
        str(dual_judge_script),
        "--round-contract-md",
        str(round_contract_for_gate),
    ]
    checks.append(
        _run_gate_command(
            gate_name="dual_judge_gate",
            gate_message="Dual-judge gate",
            script_path=dual_judge_script,
            command=dual_judge_cmd,
        )
    )

    refactor_mock_policy_cmd = [
        args.python_exe,
        str(refactor_mock_policy_script),
        "--round-contract-md",
        str(round_contract_for_gate),
    ]
    checks.append(
        _run_gate_command(
            gate_name="refactor_mock_policy_gate",
            gate_message="Refactor/mock policy gate",
            script_path=refactor_mock_policy_script,
            command=refactor_mock_policy_cmd,
        )
    )

    if review_checklist_path.exists():
        review_checklist_cmd = [
            args.python_exe,
            str(review_checklist_script),
            "--input",
            str(review_checklist_path),
        ]
        checks.append(
            _run_gate_command(
                gate_name="review_checklist_gate",
                gate_message="Review checklist gate",
                script_path=review_checklist_script,
                command=review_checklist_cmd,
            )
        )
    else:
        checks.append(
            _check_record(
                name="review_checklist_gate",
                status="SKIP",
                message="Review checklist artifact not found; gate skipped.",
                path=review_checklist_path,
            )
        )

    if interface_contract_manifest_path.exists():
        interface_contract_cmd = [
            args.python_exe,
            str(interface_contracts_script),
            "--manifest-json",
            str(interface_contract_manifest_path),
        ]
        checks.append(
            _run_gate_command(
                gate_name="interface_contract_gate",
                gate_message="Interface contract gate",
                script_path=interface_contracts_script,
                command=interface_contract_cmd,
            )
        )
    else:
        checks.append(
            _check_record(
                name="interface_contract_gate",
                status="SKIP",
                message="Interface contract manifest not found; gate skipped.",
                path=interface_contract_manifest_path,
            )
        )

    parallel_fanin_cmd = [
        args.python_exe,
        str(parallel_fanin_script),
        "--context-dir",
        str(context_dir),
    ]
    if parallel_manifest_json is not None:
        parallel_fanin_cmd.extend(["--manifest-json", str(parallel_manifest_json)])
    parallel_fanin_check = _run_gate_command(
        gate_name="parallel_fanin_gate",
        gate_message="Parallel fan-in gate",
        script_path=parallel_fanin_script,
        command=parallel_fanin_cmd,
    )
    if parallel_fanin_check["status"] == "PASS":
        details = str(parallel_fanin_check.get("details", ""))
        if "no active parallel shards" in details.lower():
            parallel_fanin_check["message"] = (
                "Parallel fan-in gate passed (no active parallel shards)."
            )
    checks.append(parallel_fanin_check)

    # Freshness check for key artifacts.
    stale_targets: list[str] = []
    freshness_targets: list[tuple[str, Path]] = list(required_artifacts)
    if startup_intake_path.exists():
        freshness_targets.append(("startup_intake_json", startup_intake_path))
    if weekly_summary_path.exists():
        freshness_targets.append(("weekly_summary_md", weekly_summary_path))
    for label, path in freshness_targets:
        if not path.exists():
            continue
        age = _artifact_age_hours(path=path, now_utc=now_utc)
        if age > args.freshness_hours:
            stale_targets.append(f"{label} ({path}) age={age:.2f}h")

    if stale_targets:
        checks.append(
            _check_record(
                name="freshness_gate",
                status="FAIL",
                message=(
                    f"{len(stale_targets)} artifacts exceed freshness threshold "
                    f"({args.freshness_hours:.2f}h)."
                ),
                details="; ".join(stale_targets),
            )
        )
    else:
        checks.append(
            _check_record(
                name="freshness_gate",
                status="PASS",
                message=(
                    f"All checked artifacts are within freshness threshold "
                    f"({args.freshness_hours:.2f}h)."
                ),
            )
        )

    # Delegated dossier/calibration/go consistency check.
    can_run_go_truth = (
        dossier_path.exists() and calibration_path.exists() and go_signal_path.exists()
    )
    if not can_run_go_truth:
        checks.append(
            _check_record(
                name="go_signal_truth_gate",
                status="SKIP",
                message="Skipping go-signal truth gate because required artifacts are missing.",
            )
        )
    elif not go_truth_script.exists():
        checks.append(
            _check_record(
                name="go_signal_truth_gate",
                status="ERROR",
                message="Go truth-check script not found.",
                path=go_truth_script,
            )
        )
    else:
        go_truth_cmd = [
            args.python_exe,
            str(go_truth_script),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--go-signal-md",
            str(go_signal_path),
        ]
        try:
            go_truth_result = _run_truth_command(go_truth_cmd)
        except Exception as exc:
            checks.append(
                _check_record(
                    name="go_signal_truth_gate",
                    status="ERROR",
                    message="Failed to execute go truth-check script.",
                    command=go_truth_cmd,
                    details=str(exc),
                )
            )
        else:
            details = (go_truth_result.stdout + go_truth_result.stderr).strip()
            if go_truth_result.returncode == 0:
                checks.append(
                    _check_record(
                        name="go_signal_truth_gate",
                        status="PASS",
                        message="Go-signal truth-check passed.",
                        command=go_truth_cmd,
                        exit_code=go_truth_result.returncode,
                        details=details,
                    )
                )
            elif go_truth_result.returncode == 1:
                checks.append(
                    _check_record(
                        name="go_signal_truth_gate",
                        status="FAIL",
                        message="Go-signal truth-check failed.",
                        command=go_truth_cmd,
                        exit_code=go_truth_result.returncode,
                        details=details,
                    )
                )
            else:
                checks.append(
                    _check_record(
                        name="go_signal_truth_gate",
                        status="ERROR",
                        message="Go-signal truth-check had input/infra errors.",
                        command=go_truth_cmd,
                        exit_code=go_truth_result.returncode,
                        details=details,
                    )
                )

    # Weekly summary truth gate is conditional on both artifact and script existing.
    if weekly_summary_path.exists() and weekly_truth_script.exists():
        weekly_truth_cmd = [
            args.python_exe,
            str(weekly_truth_script),
            "--dossier-json",
            str(dossier_path),
            "--calibration-json",
            str(calibration_path),
            "--weekly-md",
            str(weekly_summary_path),
        ]
        try:
            weekly_truth_result = _run_truth_command(weekly_truth_cmd)
        except Exception as exc:
            checks.append(
                _check_record(
                    name="weekly_summary_truth_gate",
                    status="ERROR",
                    message="Failed to execute weekly summary truth-check script.",
                    command=weekly_truth_cmd,
                    details=str(exc),
                )
            )
        else:
            details = (weekly_truth_result.stdout + weekly_truth_result.stderr).strip()
            if weekly_truth_result.returncode == 0:
                checks.append(
                    _check_record(
                        name="weekly_summary_truth_gate",
                        status="PASS",
                        message="Weekly summary truth-check passed.",
                        command=weekly_truth_cmd,
                        exit_code=weekly_truth_result.returncode,
                        details=details,
                    )
                )
            elif weekly_truth_result.returncode == 1:
                checks.append(
                    _check_record(
                        name="weekly_summary_truth_gate",
                        status="FAIL",
                        message="Weekly summary truth-check failed.",
                        command=weekly_truth_cmd,
                        exit_code=weekly_truth_result.returncode,
                        details=details,
                    )
                )
            else:
                checks.append(
                    _check_record(
                        name="weekly_summary_truth_gate",
                        status="ERROR",
                        message="Weekly summary truth-check had input/infra errors.",
                        command=weekly_truth_cmd,
                        exit_code=weekly_truth_result.returncode,
                        details=details,
                    )
                )
    elif weekly_summary_path.exists():
        checks.append(
            _check_record(
                name="weekly_summary_truth_gate",
                status="SKIP",
                message=(
                    "Weekly summary exists but weekly truth-check script is missing; "
                    "gate skipped."
                ),
                path=weekly_truth_script,
            )
        )
    else:
        checks.append(
            _check_record(
                name="weekly_summary_truth_gate",
                status="SKIP",
                message="Weekly summary artifact not found; gate skipped.",
                path=weekly_summary_path,
            )
        )

    # Exec memory truth gate is conditional on both artifact and script existing.
    if memory_json.exists() and memory_truth_script.exists():
        memory_truth_cmd = [
            args.python_exe,
            str(memory_truth_script),
            "--memory-json",
            str(memory_json),
            "--repo-root",
            str(repo_root),
        ]
        try:
            memory_truth_result = _run_truth_command(memory_truth_cmd)
        except Exception as exc:
            checks.append(
                _check_record(
                    name="exec_memory_truth_gate",
                    status="ERROR",
                    message="Failed to execute exec memory truth-check script.",
                    command=memory_truth_cmd,
                    details=str(exc),
                )
            )
        else:
            details = (memory_truth_result.stdout + memory_truth_result.stderr).strip()
            if memory_truth_result.returncode == 0:
                checks.append(
                    _check_record(
                        name="exec_memory_truth_gate",
                        status="PASS",
                        message="Exec memory truth-check passed.",
                        command=memory_truth_cmd,
                        exit_code=memory_truth_result.returncode,
                        details=details,
                    )
                )
            elif memory_truth_result.returncode == 1:
                checks.append(
                    _check_record(
                        name="exec_memory_truth_gate",
                        status="FAIL",
                        message="Exec memory truth-check failed.",
                        command=memory_truth_cmd,
                        exit_code=memory_truth_result.returncode,
                        details=details,
                    )
                )
            else:
                checks.append(
                    _check_record(
                        name="exec_memory_truth_gate",
                        status="ERROR",
                        message="Exec memory truth-check had input/infra errors.",
                        command=memory_truth_cmd,
                        exit_code=memory_truth_result.returncode,
                        details=details,
                    )
                )
    elif memory_json.exists():
        checks.append(
            _check_record(
                name="exec_memory_truth_gate",
                status="SKIP",
                message=(
                    "Exec memory packet exists but truth-check script is missing; "
                    "gate skipped."
                ),
                path=memory_truth_script,
            )
        )
    else:
        checks.append(
            _check_record(
                name="exec_memory_truth_gate",
                status="FAIL",
                message="Exec memory packet not found; gate failed.",
                path=memory_json,
            )
        )

    summary = {
        "pass_count": sum(1 for c in checks if c["status"] == "PASS"),
        "fail_count": sum(1 for c in checks if c["status"] == "FAIL"),
        "error_count": sum(1 for c in checks if c["status"] == "ERROR"),
        "skip_count": sum(1 for c in checks if c["status"] == "SKIP"),
        "total_checks": len(checks),
    }

    if summary["error_count"] > 0:
        result_label = RESULT_INFRA_ERROR
        exit_code = 2
    elif summary["fail_count"] > 0:
        result_label = RESULT_NOT_READY
        exit_code = 1
    else:
        result_label = RESULT_READY
        exit_code = 0

    output_payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "result": result_label,
        "exit_code": exit_code,
        "freshness_hours": args.freshness_hours,
        "paths": {
            "repo_root": str(repo_root),
            "context_dir": str(context_dir),
            "startup_intake_json": str(startup_intake_path),
            "dossier_json": str(dossier_path),
            "calibration_json": str(calibration_path),
            "go_signal_md": str(go_signal_path),
            "startup_card_md": str(startup_card_path),
            "weekly_summary_md": str(weekly_summary_path),
            "round_contract_md": str(round_contract_path) if round_contract_path else "",
            "go_truth_script": str(go_truth_script),
            "weekly_truth_script": str(weekly_truth_script),
            "memory_json": str(memory_json),
            "memory_truth_script": str(memory_truth_script),
            "loop_summary_json": str(loop_summary_json),
            "round_contract_checks_script": str(round_contract_checks_script),
            "domain_falsification_script": str(domain_falsification_script),
            "counterexample_script": str(counterexample_script),
            "dual_judge_script": str(dual_judge_script),
            "refactor_mock_policy_script": str(refactor_mock_policy_script),
            "review_checklist_script": str(review_checklist_script),
            "interface_contracts_script": str(interface_contracts_script),
            "parallel_fanin_script": str(parallel_fanin_script),
            "parallel_manifest_json": str(parallel_manifest_json) if parallel_manifest_json else "",
            "output_json": str(output_json_path),
            "output_md": str(output_md_path),
        },
        "summary": summary,
        "checks": checks,
    }

    md_lines: list[str] = [
        "# Loop Closure Validation",
        "",
        f"- GeneratedAtUTC: {generated_at_utc}",
        f"- Result: {result_label}",
        f"- ExitCode: {exit_code}",
        f"- FreshnessHours: {args.freshness_hours:.2f}",
        "",
        "| Check | Status | Message |",
        "|---|---|---|",
    ]
    for check in checks:
        message = check["message"].replace("|", "\\|")
        md_lines.append(f"| {check['name']} | {check['status']} | {message} |")
    md_lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Pass: {summary['pass_count']}",
            f"- Fail: {summary['fail_count']}",
            f"- Error: {summary['error_count']}",
            f"- Skip: {summary['skip_count']}",
            "",
        ]
    )
    markdown = "\n".join(md_lines)

    try:
        _atomic_write_text(output_json_path, json.dumps(output_payload, indent=2) + "\n")
        _atomic_write_text(output_md_path, markdown)
    except OSError as exc:
        # I/O failures are input/infra errors.
        output_payload["result"] = RESULT_INFRA_ERROR
        output_payload["exit_code"] = 2
        output_payload.setdefault("infra_errors", [])
        output_payload["infra_errors"].append(str(exc))
        return 2, output_payload, markdown

    return exit_code, output_payload, markdown


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    exit_code, payload, _ = run_validation(args)
    print(payload["result"])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
