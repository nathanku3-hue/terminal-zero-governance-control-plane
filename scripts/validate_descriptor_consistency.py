"""
Consistency validator for descriptor compliance.

This validator performs comprehensive schema validation on descriptors
to ensure they conform to the ValidatorDescriptor schema. It is
non-authoritative and NEVER blocks execution.

Authority: automation_boundary_registry.md remains canonical.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


class DescriptorConsistencyValidator:
    """Validate descriptor consistency without enforcing permissions."""
    
    def __init__(self, descriptor_path: str):
        """Initialize validator with descriptor path.
        
        Args:
            descriptor_path: Path to descriptor JSON file.
        """
        self.descriptor_path = Path(descriptor_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.schema = None
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Validate descriptor consistency.
        
        Returns:
            Tuple of (is_valid, errors, warnings).
            Note: This is read-only validation. Errors do NOT block execution.
        """
        self.errors = []
        self.warnings = []
        
        # Load schema first
        if not self._load_schema():
            return False, self.errors, self.warnings
        
        # Check file exists
        if not self._check_file_exists():
            return False, self.errors, self.warnings
        
        # Load JSON
        if not self._load_json():
            return False, self.errors, self.warnings
        
        # Validate against schema
        self._validate_against_schema()
        
        # Validate field content
        self._validate_field_content()
        
        # Return validation result
        # Note: Even with errors, this does NOT block execution
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _load_schema(self) -> bool:
        """Load schema from canonical location."""
        schema_path = Path(__file__).parent.parent / "src" / "sop" / "descriptors" / "schema.json"
        
        if not schema_path.exists():
            self.errors.append(f"Schema file not found at {schema_path}")
            return False
        
        try:
            with open(schema_path) as f:
                self.schema = json.load(f)
            return True
        except Exception as e:
            self.errors.append(f"Error loading schema: {e}")
            return False
    
    def _check_file_exists(self) -> bool:
        """Check descriptor file exists."""
        if not self.descriptor_path.exists():
            self.errors.append(f"Descriptor file not found: {self.descriptor_path}")
            return False
        return True
    
    def _load_json(self) -> bool:
        """Load and parse JSON file."""
        try:
            with open(self.descriptor_path) as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading file: {e}")
            return False
    
    def _validate_against_schema(self) -> None:
        """Validate descriptor against schema.json comprehensively."""
        if not self.schema:
            return
        
        # Get required fields from schema
        required_fields = set(self.schema.get("required", []))
        actual_fields = set(self.data.keys())
        
        missing = required_fields - actual_fields
        if missing:
            self.errors.append(f"Missing required fields: {missing}")
        
        extra = actual_fields - required_fields
        if extra:
            self.warnings.append(f"Extra fields (ignored): {extra}")
        
        # Validate properties against schema
        if "properties" in self.schema:
            for field_name, field_schema in self.schema["properties"].items():
                if field_name not in self.data:
                    continue
                
                # Check type
                expected_type = field_schema.get("type")
                if expected_type:
                    self._validate_field_type(field_name, self.data[field_name], expected_type, field_schema)
                
                # Check nested properties (for objects)
                if expected_type == "object" and "properties" in field_schema:
                    if isinstance(self.data[field_name], dict):
                        self._validate_nested_properties(field_name, self.data[field_name], field_schema["properties"])
                
                # Check array items
                if expected_type == "array" and "items" in field_schema:
                    if isinstance(self.data[field_name], list):
                        for i, item in enumerate(self.data[field_name]):
                            item_schema = field_schema["items"]
                            item_type = item_schema.get("type")
                            if item_type:
                                self._validate_field_type(f"{field_name}[{i}]", item, item_type, item_schema)
    
    def _validate_field_type(self, field_name: str, value: Any, expected_type: str, field_schema: dict) -> None:
        """Validate a field's type and constraints."""
        # Map JSON schema types to Python types
        type_map = {
            "string": str,
            "object": dict,
            "array": list,
            "boolean": bool,
            "number": (int, float),
            "integer": int
        }
        
        if expected_type in type_map:
            expected_python_type = type_map[expected_type]
            if not isinstance(value, expected_python_type):
                self.errors.append(
                    f"Field '{field_name}' must be {expected_type}, "
                    f"got {type(value).__name__}"
                )
                return
        
        # Validate string constraints
        if expected_type == "string" and isinstance(value, str):
            if not value.strip():
                self.errors.append(f"Field '{field_name}' cannot be empty")
            
            # Check minLength
            if "minLength" in field_schema and len(value) < field_schema["minLength"]:
                self.errors.append(f"Field '{field_name}' must be at least {field_schema['minLength']} characters")
            
            # Check maxLength
            if "maxLength" in field_schema and len(value) > field_schema["maxLength"]:
                self.errors.append(f"Field '{field_name}' must be at most {field_schema['maxLength']} characters")
            
            # Check enum
            if "enum" in field_schema and value not in field_schema["enum"]:
                self.errors.append(f"Field '{field_name}' must be one of {field_schema['enum']}, got {value}")
        
        # Validate number constraints
        if expected_type in ("number", "integer") and isinstance(value, (int, float)):
            if "minimum" in field_schema and value < field_schema["minimum"]:
                self.errors.append(f"Field '{field_name}' must be >= {field_schema['minimum']}")
            
            if "maximum" in field_schema and value > field_schema["maximum"]:
                self.errors.append(f"Field '{field_name}' must be <= {field_schema['maximum']}")
    
    def _validate_nested_properties(self, parent_name: str, obj: dict, properties: dict) -> None:
        """Validate nested object properties."""
        for prop_name, prop_schema in properties.items():
            if prop_name not in obj:
                continue
            
            prop_type = prop_schema.get("type")
            if prop_type:
                self._validate_field_type(f"{parent_name}.{prop_name}", obj[prop_name], prop_type, prop_schema)
    
    def _validate_field_content(self) -> None:
        """Validate field content consistency."""
        # Validate input_schema structure
        if "input_schema" in self.data and isinstance(self.data["input_schema"], dict):
            if "type" not in self.data["input_schema"]:
                self.warnings.append("input_schema should have 'type' field")
        
        # Validate output_schema structure
        if "output_schema" in self.data and isinstance(self.data["output_schema"], dict):
            if "type" not in self.data["output_schema"]:
                self.warnings.append("output_schema should have 'type' field")
        
        # Validate name format (alphanumeric + underscore)
        if "name" in self.data and isinstance(self.data["name"], str):
            if not all(c.isalnum() or c == "_" for c in self.data["name"]):
                self.warnings.append(f"name '{self.data['name']}' contains non-alphanumeric characters")
    
    def report(self) -> Dict:
        """Generate validation report.
        
        Returns:
            Dictionary with validation results.
            Note: This is informational only and does NOT block execution.
        """
        is_valid, errors, warnings = self.validate()
        
        return {
            "descriptor": str(self.descriptor_path),
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "note": "This is read-only consistency validation. Errors do NOT block execution. Authority: automation_boundary_registry.md"
        }


def validate_descriptor(descriptor_path: str) -> int:
    """Validate descriptor and print report.
    
    Args:
        descriptor_path: Path to descriptor JSON file.
    
    Returns:
        Exit code (always 0).
        Note: This validator is advisory only and NEVER blocks execution.
        All results are informational. Authority: automation_boundary_registry.md
    """
    validator = DescriptorConsistencyValidator(descriptor_path)
    report = validator.report()
    
    # Print report
    print(json.dumps(report, indent=2))
    
    # Always return 0 (never block execution)
    # This validator is advisory only
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_descriptor_consistency.py <descriptor_path>")
        sys.exit(0)  # Always exit 0 (never block)
    
    descriptor_path = sys.argv[1]
    exit_code = validate_descriptor(descriptor_path)
    
    # Always exit 0 (never block execution)
    sys.exit(exit_code)
