"""
ValidatorDescriptor: Minimal descriptor for validators.

Fields:
- name: Validator name (unique identifier)
- description: Human-readable description
- input_schema: JSON Schema for input
- output_schema: JSON Schema for output
- declared_capabilities: Informational only (NOT permissions)

Authority: automation_boundary_registry.md is canonical for permissions.
"""

import json
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ValidatorDescriptor:
    """Minimal descriptor for validators.
    
    This descriptor provides a standardized format for declaring validator
    metadata across the SOP and skill layers. The declared_capabilities field
    is informational only and does not enforce permissions; permission
    enforcement is handled by automation_boundary_registry.md.
    """
    
    name: str
    description: str
    input_schema: Dict
    output_schema: Dict
    declared_capabilities: List[str]
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary.
        
        Returns:
            Dictionary representation of the descriptor.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "declared_capabilities": self.declared_capabilities
        }
    
    def to_json(self) -> str:
        """Serialize to JSON.
        
        Returns:
            JSON string representation of the descriptor.
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ValidatorDescriptor":
        """Deserialize from dictionary.
        
        Args:
            data: Dictionary containing descriptor fields.
            
        Returns:
            ValidatorDescriptor instance.
        """
        return cls(
            name=data["name"],
            description=data["description"],
            input_schema=data["input_schema"],
            output_schema=data["output_schema"],
            declared_capabilities=data["declared_capabilities"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "ValidatorDescriptor":
        """Deserialize from JSON.
        
        Args:
            json_str: JSON string representation of the descriptor.
            
        Returns:
            ValidatorDescriptor instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
