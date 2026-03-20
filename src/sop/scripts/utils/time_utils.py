"""Canonical time utility functions for consistent UTC timestamp handling across scripts.

This module provides standardized functions for working with UTC timestamps,
replacing various local implementations of _utc_now, _utc_iso, and _utc_now_iso
found throughout the scripts/ directory.

Usage:
    from scripts.utils.time_utils import utc_now, utc_iso, utc_now_iso

    # Get current UTC datetime
    now = utc_now()

    # Convert datetime to ISO string
    timestamp = utc_iso(now)

    # Get current UTC as ISO string (convenience)
    timestamp = utc_now_iso()
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime.

    Returns:
        datetime: Current time in UTC with timezone info.
    """
    return datetime.now(timezone.utc)


def utc_iso(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string with Z suffix.

    Args:
        dt: Datetime object to convert (should be UTC).

    Returns:
        str: ISO 8601 formatted string (e.g., "2026-03-09T15:30:45Z").
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_iso() -> str:
    """Get current UTC time as ISO 8601 string.

    Convenience function combining utc_now() and utc_iso().

    Returns:
        str: Current UTC time in ISO 8601 format with Z suffix.
    """
    return utc_iso(utc_now())
