from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Read JSON file, return (data, error)."""
    if not path.exists():
        return None, f"Missing input file: {path}"
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"Failed to read JSON file {path}: {exc}"

    try:
        data = json.loads(raw)
    except Exception as exc:
        return None, f"Invalid JSON in {path}: {exc}"

    if not isinstance(data, dict):
        return None, f"JSON root must be an object: {path}"
    return data, None


def _parse_utc_timestamp(timestamp: str) -> tuple[datetime | None, str | None]:
    """Parse UTC timestamp, return (datetime, error)."""
    try:
        # Handle both Z and +00:00 suffixes
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            return None, "Timestamp missing timezone info"
        return dt, None
    except Exception as exc:
        return None, f"Invalid timestamp format: {exc}"


def _validate_required_fields(packet: dict[str, Any]) -> list[str]:
    """Validate required top-level fields are present."""
    errors = []
    required_fields = [
        "schema_version",
        "generated_at_utc",
        "token_budget",
        "hierarchical_summary",
        "retrieval_namespaces",
        "source_bindings",
        "semantic_claims",
    ]
    for field in required_fields:
        if field not in packet:
            errors.append(f"Missing required field: {field}")
    return errors


def _validate_token_budget(packet: dict[str, Any]) -> list[str]:
    """Validate token budget fields are numeric and coherent."""
    errors = []
    budget = packet.get("token_budget")
    if not isinstance(budget, dict):
        errors.append("token_budget must be a dict")
        return errors

    required_keys = [
        "pm_budget",
        "ceo_budget",
        "pm_actual",
        "ceo_actual",
        "pm_budget_ok",
        "ceo_budget_ok",
    ]
    for key in required_keys:
        if key not in budget:
            errors.append(f"Missing token_budget field: {key}")

    # Check numeric fields
    for key in ["pm_budget", "ceo_budget", "pm_actual", "ceo_actual"]:
        if key in budget and not isinstance(budget[key], (int, float)):
            errors.append(f"token_budget.{key} must be numeric")

    # Check boolean fields
    for key in ["pm_budget_ok", "ceo_budget_ok"]:
        if key in budget and not isinstance(budget[key], bool):
            errors.append(f"token_budget.{key} must be boolean")

    # Check coherence: pass flags should match estimate<=budget
    if all(k in budget for k in ["pm_actual", "pm_budget", "pm_budget_ok"]):
        expected_pm_ok = budget["pm_actual"] <= budget["pm_budget"]
        if budget["pm_budget_ok"] != expected_pm_ok:
            errors.append(
                f"token_budget.pm_budget_ok={budget['pm_budget_ok']} "
                f"inconsistent with pm_actual={budget['pm_actual']} <= pm_budget={budget['pm_budget']}"
            )

    if all(k in budget for k in ["ceo_actual", "ceo_budget", "ceo_budget_ok"]):
        expected_ceo_ok = budget["ceo_actual"] <= budget["ceo_budget"]
        if budget["ceo_budget_ok"] != expected_ceo_ok:
            errors.append(
                f"token_budget.ceo_budget_ok={budget['ceo_budget_ok']} "
                f"inconsistent with ceo_actual={budget['ceo_actual']} <= ceo_budget={budget['ceo_budget']}"
            )

    return errors


def _validate_retrieval_namespaces(packet: dict[str, Any]) -> list[str]:
    """Validate retrieval_namespaces include exactly governance, operations, risk, roadmap."""
    errors = []
    namespaces = packet.get("retrieval_namespaces")
    if not isinstance(namespaces, dict):
        errors.append("retrieval_namespaces must be a dict")
        return errors

    expected_namespaces = {"governance", "operations", "risk", "roadmap"}
    actual_namespaces = set(namespaces.keys())

    missing = expected_namespaces - actual_namespaces
    if missing:
        errors.append(f"Missing retrieval_namespaces: {sorted(missing)}")

    extra = actual_namespaces - expected_namespaces
    if extra:
        errors.append(f"Unexpected retrieval_namespaces: {sorted(extra)}")

    return errors


def _validate_source_bindings(packet: dict[str, Any], repo_root: Path) -> list[str]:
    """Validate each source_binding path exists."""
    errors = []
    bindings = packet.get("source_bindings")
    if not isinstance(bindings, list):
        errors.append("source_bindings must be a list")
        return errors

    for binding in bindings:
        if not isinstance(binding, str):
            errors.append(f"source_binding must be string: {binding}")
            continue

        # Resolve relative paths against repo_root
        binding_path = Path(binding)
        if not binding_path.is_absolute():
            binding_path = repo_root / binding_path

        if not binding_path.exists():
            errors.append(f"source_binding path does not exist: {binding}")

    return errors


def _validate_semantic_claims(packet: dict[str, Any], repo_root: Path) -> list[str]:
    """Validate semantic claims map to real sources and summary text."""
    errors = []
    claims = packet.get("semantic_claims")
    if not isinstance(claims, list):
        errors.append("semantic_claims must be a list")
        return errors

    bindings = packet.get("source_bindings")
    if not isinstance(bindings, list):
        errors.append("source_bindings must be a list for semantic claims validation")
        return errors
    binding_set = {binding for binding in bindings if isinstance(binding, str)}

    hierarchical_summary = packet.get("hierarchical_summary")
    if not isinstance(hierarchical_summary, dict):
        errors.append("hierarchical_summary must be a dict for semantic claims validation")
        return errors

    summary_sections = []
    for section_key in [
        "working_summary",
        "issue_summary",
        "daily_pm_summary",
        "weekly_ceo_summary",
    ]:
        section_text = hierarchical_summary.get(section_key)
        if not isinstance(section_text, str):
            errors.append(
                f"hierarchical_summary.{section_key} must be a string for semantic claims validation"
            )
            continue
        summary_sections.append(section_text)

    required_claim_fields = ["claim_id", "text", "source_path"]
    source_json_cache: dict[str, tuple[dict[str, Any] | None, str | None]] = {}
    for index, claim in enumerate(claims):
        claim_prefix = f"semantic_claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{claim_prefix} must be an object")
            continue

        invalid_claim = False
        for field in required_claim_fields:
            value = claim.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{claim_prefix}.{field} must be a non-empty string")
                invalid_claim = True
        if invalid_claim:
            continue

        claim_text = claim["text"]
        source_path = claim["source_path"]

        if source_path not in binding_set:
            errors.append(f"{claim_prefix}.source_path not found in source_bindings: {source_path}")

        resolved_source = Path(source_path)
        if not resolved_source.is_absolute():
            resolved_source = repo_root / resolved_source
        if not resolved_source.exists():
            errors.append(f"{claim_prefix}.source_path path does not exist: {source_path}")

        if summary_sections and not any(claim_text in section for section in summary_sections):
            errors.append(f"{claim_prefix}.text not found in hierarchical_summary sections: {claim_text}")

        # Contradiction checks only for supported patterns with JSON-backed sources.
        if resolved_source.suffix.lower() != ".json":
            continue

        source_payload: dict[str, Any] | None
        source_error: str | None
        cache_key = str(resolved_source)
        if cache_key in source_json_cache:
            source_payload, source_error = source_json_cache[cache_key]
        else:
            source_payload, source_error = _read_json_object(resolved_source)
            source_json_cache[cache_key] = (source_payload, source_error)

        if source_error is not None or source_payload is None:
            errors.append(f"{claim_prefix}.source_path JSON parse failure: {source_error}")
            continue

        final_result_match = re.fullmatch(r"Final result:\s*(.+?)\s*", claim_text)
        if final_result_match is not None:
            actual_value = final_result_match.group(1).strip()
            expected_raw = source_payload.get("final_result")
            expected_value = (
                str(expected_raw).strip()
                if isinstance(expected_raw, (str, int, float))
                else None
            )
            if expected_value is None or actual_value != expected_value:
                errors.append(
                    f"{claim_prefix} contradiction (Final result): expected={expected_value!r}, actual={actual_value!r}"
                )
            continue

        steps_total_match = re.fullmatch(r"Steps total:\s*(-?\d+)\s*", claim_text)
        if steps_total_match is not None:
            actual_value = int(steps_total_match.group(1))
            step_summary = source_payload.get("step_summary")
            expected_value: int | None = None
            if isinstance(step_summary, dict):
                raw_total_steps = step_summary.get("total_steps")
                if isinstance(raw_total_steps, (int, float)) and not isinstance(raw_total_steps, bool):
                    expected_value = int(raw_total_steps)
                else:
                    raw_total = step_summary.get("total")
                    if isinstance(raw_total, (int, float)) and not isinstance(raw_total, bool):
                        expected_value = int(raw_total)
            if expected_value is None:
                steps = source_payload.get("steps")
                if isinstance(steps, list):
                    expected_value = len(steps)
            if expected_value is None or actual_value != expected_value:
                errors.append(
                    f"{claim_prefix} contradiction (Steps total): expected={expected_value!r}, actual={actual_value!r}"
                )
            continue

        findings_match = re.fullmatch(
            r"Auditor findings:\s*(-?\d+)\s+critical,\s*(-?\d+)\s+high\s*",
            claim_text,
        )
        if findings_match is not None:
            actual_critical = int(findings_match.group(1))
            actual_high = int(findings_match.group(2))
            totals = source_payload.get("totals")
            expected_critical: int | None = None
            expected_high: int | None = None
            if isinstance(totals, dict):
                raw_critical = totals.get("critical")
                raw_high = totals.get("high")
                if isinstance(raw_critical, (int, float)) and not isinstance(raw_critical, bool):
                    expected_critical = int(raw_critical)
                if isinstance(raw_high, (int, float)) and not isinstance(raw_high, bool):
                    expected_high = int(raw_high)
            if (
                expected_critical is None
                or expected_high is None
                or actual_critical != expected_critical
                or actual_high != expected_high
            ):
                errors.append(
                    f"{claim_prefix} contradiction (Auditor findings): expected=({expected_critical!r}, {expected_high!r}), actual=({actual_critical!r}, {actual_high!r})"
                )
            continue

        blockers_match = re.fullmatch(r"Promotion blockers:\s*(.+?)\s*", claim_text)
        if blockers_match is not None:
            actual_raw = blockers_match.group(1).strip()
            actual_set = {
                item.strip()
                for item in actual_raw.split(",")
                if item.strip()
            }
            expected_set: set[str] = set()
            criteria = source_payload.get("promotion_criteria")
            if isinstance(criteria, dict):
                expected_set = {
                    key
                    for key, value in criteria.items()
                    if isinstance(value, dict) and value.get("met") is False
                }
            if actual_set != expected_set:
                errors.append(
                    f"{claim_prefix} contradiction (Promotion blockers): expected={sorted(expected_set)!r}, actual={sorted(actual_set)!r}"
                )
            continue

        items_match = re.fullmatch(r"Items reviewed:\s*(-?\d+)\s*", claim_text)
        if items_match is not None:
            actual_value = int(items_match.group(1))
            expected_value: int | None = None
            totals = source_payload.get("totals")
            if isinstance(totals, dict):
                raw_items = totals.get("items_reviewed")
                if isinstance(raw_items, (int, float)) and not isinstance(raw_items, bool):
                    expected_value = int(raw_items)
            if expected_value is None or actual_value != expected_value:
                errors.append(
                    f"{claim_prefix} contradiction (Items reviewed): expected={expected_value!r}, actual={actual_value!r}"
                )
            continue

    return errors


def _validate_freshness(packet: dict[str, Any], freshness_hours: int) -> list[str]:
    """Validate generated_at_utc is within freshness threshold."""
    errors = []
    timestamp_str = packet.get("generated_at_utc")
    if not isinstance(timestamp_str, str):
        errors.append("generated_at_utc must be a string")
        return errors

    timestamp, parse_error = _parse_utc_timestamp(timestamp_str)
    if parse_error:
        errors.append(f"generated_at_utc parse error: {parse_error}")
        return errors

    if timestamp is None:
        errors.append("generated_at_utc parsing failed")
        return errors

    now = datetime.now(timezone.utc)
    age_hours = (now - timestamp).total_seconds() / 3600

    if age_hours > freshness_hours:
        errors.append(
            f"Packet is stale: age={age_hours:.1f}h exceeds threshold={freshness_hours}h"
        )

    if age_hours < 0:
        errors.append(f"Packet timestamp is in the future: age={age_hours:.1f}h")

    return errors


def _write_output_json(path: Path, status: dict[str, Any]) -> None:
    """Write validation status to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")


