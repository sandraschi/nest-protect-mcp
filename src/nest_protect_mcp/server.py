"""
Nest Protect MCP Server

This module implements the main server for interacting with Nest Protect devices
using the Message Control Protocol (MCP).
"""
import asyncio
import json
import logging
import os
import time
import aiohttp
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable, TypeVar, cast

from fastapi import FastAPI, Request
from fastmcp import FastMCP
from fastmcp.client.messages import Message as McpMessage
from pydantic import ValidationError

from .state_manager import state_manager

# Constants
NEST_AUTH_URL = "https://www.googleapis.com/oauth2/v4/token"
NEST_API_URL = "https://smartdevicemanagement.googleapis.com/v1"
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes in seconds

from .models import (
    ProtectConfig,
    ProtectDeviceState,
    ProtectCommand,
    ProtectEvent,
    ProtectAlarmState,
    ProtectBatteryState,
)
from .exceptions import (
    NestProtectError,
    NestAuthError,
    NestConnectionError,
    NestDeviceNotFoundError,
    NestInvalidCommandError,
)

# Type aliases
T = TypeVar('T')
MessageHandler = Callable[[McpMessage], Awaitable[Dict[str, Any]]]

# Configure logging
logger = logging.getLogger(__name__)

class NestProtectMCP(FastMCP):
    """MCP server for interacting with Nest Protect devices with stateful support."""
    
    def __init__(self, config: Union[Dict[str, Any], 'ProtectConfig'], **kwargs):
        """Initialize the Nest Protect MCP server.
        
        Args:
            config: Configuration dictionary or ProtectConfig instance
            **kwargs: Additional arguments to pass to the base class
        """
        try:
            logger.debug("Initializing NestProtectMCP with config: %s", 
                        {k: '***' if 'secret' in k.lower() or 'token' in k.lower() else v 
                         for k, v in (config if isinstance(config, dict) else config.dict()).items()})
            
            # Initialize the base class with required parameters
            super().__init__(
                name=kwargs.pop("name", "nest-protect"),
                instructions=kwargs.pop("instructions", "MCP server for Nest Protect devices"),
                version=kwargs.pop("version", "1.0.0"),
                **kwargs
            )
            
            # Initialize FastAPI router
            from fastapi import APIRouter
            self.router = APIRouter()
            self._setup_routes()
            
            # Store state manager reference
            self._state_manager = state_manager
            
            # Load configuration
            if isinstance(config, dict):
                from .models import ProtectConfig
                self._config = ProtectConfig(**config)
            else:
                self._config = config
                
            logger.debug("Configuration loaded successfully")
            
        except Exception as e:
            logger.error("Failed to initialize NestProtectMCP: %s", str(e), exc_info=True)
            raise
            
        # Initialize state
        self._session = None
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = 0
        self._devices = {}
        self._initialized = False
        self._auth_loaded = asyncio.Event()
        
        # State keys for persistence
        self._state_keys = {
            'access_token': 'nest_access_token',
            'refresh_token': 'nest_refresh_token',
            'token_expires_at': 'nest_token_expires_at',
            'devices': 'nest_devices'
        }
        
        # Register message handlers
        self._message_handlers = {}
        self._register_message_handlers()
        
    async def initialize(self):
        """Initialize the server asynchronously."""
        if self._initialized:
            logger.debug("Server already initialized, skipping initialization")
            return
            
        try:
            logger.info("Initializing Nest Protect MCP server...")
            
            # Initialize HTTP client session first
            logger.debug("Initializing HTTP client session...")
            self._session = aiohttp.ClientSession()
            
            # Load auth state
            logger.debug("Loading authentication state...")
            await self._load_auth_state()
            
            # Register message handlers
            logger.debug("Registering message handlers...")
            self._register_message_handlers()
            
            # Try to initialize device state, but don't fail if not authenticated yet
            try:
                logger.debug("Attempting to initialize device state...")
                await self._get_devices_from_api()
                logger.info("Successfully connected to Nest API")
            except Exception as e:
                logger.warning(f"Could not initialize device state: {e}")
                logger.info("Please complete the authentication process to access Nest devices")
            
            self._initialized = True
            logger.info("Nest Protect MCP server initialized successfully")
            if not self._refresh_token:
                logger.info("\n⚠️  No authentication token found. Please run the following command to authenticate:")
                logger.info("   python -m nest_protect_mcp auth\n")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}", exc_info=True)
            if hasattr(self, '_session') and not self._session.closed:
                await self._session.close()
            raise
    
    async def shutdown(self):
        """Shutdown the server and clean up resources."""
        logger.info("Shutting down Nest Protect MCP server...")
        if hasattr(self, '_session') and self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP session closed")
        self._initialized = False
        logger.info("Nest Protect MCP server shutdown complete")
    
    def _setup_routes(self) -> None:
        """Set up FastAPI routes for the server."""
        @self.router.get("/health")
        async def health_check():
            return {"status": "ok"}
            
        @self.router.get("/api/devices")
        async def get_devices():
            return await self._handle_get_devices()
            
        @self.router.get("/api/devices/{device_id}")
        async def get_device(device_id: str):
            return await self._handle_get_device(device_id)
            
        @self.router.post("/api/devices/{device_id}/hush")
        async def hush_device(device_id: str):
            return await self._handle_hush_alarm(device_id)
            
        @self.router.post("/api/devices/{device_id}/test")
        async def test_device(device_id: str, test_type: str = "manual"):
            return await self._handle_run_test(device_id, test_type)
    
    def _register_message_handlers(self) -> None:
        """Register message handlers for MCP server using FastMCP 2.12.0 tool decorators."""
        # Create tool methods with proper decorators
        @self.tool(name="get_devices")
        async def get_devices_tool():
            """Get all Nest Protect devices."""
            return await self._handle_get_devices()
            
        @self.tool(name="get_device")
        async def get_device_tool(device_id: str):
            """Get a specific Nest Protect device by ID."""
            return await self._handle_get_device(device_id)
            
        @self.tool(name="send_command")
        async def send_command_tool(device_id: str, command: str, params: dict = None):
            """Send a command to a Nest Protect device."""
            return await self._handle_send_command(device_id, command, params or {})
            
        @self.tool(name="get_alarm_state")
        async def get_alarm_state_tool(device_id: str):
            """Get the current alarm state of a Nest Protect device."""
            return await self._handle_get_alarm_state(device_id)
            
        @self.tool(name="hush_alarm")
        async def hush_alarm_tool(device_id: str):
            """Hush the alarm on a Nest Protect device."""
            return await self._handle_hush_alarm(device_id)
            
        @self.tool(name="run_test")
        async def run_test_tool(device_id: str, test_type: str = "manual"):
            """Run a test on a Nest Protect device."""
            return await self._handle_run_test(device_id, test_type)
            
        # Store references to prevent garbage collection
        self._tools = [
            get_devices_tool,
            get_device_tool,
            send_command_tool,
            get_alarm_state_tool,
            hush_alarm_tool,
            run_test_tool
        ]
    
    async def _ensure_session(self) -> None:
        """Ensure we have a valid session and access token."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def _load_auth_state(self):
        """Load authentication state from the state manager."""
        try:
            state = await self._state_manager.get_all()
            if state:
                self._access_token = state.get(self._state_keys['access_token'])
                self._refresh_token = state.get(self._state_keys['refresh_token'])
                expires_at = state.get(self._state_keys['token_expires_at'])
                self._token_expires_at = float(expires_at) if expires_at is not None else 0
                
                # Load devices if they exist in state
                devices_data = state.get(self._state_keys['devices'], {})
                if devices_data and isinstance(devices_data, dict):
                    self._devices = devices_data
                
                logger.info("Loaded authentication state from state manager")
            else:
                logger.info("No existing auth state found, starting fresh")
                self._access_token = None
                self._refresh_token = None
                self._token_expires_at = 0
        except Exception as e:
            logger.error(f"Failed to load auth state: {e}")
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = 0
    
    async def _save_auth_state(self):
        """Save authentication state to the state manager."""
        try:
            # Save tokens
            await self._state_manager.set(self._state_keys['access_token'], self._access_token)
            await self._state_manager.set(self._state_keys['refresh_token'], self._refresh_token)
            await self._state_manager.set(self._state_keys['token_expires_at'], self._token_expires_at)
            
            # Save devices state
            if self._devices:
                await self._state_manager.set(self._state_keys['devices'], self._devices)
                
            logger.debug("Saved authentication state to state manager")
        except Exception as e:
            logger.error(f"Failed to save auth state: {e}")
            raise NestAuthError(f"Failed to save auth state: {e}")
    
    @property
    async def access_token(self) -> Optional[str]:
    # Get the current access token, refreshing if necessary
        if not self._access_token or time.time() >= self._token_expires_at - 300:  # 5 min buffer
            await self._refresh_access_token()
            
            # Save state after token refresh
            try:
                await self._save_auth_state()
            except Exception as e:
                logger.error(f"Failed to save auth state after token refresh: {e}")
                
        return self._access_token
    
    async def _get_access_token(self) -> str:
    # Get a valid access token, refreshing if necessary
        token = await self.access_token
        if not token:
            raise NestAuthError("No access token available")
        return token
    
    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            logger.warning("No refresh token available. Please complete the authentication process.")
            return
            
        logger.info("Refreshing access token...")
        
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
                
            data = {
                'client_id': self._config.client_id,
                'client_secret': self._config.client_secret,
                'refresh_token': self._refresh_token,
                'grant_type': 'refresh_token'
            }
            
            async with self._session.post(NEST_AUTH_URL, data=data) as response:
                response.raise_for_status()
                token_data = await response.json()
                
                # Update tokens
                self._access_token = token_data['access_token']
                self._refresh_token = token_data.get('refresh_token', self._refresh_token)
                self._token_expires_at = time.time() + int(token_data.get('expires_in', 3600))
                
                # Save the updated tokens
                await self._save_auth_state()
                logger.info("Successfully refreshed and saved access token")
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to refresh access token: {e}")
            
            # Clear invalid tokens on auth failure
            if '401' in str(e) or '403' in str(e):
                self._access_token = None
                self._refresh_token = None
                self._token_expires_at = 0
                await self._save_auth_state()
                
            raise NestConnectionError(f"Failed to refresh token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error refreshing token: {e}")
            raise NestAuthError(f"Failed to refresh token: {e}")
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        # Make an authenticated request to the Nest API
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        # Ensure we have a valid access token
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._refresh_access_token()
            
        # Initialize headers with defaults and merge with any provided headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }
        headers.update(kwargs.pop('headers', {}))
        
        url = f"{NEST_API_URL}/{endpoint.lstrip('/')}"
        
        # Log the request
        logger.debug(f"Making {method} request to {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, **kwargs) as response:
                    if response.status == 401:  # Unauthorized
                        # Try refreshing the token once
                        await self._refresh_access_token()
                        new_token = await self.access_token
                        if not new_token:
                            raise NestAuthError("Failed to refresh access token")
                            
                        headers['Authorization'] = f"Bearer {new_token}"
                        
                        # Retry the request
                        logger.debug(f"Retrying {method} request to {url} with new token")
                        async with session.request(method, url, headers=headers, **kwargs) as retry_response:
                            retry_response.raise_for_status()
                            return await retry_response.json()
                    
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            raise NestConnectionError(f"Network error: {e}")
    
    async def _get_devices_from_api(self) -> List[Dict[str, Any]]:
        # Load all devices from the Nest API
        if not self._refresh_token:
            logger.warning("No refresh token available. Please complete the authentication process first.")
            return []
            
        try:
            response = await self._make_request('GET', f'enterprises/{self._config.project_id}/devices')
            return response.get('devices', [])
        except NestAuthError as e:
            logger.warning(f"Authentication error while fetching devices: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get devices from API: {e}")
            return []
    
    def _map_device_state(self, device_data: Dict[str, Any]) -> ProtectDeviceState:
        # Map Nest API device data to our internal device state model
        traits = device_data.get('traits', {})
        
        # Map alarm states
        co_alarm_state = self._map_alarm_state(traits.get('sdm.devices.traits.Smoke', {}).get('alarmState'))
        smoke_alarm_state = self._map_alarm_state(traits.get('sdm.devices.traits.CarbonMonoxide', {}).get('alarmState'))
        heat_alarm_state = self._map_alarm_state(traits.get('sdm.devices.traits.Heat', {}).get('alarmState'))
        
        # Map battery state
        battery_state = self._map_battery_state(traits.get('sdm.devices.traits.Battery', {}).get('batteryStatus'))
        
        return ProtectDeviceState(
            device_id=device_data['name'].split('/')[-1],
            name=traits.get('sdm.devices.traits.Info', {}).get('customName', device_data['name']),
            model=traits.get('sdm.devices.traits.Info', {}).get('model', 'Unknown'),
            serial_number=traits.get('sdm.devices.traits.Info', {}).get('serialNumber', ''),
            online=traits.get('sdm.devices.traits.Connectivity', {}).get('status') == 'ONLINE',
            battery_health=battery_state,
            co_alarm_state=co_alarm_state,
            smoke_alarm_state=smoke_alarm_state,
            heat_alarm_state=heat_alarm_state,
            battery_level=traits.get('sdm.devices.traits.Battery', {}).get('batteryLevel'),
            temperature=traits.get('sdm.devices.traits.Temperature', {}).get('ambientTemperatureCelsius'),
            humidity=traits.get('sdm.devices.traits.Humidity', {}).get('ambientHumidityPercent'),
            last_connection=datetime.fromisoformat(device_data.get('lastEventTime', '').replace('Z', '+00:00')) if device_data.get('lastEventTime') else None,
            software_version=traits.get('sdm.devices.traits.Software', {}).get('version')
        )
    
    def _map_alarm_state(self, state: Optional[str]) -> ProtectAlarmState:
    # Map Nest API alarm state to our enum
        if not state:
            return ProtectAlarmState.OFF
        
        state_map = {
            'ALARM_STATE_UNSPECIFIED': ProtectAlarmState.OFF,
            'ALARM_STATE_OFF': ProtectAlarmState.OFF,
            'ALARM_STATE_WARNING': ProtectAlarmState.WARNING,
            'ALARM_STATE_CRITICAL': ProtectAlarmState.EMERGENCY,
            'ALARM_STATE_TEST': ProtectAlarmState.TESTING
        }
        return state_map.get(state, ProtectAlarmState.OFF)
    
    def _map_battery_state(self, status: Optional[str]) -> ProtectBatteryState:
    # Map Nest API battery status to our enum
        if not status:
            return ProtectBatteryState.INVALID
        
        status_map = {
            'BATTERY_STATUS_UNSPECIFIED': ProtectBatteryState.INVALID,
            'BATTERY_STATUS_NORMAL': ProtectBatteryState.OK,
            'BATTERY_STATUS_LOW': ProtectBatteryState.REPLACE,
            'BATTERY_STATUS_CRITICAL': ProtectBatteryState.CRITICAL,
            'BATTERY_STATUS_MISSING': ProtectBatteryState.MISSING
        }
        return status_map.get(status, ProtectBatteryState.INVALID)
    
    # ===== Public API =====
    
    # === API Endpoints ===
    
    async def _handle_get_devices(self) -> List[Dict[str, Any]]:
        """Get all Nest Protect devices.
        
        Returns:
            List of device information dictionaries
        """
        try:
            devices = await self.get_devices()
            return [device.dict() for device in devices]
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            raise Exception(f"Failed to get devices: {str(e)}")
    
    async def _handle_get_device(self, device_id: str) -> Dict[str, Any]:
        """Get a specific Nest Protect device by ID.
        
        Args:
            device_id: The ID of the device to retrieve
            
        Returns:
            Device information dictionary
            
        Raises:
            Exception: If device is not found or an error occurs
        """
        if not device_id:
            raise ValueError("device_id is required")
            
        device = await self.get_device(device_id)
        if not device:
            raise Exception(f"Device {device_id} not found")
            
        return device.dict()
    
    async def _handle_send_command(self, device_id: str, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to a Nest Protect device.
        
        Args:
            device_id: The ID of the device to send the command to
            command: The command to send
            params: Optional parameters for the command
            
        Returns:
            Dictionary with status and message
            
        Raises:
            Exception: If the command fails
        """
        try:
            cmd = ProtectCommand(device_id=device_id, command=command, params=params or {})
            success = await self.send_command(cmd)
            if not success:
                raise Exception("Failed to send command")
            return {"status": "success", "message": "Command sent successfully"}
        except ValidationError as e:
            raise Exception(f"Invalid command: {e}")
        except NestDeviceNotFoundError as e:
            raise Exception(str(e))
        except Exception as e:
            logger.error(f"Error sending command: {e}", exc_info=True)
            raise Exception(f"Error sending command: {e}")
    
    async def _handle_get_alarm_state(self, device_id: str) -> Dict[str, Any]:
        """Get the current alarm state of a Nest Protect device.
        
        Args:
            device_id: The ID of the device
            
        Returns:
            Dictionary containing alarm state information
            
        Raises:
            Exception: If device is not found or an error occurs
        """
        if not device_id:
            raise ValueError("device_id is required")
            
        device = await self.get_device(device_id)
        if not device:
            raise Exception(f"Device {device_id} not found")
            
        return {
            "status": "success",
            "device_id": device_id,
            "co_alarm_state": device.co_alarm_state,
            "smoke_alarm_state": device.smoke_alarm_state,
            "heat_alarm_state": device.heat_alarm_state,
            "battery_health": device.battery_health
        }
    
    async def _handle_hush_alarm(self, device_id: str) -> Dict[str, Any]:
        """Hush the alarm on a Nest Protect device.
        
        Args:
            device_id: The ID of the device to hush
            
        Returns:
            Dictionary with status and message
            
        Raises:
            Exception: If the operation fails
        """
        if not device_id:
            raise ValueError("device_id is required")
            
        try:
            success = await self.hush_alarm(device_id)
            if not success:
                raise Exception("Failed to hush alarm")
            return {"status": "success", "message": "Alarm hushed successfully"}
        except NestDeviceNotFoundError as e:
            raise Exception(str(e))
        except Exception as e:
            logger.error(f"Error hushing alarm: {e}", exc_info=True)
            raise Exception(f"Error hushing alarm: {e}")
    
    async def _handle_run_test(self, device_id: str, test_type: str = "manual") -> Dict[str, Any]:
        """Run a test on a Nest Protect device.
        
        Args:
            device_id: The ID of the device
            test_type: Type of test to run (default: "manual")
            
        Returns:
            Dictionary with status and message
            
        Raises:
            Exception: If the test fails to start
        """
        if not device_id:
            raise ValueError("device_id is required")
            
        try:
            success = await self.run_test(device_id, test_type)
            if not success:
                raise Exception(f"Failed to start test '{test_type}'")
            return {"status": "success", "message": f"Test '{test_type}' started successfully"}
        except NestDeviceNotFoundError as e:
            raise Exception(str(e))
        except Exception as e:
            logger.error(f"Error running test: {e}", exc_info=True)
            raise Exception(f"Error running test: {e}")

