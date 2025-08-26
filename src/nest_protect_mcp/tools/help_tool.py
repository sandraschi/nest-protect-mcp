"""Help tools for Nest Protect MCP."""

import inspect
from typing import Dict, Any, List, Optional, Type, get_type_hints
from ..tools import tool, Tool

@tool(name="list_available_tools", description="List all available tools with their descriptions", parameters={}, examples=["list_available_tools()"])
async def list_available_tools() -> Dict[str, Any]:
    """List all available tools with their descriptions."""
    from ..server import app
    
    try:
        tools = []
        for tool_name, tool_func in app.state.tool_functions.items():
            if hasattr(tool_func, "tool_metadata"):
                metadata = tool_func.tool_metadata
                tools.append({
                    "name": tool_name,
                    "description": metadata.get("description", "No description"),
                    "parameters": metadata.get("parameters", {}),
                    "examples": metadata.get("examples", [])
                })
        
        return {
            "status": "success",
            "count": len(tools),
            "tools": sorted(tools, key=lambda x: x["name"])
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list tools: {str(e)}"}

@tool(name="get_tool_help", description="Get detailed help for a specific tool", parameters={"tool_name": {"type": "string", "description": "Name of the tool to get help for", "required": True}}, examples=["get_tool_help('list_devices')", "get_tool_help('hush_alarm')"])
async def get_tool_help(tool_name: str) -> Dict[str, Any]:
    """Get detailed help for a specific tool."""
    from ..server import app
    
    try:
        if tool_name not in app.state.tool_functions:
            return {"status": "error", "message": f"Tool '{tool_name}' not found"}
        
        tool_func = app.state.tool_functions[tool_name]
        if not hasattr(tool_func, "tool_metadata"):
            return {
                "status": "success",
                "tool": tool_name,
                "description": "No metadata available for this tool",
                "signature": str(inspect.signature(tool_func)),
                "docstring": tool_func.__doc__ or "No documentation available"
            }
        
        metadata = tool_func.tool_metadata
        signature = inspect.signature(tool_func)
        
        # Get parameter types from type hints
        type_hints = get_type_hints(tool_func)
        
        # Build parameter info
        parameters = {}
        for name, param in signature.parameters.items():
            if name == "self":
                continue
                
            param_info = {"type": str(type_hints.get(name, "any"))}
            
            # Add parameter metadata if available
            if "parameters" in metadata and name in metadata["parameters"]:
                param_info.update(metadata["parameters"][name])
            
            # Add default value if any
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            
            parameters[name] = param_info
        
        return {
            "status": "success",
            "tool": tool_name,
            "description": metadata.get("description", "No description"),
            "signature": str(signature),
            "parameters": parameters,
            "examples": metadata.get("examples", []),
            "docstring": tool_func.__doc__ or "No detailed documentation available"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get help for tool '{tool_name}': {str(e)}"}

@tool(name="search_tools", description="Search for tools by keyword or description", parameters={"query": {"type": "string", "description": "Search query", "required": True}, "search_in": {"type": "array", "items": {"type": "string", "enum": ["name", "description", "parameters"]}, "description": "Fields to search in", "default": ["name", "description"]}}, examples=["search_tools('auth')", "search_tools('device', ['name'])"])
async def search_tools(query: str, search_in: List[str] = ["name", "description"]) -> Dict[str, Any]:
    """Search for tools by keyword or description."""
    from ..server import app
    
    try:
        query = query.lower()
        results = []
        
        for tool_name, tool_func in app.state.tool_functions.items():
            if not hasattr(tool_func, "tool_metadata"):
                continue
                
            metadata = tool_func.tool_metadata
            match = False
            
            # Search in name
            if "name" in search_in and query in tool_name.lower():
                match = True
            
            # Search in description
            if not match and "description" in search_in and "description" in metadata:
                if query in metadata["description"].lower():
                    match = True
            
            # Search in parameter names and descriptions
            if not match and "parameters" in search_in and "parameters" in metadata:
                for param_name, param_info in metadata["parameters"].items():
                    if query in param_name.lower() or \
                       (isinstance(param_info, dict) and "description" in param_info and 
                        query in param_info["description"].lower()):
                        match = True
                        break
            
            if match:
                results.append({
                    "name": tool_name,
                    "description": metadata.get("description", "No description"),
                    "parameters": list(metadata.get("parameters", {}).keys())
                })
        
        return {
            "status": "success",
            "query": query,
            "search_in": search_in,
            "count": len(results),
            "results": sorted(results, key=lambda x: x["name"])
        }
    except Exception as e:
        return {"status": "error", "message": f"Search failed: {str(e)}"}
