from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0.0"
DEFAULT_CORPUS_DIR = Path("docs/context/profile_outcomes_corpus")
DEFAULT_OUTPUT_JSON = Path("docs/context/profile_selection_ranking_latest.json")
DEFAULT_OUTPUT_MD = Path("docs/context/profile_selection_ranking_latest.md")

WEIGHTS = {
    "shipped_rate": 0.55,
    "ready_rate": 0.35,
    "board_reentry_rate": 0.07,
    "unknown_domain_rate": 0.03,
}

SCORE_FORMULA = (
    "score_0_100 = 100 * clamp01("
    "0.55*shipped_rate + 0.35*ready_rate - 0.07*board_reentry_rate - 0.03*unknown_domain_rate)"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _resolve_path(repo_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in {
        "1",
        "true",
        "yes",
        "y",
        "pass",
        "passed",
        "ok",
        "ready",
        "shipped",
        "go",
        "complete",
        "completed",
    }:
        return True
    if normalized in {
        "0",
        "false",
        "no",
        "n",
        "fail",
        "failed",
        "blocked",
        "block",
        "hold",
        "not_ready",
        "not_shipped",
        "unknown",
    }:
        return False
    return None


def _resolve_bool(record: dict[str, Any], keys: tuple[str, ...], default: bool = False) -> bool:
    for key in keys:
        if key not in record:
            continue
        parsed = _coerce_bool(record[key])
        if parsed is not None:
            return parsed
    return default


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "outcomes", "items", "profile_outcomes"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def _normalize_profile_name(record: dict[str, Any]) -> str:
    for key in ("project_profile", "profile", "projectProfile"):
        value = record.get(key)
        text = str(value).strip() if value is not None else ""
        if text:
            return text
    return ""


def _build_rankings(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aggregates: dict[str, dict[str, int]] = {}
    for record in records:
        profile = _normalize_profile_name(record)
        if not profile:
            continue

        bucket = aggregates.setdefault(
            profile,
            {
                "total_records": 0,
                "shipped_success_count": 0,
                "ready_success_count": 0,
                "board_reentry_count": 0,
                "unknown_domain_count": 0,
            },
        )
        bucket["total_records"] += 1
        bucket["shipped_success_count"] += int(
            _resolve_bool(
                record,
                (
                    "shipped",
                    "shipped_success",
                    "ship_success",
                    "release_shipped",
                    "outcome_shipped",
                ),
            )
        )
        bucket["ready_success_count"] += int(
            _resolve_bool(
                record,
                (
                    "ready",
                    "ready_to_ship",
                    "ready_to_escalate",
                    "startup_ready",
                    "outcome_ready",
                ),
            )
        )
        bucket["board_reentry_count"] += int(
            _resolve_bool(
                record,
                ("board_reentry_required", "board_reentry", "reentered_board"),
            )
        )
        bucket["unknown_domain_count"] += int(
            _resolve_bool(
                record,
                (
                    "unknown_domain_triggered",
                    "unknown_expert_domain",
                    "unknown_domain",
                    "unknown_domain_churn",
                ),
            )
        )

    rankings: list[dict[str, Any]] = []
    for profile, stats in aggregates.items():
        total = max(1, stats["total_records"])
        shipped_rate = stats["shipped_success_count"] / total
        ready_rate = stats["ready_success_count"] / total
        board_reentry_rate = stats["board_reentry_count"] / total
        unknown_domain_rate = stats["unknown_domain_count"] / total

        raw_score = (
            (WEIGHTS["shipped_rate"] * shipped_rate)
            + (WEIGHTS["ready_rate"] * ready_rate)
            - (WEIGHTS["board_reentry_rate"] * board_reentry_rate)
            - (WEIGHTS["unknown_domain_rate"] * unknown_domain_rate)
        )
        clamped_score = min(1.0, max(0.0, raw_score))

        rankings.append(
            {
                "project_profile": profile,
                "total_records": stats["total_records"],
                "shipped_success_count": stats["shipped_success_count"],
                "ready_success_count": stats["ready_success_count"],
                "board_reentry_count": stats["board_reentry_count"],
                "unknown_domain_count": stats["unknown_domain_count"],
                "shipped_rate": round(shipped_rate, 4),
                "ready_rate": round(ready_rate, 4),
                "board_reentry_rate": round(board_reentry_rate, 4),
                "unknown_domain_rate": round(unknown_domain_rate, 4),
                "score": round(clamped_score * 100.0, 2),
            }
        )

    rankings.sort(
        key=lambda item: (
            -float(item["score"]),
            -int(item["total_records"]),
            str(item["project_profile"]).lower(),
        )
    )
    for index, item in enumerate(rankings, start=1):
        item["rank"] = index
    return rankings


def _build_evidence_summary(top_ranking: dict[str, Any] | None) -> str:
    if top_ranking is None:
        return "No valid profile outcome records were found in the local corpus."
    return (
        f"Top profile {top_ranking['project_profile']} from {top_ranking['total_records']} local outcome records; "
        f"shipped_rate={top_ranking['shipped_rate']}, ready_rate={top_ranking['ready_rate']}, "
        f"board_reentry_rate={top_ranking['board_reentry_rate']}, "
        f"unknown_domain_rate={top_ranking['unknown_domain_rate']}."
    )


def _build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Profile Selection Ranking (Advisory)",
        "",
        f"**Generated:** {payload['generated_at_utc']}",
        f"**Status:** {payload['status']}",
        f"**CorpusDir:** `{payload['corpus']['path']}`",
        f"**FilesScanned:** {payload['corpus']['files_scanned']}",
        f"**RecordsUsed:** {payload['corpus']['records_used']}",
        f"**MalformedRecords:** {payload['corpus']['records_malformed']}",
        f"**Confidence:** {payload['confidence'] if payload['confidence'] is not None else 'N/A'}",
        f"**EvidenceSummary:** {payload['evidence_summary']}",
        "",
        "## Scoring Formula",
        f"- `{payload['scoring']['formula']}`",
        (
            f"- Weights: shipped={payload['scoring']['weights']['shipped_rate']}, "
            f"ready={payload['scoring']['weights']['ready_rate']}, "
            f"board_reentry_penalty={payload['scoring']['weights']['board_reentry_rate']}, "
            f"unknown_domain_penalty={payload['scoring']['weights']['unknown_domain_rate']}"
        ),
        "",
    ]

    malformed_files = payload["corpus"]["malformed_files"]
    if malformed_files:
        lines.extend(["## Malformed Files", *[f"- `{name}`" for name in malformed_files], ""])

    if payload["status"] == "NO_DATA":
        lines.extend(
            [
                "## Ranking",
                "- No valid profile outcome records were found.",
                "",
                "```text",
                "PROFILE_SELECTION_STATUS: NO_DATA",
                "RECOMMENDED_PROFILE: none",
                "```",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "## Ranking",
            "| Rank | Profile | Score | Records | Shipped | Ready | BoardReentry | UnknownDomain |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["profile_rankings"]:
        lines.append(
            "| {rank} | {profile} | {score:.2f} | {records} | {shipped:.4f} | {ready:.4f} | {board:.4f} | {unknown:.4f} |".format(
                rank=row["rank"],
                profile=row["project_profile"],
                score=float(row["score"]),
                records=row["total_records"],
                shipped=float(row["shipped_rate"]),
                ready=float(row["ready_rate"]),
                board=float(row["board_reentry_rate"]),
                unknown=float(row["unknown_domain_rate"]),
            )
        )

    lines.extend(
        [
            "",
            "```text",
            f"PROFILE_SELECTION_STATUS: {payload['status']}",
            f"RECOMMENDED_PROFILE: {payload['recommended_profile'] or 'none'}",
            f"TOP_SCORE: {payload['profile_rankings'][0]['score'] if payload['profile_rankings'] else 0}",
            "ADVISORY_ONLY: YES",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an offline deterministic advisory ranking for startup project profiles "
            "from local profile outcome records."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    corpus_dir = _resolve_path(repo_root, args.corpus_dir)
    output_json = _resolve_path(repo_root, args.output_json)
    output_md = _resolve_path(repo_root, args.output_md)
    json_files = sorted(corpus_dir.glob("*.json")) if corpus_dir.exists() else []

    malformed_files: list[str] = []
    raw_records_total = 0
    used_records_total = 0
    malformed_records_total = 0
    collected_records: list[dict[str, Any]] = []

    for file_path in json_files:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            malformed_files.append(file_path.name)
            continue

        extracted = _extract_records(payload)
        raw_records_total += len(extracted)
        for record in extracted:
            profile = _normalize_profile_name(record)
            if not profile:
                malformed_records_total += 1
                continue
            collected_records.append(record)
            used_records_total += 1

    rankings = _build_rankings(collected_records)
    status = "RANKED" if rankings else "NO_DATA"
    top_ranking = rankings[0] if rankings else None
    confidence = (
        round(float(top_ranking["score"]) / 100.0, 4)
        if top_ranking is not None
        else None
    )

    result_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "advisory_only": True,
        "control_plane_impact": "none",
        "status": status,
        "recommended_profile": top_ranking["project_profile"] if top_ranking else None,
        "score": top_ranking["score"] if top_ranking else None,
        "confidence": confidence,
        "evidence_summary": _build_evidence_summary(top_ranking),
        "scoring": {
            "formula": SCORE_FORMULA,
            "weights": WEIGHTS,
            "tie_break_order": [
                "score_desc",
                "total_records_desc",
                "project_profile_asc",
            ],
        },
        "corpus": {
            "path": str(corpus_dir),
            "files_scanned": len(json_files),
            "files_loaded": len(json_files) - len(malformed_files),
            "malformed_files": malformed_files,
            "records_total": raw_records_total,
            "records_used": used_records_total,
            "records_malformed": malformed_records_total,
        },
        "ranking": rankings,
        "profile_rankings": rankings,
    }

    markdown_text = _build_markdown(result_payload)
    _atomic_write_text(output_json, json.dumps(result_payload, indent=2) + "\n")
    _atomic_write_text(output_md, markdown_text)

    print(f"PROFILE_SELECTION_STATUS: {status}")
    print(f"RECOMMENDED_PROFILE: {result_payload['recommended_profile'] or 'none'}")
    print(f"CORPUS_FILES_SCANNED: {len(json_files)}")
    print(f"MALFORMED_FILES: {len(malformed_files)}")
    print(f"RECORDS_USED: {used_records_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
