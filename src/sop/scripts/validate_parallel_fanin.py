from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _resolve_manifest_path(context_dir: Path, override: Path | None) -> Path:
    if override is None:
        return context_dir / "parallel_shard_manifest_latest.json"
    return override


def _load_manifest(path: Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    if not path.exists():
        return None, None
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"Failed to read manifest {path}: {exc}"

    try:
        payload = json.loads(raw)
    except Exception as exc:
        return None, f"Invalid JSON in manifest {path}: {exc}"

    if not isinstance(payload, list):
        return None, "Manifest root must be a list of shard objects"

    shards: list[dict[str, Any]] = []
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            return None, f"Manifest shard at index {idx} is not an object"
        shards.append(item)
    return shards, None


def _validate_schema(shards: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for idx, shard in enumerate(shards):
        prefix = f"shard[{idx}]"
        shard_id = shard.get("shard_id")
        if not isinstance(shard_id, str) or not shard_id.strip():
            errors.append(f"{prefix}.shard_id must be a non-empty string")

        owned_files = shard.get("owned_files")
        if not isinstance(owned_files, list):
            errors.append(f"{prefix}.owned_files must be a list")
        else:
            for f_idx, owned in enumerate(owned_files):
                if not isinstance(owned, str) or not owned.strip():
                    errors.append(
                        f"{prefix}.owned_files[{f_idx}] must be a non-empty string"
                    )

        status = shard.get("status")
        if not isinstance(status, str) or not status.strip():
            errors.append(f"{prefix}.status must be a non-empty string")

        evidence_ok = shard.get("evidence_ok")
        if not isinstance(evidence_ok, bool):
            errors.append(f"{prefix}.evidence_ok must be a boolean")

    return len(errors) == 0, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate parallel fan-in shard manifest. "
            "Exit 0=pass, 1=gate fail, 2=input/infra error."
        )
    )
    parser.add_argument("--context-dir", type=Path, default=Path("docs/context"))
    parser.add_argument("--manifest-json", type=Path, default=None)
    args = parser.parse_args(argv)

    manifest_path = _resolve_manifest_path(args.context_dir, args.manifest_json)
    shards, load_error = _load_manifest(manifest_path)
    if load_error is not None:
        print(f"[ERROR] {load_error}")
        return 2
    if shards is None:
        print("[OK] no active parallel shards")
        return 0

    schema_ok, schema_errors = _validate_schema(shards)
    if not schema_ok:
        for item in schema_errors:
            print(f"[ERROR] {item}")
        return 2

    overlaps: list[str] = []
    ownership: dict[str, set[str]] = {}
    shard_failures: list[str] = []
    for shard in shards:
        shard_id = str(shard["shard_id"]).strip()
        status = str(shard["status"]).strip().upper()
        evidence_ok = bool(shard["evidence_ok"])
        if status != "PASS":
            shard_failures.append(f"shard {shard_id} status={status} (must be PASS)")
        if not evidence_ok:
            shard_failures.append(f"shard {shard_id} evidence_ok=false (must be true)")

        for owned_file in shard["owned_files"]:
            key = str(owned_file).strip()
            owners = ownership.setdefault(key, set())
            owners.add(shard_id)

    for owned_file, owners in ownership.items():
        if len(owners) > 1:
            sorted_owners = ",".join(sorted(owners))
            overlaps.append(f"{owned_file} owned by {sorted_owners}")

    if overlaps:
        for item in overlaps:
            print(f"[FAIL] Overlap: {item}")
        return 1

    if shard_failures:
        for item in shard_failures:
            print(f"[FAIL] {item}")
        return 1

    print("[OK] Parallel fan-in gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
