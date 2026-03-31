from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CONTROL_IDS = ("release", "evidence", "drift", "runbooks")
SCHEMA_VERSION = "1.0.0"

SNAPSHOT_PATH = Path("docs/context/compliance_snapshot_latest.json")
ESCALATION_QUEUE_PATH = Path("docs/context/compliance_escalation_queue_latest.json")

RELEASE_PATH = Path("docs/context/change_review_result_latest.json")
DRIFT_PATH = Path("docs/context/regression_watch_latest.json")

PHASE9_EVIDENCE_PATH = Path("docs/evidence/phase9_post_ga_ops_evidence.md")
PHASE10_EVIDENCE_PATH = Path("docs/evidence/phase10_continuous_compliance_evidence.md")

RUNBOOK_FILES = (
    Path("docs/runbooks/post-ga-operations.md"),
    Path("docs/runbooks/hotfix-protocol.md"),
    Path("docs/runbooks/continuous-compliance.md"),
    Path("docs/policies/compliance_violations.md"),
)

VIOLATION_POLICY_PATH = Path("docs/policies/compliance_violations.md")


class InputError(RuntimeError):
    """Raised for missing/invalid required input or config mapping errors."""


@dataclass
class ControlResult:
    control_id: str
    status: str
    reason: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_compliance_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _load_json_with_status_contract(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise InputError(f"Unreadable JSON artifact: {path} ({exc})") from exc

    if not isinstance(data, dict):
        raise InputError(f"Schema-invalid JSON artifact (not object): {path}")

    overall_status = data.get("overall_status")
    if not isinstance(overall_status, str) or overall_status not in {"PASS", "FAIL"}:
        raise InputError(
            f"Schema-invalid JSON artifact (overall_status must be PASS/FAIL): {path}"
        )

    return data


def _require_markdown_heading(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "#" not in text:
        raise InputError(f"Runbook markdown missing heading marker '#': {path}")


def _parse_violation_policy_rows(policy_path: Path) -> dict[str, dict[str, str]]:
    text = policy_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    table_header_idx = None
    headers: list[str] = []
    for idx, line in enumerate(lines):
        if "|" not in line:
            continue
        columns = [c.strip() for c in line.strip().strip("|").split("|")]
        if {"Violation Type", "Severity", "SLA", "Required Action"}.issubset(set(columns)):
            table_header_idx = idx
            headers = columns
            break

    if table_header_idx is None:
        raise InputError(
            "compliance_violations.md missing required table headers: "
            "Violation Type | Severity | SLA | Required Action"
        )

    rows: dict[str, dict[str, str]] = {}
    for line in lines[table_header_idx + 2 :]:
        if "|" not in line:
            if line.strip():
                continue
            break
        columns = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(columns) != len(headers):
            continue
        row = dict(zip(headers, columns))
        violation_type = row.get("Violation Type", "").strip()
        if not violation_type:
            continue
        rows[violation_type] = {
            "severity": row.get("Severity", "").strip(),
            "sla": row.get("SLA", "").strip(),
            "required_action": row.get("Required Action", "").strip(),
        }

    return rows


def _evaluate_release(repo_root: Path) -> ControlResult:
    path = repo_root / RELEASE_PATH
    if not path.exists():
        return ControlResult("release", "FAIL", f"Missing required artifact: {RELEASE_PATH}")
    payload = _load_json_with_status_contract(path)
    if payload["overall_status"] == "PASS":
        return ControlResult("release", "PASS", "change_review_result overall_status=PASS")
    return ControlResult("release", "FAIL", "change_review_result overall_status!=PASS")


def _evaluate_evidence(repo_root: Path, first_run: bool) -> ControlResult:
    phase9_exists = (repo_root / PHASE9_EVIDENCE_PATH).exists()
    phase10_exists = (repo_root / PHASE10_EVIDENCE_PATH).exists()

    if not phase9_exists:
        return ControlResult(
            "evidence",
            "FAIL",
            f"Missing required evidence artifact: {PHASE9_EVIDENCE_PATH}",
        )

    if phase10_exists:
        return ControlResult(
            "evidence",
            "PASS",
            "Phase 9 and Phase 10 evidence artifacts present",
        )

    if first_run:
        return ControlResult(
            "evidence",
            "PASS",
            "Informational: first run allows absent phase10_continuous_compliance_evidence.md",
        )

    return ControlResult(
        "evidence",
        "FAIL",
        f"Missing required evidence artifact: {PHASE10_EVIDENCE_PATH}",
    )


def _evaluate_drift(repo_root: Path) -> ControlResult:
    path = repo_root / DRIFT_PATH
    if not path.exists():
        return ControlResult("drift", "FAIL", f"Missing required artifact: {DRIFT_PATH}")
    payload = _load_json_with_status_contract(path)
    if payload["overall_status"] == "PASS":
        return ControlResult("drift", "PASS", "regression_watch overall_status=PASS")
    return ControlResult("drift", "FAIL", "regression_watch overall_status!=PASS")


def _evaluate_runbooks(repo_root: Path) -> ControlResult:
    missing = [str(p) for p in RUNBOOK_FILES if not (repo_root / p).exists()]
    if missing:
        return ControlResult("runbooks", "FAIL", f"Missing required runbook/docs files: {missing}")

    for runbook_path in RUNBOOK_FILES[:3]:
        _require_markdown_heading(repo_root / runbook_path)

    return ControlResult("runbooks", "PASS", "All required runbook/docs files exist")


def _build_escalation_queue(
    failing_controls: list[ControlResult],
    policy_rows: dict[str, dict[str, str]],
) -> dict:
    queue_entries = []
    for control in failing_controls:
        row = policy_rows.get(control.control_id)
        if row is None:
            raise InputError(
                "Missing escalation mapping row in compliance_violations.md for "
                f"control_id={control.control_id}"
            )
        queue_entries.append(
            {
                "control_id": control.control_id,
                "severity": row["severity"],
                "sla": row["sla"],
                "required_action": row["required_action"],
                "reason": control.reason,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "queue_size": len(queue_entries),
        "entries": queue_entries,
    }


def run_nightly_audit(repo_root: Path) -> tuple[int, str, str]:
    snapshot_path = repo_root / SNAPSHOT_PATH
    first_run = not snapshot_path.exists()

    release = _evaluate_release(repo_root)
    evidence = _evaluate_evidence(repo_root, first_run=first_run)
    drift = _evaluate_drift(repo_root)
    runbooks = _evaluate_runbooks(repo_root)

    controls = [release, evidence, drift, runbooks]
    failing = [c for c in controls if c.status == "FAIL"]

    policy_path = repo_root / VIOLATION_POLICY_PATH
    if not policy_path.exists():
        raise InputError(f"Missing required policy file: {VIOLATION_POLICY_PATH}")

    policy_rows = _parse_violation_policy_rows(policy_path)
    escalation_queue = _build_escalation_queue(failing_controls=failing, policy_rows=policy_rows)

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "overall_status": "PASS" if not failing else "FAIL",
        "controls": [
            {
                "control_id": c.control_id,
                "status": c.status,
                "reason": c.reason,
            }
            for c in controls
        ],
        "failing_control_ids": [c.control_id for c in failing],
        "escalation_queue_path": str(ESCALATION_QUEUE_PATH).replace("\\", "/"),
    }

    snapshot_json = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    queue_json = json.dumps(escalation_queue, indent=2, ensure_ascii=False) + "\n"

    _atomic_write_text(snapshot_path, snapshot_json)
    _atomic_write_text(repo_root / ESCALATION_QUEUE_PATH, queue_json)

    exit_code = 0 if not failing else 2
    return exit_code, snapshot_json, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run nightly compliance audit for SOP ops.")
    parser.add_argument("--repo-root", required=True, help="Repository root path")
    parser.add_argument("--format", required=True, choices=["json"], help="Output format")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()

    try:
        exit_code, stdout_json, _ = run_nightly_audit(repo_root)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Unexpected nightly-audit failure: {exc}", file=sys.stderr)
        return 3

    sys.stdout.write(stdout_json)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
