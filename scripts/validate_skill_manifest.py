#!/usr/bin/env python3
"""
Validate Skill Manifest
Validates a complete skill directory: skill.yaml, guardrails.yaml, eval.yaml, README.md, examples/
Checks schema compliance and internal consistency.
"""

import sys
import yaml
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


def validate_skill_yaml(skill_dir: Path) -> List[str]:
    """Validate skill.yaml against schema."""
    errors = []
    skill_path = skill_dir / 'skill.yaml'

    if not skill_path.exists():
        errors.append(f"Missing skill.yaml in {skill_dir}")
        return errors

    skill = load_yaml(skill_path)

    # Required fields
    required_fields = [
        'schema_version', 'name', 'version', 'category',
        'description', 'author', 'steps'
    ]

    for field in required_fields:
        if field not in skill:
            errors.append(f"skill.yaml: Missing required field '{field}'")

    # Validate name format
    if 'name' in skill:
        name = skill['name']
        if not all(c.islower() or c.isdigit() or c == '-' for c in name):
            errors.append("skill.yaml: name must be kebab-case")

    # Validate version format
    if 'version' in skill:
        version = skill['version']
        parts = str(version).split('.')
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            errors.append("skill.yaml: version must be semantic version (e.g., 1.0.0)")

    # Validate category
    valid_categories = [
        'database', 'frontend', 'backend', 'infrastructure',
        'testing', 'security', 'devops', 'data'
    ]
    if 'category' in skill and skill['category'] not in valid_categories:
        errors.append(f"skill.yaml: category must be one of {valid_categories}")

    # Validate steps
    if 'steps' in skill:
        if not isinstance(skill['steps'], list):
            errors.append("skill.yaml: steps must be a list")
        elif len(skill['steps']) == 0:
            errors.append("skill.yaml: steps must contain at least one step")
        else:
            for idx, step in enumerate(skill['steps']):
                if not isinstance(step, dict):
                    errors.append(f"skill.yaml: steps[{idx}] must be an object")
                    continue

                # Required step fields
                step_required = ['step_id', 'description', 'action']
                for field in step_required:
                    if field not in step:
                        errors.append(f"skill.yaml: steps[{idx}] missing required field '{field}'")

                # Validate action
                valid_actions = ['analyze', 'generate', 'validate', 'review', 'execute', 'rollback']
                if 'action' in step and step['action'] not in valid_actions:
                    errors.append(f"skill.yaml: steps[{idx}] action must be one of {valid_actions}")

    return errors


def validate_guardrails_yaml(skill_dir: Path, skill_name: str) -> List[str]:
    """Validate guardrails.yaml against schema."""
    errors = []
    guardrails_path = skill_dir / 'guardrails.yaml'

    if not guardrails_path.exists():
        errors.append(f"Missing guardrails.yaml in {skill_dir}")
        return errors

    guardrails = load_yaml(guardrails_path)

    # Required fields
    required_fields = ['schema_version', 'skill_name', 'gates']
    for field in required_fields:
        if field not in guardrails:
            errors.append(f"guardrails.yaml: Missing required field '{field}'")

    # Validate skill_name matches
    if 'skill_name' in guardrails and guardrails['skill_name'] != skill_name:
        errors.append(f"guardrails.yaml: skill_name mismatch. Expected '{skill_name}', got '{guardrails['skill_name']}'")

    # Validate gates structure
    if 'gates' in guardrails:
        gates = guardrails['gates']
        if not isinstance(gates, dict):
            errors.append("guardrails.yaml: gates must be an object")
        else:
            valid_phases = ['pre_execution', 'during_execution', 'post_execution']
            for phase in valid_phases:
                if phase in gates:
                    if not isinstance(gates[phase], list):
                        errors.append(f"guardrails.yaml: gates.{phase} must be a list")
                    else:
                        for idx, gate in enumerate(gates[phase]):
                            if not isinstance(gate, dict):
                                errors.append(f"guardrails.yaml: gates.{phase}[{idx}] must be an object")
                                continue

                            gate_required = ['gate_id', 'description', 'required']
                            for field in gate_required:
                                if field not in gate:
                                    errors.append(f"guardrails.yaml: gates.{phase}[{idx}] missing '{field}'")

    return errors


