from __future__ import annotations

import importlib.util
from pathlib import Path

from sop._plugins import discover_plugins


REPO_ROOT = Path(__file__).parent.parent
PLUGIN_DIR = REPO_ROOT / ".sop" / "plugins"
REFERENCE_FILES = {
    "reference_policy_evaluator.py": "policy_evaluator",
    "reference_decision_store.py": "decision_store",
    "reference_iam_siem_connector.py": "iam_siem_connector",
}


def _load_plugin_from_file(path: Path):
    spec = importlib.util.spec_from_file_location(f"ref_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plugin = getattr(module, "plugin", None)
    assert plugin is not None, f"{path.name} must export plugin"
    return plugin


def test_reference_plugins_exist() -> None:
    for filename in REFERENCE_FILES:
        assert (PLUGIN_DIR / filename).exists(), f"Missing reference plugin: {filename}"


def test_reference_plugins_load_and_are_capability_valid() -> None:
    candidates = discover_plugins(PLUGIN_DIR, "0.2.0")
    by_file = {c.file_name: c for c in candidates}

    for filename in REFERENCE_FILES:
        assert filename in by_file, f"discover_plugins must return {filename}"
        assert by_file[filename].compatible is True, (
            f"{filename} must be capability-valid and compatible"
        )


def test_reference_plugins_conform_to_v2_result_contract() -> None:
    for filename, expected_kind in REFERENCE_FILES.items():
        plugin = _load_plugin_from_file(PLUGIN_DIR / filename)

        assert str(getattr(plugin, "api_version", "")).strip() == "2.0"
        assert str(getattr(plugin, "kind", "")).strip() == expected_kind

        result = plugin.evaluate(
            {"actor": "test-actor", "gate": "reference-demo"},
            {"gate": "reference-demo", "trace_id": "trace-1", "repo_root": str(REPO_ROOT)},
        )

        assert isinstance(result, dict)
        assert result.get("decision") in {"ALLOW", "BLOCK", "WARN"}
        assert isinstance(result.get("reason"), str) and result["reason"].strip()


def test_reference_plugins_preserve_deterministic_filename_order() -> None:
    candidates = discover_plugins(PLUGIN_DIR, "0.2.0")
    observed = [c.file_name for c in candidates if c.file_name in REFERENCE_FILES]
    assert observed == sorted(observed), "Reference plugins must preserve lexical discovery order"
