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
        if "startup_codex_helper.py" in command_text:
            # Default neutral READY response for tests not focused on startup_gate
            return outcomes.get(
                "startup_gate",
                subprocess.CompletedProcess(
                    command, 0,
                    stdout="STARTUP_SUMMARY: CODEX\nREADINESS_STATUS: READY\n",
                    stderr="",
                ),
            )
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
    assert len(payload["checks"]) == 3  # startup_gate, run_loop_cycle, validate_loop_closure


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
        if "startup_codex_helper.py" in command_text:
            return subprocess.CompletedProcess(command, 0, stdout="STARTUP_SUMMARY: CODEX\nREADINESS_STATUS: READY\n", stderr="")
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
        "startup_gate",
        "run_loop_cycle",
        "validate_loop_closure",
    ]


# ---------------------------------------------------------------------------
# P2 item 2: event-driven quality checkpoints (RED -> GREEN after implementation)
# ---------------------------------------------------------------------------


def test_check_selector_runs_only_named_checks(monkeypatch, tmp_path: Path) -> None:
    """--check <name> runs only that check, not the full default set."""
    called: list[str] = []

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
            called.append("validate_loop_closure")
            return subprocess.CompletedProcess(command, 0, stdout="READY_TO_ESCALATE\n", stderr="")
        if "run_loop_cycle.py" in command_text:
            called.append("run_loop_cycle")
            return subprocess.CompletedProcess(command, 0, stdout="PASS\n", stderr="")
        if "startup_codex_helper.py" in command_text:
            called.append("startup_gate")
            return subprocess.CompletedProcess(command, 0, stdout="STARTUP_SUMMARY: CODEX\nREADINESS_STATUS: READY\n", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown command")

    monkeypatch.setattr(run_fast_checks.subprocess, "run", _fake_run)

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path), "--check", "validate_loop_closure"])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 0
    assert payload["overall_status"] == "PASS"
    assert called == ["validate_loop_closure"]  # only the selected check ran
    assert len(payload["checks"]) == 1
    assert payload["checks"][0]["name"] == "validate_loop_closure"


def test_startup_gate_check_passes_when_readiness_ready(monkeypatch, tmp_path: Path) -> None:
    """startup_gate check returns PASS when startup summary reports READINESS_STATUS: READY."""

    def _fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        command_text = " ".join(command)
        if "startup_codex_helper.py" in command_text and "--summary" in command_text:
            return subprocess.CompletedProcess(
                command, 0,
                stdout="STARTUP_SUMMARY: CODEX\nREADINESS_STATUS: READY\nP2_AUTHORIZATION: ACTIVE\n",
                stderr="",
            )
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown")

    monkeypatch.setattr(run_fast_checks.subprocess, "run", _fake_run)

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path), "--check", "startup_gate"])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 0
    assert payload["overall_status"] == "PASS"
    status_by_name = {item["name"]: item["status"] for item in payload["checks"]}
    assert status_by_name["startup_gate"] == "PASS"


def test_startup_gate_check_fails_when_readiness_needs_attention(monkeypatch, tmp_path: Path) -> None:
    """startup_gate check returns HOLD when startup summary reports READINESS_STATUS: NEEDS_ATTENTION."""

    def _fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        command_text = " ".join(command)
        if "startup_codex_helper.py" in command_text and "--summary" in command_text:
            return subprocess.CompletedProcess(
                command, 0,
                stdout="STARTUP_SUMMARY: CODEX\nREADINESS_STATUS: NEEDS_ATTENTION\nMISSING_DOCS: docs/context/ceo_go_signal.md\n",
                stderr="",
            )
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown")

    monkeypatch.setattr(run_fast_checks.subprocess, "run", _fake_run)

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path), "--check", "startup_gate"])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 0  # HOLD default does not fail
    assert payload["overall_status"] == "HOLD"
    status_by_name = {item["name"]: item["status"] for item in payload["checks"]}
    assert status_by_name["startup_gate"] == "HOLD"


