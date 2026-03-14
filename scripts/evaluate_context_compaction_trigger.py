from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    _script_dir = Path(__file__).resolve().parent
    _project_root = _script_dir.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

from scripts.utils.memory_tiers import bind_memory_tier_paths
from scripts.utils.memory_tiers import build_memory_tier_snapshot


CRITERIA_ORDER = [
    ("C0", "c0_infra_health"),
    ("C1", "c1_24b_close"),
    ("C2", "c2_min_items"),
    ("C3", "c3_min_weeks"),
    ("C4", "c4_fp_rate"),
    ("C4b", "c4b_annotation_coverage"),
    ("C5", "c5_all_v2"),
]
ACTION_PATTERN = re.compile(
    r"^\s*-?\s*Recommended Action\s*:\s*(GO|HOLD|REFRAME)\s*$",
    re.IGNORECASE,
)
COMPACTION_MEMORY_FAMILIES = (
    "exec_memory_packet",
    "auditor_promotion_dossier",
    "ceo_go_signal",
    "context_compaction_state",
    "context_compaction_status",
)
COMPACTION_COLD_FALLBACK_FAMILIES = ("auditor_fp_ledger",)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _read_json_object(path: Path, *, required: bool) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise ValueError(f"Missing required file: {path}")
        return {}
    raw = path.read_text(encoding="utf-8-sig")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _parse_action(go_signal_path: Path) -> str:
    if not go_signal_path.exists():
        raise ValueError(f"Missing required file: {go_signal_path}")
    raw = go_signal_path.read_text(encoding="utf-8-sig")
    for line in raw.splitlines():
        match = ACTION_PATTERN.match(line)
        if match is None:
            continue
        return match.group(1).upper()
    raise ValueError("Recommended Action line missing in go-signal markdown")


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _extract_ratio(memory: dict[str, Any], actual_key: str, budget_key: str) -> float:
    token_budget = memory.get("token_budget")
    if not isinstance(token_budget, dict):
        raise ValueError("memory_json missing object field token_budget")

    actual = _to_float(token_budget.get(actual_key))
    budget = _to_float(token_budget.get(budget_key))
    if actual is None or budget is None:
        raise ValueError(f"token_budget missing numeric fields: {actual_key}/{budget_key}")
    if budget <= 0:
        raise ValueError(f"token_budget {budget_key} must be > 0")
    return actual / budget


