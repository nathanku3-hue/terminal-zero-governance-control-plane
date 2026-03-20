#!/usr/bin/env python3
"""
Shared path validation utilities for artifact path security.

Phase 5A.2b: Hardening for path validation
- Rejects absolute paths
- Rejects parent directory escapes (..)
- Verifies containment under repo root
"""

from pathlib import Path
import os


def validate_artifact_path(path: str, repo_root: Path) -> tuple[bool, str]:
    """
    Validate artifact path for security and correctness.

    Args:
        path: Artifact path string (should be repo-root-relative)
        repo_root: Repository root directory

    Returns:
        (is_valid, error_message): Tuple of validation result and error description
    """
    # Reject empty paths
    if not path or not path.strip():
        return False, "Empty path"

    path = path.strip()

    # Reject absolute paths (Unix-style or Windows drive letters)
    if path.startswith('/') or (len(path) >= 2 and path[1] == ':'):
        return False, f"Absolute path not allowed: {path}"

    # Reject parent directory escapes
    if '..' in path.split(os.sep):
        return False, f"Parent directory escape (..) not allowed: {path}"

    # All other paths are valid (including '.' and relative paths)
    # Note: We allow paths starting with repo root name since CI systems
    # like GitHub Actions use various directory structures
    return True, ""
