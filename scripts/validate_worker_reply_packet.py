from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


ALLOWED_DOD = {"PASS", "PARTIAL", "FAIL"}
ALLOWED_BAND = {"HIGH", "MEDIUM", "LOW"}
ALLOWED_CITATION_TYPE = {"code", "test", "doc", "log"}
ALLOWED_EXPERTISE_DOMAIN = {
    "system_eng", "architect", "principal", "riskops", "devsecops", "qa"
}
ALLOWED_EXPERTISE_VERDICT = {"APPLIED", "NOT_REQUIRED", "SKIPPED"}
SUPPORTED_SCHEMA_VERSIONS = {"1.0.0", "2.0.0"}
REQUIRED_TRIAD = {"principal", "riskops", "qa"}


def _parse_iso_utc(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _as_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


# ---------------------------------------------------------------------------
# Shared checks (both v1 and v2)
# ---------------------------------------------------------------------------

def _validate_item_shared(
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


# ---------------------------------------------------------------------------
# v1-only checks
# ---------------------------------------------------------------------------

def _validate_item_v1(item: dict, *, item_index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"items[{item_index}]"
    confidence = item.get("confidence")

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

    return errors


# ---------------------------------------------------------------------------
# v2-only checks
# ---------------------------------------------------------------------------

def _validate_confidence_level(
    confidence_level: object, prefix: str
) -> list[str]:
    errors: list[str] = []
    if not isinstance(confidence_level, dict):
        errors.append(f"{prefix}.confidence_level is required")
        return errors
    score = confidence_level.get("score")
    band = _as_str(confidence_level.get("band")).upper()
    rationale = _as_str(confidence_level.get("rationale"))
    if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
        errors.append(f"{prefix}.confidence_level.score must be number in [0.0, 1.0]")
    if band not in ALLOWED_BAND:
        errors.append(
            f"{prefix}.confidence_level.band must be one of {sorted(ALLOWED_BAND)}"
        )
    if not rationale:
        errors.append(f"{prefix}.confidence_level.rationale is required")
    return errors


def _validate_expertise_coverage(
    coverage: object, prefix: str
) -> list[str]:
    errors: list[str] = []
    if not isinstance(coverage, list) or not coverage:
        errors.append(f"{prefix}.expertise_coverage must be a non-empty list")
        return errors
    for idx, entry in enumerate(coverage):
        epfx = f"{prefix}.expertise_coverage[{idx}]"
        if not isinstance(entry, dict):
            errors.append(f"{epfx} must be an object")
            continue
        domain = _as_str(entry.get("domain")).lower()
        verdict = _as_str(entry.get("verdict")).upper()
        rationale = _as_str(entry.get("rationale"))
        if domain not in ALLOWED_EXPERTISE_DOMAIN:
            errors.append(
                f"{epfx}.domain must be one of {sorted(ALLOWED_EXPERTISE_DOMAIN)}"
            )
        if verdict not in ALLOWED_EXPERTISE_VERDICT:
            errors.append(
                f"{epfx}.verdict must be one of {sorted(ALLOWED_EXPERTISE_VERDICT)}"
            )
        if not rationale:
            errors.append(f"{epfx}.rationale is required")
    return errors


def _validate_pm_first_principles(
    fp: object, prefix: str
) -> list[str]:
    errors: list[str] = []
    if not isinstance(fp, dict):
        errors.append(f"{prefix}.pm_first_principles is required")
        return errors
    for field in ("problem", "constraints", "logic", "solution"):
        if not _as_str(fp.get(field)):
            errors.append(f"{prefix}.pm_first_principles.{field} is required")
    return errors


def _validate_response_views(response_views: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(response_views, dict):
        errors.append(f"{prefix}.response_views must be an object")
        return errors

    machine_view = response_views.get("machine_view")
    if not isinstance(machine_view, dict) or not machine_view:
        errors.append(f"{prefix}.response_views.machine_view must be a non-empty object")

    if not _as_str(response_views.get("human_brief")):
        errors.append(f"{prefix}.response_views.human_brief is required")

    if not _as_str(response_views.get("paste_ready_block")):
        errors.append(f"{prefix}.response_views.paste_ready_block is required")

    return errors


def _validate_item_v2(
    item: dict, *, item_index: int, enforce_score_thresholds: bool = False
) -> list[str]:
    errors: list[str] = []
    prefix = f"items[{item_index}]"

    # Reject bare confidence at item level
    if item.get("confidence") is not None:
        errors.append(
            f"{prefix}: v2 packets must use machine_optimized.confidence_level, "
            "not item-level confidence"
        )

    # machine_optimized block
    mo = item.get("machine_optimized")
    if not isinstance(mo, dict):
        errors.append(f"{prefix}.machine_optimized is required")
    else:
        mo_pfx = f"{prefix}.machine_optimized"
        errors.extend(_validate_confidence_level(mo.get("confidence_level"), mo_pfx))

        psa_score = mo.get("problem_solving_alignment_score")
        if not isinstance(psa_score, (int, float)) or not (
            0.0 <= float(psa_score) <= 1.0
        ):
            errors.append(
                f"{mo_pfx}.problem_solving_alignment_score must be number in [0.0, 1.0]"
            )

        errors.extend(_validate_expertise_coverage(mo.get("expertise_coverage"), mo_pfx))

        # --- Enforcement checks (gated by --enforce-score-thresholds) ---
        # GAP 1 FIX: triad + threshold checks are ONLY active when flag is
        # set, so normal G06 runs cannot break repos missing triad rows.
        if enforce_score_thresholds:
            # Score thresholds
            cl = mo.get("confidence_level")
            if isinstance(cl, dict):
                conf_score = cl.get("score")
                if isinstance(conf_score, (int, float)) and float(conf_score) < 0.70:
                    errors.append(
                        f"{mo_pfx}.confidence_level.score={conf_score} "
                        "is below 0.70 threshold (HOLD)"
                    )
            if isinstance(psa_score, (int, float)) and float(psa_score) < 0.75:
                errors.append(
                    f"{mo_pfx}.problem_solving_alignment_score={psa_score} "
                    "is below 0.75 threshold (REFRAME)"
                )

            # Triad structural check: all 3 triad domains must be present
            coverage = mo.get("expertise_coverage")
            if isinstance(coverage, list):
                found_domains = set()
                for entry in coverage:
                    if isinstance(entry, dict):
                        found_domains.add(
                            _as_str(entry.get("domain")).lower()
                        )
                missing = REQUIRED_TRIAD - found_domains
                if missing:
                    errors.append(
                        f"{mo_pfx}.expertise_coverage missing required triad "
                        f"domains: {sorted(missing)}"
                    )

                # Triad substantive check: at least one triad domain must be
                # APPLIED or NOT_REQUIRED (not all SKIPPED)
                if not missing:
                    triad_verdicts = []
                    for entry in coverage:
                        if isinstance(entry, dict):
                            d = _as_str(entry.get("domain")).lower()
                            v = _as_str(entry.get("verdict")).upper()
                            if d in REQUIRED_TRIAD:
                                triad_verdicts.append(v)
                    if triad_verdicts and all(
                        v == "SKIPPED" for v in triad_verdicts
                    ):
                        errors.append(
                            f"{mo_pfx}.expertise_coverage: all triad domains "
                            "are SKIPPED; at least one must be APPLIED or "
                            "NOT_REQUIRED when score thresholds are enforced"
                        )

    # Optional additive split-style response views
    if item.get("response_views") is not None:
        errors.extend(_validate_response_views(item.get("response_views"), prefix))

    # pm_first_principles block
    errors.extend(_validate_pm_first_principles(item.get("pm_first_principles"), prefix))

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

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
        "--schema-version-override",
        type=str,
        default="",
        help="Override packet schema_version for validation dispatch",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print validation findings and force exit 0",
    )
    parser.add_argument(
        "--enforce-score-thresholds",
        action="store_true",
        help=(
            "Enforce score thresholds (confidence >= 0.70, relatability >= 0.75), "
            "triad coverage (principal/riskops/qa present), and triad substantive "
            "quality (at least one triad domain APPLIED or NOT_REQUIRED)"
        ),
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

    # Resolve effective version: override takes precedence
    override = _as_str(args.schema_version_override)
    effective_version = override if override else schema_version

    if not effective_version:
        errors.append("schema_version is required")
    elif effective_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"unsupported schema_version: {effective_version}")

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
            # Shared checks always run
            errors.extend(
                _validate_item_shared(
                    item,
                    item_index=index,
                    repo_root=repo_root,
                    require_existing_paths=args.require_existing_paths,
                )
            )
            # CUTOVER: Enable -EnforceScoreThresholds after all repos pass G05b readiness gate.
            # Phase 25+ will remove v1 path entirely.
            if effective_version == "1.0.0":
                errors.extend(_validate_item_v1(item, item_index=index))
            elif effective_version == "2.0.0":
                errors.extend(
                    _validate_item_v2(
                        item,
                        item_index=index,
                        enforce_score_thresholds=args.enforce_score_thresholds,
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
