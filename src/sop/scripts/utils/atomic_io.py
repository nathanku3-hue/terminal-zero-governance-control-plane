"""Atomic file I/O utilities.

Provides atomic write operations using temp file + rename pattern to ensure
file consistency even if the write operation is interrupted.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Atomically write text content to a file.

    Creates parent directories if needed. Uses temp file + rename to ensure
    atomicity - the file will either be fully written or not modified at all.

    Args:
        path: Target file path
        content: Text content to write
        encoding: Text encoding (default: utf-8)

    Raises:
        OSError: If write or rename fails
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(path: Path, data: Any, encoding: str = "utf-8") -> None:
    """Atomically write JSON data to a file.

    Creates parent directories if needed. Uses temp file + rename to ensure
    atomicity. Output is formatted with 2-space indentation and trailing newline.

    Args:
        path: Target file path
        data: Data to serialize as JSON
        encoding: Text encoding (default: utf-8)

    Raises:
        OSError: If write or rename fails
        TypeError: If data is not JSON serializable
    """
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    atomic_write_text(path, content, encoding=encoding)
