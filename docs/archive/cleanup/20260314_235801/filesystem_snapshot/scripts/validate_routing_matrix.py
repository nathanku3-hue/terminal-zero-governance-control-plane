#!/usr/bin/env python3
"""
Validate subagent routing matrix schema and artifact paths.

Phase 5A.2: Subagent Routing Matrix validator
- Validates YAML schema structure
- Checks all artifact paths exist relative to repo root
- Detects duplicate artifacts across required/optional/conditional
- Validates token budget constraints
- Exit codes: 0=valid, 1=validation error, 2=file error
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Any

# Import shared path validator
sys.path.insert(0, str(Path(__file__).parent))
from utils.path_validator import validate_artifact_path


def validate_schema(data: Dict[str, Any]) -> List[str]:
    """Validate routing matrix schema structure."""
    errors = []

    if "roles" not in data:
        errors.append("Missing top-level 'roles' key")
        return errors

    roles = data["roles"]
    if not isinstance(roles, dict):
        errors.append("'roles' must be a dictionary")
        return errors

    required_role_fields = [
        "description",
        "required_artifacts",
        "optional_artifacts",
        "conditional_artifacts",
        "excluded_artifacts",
        "max_context_tokens"
    ]

    for role_name, role_config in roles.items():
        if not isinstance(role_config, dict):
            errors.append(f"Role '{role_name}' must be a dictionary")
            continue

        # Check required fields
        for field in required_role_fields:
            if field not in role_config:
                errors.append(f"Role '{role_name}' missing required field '{field}'")

        # Validate field types
        if "required_artifacts" in role_config:
            if not isinstance(role_config["required_artifacts"], list):
                errors.append(f"Role '{role_name}': required_artifacts must be a list")

        if "optional_artifacts" in role_config:
            if not isinstance(role_config["optional_artifacts"], list):
                errors.append(f"Role '{role_name}': optional_artifacts must be a list")

        if "conditional_artifacts" in role_config:
            if not isinstance(role_config["conditional_artifacts"], dict):
                errors.append(f"Role '{role_name}': conditional_artifacts must be a dict")
            else:
                for condition, artifacts in role_config["conditional_artifacts"].items():
                    if not isinstance(artifacts, list):
                        errors.append(
                            f"Role '{role_name}': conditional_artifacts['{condition}'] must be a list"
                        )

        if "excluded_artifacts" in role_config:
            if not isinstance(role_config["excluded_artifacts"], list):
                errors.append(f"Role '{role_name}': excluded_artifacts must be a list")

        if "max_context_tokens" in role_config:
            if not isinstance(role_config["max_context_tokens"], int):
                errors.append(f"Role '{role_name}': max_context_tokens must be an integer")
            elif role_config["max_context_tokens"] <= 0:
                errors.append(f"Role '{role_name}': max_context_tokens must be positive")

    return errors


def validate_paths(data: Dict[str, Any], repo_root: Path) -> List[str]:
    """Validate that all artifact paths exist relative to repo root."""
    errors = []

    roles = data.get("roles", {})
    for role_name, role_config in roles.items():
        # Check required artifacts
        for artifact in role_config.get("required_artifacts", []):
            # Validate path security
            is_valid, error_msg = validate_artifact_path(artifact, repo_root)
            if not is_valid:
                errors.append(
                    f"Role '{role_name}': invalid required artifact path: {error_msg}"
                )
                continue

            artifact_path = repo_root / artifact
            if not artifact_path.exists():
                errors.append(
                    f"Role '{role_name}': required artifact not found: {artifact}"
                )

        # Check optional artifacts
        for artifact in role_config.get("optional_artifacts", []):
            # Validate path security
            is_valid, error_msg = validate_artifact_path(artifact, repo_root)
            if not is_valid:
                errors.append(
                    f"Role '{role_name}': invalid optional artifact path: {error_msg}"
                )
                continue

            artifact_path = repo_root / artifact
            if not artifact_path.exists():
                # Optional artifacts may not exist - this is informational
                pass

        # Check conditional artifacts
        for condition, artifacts in role_config.get("conditional_artifacts", {}).items():
            for artifact in artifacts:
                # Validate path security
                is_valid, error_msg = validate_artifact_path(artifact, repo_root)
                if not is_valid:
                    errors.append(
                        f"Role '{role_name}': invalid conditional artifact path ({condition}): {error_msg}"
                    )
                    continue

                artifact_path = repo_root / artifact
                if not artifact_path.exists():
                    # Conditional artifacts may not exist yet
                    pass

    return errors


def detect_duplicates(data: Dict[str, Any]) -> List[str]:
    """Detect duplicate artifacts within a role's artifact lists."""
    errors = []

    roles = data.get("roles", {})
    for role_name, role_config in roles.items():
        all_artifacts: Set[str] = set()

        # Collect all artifacts
        required = role_config.get("required_artifacts", [])
        optional = role_config.get("optional_artifacts", [])
        conditional_all = []
        for artifacts in role_config.get("conditional_artifacts", {}).values():
            conditional_all.extend(artifacts)

        # Check for duplicates
        for artifact in required:
            if artifact in all_artifacts:
                errors.append(
                    f"Role '{role_name}': duplicate artifact '{artifact}' in required_artifacts"
                )
            all_artifacts.add(artifact)

        for artifact in optional:
            if artifact in all_artifacts:
                errors.append(
                    f"Role '{role_name}': duplicate artifact '{artifact}' across required/optional"
                )
            all_artifacts.add(artifact)

        for artifact in conditional_all:
            if artifact in all_artifacts:
                errors.append(
                    f"Role '{role_name}': duplicate artifact '{artifact}' across required/optional/conditional"
                )
            all_artifacts.add(artifact)

    return errors


def main():
    if len(sys.argv) < 3:
        print("Usage: validate_routing_matrix.py <matrix_yaml> <repo_root>", file=sys.stderr)
        sys.exit(2)

    matrix_path = Path(sys.argv[1])
    repo_root = Path(sys.argv[2])

    if not matrix_path.exists():
        print(f"Error: Matrix file not found: {matrix_path}", file=sys.stderr)
        sys.exit(2)

    if not repo_root.is_dir():
        print(f"Error: Repo root not found: {repo_root}", file=sys.stderr)
        sys.exit(2)

    # Load YAML
    try:
        with open(matrix_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML: {e}", file=sys.stderr)
        sys.exit(2)

    # Run validations
    all_errors = []
    all_errors.extend(validate_schema(data))
    all_errors.extend(validate_paths(data, repo_root))
    all_errors.extend(detect_duplicates(data))

    if all_errors:
        print("Validation failed:", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Routing matrix valid: {len(data.get('roles', {}))} roles")
    sys.exit(0)


if __name__ == "__main__":
    main()
