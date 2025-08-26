"""Device control tools for Nest Protect MCP."""

from typing import Dict, Any, Optional, Literal
from ..tools import tool

@tool(name="hush_alarm", description="Silence an active alarm on a Nest Protect device", parameters={"device_id": {"type": "string", "description": "ID of the device to hush", "required": True}, "duration_seconds": {"type": "integer", "description": "Duration to hush in seconds (30-300)", "minimum": 30, "maximum": 300, "default": 180}}, examples=["hush_alarm('device123')", "hush_alarm(device_id='device123', duration_seconds=120)"])
async def hush_alarm(device_id: str, duration_seconds: int = 180) -> Dict[str, Any]:
    """Silence an active alarm on a Nest Protect device."""
    from ..server import app
    
    if not hasattr(app.state, 'access_token') or not app.state.access_token:
        return {"status": "error", "message": "Not authenticated with Nest API"}
    
    try:
        url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{app.state.config.project_id}/devices/{device_id}:executeCommand"
        headers = {"Authorization": f"Bearer {app.state.access_token}"}
        payload = {
            "command": "sdm.devices.commands.SafetyHush.Hush",
            "params": {"duration": f"{duration_seconds}s"}
        }
        
        async with app.state.http_session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                return {"status": "success", "message": f"Alarm hushed for {duration_seconds} seconds", "device_id": device_id}
            else:
                error = await response.json()
                return {"status": "error", "message": "Failed to hush alarm", "error": error.get("error", {}).get("message")}
    except Exception as e:
        return {"status": "error", "message": f"Failed to hush alarm: {str(e)}"}

@tool(name="run_safety_check", description="Run a safety check on a Nest Protect device", parameters={"device_id": {"type": "string", "description": "ID of the device to test", "required": True}, "test_type": {"type": "string", "description": "Type of test to run", "enum": ["full", "smoke", "co", "heat"], "default": "full"}}, examples=["run_safety_check('device123')", "run_safety_check(device_id='device123', test_type='smoke')"])
async def run_safety_check(device_id: str, test_type: Literal["full", "smoke", "co", "heat"] = "full") -> Dict[str, Any]:
    """Run a safety check on a Nest Protect device."""
    from ..server import app
    
    if not hasattr(app.state, 'access_token') or not app.state.access_token:
        return {"status": "error", "message": "Not authenticated with Nest API"}
    
    try:
        url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{app.state.config.project_id}/devices/{device_id}:executeCommand"
        headers = {"Authorization": f"Bearer {app.state.access_token}"}
        
        if test_type == "full":
            payload = {"command": "sdm.devices.commands.SafetyTest.SelfTest"}
        else:
            payload = {
                "command": "sdm.devices.commands.SafetyTest.SelfTest",
                "params": {"test_type": test_type.upper()}
            }
        
        async with app.state.http_session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                return {"status": "success", "message": f"Started {test_type} safety test", "device_id": device_id}
            else:
                error = await response.json()
                return {"status": "error", "message": "Failed to start safety test", "error": error.get("error", {}).get("message")}
    except Exception as e:
        return {"status": "error", "message": f"Failed to run safety test: {str(e)}"}

@tool(name="set_led_brightness", description="Set LED brightness for a Nest Protect device", parameters={"device_id": {"type": "string", "description": "ID of the device", "required": True}, "brightness": {"type": "integer", "description": "Brightness level (0-100)", "minimum": 0, "maximum": 100, "required": True}}, examples=["set_led_brightness('device123', 50)", "set_led_brightness(device_id='device123', brightness=75)"])
async def set_led_brightness(device_id: str, brightness: int) -> Dict[str, Any]:
    """Set LED brightness for a Nest Protect device."""
    from ..server import app
    
    if not hasattr(app.state, 'access_token') or not app.state.access_token:
        return {"status": "error", "message": "Not authenticated with Nest API"}
    
    try:
        url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{app.state.config.project_id}/devices/{device_id}:executeCommand"
        headers = {"Authorization": f"Bearer {app.state.access_token}"}
        payload = {
            "command": "sdm.devices.commands.Settings.LedBrightness",
            "params": {"level": brightness}
        }
        
        async with app.state.http_session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                return {"status": "success", "message": f"LED brightness set to {brightness}%", "device_id": device_id}
            else:
                error = await response.json()
                return {"status": "error", "message": "Failed to set LED brightness", "error": error.get("error", {}).get("message")}
    except Exception as e:
        return {"status": "error", "message": f"Failed to set LED brightness: {str(e)}"}