# For backward compatibility
NestProtectServer = NestProtectMCP

# Lifespan handler for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for FastAPI application."""
    # Startup
    logger.info("Starting Nest Protect MCP server...")
    
    # Initialize MCP server
    mcp_server = NestProtectMCP(config=app.state.config)
    await mcp_server.initialize()
    
    # Store server instance
    app.state.mcp_server = mcp_server
    
    # Include MCP routes if router is available
    if hasattr(mcp_server, 'router'):
        app.include_router(mcp_server.router, prefix="/mcp")
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down Nest Protect MCP server...")
        try:
            await mcp_server.shutdown()
            if mcp_server._session and not mcp_server._session.closed:
                await mcp_server._session.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        logger.info("Nest Protect MCP server stopped")

def create_app(config: Optional[Dict[str, Any]] = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    # Create the app with lifespan management
    app = FastAPI(
        title="Nest Protect MCP Server",
        description="MCP server for controlling Nest Protect devices",
        version="1.0.0",
        docs_url="/api/docs",  # Enable Swagger UI at /api/docs
        redoc_url="/api/redoc",  # Enable ReDoc at /api/redoc
        openapi_url="/api/openapi.json",  # Path to OpenAPI schema
        lifespan=lifespan
    )
    
    # Store config in app state
    app.state.config = config or {}
    
    # Add built-in routes
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint.
        
        Returns:
            dict: Status of the service
        """
        return {"status": "ok", "service": "Nest Protect MCP Server"}
    
    # Add API versioning
    @app.get("/api/version", tags=["API"])
    async def get_version():
        """Get API version information.
        
        Returns:
            dict: API version information
        """
        return {
            "name": "Nest Protect MCP API",
            "version": "1.0.0",
            "docs": "/api/docs"
        }
    
    return app

# Create default app instance
app = create_app()
