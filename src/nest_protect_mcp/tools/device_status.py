"""Device status tools for Nest Protect MCP."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class EmptyParams(BaseModel):
    """Empty parameters for tools that don't need input."""
    pass

class DeviceIdParams(BaseModel):
    """Parameters for device-specific operations."""
    device_id: str = Field(..., description="ID of the device")

class DeviceEventsParams(BaseModel):
    """Parameters for getting device events."""
    device_id: str = Field(..., description="ID of the device")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of events to return")

async def list_devices() -> Dict[str, Any]:
    """List all Nest Protect devices."""
    from ..state_manager import get_app_state
    import aiohttp
    
    state = get_app_state()
    
    if not state.access_token:
        return {"status": "error", "message": "Not authenticated with Nest API"}
    
    try:
        url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{state.config.project_id}/devices"
        headers = {"Authorization": f"Bearer {state.access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    devices = data.get("devices", [])
                    return {
                        "status": "success",
                        "count": len(devices),
                        "devices": [{
                            "id": d["name"].split("/")[-1],
                            "type": d.get("type", "").split(".")[-1],
                            "name": d.get("traits", {}).get("sdm.devices.traits.Info", {}).get("customName", ""),
                            "model": d.get("traits", {}).get("sdm.devices.traits.Info", {}).get("modelNumber", ""),
                            "online": d.get("traits", {}).get("sdm.devices.traits.Connectivity", {}).get("status") == "ONLINE"
                        } for d in devices]
                    }
                else:
                    error = await response.json()
                    return {"status": "error", "message": "Failed to list devices", "error": error.get("error", {}).get("message")}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list devices: {str(e)}"}

async def get_device_status(device_id: str) -> Dict[str, Any]:
    """Get status of a specific Nest Protect device."""
    from ..state_manager import get_app_state
    import aiohttp
    
    state = get_app_state()
    
    if not state.access_token:
        return {"status": "error", "message": "Not authenticated with Nest API"}
    
    try:
        url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{state.config.project_id}/devices/{device_id}"
        headers = {"Authorization": f"Bearer {state.access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    device = await response.json()
                    traits = device.get("traits", {})
                    info = traits.get("sdm.devices.traits.Info", {})
                    connectivity = traits.get("sdm.devices.traits.Connectivity", {})
                    
                    status = {
                        "id": device_id,
                        "name": info.get("customName", ""),
                        "model": info.get("modelNumber", ""),
                        "online": connectivity.get("status") == "ONLINE",
                        "battery": {
                            "level": traits.get("sdm.devices.traits.Battery", {}).get("batteryLevel"),
                            "status": traits.get("sdm.devices.traits.Battery", {}).get("batteryStatus")
                        },
                        "alarm": {
                            "status": traits.get("sdm.devices.traits.SafetyAlarm", {}).get("alarmStatus"),
                            "last_event": traits.get("sdm.devices.traits.SafetyAlarm", {}).get("lastEvent")
                        },
                        "smoke": {
                            "status": traits.get("sdm.devices.traits.Smoke", {}).get("smokeStatus"),
                            "last_event": traits.get("sdm.devices.traits.Smoke", {}).get("lastEvent")
                        },
                        "co": {
                            "status": traits.get("sdm.devices.traits.CarbonMonoxide", {}).get("coStatus"),
                            "level_ppm": traits.get("sdm.devices.traits.CarbonMonoxide", {}).get("coLevel"),
                            "last_event": traits.get("sdm.devices.traits.CarbonMonoxide", {}).get("lastEvent")
                        },
                        "heat": {
                            "status": traits.get("sdm.devices.traits.Heat", {}).get("heatStatus"),
                            "temperature_c": traits.get("sdm.devices.traits.Temperature", {}).get("temperature"),
                            "humidity": traits.get("sdm.devices.traits.Humidity", {}).get("humidity")
                        },
                        "last_update": device.get("lastEventTime")
                    }
                    
                    return {"status": "success", "device": status}
                else:
                    error = await response.json()
                    return {"status": "error", "message": "Failed to get device status", "error": error.get("error", {}).get("message")}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get device status: {str(e)}"}

async def get_device_events(device_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get recent events for a Nest Protect device."""
    from ..state_manager import get_app_state
    import aiohttp
    
    state = get_app_state()
    
    if not state.access_token:
        return {"status": "error", "message": "Not authenticated with Nest API"}
    
    try:
        url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{state.config.project_id}/devices/{device_id}/events"
        headers = {"Authorization": f"Bearer {state.access_token}"}
        params = {"pageSize": min(max(1, limit), 100)}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get("events", [])
                    
                    formatted_events = []
                    for event in events:
                        event_type = event.get("resourceType", "").split(".")[-1]
                        event_data = event.get("traits", {})
                        
                        formatted_events.append({
                            "event_id": event.get("eventId"),
                            "type": event_type,
                            "timestamp": event.get("timestamp"),
                            "data": event_data
                        })
                    
                    return {
                        "status": "success",
                        "count": len(formatted_events),
                        "events": formatted_events
                    }
                else:
                    error = await response.json()
                    return {"status": "error", "message": "Failed to get device events", "error": error.get("error", {}).get("message")}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get device events: {str(e)}"}
