"""
Nest Protect MCP Server (FastMCP 2.12)

This module implements the main server for interacting with Nest Protect devices
using the Message Control Protocol (MCP) with FastMCP 2.12 compatibility.
"""
import asyncio
import logging
import signal
import sys
import time
import aiohttp
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable, TypeVar, cast, Type

from fastmcp import FastMCP
from fastmcp.tools import Tool
from fastmcp.client.messages import Message as McpMessage
from pydantic import BaseModel, ValidationError, Field

from .state_manager import state_manager

# Constants
NEST_AUTH_URL = "https://www.googleapis.com/oauth2/v4/token"
NEST_API_URL = "https://smartdevicemanagement.googleapis.com/v1"
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes in seconds

# Import models and exceptions
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nest_protect_mcp")

# Type aliases
T = TypeVar('T')
MessageHandler = Callable[[McpMessage], Awaitable[Dict[str, Any]]]

# Pydantic models for tool parameters
class EmptyParams(BaseModel):
    pass

class DeviceIdParams(BaseModel):
    device_id: str = Field(..., description="The ID of the device")

class SilenceAlarmParams(DeviceIdParams):
    duration_seconds: int = Field(
        300, 
        ge=60, 
        le=3600,
        description="Duration to silence the alarm in seconds"
    )

