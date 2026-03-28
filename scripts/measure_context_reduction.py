#!/usr/bin/env python3
"""
Measure context reduction from subagent routing matrix.

Phase 5A.2: Token savings calculator
- Loads routing matrix and calculates token budgets per role
- Measures actual artifact sizes using token estimator (len(text) // 4)
- Compares against baseline (all artifacts loaded for all roles)
- Reports token savings and reduction percentage
- Exit codes: 0=success, 2=file error
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

# Import shared path validator
sys.path.insert(0, str(Path(__file__).parent))
from utils.path_validator import validate_artifact_path


def estimate_tokens(text: str) -> int:
    """Deterministic simple token estimate: ~4 chars per token."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def load_artifact_size(artifact_path: Path) -> int:
    """Load artifact and return token count."""
    try:
        with open(artifact_path, "r", encoding="utf-8") as f:
            content = f.read()
        return estimate_tokens(content)
    except Exception:
        return 0


def calculate_role_context(
    role_name: str,
    role_config: Dict,
    repo_root: Path,
    include_conditional: bool = False
) -> Tuple[int, List[str]]:
    """Calculate total context tokens for a role."""
    total_tokens = 0
    loaded_artifacts = []

    # Required artifacts
    for artifact in role_config.get("required_artifacts", []):
        # Validate path security
        is_valid, error_msg = validate_artifact_path(artifact, repo_root)
        if not is_valid:
            print(f"Warning: Skipping invalid required artifact in role '{role_name}': {error_msg}", file=sys.stderr)
            sys.exit(1)

        artifact_path = repo_root / artifact
        tokens = load_artifact_size(artifact_path)
        total_tokens += tokens
        loaded_artifacts.append(f"{artifact} ({tokens} tokens)")

    # Optional artifacts
    for artifact in role_config.get("optional_artifacts", []):
        # Validate path security
        is_valid, error_msg = validate_artifact_path(artifact, repo_root)
        if not is_valid:
            print(f"Warning: Skipping invalid optional artifact in role '{role_name}': {error_msg}", file=sys.stderr)
            sys.exit(1)

        artifact_path = repo_root / artifact
        tokens = load_artifact_size(artifact_path)
        total_tokens += tokens
        loaded_artifacts.append(f"{artifact} ({tokens} tokens, optional)")

    # Conditional artifacts (if requested)
    if include_conditional:
        for condition, artifacts in role_config.get("conditional_artifacts", {}).items():
            for artifact in artifacts:
                # Validate path security
                is_valid, error_msg = validate_artifact_path(artifact, repo_root)
                if not is_valid:
                    print(f"Warning: Skipping invalid conditional artifact in role '{role_name}': {error_msg}", file=sys.stderr)
                    sys.exit(1)

                artifact_path = repo_root / artifact
                tokens = load_artifact_size(artifact_path)
                total_tokens += tokens
                loaded_artifacts.append(f"{artifact} ({tokens} tokens, conditional:{condition})")

    return total_tokens, loaded_artifacts


def calculate_baseline_context(data: Dict, repo_root: Path) -> Tuple[int, set]:
    """Calculate baseline context (all artifacts for all roles)."""
    all_artifacts = set()

    roles = data.get("roles", {})
    for role_config in roles.values():
        all_artifacts.update(role_config.get("required_artifacts", []))
        all_artifacts.update(role_config.get("optional_artifacts", []))
        for artifacts in role_config.get("conditional_artifacts", {}).values():
            all_artifacts.update(artifacts)

    total_tokens = 0
    for artifact in all_artifacts:
        # Validate path security
        is_valid, error_msg = validate_artifact_path(artifact, repo_root)
        if not is_valid:
            print(f"Warning: Skipping invalid artifact in baseline: {error_msg}", file=sys.stderr)
            sys.exit(1)

        artifact_path = repo_root / artifact
        tokens = load_artifact_size(artifact_path)
        total_tokens += tokens

    return total_tokens, all_artifacts


def main():
    if len(sys.argv) < 3:
        print("Usage: measure_context_reduction.py <matrix_yaml> <repo_root> [--include-conditional]", file=sys.stderr)
        sys.exit(2)

    matrix_path = Path(sys.argv[1])
    repo_root = Path(sys.argv[2])
    include_conditional = "--include-conditional" in sys.argv

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

    # Calculate baseline
    baseline_tokens, baseline_artifacts = calculate_baseline_context(data, repo_root)
    print("Baseline Context (all artifacts for all roles):")
    print(f"  Total artifacts: {len(baseline_artifacts)}")
    print(f"  Total tokens: {baseline_tokens:,}")
    print()

    # Calculate per-role context
    roles = data.get("roles", {})
    total_savings = 0
    role_count = len(roles)

    print("Per-Role Context Analysis:")
    print()

    for role_name, role_config in roles.items():
        role_tokens, loaded_artifacts = calculate_role_context(
            role_name, role_config, repo_root, include_conditional
        )
        max_budget = role_config.get("max_context_tokens", 0)
        savings = baseline_tokens - role_tokens
        reduction_pct = (savings / baseline_tokens * 100) if baseline_tokens > 0 else 0
        total_savings += savings

        print(f"Role: {role_name}")
        print(f"  Description: {role_config.get('description', 'N/A')}")
        print(f"  Actual tokens: {role_tokens:,}")
        print(f"  Budget: {max_budget:,} tokens")
        print(f"  Budget utilization: {role_tokens / max_budget * 100:.1f}%" if max_budget > 0 else "  Budget utilization: N/A")
        print(f"  Savings vs baseline: {savings:,} tokens ({reduction_pct:.1f}% reduction)")
        print(f"  Loaded artifacts: {len(loaded_artifacts)}")
        for artifact_info in loaded_artifacts:
            print(f"    - {artifact_info}")
        print()

    # Summary
    avg_savings = total_savings / role_count if role_count > 0 else 0
    avg_reduction_pct = (avg_savings / baseline_tokens * 100) if baseline_tokens > 0 else 0

    print("Summary:")
    print(f"  Total roles: {role_count}")
    print(f"  Average savings per role: {avg_savings:,.0f} tokens ({avg_reduction_pct:.1f}% reduction)")
    print(f"  Total baseline tokens: {baseline_tokens:,}")
    print(f"  Conditional artifacts included: {include_conditional}")

    sys.exit(0)


if __name__ == "__main__":
    main()
