"""ArchitectCalibrationTool wrapper for validate_architect_calibration validator."""

import json
from pathlib import Path

from sop.tools.validators.validator_tool import ValidatorTool
from sop.descriptors import ValidatorDescriptor


class ArchitectCalibrationTool(ValidatorTool):
    """Wrapper for validate_architect_calibration validator."""

    @staticmethod
    def create(repo_root: Path) -> ValidatorTool:
        """Factory method to create tool from descriptor.

        Args:
            repo_root: Path to repo root

        Returns:
            ValidatorTool instance for architect_calibration validator
        """
        descriptor_path = (
            repo_root / ".codex/skills/_shared/scripts/validate_architect_calibration.descriptor.json"
        )
        
        # Load descriptor from JSON file
        with open(descriptor_path, 'r') as f:
            descriptor_data = json.load(f)
        
        descriptor = ValidatorDescriptor.from_dict(descriptor_data)

        return ValidatorTool(
            validator_script_path=".codex/skills/_shared/scripts/validate_architect_calibration.py",
            descriptor=descriptor,
            repo_root=repo_root,
        )
