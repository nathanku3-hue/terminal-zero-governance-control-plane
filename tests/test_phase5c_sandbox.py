"""Tests for Phase 5C.3 — sandbox_executor.py"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

try:
    from sop.scripts.sandbox_executor import (
        SandboxUnavailableError, SandboxExecutionError, SandboxResult,
        run_in_sandbox, run_repair_in_sandbox, check_docker_available,
        DEFAULT_IMAGE, main as sandbox_main,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from sop.scripts.sandbox_executor import (
        SandboxUnavailableError, SandboxExecutionError, SandboxResult,
        run_in_sandbox, run_repair_in_sandbox, check_docker_available,
        DEFAULT_IMAGE, main as sandbox_main,
    )


def _proc(rc=0, stdout="", stderr=""):
    p = MagicMock()
    p.returncode, p.stdout, p.stderr = rc, stdout, stderr
    return p


# --- exception hierarchy ---

def test_unavailable_is_exception():
    assert issubclass(SandboxUnavailableError, Exception)

def test_execution_error_is_exception():
    assert issubclass(SandboxExecutionError, Exception)

def test_unavailable_not_subclass_of_execution_error():
    assert not issubclass(SandboxUnavailableError, SandboxExecutionError)


# --- output contract ---

def test_result_keys_present(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", lambda *a, **kw: _proc(0, "ok"))
    r = run_in_sandbox(["echo"], check_docker=False)
    for k in ("command", "image", "exit_code", "stdout", "stderr", "success", "error"):
        assert k in r.to_dict()

def test_success_true_when_exit_zero(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", lambda *a, **kw: _proc(0))
    r = run_in_sandbox(["true"], check_docker=False)
    assert r.success is True and r.exit_code == 0

def test_success_false_when_nonzero(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", lambda *a, **kw: _proc(1))
    r = run_in_sandbox(["false"], check_docker=False)
    assert r.success is False and r.exit_code == 1

def test_result_carries_stdout_stderr(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run",
                        lambda *a, **kw: _proc(0, stdout="out", stderr="err"))
    r = run_in_sandbox(["cmd"], check_docker=False)
    assert r.stdout == "out" and r.stderr == "err"

def test_result_carries_image(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", lambda *a, **kw: _proc(0))
    r = run_in_sandbox(["cmd"], image="alpine:3", check_docker=False)
    assert r.image == "alpine:3"

def test_result_carries_command(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", lambda *a, **kw: _proc(0))
    r = run_in_sandbox(["echo", "hi"], check_docker=False)
    assert r.command == ["echo", "hi"]


# --- fail-closed: no host fallback ---

def test_raises_unavailable_when_docker_not_on_path(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: None)
    with pytest.raises(SandboxUnavailableError):
        run_in_sandbox(["echo"], check_docker=False)

def test_raises_unavailable_when_docker_info_fails(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run",
                        lambda *a, **kw: _proc(1, stderr="Cannot connect"))
    with pytest.raises(SandboxUnavailableError):
        check_docker_available()

def test_no_silent_fallback_to_host(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: None)
    with pytest.raises(SandboxUnavailableError):
        run_in_sandbox(["echo"], check_docker=False)


# --- docker command construction ---

def _capture(monkeypatch, rc=0):
    calls = []
    def cap(*a, **kw):
        calls.append(a[0])
        return _proc(rc)
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", cap)
    return calls

def test_uses_rm_flag(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["echo"], check_docker=False)
    assert "--rm" in calls[0]

def test_disables_network(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["echo"], check_docker=False)
    idx = calls[0].index("--network")
    assert calls[0][idx + 1] == "none"

def test_sets_workdir(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["echo"], workdir="/app", check_docker=False)
    idx = calls[0].index("--workdir")
    assert calls[0][idx + 1] == "/app"

def test_includes_image(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["echo"], image="alpine:3", check_docker=False)
    assert "alpine:3" in calls[0]

def test_appends_command_last(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["echo", "hello"], check_docker=False)
    assert calls[0][-2:] == ["echo", "hello"]

def test_adds_mount_when_provided(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["ls"], mount=("/h", "/c"), check_docker=False)
    idx = calls[0].index("-v")
    assert calls[0][idx + 1] == "/h:/c"

def test_no_mount_when_not_provided(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["ls"], check_docker=False)
    assert "-v" not in calls[0]

def test_passes_env_vars(monkeypatch):
    calls = _capture(monkeypatch)
    run_in_sandbox(["env"], env={"FOO": "bar"}, check_docker=False)
    idx = calls[0].index("-e")
    assert calls[0][idx + 1] == "FOO=bar"


# --- timeout and infrastructure errors ---

def test_raises_execution_error_on_timeout(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    def raise_timeout(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="docker", timeout=1)
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", raise_timeout)
    with pytest.raises(SandboxExecutionError):
        run_in_sandbox(["sleep", "999"], timeout=1, check_docker=False)

def test_raises_unavailable_on_file_not_found(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    def raise_fnf(*a, **kw):
        raise FileNotFoundError("docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", raise_fnf)
    with pytest.raises(SandboxUnavailableError):
        run_in_sandbox(["echo"], check_docker=False)


# --- run_repair_in_sandbox ---

def test_repair_mounts_repo_root(tmp_path, monkeypatch):
    calls = _capture(monkeypatch)
    run_repair_in_sandbox(["ruff", "check", "."], repo_root=tmp_path, check_docker=False)
    idx = calls[0].index("-v")
    assert calls[0][idx + 1].endswith(":/workspace")

def test_repair_no_mount_when_no_repo_root(monkeypatch):
    calls = _capture(monkeypatch)
    run_repair_in_sandbox(["ruff", "check", "."], check_docker=False)
    assert "-v" not in calls[0]

def test_repair_uses_workspace_workdir(tmp_path, monkeypatch):
    calls = _capture(monkeypatch)
    run_repair_in_sandbox(["ruff", "."], repo_root=tmp_path, check_docker=False)
    idx = calls[0].index("--workdir")
    assert calls[0][idx + 1] == "/workspace"


# --- CLI ---

def test_cli_returns_zero_on_success(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", lambda *a, **kw: _proc(0))
    monkeypatch.setattr("sop.scripts.sandbox_executor.check_docker_available", lambda: None)
    assert sandbox_main(["echo", "hello"]) == 0

def test_cli_returns_one_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run", lambda *a, **kw: _proc(1))
    monkeypatch.setattr("sop.scripts.sandbox_executor.check_docker_available", lambda: None)
    assert sandbox_main(["false"]) == 1

def test_cli_returns_three_on_unavailable(monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: None)
    assert sandbox_main(["echo", "hi"]) == 3

def test_cli_writes_json_output(tmp_path, monkeypatch):
    monkeypatch.setattr("sop.scripts.sandbox_executor.shutil.which", lambda x: "docker")
    monkeypatch.setattr("sop.scripts.sandbox_executor.subprocess.run",
                        lambda *a, **kw: _proc(0, stdout="hello"))
    monkeypatch.setattr("sop.scripts.sandbox_executor.check_docker_available", lambda: None)
    out_file = tmp_path / "result.json"
    sandbox_main(["echo", "hello", "--output", str(out_file)])
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data["success"] is True
    assert data["exit_code"] == 0
