"""
Nest Protect MCP Tools

This module defines all the MCP tools for interacting with Nest Protect devices.
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class DeviceType(str, Enum):
    SMOKE_ALARM = "sdm.devices.types.SMOKE_ALARM"
    CO_ALARM = "sdm.devices.types.COA_ALARM"
    CAMERA = "sdm.devices.types.CAMERA"
    THERMOSTAT = "sdm.devices.types.THERMOSTAT"
    DISPLAY = "sdm.devices.types.DISPLAY"
    DOORBELL = "sdm.devices.types.DOORBELL"

class AlarmState(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class BatteryState(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    CRITICAL = "CRITICAL"

class DeviceInfo(BaseModel):
    """Information about a Nest Protect device."""
    id: str = Field(..., description="The unique identifier for the device")
    name: str = Field(..., description="The display name of the device")
    type: DeviceType = Field(..., description="The type of the device")
    online: bool = Field(..., description="Whether the device is online")
    battery_state: Optional[BatteryState] = Field(None, description="Battery state if applicable")
    alarm_state: Optional[AlarmState] = Field(None, description="Current alarm state")
    last_connection: Optional[str] = Field(None, description="Last connection timestamp")

class GetDevicesTool(BaseModel):
    """Get a list of all Nest Protect devices."""
    pass

class GetDeviceTool(BaseModel):
    """Get detailed information about a specific Nest Protect device."""
    device_id: str = Field(..., description="The ID of the device to get information about")

class SilenceAlarmTool(BaseModel):
    """Silence the alarm on a specific Nest Protect device."""
    device_id: str = Field(..., description="The ID of the device to silence")
    duration_seconds: int = Field(300, description="Duration to silence the alarm in seconds", ge=60, le=600)

class GetDeviceHistoryTool(BaseModel):
    """Get the history of events for a specific Nest Protect device."""
    device_id: str = Field(..., description="The ID of the device to get history for")
    start_time: Optional[str] = Field(None, description="Start time for the history query (ISO 8601 format)")
    end_time: Optional[str] = Field(None, description="End time for the history query (ISO 8601 format)")
    max_results: int = Field(10, description="Maximum number of results to return", ge=1, le=100)

# Tool schemas for MCP
tool_schemas = {
    "get_devices": {
        "name": "get_devices",
        "description": "Get a list of all Nest Protect devices",
        "parameters": {},
        "returns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "online": {"type": "boolean"},
                    "battery_state": {"type": "string", "nullable": True},
                    "alarm_state": {"type": "string", "nullable": True},
                    "last_connection": {"type": "string", "nullable": True}
                },
                "required": ["id", "name", "type", "online"]
            }
        }
    },
    "get_device": {
        "name": "get_device",
        "description": "Get detailed information about a specific Nest Protect device",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "The ID of the device to get information about"}
            },
            "required": ["device_id"]
        },
        "returns": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "online": {"type": "boolean"},
                "battery_state": {"type": "string", "nullable": True},
                "alarm_state": {"type": "string", "nullable": True},
                "last_connection": {"type": "string", "nullable": True},
                "details": {"type": "object"}
            },
            "required": ["id", "name", "type", "online"]
        }
    },
    "silence_alarm": {
        "name": "silence_alarm",
        "description": "Silence the alarm on a specific Nest Protect device",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "The ID of the device to silence"},
                "duration_seconds": {"type": "integer", "description": "Duration to silence the alarm in seconds", "default": 300, "minimum": 60, "maximum": 600}
            },
            "required": ["device_id"]
        },
        "returns": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"}
            },
            "required": ["success"]
        }
    },
    "get_device_history": {
        "name": "get_device_history",
        "description": "Get the history of events for a specific Nest Protect device",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "The ID of the device to get history for"},
                "start_time": {"type": "string", "description": "Start time for the history query (ISO 8601 format)", "nullable": True},
                "end_time": {"type": "string", "description": "End time for the history query (ISO 8601 format)", "nullable": True},
                "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 10, "minimum": 1, "maximum": 100}
            },
            "required": ["device_id"]
        },
        "returns": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string"},
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string"},
                            "event_type": {"type": "string"},
                            "description": {"type": "string"},
                            "details": {"type": "object"}
                        },
                        "required": ["timestamp", "event_type"]
                    }
                }
            },
            "required": ["device_id", "events"]
        }
    }
}
