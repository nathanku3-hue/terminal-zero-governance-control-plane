from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


ALLOWED_DOD = {"PASS", "PARTIAL", "FAIL"}
ALLOWED_BAND = {"HIGH", "MEDIUM", "LOW"}
ALLOWED_CITATION_TYPE = {"code", "test", "doc", "log"}


def _parse_iso_utc(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _as_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _validate_item(
    item: dict,
    *,
    item_index: int,
    repo_root: Path,
    require_existing_paths: bool,
) -> list[str]:
    errors: list[str] = []
    prefix = f"items[{item_index}]"

    task_id = _as_str(item.get("task_id"))
    decision = _as_str(item.get("decision"))
    dod_result = _as_str(item.get("dod_result")).upper()
    evidence_ids = item.get("evidence_ids")
    open_risks = item.get("open_risks")
    confidence = item.get("confidence")
    citations = item.get("citations")

    if not task_id:
        errors.append(f"{prefix}.task_id is required")
    if not decision:
        errors.append(f"{prefix}.decision is required")
    if dod_result not in ALLOWED_DOD:
        errors.append(f"{prefix}.dod_result must be one of {sorted(ALLOWED_DOD)}")
    if not isinstance(evidence_ids, list) or not evidence_ids:
        errors.append(f"{prefix}.evidence_ids must be a non-empty list")
    if not isinstance(open_risks, list):
        errors.append(f"{prefix}.open_risks must be a list")

    if not isinstance(confidence, dict):
        errors.append(f"{prefix}.confidence is required")
    else:
        score = confidence.get("score")
        band = _as_str(confidence.get("band")).upper()
        rationale = _as_str(confidence.get("rationale"))
        if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
            errors.append(f"{prefix}.confidence.score must be number in [0.0, 1.0]")
        if band not in ALLOWED_BAND:
            errors.append(
                f"{prefix}.confidence.band must be one of {sorted(ALLOWED_BAND)}"
            )
        if not rationale:
            errors.append(f"{prefix}.confidence.rationale is required")

    if not isinstance(citations, list) or not citations:
        errors.append(f"{prefix}.citations must be a non-empty list")
    else:
        for citation_index, citation in enumerate(citations):
            cpfx = f"{prefix}.citations[{citation_index}]"
            if not isinstance(citation, dict):
                errors.append(f"{cpfx} must be an object")
                continue
            citation_type = _as_str(citation.get("type")).lower()
            citation_path = _as_str(citation.get("path"))
            locator = _as_str(citation.get("locator"))
            claim = _as_str(citation.get("claim"))

            if citation_type not in ALLOWED_CITATION_TYPE:
                errors.append(
                    f"{cpfx}.type must be one of {sorted(ALLOWED_CITATION_TYPE)}"
                )
            if not citation_path:
                errors.append(f"{cpfx}.path is required")
            if not locator:
                errors.append(f"{cpfx}.locator is required")
            if not claim:
                errors.append(f"{cpfx}.claim is required")
            if require_existing_paths and citation_path:
                abs_path = (repo_root / citation_path).resolve()
                if not abs_path.exists():
                    errors.append(f"{cpfx}.path does not exist: {citation_path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to worker reply packet JSON",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=".",
        help="Repo root used to resolve citation paths when --require-existing-paths is set",
    )
    parser.add_argument(
        "--require-existing-paths",
        action="store_true",
        help="Fail when citations refer to paths that do not exist on disk",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print validation findings and force exit 0",
    )
    args = parser.parse_args()

    in_path = Path(args.input).resolve()
    repo_root = Path(args.repo_root).resolve()
    if not in_path.exists():
        print(f"Error: worker reply packet not found at {in_path}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print("Error: packet must be a JSON object", file=sys.stderr)
        return 1

    errors: list[str] = []
    schema_version = _as_str(payload.get("schema_version"))
    worker_id = _as_str(payload.get("worker_id"))
    phase = _as_str(payload.get("phase"))
    generated_at_utc = _as_str(payload.get("generated_at_utc"))
    items = payload.get("items")

    if not schema_version:
        errors.append("schema_version is required")
    if not worker_id:
        errors.append("worker_id is required")
    if not phase:
        errors.append("phase is required")
    if not generated_at_utc or _parse_iso_utc(generated_at_utc) is None:
        errors.append("generated_at_utc must be valid ISO-8601 UTC timestamp")
    if not isinstance(items, list) or not items:
        errors.append("items must be a non-empty list")
    else:
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"items[{index}] must be an object")
                continue
            errors.extend(
                _validate_item(
                    item,
                    item_index=index,
                    repo_root=repo_root,
                    require_existing_paths=args.require_existing_paths,
                )
            )

    if errors:
        for line in errors:
            print(f"[ERROR] {line}")
        if args.dry_run:
            print("[DRY-RUN] Validation failed but forcing exit 0.")
            return 0
        return 1

    if args.dry_run:
        print("[DRY-RUN] Validation passed. No writes performed.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
