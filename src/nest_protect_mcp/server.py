"""
Nest Protect MCP Server

This module implements the main server for interacting with Nest Protect devices
using the Message Control Protocol (MCP).
"""
import asyncio
import json
import logging
import time
import aiohttp
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable, TypeVar, cast

from fastapi import FastAPI
from fastmcp.server import McpServer
from fastmcp.messages import McpMessage
from fastmcp.fastmcp import FastMCP
from pydantic import ValidationError

from .state_manager import state_manager, lifespan

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

class NestProtectMCP(McpServer):
# MCP server for interacting with Nest Protect devices with stateful support
    
    def __init__(self, config: Union[Dict[str, Any], ProtectConfig], **kwargs):
        """Initialize the Nest Protect MCP server.
        
        Args:
            config: Configuration dictionary or ProtectConfig instance
            **kwargs: Additional arguments to pass to the base class
        """
        # Initialize the base class with FastAPI app and state management
        app = FastAPI(lifespan=lifespan)
        super().__init__("nest-protect", app=app, **kwargs)
        
        # Store state manager reference
        self._state_manager = state_manager
        
        # Load configuration
        if isinstance(config, dict):
            self._config = ProtectConfig(**config)
        else:
            self._config = config
            
        # Initialize instance variables
        self._session = None
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = 0
        self._devices = {}
        self._initialized = False
        
        # State keys for the state manager
        self._state_keys = {
            'access_token': 'nest_access_token',
            'refresh_token': 'nest_refresh_token',
            'token_expires_at': 'nest_token_expires_at',
            'devices': 'nest_devices'
        }
        
        # Initialize FastMCP server with state management
        self._fastmcp = FastMCP(
            name="nest_protect",
            version="0.1.0",
            description="MCP server for Nest Protect devices",
            state_manager=self._state_manager
        )
        
        # Load auth state
        asyncio.create_task(self._load_auth_state())
        
        # Register message handlers
        self._register_message_handlers()
    
    async def _ensure_session(self) -> None:
    # Ensure we have a valid session and access token
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
            raise NestAuthError("No refresh token available")
            
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
        try:
            response = await self._make_request('GET', f'enterprises/{self._config.project_id}/devices')
            return response.get('devices', [])
        except Exception as e:
            logger.error(f"Failed to get devices from API: {e}")
            raise NestConnectionError(f"Failed to get devices: {e}")
    
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
    
    async def _handle_get_devices(self, message: McpMessage) -> Dict[str, Any]:
    # Handle GET /devices endpoint
        devices = await self.get_devices()
        return {
            "status": "success",
            "data": [device.dict() for device in devices]
        }
    
    async def _handle_get_device_status(self, message: McpMessage) -> Dict[str, Any]:
    # Handle GET /device/{device_id}/status endpoint
        device_id = message.params.get("device_id")
        if not device_id:
            return {"status": "error", "message": "Device ID is required"}
        
        device = await self.get_device(device_id)
        if not device:
            return {"status": "error", "message": f"Device {device_id} not found"}
        
        return {"status": "success", "data": device.dict()}
    
    async def _handle_get_alarms(self, message: McpMessage) -> Dict[str, Any]:
    # Handle GET /alarms endpoint
        devices = await self.get_devices()
        alarms = []
        
        for device in devices:
            if device.smoke_alarm_state in [ProtectAlarmState.WARNING, ProtectAlarmState.EMERGENCY]:
                alarms.append({
                    "device_id": device.device_id,
                    "device_name": device.name,
                    "alarm_type": "smoke",
                    "state": device.smoke_alarm_state,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            if device.co_alarm_state in [ProtectAlarmState.WARNING, ProtectAlarmState.EMERGENCY]:
                alarms.append({
                    "device_id": device.device_id,
                    "device_name": device.name,
                    "alarm_type": "carbon_monoxide",
                    "state": device.co_alarm_state,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        return {"status": "success", "data": alarms}
    
    async def _handle_hush_alarm(self, message: McpMessage) -> Dict[str, Any]:
    # Handle POST /device/{device_id}/hush endpoint
        device_id = message.params.get("device_id")
        if not device_id:
            return {"status": "error", "message": "Device ID is required"}
        
        duration = message.params.get("duration", 10)  # Default 10 minutes
        
        try:
            success = await self.send_command(ProtectCommand(
                command="hush",
                device_id=device_id,
                params={"duration": duration}
            ))
            
            if success:
                return {
                    "status": "success",
                    "message": f"Alarm hush command sent to device {device_id} for {duration} minutes"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to send hush command to device {device_id}"
                }
                
        except Exception as e:
            logger.error(f"Error hushing alarm: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to hush alarm: {str(e)}"
            }
    
    # === Server Lifecycle ===
    
    async def start(self) -> None:
    # Start the Nest Protect MCP server
        if self._running:
            logger.warning("Server is already running")
            return
        
        logger.info("Starting Nest Protect MCP server")
        
        try:
            # Initialize connection to Nest API
            await self._init_nest_connection()
            
            # Start background tasks
            self._running = True
            self._update_task = asyncio.create_task(self._update_loop())
            
            # Start MCP server
            await super().start()
            
            logger.info("Nest Protect MCP server started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Nest Protect MCP server: {e}", exc_info=True)
            await self.stop()
            raise
    
    async def stop(self) -> None:
    # Stop the Nest Protect MCP server
        if not self._running:
            return
        
        logger.info("Stopping Nest Protect MCP server")
        self._running = False
        
        # Cancel background tasks
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
        
        # Close Nest API connection
        await self._close_nest_connection()
        
        # Stop MCP server
        await super().stop()
        
        logger.info("Nest Protect MCP server stopped")
    
    async def get_devices(self) -> List[ProtectDeviceState]:
    # Get the current state of all Nest Protect devices
        return list(self._devices.values())
    
    async def get_device(self, device_id: str) -> Optional[ProtectDeviceState]:
    # Get the current state of a specific Nest Protect device
        logger.info(f"Attempting to hush alarm on device {device_id}")
        
        # Check if device exists
        if device_id not in self._devices:
            logger.warning(f"Device {device_id} not found")
            raise NestDeviceNotFound(f"Device {device_id} not found")
        
        try:
            # Execute the hush command via the Nest API
            response = await self._make_request(
                'POST',
                f'enterprises/{self.config.project_id}/devices/{device_id}:executeCommand',
                json={
                    'command': 'sdm.devices.commands.SafetyHush.Hush',
                    'params': {}
                }
            )
            
            # Check if the command was successful
            if response.get('results', {}).get('status') == 'SUCCESS':
                logger.info(f"Successfully hushed alarm on device {device_id}")
                
                # Update the local device state
                device = self._devices[device_id]
                old_state = device.copy()
                device.co_alarm_state = ProtectAlarmState.OFF
                device.smoke_alarm_state = ProtectAlarmState.OFF
                device.heat_alarm_state = ProtectAlarmState.OFF
                
                # Emit an event for the state change
                event = ProtectEvent(
                    event_type="alarm_hushed",
                    device_id=device_id,
                    timestamp=datetime.now(timezone.utc),
                    data={
                        "device": device.dict(),
                        "previous_state": old_state.dict()
                    }
                )
                self._emit_event(event)
                
                return True
            else:
                logger.error(f"Failed to hush alarm on device {device_id}: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error hushing alarm on device {device_id}: {e}", exc_info=True)
            raise NestConnectionError(f"Failed to hush alarm: {e}")

    async def _send_device_command(self, device_id: str, command: ProtectCommand) -> bool:
    # Send a command to a specific device
        logger.info(f"Sending command {command.command} to device {device_id}")
        
        # Check if device exists
        if device_id not in self._devices:
            logger.warning(f"Device {device_id} not found")
            raise NestDeviceNotFound(f"Device {device_id} not found")
        
        try:
            if command.command == "hush":
                # Handle hush command
                return await self._hush_alarm(device_id)
                
            elif command.command == "test":
                # Handle test command
                logger.info(f"Starting test on device {device_id}")
                
                # Execute the test command via the Nest API
                response = await self._make_request(
                    'POST',
                    f'enterprises/{self.config.project_id}/devices/{device_id}:executeCommand',
                    json={
                        'command': 'sdm.devices.commands.SafetyTest.Test',
                        'params': {}
                    }
                )
                
                # Check if the command was successful
                if response.get('results', {}).get('status') == 'SUCCESS':
                    logger.info(f"Successfully started test on device {device_id}")
                    
                    # Emit an event for the test start
                    event = ProtectEvent(
                        event_type="test_started",
                        device_id=device_id,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "test_type": command.params.get("test_type", "manual")
                        }
                    )
                    self._emit_event(event)
                    
                    return True
                else:
                    logger.error(f"Failed to start test on device {device_id}: {response}")
                    return False
                    
            else:
                logger.warning(f"Unsupported command: {command.command}")
                raise NestInvalidCommandError(f"Unsupported command: {command.command}")
                
        except Exception as e:
            logger.error(f"Error sending command to device {device_id}: {e}", exc_info=True)
            if not isinstance(e, (NestDeviceNotFound, NestInvalidCommandError)):
                raise NestConnectionError(f"Failed to send command: {e}")
            raise
    
    def _fire_event(self, event: ProtectEvent) -> None:
    # Fire an event to all listeners
        logger.debug(f"Firing event: {event.event_type} for device {event.device_id}")
        for callback in self._event_listeners:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}", exc_info=True)
    
    # ===== MCP Message Handlers =====
    
    async def _handle_get_devices(self, message: McpMessage) -> Dict[str, Any]:
    # Handle get_devices message
        devices = await self.get_devices()
        return {
            "status": "success",
            "devices": [device.dict() for device in devices]
        }
    
    async def _handle_get_device(self, message: McpMessage) -> Dict[str, Any]:
    # Handle get_device message
        device_id = message.params.get("device_id")
        if not device_id:
            return {"status": "error", "message": "device_id is required"}
        
        device = await self.get_device(device_id)
        if not device:
            return {"status": "error", "message": f"Device {device_id} not found"}
        
        return {
            "status": "success",
            "device": device.dict()
        }
    
    async def _handle_send_command(self, message: McpMessage) -> Dict[str, Any]:
    # Handle send_command message
        try:
            command = ProtectCommand(**message.params)
            success = await self.send_command(command)
            return {
                "status": "success" if success else "error",
                "message": "Command sent successfully" if success else "Failed to send command"
            }
        except ValidationError as e:
            return {"status": "error", "message": f"Invalid command: {e}"}
        except NestDeviceNotFoundError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error sending command: {e}", exc_info=True)
            return {"status": "error", "message": f"Error sending command: {e}"}
    
    async def _handle_get_alarm_state(self, message: McpMessage) -> Dict[str, Any]:
    # Handle get_alarm_state message
        device_id = message.params.get("device_id")
        if not device_id:
            return {"status": "error", "message": "device_id is required"}
        
        device = await self.get_device(device_id)
        if not device:
            return {"status": "error", "message": f"Device {device_id} not found"}
        
        return {
            "status": "success",
            "device_id": device_id,
            "co_alarm_state": device.co_alarm_state,
            "smoke_alarm_state": device.smoke_alarm_state,
            "heat_alarm_state": device.heat_alarm_state,
            "battery_health": device.battery_health
        }
    
    async def _handle_hush_alarm(self, message: McpMessage) -> Dict[str, Any]:
    # Handle hush_alarm message
        device_id = message.params.get("device_id")
        if not device_id:
            return {"status": "error", "message": "device_id is required"}
        
        duration = message.params.get("duration", 15 * 60)  # Default 15 minutes
        
        try:
            success = await self.send_command({
                "command": "hush",
                "device_id": device_id,
                "params": {"duration": duration}
            })
            
            return {
                "status": "success" if success else "error",
                "message": "Alarm hushed successfully" if success else "Failed to hush alarm"
            }
            
        except Exception as e:
            logger.error(f"Error hushing alarm: {e}", exc_info=True)
            return {"status": "error", "message": f"Error hushing alarm: {e}"}
    
    async def _handle_run_test(self, message: McpMessage) -> Dict[str, Any]:
    # Handle run_test message
        device_id = message.params.get("device_id")
        if not device_id:
            return {"status": "error", "message": "device_id is required"}
        
        test_type = message.params.get("type", "full")  # full, smoke, co, etc.
        
        try:
            success = await self.send_command({
                "command": "test",
                "device_id": device_id,
                "params": {"type": test_type}
            })
            
            return {
                "status": "success" if success else "error",
                "message": "Test started successfully" if success else "Failed to start test"
            }
            
        except Exception as e:
            logger.error(f"Error running test: {e}", exc_info=True)
            return {"status": "error", "message": f"Error running test: {e}"}

# For backward compatibility
NestProtectServer = NestProtectMCP

# Create FastAPI app with lifespan management
app = FastAPI(lifespan=lifespan)

# Initialize the MCP server
mcp_server = None

@app.on_event("startup")
async def startup_event():
## Initialize the MCP server and load startup
    global mcp_server
    try:
        # Load configuration (you should implement this)
        config = {}
        
        # Initialize MCP server
        mcp_server = NestProtectMCP(config)
        await mcp_server.initialize()
        
        # Register MCP routes
        app.include_router(mcp_server.router, prefix="/mcp")
        
        logger.info("Nest Protect MCP server started")
    except Exception as e:
        logger.error(f"Failed to start Nest Protect MCP: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
## Clean up resources on shutdown
    global mcp_server
    if mcp_server:
        await mcp_server.close()
        logger.info("Nest Protect MCP server stopped")
