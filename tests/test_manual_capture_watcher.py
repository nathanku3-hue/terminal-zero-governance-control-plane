from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path

import pytest

from scripts.manual_capture_watcher import _load_or_init_registry
from scripts.manual_capture_watcher import _load_or_init_state
from scripts.manual_capture_watcher import _iso_utc
from scripts.manual_capture_watcher import _load_or_init_alerts
from scripts.manual_capture_watcher import _update_index_lines
from scripts.manual_capture_watcher import ManualCaptureError
from scripts.manual_capture_watcher import ensure_queue_payload
from scripts.manual_capture_watcher import infer_task_id
from scripts.manual_capture_watcher import load_index_rows
from scripts.manual_capture_watcher import process_cycle
from scripts.manual_capture_watcher import summarize_queue


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_index(path: Path) -> None:
    _write(
        path,
        "\n".join(
            [
                "| ID | Gate | Result | Date | Evidence |",
                "|---|---|---|---|---|",
                "| gate1 | Status Aggregation | PASS | 2026-03-01 | [Log](T12_gate1_20260301.log) |",
                "| gate2 | Traceability Gate | PASS | 2026-03-01 | [Log](T12_gate2_20260301.log) |",
                "| manual1 | CEO Paste Test | Machine PASS + Manual Pending | 2026-03-01 | [Img](REAL_CAPTURE_MISSING) <br> *Criteria: Digest paste has no formatting breaks.* |",
                "| manual2 | CommandPlan Round-Trip | Machine PASS + Manual Pending | 2026-03-01 | [Img](REAL_CAPTURE_MISSING) <br> *Criteria: Manifest is ACKED and COMPLETED.* |",
                "| manual3 | Digest Readability | Machine PASS + Manual Pending | 2026-03-01 | [Img](REAL_CAPTURE_MISSING) <br> *Criteria: Matrix renders as readable table.* |",
            ]
        )
        + "\n",
    )


def _fake_png(path: Path, size: int = 2048) -> None:
    payload = b"\x89PNG\r\n\x1a\n" + (b"\x00" * max(0, size - 8))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_infer_task_id_and_capture_acceptance_updates_manual_row(tmp_path: Path) -> None:
    index_path = tmp_path / "e2e" / "index.md"
    queue_path = tmp_path / "e2e" / "manual_capture_queue.json"
    alerts_path = tmp_path / "e2e" / "manual_capture_alerts.json"
    drop_dir = tmp_path / "drop"
    evidence_dir = tmp_path / "e2e"
    _build_index(index_path)

    lines, rows = load_index_rows(index_path)
    assert len(rows) == 3
    task_id = infer_task_id(lines)
    assert task_id == "T12"

    now = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    queue = ensure_queue_payload(
        queue_path=queue_path,
        rows=rows,
        task_id=task_id,
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        now=now,
    )
    alerts = _load_or_init_alerts(alerts_path, _iso_utc(now))

    capture_name = "T12_manual1_ceo_paste_20260301.png"
    _fake_png(drop_dir / capture_name)

    queue = process_cycle(
        queue=queue,
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        warn_minutes=15,
        block_minutes=30,
        min_image_bytes=32,
        move_from_drop=False,
        accept_any_filename=False,
        now=now,
        alerts=alerts,
    )
    summary = summarize_queue(queue)
    assert summary["received"] == 1
    assert summary["pending"] == 2
    assert (evidence_dir / capture_name).exists()

    updated = _update_index_lines(lines=lines, rows=rows, queue=queue, now=now)
    manual1 = [line for line in updated if line.startswith("| manual1 |")][0]
    assert "| PASS | 2026-03-01 |" in manual1
    assert f"[Img]({capture_name})" in manual1


def test_block_state_after_threshold_marks_index_block(tmp_path: Path) -> None:
    index_path = tmp_path / "e2e" / "index.md"
    queue_path = tmp_path / "e2e" / "manual_capture_queue.json"
    alerts_path = tmp_path / "e2e" / "manual_capture_alerts.json"
    drop_dir = tmp_path / "drop"
    evidence_dir = tmp_path / "e2e"
    _build_index(index_path)

    lines, rows = load_index_rows(index_path)
    now = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    queue = ensure_queue_payload(
        queue_path=queue_path,
        rows=rows,
        task_id="T12",
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        now=now,
    )
    for item in queue["items"]:
        item["created_at_utc"] = _iso_utc(now - timedelta(minutes=31))

    alerts = _load_or_init_alerts(alerts_path, _iso_utc(now))
    queue = process_cycle(
        queue=queue,
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        warn_minutes=15,
        block_minutes=30,
        min_image_bytes=32,
        move_from_drop=False,
        accept_any_filename=False,
        now=now,
        alerts=alerts,
    )
    summary = summarize_queue(queue)
    assert summary["blocked"] == 3

    updated = _update_index_lines(lines=lines, rows=rows, queue=queue, now=now)
    assert any("| manual1 | CEO Paste Test | BLOCK | 2026-03-01 |" in line for line in updated)
    assert any("| manual2 | CommandPlan Round-Trip | BLOCK | 2026-03-01 |" in line for line in updated)


