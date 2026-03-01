from __future__ import annotations

import json
from pathlib import Path

from scripts.sync_philosophy_feedback import run_sync


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_source(main_repo: Path) -> Path:
    source = main_repo / "top_level_PM.md"
    _write(
        source,
        "\n".join(
            [
                "# Top Level PM",
                "",
                "## 6. Theory of Constraints",
                "- Constraint-first.",
                "",
                "## 7. Cynefin Framework",
                "- Domain-aware control.",
                "",
                "## 8. Ergodicity",
                "- Survival-first.",
            ]
        ),
    )
    return source


def test_run_sync_updates_workers_then_migrates_main(tmp_path: Path) -> None:
    scan_root = tmp_path / "Code"
    main_repo = scan_root / "SOP" / "quant_current_scope"
    _write(main_repo / "docs/lessonss.md", "# lessonss.md\n")
    source = _make_source(main_repo)

    worker_a = scan_root / "WorkerA"
    _write(worker_a / "AGENTS.md", "# agents\n")
    _write(worker_a / "docs/lessonss.md", "# lessonss.md\n")

    worker_b = scan_root / "WorkerB"
    _write(worker_b / "AGENTS.md", "# agents\n")

    log_out = main_repo / "docs/context/philosophy_migration_log.json"
    report_out = main_repo / "docs/context/philosophy_migration_report.md"
    code, payload = run_sync(
        scan_root=scan_root,
        main_repo=main_repo,
        source_path=source,
        log_out=log_out,
        report_out=report_out,
        strict=True,
        update_id="test-sync-1",
        dry_run=False,
    )
    assert code == 0
    assert payload["overall_status"] == "PASS"

    assert "PhilosophySyncID: test-sync-1" in (worker_a / "docs/lessonss.md").read_text(
        encoding="utf-8"
    )
    assert "PhilosophySyncID: test-sync-1" in (worker_b / "docs/lessonss.md").read_text(
        encoding="utf-8"
    )
    assert log_out.exists()
    assert report_out.exists()
    assert "test-sync-1" in (main_repo / "docs/lessonss.md").read_text(encoding="utf-8")

    payload_from_disk = json.loads(log_out.read_text(encoding="utf-8"))
    assert payload_from_disk["overall_status"] == "PASS"


def test_run_sync_blocks_main_migration_when_worker_update_fails(tmp_path: Path) -> None:
    scan_root = tmp_path / "Code"
    main_repo = scan_root / "SOP" / "quant_current_scope"
    _write(main_repo / "docs/lessonss.md", "# lessonss.md\n")
    source = _make_source(main_repo)

    worker_bad = scan_root / "WorkerBad"
    _write(worker_bad / "AGENTS.md", "# agents\n")
    (worker_bad / "docs/lessonss.md").mkdir(parents=True, exist_ok=True)

    log_out = main_repo / "docs/context/philosophy_migration_log.json"
    report_out = main_repo / "docs/context/philosophy_migration_report.md"
    code, payload = run_sync(
        scan_root=scan_root,
        main_repo=main_repo,
        source_path=source,
        log_out=log_out,
        report_out=report_out,
        strict=True,
        update_id="test-sync-block",
        dry_run=False,
    )
    assert code == 1
    assert payload["overall_status"] == "BLOCK"
    main_lessons_text = (main_repo / "docs/lessonss.md").read_text(encoding="utf-8")
    assert "test-sync-block" not in main_lessons_text


def test_run_sync_is_idempotent_for_same_update_id(tmp_path: Path) -> None:
    scan_root = tmp_path / "Code"
    main_repo = scan_root / "SOP" / "quant_current_scope"
    _write(main_repo / "docs/lessonss.md", "# lessonss.md\n")
    source = _make_source(main_repo)

    worker = scan_root / "WorkerA"
    _write(worker / "AGENTS.md", "# agents\n")
    _write(worker / "docs/lessonss.md", "# lessonss.md\n")

    log_out = main_repo / "docs/context/philosophy_migration_log.json"
    report_out = main_repo / "docs/context/philosophy_migration_report.md"
    first_code, _ = run_sync(
        scan_root=scan_root,
        main_repo=main_repo,
        source_path=source,
        log_out=log_out,
        report_out=report_out,
        strict=True,
        update_id="test-sync-idem",
        dry_run=False,
    )
    second_code, second_payload = run_sync(
        scan_root=scan_root,
        main_repo=main_repo,
        source_path=source,
        log_out=log_out,
        report_out=report_out,
        strict=True,
        update_id="test-sync-idem",
        dry_run=False,
    )
    assert first_code == 0
    assert second_code == 0
    assert second_payload["overall_status"] == "PASS"

    worker_text = (worker / "docs/lessonss.md").read_text(encoding="utf-8")
    assert worker_text.count("PhilosophySyncID: test-sync-idem") == 1
    main_text = (main_repo / "docs/lessonss.md").read_text(encoding="utf-8")
    assert main_text.count("test-sync-idem") == 1
