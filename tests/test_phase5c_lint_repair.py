"""Tests for Phase 5C.2 — lint_repair_loop.py (updated for fail-closed contracts)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

try:
    from sop.scripts.lint_repair_loop import (
        MAX_ITERATIONS, HumanEscalationRequired, LintCommandError,
        run_lint_repair, main as lint_main,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from sop.scripts.lint_repair_loop import (
        MAX_ITERATIONS, HumanEscalationRequired, LintCommandError,
        run_lint_repair, main as lint_main,
    )


def _runner(outputs):
    """Return a fake _run that yields successive (exit, output) pairs."""
    calls = iter(outputs)
    def fake(cmd, cwd=None):
        return next(calls)
    return fake


def _lint_fix_pairs(lint_out, fix_out=(0, "Fixed"), n=MAX_ITERATIONS):
    """Produce n iterations of (lint_out, fix_out) pairs."""
    out = []
    for _ in range(n):
        out.append(lint_out)
        out.append(fix_out)
    return out


# --- constant ---

def test_max_iterations_is_five():
    assert MAX_ITERATIONS == 5


# --- output contract ---

def test_result_keys_present(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner([(0, "")]))
    r = run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=[])
    for k in ("target", "iterations_used", "max_iterations", "final_status", "findings", "iteration_log"):
        assert k in r.to_dict()

def test_max_iterations_field_always_five(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner([(0, "")]))
    r = run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=[])
    assert r.max_iterations == MAX_ITERATIONS

def test_max_iterations_not_overridable():
    """run_lint_repair must not accept a max_iterations kwarg."""
    import inspect
    sig = inspect.signature(run_lint_repair)
    assert "max_iterations" not in sig.parameters


# --- clean on first iteration ---

def test_clean_immediately(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner([(0, "")]))
    r = run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=[])
    assert r.final_status == "clean"
    assert r.iterations_used == 1
    assert r.findings == []

def test_clean_has_one_log_entry(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner([(0, "")]))
    r = run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=[])
    assert len(r.iteration_log) == 1


# --- fail-closed: nonzero lint exit with no output is an infra error ---

def test_nonzero_lint_exit_with_no_output_raises_command_error(monkeypatch):
    """A linter that exits nonzero but emits nothing is an infra failure, not clean."""
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner([(2, "")]))
    with pytest.raises(LintCommandError) as ei:
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=[])
    assert "infrastructure failure" in str(ei.value).lower() or "exited 2" in str(ei.value)

def test_nonzero_lint_exit_with_output_is_findings_not_error(monkeypatch):
    """Nonzero exit WITH findings text = findings present, not infra error."""
    outputs = [
        (1, "src/a.py:1:1: E501 line too long"),
        (0, "Fixed 1"),
        (0, ""),
    ]
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(outputs))
    r = run_lint_repair(
        "src/",
        lint_cmd=["ruff", "check", "src/"],
        fix_cmd=["ruff", "--fix", "src/"],
    )
    assert r.final_status == "clean"


# --- fail-closed: nonzero fix exit raises immediately ---

def test_nonzero_fix_exit_raises_lint_command_error(monkeypatch):
    """A fixer that crashes must raise immediately, not burn remaining iterations."""
    outputs = [
        (1, "src/a.py:1:1: E501"),  # lint: findings
        (1, "fixer crashed"),         # fix: nonzero
    ]
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(outputs))
    with pytest.raises(LintCommandError) as ei:
        run_lint_repair(
            "src/",
            lint_cmd=["ruff", "check", "src/"],
            fix_cmd=["ruff", "--fix", "src/"],
        )
    assert "exited 1" in str(ei.value) or "Fix command" in str(ei.value)

def test_nonzero_fix_exit_does_not_burn_all_iterations(monkeypatch):
    """Fix crash must raise on iteration 1, not after MAX_ITERATIONS."""
    call_count = [0]
    def counting(cmd, cwd=None):
        call_count[0] += 1
        if call_count[0] % 2 == 1:  # lint calls (odd)
            return (1, "src/a.py:1:1: E501")
        else:  # fix calls (even)
            return (1, "fixer crashed")
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", counting)
    with pytest.raises(LintCommandError):
        run_lint_repair(
            "src/",
            lint_cmd=["ruff", "check", "src/"],
            fix_cmd=["ruff", "--fix", "src/"],
        )
    # Should have raised after 1 lint + 1 fix = 2 calls, not MAX_ITERATIONS*2
    assert call_count[0] == 2


# --- fix and clean ---

def test_cleans_after_one_fix(monkeypatch):
    outputs = [
        (1, "src/a.py:1:1: E501 line too long"),
        (0, "Fixed 1 error"),
        (0, ""),
    ]
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(outputs))
    r = run_lint_repair(
        "src/",
        lint_cmd=["ruff", "check", "src/"],
        fix_cmd=["ruff", "check", "--fix", "src/"],
    )
    assert r.final_status == "clean"
    assert r.iterations_used == 2
    assert r.iteration_log[0].fix_applied is True

def test_iteration_log_records_fix_output(monkeypatch):
    outputs = [(1, "src/a.py:1:1: E501"), (0, "Fixed 1"), (0, "")]
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(outputs))
    r = run_lint_repair(
        "src/",
        lint_cmd=["ruff", "check", "src/"],
        fix_cmd=["ruff", "check", "--fix", "src/"],
    )
    assert r.iteration_log[0].fix_output == "Fixed 1"


# --- iteration cap (fix succeeds but lint keeps finding issues) ---

def _always_failing_lint(n):
    """n iterations: lint finds issues, fix succeeds (exit 0), lint still finds issues."""
    out = []
    for _ in range(n):
        out.append((1, "src/a.py:1:1: E501 line too long"))
        out.append((0, "Fixed"))  # fix exits 0
    return out

def test_raises_escalation_after_five_iterations(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(_always_failing_lint(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=["ruff", "--fix", "src/"])
    assert ei.value.result.iterations_used == MAX_ITERATIONS

def test_escalation_status_is_escalated(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(_always_failing_lint(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=["ruff", "--fix", "src/"])
    assert ei.value.result.final_status == "escalated"

def test_escalation_carries_remaining_findings(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(_always_failing_lint(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=["ruff", "--fix", "src/"])
    assert len(ei.value.result.findings) > 0

def test_escalation_carries_full_iteration_log(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(_always_failing_lint(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=["ruff", "--fix", "src/"])
    assert len(ei.value.result.iteration_log) == MAX_ITERATIONS

def test_does_not_exceed_cap(monkeypatch):
    """Loop stops at exactly MAX_ITERATIONS when fix always succeeds but lint persists."""
    count = [0]
    def counting(cmd, cwd=None):
        count[0] += 1
        if count[0] % 2 == 1:  # lint calls
            return (1, "src/a.py:1:1: E501 persistent")
        else:  # fix calls — must exit 0
            return (0, "Fixed")
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", counting)
    with pytest.raises(HumanEscalationRequired):
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=["ruff", "--fix", "src/"])
    assert count[0] == MAX_ITERATIONS * 2


# --- no-fix mode ---

def test_no_fix_applied_when_fix_cmd_empty(monkeypatch):
    outputs = [(1, "src/a.py:1:1: E501")] * MAX_ITERATIONS
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(outputs))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=[])
    for rec in ei.value.result.iteration_log:
        assert rec.fix_applied is False


# --- command error ---

def test_raises_lint_command_error_on_missing_exe(monkeypatch):
    def raise_err(cmd, cwd=None):
        raise LintCommandError("Executable not found")
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", raise_err)
    with pytest.raises(LintCommandError):
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"])


# --- escalation is never swallowed ---

def test_human_escalation_required_is_exception():
    assert issubclass(HumanEscalationRequired, Exception)

def test_escalation_carries_result_attribute(monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(_always_failing_lint(MAX_ITERATIONS)))
    with pytest.raises(HumanEscalationRequired) as ei:
        run_lint_repair("src/", lint_cmd=["ruff", "check", "src/"], fix_cmd=["ruff", "--fix", "src/"])
    assert hasattr(ei.value, "result")


# --- CLI ---

def test_cli_returns_zero_on_clean(tmp_path, monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner([(0, "")]))
    assert lint_main([str(tmp_path), "--lint-cmd", "ruff", "check", str(tmp_path)]) == 0

def test_cli_returns_one_on_escalation(tmp_path, monkeypatch):
    # fix must exit 0 so we reach cap; lint always has findings
    outputs = _always_failing_lint(MAX_ITERATIONS)
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(outputs))
    rc = lint_main([
        str(tmp_path),
        "--lint-cmd", "ruff", "check", str(tmp_path),
        "--fix-cmd", "ruff", "check", "--fix", str(tmp_path),
    ])
    assert rc == 1

def test_cli_writes_json_output(tmp_path, monkeypatch):
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner([(0, "")]))
    out_file = tmp_path / "result.json"
    lint_main([str(tmp_path), "--lint-cmd", "ruff", "check", str(tmp_path), "--output", str(out_file)])
    assert out_file.exists()
    assert json.loads(out_file.read_text())["final_status"] == "clean"

def test_cli_returns_two_on_command_error(tmp_path, monkeypatch):
    def raise_err(cmd, cwd=None):
        raise LintCommandError("not found")
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", raise_err)
    assert lint_main([str(tmp_path), "--lint-cmd", "ruff", "check", str(tmp_path)]) == 2

def test_cli_returns_two_on_nonzero_fix_exit(tmp_path, monkeypatch):
    """Nonzero fix exit should surface as command error (return code 2)."""
    outputs = [
        (1, "src/a.py:1:1: E501"),  # lint: findings
        (1, "fixer crashed"),         # fix: nonzero -> LintCommandError
    ]
    monkeypatch.setattr("sop.scripts.lint_repair_loop._run", _runner(outputs))
    rc = lint_main([
        str(tmp_path),
        "--lint-cmd", "ruff", "check", str(tmp_path),
        "--fix-cmd", "ruff", "--fix", str(tmp_path),
    ])
    assert rc == 2