def validate_eval_yaml(skill_dir: Path, skill_name: str) -> List[str]:
    """Validate eval.yaml against schema and benchmark evidence."""
    errors = []
    warnings = []
    eval_path = skill_dir / 'eval.yaml'

    if not eval_path.exists():
        errors.append(f"Missing eval.yaml in {skill_dir}")
        return errors

    eval_data = load_yaml(eval_path)

    # Required fields
    required_fields = ['schema_version', 'skill_name', 'benchmark_requirements']
    for field in required_fields:
        if field not in eval_data:
            errors.append(f"eval.yaml: Missing required field '{field}'")

    # Validate skill_name matches
    if 'skill_name' in eval_data and eval_data['skill_name'] != skill_name:
        errors.append(f"eval.yaml: skill_name mismatch. Expected '{skill_name}', got '{eval_data['skill_name']}'")

    # Validate benchmark_requirements
    if 'benchmark_requirements' in eval_data:
        reqs = eval_data['benchmark_requirements']
        if not isinstance(reqs, list):
            errors.append("eval.yaml: benchmark_requirements must be a list")
        elif len(reqs) == 0:
            errors.append("eval.yaml: benchmark_requirements must contain at least one requirement")
        else:
            valid_benchmarks = [
                'sql_accuracy', 'code_generation', 'reasoning_depth',
                'hallucination_rate', 'test_coverage', 'security_awareness'
            ]
            valid_operators = ['>=', '>', '<=', '<', '==']

            for idx, req in enumerate(reqs):
                if not isinstance(req, dict):
                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] must be an object")
                    continue

                req_required = ['benchmark_name', 'threshold', 'operator']
                for field in req_required:
                    if field not in req:
                        errors.append(f"eval.yaml: benchmark_requirements[{idx}] missing '{field}'")

                if 'benchmark_name' in req and req['benchmark_name'] not in valid_benchmarks:
                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] benchmark_name must be one of {valid_benchmarks}")

                if 'operator' in req and req['operator'] not in valid_operators:
                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] operator must be one of {valid_operators}")

                if 'threshold' in req:
                    threshold = req['threshold']
                    if not isinstance(threshold, (int, float)):
                        errors.append(f"eval.yaml: benchmark_requirements[{idx}] threshold must be a number")
                    elif threshold < 0.0 or threshold > 1.0:
                        errors.append(f"eval.yaml: benchmark_requirements[{idx}] threshold must be between 0.0 and 1.0")

                # Benchmark evidence enforcement
                if 'benchmark_name' in req and 'threshold' in req and 'operator' in req:
                    benchmark_name = req['benchmark_name']
                    threshold = req['threshold']
                    operator = req['operator']

                    # Load baseline from benchmark/baselines/
                    baseline_path = skill_dir.parent.parent / 'benchmark' / 'baselines' / f'anthropic_claude-opus-4-6_{benchmark_name}_baseline.json'

                    if baseline_path.exists():
                        try:
                            import json
                            with open(baseline_path, 'r') as f:
                                baseline_data = json.load(f)

                            baseline_score = baseline_data.get('baseline_score')

                            if baseline_score is not None:
                                # Compare baseline to threshold
                                if operator == '>=' and baseline_score < threshold:
                                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] baseline score {baseline_score} is below required threshold {threshold}")
                                elif operator == '>' and baseline_score <= threshold:
                                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] baseline score {baseline_score} is below required threshold {threshold}")
                                elif operator == '<=' and baseline_score > threshold:
                                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] baseline score {baseline_score} is above required threshold {threshold}")
                                elif operator == '<' and baseline_score >= threshold:
                                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] baseline score {baseline_score} is above required threshold {threshold}")
                                elif operator == '==' and baseline_score != threshold:
                                    errors.append(f"eval.yaml: benchmark_requirements[{idx}] baseline score {baseline_score} does not equal required threshold {threshold}")
                        except Exception as e:
                            print(f"WARNING: Failed to load baseline {baseline_path}: {e}")
                    else:
                        # Missing baseline is a warning, not error (forward compatibility)
                        print(f"WARNING: Baseline file not found: {baseline_path}")

    return errors


def validate_readme(skill_dir: Path) -> List[str]:
    """Validate README.md exists and has content."""
    errors = []
    readme_path = skill_dir / 'README.md'

    if not readme_path.exists():
        errors.append(f"Missing README.md in {skill_dir}")
        return errors

    try:
        content = readme_path.read_text(encoding='utf-8')
        if len(content.strip()) < 100:
            errors.append("README.md: Content too short (minimum 100 characters)")
    except Exception as e:
        errors.append(f"README.md: Failed to read file: {e}")

    return errors


def validate_examples(skill_dir: Path) -> List[str]:
    """Validate examples directory exists and has content."""
    errors = []
    examples_dir = skill_dir / 'examples'

    if not examples_dir.exists():
        errors.append(f"Missing examples/ directory in {skill_dir}")
        return errors

    if not examples_dir.is_dir():
        errors.append(f"examples/ is not a directory in {skill_dir}")
        return errors

    example_files = list(examples_dir.glob('*.md'))
    if len(example_files) == 0:
        errors.append(f"examples/ directory is empty in {skill_dir}")

    return errors


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description='Validate skill manifest')
    parser.add_argument('skill_dir', type=str, help='Path to skill directory (e.g., skills/safe_db_migration)')
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()

    if not skill_dir.exists():
        print(f"ERROR: Skill directory not found: {skill_dir}")
        sys.exit(1)

    if not skill_dir.is_dir():
        print(f"ERROR: Not a directory: {skill_dir}")
        sys.exit(1)

    print(f"Validating skill manifest: {skill_dir}")

    # Extract skill name from directory (convert snake_case to kebab-case)
    skill_name = skill_dir.name.replace('_', '-')

    # Run validations
    all_errors = []

    print("  Checking skill.yaml...")
    all_errors.extend(validate_skill_yaml(skill_dir))

    print("  Checking guardrails.yaml...")
    all_errors.extend(validate_guardrails_yaml(skill_dir, skill_name))

    print("  Checking eval.yaml...")
    all_errors.extend(validate_eval_yaml(skill_dir, skill_name))

    print("  Checking README.md...")
    all_errors.extend(validate_readme(skill_dir))

    print("  Checking examples/...")
    all_errors.extend(validate_examples(skill_dir))

    # Report results
    if all_errors:
        print(f"\n[FAIL] Validation FAILED with {len(all_errors)} error(s):\n")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"\n[OK] Validation PASSED: {skill_name} manifest is valid")
        sys.exit(0)


if __name__ == '__main__':
    main()
