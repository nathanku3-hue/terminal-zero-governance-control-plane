"""Shared JSON utilities for safe loading and parsing."""

import json
from pathlib import Path
from typing import Any


def safe_load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """
    Safely load a JSON file that must contain an object at the root.

    Args:
        path: Path to the JSON file

    Returns:
        Tuple of (data, error_message):
        - On success: (dict, None)
        - On failure: (None, error_message)

    Error types:
        - "file_not_found": File does not exist
        - "read_error: {exc}": File read failed
        - "json_error: {exc}": JSON parsing failed
        - "json_error: root must be object": JSON root is not an object
    """
    if not path.exists():
        return None, "file_not_found"

    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return None, f"read_error: {exc}"

    try:
        payload = json.loads(raw)
    except Exception as exc:
        return None, f"json_error: {exc}"

    if not isinstance(payload, dict):
        return None, "json_error: root must be object"

    return payload, None
