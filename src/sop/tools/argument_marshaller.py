"""Argument marshaller for converting kwargs to CLI arguments (formatting only)."""

from typing import Any, Dict, List

from sop.tools.tool_error import ToolError


class ArgumentMarshaller:
    """Convert kwargs to CLI arguments (formatting only, not validation).
    
    NOTE: This class handles CLI argument formatting only. Constraint validation
    (required, oneOf, enum) is performed by Tool.validate_input() before marshalling.
    """

    @staticmethod
    def marshal(kwargs: Dict[str, Any], input_schema: Dict[str, Any]) -> List[str]:
        """Convert kwargs to CLI argument list.

        Handles:
        - Boolean flags (--flag, not --flag true)
        - String values (--key value)
        - Unknown field rejection

        NOTE: Constraint validation (required, oneOf, enum) must be done by
        Tool.validate_input() before calling this method.

        Args:
            kwargs: Input parameters
            input_schema: JSON schema with properties

        Returns:
            List of CLI arguments

        Raises:
            ToolError: If field is unknown
        """
        args = []
        properties = input_schema.get("properties", {})

        for key, value in kwargs.items():
            if key not in properties:
                raise ToolError(f"Unknown field: {key}")

            prop_schema = properties[key]
            cli_key = f"--{key.replace('_', '-')}"

            # Handle boolean flags
            if prop_schema.get("type") == "boolean":
                if value:
                    args.append(cli_key)
                # Don't add anything if False (flag not present)
            else:
                # Handle string/number values
                args.append(cli_key)
                args.append(str(value))

        return args
