#!/usr/bin/env python3
"""
Validate Skills Registry
Validates skills/registry.yaml against schema and checks consistency with skill directories.
Registry-driven validation: only validates skills listed in registry, ignores legacy skills/* directories.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load and parse YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {file_path}: {e}")
        sys.exit(2)


def validate_registry_schema(registry: Dict[str, Any]) -> List[str]:
    """Validate registry against schema requirements."""
    errors = []

    # Check required top-level fields
    if 'schema_version' not in registry:
        errors.append("Missing required field: schema_version")
    elif not isinstance(registry['schema_version'], str):
        errors.append("schema_version must be a string")

    if 'last_updated' not in registry:
        errors.append("Missing required field: last_updated")
    elif not isinstance(registry['last_updated'], str):
        errors.append("last_updated must be a string")

    if 'skills' not in registry:
        errors.append("Missing required field: skills")
        return errors

    if not isinstance(registry['skills'], list):
        errors.append("skills must be a list")
        return errors

    # Validate each skill entry
    for idx, skill in enumerate(registry['skills']):
        prefix = f"skills[{idx}]"

        # Required fields
        required_fields = [
            'name', 'version', 'category', 'description',
            'author', 'approval_status', 'approval_decision_id', 'documentation'
        ]

        for field in required_fields:
            if field not in skill:
                errors.append(f"{prefix}: Missing required field '{field}'")

        # Validate name format (kebab-case)
        if 'name' in skill:
            name = skill['name']
            if not isinstance(name, str):
                errors.append(f"{prefix}: name must be a string")
            elif not all(c.islower() or c.isdigit() or c == '-' for c in name):
                errors.append(f"{prefix}: name must be kebab-case (lowercase, digits, hyphens only)")

        # Validate version format (semver)
        if 'version' in skill:
            version = skill['version']
            if not isinstance(version, str):
                errors.append(f"{prefix}: version must be a string")
            else:
                parts = version.split('.')
                if len(parts) != 3 or not all(p.isdigit() for p in parts):
                    errors.append(f"{prefix}: version must be semantic version (e.g., 1.0.0)")

        # Validate category
        valid_categories = [
            'database', 'frontend', 'backend', 'infrastructure',
            'testing', 'security', 'devops', 'data'
        ]
        if 'category' in skill:
            if skill['category'] not in valid_categories:
                errors.append(f"{prefix}: category must be one of {valid_categories}")

        # Validate approval_status
        valid_statuses = ['active', 'deprecated', 'disabled']
        if 'approval_status' in skill:
            if skill['approval_status'] not in valid_statuses:
                errors.append(f"{prefix}: approval_status must be one of {valid_statuses}")

        # Validate approval_decision_id format
        if 'approval_decision_id' in skill:
            decision_id = skill['approval_decision_id']
            if not isinstance(decision_id, str):
                errors.append(f"{prefix}: approval_decision_id must be a string")
            elif not decision_id.startswith('D-'):
                errors.append(f"{prefix}: approval_decision_id must start with 'D-' (e.g., D-176)")

    return errors


def validate_skill_directories(registry: Dict[str, Any], repo_root: Path) -> List[str]:
    """Validate that skill directories exist for registry entries."""
    errors = []

    skills = registry.get('skills', [])

    for skill in skills:
        name = skill.get('name')
        if not name:
            continue

        # Convert kebab-case to snake_case for directory name
        dir_name = name.replace('-', '_')
        skill_dir = repo_root / 'skills' / dir_name

        if not skill_dir.exists():
            errors.append(f"Skill directory not found: {skill_dir}")
            continue

        # Check required files
        required_files = ['skill.yaml', 'guardrails.yaml', 'eval.yaml', 'README.md']
        for file_name in required_files:
            file_path = skill_dir / file_name
            if not file_path.exists():
                errors.append(f"Missing required file: {file_path}")

        # Check examples directory
        examples_dir = skill_dir / 'examples'
        if not examples_dir.exists():
            errors.append(f"Missing examples directory: {examples_dir}")
        elif not any(examples_dir.iterdir()):
            errors.append(f"Examples directory is empty: {examples_dir}")

        # Validate documentation path matches
        doc_path = skill.get('documentation', '')
        expected_doc_path = f"skills/{dir_name}/README.md"
        if doc_path != expected_doc_path:
            errors.append(f"Skill '{name}': documentation path mismatch. Expected '{expected_doc_path}', got '{doc_path}'")

    return errors


def validate_no_duplicates(registry: Dict[str, Any]) -> List[str]:
    """Validate no duplicate skill names or name+version combinations."""
    errors = []

    skills = registry.get('skills', [])

    # Check for duplicate names
    names = [s.get('name') for s in skills if 'name' in s]
    name_counts = {}
    for name in names:
        name_counts[name] = name_counts.get(name, 0) + 1

    for name, count in name_counts.items():
        if count > 1:
            errors.append(f"Duplicate skill name: '{name}' appears {count} times")

    # Check for duplicate name+version combinations
    name_versions = [(s.get('name'), s.get('version')) for s in skills if 'name' in s and 'version' in s]
    nv_counts = {}
    for nv in name_versions:
        nv_counts[nv] = nv_counts.get(nv, 0) + 1

    for (name, version), count in nv_counts.items():
        if count > 1:
            errors.append(f"Duplicate skill name+version: '{name}' v{version} appears {count} times")

    return errors


def main():
    """Main validation entry point."""
    # Determine repo root
    repo_root = Path(__file__).parent.parent.resolve()

    # Load registry
    registry_path = repo_root / 'skills' / 'registry.yaml'
    if not registry_path.exists():
        print(f"ERROR: Registry not found: {registry_path}")
        sys.exit(1)

    print(f"Validating skills registry: {registry_path}")
    registry = load_yaml(registry_path)

    # Run validations
    all_errors = []

    print("  Checking schema compliance...")
    all_errors.extend(validate_registry_schema(registry))

    print("  Checking for duplicates...")
    all_errors.extend(validate_no_duplicates(registry))

    print("  Checking skill directories...")
    all_errors.extend(validate_skill_directories(registry, repo_root))

    # Report results
    if all_errors:
        print(f"\n[FAIL] Validation FAILED with {len(all_errors)} error(s):\n")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        skill_count = len(registry.get('skills', []))
        print(f"\n[OK] Validation PASSED: {skill_count} skill(s) in registry")
        sys.exit(0)


if __name__ == '__main__':
    main()
