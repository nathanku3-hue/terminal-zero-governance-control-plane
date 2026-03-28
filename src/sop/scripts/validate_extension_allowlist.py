#!/usr/bin/env python3
"""
Validate Extension Allowlist
Validates extension_allowlist.yaml and .sop_config.yaml against schemas.
Checks approval_decision_id exists in decision log.md.
Validates project config against global allowlist.
"""

import sys
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any
import argparse


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load and parse YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {file_path}: {e}")
        sys.exit(2)


def load_decision_log(repo_root: Path) -> str:
    """Load decision log content."""
    decision_log_path = repo_root / 'docs' / 'decision log.md'
    if not decision_log_path.exists():
        print(f"WARNING: Decision log not found: {decision_log_path}")
        return ""

    try:
        return decision_log_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"WARNING: Failed to read decision log: {e}")
        return ""


def validate_allowlist_schema(allowlist: Dict[str, Any]) -> List[str]:
    """Validate allowlist against schema requirements."""
    errors = []

    # Check required top-level fields
    if 'schema_version' not in allowlist:
        errors.append("Missing required field: schema_version")
    elif not isinstance(allowlist['schema_version'], str):
        errors.append("schema_version must be a string")

    if 'last_updated' not in allowlist:
        errors.append("Missing required field: last_updated")
    elif not isinstance(allowlist['last_updated'], str):
        errors.append("last_updated must be a string")

    if 'skills' not in allowlist:
        errors.append("Missing required field: skills")
        return errors

    if not isinstance(allowlist['skills'], list):
        errors.append("skills must be a list")
        return errors

    # Validate each skill entry
    for idx, skill in enumerate(allowlist['skills']):
        prefix = f"skills[{idx}]"

        # Required fields
        required_fields = [
            'skill_name', 'version', 'approved_by', 'approval_decision_id',
            'approval_date', 'status', 'risk_level', 'applicable_projects'
        ]

        for field in required_fields:
            if field not in skill:
                errors.append(f"{prefix}: Missing required field '{field}'")

        # Validate skill_name format
        if 'skill_name' in skill:
            name = skill['skill_name']
            if not isinstance(name, str):
                errors.append(f"{prefix}: skill_name must be a string")
            elif not all(c.islower() or c.isdigit() or c == '-' for c in name):
                errors.append(f"{prefix}: skill_name must be kebab-case")

        # Validate version format
        if 'version' in skill:
            version = skill['version']
            if not isinstance(version, (str, float)):
                errors.append(f"{prefix}: version must be a string or number")
            else:
                parts = str(version).split('.')
                if len(parts) != 3 or not all(p.isdigit() for p in parts):
                    errors.append(f"{prefix}: version must be semantic version (e.g., 1.0.0)")

        # Validate approved_by
        valid_approvers = ['PM', 'CEO', 'PM/CEO']
        if 'approved_by' in skill and skill['approved_by'] not in valid_approvers:
            errors.append(f"{prefix}: approved_by must be one of {valid_approvers}")

        # Validate approval authority rules based on risk level
        if 'risk_level' in skill and 'approved_by' in skill:
            risk_level = skill['risk_level']
            approved_by = skill['approved_by']
            skill_name = skill.get('skill_name', 'unknown')

            # LOW-risk: PM, CEO, or PM/CEO allowed
            if risk_level == "LOW" and approved_by not in ["PM", "CEO", "PM/CEO"]:
                errors.append(f"{prefix}: LOW-risk skill '{skill_name}' requires PM or CEO approval, got '{approved_by}'")

            # MEDIUM/HIGH-risk: CEO or PM/CEO required (reject PM alone)
            if risk_level in ["MEDIUM", "HIGH"] and approved_by not in ["CEO", "PM/CEO"]:
                errors.append(f"{prefix}: {risk_level}-risk skill '{skill_name}' requires CEO approval, got '{approved_by}'")

        # Validate approval_decision_id format
        if 'approval_decision_id' in skill:
            decision_id = skill['approval_decision_id']
            if not isinstance(decision_id, str):
                errors.append(f"{prefix}: approval_decision_id must be a string")
            elif not re.match(r'^D-\d+[a-z]?$', decision_id):
                errors.append(f"{prefix}: approval_decision_id must match pattern D-NNN[a] (e.g., D-176)")

        # Validate status
        valid_statuses = ['active', 'deprecated', 'disabled']
        if 'status' in skill and skill['status'] not in valid_statuses:
            errors.append(f"{prefix}: status must be one of {valid_statuses}")

        # Validate risk_level
        valid_risk_levels = ['LOW', 'MEDIUM', 'HIGH']
        if 'risk_level' in skill and skill['risk_level'] not in valid_risk_levels:
            errors.append(f"{prefix}: risk_level must be one of {valid_risk_levels}")

        # Validate applicable_projects
        if 'applicable_projects' in skill:
            projects = skill['applicable_projects']
            if not isinstance(projects, list):
                errors.append(f"{prefix}: applicable_projects must be a list")
            elif len(projects) == 0:
                errors.append(f"{prefix}: applicable_projects must contain at least one entry")

        # Validate optional assigned_roles (Phase 1.2)
        if 'assigned_roles' in skill:
            assigned_roles = skill['assigned_roles']
            valid_roles = ['worker', 'auditor', 'planner']
            if not isinstance(assigned_roles, list):
                errors.append(f"{prefix}: assigned_roles must be a list")
            elif len(assigned_roles) == 0:
                errors.append(f"{prefix}: assigned_roles must be non-empty if present")
            else:
                for ar in assigned_roles:
                    if ar not in valid_roles:
                        errors.append(
                            f"{prefix}: assigned_roles entry '{ar}' must be one of {valid_roles}"
                        )

        # Validate conditional fields
        if 'status' in skill:
            if skill['status'] == 'deprecated':
                if 'deprecation_reason' not in skill:
                    errors.append(f"{prefix}: deprecation_reason required when status=deprecated")
                if 'removal_date' not in skill:
                    errors.append(f"{prefix}: removal_date required when status=deprecated")

            if skill['status'] == 'disabled':
                if 'disable_reason' not in skill:
                    errors.append(f"{prefix}: disable_reason required when status=disabled")

    return errors