def _extract_criteria_met(dossier: dict[str, Any]) -> dict[str, Any]:
    criteria_obj = dossier.get("promotion_criteria")
    if not isinstance(criteria_obj, dict):
        raise ValueError("dossier_json missing object field promotion_criteria")

    result: dict[str, Any] = {}
    for code, key in CRITERIA_ORDER:
        entry = criteria_obj.get(key)
        if isinstance(entry, dict):
            result[code] = entry.get("met")
        else:
            result[code] = None
    return result


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _normalize_previous_criteria(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, Any] = {}
    for code, _ in CRITERIA_ORDER:
        normalized[code] = value.get(code)
    return normalized


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate event-driven context compaction trigger from memory budget, "
            "dossier/go-signal changes, and compaction staleness."
        )
    )
    parser.add_argument(
        "--memory-json",
        type=Path,
        default=Path("docs/context/exec_memory_packet_latest.json"),
    )
    parser.add_argument(
        "--dossier-json",
        type=Path,
        default=Path("docs/context/auditor_promotion_dossier.json"),
    )
    parser.add_argument(
        "--go-signal-md",
        type=Path,
        default=Path("docs/context/ceo_go_signal.md"),
    )
    parser.add_argument(
        "--state-json",
        type=Path,
        default=Path("docs/context/context_compaction_state_latest.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/context/context_compaction_status_latest.json"),
    )
    parser.add_argument("--pm-warn", type=float, default=0.75)
    parser.add_argument("--ceo-warn", type=float, default=0.70)
    parser.add_argument("--force", type=float, default=0.90)
    parser.add_argument("--max-age-hours", type=float, default=24.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    now_utc = _utc_now()
    generated_at_utc = _utc_iso(now_utc)

    try:
        memory = _read_json_object(args.memory_json, required=True)
        dossier = _read_json_object(args.dossier_json, required=True)
        state = _read_json_object(args.state_json, required=False)
        action_current = _parse_action(args.go_signal_md)

        pm_ratio = _extract_ratio(memory, "pm_actual", "pm_budget")
        ceo_ratio = _extract_ratio(memory, "ceo_actual", "ceo_budget")

        criteria_current = _extract_criteria_met(dossier)

        action_previous_raw = state.get("action_current", state.get("action_previous"))
        action_previous = (
            action_previous_raw.strip().upper()
            if isinstance(action_previous_raw, str)
            else None
        )
        criteria_previous = _normalize_previous_criteria(
            state.get("criteria_current", state.get("criteria_previous"))
        )

        reasons: list[str] = []

        if pm_ratio >= args.pm_warn or ceo_ratio >= args.ceo_warn:
            reasons.append("warn_threshold_exceeded")
        if pm_ratio >= args.force or ceo_ratio >= args.force:
            reasons.append("force_threshold_exceeded")

        if action_previous is not None and action_current != action_previous:
            reasons.append("recommended_action_changed")

        changed_codes: list[str] = []
        for code, _ in CRITERIA_ORDER:
            prev = criteria_previous.get(code)
            curr = criteria_current.get(code)
            if code in criteria_previous and prev != curr:
                changed_codes.append(code)
        if changed_codes:
            reasons.append("criteria_changed:" + ",".join(changed_codes))

        freshness_hours_since_last: float | None = None
        last_compacted = _parse_utc(state.get("last_compacted_at_utc"))
        if last_compacted is not None:
            freshness_hours_since_last = max(
                0.0, (now_utc - last_compacted).total_seconds() / 3600.0
            )
            if freshness_hours_since_last > args.max_age_hours:
                reasons.append("stale_since_last_compaction")

        should_compact = len(reasons) > 0

        next_state: dict[str, Any] = {
            "schema_version": "1.0.0",
            "updated_at_utc": generated_at_utc,
            "action_current": action_current,
            "criteria_current": criteria_current,
        }
        if "last_compacted_at_utc" in state:
            next_state["last_compacted_at_utc"] = state["last_compacted_at_utc"]

        _atomic_write_text(args.state_json, json.dumps(next_state, indent=2) + "\n")
        state_updated = True

        payload: dict[str, Any] = {
            "generated_at_utc": generated_at_utc,
            "should_compact": should_compact,
            "reasons": reasons,
            "ratios": {
                "pm_ratio": round(pm_ratio, 6),
                "ceo_ratio": round(ceo_ratio, 6),
            },
            "memory_tier_contract": build_memory_tier_snapshot(
                family_ids=COMPACTION_MEMORY_FAMILIES,
                cold_fallback_ids=COMPACTION_COLD_FALLBACK_FAMILIES,
            ),
            "memory_tier_bindings": {
                "inputs": bind_memory_tier_paths(
                    {
                        "exec_memory_packet": args.memory_json,
                        "auditor_promotion_dossier": args.dossier_json,
                        "ceo_go_signal": args.go_signal_md,
                        "context_compaction_state": args.state_json,
                    }
                ),
                "outputs": bind_memory_tier_paths(
                    {
                        "context_compaction_state": args.state_json,
                        "context_compaction_status": args.output_json,
                    }
                ),
            },
            "action_current": action_current,
            "action_previous": action_previous,
            "criteria_current": criteria_current,
            "criteria_previous": criteria_previous,
            "freshness_hours_since_last": (
                round(freshness_hours_since_last, 3)
                if freshness_hours_since_last is not None
                else None
            ),
            "state_updated": state_updated,
        }

        _atomic_write_text(args.output_json, json.dumps(payload, indent=2) + "\n")
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
