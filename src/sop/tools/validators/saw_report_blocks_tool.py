"""SawReportBlocksTool wrapper for validate_saw_report_blocks validator."""

import json
from pathlib import Path

from sop.tools.validators.validator_tool import ValidatorTool
from sop.descriptors import ValidatorDescriptor


class SawReportBlocksTool(ValidatorTool):
    """Wrapper for validate_saw_report_blocks validator."""

    @staticmethod
    def create(repo_root: Path) -> ValidatorTool:
        """Factory method to create tool from descriptor.

        Args:
            repo_root: Path to repo root

        Returns:
            ValidatorTool instance for saw_report_blocks validator
        """
        descriptor_path = (
            repo_root / ".codex/skills/_shared/scripts/validate_saw_report_blocks.descriptor.json"
        )
        
        # Load descriptor from JSON file
        with open(descriptor_path, 'r') as f:
            descriptor_data = json.load(f)
        
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)

        return ValidatorTool(
            validator_script_path=".codex/skills/_shared/scripts/validate_saw_report_blocks.py",
            descriptor=descriptor,
            repo_root=repo_root,
        )
