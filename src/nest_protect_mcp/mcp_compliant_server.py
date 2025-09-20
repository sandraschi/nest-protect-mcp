"""
Nest Protect MCP Server (FastMCP 2.12 Compliant)

This module implements a FastMCP 2.12 compliant server for interacting with Nest Protect devices.
"""
import asyncio
import logging
import json
import signal
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Type, TypeVar, Union, Callable, Awaitable

from fastmcp import FastMCP
from fastmcp.tools import Tool
from fastmcp.client.messages import Message as McpMessage
from pydantic import BaseModel, Field, ValidationError, ConfigDict

from .models import ProtectConfig, ProtectDeviceState, ProtectAlarmState, ProtectBatteryState
from .exceptions import (
    NestDeviceNotFoundError, 
    NestAuthError, 
    NestConnectionError,
    NestInvalidCommandError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nest_protect_mcp")

# Type aliases
T = TypeVar('T')

# Pydantic models for tool parameters with proper schema definitions
class EmptyParams(BaseModel):
    model_config = ConfigDict(
        schema_extra={
            "description": "Empty parameters for methods that don't require any input"
        }
    )

class DeviceIdParams(BaseModel):
    device_id: str = Field(
        ..., 
        description="The unique identifier of the device"
    )
    
    class Config:
        schema_extra = {
            "example": {"device_id": "enterprises/project-id/devices/device-id"}
        }

class SilenceAlarmParams(DeviceIdParams):
    duration_seconds: int = Field(
        300, 
        ge=60, 
        le=3600,
        description="Duration to silence the alarm in seconds"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "enterprises/project-id/devices/device-id",
                "duration_seconds": 300
            }
        }

class GetDeviceHistoryParams(DeviceIdParams):
    start_time: Optional[str] = Field(
        None,
        description="Start time for history (ISO 8601 format)"
    )
    end_time: Optional[str] = Field(
        None,
        description="End time for history (ISO 8601 format)"
    )
    max_results: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "enterprises/project-id/devices/device-id",
                "start_time": "2023-01-01T00:00:00Z",
                "end_time": "2023-01-31T23:59:59Z",
                "max_results": 10
            }
        }

