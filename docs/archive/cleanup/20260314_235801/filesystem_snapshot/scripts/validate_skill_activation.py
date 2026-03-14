#!/usr/bin/env python3
"""Skill Activation Validator - Fail-closed validation.

Phase 5B.2: Thin Skill-Activation Bridge
Validates skill_activation_latest.json against governance requirements.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _load_json_safe(path: Path) -> dict[str, Any] | None:
    """Load JSON file, return None if missing or invalid."""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def _load_yaml_safe(path: Path) -> dict[str, Any] | None:
    """Load YAML file, return None if missing or invalid."""
    if yaml is None:
        return None
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def validate_skill_activation(
    skill_activation_json: Path,
    repo_root: Path,
) -> tuple[bool, list[str]]:
    """Validate skill_activation_latest.json with fail-closed semantics.

    Args:
        skill_activation_json: Path to skill_activation_latest.json
        repo_root: Repository root path

    Returns:
        Tuple of (is_valid, errors)
    """
    errors: list[str] = []

    # Load skill_activation_latest.json
    skill_activation = _load_json_safe(skill_activation_json)
    if skill_activation is None:
        errors.append(f"Failed to load {skill_activation_json}")
        return False, errors

    # Validate schema_version
    schema_version = skill_activation.get("schema_version")
    if schema_version != "1.0.0":
        errors.append(f"Invalid schema_version: {schema_version} (expected 1.0.0)")

    # Validate generated_at_utc
    generated_at_utc = skill_activation.get("generated_at_utc")
    if not isinstance(generated_at_utc, str) or not generated_at_utc.strip():
        errors.append("Missing or invalid generated_at_utc")

    # Validate skill_activation section
    skill_activation_data = skill_activation.get("skill_activation")
    if not isinstance(skill_activation_data, dict):
        errors.append("Missing or invalid skill_activation section")
        return False, errors

    # Validate status
    status = skill_activation_data.get("status")
    if status not in {"ok", "degraded", "failed"}:
        errors.append(f"Invalid status: {status} (expected ok/degraded/failed)")

    # Validate skills list
    skills = skill_activation_data.get("skills")
    if not isinstance(skills, list):
        errors.append("Missing or invalid skills list")
        return False, errors

    # Load governance files for cross-validation
    sop_config_path = repo_root / ".sop_config.yaml"
    allowlist_path = repo_root / "extension_allowlist.yaml"
    registry_path = repo_root / "skills" / "registry.yaml"

    sop_config = _load_yaml_safe(sop_config_path)
    allowlist = _load_yaml_safe(allowlist_path)
    registry = _load_yaml_safe(registry_path)

    if sop_config is None:
        errors.append(f"Failed to load {sop_config_path}")
    if allowlist is None:
        errors.append(f"Failed to load {allowlist_path}")
    if registry is None:
        errors.append(f"Failed to load {registry_path}")

    # If governance files failed to load, fail validation
    if sop_config is None or allowlist is None or registry is None:
        return False, errors

    # Build lookups
    active_skills_config = sop_config.get("active_skills", [])
    if not isinstance(active_skills_config, list):
        errors.append("Invalid active_skills in .sop_config.yaml")
        return False, errors

    allowlist_skills: dict[str, dict[str, Any]] = {}
    for skill in allowlist.get("skills", []):
        skill_name = skill.get("skill_name")
        if skill_name:
            allowlist_skills[skill_name] = skill

    registry_skills: dict[str, dict[str, Any]] = {}
    for skill in registry.get("skills", []):
        skill_name = skill.get("name")
        if skill_name:
            registry_skills[skill_name] = skill

    # Build set of skills present in artifact
    artifact_skill_names = {skill.get("name") for skill in skills if isinstance(skill, dict)}

    # Validate ALL configured active_skills are present in artifact
    project_name = sop_config.get("project_name", "")
    for config_skill_name in active_skills_config:
        if not isinstance(config_skill_name, str):
            errors.append(f"Invalid skill name in active_skills: {config_skill_name}")
            continue

        # Check if skill is in allowlist and applicable to this project
        if config_skill_name not in allowlist_skills:
            errors.append(f"Configured skill '{config_skill_name}' not found in extension_allowlist.yaml")
            continue

        allowlist_entry = allowlist_skills[config_skill_name]
        applicable_projects = allowlist_entry.get("applicable_projects", [])

        # Skip if not applicable to this project
        if isinstance(applicable_projects, list):
            if "all" not in applicable_projects and project_name not in applicable_projects:
                continue

        # Skill should be in artifact
        if config_skill_name not in artifact_skill_names:
            errors.append(f"Configured skill '{config_skill_name}' missing from skill_activation artifact")

    # Validate each skill in the activation list
    for skill in skills:
        if not isinstance(skill, dict):
            errors.append(f"Invalid skill entry: {skill}")
            continue

        skill_name = skill.get("name")
        if not isinstance(skill_name, str) or not skill_name:
            errors.append("Skill missing name field")
            continue

        # Validate skill is in active_skills config
        if skill_name not in active_skills_config:
            errors.append(f"Skill '{skill_name}' not in .sop_config.yaml active_skills")

        # Validate skill is in allowlist
        if skill_name not in allowlist_skills:
            errors.append(f"Skill '{skill_name}' not in extension_allowlist.yaml")
            continue

        allowlist_entry = allowlist_skills[skill_name]

        # Validate status is active
        allowlist_status = allowlist_entry.get("status")
        if allowlist_status != "active":
            errors.append(f"Skill '{skill_name}' has status '{allowlist_status}' in allowlist (must be 'active')")

        # Validate applicable_projects (match resolver logic)
        applicable_projects = allowlist_entry.get("applicable_projects", [])
        if isinstance(applicable_projects, list):
            if "all" not in applicable_projects and project_name not in applicable_projects:
                errors.append(f"Skill '{skill_name}' not applicable to project '{project_name}'")

        # Validate version matches
        skill_version = skill.get("version")
        allowlist_version = str(allowlist_entry.get("version", ""))
        if str(skill_version) != allowlist_version:
            errors.append(f"Skill '{skill_name}' version mismatch: {skill_version} != {allowlist_version}")

        # Validate required fields
        if not skill.get("manifest_path"):
            errors.append(f"Skill '{skill_name}' missing manifest_path")
        if not skill.get("category"):
            errors.append(f"Skill '{skill_name}' missing category")
        if not skill.get("approval_decision_id"):
            errors.append(f"Skill '{skill_name}' missing approval_decision_id")

        # Validate manifest exists
        manifest_path = repo_root / skill.get("manifest_path", "")
        if not manifest_path.exists():
            errors.append(f"Skill '{skill_name}' manifest not found: {manifest_path}")

    # Validate warnings and errors lists
    warnings = skill_activation_data.get("warnings")
    if not isinstance(warnings, list):
        errors.append("Missing or invalid warnings list")

    activation_errors = skill_activation_data.get("errors")
    if not isinstance(activation_errors, list):
        errors.append("Missing or invalid errors list")

    # If status is "failed", there must be errors
    if status == "failed" and not activation_errors:
        errors.append("Status is 'failed' but no errors reported")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate skill activation artifact")
    parser.add_argument(
        "--skill-activation-json",
        default="docs/context/skill_activation_latest.json",
        help="Path to skill_activation_latest.json",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path",
    )
    args = parser.parse_args()

    skill_activation_json = Path(args.skill_activation_json)
    repo_root = Path(args.repo_root).resolve()

    is_valid, errors = validate_skill_activation(skill_activation_json, repo_root)

    if is_valid:
        print(f"✓ Skill activation valid: {skill_activation_json}")
        return 0
    else:
        print(f"✗ Skill activation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
