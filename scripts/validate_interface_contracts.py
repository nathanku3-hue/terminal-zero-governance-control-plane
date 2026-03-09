from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _resolve_path(raw_path: str, manifest_path: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path

    cwd_candidate = (Path.cwd() / path).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    manifest_candidate = (manifest_path.parent / path).resolve()
    if manifest_candidate.exists():
        return manifest_candidate

    return cwd_candidate


def _load_manifest(manifest_path: Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not manifest_path.exists():
        return None, f"Manifest does not exist: {manifest_path}"

    try:
        raw = manifest_path.read_text(encoding="utf-8-sig")
    except Exception as exc:  # pragma: no cover - defensive
        return None, f"Failed to read manifest {manifest_path}: {exc}"

    try:
        payload = json.loads(raw)
    except Exception as exc:
        return None, f"Invalid JSON in manifest {manifest_path}: {exc}"

    if not isinstance(payload, dict):
        return None, "Manifest root must be an object"

    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        return None, "Manifest root must contain contracts[] list"

    normalized: list[dict[str, Any]] = []
    for idx, entry in enumerate(contracts):
        if not isinstance(entry, dict):
            return None, f"contracts[{idx}] must be an object"

        contract_id = entry.get("id")
        producer_path = entry.get("producer_path")
        consumer_path = entry.get("consumer_path")
        required_keys = entry.get("required_keys")
        required_markers = entry.get("required_markers")

        if not isinstance(contract_id, str) or not contract_id.strip():
            return None, f"contracts[{idx}].id must be a non-empty string"
        if not isinstance(producer_path, str) or not producer_path.strip():
            return None, f"contracts[{idx}].producer_path must be a non-empty string"
        if not isinstance(consumer_path, str) or not consumer_path.strip():
            return None, f"contracts[{idx}].consumer_path must be a non-empty string"
        if not isinstance(required_keys, list):
            return None, f"contracts[{idx}].required_keys must be a list"
        if not isinstance(required_markers, list):
            return None, f"contracts[{idx}].required_markers must be a list"

        for key_idx, key in enumerate(required_keys):
            if not isinstance(key, str) or not key.strip():
                return None, f"contracts[{idx}].required_keys[{key_idx}] must be a non-empty string"
        for marker_idx, marker in enumerate(required_markers):
            if not isinstance(marker, str) or not marker.strip():
                return None, f"contracts[{idx}].required_markers[{marker_idx}] must be a non-empty string"

        status = entry.get("status", "ACTIVE")
        if status is not None and not isinstance(status, str):
            return None, f"contracts[{idx}].status must be a string when provided"

        normalized.append(entry)

    return normalized, None


def _has_json_path(data: Any, dotted_key: str) -> bool:
    current = data
    for part in dotted_key.split("."):
        if not part:
            return False
        if isinstance(current, dict):
            if part not in current:
                return False
            current = current[part]
            continue
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return False
            if index < 0 or index >= len(current):
                return False
            current = current[index]
            continue
        return False
    return True


def _validate_contracts(
    contracts: list[dict[str, Any]],
    manifest_path: Path,
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    json_cache: dict[Path, Any] = {}
    text_cache: dict[Path, str] = {}

    for contract in contracts:
        contract_id = str(contract["id"]).strip()
        status = str(contract.get("status", "ACTIVE")).strip().upper()
        if status in {"DISABLED", "INACTIVE", "SKIP"}:
            continue

        producer = _resolve_path(str(contract["producer_path"]), manifest_path)
        consumer = _resolve_path(str(contract["consumer_path"]), manifest_path)
        required_keys = [str(item).strip() for item in contract.get("required_keys", [])]
        required_markers = [str(item).strip() for item in contract.get("required_markers", [])]

        file_targets: list[tuple[str, Path]] = [("producer", producer), ("consumer", consumer)]

        missing_any = False
        for role, path in file_targets:
            if not path.exists():
                failures.append(f"{contract_id}: Missing {role} file: {path}")
                missing_any = True
        if missing_any:
            continue

        if required_keys:
            json_targets = [path for _, path in file_targets if path.suffix.lower() == ".json"]
            if not json_targets:
                failures.append(
                    f"{contract_id}: required_keys provided but no JSON producer/consumer file was supplied"
                )
            for path in json_targets:
                if path not in json_cache:
                    try:
                        json_cache[path] = json.loads(path.read_text(encoding="utf-8-sig"))
                    except Exception as exc:
                        failures.append(f"{contract_id}: Invalid JSON in {path}: {exc}")
                        continue
                payload = json_cache[path]
                for dotted_key in required_keys:
                    if not _has_json_path(payload, dotted_key):
                        failures.append(
                            f"{contract_id}: {path} missing JSON key '{dotted_key}'"
                        )

        if required_markers:
            text_targets = [path for _, path in file_targets if path.suffix.lower() != ".json"]
            if not text_targets:
                failures.append(
                    f"{contract_id}: required_markers provided but no text producer/consumer file was supplied"
                )
            for path in text_targets:
                if path not in text_cache:
                    try:
                        text_cache[path] = path.read_text(encoding="utf-8-sig")
                    except Exception as exc:
                        failures.append(f"{contract_id}: Failed to read text file {path}: {exc}")
                        continue
                content = text_cache[path]
                for marker in required_markers:
                    if marker not in content:
                        failures.append(
                            f"{contract_id}: {path} missing text marker '{marker}'"
                        )

    return len(failures) == 0, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate producer/consumer interface contracts. "
            "Exit 0=pass, 1=validation fail, 2=input/infra error."
        )
    )
    parser.add_argument("--manifest-json", type=Path, required=True)
    args = parser.parse_args(argv)

    contracts, error = _load_manifest(args.manifest_json)
    if error is not None:
        print(f"[ERROR] {error}")
        return 2
    if contracts is None:  # pragma: no cover - defensive
        print("[ERROR] No contracts were loaded")
        return 2

    passed, failures = _validate_contracts(contracts, args.manifest_json)
    if not passed:
        for item in failures:
            print(f"[FAIL] {item}")
        return 1

    print(f"[OK] Interface contract gate passed ({len(contracts)} contract(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
