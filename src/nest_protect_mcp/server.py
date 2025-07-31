"""
Nest Protect MCP Server

This module implements the main server for interacting with Nest Protect devices
using the Message Control Protocol (MCP).
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable, TypeVar, cast

from fastmcp import FastMCP, McpMessage, McpServer
from pydantic import ValidationError

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
    """MCP server for interacting with Nest Protect devices."""
    
    def __init__(self, config: Union[Dict[str, Any], ProtectConfig], **kwargs):
        """Initialize the Nest Protect MCP server.
        
        Args:
            config: Configuration dictionary or ProtectConfig instance
            **kwargs: Additional arguments to pass to the base class
        """
        # Initialize configuration
        if isinstance(config, dict):
            self.config = ProtectConfig(**config)
        else:
            self.config = config
        
        # Initialize state
        self._devices: Dict[str, ProtectDeviceState] = {}
        self._message_handlers: Dict[str, MessageHandler] = {}
        self._event_listeners: List[Callable[[ProtectEvent], None]] = []
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Initialize MCP server
        super().__init__(
            name="nest_protect",
            version="0.1.0",
            description="MCP server for Nest Protect devices",
            **kwargs
        )
        
        # Register message handlers
        self._register_message_handlers()
    
    # ===== Public API =====
    
    async def start(self) -> None:
        """Start the Nest Protect MCP server."""
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
        """Stop the Nest Protect MCP server."""
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
        """Get the current state of all Nest Protect devices.
        
        Returns:
            List of device states
        """
        return list(self._devices.values())
    
    async def get_device(self, device_id: str) -> Optional[ProtectDeviceState]:
        """Get the current state of a specific Nest Protect device.
        
        Args:
            device_id: The ID of the device to get
            
        Returns:
            The device state, or None if not found
        """
        return self._devices.get(device_id)
    
    async def send_command(self, command: Union[Dict[str, Any], ProtectCommand]) -> bool:
        """Send a command to a Nest Protect device.
        
        Args:
            command: The command to send
            
        Returns:
            True if the command was sent successfully, False otherwise
            
        Raises:
            NestInvalidCommandError: If the command is invalid
            NestDeviceNotFoundError: If the device is not found
            NestConnectionError: If there's a connection error
        """
        # Parse command
        if isinstance(command, dict):
            try:
                command = ProtectCommand(**command)
            except ValidationError as e:
                raise NestInvalidCommandError(f"Invalid command: {e}")
        
        logger.info(f"Sending command to device {command.device_id or 'all'}: {command.command}")
        
        try:
            # Send command to device(s)
            if command.device_id:
                # Send to specific device
                if command.device_id not in self._devices:
                    raise NestDeviceNotFoundError(f"Device {command.device_id} not found")
                
                success = await self._send_device_command(command.device_id, command)
            else:
                # Send to all devices
                success = True
                for device_id in self._devices:
                    if not await self._send_device_command(device_id, command):
                        success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending command: {e}", exc_info=True)
            raise
    
    def add_event_listener(self, callback: Callable[[ProtectEvent], None]) -> None:
        """Add an event listener.
        
        Args:
            callback: Function to call when an event occurs
        """
        if callback not in self._event_listeners:
            self._event_listeners.append(callback)
    
    def remove_event_listener(self, callback: Callable[[ProtectEvent], None]) -> None:
        """Remove an event listener.
        
        Args:
            callback: Function to remove
        """
        if callback in self._event_listeners:
            self._event_listeners.remove(callback)
    
    # ===== Private Methods =====
    
    def _register_message_handlers(self) -> None:
        """Register MCP message handlers."""
        self._message_handlers = {
            "get_devices": self._handle_get_devices,
            "get_device": self._handle_get_device,
            "send_command": self._handle_send_command,
            "get_alarm_state": self._handle_get_alarm_state,
            "hush_alarm": self._handle_hush_alarm,
            "run_test": self._handle_run_test,
        }
    
    async def _init_nest_connection(self) -> None:
        """Initialize connection to the Nest API."""
        logger.info("Initializing Nest API connection")
        # TODO: Implement actual Nest API connection
        # This is a placeholder for the actual implementation
        await asyncio.sleep(0.1)
        logger.info("Nest API connection initialized")
    
    async def _close_nest_connection(self) -> None:
        """Close the connection to the Nest API."""
        logger.info("Closing Nest API connection")
        # TODO: Implement actual Nest API disconnection
        # This is a placeholder for the actual implementation
        await asyncio.sleep(0.1)
        logger.info("Nest API connection closed")
    
    async def _update_loop(self) -> None:
        """Background task to update device states."""
        logger.info("Starting device update loop")
        
        try:
            while self._running:
                try:
                    await self._update_devices()
                except Exception as e:
                    logger.error(f"Error updating devices: {e}", exc_info=True)
                
                # Wait for the next update
                await asyncio.sleep(self.config.update_interval)
                
        except asyncio.CancelledError:
            logger.info("Device update loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Device update loop failed: {e}", exc_info=True)
            raise
        finally:
            logger.info("Device update loop stopped")
    
    async def _update_devices(self) -> None:
        """Update the state of all devices."""
        # TODO: Implement actual device state updates from Nest API
        # This is a placeholder for the actual implementation
        
        # Simulate some devices for testing
        if not self._devices:
            self._devices = {
                "protect_kitchen": ProtectDeviceState(
                    device_id="protect_kitchen",
                    name="Kitchen Protect",
                    model="Nest Protect 2nd Gen",
                    serial_number="18B4300000ABCDEF",
                    online=True,
                    battery_health=ProtectBatteryState.OK,
                    co_alarm_state=ProtectAlarmState.OK,
                    smoke_alarm_state=ProtectAlarmState.OK,
                    heat_alarm_state=ProtectAlarmState.OK,
                    battery_level=85,
                    temperature=22.5,
                    humidity=45.0,
                    last_connection=datetime.now(timezone.utc),
                    software_version="3.1.9",
                    wifi_ip="192.168.1.100",
                    wifi_ssid="MyWiFi"
                ),
                "protect_living_room": ProtectDeviceState(
                    device_id="protect_living_room",
                    name="Living Room Protect",
                    model="Nest Protect 3rd Gen",
                    serial_number="18B4300000FEDCBA",
                    online=True,
                    battery_health=ProtectBatteryState.REPLACE,
                    co_alarm_state=ProtectAlarmState.OK,
                    smoke_alarm_state=ProtectAlarmState.OK,
                    heat_alarm_state=ProtectAlarmState.OK,
                    battery_level=15,
                    temperature=21.8,
                    humidity=42.0,
                    last_connection=datetime.now(timezone.utc),
                    software_version="3.2.1",
                    wifi_ip="192.168.1.101",
                    wifi_ssid="MyWiFi"
                )
            }
        else:
            # Update existing devices
            now = datetime.now(timezone.utc)
            for device in self._devices.values():
                device.last_connection = now
                
                # Simulate some state changes
                if device.device_id == "protect_kitchen":
                    # Simulate small temperature changes
                    if device.temperature is not None:
                        device.temperature += (0.1 if device.temperature < 25.0 else -0.1)
                
                elif device.device_id == "protect_living_room":
                    # Simulate battery drain
                    if device.battery_level is not None and device.battery_level > 0:
                        device.battery_level -= 1
                        
                        # Update battery health based on level
                        if device.battery_level <= 10:
                            device.battery_health = ProtectBatteryState.CRITICAL
                        elif device.battery_level <= 20:
                            device.battery_health = ProtectBatteryState.REPLACE
    
    async def _send_device_command(self, device_id: str, command: ProtectCommand) -> bool:
        """Send a command to a specific device.
        
        Args:
            device_id: The ID of the device to send the command to
            command: The command to send
            
        Returns:
            True if the command was sent successfully, False otherwise
        """
        # TODO: Implement actual device command sending
        # This is a placeholder for the actual implementation
        
        logger.info(f"Sending {command.command} command to device {device_id}")
        
        # Simulate command processing
        await asyncio.sleep(0.1)
        
        # Update device state based on command
        device = self._devices.get(device_id)
        if not device:
            return False
        
        if command.command == "hush":
            # Simulate hushing an alarm
            if device.co_alarm_state == ProtectAlarmState.EMERGENCY:
                device.co_alarm_state = ProtectAlarmState.WARNING
            if device.smoke_alarm_state == ProtectAlarmState.EMERGENCY:
                device.smoke_alarm_state = ProtectAlarmState.WARNING
            
            self._fire_event(ProtectEvent(
                event_id=f"event_{int(datetime.now().timestamp())}",
                device_id=device_id,
                event_type="alarm_hushed",
                event_data={"hush_duration": command.params.get("duration", 15 * 60)}
            ))
            
        elif command.command == "test":
            # Simulate running a test
            self._fire_event(ProtectEvent(
                event_id=f"event_{int(datetime.now().timestamp())}",
                device_id=device_id,
                event_type="test_started",
                event_data={"test_type": command.params.get("type", "full")}
            ))
            
            # Simulate test completion after a delay
            async def complete_test():
                await asyncio.sleep(5)
                self._fire_event(ProtectEvent(
                    event_id=f"event_{int(datetime.now().timestamp())}",
                    device_id=device_id,
                    event_type="test_completed",
                    event_data={"result": "success"}
                ))
            
            asyncio.create_task(complete_test())
            
        elif command.command == "locate":
            # Simulate device location sound
            self._fire_event(ProtectEvent(
                event_id=f"event_{int(datetime.now().timestamp())}",
                device_id=device_id,
                event_type="locate",
                event_data={"duration": command.params.get("duration", 10)}
            ))
            
        return True
    
    def _fire_event(self, event: ProtectEvent) -> None:
        """Fire an event to all listeners."""
        logger.debug(f"Firing event: {event.event_type} for device {event.device_id}")
        for callback in self._event_listeners:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}", exc_info=True)
    
    # ===== MCP Message Handlers =====
    
    async def _handle_get_devices(self, message: McpMessage) -> Dict[str, Any]:
        """Handle get_devices message."""
        devices = await self.get_devices()
        return {
            "status": "success",
            "devices": [device.dict() for device in devices]
        }
    
    async def _handle_get_device(self, message: McpMessage) -> Dict[str, Any]:
        """Handle get_device message."""
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
        """Handle send_command message."""
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
        """Handle get_alarm_state message."""
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
        """Handle hush_alarm message."""
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
        """Handle run_test message."""
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
