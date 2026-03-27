"""Tool base class for unified tool interface."""

from typing import Any, Dict


class Tool:
    """Base tool interface for all tools in the registry."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
    ):
        """Initialize tool with metadata and schemas.

        Args:
            name: Tool name (unique identifier)
            description: Tool description
            input_schema: JSON schema for input validation
            output_schema: JSON schema for output structure
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool with given inputs.

        Args:
            **kwargs: Input parameters matching input_schema

        Returns:
            Dict with 'valid', 'output', 'exit_code' keys

        Raises:
            NotImplementedError: Subclasses must implement
        """
        raise NotImplementedError

    def validate_input(self, **kwargs) -> bool:
        """Validate input against schema (required, properties, oneOf, enum).

        Args:
            **kwargs: Input parameters to validate

        Returns:
            True if valid

        Raises:
            ToolError: If validation fails
        """
        from sop.tools.tool_error import ToolError

        # Check required fields
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in kwargs:
                raise ToolError(f"Missing required field: {field}")

        properties = self.input_schema.get("properties", {})
        
        # Check for unknown fields
        for field in kwargs:
            if field not in properties:
                raise ToolError(f"Unknown field: {field}")

        # Validate each field against its schema
        for field, value in kwargs.items():
            prop_schema = properties[field]

            # Check enum constraint
            if "enum" in prop_schema and value not in prop_schema["enum"]:
                raise ToolError(
                    f"Field {field} must be one of {prop_schema['enum']}, got {value}"
                )

        # Check oneOf constraint (exactly one option must be satisfied)
        if "oneOf" in self.input_schema:
            one_of_options = self.input_schema["oneOf"]
            matching_options = []
            
            for option in one_of_options:
                # Each option is a schema with required fields
                required_for_option = option.get("required", [])
                provided_count = sum(1 for field in required_for_option if field in kwargs)
                
                # If all required fields for this option are provided, it matches
                if provided_count == len(required_for_option) and len(required_for_option) > 0:
                    matching_options.append(option)
            
            # Enforce: exactly one option must match
            if len(matching_options) == 0:
                raise ToolError(
                    f"oneOf constraint violated: must provide fields for exactly one option. "
                    f"Options: {[opt.get('required', []) for opt in one_of_options]}"
                )
            elif len(matching_options) > 1:
                raise ToolError(
                    f"oneOf constraint violated: cannot provide fields from multiple options. "
                    f"Matched options: {[opt.get('required', []) for opt in matching_options]}"
                )

        return True
