"""Tests for Phase 5C.2 — test_repair_loop.py (updated for fail-closed contracts)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

try:
    from sop.scripts.lint_repair_loop import HumanEscalationRequired, MAX_ITERATIONS, LintCommandError
    from sop.scripts.test_repair_loop import (
        run_test_repair, _parse_failures, _is_passing,
    )
    from sop.scripts.test_repair_loop import main as run_test_repair_cli
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from sop.scripts.lint_repair_loop import HumanEscalationRequired, MAX_ITERATIONS, LintCommandError
    from sop.scripts.test_repair_loop import (
        run_test_repair, _parse_failures, _is_passing,
    )
    from sop.scripts.test_repair_loop import main as run_test_repair_cli


def _runner(outputs):
    calls = iter(outputs)
    def fake(cmd, cwd=None):
        return next(calls)
    return fake

def _always_failing(n):
    """n iterations: test fails, fix succeeds (exit 0)."""
    out = []
    for _ in range(n):
        out.append((1, "FAILED tests/test_foo.py::test_bar"))
        out.append((0, "fix applied"))  # fix exits 0
    return out


# --- _parse_failures ---

def test_detects_failed_marker():
    assert _parse_failures("FAILED tests/test_foo.py::test_bar") != []

def test_detects_error_marker():
    assert _parse_failures("ERROR tests/test_foo.py") != []

def test_empty_output_returns_empty():
    assert _parse_failures("") == []

def test_passing_summary_returns_empty():
    assert _parse_failures("1 passed in 0.1s") == []


# --- _is_passing ---

def test_passing_when_exit_zero_and_no_failures():
    assert _is_passing(0, []) is True

def test_not_passing_when_nonzero_exit():
    assert _is_passing(1, []) is False

def test_not_passing_when_failures_present():
    assert _is_passing(0, ["FAILED test_foo"]) is False


# --- output contract ---

def test_result_keys_present(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner([(0, "1 passed")]))
    r = run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"])
    for k in ("target", "iterations_used", "max_iterations", "final_status", "failures", "iteration_log"):
        assert k in r.to_dict()

def test_max_iterations_field_is_five(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner([(0, "1 passed")]))
    r = run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"])
    assert r.max_iterations == MAX_ITERATIONS

def test_max_iterations_not_overridable():
    """run_test_repair must not accept a max_iterations kwarg."""
    import inspect
    sig = inspect.signature(run_test_repair)
    assert "max_iterations" not in sig.parameters


# --- passing immediately ---

def test_returns_passing_immediately(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner([(0, "1 passed")]))
    r = run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"])
    assert r.final_status == "passing"
    assert r.iterations_used == 1
    assert r.failures == []


# --- fail-closed: nonzero fix exit raises immediately ---

def test_nonzero_fix_exit_raises_lint_command_error(monkeypatch):
    """Fix command crashing must raise immediately, not defer to cap."""
    outputs = [
        (1, "FAILED tests/test_foo.py::test_bar"),  # test: failing
        (1, "fixer crashed"),                         # fix: nonzero
    ]
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(outputs))
    with pytest.raises(LintCommandError) as ei:
        run_test_repair(
            "tests/",
            test_cmd=["python", "-m", "pytest", "tests/", "-q"],
            fix_cmd=["python", "fix.py"],
        )
    assert "exited 1" in str(ei.value) or "Fix command" in str(ei.value)

def test_nonzero_fix_exit_does_not_burn_all_iterations(monkeypatch):
    """Fix crash should raise after 1 test + 1 fix = 2 calls, not MAX_ITERATIONS*2."""
    call_count = [0]
    def counting(cmd, cwd=None):
        call_count[0] += 1
        if call_count[0] % 2 == 1:  # test calls
            return (1, "FAILED tests/test_foo.py::test_bar")
        else:  # fix calls
            return (1, "fixer crashed")
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", counting)
    with pytest.raises(LintCommandError):
        run_test_repair(
            "tests/",
            test_cmd=["python", "-m", "pytest", "tests/", "-q"],
            fix_cmd=["python", "fix.py"],
        )
    assert call_count[0] == 2


# --- fix and pass ---

def test_passes_after_one_fix(monkeypatch):
    outputs = [
        (1, "FAILED tests/test_foo.py::test_bar"),
        (0, "fix applied"),
        (0, "1 passed"),
    ]
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(outputs))
    r = run_test_repair(
        "tests/",
        test_cmd=["python", "-m", "pytest", "tests/", "-q"],
        fix_cmd=["python", "fix.py"],
    )
    assert r.final_status == "passing"
    assert r.iterations_used == 2
    assert r.iteration_log[0].fix_applied is True


# --- iteration cap ---

def test_raises_escalation_after_five_iterations(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(_always_failing(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"], fix_cmd=["python", "fix.py"])
    assert ei.value.result.iterations_used == MAX_ITERATIONS

def test_escalation_status_is_escalated(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(_always_failing(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"], fix_cmd=["python", "fix.py"])
    assert ei.value.result.final_status == "escalated"

def test_escalation_carries_remaining_failures(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(_always_failing(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"], fix_cmd=["python", "fix.py"])
    assert len(ei.value.result.failures) > 0

def test_escalation_carries_full_iteration_log(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(_always_failing(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"], fix_cmd=["python", "fix.py"])
    assert len(ei.value.result.iteration_log) == MAX_ITERATIONS

def test_does_not_exceed_cap(monkeypatch):
    """Loop stops at MAX_ITERATIONS when fix exits 0 but tests keep failing."""
    count = [0]
    def counting(cmd, cwd=None):
        count[0] += 1
        if count[0] % 2 == 1:  # test calls
            return (1, "FAILED tests/test_foo.py::test_bar")
        else:  # fix calls — must exit 0
            return (0, "fix applied")
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", counting)
    with pytest.raises(HumanEscalationRequired):
        run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"], fix_cmd=["python", "fix.py"])
    assert count[0] == MAX_ITERATIONS * 2


# --- no-fix mode ---

def test_no_fix_when_fix_cmd_none(monkeypatch):
    outputs = [(1, "FAILED tests/test_foo.py::test_bar")] * MAX_ITERATIONS
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(outputs))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"], fix_cmd=None)
    for rec in ei.value.result.iteration_log:
        assert rec.fix_applied is False


# --- no-bypass governance invariants ---

def test_human_escalation_required_is_exception():
    assert issubclass(HumanEscalationRequired, Exception)

def test_escalation_carries_result_attribute(monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(_always_failing(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_test_repair("tests/", test_cmd=["python", "-m", "pytest", "tests/", "-q"], fix_cmd=["python", "fix.py"])
    assert hasattr(ei.value, "result")
    assert ei.value.result.final_status == "escalated"


# --- CLI ---

def test_cli_returns_zero_on_passing(tmp_path, monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner([(0, "1 passed")]))
    assert run_test_repair_cli([str(tmp_path)]) == 0

def test_cli_returns_one_on_escalation(tmp_path, monkeypatch):
    outputs = _always_failing(MAX_ITERATIONS)
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(outputs))
    rc = run_test_repair_cli([str(tmp_path), "--fix-cmd", "python", "fix.py"])
    assert rc == 1

def test_cli_writes_json_output(tmp_path, monkeypatch):
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner([(0, "1 passed")]))
    out_file = tmp_path / "result.json"
    run_test_repair_cli([str(tmp_path), "--output", str(out_file)])
    assert out_file.exists()
    assert json.loads(out_file.read_text())["final_status"] == "passing"

def test_cli_returns_two_on_nonzero_fix_exit(tmp_path, monkeypatch):
    """Nonzero fix exit should surface as command error (return code 2)."""
    outputs = [
        (1, "FAILED tests/test_foo.py::test_bar"),
        (1, "fixer crashed"),
    ]
    monkeypatch.setattr("sop.scripts.test_repair_loop._run", _runner(outputs))
    rc = run_test_repair_cli([str(tmp_path), "--fix-cmd", "python", "fix.py"])
    assert rc == 2
