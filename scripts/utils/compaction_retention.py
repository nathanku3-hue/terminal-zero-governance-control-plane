from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Mapping


COMPACTION_RETENTION_SCHEMA_VERSION = "1.0.0"
COMPACTION_RETENTION_SOURCE_PATH = "scripts/utils/compaction_retention.py"
COMPACTION_RETENTION_DOC_PATH = "docs/compaction_behavior_contract.md"

_REQUIRED_ALWAYS = (
    {
        "surface": "next_round_handoff",
        "packet_section": "next_round_handoff",
        "reason": "Primary blocker-to-action handoff must survive compaction.",
    },
    {
        "surface": "expert_request",
        "packet_section": "expert_request",
        "reason": "Specialist escalation request must survive compaction.",
    },
    {
        "surface": "pm_ceo_research_brief",
        "packet_section": "pm_ceo_research_brief",
        "reason": "Leadership research brief must survive compaction.",
    },
    {
        "surface": "board_decision_brief",
        "packet_section": "board_decision_brief",
        "reason": "Board-level decision framing must survive compaction.",
    },
)

_REQUIRED_IF_PRESENT = (
    {
        "surface": "replanning",
        "packet_section": "replanning",
        "reason": "Replanning payload is retained when present.",
    },
    {
        "surface": "automation_uncertainty_status",
        "packet_section": "automation_uncertainty_status",
        "reason": "Automation uncertainty context is retained when present.",
    },
)

_COLD_MANUAL_FALLBACK = (
    {
        "surface": "auditor_fp_ledger",
        "artifact_path": "docs/context/auditor_fp_ledger.json",
        "access": "manual_fallback",
        "reason": "Ledger-level deep dives stay manual-load only.",
    },
)


def _compact_ndjson_rolling(path: Path, max_records: int = 500) -> None:
    """Prune an NDJSON file to the last ``max_records`` lines.

    Reads all non-empty lines from ``path``, keeps the last ``max_records``,
    and writes them back atomically via a temp-file rename.  No-op if the
    file does not exist or has fewer than ``max_records`` lines.

    Args:
        path: Target NDJSON file path.
        max_records: Maximum number of lines to retain (default 500).
    """
    if not path.exists():
        return
    try:
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return
    if len(lines) <= max_records:
        return
    kept = lines[-max_records:]
    import os
    import tempfile
    try:
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_ndjson_", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(kept) + "\n")
        os.replace(tmp, path)
    except OSError:
        try:
            Path(tmp).unlink(missing_ok=True)  # type: ignore[possibly-undefined]
        except Exception:
            pass


def build_compaction_policy_snapshot() -> dict[str, Any]:
    """Build a stable, code-owned compaction retention contract snapshot."""
    return {
        "schema_version": COMPACTION_RETENTION_SCHEMA_VERSION,
        "source_of_truth": COMPACTION_RETENTION_SOURCE_PATH,
        "documentation": COMPACTION_RETENTION_DOC_PATH,
        "required_always": [dict(row) for row in _REQUIRED_ALWAYS],
        "required_if_present": [dict(row) for row in _REQUIRED_IF_PRESENT],
        "cold_manual_fallback": [dict(row) for row in _COLD_MANUAL_FALLBACK],
    }


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def evaluate_compaction_guardrails(memory_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate required retention surfaces before a compaction action is allowed."""
    snapshot = build_compaction_policy_snapshot()

    required_always_plan: list[dict[str, Any]] = []
    required_if_present_plan: list[dict[str, Any]] = []
    violations: list[str] = []

    for row in snapshot["required_always"]:
        section = str(row["packet_section"])
        present = _is_present(memory_payload.get(section))
        required_always_plan.append(
            {
                "surface": str(row["surface"]),
                "packet_section": section,
                "present": present,
                "retention_rule": "required_always",
                "status": "retained" if present else "missing_required",
            }
        )
        if not present:
            violations.append(f"missing_required_surface:{section}")

    for row in snapshot["required_if_present"]:
        section = str(row["packet_section"])
        present = _is_present(memory_payload.get(section))
        required_if_present_plan.append(
            {
                "surface": str(row["surface"]),
                "packet_section": section,
                "present": present,
                "retention_rule": "required_if_present",
                "status": "retained" if present else "not_present",
            }
        )

    cold_manual_fallback_plan = [
        {
            "surface": str(row["surface"]),
            "artifact_path": str(row["artifact_path"]),
            "access": str(row["access"]),
            "retention_rule": "cold_manual_fallback",
            "default_loaded": False,
            "status": "manual_only",
        }
        for row in snapshot["cold_manual_fallback"]
    ]

    return {
        "policy_snapshot": snapshot,
        "retention_plan": {
            "required_always": required_always_plan,
            "required_if_present": required_if_present_plan,
            "cold_manual_fallback": cold_manual_fallback_plan,
        },
        "guardrail_violations": violations,
    }