def test_freshness_hours_forwarded_to_validate_loop_closure(monkeypatch, tmp_path: Path) -> None:
    """--freshness-hours is passed through to validate_loop_closure check."""
    captured_args: list[str] = []

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
            captured_args[:] = command
            return subprocess.CompletedProcess(command, 0, stdout="READY_TO_ESCALATE\n", stderr="")
        if "run_loop_cycle.py" in command_text:
            return subprocess.CompletedProcess(command, 0, stdout="PASS\n", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown")

    monkeypatch.setattr(run_fast_checks.subprocess, "run", _fake_run)

    args = run_fast_checks.parse_args([
        "--repo-root", str(tmp_path),
        "--check", "validate_loop_closure",
        "--freshness-hours", "24",
    ])
    run_fast_checks.run_fast_checks(args)

    assert "--freshness-hours" in captured_args
    idx = captured_args.index("--freshness-hours")
    assert captured_args[idx + 1] == "24"


# ---------------------------------------------------------------------------
# Auditor gap fixes (RED -> GREEN)
# ---------------------------------------------------------------------------


def test_startup_gate_hold_short_circuits_heavier_checks(monkeypatch, tmp_path: Path) -> None:
    """When startup_gate returns HOLD, run_loop_cycle and validate_loop_closure must NOT run."""
    called: list[str] = []

    def _fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        command_text = " ".join(command)
        if "startup_codex_helper.py" in command_text:
            called.append("startup_gate")
            return subprocess.CompletedProcess(
                command, 0,
                stdout="STARTUP_SUMMARY: CODEX\nREADINESS_STATUS: NEEDS_ATTENTION\n",
                stderr="",
            )
        if "run_loop_cycle.py" in command_text:
            called.append("run_loop_cycle")
            return subprocess.CompletedProcess(command, 0, stdout="PASS\n", stderr="")
        if "validate_loop_closure.py" in command_text:
            called.append("validate_loop_closure")
            return subprocess.CompletedProcess(command, 0, stdout="READY_TO_ESCALATE\n", stderr="")
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown")

    monkeypatch.setattr(run_fast_checks.subprocess, "run", _fake_run)

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path)])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    # startup_gate fired, heavier checks must NOT have been called
    assert called == ["startup_gate"], f"Expected only startup_gate to run, got: {called}"
    assert exit_code == 0  # HOLD is non-failing by default
    assert payload["overall_status"] == "HOLD"

    # Heavier checks must appear in payload as SKIPPED
    status_by_name = {item["name"]: item["status"] for item in payload["checks"]}
    assert status_by_name["startup_gate"] == "HOLD"
    assert status_by_name["run_loop_cycle"] == "SKIPPED"
    assert status_by_name["validate_loop_closure"] == "SKIPPED"


def test_startup_gate_malformed_output_is_fail(monkeypatch, tmp_path: Path) -> None:
    """startup_gate exit-0 output with no STARTUP_SUMMARY: header must be FAIL (fail-closed)."""

    def _fake_run(
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        command_text = " ".join(command)
        if "startup_codex_helper.py" in command_text:
            # Malformed: exits 0 but missing STARTUP_SUMMARY: header (interface drift / truncation)
            return subprocess.CompletedProcess(
                command, 0,
                stdout="something unexpected happened\n",
                stderr="",
            )
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="unknown")

    monkeypatch.setattr(run_fast_checks.subprocess, "run", _fake_run)

    args = run_fast_checks.parse_args(["--repo-root", str(tmp_path), "--check", "startup_gate"])
    exit_code, payload = run_fast_checks.run_fast_checks(args)

    assert exit_code == 1  # malformed = FAIL = hard exit
    assert payload["overall_status"] == "FAIL"
    status_by_name = {item["name"]: item["status"] for item in payload["checks"]}
    assert status_by_name["startup_gate"] == "FAIL"