def validate_approval_decisions(allowlist: Dict[str, Any], decision_log: str) -> List[str]:
    """Validate that all approval_decision_ids exist in decision log."""
    errors = []

    if not decision_log:
        errors.append("WARNING: Cannot validate approval decisions (decision log not available)")
        return errors

    skills = allowlist.get('skills', [])

    for skill in skills:
        decision_id = skill.get('approval_decision_id')
        skill_name = skill.get('skill_name', 'unknown')

        if not decision_id:
            continue

        # Search for decision ID in decision log
        # Look for patterns like "D-176" or "### D-176" or "| D-176 |"
        pattern = rf'\b{re.escape(decision_id)}\b'
        if not re.search(pattern, decision_log):
            errors.append(f"Skill '{skill_name}': approval_decision_id '{decision_id}' not found in decision log")

    return errors


def validate_no_duplicates(allowlist: Dict[str, Any]) -> List[str]:
    """Validate no duplicate skill entries."""
    errors = []

    skills = allowlist.get('skills', [])

    # Check for duplicate skill_name + version combinations
    name_versions = [(s.get('skill_name'), s.get('version')) for s in skills if 'skill_name' in s and 'version' in s]
    nv_counts = {}
    for nv in name_versions:
        nv_counts[nv] = nv_counts.get(nv, 0) + 1

    for (name, version), count in nv_counts.items():
        if count > 1:
            errors.append(f"Duplicate skill entry: '{name}' v{version} appears {count} times")

    return errors