def _write_output_md(path: Path, status: dict[str, Any]) -> None:
    """Write validation status to markdown file."""
    lines = [
        "# Exec Memory Packet Validation",
        "",
        f"**Status:** {'✅ PASS' if status['valid'] else '❌ FAIL'}",
        f"**Timestamp:** {status['validated_at_utc']}",
        "",
    ]

    if status["errors"]:
        lines.append("## Errors")
        lines.append("")
        for error in status["errors"]:
            lines.append(f"- {error}")
        lines.append("")

    if status["warnings"]:
        lines.append("## Warnings")
        lines.append("")
        for warning in status["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate exec memory packet truth/freshness. "
            "Exit 0=pass, 1=validation fail, 2=infra/input error."
        )
    )
    parser.add_argument("--memory-json", required=True, help="Path to exec memory packet JSON")
    parser.add_argument(
        "--freshness-hours",
        type=int,
        default=72,
        help="Maximum age in hours (default: 72)",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root for resolving paths")
    parser.add_argument("--output-json", help="Optional output JSON path")
    parser.add_argument("--output-md", help="Optional output markdown path")
    args = parser.parse_args()

    memory_path = Path(args.memory_json)
    repo_root = Path(args.repo_root).resolve()

    # Load packet
    packet, load_error = _read_json_object(memory_path)
    if load_error:
        print(f"[ERROR] {load_error}")
        return 2

    if packet is None:
        print("[ERROR] Failed to load memory packet")
        return 2

    # Run validations
    validation_errors = []
    validation_errors.extend(_validate_required_fields(packet))
    validation_errors.extend(_validate_token_budget(packet))
    validation_errors.extend(_validate_retrieval_namespaces(packet))
    validation_errors.extend(_validate_source_bindings(packet, repo_root))
    validation_errors.extend(_validate_semantic_claims(packet, repo_root))
    validation_errors.extend(_validate_freshness(packet, args.freshness_hours))

    # Determine exit code
    if validation_errors:
        for error in validation_errors:
            print(f"[ERROR] {error}")
        exit_code = 1
    else:
        print("[OK] Exec memory packet validation passed")
        exit_code = 0

    # Write outputs if requested
    if args.output_json or args.output_md:
        status = {
            "valid": exit_code == 0,
            "validated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "errors": validation_errors,
            "warnings": [],
        }

        if args.output_json:
            try:
                _write_output_json(Path(args.output_json), status)
            except Exception as exc:
                print(f"[ERROR] Failed to write output JSON: {exc}")
                return 2

        if args.output_md:
            try:
                _write_output_md(Path(args.output_md), status)
            except Exception as exc:
                print(f"[ERROR] Failed to write output markdown: {exc}")
                return 2

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
