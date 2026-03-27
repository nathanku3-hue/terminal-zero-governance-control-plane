"""Tool error classes for unified error handling."""


class ToolError(Exception):
    """Base tool error."""

    pass


class ToolNotFound(ToolError):
    """Tool not found in registry."""

    pass


class ToolExecutionError(ToolError):
    """Tool execution failed."""

    pass