def validate_project_config(config: Dict[str, Any], allowlist: Dict[str, Any]) -> List[str]:
    """Validate project config against allowlist."""
    errors = []

    # Check required fields
    required_fields = ['project_name', 'guardrail_strength', 'active_skills']
    for field in required_fields:
        if field not in config:
            errors.append(f"project_config: Missing required field '{field}'")

    # Validate guardrail_strength
    valid_strengths = ['loose', 'medium', 'tight']
    if 'guardrail_strength' in config and config['guardrail_strength'] not in valid_strengths:
        errors.append(f"project_config: guardrail_strength must be one of {valid_strengths}")

    # Validate active_skills
    if 'active_skills' not in config:
        return errors

    active_skills = config['active_skills']
    if not isinstance(active_skills, list):
        errors.append("project_config: active_skills must be a list")
        return errors

    # Build allowlist lookup
    allowlist_skills = {}
    for skill in allowlist.get('skills', []):
        skill_name = skill.get('skill_name')
        if skill_name:
            allowlist_skills[skill_name] = skill

    # Validate each active skill
    project_name = config.get('project_name', 'unknown')

    for skill_name in active_skills:
        if skill_name not in allowlist_skills:
            errors.append(f"project_config: active_skill '{skill_name}' not in global allowlist")
            continue

        allowlist_entry = allowlist_skills[skill_name]

        # Check status
        status = allowlist_entry.get('status')
        if status != 'active':
            errors.append(f"project_config: active_skill '{skill_name}' has status '{status}' (must be 'active')")

        # Check applicable_projects
        applicable_projects = allowlist_entry.get('applicable_projects', [])
        if 'all' not in applicable_projects and project_name not in applicable_projects:
            errors.append(f"project_config: active_skill '{skill_name}' not applicable to project '{project_name}'")

    # Validate disabled_skills (if present)
    if 'disabled_skills' in config:
        disabled_skills = config['disabled_skills']
        if not isinstance(disabled_skills, list):
            errors.append("project_config: disabled_skills must be a list")

    return errors


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description='Validate extension allowlist and project config')
    parser.add_argument('--repo-root', type=str, help='Repository root path (default: auto-detect)')
    parser.add_argument('--skip-decision-log', action='store_true', help='Skip decision log validation')
    args = parser.parse_args()

    # Determine repo root
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = Path(__file__).parent.parent.resolve()

    # Load allowlist
    allowlist_path = repo_root / 'extension_allowlist.yaml'
    if not allowlist_path.exists():
        print(f"ERROR: Allowlist not found: {allowlist_path}")
        sys.exit(1)

    print(f"Validating extension allowlist: {allowlist_path}")
    allowlist = load_yaml(allowlist_path)

    # Load project config
    project_config_path = repo_root / '.sop_config.yaml'
    project_config = None
    if project_config_path.exists():
        print(f"Validating project config: {project_config_path}")
        project_config = load_yaml(project_config_path)

    # Load decision log
    decision_log = ""
    if not args.skip_decision_log:
        decision_log = load_decision_log(repo_root)

    # Run validations
    all_errors = []

    print("  Checking allowlist schema...")
    all_errors.extend(validate_allowlist_schema(allowlist))

    print("  Checking for duplicates...")
    all_errors.extend(validate_no_duplicates(allowlist))

    if not args.skip_decision_log:
        print("  Checking approval decisions...")
        all_errors.extend(validate_approval_decisions(allowlist, decision_log))

    if project_config:
        print("  Checking project config...")
        all_errors.extend(validate_project_config(project_config, allowlist))

    # Report results
    if all_errors:
        print(f"\nFAIL Validation FAILED with {len(all_errors)} error(s):\n")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        skill_count = len(allowlist.get('skills', []))
        print(f"\nPASS Validation PASSED: {skill_count} skill(s) in allowlist")
        if project_config:
            active_count = len(project_config.get('active_skills', []))
            print(f"PASS Project config valid: {active_count} active skill(s)")
        sys.exit(0)


if __name__ == '__main__':
    main()
