from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


_VALID_DECISIONS = {"ALLOW", "BLOCK", "WARN"}


@dataclass(frozen=True)
class PluginCandidate:
    file_path: Path
    file_name: str
    plugin_name: str
    plugin_version: str
    min_sop_version: str
    evaluate: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any] | None] | None
    compatible: bool
    skip_reason: str | None


@dataclass(frozen=True)
class PluginEvent:
    decision: str
    reason: str
    plugin_name: str
    plugin_version: str
    plugin_status: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PluginChainResult:
    blocked: bool
    events: list[PluginEvent]


def _parse_semver(value: str) -> tuple[int, int, int] | None:
    text = str(value).strip()
    parts = text.split(".")
    if len(parts) != 3:
        return None
    try:
        major, minor, patch = (int(part) for part in parts)
    except ValueError:
        return None
    if major < 0 or minor < 0 or patch < 0:
        return None
    return major, minor, patch


def _load_module_from_path(path: Path) -> ModuleType:
    module_name = f"sop_plugin_{path.stem}_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_plugins(plugin_dir: Path, sop_version: str) -> list[PluginCandidate]:
    if not plugin_dir.exists() or not plugin_dir.is_dir():
        return []

    sop_semver = _parse_semver(sop_version)
    candidates: list[PluginCandidate] = []

    plugin_files = sorted(
        [
            path
            for path in plugin_dir.iterdir()
            if path.is_file() and path.suffix == ".py" and not path.name.startswith("_")
        ],
        key=lambda path: path.name,
    )

    for path in plugin_files:
        default_name = path.stem
        try:
            module = _load_module_from_path(path)
            plugin = getattr(module, "plugin", None)
            if plugin is None:
                candidates.append(
                    PluginCandidate(
                        file_path=path,
                        file_name=path.name,
                        plugin_name=default_name,
                        plugin_version="0.0.0",
                        min_sop_version="0.0.0",
                        evaluate=None,
                        compatible=False,
                        skip_reason="module does not export 'plugin' symbol",
                    )
                )
                continue

            evaluate = getattr(plugin, "evaluate", None)
            if not callable(evaluate):
                candidates.append(
                    PluginCandidate(
                        file_path=path,
                        file_name=path.name,
                        plugin_name=str(getattr(plugin, "name", default_name)),
                        plugin_version=str(getattr(plugin, "version", "0.0.0")),
                        min_sop_version=str(getattr(plugin, "min_sop_version", "0.0.0")),
                        evaluate=None,
                        compatible=False,
                        skip_reason="plugin.evaluate is missing or not callable",
                    )
                )
                continue

            min_sop_version = str(getattr(plugin, "min_sop_version", "0.0.0"))
            plugin_semver = _parse_semver(min_sop_version)
            if plugin_semver is None or sop_semver is None:
                candidates.append(
                    PluginCandidate(
                        file_path=path,
                        file_name=path.name,
                        plugin_name=str(getattr(plugin, "name", default_name)),
                        plugin_version=str(getattr(plugin, "version", "0.0.0")),
                        min_sop_version=min_sop_version,
                        evaluate=None,
                        compatible=False,
                        skip_reason="invalid semver format in min_sop_version or sop.__version__",
                    )
                )
                continue

            if sop_semver < plugin_semver:
                candidates.append(
                    PluginCandidate(
                        file_path=path,
                        file_name=path.name,
                        plugin_name=str(getattr(plugin, "name", default_name)),
                        plugin_version=str(getattr(plugin, "version", "0.0.0")),
                        min_sop_version=min_sop_version,
                        evaluate=None,
                        compatible=False,
                        skip_reason=f"incompatible: sop version {sop_version} < plugin minimum {min_sop_version}",
                    )
                )
                continue

            candidates.append(
                PluginCandidate(
                    file_path=path,
                    file_name=path.name,
                    plugin_name=str(getattr(plugin, "name", default_name)),
                    plugin_version=str(getattr(plugin, "version", "0.0.0")),
                    min_sop_version=min_sop_version,
                    evaluate=evaluate,
                    compatible=True,
                    skip_reason=None,
                )
            )
        except Exception as exc:  # noqa: BLE001
            candidates.append(
                PluginCandidate(
                    file_path=path,
                    file_name=path.name,
                    plugin_name=default_name,
                    plugin_version="0.0.0",
                    min_sop_version="0.0.0",
                    evaluate=None,
                    compatible=False,
                    skip_reason=f"plugin load error: {exc}",
                )
            )

    return candidates


def run_plugin_chain(
    *,
    candidates: list[PluginCandidate],
    action: dict[str, Any],
    context: dict[str, Any],
) -> PluginChainResult:
    events: list[PluginEvent] = []

    for candidate in candidates:
        if not candidate.compatible or candidate.evaluate is None:
            events.append(
                PluginEvent(
                    decision="WARN",
                    reason=candidate.skip_reason or "plugin incompatible",
                    plugin_name=candidate.plugin_name,
                    plugin_version=candidate.plugin_version,
                    plugin_status="skipped_incompatible",
                )
            )
            continue

        try:
            raw_result = candidate.evaluate(action, context)
        except Exception as exc:  # noqa: BLE001
            events.append(
                PluginEvent(
                    decision="WARN",
                    reason=f"plugin exception: {exc}",
                    plugin_name=candidate.plugin_name,
                    plugin_version=candidate.plugin_version,
                    plugin_status="error",
                )
            )
            continue

        if raw_result is None:
            events.append(
                PluginEvent(
                    decision="ALLOW",
                    reason="plugin returned None",
                    plugin_name=candidate.plugin_name,
                    plugin_version=candidate.plugin_version,
                    plugin_status="executed",
                )
            )
            continue

        if not isinstance(raw_result, dict):
            events.append(
                PluginEvent(
                    decision="WARN",
                    reason="plugin result must be a dict or None",
                    plugin_name=candidate.plugin_name,
                    plugin_version=candidate.plugin_version,
                    plugin_status="error",
                )
            )
            continue

        decision = str(raw_result.get("decision", "")).strip().upper()
        reason = str(raw_result.get("reason", "")).strip()
        metadata = raw_result.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            metadata = None

        if decision not in _VALID_DECISIONS or not reason:
            events.append(
                PluginEvent(
                    decision="WARN",
                    reason="plugin result missing valid decision/reason",
                    plugin_name=candidate.plugin_name,
                    plugin_version=candidate.plugin_version,
                    plugin_status="error",
                )
            )
            continue

        events.append(
            PluginEvent(
                decision=decision,
                reason=reason,
                plugin_name=candidate.plugin_name,
                plugin_version=candidate.plugin_version,
                plugin_status="executed",
                metadata=metadata,
            )
        )
        if decision == "BLOCK":
            return PluginChainResult(blocked=True, events=events)

    return PluginChainResult(blocked=False, events=events)