class NestProtectMCP(FastMCP):
    """MCP server for interacting with Nest Protect devices with FastMCP 2.12 compatibility."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Nest Protect MCP server.
        
        Args:
            config: Optional configuration dictionary with the following keys:
                - client_id: Nest OAuth client ID
                - client_secret: Nest OAuth client secret
                - project_id: Google Cloud project ID
                - log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                - state_file: Path to the state file for persistence
        """
        super().__init__(
            name="nest-protect",
            version="1.0.0",
            instructions="MCP server for Nest Protect devices with FastMCP 2.12 compatibility"
        )
        
        # Initialize state
        self._config = ProtectConfig(**(config or {}))
        self._session = None
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = 0
        self._devices: Dict[str, ProtectDeviceState] = {}
        self._initialized = False
        self._auth_loaded = asyncio.Event()
        
        # State keys for persistence
        self._state_keys = {
            'access_token': 'nest_access_token',
            'refresh_token': 'nest_refresh_token',
            'token_expires_at': 'nest_token_expires_at',
            'devices': 'nest_devices'
        }
        
        # Tool registry is handled by FastMCP base class
        
        # Register tools and message handlers
        self._register_tools()
        self._register_message_handlers()
        
        logger.info("NestProtectMCP initialized with FastMCP 2.12 compatibility")
    
    def _register_tools(self):
        """Register all MCP tools with proper FastMCP 2.12 schemas."""
        # Import all tools from the tools module
        from .tools import get_all_tools
        from .tools.device_status import EmptyParams, DeviceIdParams, DeviceEventsParams
        from .tools.device_control import HushAlarmParams, SafetyCheckParams, LedBrightnessParams
        from .tools.auth_tools import OAuthFlowParams, OAuthCallbackParams, RefreshTokenParams
        from .tools.config_tools import ConfigSectionParams, UpdateConfigParams, ResetConfigParams, ExportConfigParams, ImportConfigParams
        from .tools.system_status import ProcessStatusParams
        from .tools.help_tool import ToolHelpParams, SearchToolsParams
        
        all_tools = get_all_tools()
        
        # Register device status tools
        @self.tool("list_devices", description="Get a list of all Nest Protect devices")
        async def list_devices(params: EmptyParams) -> List[Dict[str, Any]]:
            return await all_tools['list_devices']()
            
        @self.tool("get_device_status", description="Get status of a specific Nest Protect device")
        async def get_device_status(params: DeviceIdParams) -> Dict[str, Any]:
            return await all_tools['get_device_status'](params.device_id)
            
        @self.tool("get_device_events", description="Get recent events for a Nest Protect device")
        async def get_device_events(params: DeviceEventsParams) -> Dict[str, Any]:
            return await all_tools['get_device_events'](params.device_id, params.limit)
        
        # Register device control tools
        @self.tool("hush_alarm", description="Silence an active alarm on a Nest Protect device")
        async def hush_alarm(params: HushAlarmParams) -> Dict[str, Any]:
            return await all_tools['hush_alarm'](params.device_id, params.duration_seconds)
            
        @self.tool("run_safety_check", description="Run a safety check on a Nest Protect device")
        async def run_safety_check(params: SafetyCheckParams) -> Dict[str, Any]:
            return await all_tools['run_safety_check'](params.device_id, params.test_type)
            
        @self.tool("set_led_brightness", description="Set LED brightness for a Nest Protect device")
        async def set_led_brightness(params: LedBrightnessParams) -> Dict[str, Any]:
            return await all_tools['set_led_brightness'](params.device_id, params.brightness)
        
        # Register system status tools
        @self.tool("get_system_status", description="Get system status and metrics")
        async def get_system_status(params: EmptyParams) -> Dict[str, Any]:
            return await all_tools['get_system_status']()
            
        @self.tool("get_process_status", description="Get status of the Nest Protect MCP process")
        async def get_process_status(params: ProcessStatusParams) -> Dict[str, Any]:
            return await all_tools['get_process_status'](params.pid)
            
        @self.tool("get_api_status", description="Get status of the Nest API connection")
        async def get_api_status(params: EmptyParams) -> Dict[str, Any]:
            return await all_tools['get_api_status']()
        
        # Register help tools
        @self.tool("list_available_tools", description="List all available tools with their descriptions")
        async def list_available_tools(params: EmptyParams) -> Dict[str, Any]:
            return await all_tools['list_available_tools']()
            
        @self.tool("get_tool_help", description="Get detailed help for a specific tool")
        async def get_tool_help(params: ToolHelpParams) -> Dict[str, Any]:
            return await all_tools['get_tool_help'](params.tool_name)
            
        @self.tool("search_tools", description="Search for tools by keyword or description")
        async def search_tools(params: SearchToolsParams) -> Dict[str, Any]:
            return await all_tools['search_tools'](params.query, params.search_in)
        
        # Register auth tools
        @self.tool("initiate_oauth_flow", description="Start OAuth 2.0 flow for Nest API")
        async def initiate_oauth_flow(params: OAuthFlowParams) -> Dict[str, Any]:
            return await all_tools['initiate_oauth_flow'](params.redirect_uri, params.state, params.open_browser)
            
        @self.tool("handle_oauth_callback", description="Handle OAuth 2.0 callback from Nest API")
        async def handle_oauth_callback(params: OAuthCallbackParams) -> Dict[str, Any]:
            return await all_tools['handle_oauth_callback'](params.code, params.state, params.expected_state, params.redirect_uri)
            
        @self.tool("refresh_access_token", description="Refresh OAuth 2.0 access token")
        async def refresh_access_token(params: RefreshTokenParams) -> Dict[str, Any]:
            return await all_tools['refresh_access_token'](params.force)
        
        # Register config tools
        @self.tool("get_config", description="Get current configuration")
        async def get_config(params: ConfigSectionParams) -> Dict[str, Any]:
            return await all_tools['get_config'](params.section)
            
        @self.tool("update_config", description="Update configuration values")
        async def update_config(params: UpdateConfigParams) -> Dict[str, Any]:
            return await all_tools['update_config'](params.updates, params.save_to_file)
            
        @self.tool("reset_config", description="Reset configuration to defaults")
        async def reset_config(params: ResetConfigParams) -> Dict[str, Any]:
            return await all_tools['reset_config'](params.confirm)
            
        @self.tool("export_config", description="Export current configuration to a file")
        async def export_config(params: ExportConfigParams) -> Dict[str, Any]:
            return await all_tools['export_config'](params.file_path, params.format)
            
        @self.tool("import_config", description="Import configuration from a file")
        async def import_config(params: ImportConfigParams) -> Dict[str, Any]:
            return await all_tools['import_config'](params.file_path, params.merge)
            
    def _register_message_handlers(self):
        """Register message handlers for MCP protocol."""
        self._message_handlers = {
            "list_tools": self._handle_list_tools,
            "get_tool": self._handle_get_tool,
            "execute_tool": self._handle_execute_tool,
        }
        
    async def handle_message(self, message: Union[Dict[str, Any], McpMessage]) -> Dict[str, Any]:
        """Handle an incoming MCP message.
        
        Args:
            message: The incoming MCP message
            
        Returns:
            Dict[str, Any]: The response message
            
        Raises:
            ValueError: If the message is invalid
        """
        # Convert to dict if it's a McpMessage
        if isinstance(message, McpMessage):
            msg_dict = message.dict()
        else:
            msg_dict = message
            
        try:
            msg_id = msg_dict.get("id")
            method = msg_dict.get("method")
            params = msg_dict.get("params", {})
            
            if not method:
                raise ValueError("Missing required field: method")
                
            logger.debug(f"Handling MCP message: method={method}, id={msg_id}")
            
            if method in self._message_handlers:
                handler = self._message_handlers[method]
                result = await handler(message if isinstance(message, McpMessage) else McpMessage(**msg_dict))
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                }
            else:
                raise ValueError(f"Unsupported method: {method}")
                
        except ValidationError as e:
            error_msg = f"Invalid message format: {str(e)}"
            logger.error(error_msg)
            return {
                "jsonrpc": "2.0",
                "id": msg_dict.get("id"),
                "error": {
                    "code": -32600,
                    "message": error_msg,
                    "data": {"errors": e.errors()}
                }
            }
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Invalid request: {error_msg}")
            return {
                "jsonrpc": "2.0",
                "id": msg_dict.get("id"),
                "error": {
                    "code": -32601,
                    "message": error_msg
                }
            }
            
        except Exception as e:
            error_msg = f"Internal server error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": msg_dict.get("id"),
                "error": {
                    "code": -32603,
                    "message": error_msg
                }
            }
    
    async def _handle_list_tools(self, message: McpMessage) -> Dict[str, Any]:
        """Handle list_tools MCP message."""
        tools = []
        for name, tool in self.get_tools().items():
            tools.append({
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
                "returns": tool.returns_schema
            })
        return tools
        
    async def _handle_get_tool(self, message: McpMessage) -> Dict[str, Any]:
        """Handle get_tool MCP message."""
        tool_name = message.params.get("name")
        if not tool_name:
            raise ValueError("Tool name is required")
            
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        return {
            "name": tool_name,
            "description": tool.description,
            "parameters": tool.parameters_schema,
            "returns": tool.returns_schema
        }
        
    async def _handle_execute_tool(self, message: McpMessage) -> Any:
        """Handle execute_tool MCP message."""
        tool_name = message.params.get("tool")
        if not tool_name:
            raise ValueError("Tool name is required")
            
        params = message.params.get("params", {})
        return await self._execute_tool(tool_name, params)
        
    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            The result of the tool execution
            
        Raises:
            ValueError: If the tool is not found or parameters are invalid
            Exception: If the tool execution fails
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        try:
            # Validate parameters against the tool's schema
            if tool.parameters_schema:
                try:
                    # This is a simplified validation - in a real implementation,
                    # you would want to use the actual Pydantic model for validation
                    import jsonschema
                    jsonschema.validate(params, tool.parameters_schema)
                except ImportError:
                    logger.warning("jsonschema not available, parameter validation skipped")
                except Exception as e:
                    raise ValueError(f"Invalid parameters: {str(e)}")
            
            # Execute the tool
            result = await tool.func(params)
            return result
            
        except ValidationError as e:
            raise ValueError(f"Parameter validation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            raise
    
    async def initialize(self):
        """Initialize the server asynchronously."""
        if self._initialized:
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
            
            # Try to load authentication state
            try:
                await self._load_auth_state()
                logger.info("Authentication state loaded successfully")
            except Exception as auth_error:
                logger.warning("Could not load authentication: %s", str(auth_error))
                logger.info("Server will start in unauthenticated mode")
                self._access_token = None
                self._refresh_token = None
            
            # Try to initialize devices if we have auth
            if self._access_token:
                try:
                    await self._initialize_devices()
                    logger.info("Initialized %d devices", len(self._devices))
                except Exception as dev_error:
                    logger.warning("Could not initialize devices: %s", str(dev_error))
                    self._devices = {}
            
            self._initialized = True
            logger.info("Nest Protect MCP server initialized")
            
        except Exception as e:
            logger.error("Initialization failed: %s", str(e), exc_info=True)
            self._initialized = True  # Still mark as initialized to allow operation
    
    # Implement the actual tool methods
    async def _get_devices(self) -> List[Dict[str, Any]]:
        """Get all Nest Protect devices.
        
        Returns:
            List[Dict[str, Any]]: List of devices with their basic information
            
        Raises:
            NestConnectionError: If there's an error connecting to the Nest service
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            if not self._devices:
                # Load devices if not already loaded
                await self._load_devices()
                
            return [
                {
                    "id": device.device_id,
                    "name": device.name,
                    "type": device.model,
                    "online": device.online,
                    "battery_state": device.battery_health.value if device.battery_health else None,
                    "alarm_state": device.smoke_alarm_state.value if device.smoke_alarm_state else None,
                    "last_seen": device.last_connection.isoformat() if device.last_connection else None,
                    "software_version": device.software_version,
                    "battery_level": device.battery_level
                }
                for device in self._devices.values()
            ]
            
        except Exception as e:
            logger.error(f"Error getting devices: {str(e)}", exc_info=True)
            raise NestConnectionError(f"Failed to get devices: {str(e)}")
    
    async def _get_device(self, device_id: str) -> Dict[str, Any]:
        """Get a specific device by ID.
        
        Args:
            device_id: The ID of the device to retrieve
            
        Returns:
            Dict[str, Any]: Detailed device information
            
        Raises:
            NestDeviceNotFoundError: If the device is not found
            NestConnectionError: If there's an error connecting to the Nest service
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            if not self._devices:
                # Load devices if not already loaded
                await self._load_devices()
                
            if device_id not in self._devices:
                raise NestDeviceNotFoundError(f"Device {device_id} not found")
            
            device = self._devices[device_id]
            
            return {
                "id": device.device_id,
                "name": device.name,
                "type": device.model,
                "online": device.online,
                "battery_state": device.battery_health.value if device.battery_health else None,
                "alarm_state": device.smoke_alarm_state.value if device.smoke_alarm_state else None,
                "last_seen": device.last_connection.isoformat() if device.last_connection else None,
                "software_version": device.software_version,
                "battery_level": device.battery_level,
                "serial_number": device.serial_number,
                "model": device.model
            }
            
        except NestDeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting device {device_id}: {str(e)}", exc_info=True)
            raise NestConnectionError(f"Failed to get device: {str(e)}")
    
    async def _silence_alarm(self, device_id: str, duration_seconds: int = 300) -> Dict[str, Any]:
        """Silence the alarm on a specific device.
        
        Args:
            device_id: The ID of the device to silence
            duration_seconds: Duration to silence the alarm (60-3600 seconds)
            
        Returns:
            Dict[str, Any]: Result of the silence operation
            
        Raises:
            NestDeviceNotFoundError: If the device is not found
            NestConnectionError: If there's an error connecting to the Nest service
            ValueError: If the duration is out of range
        """
        if not self._initialized:
            await self.initialize()
            
        if not 60 <= duration_seconds <= 3600:
            raise ValueError("Duration must be between 60 and 3600 seconds")
            
        try:
            if not self._devices:
                # Load devices if not already loaded
                await self._load_devices()
                
            if device_id not in self._devices:
                raise NestDeviceNotFoundError(f"Device {device_id} not found")
                
            # Get the device
            device = self._devices[device_id]
            
            # Check if the device supports alarm silencing
            if not hasattr(device, 'supports_alarm_silence') or not device.supports_alarm_silence:
                return {
                    "success": False,
                    "message": f"Device {device_id} does not support alarm silencing",
                    "device_id": device_id,
                    "duration_seconds": 0
                }
                
            # Here you would implement the actual alarm silencing logic
            # This is a placeholder implementation
            logger.info(f"Silencing alarm on device {device_id} for {duration_seconds} seconds")
            
            # Simulate a network request
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "message": f"Alarm silenced on device {device_id} for {duration_seconds} seconds",
                "device_id": device_id,
                "duration_seconds": duration_seconds,
                "silenced_until": (datetime.utcnow() + timedelta(seconds=duration_seconds)).isoformat() + 'Z'
            }
            
        except NestDeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error silencing alarm on device {device_id}: {str(e)}", exc_info=True)
            raise NestConnectionError(f"Failed to silence alarm: {str(e)}")
    
    async def _get_device_history(
        self,
        device_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Get device history.
        
        Args:
            device_id: The ID of the device
            start_time: Start time in ISO 8601 format (optional)
            end_time: End time in ISO 8601 format (optional)
            max_results: Maximum number of results to return (1-100)
            
        Returns:
            Dict[str, Any]: Device history with events
            
        Raises:
            NestDeviceNotFoundError: If the device is not found
            NestConnectionError: If there's an error connecting to the Nest service
            ValueError: If the parameters are invalid
        """
        if not self._initialized:
            await self.initialize()
            
        # Validate parameters
        if not 1 <= max_results <= 100:
            raise ValueError("max_results must be between 1 and 100")
            
        # Parse timestamps if provided
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError as e:
                raise ValueError(f"Invalid start_time format: {str(e)}")
                
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError as e:
                raise ValueError(f"Invalid end_time format: {str(e)}")
                
        if start_dt and end_dt and start_dt >= end_dt:
            raise ValueError("start_time must be before end_time")
            
        try:
            if not self._devices:
                # Load devices if not already loaded
                await self._load_devices()
                
            if device_id not in self._devices:
                raise NestDeviceNotFoundError(f"Device {device_id} not found")
                
            # Here you would implement the actual history retrieval logic
            # This is a placeholder implementation that returns mock data
            
            # Generate some mock events
            events = []
            now = datetime.utcnow()
            
            # Add some sample events
            sample_events = [
                (now, "ALARM_STARTED", "Smoke alarm was triggered", "critical"),
                (now - timedelta(minutes=5), "BATTERY_LOW", "Battery level is low", "warning"),
                (now - timedelta(hours=1), "DEVICE_ONLINE", "Device came online", "info"),
                (now - timedelta(days=1), "TEST_ALARM", "Test alarm was triggered", "info"),
                (now - timedelta(days=2), "DEVICE_ADDED", "Device was added to the system", "info")
            ]
            
            for event_time, event_type, description, severity in sample_events:
                # Filter by time range if specified
                if start_dt and event_time < start_dt:
                    continue
                if end_dt and event_time > end_dt:
                    continue
                    
                events.append({
                    "timestamp": event_time.isoformat() + 'Z',
                    "event_type": event_type,
                    "description": description,
                    "severity": severity
                })
                
                # Limit the number of results
                if len(events) >= max_results:
                    break
            
            return {
                "device_id": device_id,
                "events": events,
                "total_events": len(events),
                "time_range": {
                    "start": start_time or "",
                    "end": end_time or ""
                }
            }
            
        except NestDeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting device history for {device_id}: {str(e)}", exc_info=True)
            raise NestConnectionError(f"Failed to get device history: {str(e)}")
    
    async def _load_auth_state(self):
        """Load authentication state (placeholder implementation)."""
        # This is a placeholder - in a real implementation you would load from persistent storage
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = 0
        
    async def _initialize_devices(self):
        """Initialize devices (placeholder implementation)."""
        # This is a placeholder - in a real implementation you would load device data
        self._devices = {}
        
    async def _load_devices(self):
        """Load devices (placeholder implementation)."""
        # This is a placeholder - in a real implementation you would fetch from the API
        if not self._devices:
            # Create a mock device for demonstration
            mock_device = ProtectDeviceState(
                device_id="demo-device-1",
                name="Demo Protect",
                model="smoke_detector",
                online=True,
                battery_health=ProtectBatteryState.OK,
                co_alarm_state=ProtectAlarmState.OFF,
                smoke_alarm_state=ProtectAlarmState.OFF,
                heat_alarm_state=ProtectAlarmState.OFF
            )
            self._devices = {"demo-device-1": mock_device}

    async def shutdown(self):
        """Shutdown the server and clean up resources."""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
        self._initialized = False

async def run_server(config: Optional[Dict[str, Any]] = None):
    """Run the MCP server using FastMCP 2.12.
    
    Args:
        config: Optional configuration dictionary
    """
    # Create and initialize the server
    server = NestProtectMCP(config or {})
    
    try:
        logger.info("Starting Nest Protect MCP server...")
        
        # Initialize the server
        await server.initialize()
        
        # Run the server using stdio - this blocks until server stops
        await server.run_stdio_async()
        
    except Exception as e:
        logger.error(f"Error running server: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure resources are cleaned up
        try:
            await server.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            
    logger.info("Server stopped")

if __name__ == "__main__":
    import argparse
    import json
    import os
    from pathlib import Path
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Nest Protect MCP Server")
    parser.add_argument(
        "--config", 
        type=str, 
        default=None,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration if specified
    config = {}
    if args.config:
        try:
            config_path = Path(args.config).expanduser().resolve()
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {args.config}: {str(e)}")
            raise
    
    # Run the server
    try:
        asyncio.run(run_server(config))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise
