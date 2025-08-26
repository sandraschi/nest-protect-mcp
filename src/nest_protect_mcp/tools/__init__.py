"""Nest Protect MCP Tools.

This module contains all the tools available in the Nest Protect MCP server.
"""

from typing import Dict, Type
from fastmcp.tools import MCPTool, ToolRegistry

# Import all tools to register them
from . import (
    device_status,
    device_control,
    system_status,
    help_tool,
    auth_tools,
    config_tools,
    event_tools
)

# Re-export the tool registry
tool_registry = ToolRegistry()

# Re-export the tool decorator
tool = tool_registry.tool

# Re-export commonly used types
__all__ = [
    'MCPTool',
    'ToolRegistry',
    'tool',
    'tool_registry',
]
