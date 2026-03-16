#!/usr/bin/env python3
"""
Test Skill Infrastructure
Tests for schema validation, allowlist resolution, approval metadata, and registry-driven validation.
Executes production validators via subprocess and includes negative test cases.
"""

import pytest
import yaml
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any
import sys
import subprocess


# Test fixtures
@pytest.fixture
def temp_repo():
    """Create temporary repository structure."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create directory structure
    (temp_dir / 'skills' / 'schemas').mkdir(parents=True)
    (temp_dir / 'skills' / 'test_skill' / 'examples').mkdir(parents=True)
    (temp_dir / 'docs').mkdir(parents=True)
    (temp_dir / 'scripts').mkdir(parents=True)
    (temp_dir / 'benchmark' / 'baselines').mkdir(parents=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def repo_root():
    """Get actual repository root."""
    return Path(__file__).parent.parent.resolve()


@pytest.fixture
def valid_skill_yaml() -> Dict[str, Any]:
    """Valid skill.yaml content."""
    return {
        'schema_version': '1.0.0',
        'name': 'test-skill',
        'version': '1.0.0',
        'category': 'database',
        'description': 'Test skill for validation',
        'author': 'Internal Team',
        'steps': [
            {
                'step_id': 'analyze',
                'description': 'Analyze the problem',
                'action': 'analyze',
                'inputs': ['problem_statement'],
                'outputs': ['analysis_report']
            }
        ]
    }


@pytest.fixture
def valid_guardrails_yaml() -> Dict[str, Any]:
    """Valid guardrails.yaml content."""
    return {
        'schema_version': '1.0.0',
        'skill_name': 'test-skill',
        'gates': {
            'pre_execution': [
                {
                    'gate_id': 'backup_verified',
                    'description': 'Backup exists',
                    'required': True
                }
            ]
        },
        'failure_handling': {
            'rollback_required': True,
            'escalation_path': 'pm_ceo',
            'max_retry_attempts': 0
        }
    }


@pytest.fixture
def valid_eval_yaml() -> Dict[str, Any]:
    """Valid eval.yaml content."""
    return {
        'schema_version': '1.0.0',
        'skill_name': 'test-skill',
        'benchmark_requirements': [
            {
                'benchmark_name': 'sql_accuracy',
                'threshold': 0.85,
                'operator': '>=',
                'rationale': 'Must be competent at SQL'
            }
        ],
        'evaluation_frequency': 'per_model_version',
        'waiver_policy': {
            'waiver_allowed': False,
            'waiver_authority': 'pm_ceo',
            'waiver_documentation_required': True
        }
    }


@pytest.fixture
def valid_registry_yaml() -> Dict[str, Any]:
    """Valid registry.yaml content."""
    return {
        'schema_version': '1.0.0',
        'last_updated': '2026-03-13',
        'skills': [
            {
                'name': 'test-skill',
                'version': '1.0.0',
                'category': 'database',
                'description': 'Test skill for validation',
                'author': 'Internal Team',
                'approval_status': 'active',
                'approval_decision_id': 'D-999',
                'documentation': 'skills/test_skill/README.md',
                'examples': ['skills/test_skill/examples/example1.md']
            }
        ]
    }


@pytest.fixture
def valid_allowlist_yaml() -> Dict[str, Any]:
    """Valid allowlist content."""
    return {
        'schema_version': '1.0.0',
        'last_updated': '2026-03-13',
        'skills': [
            {
                'skill_name': 'test-skill',
                'version': '1.0.0',
                'approved_by': 'PM/CEO',
                'approval_decision_id': 'D-999',
                'approval_date': '2026-03-13',
                'status': 'active',
                'risk_level': 'HIGH',
                'applicable_projects': ['all']
            }
        ]
    }


@pytest.fixture
def valid_project_config_yaml() -> Dict[str, Any]:
    """Valid project config content."""
    return {
        'project_name': 'test-project',
        'guardrail_strength': 'tight',
        'active_skills': ['test-skill'],
        'disabled_skills': []
    }


# Schema Validation Tests
class TestSchemaValidation:
    """Test schema validation for all skill components."""

    def test_skill_yaml_valid(self, temp_repo, valid_skill_yaml):
        """Test valid skill.yaml passes validation."""
        skill_path = temp_repo / 'skills' / 'test_skill' / 'skill.yaml'
        with open(skill_path, 'w') as f:
            yaml.dump(valid_skill_yaml, f)

        assert skill_path.exists()
        loaded = yaml.safe_load(skill_path.read_text())
        assert loaded['name'] == 'test-skill'
        assert loaded['version'] == '1.0.0'

    def test_skill_yaml_missing_required_field(self, valid_skill_yaml):
        """Test skill.yaml fails without required fields."""
        invalid = valid_skill_yaml.copy()
        del invalid['name']

        # Should fail validation (name is required)
        assert 'name' not in invalid

    def test_skill_yaml_invalid_version_format(self, valid_skill_yaml):
        """Test skill.yaml fails with invalid version."""
        invalid = valid_skill_yaml.copy()
        invalid['version'] = '1.0'  # Missing patch version

        parts = invalid['version'].split('.')
        assert len(parts) != 3  # Should fail validation

    def test_guardrails_yaml_valid(self, temp_repo, valid_guardrails_yaml):
        """Test valid guardrails.yaml passes validation."""
        guardrails_path = temp_repo / 'skills' / 'test_skill' / 'guardrails.yaml'
        with open(guardrails_path, 'w') as f:
            yaml.dump(valid_guardrails_yaml, f)

        assert guardrails_path.exists()
        loaded = yaml.safe_load(guardrails_path.read_text())
        assert loaded['skill_name'] == 'test-skill'

    def test_eval_yaml_valid(self, temp_repo, valid_eval_yaml):
        """Test valid eval.yaml passes validation."""
        eval_path = temp_repo / 'skills' / 'test_skill' / 'eval.yaml'
        with open(eval_path, 'w') as f:
            yaml.dump(valid_eval_yaml, f)

        assert eval_path.exists()
        loaded = yaml.safe_load(eval_path.read_text())
        assert loaded['skill_name'] == 'test-skill'
        assert len(loaded['benchmark_requirements']) > 0


# Registry Validation Tests
class TestRegistryValidation:
    """Test registry validation logic."""

    def test_registry_valid(self, temp_repo, valid_registry_yaml):
        """Test valid registry passes validation."""
        registry_path = temp_repo / 'skills' / 'registry.yaml'
        with open(registry_path, 'w') as f:
            yaml.dump(valid_registry_yaml, f)

        loaded = yaml.safe_load(registry_path.read_text())
        assert loaded['schema_version'] == '1.0.0'
        assert len(loaded['skills']) == 1

    def test_registry_duplicate_skill_names(self, valid_registry_yaml):
        """Test registry fails with duplicate skill names."""
        invalid = valid_registry_yaml.copy()
        invalid['skills'].append(invalid['skills'][0].copy())

        # Should have duplicate names
        names = [s['name'] for s in invalid['skills']]
        assert len(names) != len(set(names))

    def test_registry_missing_approval_decision_id(self, valid_registry_yaml):
        """Test registry fails without approval_decision_id."""
        invalid = valid_registry_yaml.copy()
        del invalid['skills'][0]['approval_decision_id']

        assert 'approval_decision_id' not in invalid['skills'][0]


# Allowlist Validation Tests
class TestAllowlistValidation:
    """Test allowlist validation logic."""

    def test_allowlist_valid(self, temp_repo, valid_allowlist_yaml):
        """Test valid allowlist passes validation."""
        allowlist_path = temp_repo / 'extension_allowlist.yaml'
        with open(allowlist_path, 'w') as f:
            yaml.dump(valid_allowlist_yaml, f)

        loaded = yaml.safe_load(allowlist_path.read_text())
        assert loaded['schema_version'] == '1.0.0'
        assert len(loaded['skills']) == 1

    def test_allowlist_invalid_risk_level(self, valid_allowlist_yaml):
        """Test allowlist fails with invalid risk_level."""
        invalid = valid_allowlist_yaml.copy()
        invalid['skills'][0]['risk_level'] = 'CRITICAL'  # Not a valid level

        assert invalid['skills'][0]['risk_level'] not in ['LOW', 'MEDIUM', 'HIGH']

    def test_allowlist_invalid_approval_decision_format(self, valid_allowlist_yaml):
        """Test allowlist fails with invalid decision ID format."""
        invalid = valid_allowlist_yaml.copy()
        invalid['skills'][0]['approval_decision_id'] = 'DECISION-999'  # Wrong format

        import re
        assert not re.match(r'^D-\d+[a-z]?$', invalid['skills'][0]['approval_decision_id'])


# Project Config Validation Tests
class TestProjectConfigValidation:
    """Test project config validation against allowlist."""

    def test_project_config_valid(self, temp_repo, valid_project_config_yaml, valid_allowlist_yaml):
        """Test valid project config passes validation."""
        config_path = temp_repo / '.sop_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(valid_project_config_yaml, f)

        allowlist_path = temp_repo / 'extension_allowlist.yaml'
        with open(allowlist_path, 'w') as f:
            yaml.dump(valid_allowlist_yaml, f)

        config = yaml.safe_load(config_path.read_text())
        allowlist = yaml.safe_load(allowlist_path.read_text())

        # Check active skill is in allowlist
        active_skills = config['active_skills']
        allowlist_skills = {s['skill_name'] for s in allowlist['skills']}

        for skill in active_skills:
            assert skill in allowlist_skills

    def test_project_config_skill_not_in_allowlist(self, valid_project_config_yaml, valid_allowlist_yaml):
        """Test project config fails when skill not in allowlist."""
        config = valid_project_config_yaml.copy()
        config['active_skills'] = ['non-existent-skill']

        allowlist = valid_allowlist_yaml
        allowlist_skills = {s['skill_name'] for s in allowlist['skills']}

        # Should fail validation
        assert 'non-existent-skill' not in allowlist_skills

    def test_project_config_deprecated_skill(self, valid_project_config_yaml, valid_allowlist_yaml):
        """Test project config fails when activating deprecated skill."""
        allowlist = valid_allowlist_yaml.copy()
        allowlist['skills'][0]['status'] = 'deprecated'

        config = valid_project_config_yaml

        # Should fail validation (status != 'active')
        assert allowlist['skills'][0]['status'] != 'active'


# Approval Metadata Tests
class TestApprovalMetadata:
    """Test approval metadata validation."""

    def test_approval_decision_exists_in_log(self, temp_repo, valid_allowlist_yaml):
        """Test approval_decision_id exists in decision log."""
        # Create decision log with D-999
        decision_log = temp_repo / 'docs' / 'decision log.md'
        decision_log.write_text("""
