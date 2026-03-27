"""Tool registry for discovering and executing tools (repo-scoped)."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sop.tools.tool import Tool
from sop.tools.tool_error import ToolError, ToolNotFound


class ToolRegistry:
    """Registry for discovering and executing tools (repo-scoped)."""

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize registry with repo-root requirement.

        Args:
            repo_root: Path to repo root. If None, uses $SOP_REPO_ROOT env var.
                      Raises error if neither provided.

        Raises:
            ToolError: If repo_root not provided and not in environment
        """
        self._tools: Dict[str, Tool] = {}
        
        # Get repo_root from argument or environment
        if repo_root:
            self.repo_root = repo_root
        else:
            env_root = os.environ.get("SOP_REPO_ROOT", "").strip()
            if not env_root:
                raise ToolError(
                    "sop tools requires repo context. "
                    "Provide --repo-root or set $SOP_REPO_ROOT. "
                    "sop tools is repo-scoped and not available in installed packages."
                )
            self.repo_root = Path(env_root)

        # Verify repo_root exists
        if not self.repo_root.exists():
            raise ToolError(
                f"repo_root does not exist: {self.repo_root}. "
                "Provide --repo-root or set $SOP_REPO_ROOT to valid path."
            )

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register

        Raises:
            ToolError: If tool already registered
        """
        if tool.name in self._tools:
            raise ToolError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance

        Raises:
            ToolNotFound: If tool not found
        """
        if name not in self._tools:
            raise ToolNotFound(f"Tool not found: {name}")
        return self._tools[name]

    def list(self) -> List[Tool]:
        """List all registered tools.

        Returns:
            List of Tool instances
        """
        return list(self._tools.values())

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute tool by name.

        Args:
            name: Tool name
            **kwargs: Input parameters

        Returns:
            Dict with 'success', 'result' or 'error' keys
        """
        try:
            tool = self.get(name)
            tool.validate_input(**kwargs)
            result = tool.execute(**kwargs)
            return {"success": True, "result": result}
        except ToolError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