def test_warn_state_after_warn_threshold_without_block(tmp_path: Path) -> None:
    index_path = tmp_path / "e2e" / "index.md"
    queue_path = tmp_path / "e2e" / "manual_capture_queue.json"
    alerts_path = tmp_path / "e2e" / "manual_capture_alerts.json"
    drop_dir = tmp_path / "drop"
    evidence_dir = tmp_path / "e2e"
    _build_index(index_path)

    lines, rows = load_index_rows(index_path)
    now = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    queue = ensure_queue_payload(
        queue_path=queue_path,
        rows=rows,
        task_id="T12",
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        now=now,
    )
    for item in queue["items"]:
        item["created_at_utc"] = _iso_utc(now - timedelta(minutes=16))

    alerts = _load_or_init_alerts(alerts_path, _iso_utc(now))
    queue = process_cycle(
        queue=queue,
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        warn_minutes=15,
        block_minutes=30,
        min_image_bytes=32,
        move_from_drop=False,
        accept_any_filename=False,
        now=now,
        alerts=alerts,
    )
    summary = summarize_queue(queue)
    assert summary["warned"] == 3
    assert summary["blocked"] == 0


def test_accept_any_filename_assigns_fifo_without_naming(tmp_path: Path) -> None:
    index_path = tmp_path / "e2e" / "index.md"
    queue_path = tmp_path / "e2e" / "manual_capture_queue.json"
    alerts_path = tmp_path / "e2e" / "manual_capture_alerts.json"
    drop_dir = tmp_path / "drop"
    evidence_dir = tmp_path / "e2e"
    _build_index(index_path)

    lines, rows = load_index_rows(index_path)
    now = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    queue = ensure_queue_payload(
        queue_path=queue_path,
        rows=rows,
        task_id="T12",
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        now=now,
    )
    alerts = _load_or_init_alerts(alerts_path, _iso_utc(now))

    _fake_png(drop_dir / "IMG_1001.png", size=4096)

    queue = process_cycle(
        queue=queue,
        drop_dir=drop_dir,
        evidence_dir=evidence_dir,
        warn_minutes=15,
        block_minutes=30,
        min_image_bytes=32,
        move_from_drop=False,
        accept_any_filename=True,
        now=now,
        alerts=alerts,
    )
    summary = summarize_queue(queue)
    assert summary["received"] == 1
    first_item = [item for item in queue["items"] if item["id"] == "manual1"][0]
    assert first_item["evidence_file"].startswith("T12_manual1_")
    assert first_item["evidence_file"].endswith(".png")
    assert (evidence_dir / first_item["evidence_file"]).exists()


def test_corrupt_queue_json_is_quarantined_instead_of_reset(tmp_path: Path) -> None:
    index_path = tmp_path / "e2e" / "index.md"
    queue_path = tmp_path / "e2e" / "manual_capture_queue.json"
    drop_dir = tmp_path / "drop"
    evidence_dir = tmp_path / "e2e"
    _build_index(index_path)
    _write(queue_path, "{not valid json")

    lines, rows = load_index_rows(index_path)
    now = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(ManualCaptureError, match="Malformed JSON"):
        ensure_queue_payload(
            queue_path=queue_path,
            rows=rows,
            task_id="T12",
            drop_dir=drop_dir,
            evidence_dir=evidence_dir,
            now=now,
        )

    quarantined = list(queue_path.parent.glob("manual_capture_queue.corrupt.*.json"))
    assert len(quarantined) == 1
    assert not queue_path.exists()


@pytest.mark.parametrize(
    ("loader", "filename"),
    [
        (_load_or_init_alerts, "manual_capture_alerts.json"),
        (_load_or_init_state, "repo_capture_state.json"),
        (_load_or_init_registry, "repo_capture_registry.json"),
    ],
)
def test_corrupt_loader_state_is_quarantined(loader, filename: str, tmp_path: Path) -> None:
    path = tmp_path / filename
    _write(path, "[]")
    now_iso = "2026-03-01T10:00:00Z"

    with pytest.raises(ManualCaptureError, match="quarantined"):
        loader(path, now_iso)

    quarantined = list(path.parent.glob(f"{path.stem}.corrupt.*{path.suffix}"))
    assert len(quarantined) == 1
    assert not path.exists()