class NestProtectMCP(FastMCP):
    """MCP server for interacting with Nest Protect devices with FastMCP 2.12 support."""
    
    def __init__(self, config: Optional[Union[Dict[str, Any], 'ProtectConfig']] = None, **kwargs):
        """Initialize the Nest Protect MCP server.
        
        Args:
            config: Optional configuration dictionary or ProtectConfig instance
            **kwargs: Additional arguments to pass to the base class
        """
        # Set default config if none provided
        if config is None:
            config = {}
            
        try:
            # Initialize the base class with required parameters
            super().__init__(
                name=kwargs.pop("name", "nest-protect"),
                version=kwargs.pop("version", "1.0.0"),
                instructions=kwargs.pop("instructions", "MCP server for Nest Protect devices"),
                **kwargs
            )
            
            # Store state manager reference
            self._state_manager = state_manager
            
            # Load configuration
            if isinstance(config, dict):
                self._config = ProtectConfig(**(config or {}))
            else:
                self._config = config
                
            logger.debug("Configuration loaded successfully")
            
            # Initialize state
            self._session: Optional[aiohttp.ClientSession] = None
            self._access_token: Optional[str] = None
            self._refresh_token: Optional[str] = None
            self._token_expires_at: float = 0
            self._devices: Dict[str, Any] = {}
            self._initialized: bool = False
            self._auth_loaded = asyncio.Event()
            
            # State keys for persistence
            self._state_keys = {
                'access_token': 'nest_access_token',
                'refresh_token': 'nest_refresh_token',
                'token_expires_at': 'nest_token_expires_at',
                'devices': 'nest_devices'
            }
            
            # Register message handlers and tools
            self._message_handlers = {}
            self._register_message_handlers()
            self._register_tools()
            
        except Exception as e:
            logger.error("Failed to initialize NestProtectMCP: %s", str(e), exc_info=True)
            raise
        
    async def initialize(self):
        """Initialize the server asynchronously.
        
        This method performs the following operations:
        1. Initializes the HTTP session with proper timeouts
        2. Loads authentication state
        3. Initializes devices in the background
        4. Sets up periodic tasks
        
        Raises:
            NestAuthError: If authentication fails
            NestConnectionError: If connection to Nest services fails
            Exception: For any other unexpected errors
        """
        if self._initialized:
            logger.debug("Server already initialized, skipping initialization")
            return
            
        logger.info("Initializing Nest Protect MCP server...")
        
        try:
            # Initialize HTTP session
            self._session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'NestProtectMCP/1.0',
                    'Accept': 'application/json'
                }
            )
            
            # Load authentication state
            await self._load_auth_state()
            
            # Initialize devices
            await self._initialize_devices()
            # Set up periodic tasks
            self._setup_periodic_tasks()
            
            # Register message handlers
            self._register_message_handlers()
            
            self._initialized = True
            duration = time.time() - start_time
            logger.info(f"Nest Protect MCP server initialized successfully in {duration:.2f} seconds")
            
        except NestAuthError as e:
            logger.error(f"Authentication failed during initialization: {e}")
            await self.shutdown()
            raise
            
        except aiohttp.ClientError as e:
            error_msg = f"Network error during initialization: {e}"
            logger.error(error_msg, exc_info=True)
            await self.shutdown()
            raise NestConnectionError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error during initialization: {e}"
            logger.error(error_msg, exc_info=True)
            await self.shutdown()
            raise Exception(error_msg) from e
    
    async def _initialize_devices(self):
        """Initialize device state in the background."""
        try:
            if not self._refresh_token:
                logger.warning("No refresh token available. Please authenticate first.")
                return
                
            logger.info("Starting device initialization...")
            await self._get_devices_from_api()
            logger.info("Successfully initialized device state")
            
        except Exception as e:
            logger.warning(f"Device initialization warning: {e}")
            if "401" in str(e):
                logger.warning("Authentication may have expired. Please re-authenticate.")
                logger.info("\n⚠️  Please run: python -m nest_protect_mcp auth\n")
            logger.info("Nest Protect MCP server initialized successfully")
            if not self._refresh_token:
                logger.info("\n⚠️  No authentication token found. Please run the following command to authenticate:")
                logger.info("   python -m nest_protect_mcp auth\n")
            
    async def startup_event(self):
        """Handle application startup with improved error handling."""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting up Nest Protect MCP server (attempt {attempt + 1}/{max_retries})...")
                await self.initialize()
                logger.info("Startup completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"Startup attempt {attempt + 1} failed: {e}", exc_info=True)
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("All startup attempts failed")
                    raise NestProtectError("Failed to start Nest Protect MCP server")
    
    async def shutdown_event(self):
        """Handle application shutdown with cleanup."""
        logger.info("Shutting down Nest Protect MCP server...")
        
        # Close all active WebSocket connections
        if hasattr(self, '_active_connections'):
            logger.info(f"Closing {len(self._active_connections)} active WebSocket connections...")
            for websocket in list(self._active_connections):
                try:
                    await websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
            self._active_connections.clear()
        
        # Perform server shutdown
        try:
            await self.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        
        logger.info("Shutdown completed")
    
    async def shutdown(self):
        """Shutdown the server and clean up resources."""
        logger.info("Shutting down Nest Protect MCP server...")
        if hasattr(self, '_session') and self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP session closed")
        self._initialized = False
        logger.info("Nest Protect MCP server shutdown complete")
    
    def _setup_routes(self):
        """Set up MCP message handlers."""
        # This method is kept for backward compatibility
        # All routes are now registered in _register_message_handlers()
        pass
    
    def _register_message_handlers(self):
        """Register message handlers for MCP methods."""
        self._message_handlers = {
            "ping": self._handle_ping,
            "get_device": self._handle_get_device,
            "get_devices": self._get_devices,
            "get_alarm_state": self._handle_get_alarm_state,
            "hush_alarm": self._handle_hush_alarm,
            "run_test": self._handle_run_test,
        }
        
    def _register_tools(self):
        """Register tools for FastMCP 2.12."""
        @self.tool("get_devices")
        async def get_devices(params: EmptyParams) -> List[Dict[str, Any]]:
            """Get a list of all Nest Protect devices."""
            return await self._get_devices()
        
        @self.tool("get_device")
        async def get_device(params: DeviceIdParams) -> Dict[str, Any]:
            """Get detailed information about a specific device."""
            return await self._get_device(params.device_id)
            
        @self.tool("silence_alarm")
        async def silence_alarm(params: SilenceAlarmParams) -> Dict[str, Any]:
            """Silence the alarm on a specific device."""
            return await self._handle_hush_alarm(params.device_id)
    
    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping messages to keep the connection alive."""
        return {
            "pong": True,
            "timestamp": params.get("timestamp"),
            "server_time": time.time()
        }
    
    async def handle_message(self, message: McpMessage) -> Dict[str, Any]:
        """Handle an incoming MCP message."""
        try:
            method = message.method
            params = message.params or {}
            
            logger.debug(f"Received MCP message - Method: {method}, Params: {params}")
            
            # Find the handler for this method
            handler = self._message_handlers.get(method)
            if not handler:
                raise ValueError(f"Unknown method: {method}")
            
            # Call the handler
            result = await handler(**params)
            
            return {
                "jsonrpc": "2.0",
                "id": message.id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling MCP message: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": getattr(message, 'id', None),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
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

from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

# For backward compatibility
NestProtectServer = NestProtectMCP

def create_app():
    """Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Create FastAPI app with lifespan management
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Initialize the server
        server = NestProtectMCP({})
        try:
            # Start the server
            await server.initialize()
            
            # Make server available in app state
            app.state.server = server
            
            # Log successful startup
            logger.info("Nest Protect MCP Server started successfully")
            
            yield
            
        except Exception as e:
            logger.error("Failed to start server: %s", str(e), exc_info=True)
            raise
            
        finally:
            # Cleanup
            try:
                await server.shutdown()
                logger.info("Server shutdown complete")
            except Exception as e:
                logger.error("Error during server shutdown: %s", str(e), exc_info=True)

    # Create FastAPI app with OpenAPI configuration
    app = FastAPI(
        title="Nest Protect MCP Server",
        description="REST API for Nest Protect MCP Server with FastMCP 2.12 support",
        version="1.0.0",
        contact={
            "name": "Support",
            "url": "https://github.com/sandraschi/nest-protect-mcp/issues"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        lifespan=lifespan
    )

    # API Routes
    @app.get(
        "/api/version", 
        tags=["API"],
        summary="Get API version information",
        response_description="API version information"
    )
    async def get_version() -> Dict[str, str]:
        """Get API version information.
        
        Returns:
            dict: API version information including name, version, and MCP version
        """
        return {
            "name": "Nest Protect MCP Server",
            "version": "1.0.0",
            "mcp_version": "2.12.0",
            "docs": "/docs"
        }
    
    # Health check endpoint
    @app.get(
        "/health",
        tags=["System"],
        summary="Health check endpoint",
        response_description="Server health status"
    )
    async def health_check() -> Dict[str, str]:
        """Check if the server is running."""
        return {"status": "ok"}
    
    return app

# Create FastAPI app instance
app = create_app()

# Create server function for MCP compatibility
def create_server(config: Optional[Dict[str, Any]] = None) -> NestProtectMCP:
    """Create and configure the NestProtectMCP server.
    
    This function creates a new instance of NestProtectMCP with the provided
    configuration. It's used for both standalone MCP server operation and
    integration with the FastAPI application.
    
    Args:
        config: Optional configuration dictionary with the following keys:
            - client_id: Nest OAuth client ID
            - client_secret: Nest OAuth client secret
            - project_id: Google Cloud project ID
            - log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            - state_file: Path to the state file for persistence
            - token_expiry_buffer: Buffer time in seconds before token expiry (default: 300)
            
    Returns:
        NestProtectMCP: Configured server instance
        
    Example:
        ```python
        config = {
            "client_id": "your-client-id",
            "client_secret": "your-client-secret",
            "project_id": "your-project-id",
            "log_level": "INFO"
        }
        server = create_server(config)
        ```
    """
    # Set default config if none provided
    if config is None:
        config = {}
        
    # Initialize and return the server
    server = NestProtectMCP(config)
    return server

# Server instance will be created when needed
server = None
