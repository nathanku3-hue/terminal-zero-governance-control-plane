from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts import run_fast_checks


def _fake_subprocess_run_factory(outcomes: dict[str, subprocess.CompletedProcess[str]]):
    def _fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        command_text = " ".join(command)
        if "validate_loop_closure.py" in command_text:
            return outcomes["validate_loop_closure"]
        if "run_loop_cycle.py" in command_text:
            return outcomes["run_loop_cycle"]
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown command")

    return _fake_run


def test_parse_args_defaults() -> None:
    args = run_fast_checks.parse_args([])
    assert args.repo_root == Path(".")
    assert args.json_out is None
    assert isinstance(args.python_exe, str)
    assert args.python_exe


def test_run_fast_checks_returns_hold_when_closure_not_ready(monkeypatch, tmp_path: Path) -> None:
    outcomes = {
        "validate_loop_closure": subprocess.CompletedProcess(
            ["python", "scripts/validate_loop_closure.py"],
            1,
            stdout="NOT_READY\n",
            stderr="",
        ),
        "run_loop_cycle": subprocess.CompletedProcess(
            ["python", "scripts/run_loop_cycle.py"],
            0,
            stdout="HOLD\n",
            stderr="",
        ),
    }
    monkeypatch.setattr(
        run_fast_checks.subprocess,
        "run",
        _fake_subprocess_run_factory(outcomes),
    )

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path)])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 0
    assert payload["overall_status"] == "HOLD"
    status_by_name = {item["name"]: item["status"] for item in payload["checks"]}
    assert status_by_name["validate_loop_closure"] == "HOLD"
    assert status_by_name["run_loop_cycle"] == "HOLD"


def test_run_fast_checks_returns_pass_when_all_pass(monkeypatch, tmp_path: Path) -> None:
    outcomes = {
        "validate_loop_closure": subprocess.CompletedProcess(
            ["python", "scripts/validate_loop_closure.py"],
            0,
            stdout="READY_TO_ESCALATE\n",
            stderr="",
        ),
        "run_loop_cycle": subprocess.CompletedProcess(
            ["python", "scripts/run_loop_cycle.py"],
            0,
            stdout="PASS\n",
            stderr="",
        ),
    }
    monkeypatch.setattr(
        run_fast_checks.subprocess,
        "run",
        _fake_subprocess_run_factory(outcomes),
    )

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path)])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 0
    assert payload["overall_status"] == "PASS"


def test_run_fast_checks_fails_when_run_loop_cycle_output_is_ambiguous(
    monkeypatch,
    tmp_path: Path,
) -> None:
    outcomes = {
        "validate_loop_closure": subprocess.CompletedProcess(
            ["python", "scripts/validate_loop_closure.py"],
            0,
            stdout="READY_TO_ESCALATE\n",
            stderr="",
        ),
        "run_loop_cycle": subprocess.CompletedProcess(
            ["python", "scripts/run_loop_cycle.py"],
            0,
            stdout="completed without explicit verdict\n",
            stderr="",
        ),
    }
    monkeypatch.setattr(
        run_fast_checks.subprocess,
        "run",
        _fake_subprocess_run_factory(outcomes),
    )

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path)])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 1
    assert payload["overall_status"] == "FAIL"
    status_by_name = {item["name"]: item["status"] for item in payload["checks"]}
    assert status_by_name["run_loop_cycle"] == "FAIL"


def test_run_fast_checks_returns_fail_on_hard_error(monkeypatch, tmp_path: Path) -> None:
    outcomes = {
        "validate_loop_closure": subprocess.CompletedProcess(
            ["python", "scripts/validate_loop_closure.py"],
            2,
            stdout="INPUT_OR_INFRA_ERROR\n",
            stderr="",
        ),
        "run_loop_cycle": subprocess.CompletedProcess(
            ["python", "scripts/run_loop_cycle.py"],
            0,
            stdout="HOLD\n",
            stderr="",
        ),
    }
    monkeypatch.setattr(
        run_fast_checks.subprocess,
        "run",
        _fake_subprocess_run_factory(outcomes),
    )

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path)])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 1
    assert payload["overall_status"] == "FAIL"
    assert any(item["status"] == "FAIL" for item in payload["checks"])


def test_main_writes_json_output(monkeypatch, tmp_path: Path) -> None:
    outcomes = {
        "validate_loop_closure": subprocess.CompletedProcess(
            ["python", "scripts/validate_loop_closure.py"],
            0,
            stdout="READY_TO_ESCALATE\n",
            stderr="",
        ),
        "run_loop_cycle": subprocess.CompletedProcess(
            ["python", "scripts/run_loop_cycle.py"],
            0,
            stdout="PASS\n",
            stderr="",
        ),
    }
    monkeypatch.setattr(
        run_fast_checks.subprocess,
        "run",
        _fake_subprocess_run_factory(outcomes),
    )

    json_out = tmp_path / "fast_checks.json"
    exit_code = run_fast_checks.main(["--repo-root", str(tmp_path), "--json-out", str(json_out)])
    assert exit_code == 0
    assert json_out.exists()
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "PASS"
    assert len(payload["checks"]) == 2


def test_run_fast_checks_refreshes_cycle_before_closure_validation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    state = {"cycle_ran": False}

    def _fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        command_text = " ".join(command)
        if "run_loop_cycle.py" in command_text:
            state["cycle_ran"] = True
            return subprocess.CompletedProcess(command, 0, stdout="PASS\n", stderr="")
        if "validate_loop_closure.py" in command_text:
            if state["cycle_ran"]:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="READY_TO_ESCALATE\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(command, 1, stdout="NOT_READY\n", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown command")

    monkeypatch.setattr(run_fast_checks.subprocess, "run", _fake_run)

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path)])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 0
    assert payload["overall_status"] == "PASS"
    assert [item["name"] for item in payload["checks"]] == [
        "run_loop_cycle",
        "validate_loop_closure",
    ]
