from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from scripts import run_loop_cycle
from sop._plugins import discover_plugins, run_plugin_chain


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_scripts_dir(path: Path) -> None:
    for name in [
        "auditor_calibration_report.py",
        "generate_ceo_go_signal.py",
        "generate_ceo_weekly_summary.py",
        "evaluate_context_compaction_trigger.py",
        "build_exec_memory_packet.py",
        "validate_ceo_go_signal_truth.py",
        "validate_ceo_weekly_summary_truth.py",
        "validate_exec_memory_truth.py",
        "validate_round_contract_checks.py",
        "validate_counterexample_gate.py",
        "validate_dual_judge_gate.py",
        "validate_refactor_mock_policy.py",
        "validate_review_checklist.py",
        "validate_interface_contracts.py",
        "validate_parallel_fanin.py",
        "validate_loop_closure.py",
    ]:
        _write(path / name, "print('ok')\n")


def _fake_run(command: list[str], cwd=None, capture_output=True, text=True, check=False):
    del cwd, capture_output, text, check

    if "--output-json" in command and any("build_exec_memory_packet.py" in token for token in command):
        output_json = Path(command[command.index("--output-json") + 1])
        _write(
            output_json,
            json.dumps({"schema_version": "1.0.0", "generated_at_utc": "2026-03-31T00:00:00Z"}),
        )
    if "--output-md" in command and any("build_exec_memory_packet.py" in token for token in command):
        output_md = Path(command[command.index("--output-md") + 1])
        _write(output_md, "# Exec Memory\n")
    if "--status-json" in command and any("build_exec_memory_packet.py" in token for token in command):
        status_json = Path(command[command.index("--status-json") + 1])
        _write(
            status_json,
            json.dumps({"authoritative_latest_written": True, "reason": "ok"}),
        )
    if "--output-json" in command and any("validate_loop_closure.py" in token for token in command):
        closure_json = Path(command[command.index("--output-json") + 1])
        _write(closure_json, json.dumps({"result": "READY"}))
    if "--output-md" in command and any("validate_loop_closure.py" in token for token in command):
        closure_md = Path(command[command.index("--output-md") + 1])
        _write(closure_md, "# Closure\nREADY\n")

    return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")


def test_plugin_loader_discovers_example_plugin(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "example.py",
        """
class ExamplePlugin:
    name = "example"
    version = "1.0.0"
    min_sop_version = "0.1.0"

    def evaluate(self, action, context):
        return {"decision": "ALLOW", "reason": "ok"}

plugin = ExamplePlugin()
""".strip()
        + "\n",
    )
    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert len(candidates) == 1
    assert candidates[0].compatible is True


def test_plugin_discovery_non_recursive_and_underscore_ignored(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(plugin_dir / "_ignore.py", "plugin = object()\n")
    _write(plugin_dir / "nested" / "nested.py", "plugin = object()\n")
    _write(
        plugin_dir / "a_plugin.py",
        """
class P:
    name = "a"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        return None
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert [c.file_name for c in candidates] == ["a_plugin.py"]


def test_plugin_export_contract_requires_plugin_symbol(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(plugin_dir / "missing_symbol.py", "x = 1\n")

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert len(candidates) == 1
    assert candidates[0].compatible is False
    assert "export 'plugin'" in (candidates[0].skip_reason or "")


def test_plugin_version_incompatible_is_skipped(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "too_new.py",
        """
class P:
    name = "too-new"
    version = "1.0.0"
    min_sop_version = "9.0.0"
    def evaluate(self, action, context):
        return None
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    chain = run_plugin_chain(candidates=candidates, action={}, context={})
    assert chain.events[0].plugin_status == "skipped_incompatible"
    assert chain.events[0].decision == "WARN"


def test_plugin_evaluate_called_in_policy_chain(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "called.py",
        """
class P:
    name = "called"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def __init__(self):
        self.called = False
    def evaluate(self, action, context):
        self.called = True
        return {"decision": "ALLOW", "reason": "ok"}
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    chain = run_plugin_chain(candidates=candidates, action={"gate": "g"}, context={"trace_id": "t"})
    assert chain.events[0].plugin_status == "executed"


def test_plugin_execution_order_sorted_by_filename(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    for name in ["z_last.py", "a_first.py", "m_middle.py"]:
        _write(
            plugin_dir / name,
            """
class P:
    name = "x"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        return None
plugin = P()
""".strip()
            + "\n",
        )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert [c.file_name for c in candidates] == ["a_first.py", "m_middle.py", "z_last.py"]


def test_plugin_block_short_circuits_remaining_plugins(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "a_block.py",
        """
class P:
    name = "blocker"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        return {"decision": "BLOCK", "reason": "stop"}
plugin = P()
""".strip()
        + "\n",
    )
    _write(
        plugin_dir / "b_after.py",
        """
class P:
    name = "after"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        raise RuntimeError("should not run")
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    chain = run_plugin_chain(candidates=candidates, action={}, context={})
    assert chain.blocked is True
    assert len(chain.events) == 1
    assert chain.events[0].decision == "BLOCK"


def test_plugin_block_is_enforced_in_gate_outcome(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    context_dir = repo_root / "docs" / "context"
    scripts_dir = repo_root / "scripts"
    _prepare_scripts_dir(scripts_dir)
    _write(context_dir / "ceo_weekly_summary_latest.md", "# Weekly Summary\n")

    monkeypatch.setattr(run_loop_cycle.subprocess, "run", _fake_run)

    def _block_gate_a(**kwargs):
        if kwargs["gate_name"] == "gate_a":
            return True, [{"plugin_name": "blocker", "plugin_version": "1.0.0", "plugin_status": "executed", "decision": "BLOCK", "reason": "blocked", "metadata": None}]
        return False, []

    monkeypatch.setattr(run_loop_cycle, "_run_plugins_for_gate", _block_gate_a)

    args = run_loop_cycle.parse_args([
        "--repo-root",
        str(repo_root),
        "--scripts-dir",
        str(scripts_dir),
        "--skip-phase-end",
    ])
    exit_code, payload, _ = run_loop_cycle.run_cycle(args)

    assert exit_code == 0
    assert payload["final_result"] == "HOLD"
    assert payload["gate_decisions"][0]["plugin_events"][0]["decision"] == "BLOCK"


def test_plugin_exception_is_captured_not_crashing_run(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "boom.py",
        """
class P:
    name = "boom"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        raise RuntimeError("boom")
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    chain = run_plugin_chain(candidates=candidates, action={}, context={})
    assert chain.blocked is False
    assert chain.events[0].plugin_status == "error"
    assert chain.events[0].decision == "WARN"


def test_plugin_result_written_to_audit_log(tmp_path: Path) -> None:
    repo_root = tmp_path
    context_dir = repo_root / "docs" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    plugin_dir = repo_root / ".sop" / "plugins"
    _write(
        plugin_dir / "warner.py",
        """
class P:
    name = "warner"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        return {"decision": "WARN", "reason": "watch"}
plugin = P()
""".strip()
        + "\n",
    )

    blocked, events = run_loop_cycle._run_plugins_for_gate(
        args=argparse.Namespace(plugin_dir=plugin_dir),
        gate_name="gate_a",
        gate_label="exec_memory->advisory",
        gate_decision="PROCEED",
        repo_root=repo_root,
        trace_id="trace-1",
        policy_shadow_mode=True,
        context_dir=context_dir,
    )

    assert blocked is False
    assert events[0]["decision"] == "WARN"

    audit_path = context_dir / "audit_log.ndjson"
    lines = [line for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any('"actor":"plugin:warner"' in line for line in lines)
