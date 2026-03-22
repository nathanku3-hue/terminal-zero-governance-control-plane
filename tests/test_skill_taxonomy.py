"""Shared taxonomy definitions for skill activation tests.

This module provides canonical taxonomy definitions to prevent drift
between test expectations and production code.
"""

# Canonical skill category taxonomy
KNOWN_SKILL_CATEGORIES = {
    "testing",
    "database",
    "documentation",
    "refactoring",
    "security",
    "deployment",
    "analysis",
    "automation",
}

# Canonical risk level taxonomy
KNOWN_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}
