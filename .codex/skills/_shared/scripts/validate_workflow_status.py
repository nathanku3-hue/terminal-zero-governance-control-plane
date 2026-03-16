#!/usr/bin/env python3
"""
Validate workflow_status_latest.json against phase brief and project init.

Usage:
    python validate_workflow_status.py \\
        --status-json docs/context/workflow_status_latest.json \\
        --phase-brief docs/phase_brief/phase24c-brief.md \\
        --project-init docs/context/project_init_latest.md

Exit codes:
    0: PASS
    1: FAIL (validation errors)
    2: ERROR (missing files, invalid JSON)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_json(path: Path) -> Dict:
    """Load JSON file, exit 2 on error."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)


def load_text(path: Path) -> str:
    """Load text file, exit 2 on error."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(2)


def parse_workflow_weight_from_brief(brief_text: str) -> Dict[str, int]:
    """Extract workflow_weight from phase brief markdown."""
    weights = {}
    in_workflow_section = False

    for line in brief_text.split('\n'):
        if '## Workflow Profile' in line or '## Workflow Weight' in line:
            in_workflow_section = True
            continue
        if in_workflow_section and line.startswith('##'):
            break
        if in_workflow_section and ':' in line:
            for wtype in ['frontend', 'backend', 'governance', 'data', 'research']:
                if wtype.lower() in line.lower():
                    # Extract percentage
                    parts = line.split(':')
                    if len(parts) == 2:
                        try:
                            pct = int(parts[1].strip().replace('%', ''))
                            weights[wtype] = pct
                        except ValueError:
                            pass
    return weights


def validate_workflow_status(status: Dict, brief_text: str, init_text: str) -> Tuple[bool, List[str]]:
    """Validate workflow status JSON. Returns (is_valid, errors)."""
    errors = []

    # Check required top-level fields
    required_fields = ['schema_version', 'generated_at_utc', 'phase_id', 'phase_name',
                       'overall_status', 'overall_color', 'workflow_weight', 'workflow_status']
    for field in required_fields:
        if field not in status:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate workflow_weight sums to 100%
    weights = status.get('workflow_weight', {})
    total_weight = sum(weights.values())
    if total_weight != 100:
        errors.append(f"Workflow weight sum is {total_weight}%, expected 100%")

    # Validate workflow_weight matches phase brief
    brief_weights = parse_workflow_weight_from_brief(brief_text)
    if brief_weights:
        for wtype, expected in brief_weights.items():
            actual = weights.get(wtype, 0)
            if actual != expected:
                errors.append(f"Workflow weight mismatch for {wtype}: status={actual}%, brief={expected}%")

    # Validate workflow_status structure
    workflow_status = status.get('workflow_status', {})
    for wtype in ['frontend', 'backend', 'governance', 'data', 'research']:
        if wtype not in workflow_status:
            errors.append(f"Missing workflow_status entry for: {wtype}")
            continue

        wstatus = workflow_status[wtype]

        # Check required fields per workflow type
        required_wtype_fields = ['status', 'deliverables_total', 'deliverables_complete',
                                  'deliverables_blocked', 'criteria_total', 'criteria_pass', 'criteria_fail']
        for field in required_wtype_fields:
            if field not in wstatus:
                errors.append(f"Missing field in workflow_status.{wtype}: {field}")

        # Validate status values
        valid_statuses = ['n/a', 'green', 'yellow', 'red']
        if wstatus.get('status') not in valid_statuses:
            errors.append(f"Invalid status for {wtype}: {wstatus.get('status')}, expected one of {valid_statuses}")

        # Validate n/a status matches 0% weight
        if wstatus.get('status') == 'n/a' and weights.get(wtype, 0) != 0:
            errors.append(f"Status is n/a for {wtype} but weight is {weights.get(wtype)}% (expected 0%)")

        # Validate counts are non-negative integers
        for count_field in ['deliverables_total', 'deliverables_complete', 'deliverables_blocked',
                             'criteria_total', 'criteria_pass', 'criteria_fail']:
            val = wstatus.get(count_field)
            if not isinstance(val, int) or val < 0:
                errors.append(f"Invalid {count_field} for {wtype}: {val} (expected non-negative integer)")

    # Validate overall_status
    valid_overall = ['not_started', 'in_progress', 'blocked', 'complete']
    if status.get('overall_status') not in valid_overall:
        errors.append(f"Invalid overall_status: {status.get('overall_status')}, expected one of {valid_overall}")

    # Validate overall_color
    valid_colors = ['green', 'yellow', 'red']
    if status.get('overall_color') not in valid_colors:
        errors.append(f"Invalid overall_color: {status.get('overall_color')}, expected one of {valid_colors}")

    # Validate blocking_issues structure if present
    if 'blocking_issues' in status:
        for i, issue in enumerate(status['blocking_issues']):
            if 'type' not in issue or issue['type'] not in ['deliverable', 'criterion']:
                errors.append(f"blocking_issues[{i}]: invalid or missing type")
            if 'id' not in issue:
                errors.append(f"blocking_issues[{i}]: missing id")
            if 'reason' not in issue:
                errors.append(f"blocking_issues[{i}]: missing reason")

    # Validate realm_criteria structure if present
    if 'realm_criteria' in status:
        realm = status['realm_criteria']
        if 'realm' not in realm:
            errors.append("realm_criteria: missing realm field")
        if 'criteria_total' not in realm or not isinstance(realm.get('criteria_total'), int):
            errors.append("realm_criteria: invalid or missing criteria_total")

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(description='Validate workflow status JSON')
    parser.add_argument('--status-json', required=True, help='Path to workflow_status_latest.json')
    parser.add_argument('--phase-brief', required=True, help='Path to phase brief markdown')
    parser.add_argument('--project-init', required=True, help='Path to project init markdown')

    args = parser.parse_args()

    # Load files
    status = load_json(Path(args.status_json))
    brief_text = load_text(Path(args.phase_brief))
    init_text = load_text(Path(args.project_init))

    # Validate
    is_valid, errors = validate_workflow_status(status, brief_text, init_text)

    if is_valid:
        print("[OK] Workflow status validation passed")
        sys.exit(0)
    else:
        print("[FAIL] Workflow status validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
