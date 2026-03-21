"""
Consistency tests for descriptor validation.

These tests verify that the consistency validator correctly identifies
descriptor compliance issues. The validator is read-only and non-authoritative.
"""

import json
import pytest
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scripts.validate_descriptor_consistency import DescriptorConsistencyValidator


class TestDescriptorConsistencyValidator:
    """Test descriptor consistency validation."""
    
    @pytest.fixture
    def valid_descriptor_data(self):
        """Provide valid descriptor data."""
        return {
            "name": "test_validator",
            "description": "Test validator",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "declared_capabilities": ["read", "write"]
        }
    
    @pytest.fixture
    def temp_descriptor_file(self, valid_descriptor_data):
        """Create temporary descriptor file."""
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_descriptor_data, f)
            temp_path = f.name
        yield temp_path
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    def test_valid_descriptor(self, temp_descriptor_file):
        """Test validation of valid descriptor."""
        validator = DescriptorConsistencyValidator(temp_descriptor_file)
        is_valid, errors, warnings = validator.validate()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_file(self):
        """Test validation of missing file."""
        validator = DescriptorConsistencyValidator("/nonexistent/path/descriptor.json")
        is_valid, errors, warnings = validator.validate()
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("not found" in e.lower() for e in errors)
    
    def test_invalid_json(self):
        """Test validation of invalid JSON."""
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json")
            temp_path = f.name
        
        try:
            validator = DescriptorConsistencyValidator(temp_path)
            is_valid, errors, warnings = validator.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any("json" in e.lower() for e in errors)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_missing_required_field(self, valid_descriptor_data):
        """Test validation with missing required field."""
        del valid_descriptor_data["name"]
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_descriptor_data, f)
            temp_path = f.name
        
        try:
            validator = DescriptorConsistencyValidator(temp_path)
            is_valid, errors, warnings = validator.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any("name" in e.lower() for e in errors)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_wrong_field_type_name(self, valid_descriptor_data):
        """Test validation with wrong type for name field."""
        valid_descriptor_data["name"] = 123  # Should be string
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_descriptor_data, f)
            temp_path = f.name
        
        try:
            validator = DescriptorConsistencyValidator(temp_path)
            is_valid, errors, warnings = validator.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any("name" in e.lower() and "string" in e.lower() for e in errors)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_wrong_field_type_input_schema(self, valid_descriptor_data):
        """Test validation with wrong type for input_schema field."""
        valid_descriptor_data["input_schema"] = "not an object"  # Should be dict
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_descriptor_data, f)
            temp_path = f.name
        
        try:
            validator = DescriptorConsistencyValidator(temp_path)
            is_valid, errors, warnings = validator.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any("input_schema" in e.lower() for e in errors)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_wrong_field_type_declared_capabilities(self, valid_descriptor_data):
        """Test validation with wrong type for declared_capabilities field."""
        valid_descriptor_data["declared_capabilities"] = "not an array"  # Should be list
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_descriptor_data, f)
            temp_path = f.name
        
        try:
            validator = DescriptorConsistencyValidator(temp_path)
            is_valid, errors, warnings = validator.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any("declared_capabilities" in e.lower() for e in errors)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_empty_name(self, valid_descriptor_data):
        """Test validation with empty name."""
        valid_descriptor_data["name"] = ""
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_descriptor_data, f)
            temp_path = f.name
        
        try:
            validator = DescriptorConsistencyValidator(temp_path)
            is_valid, errors, warnings = validator.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any("empty" in e.lower() for e in errors)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_extra_fields_warning(self, valid_descriptor_data):
        """Test validation with extra fields (should warn, not error)."""
        valid_descriptor_data["extra_field"] = "extra"
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_descriptor_data, f)
            temp_path = f.name
        
        try:
            validator = DescriptorConsistencyValidator(temp_path)
            is_valid, errors, warnings = validator.validate()
            
            # Should still be valid (extra fields are warnings, not errors)
            assert is_valid is True
            assert len(warnings) > 0
            assert any("extra" in w.lower() for w in warnings)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_report_format(self, temp_descriptor_file):
        """Test report format."""
        validator = DescriptorConsistencyValidator(temp_descriptor_file)
        report = validator.report()
        
        assert "descriptor" in report
        assert "valid" in report
        assert "errors" in report
        assert "warnings" in report
        assert "note" in report
        assert isinstance(report["errors"], list)
        assert isinstance(report["warnings"], list)
    
    def test_report_note_present(self, temp_descriptor_file):
        """Test that report includes note about non-authoritative nature."""
        validator = DescriptorConsistencyValidator(temp_descriptor_file)
        report = validator.report()
        
        assert "note" in report
        note_lower = report["note"].lower()
        assert "read-only" in note_lower or "informational" in note_lower
    
    def test_consistency_validator_is_non_authoritative(self, temp_descriptor_file):
        """Test that validator is explicitly non-authoritative.
        
        This test verifies that the validator does NOT enforce permissions
        and does NOT block execution.
        """
        validator = DescriptorConsistencyValidator(temp_descriptor_file)
        report = validator.report()
        
        # Verify report includes note about non-authoritative nature
        note_lower = report["note"].lower()
        assert "block execution" in note_lower
        
        # Verify automation_boundary_registry.md is mentioned as authority
        assert "automation_boundary_registry.md" in report["note"]
    
    def test_closure_packet_descriptor_consistency(self):
        """Test consistency of actual validate_closure_packet descriptor."""
        # Use repo-local path (quant_current_scope/.codex), not parent workspace
        descriptor_path = Path(__file__).parent.parent / ".codex" / "skills" / "_shared" / "scripts" / "validate_closure_packet.descriptor.json"

        if descriptor_path.exists():
            validator = DescriptorConsistencyValidator(str(descriptor_path))
            is_valid, errors, warnings = validator.validate()

            assert is_valid is True, f"Descriptor validation failed: {errors}"
            assert len(errors) == 0
    
    def test_validator_exit_code_informational(self, temp_descriptor_file):
        """Test that exit code is informational only.
        
        This test verifies that the validator returns an exit code
        but does NOT enforce it (i.e., it's for logging/reporting only).
        """
        from scripts.validate_descriptor_consistency import validate_descriptor
        
        # Valid descriptor should return 0
        exit_code = validate_descriptor(temp_descriptor_file)
        assert exit_code == 0
        
        # But this exit code is informational only and does NOT block execution
        # (This is verified by the fact that the function returns normally)
