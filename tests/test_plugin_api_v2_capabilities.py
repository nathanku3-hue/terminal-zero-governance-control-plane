from __future__ import annotations

from pathlib import Path

from sop._plugins import discover_plugins, run_plugin_chain


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _v2_plugin(*, kind: str, capabilities: str, evaluate_body: str = "return None") -> str:
    return (
        "class P:\n"
        "    name = 'p'\n"
        "    version = '1.0.0'\n"
        "    min_sop_version = '0.1.0'\n"
        "    api_version = '2.0'\n"
        f"    kind = '{kind}'\n"
        f"    capabilities = {capabilities}\n"
        "    def evaluate(self, action, context):\n"
        f"        {evaluate_body}\n"
        "plugin = P()\n"
    )


def test_v2_policy_evaluator_accepts_policy_capabilities(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "policy_ok.py",
        _v2_plugin(
            kind="policy_evaluator",
            capabilities="['policy.read_context', 'policy.emit_decision']",
        ),
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert len(candidates) == 1
    assert candidates[0].compatible is True


def test_v2_decision_store_accepts_decision_store_capabilities(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "decision_store_ok.py",
        _v2_plugin(
            kind="decision_store",
            capabilities="['decision_store.read', 'decision_store.write']",
        ),
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert len(candidates) == 1
    assert candidates[0].compatible is True


def test_v2_iam_siem_accepts_emit_event_capability(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "iam_siem_ok.py",
        _v2_plugin(
            kind="iam_siem_connector",
            capabilities="['iam_siem.emit_event']",
        ),
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert len(candidates) == 1
    assert candidates[0].compatible is True


def test_v2_unknown_capability_rejected(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "unknown_cap.py",
        _v2_plugin(kind="policy_evaluator", capabilities="['foo.bar']"),
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert candidates[0].compatible is False
    assert "unknown v2 capability" in (candidates[0].skip_reason or "")


def test_v2_missing_capabilities_rejected(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "missing_caps.py",
        """
class P:
    name = "p"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    api_version = "2.0"
    kind = "policy_evaluator"
    def evaluate(self, action, context):
        return None
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert candidates[0].compatible is False
    assert "capabilities" in (candidates[0].skip_reason or "")


def test_v2_cross_kind_capability_rejected(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "cross_kind.py",
        _v2_plugin(
            kind="policy_evaluator",
            capabilities="['decision_store.write']",
        ),
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert candidates[0].compatible is False
    assert "capability/kind mismatch" in (candidates[0].skip_reason or "")


def test_v2_invalid_kind_rejected(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "invalid_kind.py",
        _v2_plugin(kind="not_a_real_kind", capabilities="['policy.read_context']"),
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert candidates[0].compatible is False
    assert "invalid v2 plugin kind" in (candidates[0].skip_reason or "")


def test_v2_missing_kind_rejected(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "missing_kind.py",
        """
class P:
    name = "p"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    api_version = "2.0"
    capabilities = ["policy.read_context"]
    def evaluate(self, action, context):
        return None
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert candidates[0].compatible is False
    assert "invalid v2 plugin kind" in (candidates[0].skip_reason or "")


def test_v2_malformed_capability_list_rejected(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "malformed_caps.py",
        _v2_plugin(kind="policy_evaluator", capabilities="'policy.read_context'"),
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert candidates[0].compatible is False
    assert "list[str]" in (candidates[0].skip_reason or "")


def test_v1_plugins_load_without_v2_capabilities_field(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "v1_ok.py",
        """
class P:
    name = "v1"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        return {"decision": "ALLOW", "reason": "ok"}
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    chain = run_plugin_chain(candidates=candidates, action={}, context={})
    assert candidates[0].compatible is True
    assert chain.events[0].plugin_status == "executed"


def test_mixed_v1_v2_chain_semantics_preserved(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    _write(
        plugin_dir / "a_v2_block.py",
        _v2_plugin(
            kind="policy_evaluator",
            capabilities="['policy.read_context', 'policy.emit_decision']",
            evaluate_body="return {'decision': 'BLOCK', 'reason': 'blocked by v2'}",
        ),
    )
    _write(
        plugin_dir / "b_v1_after.py",
        """
class P:
    name = "v1-after"
    version = "1.0.0"
    min_sop_version = "0.1.0"
    def evaluate(self, action, context):
        raise RuntimeError("should not run")
plugin = P()
""".strip()
        + "\n",
    )

    candidates = discover_plugins(plugin_dir, "0.2.0")
    assert [c.file_name for c in candidates] == ["a_v2_block.py", "b_v1_after.py"]

    chain = run_plugin_chain(candidates=candidates, action={}, context={})
    assert chain.blocked is True
    assert len(chain.events) == 1
    assert chain.events[0].decision == "BLOCK"
