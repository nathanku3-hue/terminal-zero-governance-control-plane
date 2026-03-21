"""
Unit tests for ValidatorDescriptor.
"""

import json
import pytest
from sop.descriptors import ValidatorDescriptor


class TestValidatorDescriptor:
    """Test ValidatorDescriptor class."""
    
    @pytest.fixture
    def sample_descriptor_data(self):
        """Provide sample descriptor data for tests."""
        return {
            "name": "validate_closure_packet",
            "description": "Validate closure packet structure and content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "packet": {"type": "object"}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "valid": {"type": "boolean"},
                    "errors": {"type": "array"}
                }
            },
            "declared_capabilities": ["read_artifacts", "validate_schema"]
        }
    
    def test_create_descriptor(self, sample_descriptor_data):
        """Test creating a descriptor."""
        desc = ValidatorDescriptor(**sample_descriptor_data)
        assert desc.name == "validate_closure_packet"
        assert desc.description == "Validate closure packet structure and content"
        assert len(desc.declared_capabilities) == 2
    
    def test_to_dict(self, sample_descriptor_data):
        """Test serializing to dictionary."""
        desc = ValidatorDescriptor(**sample_descriptor_data)
        d = desc.to_dict()
        assert d["name"] == "validate_closure_packet"
        assert d["description"] == "Validate closure packet structure and content"
        assert d["declared_capabilities"] == ["read_artifacts", "validate_schema"]
        assert "input_schema" in d
        assert "output_schema" in d
    
    def test_to_json(self, sample_descriptor_data):
        """Test serializing to JSON."""
        desc = ValidatorDescriptor(**sample_descriptor_data)
        json_str = desc.to_json()
        assert isinstance(json_str, str)
        assert "validate_closure_packet" in json_str
        assert "read_artifacts" in json_str
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "validate_closure_packet"
    
    def test_from_dict(self, sample_descriptor_data):
        """Test deserializing from dictionary."""
        desc = ValidatorDescriptor.from_dict(sample_descriptor_data)
        assert desc.name == "validate_closure_packet"
        assert desc.description == "Validate closure packet structure and content"
        assert desc.declared_capabilities == ["read_artifacts", "validate_schema"]
    
    def test_from_json(self, sample_descriptor_data):
        """Test deserializing from JSON."""
        json_str = json.dumps(sample_descriptor_data)
        desc = ValidatorDescriptor.from_json(json_str)
        assert desc.name == "validate_closure_packet"
        assert desc.description == "Validate closure packet structure and content"
        assert desc.declared_capabilities == ["read_artifacts", "validate_schema"]
    
    def test_roundtrip_dict(self, sample_descriptor_data):
        """Test roundtrip serialization to/from dict."""
        desc1 = ValidatorDescriptor(**sample_descriptor_data)
        d = desc1.to_dict()
        desc2 = ValidatorDescriptor.from_dict(d)
        assert desc1.name == desc2.name
        assert desc1.description == desc2.description
        assert desc1.input_schema == desc2.input_schema
        assert desc1.output_schema == desc2.output_schema
        assert desc1.declared_capabilities == desc2.declared_capabilities
    
    def test_roundtrip_json(self, sample_descriptor_data):
        """Test roundtrip serialization to/from JSON."""
        desc1 = ValidatorDescriptor(**sample_descriptor_data)
        json_str = desc1.to_json()
        desc2 = ValidatorDescriptor.from_json(json_str)
        assert desc1.name == desc2.name
        assert desc1.description == desc2.description
        assert desc1.input_schema == desc2.input_schema
        assert desc1.output_schema == desc2.output_schema
        assert desc1.declared_capabilities == desc2.declared_capabilities
    
    def test_declared_capabilities_informational(self, sample_descriptor_data):
        """Test that declared_capabilities is informational only.
        
        This test confirms that declared_capabilities is stored as-is
        without any permission enforcement logic. Permission enforcement
        is handled by automation_boundary_registry.md.
        """
        desc = ValidatorDescriptor(**sample_descriptor_data)
        # Verify capabilities are stored exactly as provided
        assert desc.declared_capabilities == sample_descriptor_data["declared_capabilities"]
        # Verify they appear in serialization
        d = desc.to_dict()
        assert d["declared_capabilities"] == sample_descriptor_data["declared_capabilities"]
    
    def test_schema_validation_required_fields(self):
        """Test that all required fields are present."""
        # Missing name should raise TypeError
        with pytest.raises(TypeError):
            ValidatorDescriptor(
                description="test",
                input_schema={},
                output_schema={},
                declared_capabilities=[]
            )
    
    def test_minimal_descriptor(self):
        """Test creating a minimal valid descriptor."""
        desc = ValidatorDescriptor(
            name="test_validator",
            description="A test validator",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            declared_capabilities=[]
        )
        assert desc.name == "test_validator"
        assert desc.declared_capabilities == []
