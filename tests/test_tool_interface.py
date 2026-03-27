"""Tests for tool abstraction interface."""

import os
import tempfile
from pathlib import Path

import pytest

from sop.tools import (
    ArgumentMarshaller,
    Tool,
    ToolError,
    ToolExecutionError,
    ToolNotFound,
    ToolRegistry,
)


class SimpleTool(Tool):
    """Simple test tool implementation."""

    def execute(self, **kwargs) -> dict:
        """Execute simple tool."""
        return {"valid": True, "output": "success", "exit_code": 0}


class TestToolInterface:
    """Test Tool base class."""

    def test_tool_creation(self):
        """Test tool creation with metadata."""
        tool = SimpleTool(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}, "required": []},
            output_schema={"type": "object", "properties": {}},
        )
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"

    def test_tool_validate_input_required_field(self):
        """Test input validation with required fields."""
        tool = SimpleTool(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "properties": {"field1": {"type": "string"}},
                "required": ["field1"],
            },
            output_schema={"type": "object"},
        )
        with pytest.raises(ToolError, match="Missing required field"):
            tool.validate_input()

    def test_tool_validate_input_unknown_field(self):
        """Test input validation with unknown fields."""
        tool = SimpleTool(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "properties": {"field1": {"type": "string"}},
                "required": [],
            },
            output_schema={"type": "object"},
        )
        with pytest.raises(ToolError, match="Unknown field"):
            tool.validate_input(unknown_field="value")

    def test_tool_validate_input_enum_constraint(self):
        """Test input validation with enum constraint."""
        tool = SimpleTool(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "properties": {"status": {"type": "string", "enum": ["active", "inactive"]}},
                "required": [],
            },
            output_schema={"type": "object"},
        )
        with pytest.raises(ToolError, match="must be one of"):
            tool.validate_input(status="invalid")

    def test_tool_execute(self):
        """Test tool execution."""
        tool = SimpleTool(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}, "required": []},
            output_schema={"type": "object"},
        )
        result = tool.execute()
        assert result["valid"] is True
        assert result["exit_code"] == 0


class TestToolRegistry:
    """Test ToolRegistry."""

    def test_registry_requires_repo_root(self):
        """Test that registry requires repo_root."""
        with pytest.raises(ToolError, match="does not exist"):
            ToolRegistry(repo_root=Path("/nonexistent/path/that/does/not/exist"))

    def test_registry_with_repo_root_path(self):
        """Test registry creation with repo_root path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(repo_root=Path(tmpdir))
            assert registry.repo_root == Path(tmpdir)

    def test_registry_with_env_var(self):
        """Test registry creation with SOP_REPO_ROOT env var."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_env = os.environ.get("SOP_REPO_ROOT")
            try:
                os.environ["SOP_REPO_ROOT"] = tmpdir
                registry = ToolRegistry()
                assert registry.repo_root == Path(tmpdir)
            finally:
                if old_env:
                    os.environ["SOP_REPO_ROOT"] = old_env
                elif "SOP_REPO_ROOT" in os.environ:
                    del os.environ["SOP_REPO_ROOT"]

    def test_registry_register_tool(self):
        """Test registering a tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(repo_root=Path(tmpdir))
            tool = SimpleTool(
                name="test_tool",
                description="Test tool",
                input_schema={"type": "object", "properties": {}, "required": []},
                output_schema={"type": "object"},
            )
            registry.register(tool)
            assert registry.get("test_tool") == tool

    def test_registry_register_duplicate_tool(self):
        """Test registering duplicate tool raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(repo_root=Path(tmpdir))
            tool = SimpleTool(
                name="test_tool",
                description="Test tool",
                input_schema={"type": "object", "properties": {}, "required": []},
                output_schema={"type": "object"},
            )
            registry.register(tool)
            with pytest.raises(ToolError, match="already registered"):
                registry.register(tool)

    def test_registry_get_nonexistent_tool(self):
        """Test getting nonexistent tool raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(repo_root=Path(tmpdir))
            with pytest.raises(ToolNotFound):
                registry.get("nonexistent")

    def test_registry_list_tools(self):
        """Test listing all tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(repo_root=Path(tmpdir))
            tool1 = SimpleTool(
                name="tool1",
                description="Tool 1",
                input_schema={"type": "object", "properties": {}, "required": []},
                output_schema={"type": "object"},
            )
            tool2 = SimpleTool(
                name="tool2",
                description="Tool 2",
                input_schema={"type": "object", "properties": {}, "required": []},
                output_schema={"type": "object"},
            )
            registry.register(tool1)
            registry.register(tool2)
            tools = registry.list()
            assert len(tools) == 2
            assert tool1 in tools
            assert tool2 in tools

    def test_registry_execute_tool(self):
        """Test executing a tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(repo_root=Path(tmpdir))
            tool = SimpleTool(
                name="test_tool",
                description="Test tool",
                input_schema={"type": "object", "properties": {}, "required": []},
                output_schema={"type": "object"},
            )
            registry.register(tool)
            result = registry.execute("test_tool")
            assert result["success"] is True
            assert result["result"]["valid"] is True

    def test_registry_execute_nonexistent_tool(self):
        """Test executing nonexistent tool returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ToolRegistry(repo_root=Path(tmpdir))
            result = registry.execute("nonexistent")
            assert result["success"] is False
            assert "error" in result


class TestArgumentMarshaller:
    """Test ArgumentMarshaller."""

    def test_marshal_string_argument(self):
        """Test marshalling string argument."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": [],
        }
        args = ArgumentMarshaller.marshal({"name": "test"}, schema)
        assert args == ["--name", "test"]

    def test_marshal_boolean_flag_true(self):
        """Test marshalling boolean flag (true)."""
        schema = {
            "type": "object",
            "properties": {"verbose": {"type": "boolean"}},
            "required": [],
        }
        args = ArgumentMarshaller.marshal({"verbose": True}, schema)
        assert args == ["--verbose"]

    def test_marshal_boolean_flag_false(self):
        """Test marshalling boolean flag (false)."""
        schema = {
            "type": "object",
            "properties": {"verbose": {"type": "boolean"}},
            "required": [],
        }
        args = ArgumentMarshaller.marshal({"verbose": False}, schema)
        assert args == []

    def test_marshal_multiple_arguments(self):
        """Test marshalling multiple arguments."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"},
                "verbose": {"type": "boolean"},
            },
            "required": [],
        }
        args = ArgumentMarshaller.marshal(
            {"name": "test", "count": 5, "verbose": True}, schema
        )
        assert "--name" in args
        assert "test" in args
        assert "--count" in args
        assert "5" in args
        assert "--verbose" in args

    def test_marshal_unknown_field(self):
        """Test marshalling unknown field raises error."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": [],
        }
        with pytest.raises(ToolError, match="Unknown field"):
            ArgumentMarshaller.marshal({"unknown": "value"}, schema)

    def test_marshal_underscore_to_hyphen(self):
        """Test marshalling converts underscores to hyphens."""
        schema = {
            "type": "object",
            "properties": {"my_field": {"type": "string"}},
            "required": [],
        }
        args = ArgumentMarshaller.marshal({"my_field": "value"}, schema)
        assert args == ["--my-field", "value"]
