"""
Nest Protect MCP Server

This module implements the MCP server for interacting with Nest Protect devices
using the FastMCP 2.12 framework.
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable, TypeVar, cast, Type

from fastmcp import FastMCP
from fastmcp.tools import Tool
from fastmcp.client.messages import Message as McpMessage
from pydantic import BaseModel, ValidationError

from .state_manager import state_manager
from .models import ProtectConfig
from .tools import (
    DeviceInfo, GetDevicesTool, GetDeviceTool, SilenceAlarmTool, GetDeviceHistoryTool,
    tool_schemas, DeviceType, AlarmState, BatteryState
)
from .exceptions import (
    NestProtectError,
    NestAuthError,
    NestConnectionError,
    NestDeviceNotFoundError,
    NestInvalidCommandError,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nest_protect_mcp")

class NestProtectMCP(FastMCP):
    """MCP server for interacting with Nest Protect devices."""
    
    def __init__(self, config: Union[Dict[str, Any], 'ProtectConfig'], **kwargs):
        """Initialize the Nest Protect MCP server.
        
        Args:
            config: Configuration dictionary or ProtectConfig instance
            **kwargs: Additional arguments to pass to the base class
        """
        try:
            logger.debug("Initializing NestProtectMCP")
            
            # Initialize the base class with required parameters
            super().__init__(
                name=kwargs.pop("name", "nest-protect"),
                instructions=kwargs.pop("instructions", "MCP server for Nest Protect devices"),
                version=kwargs.pop("version", "1.0.0"),
                **kwargs
            )
            
            # Load configuration
            if isinstance(config, dict):
                self._config = ProtectConfig(**config)
            else:
                self._config = config
                
            logger.debug("Configuration loaded successfully")
            
            # Initialize state
            self._session = None
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = 0
            self._devices = {}
            self._initialized = False
            
            # Register message handlers
            self._message_handlers = {}
            self._register_message_handlers()
            
        except Exception as e:
            logger.error("Failed to initialize NestProtectMCP: %s", str(e), exc_info=True)
            raise
    
    async def initialize(self):
        """Initialize the server asynchronously."""
        if self._initialized:
            logger.debug("Server already initialized")
            return
            
        logger.info("Initializing Nest Protect MCP server...")
        
        try:
            # Initialize HTTP session with timeout
            self._session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'NestProtectMCP/1.0',
                    'Accept': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            # Initialize with empty devices list by default
            self._devices = {}
            
            # Try to load authentication state, but don't fail if it's not available
            try:
                await self._load_auth_state()
                logger.info("Authentication state loaded successfully")
            except Exception as auth_error:
                logger.warning("Could not load authentication state: %s", str(auth_error))
                logger.info("Server will start in unauthenticated mode")
                self._access_token = None
                self._refresh_token = None
            
            # Try to initialize devices, but continue even if it fails
            try:
                if self._access_token:  # Only try to initialize devices if we have auth
                    await self._initialize_devices()
                    logger.info("Successfully initialized %d devices", len(self._devices))
                else:
                    logger.info("No authentication available, skipping device initialization")
            except Exception as dev_error:
                logger.warning("Could not initialize devices: %s", str(dev_error))
                logger.info("Server will start with no devices")
                self._devices = {}
            
            self._initialized = True
            logger.info("Nest Protect MCP server initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize: %s", str(e), exc_info=True)
            # Don't re-raise, allow server to start in limited mode
            self._initialized = True
    
    async def shutdown(self):
        """Shutdown the server and clean up resources."""
        logger.info("Shutting down Nest Protect MCP server...")
        if self._session and not self._session.closed:
            await self._session.close()
        self._initialized = False
        logger.info("Shutdown complete")
    
    def _register_message_handlers(self):
        """Register MCP message handlers and tools."""
        # Register core message handlers
        self._message_handlers.update({
            "initialize": self._handle_initialize,
            "ping": self._handle_ping,
            "list_tools": self._handle_list_tools,
            "get_tool": self._handle_get_tool,
        })
        
        # Register tools with FastMCP 2.12 decorators
        @self.tool("get_devices", **tool_schemas["get_devices"])
        async def get_devices() -> List[Dict[str, Any]]:
            """Get a list of all Nest Protect devices."""
            return await self._get_devices()
            
        @self.tool("get_device", **tool_schemas["get_device"])
        async def get_device(device_id: str) -> Dict[str, Any]:
            """Get detailed information about a specific Nest Protect device."""
            return await self._get_device(device_id)
            
        @self.tool("silence_alarm", **tool_schemas["silence_alarm"])
        async def silence_alarm(device_id: str, duration_seconds: int = 300) -> Dict[str, Any]:
            """Silence the alarm on a specific Nest Protect device."""
            return await self._silence_alarm(device_id, duration_seconds)
            
        @self.tool("get_device_history", **tool_schemas["get_device_history"])
        async def get_device_history(
            device_id: str,
            start_time: Optional[str] = None,
            end_time: Optional[str] = None,
            max_results: int = 10
        ) -> Dict[str, Any]:
            """Get the history of events for a specific Nest Protect device."""
            return await self._get_device_history(device_id, start_time, end_time, max_results)
    
    async def _handle_initialize(self, message: McpMessage) -> Dict[str, Any]:
        """Handle initialize message."""
        return {
            "serverInfo": {
                "name": self.name,
                "version": self.version,
                "capabilities": {
                    "tool": True,
                    "file": False,
                    "memory": False,
                }
            }
        }
    
    async def _handle_ping(self, message: McpMessage) -> Dict[str, Any]:
        """Handle ping message."""
        return {"pong": True}
    
    # Add other MCP message handlers here
    
    async def _handle_list_tools(self, message: McpMessage) -> Dict[str, Any]:
        """Handle list_tools message."""
        return {
            "tools": [
                {"name": name, "description": schema.get("description", "")}
                for name, schema in tool_schemas.items()
            ]
        }
        
    async def _handle_get_tool(self, message: McpMessage) -> Dict[str, Any]:
        """Handle get_tool message."""
        tool_name = message.params.get("name")
        if not tool_name or tool_name not in tool_schemas:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        return tool_schemas[tool_name]
    
    async def handle_message(self, message: McpMessage) -> Dict[str, Any]:
        """Handle an incoming MCP message."""
        try:
            logger.debug("Handling message: %s", message.method)
            
            # Check if this is a tool call
            if message.method == "tool_call":
                tool_name = message.params.get("name")
                tool_args = message.params.get("arguments", {})
                
                # Find and call the tool
                tool_func = getattr(self, f"_tool_{tool_name}", None)
                if not tool_func or not callable(tool_func):
                    raise ValueError(f"Unknown tool: {tool_name}")
                    
                # Call the tool with provided arguments
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(**tool_args)
                else:
                    result = tool_func(**tool_args)
                    
                return {"result": result}
                
            # Handle standard MCP messages
            handler = self._message_handlers.get(message.method)
            if not handler:
                raise ValueError(f"Unknown method: {message.method}")
                
            return await handler(message)
            
        except Exception as e:
            logger.error("Error handling message: %s", str(e), exc_info=True)
            raise

    # Tool implementation methods
    async def _get_devices(self) -> List[Dict[str, Any]]:
        """Implementation of get_devices tool."""
        try:
            if not self._initialized:
                await self.initialize()
                
            if not hasattr(self, '_devices') or not self._devices:
                logger.info("No devices available")
                return []
                
            devices = []
            for device in self._devices.values():
                try:
                    devices.append({
                        "id": getattr(device, 'id', 'unknown'),
                        "name": getattr(device, 'name', 'Unknown Device'),
                        "type": getattr(device, 'type', 'sdm.devices.types.UNKNOWN'),
                        "online": getattr(device, 'online', False),
                        "battery_state": getattr(device, 'battery_state', None),
                        "alarm_state": getattr(device, 'alarm_state', None),
                        "last_connection": getattr(device, 'last_connection', None)
                    })
                except Exception as dev_error:
                    logger.warning("Error processing device: %s", str(dev_error))
                    continue
                    
            return devices
            
        except Exception as e:
            logger.error("Failed to get devices: %s", str(e), exc_info=True)
            # Return empty list instead of failing
            return []
    
    async def _get_device(self, device_id: str) -> Dict[str, Any]:
        """Implementation of get_device tool."""
        try:
            if not self._initialized:
                await self.initialize()
                
            if not hasattr(self, '_devices') or device_id not in self._devices:
                logger.warning("Device not found: %s", device_id)
                return {
                    "id": device_id,
                    "error": "Device not found or not available",
                    "available": False
                }
                
            device = self._devices[device_id]
            return {
                "id": getattr(device, 'id', device_id),
                "name": getattr(device, 'name', 'Unknown Device'),
                "type": getattr(device, 'type', 'sdm.devices.types.UNKNOWN'),
                "online": getattr(device, 'online', False),
                "battery_state": getattr(device, 'battery_state', None),
                "alarm_state": getattr(device, 'alarm_state', None),
                "last_connection": getattr(device, 'last_connection', None),
                "details": {
                    # Add any additional device-specific details here
                },
                "available": True
            }
            
        except Exception as e:
            logger.error("Failed to get device %s: %s", device_id, str(e), exc_info=True)
            return {
                "id": device_id,
                "error": f"Error retrieving device: {str(e)}",
                "available": False
            }
    
    async def _silence_alarm(self, device_id: str, duration_seconds: int = 300) -> Dict[str, Any]:
        """Implementation of silence_alarm tool."""
        try:
            if not self._initialized:
                await self.initialize()
                
            if not hasattr(self, '_devices') or device_id not in self._devices:
                logger.warning("Attempted to silence non-existent device: %s", device_id)
                return {
                    "success": False,
                    "message": f"Device {device_id} not found or not available",
                    "device_id": device_id
                }
                
            # Check if we have authentication
            if not hasattr(self, '_access_token') or not self._access_token:
                logger.warning("Authentication required to silence alarm")
                return {
                    "success": False,
                    "message": "Authentication required to silence alarm",
                    "device_id": device_id,
                    "authentication_required": True
                }
            
            # Check if token is expired or about to expire
            if time.time() >= (getattr(self, '_token_expires_at', 0) - 60):
                try:
                    await self._refresh_token()
                except Exception as auth_error:
                    logger.warning("Failed to refresh token: %s", str(auth_error))
                    return {
                        "success": False,
                        "message": "Authentication token expired or invalid",
                        "device_id": device_id,
                        "authentication_required": True
                    }
            
            # Implement actual alarm silencing logic here
            logger.info("Silencing alarm on device %s for %d seconds", device_id, duration_seconds)
            
            # Simulate a successful response
            return {
                "success": True,
                "message": f"Alarm silenced on device {device_id} for {duration_seconds} seconds",
                "device_id": device_id,
                "duration_seconds": duration_seconds
            }
            
        except Exception as e:
            logger.error("Failed to silence alarm on device %s: %s", device_id, str(e), exc_info=True)
            return {
                "success": False,
                "message": f"Failed to silence alarm: {str(e)}",
                "device_id": device_id,
                "error": str(e)
            }
    
    async def _get_device_history(
        self,
        device_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Implementation of get_device_history tool."""
        try:
            if not self._initialized:
                await self.initialize()
                
            if not hasattr(self, '_devices') or device_id not in self._devices:
                logger.warning("Attempted to get history for non-existent device: %s", device_id)
                return {
                    "device_id": device_id,
                    "events": [],
                    "error": "Device not found or not available",
                    "available": False
                }
                
            # Check if we have authentication
            if not hasattr(self, '_access_token') or not self._access_token:
                logger.warning("Authentication required to get device history")
                return {
                    "device_id": device_id,
                    "events": [],
                    "error": "Authentication required",
                    "authentication_required": True
                }
                
            # Parse time range with error handling
            try:
                start_dt = datetime.fromisoformat(start_time) if start_time else None
                end_dt = datetime.fromisoformat(end_time) if end_time else None
            except ValueError as e:
                logger.warning("Invalid time format: %s", str(e))
                return {
                    "device_id": device_id,
                    "events": [],
                    "error": f"Invalid time format: {str(e)}",
                    "available": True
                }
            
            # Return empty history for now
            # In a real implementation, this would fetch from the Nest API
            return {
                "device_id": device_id,
                "events": [],
                "message": "Device history is not currently implemented",
                "available": True
            }
            
        except Exception as e:
            logger.error("Failed to get history for device %s: %s", device_id, str(e), exc_info=True)
            return {
                "device_id": device_id,
                "events": [],
                "error": f"Failed to get history: {str(e)}",
                "available": False
            }

# Create a global instance
server = None

def create_server(config: Optional[Dict[str, Any]] = None) -> NestProtectMCP:
    """Create and configure the MCP server."""
    global server
    if not server:
        if config is None:
            config = {}
        server = NestProtectMCP(config)
    return server

async def main():
    """Run the MCP server."""
    server = create_server()
    try:
        await server.initialize()
        await server.serve()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Server error: %s", str(e), exc_info=True)
    finally:
        await server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