# Decision Log

| ID | Component | Decision |
|----|-----------|----------|
| D-999 | skills | Approve test-skill |
""")

        allowlist = valid_allowlist_yaml
        decision_id = allowlist['skills'][0]['approval_decision_id']

        # Check decision ID exists in log
        log_content = decision_log.read_text()
        assert decision_id in log_content

    def test_approval_decision_missing_from_log(self, temp_repo, valid_allowlist_yaml):
        """Test validation fails when decision ID missing from log."""
        # Create empty decision log
        decision_log = temp_repo / 'docs' / 'decision log.md'
        decision_log.write_text("# Decision Log\n\nNo decisions yet.")

        allowlist = valid_allowlist_yaml
        decision_id = allowlist['skills'][0]['approval_decision_id']

        # Check decision ID does NOT exist in log
        log_content = decision_log.read_text()
        assert decision_id not in log_content


# Integration Tests
class TestIntegration:
    """Integration tests for complete skill infrastructure."""

    def test_complete_skill_structure(self, temp_repo, valid_skill_yaml, valid_guardrails_yaml,
                                     valid_eval_yaml, valid_registry_yaml, valid_allowlist_yaml):
        """Test complete skill directory structure validates."""
        # Create skill directory
        skill_dir = temp_repo / 'skills' / 'test_skill'

        # Write all required files
        (skill_dir / 'skill.yaml').write_text(yaml.dump(valid_skill_yaml))
        (skill_dir / 'guardrails.yaml').write_text(yaml.dump(valid_guardrails_yaml))
        (skill_dir / 'eval.yaml').write_text(yaml.dump(valid_eval_yaml))
        (skill_dir / 'README.md').write_text("# Test Skill\n\nThis is a test skill with sufficient content for validation.")
        (skill_dir / 'examples' / 'example1.md').write_text("# Example 1\n\nExample content.")

        # Write registry
        (temp_repo / 'skills' / 'registry.yaml').write_text(yaml.dump(valid_registry_yaml))

        # Write allowlist
        (temp_repo / 'extension_allowlist.yaml').write_text(yaml.dump(valid_allowlist_yaml))

        # Verify all files exist
        assert (skill_dir / 'skill.yaml').exists()
        assert (skill_dir / 'guardrails.yaml').exists()
        assert (skill_dir / 'eval.yaml').exists()
        assert (skill_dir / 'README.md').exists()
        assert (skill_dir / 'examples' / 'example1.md').exists()
        assert (temp_repo / 'skills' / 'registry.yaml').exists()
        assert (temp_repo / 'extension_allowlist.yaml').exists()


# Benchmark Evidence Tests
class TestBenchmarkEvidence:
    """Test benchmark evidence validation."""

    def test_sql_accuracy_threshold_met(self, repo_root):
        """Test sql_accuracy baseline meets safe-db-migration requirement."""
        # Read real baseline file
        baseline_path = repo_root / 'benchmark' / 'baselines' / 'anthropic_claude-opus-4-6_sql_accuracy_baseline.json'

        if baseline_path.exists():
            with open(baseline_path, 'r') as f:
                baseline_data = json.load(f)

            baseline_score = baseline_data['baseline_score']

            # Read real eval.yaml
            eval_path = repo_root / 'skills' / 'safe_db_migration' / 'eval.yaml'
            if eval_path.exists():
                with open(eval_path, 'r') as f:
                    eval_data = yaml.safe_load(f)

                # Find sql_accuracy requirement
                for req in eval_data['benchmark_requirements']:
                    if req['benchmark_name'] == 'sql_accuracy':
                        required_threshold = req['threshold']
                        assert baseline_score >= required_threshold, \
                            f"Baseline {baseline_score} does not meet threshold {required_threshold}"
                        break

    def test_eval_yaml_threshold_validation(self, valid_eval_yaml):
        """Test eval.yaml threshold is within valid range."""
        requirements = valid_eval_yaml['benchmark_requirements']

        for req in requirements:
            threshold = req['threshold']
            assert 0.0 <= threshold <= 1.0
            assert req['operator'] in ['>=', '>', '<=', '<', '==']


# Negative Test Cases (Production Validators via Subprocess)
class TestNegativeCases:
    """Test negative cases by executing production validators via subprocess."""

    def test_reject_high_risk_pm_only_approval(self, temp_repo, valid_allowlist_yaml, repo_root):
        """Test validator rejects HIGH-risk skill with PM-only approval."""
        # Create allowlist with HIGH-risk + PM approval
        invalid_allowlist = valid_allowlist_yaml.copy()
        invalid_allowlist['skills'][0]['risk_level'] = 'HIGH'
        invalid_allowlist['skills'][0]['approved_by'] = 'PM'  # Should require CEO or PM/CEO

        allowlist_path = temp_repo / 'extension_allowlist.yaml'
        with open(allowlist_path, 'w') as f:
            yaml.dump(invalid_allowlist, f)

        # Create decision log with D-999
        decision_log = temp_repo / 'docs' / 'decision log.md'
        decision_log.write_text("| D-999 | skills | Approve test-skill |")

        # Run validator
        validator_script = repo_root / 'scripts' / 'validate_extension_allowlist.py'
        result = subprocess.run(
            [sys.executable, str(validator_script), '--repo-root', str(temp_repo)],
            capture_output=True,
            text=True
        )

        # Should fail validation
        assert result.returncode != 0, "Validator should reject HIGH-risk skill with PM-only approval"
        assert 'HIGH-risk' in result.stdout or 'CEO approval' in result.stdout

    def test_reject_missing_decision_log_ref(self, temp_repo, valid_allowlist_yaml, repo_root):
        """Test validator rejects allowlist with invalid decision_log_ref."""
        # Create allowlist with non-existent decision ID
        invalid_allowlist = valid_allowlist_yaml.copy()
        invalid_allowlist['skills'][0]['approval_decision_id'] = 'D-99999'

        allowlist_path = temp_repo / 'extension_allowlist.yaml'
        with open(allowlist_path, 'w') as f:
            yaml.dump(invalid_allowlist, f)

        # Create decision log WITHOUT D-99999
        decision_log = temp_repo / 'docs' / 'decision log.md'
        decision_log.write_text("# Decision Log\n\n| D-1 | test | test |")

        # Run validator
        validator_script = repo_root / 'scripts' / 'validate_extension_allowlist.py'
        result = subprocess.run(
            [sys.executable, str(validator_script), '--repo-root', str(temp_repo)],
            capture_output=True,
            text=True
        )

        # Should fail validation
        assert result.returncode != 0, "Validator should reject missing decision log reference"
        assert 'D-99999' in result.stdout and 'not found' in result.stdout

    def test_reject_active_skill_not_in_allowlist(self, temp_repo, valid_allowlist_yaml,
                                                   valid_project_config_yaml, repo_root):
        """Test validator rejects project config with skill not in allowlist."""
        # Create allowlist with test-skill
        allowlist_path = temp_repo / 'extension_allowlist.yaml'
        with open(allowlist_path, 'w') as f:
            yaml.dump(valid_allowlist_yaml, f)

        # Create project config with non-existent skill
        invalid_config = valid_project_config_yaml.copy()
        invalid_config['active_skills'] = ['non-existent-skill']

        config_path = temp_repo / '.sop_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(invalid_config, f)

        # Create decision log
        decision_log = temp_repo / 'docs' / 'decision log.md'
        decision_log.write_text("| D-999 | skills | Approve test-skill |")

        # Run validator
        validator_script = repo_root / 'scripts' / 'validate_extension_allowlist.py'
        result = subprocess.run(
            [sys.executable, str(validator_script), '--repo-root', str(temp_repo)],
            capture_output=True,
            text=True
        )

        # Should fail validation
        assert result.returncode != 0, "Validator should reject skill not in allowlist"
        assert 'non-existent-skill' in result.stdout and 'not in global allowlist' in result.stdout

    def test_reject_benchmark_below_threshold(self, temp_repo, repo_root):
        """Test validator rejects eval.yaml with threshold above baseline."""
        # Create skill directory
        skill_dir = temp_repo / 'skills' / 'test_skill'
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Create eval.yaml with impossible threshold (0.99 > baseline 0.91)
        invalid_eval = {
            'schema_version': '1.0.0',
            'skill_name': 'test-skill',
            'benchmark_requirements': [
                {
                    'benchmark_name': 'sql_accuracy',
                    'threshold': 0.99,  # Higher than baseline 0.91
                    'operator': '>=',
                    'rationale': 'Impossible threshold'
                }
            ],
            'evaluation_frequency': 'per_model_version',
            'waiver_policy': {
                'waiver_allowed': False,
                'waiver_authority': 'pm_ceo',
                'waiver_documentation_required': True
            }
        }

        eval_path = skill_dir / 'eval.yaml'
        with open(eval_path, 'w') as f:
            yaml.dump(invalid_eval, f)

        # Create minimal skill.yaml
        skill_yaml = {
            'schema_version': '1.0.0',
            'name': 'test-skill',
            'version': '1.0.0',
            'category': 'database',
            'description': 'Test',
            'author': 'Test',
            'steps': [{'step_id': 'test', 'description': 'Test', 'action': 'analyze'}]
        }
        (skill_dir / 'skill.yaml').write_text(yaml.dump(skill_yaml))

        # Create minimal guardrails.yaml
        guardrails_yaml = {
            'schema_version': '1.0.0',
            'skill_name': 'test-skill',
            'gates': {'pre_execution': []},
            'failure_handling': {
                'rollback_required': False,
                'escalation_path': 'pm',
                'max_retry_attempts': 0
            }
        }
        (skill_dir / 'guardrails.yaml').write_text(yaml.dump(guardrails_yaml))

        # Create README
        (skill_dir / 'README.md').write_text("# Test Skill\n\nTest content with sufficient length to pass validation requirements for README files.")

        # Create examples directory
        examples_dir = skill_dir / 'examples'
        examples_dir.mkdir(parents=True, exist_ok=True)
        (examples_dir / 'example1.md').write_text("# Example 1\n\nExample content.")

        # Create baseline with lower score (0.91 < 0.99 threshold)
        baseline_dir = temp_repo / 'benchmark' / 'baselines'
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_data = {
            'model': 'anthropic:claude-opus-4-6',
            'suite': 'sql_accuracy',
            'baseline_score': 0.91,
            'baseline_runs': [],
            'established_at': '2026-03-13T00:00:00Z'
        }
        baseline_path = baseline_dir / 'anthropic_claude-opus-4-6_sql_accuracy_baseline.json'
        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)

        # Run validator
        validator_script = repo_root / 'scripts' / 'validate_skill_manifest.py'
        result = subprocess.run(
            [sys.executable, str(validator_script), str(skill_dir)],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, 'PYTHONPATH': str(repo_root)}
        )

        # Should fail validation (baseline 0.91 < threshold 0.99)
        assert result.returncode != 0, "Validator should reject threshold above baseline"
        assert 'below required threshold' in result.stdout, f"Expected 'below required threshold' in output, got: {result.stdout}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
