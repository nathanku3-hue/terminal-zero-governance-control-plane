from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path


SCHEMA_VERSION = "1.0.0"
DEFAULT_SCAN_ROOT = Path("E:/Code")
DEFAULT_LOG_OUT = Path("docs/context/philosophy_migration_log.json")
DEFAULT_REPORT_OUT = Path("docs/context/philosophy_migration_report.md")
DEFAULT_SOURCE = Path("top_level_PM.md")
DEFAULT_MAIN_LESSONS = Path("docs/lessonss.md")
PHILOSOPHY_SECTION_IDS = ("6", "7", "8")
IGNORE_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}
DEFAULT_MAX_DISCOVERY_DEPTH = 4


class PhilosophySyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerResult:
    repo_path: str
    local_loop_path: str | None
    status: str
    message: str
    updated: bool


def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso_utc(ts: datetime | None = None) -> str:
    value = ts or _now_utc()
    return value.isoformat().replace("+00:00", "Z")


def _date_utc(ts: datetime | None = None) -> str:
    value = ts or _now_utc()
    return value.date().isoformat()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def _resolve_path(main_repo: Path, path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (main_repo / path).resolve()


def _should_skip_dir(path: Path) -> bool:
    return any(part in IGNORE_PARTS for part in path.parts)


def discover_worker_repos(
    scan_root: Path, main_repo: Path, max_depth: int = DEFAULT_MAX_DISCOVERY_DEPTH
) -> list[Path]:
    if not scan_root.exists():
        raise PhilosophySyncError(f"Scan root does not exist: {scan_root}")

    candidates: set[Path] = set()
    for root, dirs, files in os.walk(scan_root):
        root_path = Path(root).resolve()
        rel_depth = len(root_path.relative_to(scan_root).parts)
        dirs[:] = [name for name in dirs if not _should_skip_dir(root_path / name)]
        if rel_depth >= max_depth:
            dirs[:] = []
        if "AGENTS.md" in files and not _should_skip_dir(root_path):
            if root_path == main_repo:
                continue
            candidates.add(root_path)

    sorted_candidates = sorted(candidates, key=lambda p: (len(p.parts), p.as_posix().lower()))
    pruned: list[Path] = []
    for path in sorted_candidates:
        if any(parent in pruned for parent in path.parents):
            continue
        pruned.append(path)
    return pruned


def _extract_sections_6_8(source_text: str) -> str:
    lines = source_text.splitlines()
    capture = False
    current: list[str] = []
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if any(heading.startswith(f"{idx}.") for idx in PHILOSOPHY_SECTION_IDS):
                if current:
                    out.extend(current)
                    out.append("")
                    current = []
                capture = True
                current.append(line)
                continue
            if capture:
                if current:
                    out.extend(current)
                    out.append("")
                    current = []
                capture = False
        if capture:
            current.append(line)
    if current:
        out.extend(current)
    while out and not out[-1].strip():
        out.pop()
    if not out:
        raise PhilosophySyncError("Failed to extract philosophy sections 6/7/8 from top_level_PM.md")
    return "\n".join(out) + "\n"


def _pick_local_loop_path(repo: Path) -> Path:
    candidates = (
        repo / "docs/lessonss.md",
        repo / "docs/lessons.md",
        repo / "LESSONS_LEARNED.md",
        repo / "docs/LESSONS_LEARNED.md",
    )
    for path in candidates:
        if path.exists():
            return path
    return repo / "docs/lessonss.md"


def _init_local_loop(path: Path) -> str:
    name = path.name.lower()
    if name in {"lessonss.md", "lessons.md"}:
        return (
            "# lessonss.md\n\n"
            "## Purpose\n"
            "Track mistakes, root causes, and guardrails so repeated errors are prevented.\n\n"
            "## Entries\n"
        )
    return "# Lessons Learned\n\n## Entries\n"


def _build_feedback_block(
    *,
    update_id: str,
    update_date: str,
    source_rel: str,
    section_text: str,
) -> str:
    return (
        "\n"
        f"## Philosophy Sync ({update_date})\n"
        f"- PhilosophySyncID: {update_id}\n"
        "- LocalFirstStatus: COMPLETED\n"
        f"- Source: {source_rel}\n"
        "- AppliedSections: 6,7,8\n\n"
        "### Synced Sections\n"
        "```markdown\n"
        f"{section_text.rstrip()}\n"
        "```\n"
    )


def update_worker_local_loop(
    *,
    repo: Path,
    update_id: str,
    update_date: str,
    source_rel: str,
    section_text: str,
) -> WorkerResult:
    loop_path = _pick_local_loop_path(repo)
    try:
        existing = loop_path.read_text(encoding="utf-8") if loop_path.exists() else _init_local_loop(loop_path)
        if f"PhilosophySyncID: {update_id}" in existing:
            return WorkerResult(
                repo_path=repo.as_posix(),
                local_loop_path=loop_path.as_posix(),
                status="PASS",
                message="already synced",
                updated=False,
            )
        updated = existing.rstrip() + _build_feedback_block(
            update_id=update_id,
            update_date=update_date,
            source_rel=source_rel,
            section_text=section_text,
        )
        _atomic_write_text(loop_path, updated + "\n")
        return WorkerResult(
            repo_path=repo.as_posix(),
            local_loop_path=loop_path.as_posix(),
            status="PASS",
            message="local loop updated",
            updated=True,
        )
    except OSError as exc:
        return WorkerResult(
            repo_path=repo.as_posix(),
            local_loop_path=loop_path.as_posix(),
            status="BLOCK",
            message=f"I/O failure: {exc}",
            updated=False,
        )


def preview_worker_local_loop(
    *,
    repo: Path,
    update_id: str,
) -> WorkerResult:
    loop_path = _pick_local_loop_path(repo)
    try:
        existing = loop_path.read_text(encoding="utf-8") if loop_path.exists() else ""
        if f"PhilosophySyncID: {update_id}" in existing:
            return WorkerResult(
                repo_path=repo.as_posix(),
                local_loop_path=loop_path.as_posix(),
                status="PASS",
                message="already synced",
                updated=False,
            )
        return WorkerResult(
            repo_path=repo.as_posix(),
            local_loop_path=loop_path.as_posix(),
            status="PASS",
            message="dry-run: local loop would be updated",
            updated=True,
        )
    except OSError as exc:
        return WorkerResult(
            repo_path=repo.as_posix(),
            local_loop_path=loop_path.as_posix(),
            status="BLOCK",
            message=f"I/O failure: {exc}",
            updated=False,
        )


def _append_main_lessons_row(
    *,
    main_lessons_path: Path,
    update_id: str,
    worker_pass_count: int,
    worker_total_count: int,
    log_rel: str,
) -> None:
    if not main_lessons_path.exists():
        raise PhilosophySyncError(f"Main lessons file is missing: {main_lessons_path}")
    text = main_lessons_path.read_text(encoding="utf-8")
    if update_id in text:
        return
    row = (
        f"| {_date_utc()} | philosophy-sync ({update_id}) | worker philosophy update not propagated to SOP main | "
        "missing local-first migration loop | synchronized worker loops then migrated summary to SOP main | "
        "enforce local-first then main migration as fail-closed gate | "
        f"`{log_rel}`, `top_level_PM.md`, worker `docs/lessonss.md` |\n"
    )
    _atomic_write_text(main_lessons_path, text.rstrip() + "\n" + row)


def _render_report_markdown(log_payload: dict[str, object]) -> str:
    lines = [
        "# Philosophy Migration Report",
        "",
        f"- GeneratedAtUTC: {log_payload['generated_at_utc']}",
        f"- UpdateID: {log_payload['update_id']}",
        f"- ScanRoot: {log_payload['scan_root']}",
        f"- MainRepo: {log_payload['main_repo']}",
        f"- OverallStatus: {log_payload['overall_status']}",
        "",
        "| Repo | Local Loop | Status | Updated | Message |",
        "|---|---|---|---|---|",
    ]
    for item in log_payload["worker_results"]:
        result = dict(item)
        lines.append(
            f"| `{result['repo_path']}` | `{result['local_loop_path']}` | "
            f"{result['status']} | {result['updated']} | {result['message']} |"
        )
    return "\n".join(lines) + "\n"


def run_sync(
    *,
    scan_root: Path,
    main_repo: Path,
    source_path: Path,
    log_out: Path,
    report_out: Path,
    strict: bool,
    update_id: str,
    dry_run: bool,
    worker_repos: list[Path] | None = None,
    max_discovery_depth: int = DEFAULT_MAX_DISCOVERY_DEPTH,
) -> tuple[int, dict[str, object]]:
    if not source_path.exists():
        raise PhilosophySyncError(f"Philosophy source file not found: {source_path}")
    source_text = source_path.read_text(encoding="utf-8")
    section_text = _extract_sections_6_8(source_text)
    source_rel = source_path.relative_to(main_repo).as_posix()

    resolved_worker_repos = (
        sorted({repo.resolve() for repo in worker_repos if repo.resolve() != main_repo})
        if worker_repos
        else discover_worker_repos(
            scan_root=scan_root,
            main_repo=main_repo,
            max_depth=max_discovery_depth,
        )
    )
    results: list[WorkerResult] = []
    for worker in resolved_worker_repos:
        if dry_run:
            results.append(
                preview_worker_local_loop(
                    repo=worker,
                    update_id=update_id,
                )
            )
        else:
            results.append(
                update_worker_local_loop(
                    repo=worker,
                    update_id=update_id,
                    update_date=_date_utc(),
                    source_rel=source_rel,
                    section_text=section_text,
                )
            )

    blocked = [result for result in results if result.status != "PASS"]
    overall_status = "BLOCK" if (blocked and strict) else "PASS"
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _iso_utc(),
        "update_id": update_id,
        "scan_root": scan_root.as_posix(),
        "main_repo": main_repo.as_posix(),
        "worker_repo_count": len(resolved_worker_repos),
        "max_discovery_depth": max_discovery_depth,
        "source_file": source_rel,
        "applied_sections": list(PHILOSOPHY_SECTION_IDS),
        "strict_mode": strict,
        "dry_run": dry_run,
        "overall_status": overall_status,
        "worker_results": [asdict(result) for result in results],
    }

    if dry_run:
        return (0 if overall_status == "PASS" else 1, payload)

    if overall_status == "BLOCK":
        _atomic_write_text(log_out, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
        _atomic_write_text(report_out, _render_report_markdown(payload))
        return (1, payload)

    _atomic_write_text(log_out, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
    _atomic_write_text(report_out, _render_report_markdown(payload))

    main_lessons = main_repo / DEFAULT_MAIN_LESSONS
    log_rel = log_out.relative_to(main_repo).as_posix() if log_out.is_relative_to(main_repo) else log_out.as_posix()
    _append_main_lessons_row(
        main_lessons_path=main_lessons,
        update_id=update_id,
        worker_pass_count=len(results) - len(blocked),
        worker_total_count=len(results),
        log_rel=log_rel,
    )
    return (0, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local-first philosophy sync: update worker loops first, then migrate summary to SOP main."
    )
    parser.add_argument(
        "--scan-root",
        type=Path,
        default=DEFAULT_SCAN_ROOT,
        help="Directory root used to discover worker repos (repos with AGENTS.md).",
    )
    parser.add_argument(
        "--main-repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Main repo path that receives migration logs after local updates pass.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Philosophy source markdown path (relative to --main-repo when not absolute).",
    )
    parser.add_argument(
        "--log-out",
        type=Path,
        default=DEFAULT_LOG_OUT,
        help="JSON migration log output path (relative to --main-repo when not absolute).",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=DEFAULT_REPORT_OUT,
        help="Markdown migration report output path (relative to --main-repo when not absolute).",
    )
    parser.add_argument(
        "--update-id",
        type=str,
        default=f"{_date_utc()}-top-level-philosophy-6-8",
        help="Stable id used for idempotent sync markers.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Block main migration when any worker update fails (default: true).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover and evaluate without writing files.",
    )
    parser.add_argument(
        "--worker-repo",
        action="append",
        default=None,
        help="Optional explicit worker repo path. If provided, discovery scan is skipped.",
    )
    parser.add_argument(
        "--max-discovery-depth",
        type=int,
        default=DEFAULT_MAX_DISCOVERY_DEPTH,
        help="Max recursive depth for AGENTS.md discovery when --worker-repo is not provided.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    main_repo = args.main_repo.resolve()
    scan_root = args.scan_root.resolve()
    source_path = _resolve_path(main_repo, args.source)
    log_out = _resolve_path(main_repo, args.log_out)
    report_out = _resolve_path(main_repo, args.report_out)
    try:
        worker_repos = (
            [_resolve_path(main_repo, Path(raw)) for raw in args.worker_repo]
            if args.worker_repo
            else None
        )
        code, payload = run_sync(
            scan_root=scan_root,
            main_repo=main_repo,
            source_path=source_path,
            log_out=log_out,
            report_out=report_out,
            strict=args.strict,
            update_id=args.update_id.strip(),
            dry_run=args.dry_run,
            worker_repos=worker_repos,
            max_discovery_depth=max(1, int(args.max_discovery_depth)),
        )
    except PhilosophySyncError as exc:
        print(str(exc))
        return 2
    except OSError as exc:
        print(f"I/O failure during philosophy sync: {exc}")
        return 3

    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
