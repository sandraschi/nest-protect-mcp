#!/usr/bin/env python3
"""
Nest Protect MCP Server using FastMCP 2.12
Complete implementation with all 20 tools properly registered.
"""
import sys
import logging
from typing import Dict, Any, List, Optional, Literal
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nest_protect_mcp")

# Create the FastMCP app with emoji icon
app = FastMCP("🔥 nest-protect", version="1.0.0")

# ===== Pydantic Models for Tool Parameters =====

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

class HushAlarmParams(BaseModel):
    """Parameters for hushing an alarm."""
    device_id: str = Field(..., description="ID of the device to hush")
    duration_seconds: int = Field(180, ge=30, le=300, description="Duration to hush in seconds (30-300)")

class SafetyCheckParams(BaseModel):
    """Parameters for running a safety check."""
    device_id: str = Field(..., description="ID of the device to test")
    test_type: Literal["full", "smoke", "co", "heat"] = Field("full", description="Type of test to run")

class LedBrightnessParams(BaseModel):
    """Parameters for setting LED brightness."""
    device_id: str = Field(..., description="ID of the device")
    brightness: int = Field(..., ge=0, le=100, description="Brightness level (0-100)")

class ProcessStatusParams(BaseModel):
    """Parameters for process status."""
    pid: Optional[int] = Field(None, description="Process ID to check (default: current process)")

class ToolHelpParams(BaseModel):
    """Parameters for getting tool help."""
    tool_name: str = Field(..., description="Name of the tool to get help for")

class SearchToolsParams(BaseModel):
    """Parameters for searching tools."""
    query: str = Field(..., description="Search query")
    search_in: List[str] = Field(["name", "description"], description="Fields to search in")

class OAuthFlowParams(BaseModel):
    """Parameters for OAuth flow initiation."""
    redirect_uri: str = Field("http://localhost:8000/auth/callback", description="Redirect URI for auth code")
    state: Optional[str] = Field(None, description="CSRF protection state")
    open_browser: bool = Field(True, description="Open auth URL in browser")

class OAuthCallbackParams(BaseModel):
    """Parameters for OAuth callback handling."""
    code: str = Field(..., description="Auth code from OAuth callback")
    state: str = Field(..., description="State param from OAuth")
    expected_state: Optional[str] = Field(None, description="Expected CSRF state")
    redirect_uri: str = Field("http://localhost:8000/auth/callback", description="Redirect URI used in auth request")

class RefreshTokenParams(BaseModel):
    """Parameters for token refresh."""
    force: bool = Field(False, description="Force refresh even if token not expired")

class ConfigSectionParams(BaseModel):
    """Parameters for getting config section."""
    section: Optional[str] = Field(None, description="Specific section to retrieve (optional)")

class UpdateConfigParams(BaseModel):
    """Parameters for updating config."""
    updates: Dict[str, Any] = Field(..., description="Dictionary of configuration updates")
    save_to_file: bool = Field(True, description="Whether to save changes to config file")

class ResetConfigParams(BaseModel):
    """Parameters for resetting config."""
    confirm: bool = Field(False, description="Must be set to True to confirm reset")

class ExportConfigParams(BaseModel):
    """Parameters for exporting config."""
    file_path: str = Field("config/exported_config.toml", description="Path to save the config file")
    format: str = Field("toml", description="Export format (toml, json)")

class ImportConfigParams(BaseModel):
    """Parameters for importing config."""
    file_path: str = Field(..., description="Path to the config file to import")
    merge: bool = Field(True, description="Merge with existing config (True) or replace (False)")

class SoundAlarmParams(BaseModel):
    """Parameters for sounding an alarm for testing."""
    device_id: str = Field(..., description="ID of the device to test")
    alarm_type: Literal["smoke", "co", "security", "emergency"] = Field("smoke", description="Type of alarm to sound")
    duration_seconds: int = Field(10, ge=5, le=60, description="Duration to sound alarm in seconds (5-60)")
    volume: int = Field(100, ge=50, le=100, description="Alarm volume percentage (50-100)")

class ArmDisarmParams(BaseModel):
    """Parameters for arming/disarming security system."""
    device_id: str = Field(..., description="ID of the security device (Nest Guard)")
    action: Literal["arm_home", "arm_away", "disarm"] = Field(..., description="Security action to perform")
    passcode: Optional[str] = Field(None, description="Security passcode (required for disarm)")

class AboutParams(BaseModel):
    """Parameters for getting about information."""
    level: Literal["simple", "intermediate", "technical"] = Field("simple", description="Level of detail (simple, intermediate, technical)")

# ===== Device Status Tools =====

@app.tool("list_devices")
async def list_devices(params: EmptyParams) -> Dict[str, Any]:
    """Get a list of all Nest Protect devices."""
    # Import here to avoid circular imports
    from .tools.device_status import list_devices as tool_func
    return await tool_func()

@app.tool("get_device_status")
async def get_device_status(params: DeviceIdParams) -> Dict[str, Any]:
    """Get status of a specific Nest Protect device."""
    from .tools.device_status import get_device_status as tool_func
    return await tool_func(params.device_id)

@app.tool("get_device_events")
async def get_device_events(params: DeviceEventsParams) -> Dict[str, Any]:
    """Get recent events for a Nest Protect device."""
    from .tools.device_status import get_device_events as tool_func
    return await tool_func(params.device_id, params.limit)

# ===== Device Control Tools =====

@app.tool("hush_alarm")
async def hush_alarm(params: HushAlarmParams) -> Dict[str, Any]:
    """Silence an active alarm on a Nest Protect device."""
    from .tools.device_control import hush_alarm as tool_func
    return await tool_func(params.device_id, params.duration_seconds)

@app.tool("run_safety_check")
async def run_safety_check(params: SafetyCheckParams) -> Dict[str, Any]:
    """Run a safety check on a Nest Protect device."""
    from .tools.device_control import run_safety_check as tool_func
    return await tool_func(params.device_id, params.test_type)

@app.tool("set_led_brightness")
async def set_led_brightness(params: LedBrightnessParams) -> Dict[str, Any]:
    """Set LED brightness for a Nest Protect device."""
    from .tools.device_control import set_led_brightness as tool_func
    return await tool_func(params.device_id, params.brightness)

@app.tool("sound_alarm")
async def sound_alarm(params: SoundAlarmParams) -> Dict[str, Any]:
    """Sound an alarm on a Nest device for testing purposes."""
    from .tools.device_control import sound_alarm as tool_func
    return await tool_func(params.device_id, params.alarm_type, params.duration_seconds, params.volume)

@app.tool("arm_disarm_security")
async def arm_disarm_security(params: ArmDisarmParams) -> Dict[str, Any]:
    """Arm or disarm Nest security system (Nest Guard/Secure)."""
    from .tools.device_control import arm_disarm_security as tool_func
    return await tool_func(params.device_id, params.action, params.passcode)

# ===== System Status Tools =====

@app.tool("get_system_status")
async def get_system_status(params: EmptyParams) -> Dict[str, Any]:
    """Get system status and metrics."""
    from .tools.system_status import get_system_status as tool_func
    return await tool_func()

@app.tool("get_process_status")
async def get_process_status(params: ProcessStatusParams) -> Dict[str, Any]:
    """Get status of the Nest Protect MCP process."""
    from .tools.system_status import get_process_status as tool_func
    return await tool_func(params.pid)

@app.tool("get_api_status")
async def get_api_status(params: EmptyParams) -> Dict[str, Any]:
    """Get status of the Nest API connection."""
    from .tools.system_status import get_api_status as tool_func
    return await tool_func()

# ===== Help Tools =====

@app.tool("list_available_tools")
async def list_available_tools(params: EmptyParams) -> Dict[str, Any]:
    """List all available tools with their descriptions."""
    from .tools.help_tool import list_available_tools as tool_func
    return await tool_func()

@app.tool("get_tool_help")
async def get_tool_help(params: ToolHelpParams) -> Dict[str, Any]:
    """Get detailed help for a specific tool."""
    from .tools.help_tool import get_tool_help as tool_func
    return await tool_func(params.tool_name)

@app.tool("search_tools")
async def search_tools(params: SearchToolsParams) -> Dict[str, Any]:
    """Search for tools by keyword or description."""
    from .tools.help_tool import search_tools as tool_func
    return await tool_func(params.query, params.search_in)

# ===== Authentication Tools =====

@app.tool("initiate_oauth_flow")
async def initiate_oauth_flow(params: OAuthFlowParams) -> Dict[str, Any]:
    """Start OAuth 2.0 flow for Nest API."""
    from .tools.auth_tools import initiate_oauth_flow as tool_func
    return await tool_func(params.redirect_uri, params.state, params.open_browser)

@app.tool("handle_oauth_callback")
async def handle_oauth_callback(params: OAuthCallbackParams) -> Dict[str, Any]:
    """Handle OAuth 2.0 callback from Nest API."""
    from .tools.auth_tools import handle_oauth_callback as tool_func
    return await tool_func(params.code, params.state, params.expected_state, params.redirect_uri)

@app.tool("refresh_access_token")
async def refresh_access_token(params: RefreshTokenParams) -> Dict[str, Any]:
    """Refresh OAuth 2.0 access token."""
    from .tools.auth_tools import refresh_access_token as tool_func
    return await tool_func(params.force)

# ===== Configuration Tools =====

@app.tool("get_config")
async def get_config(params: ConfigSectionParams) -> Dict[str, Any]:
    """Get current configuration."""
    from .tools.config_tools import get_config as tool_func
    return await tool_func(params.section)

@app.tool("update_config")
async def update_config(params: UpdateConfigParams) -> Dict[str, Any]:
    """Update configuration values."""
    from .tools.config_tools import update_config as tool_func
    return await tool_func(params.updates, params.save_to_file)

@app.tool("reset_config")
async def reset_config(params: ResetConfigParams) -> Dict[str, Any]:
    """Reset configuration to defaults."""
    from .tools.config_tools import reset_config as tool_func
    return await tool_func(params.confirm)

@app.tool("export_config")
async def export_config(params: ExportConfigParams) -> Dict[str, Any]:
    """Export current configuration to a file."""
    from .tools.config_tools import export_config as tool_func
    return await tool_func(params.file_path, params.format)

@app.tool("import_config")
async def import_config(params: ImportConfigParams) -> Dict[str, Any]:
    """Import configuration from a file."""
    from .tools.config_tools import import_config as tool_func
    return await tool_func(params.file_path, params.merge)

# ===== About & General Help Tools =====

@app.tool("about_server")
async def about_server(params: AboutParams) -> Dict[str, Any]:
    """Get information about what this MCP server is and what it can do."""
    from .tools.about_tool import about_server as tool_func
    return await tool_func(params.level)

@app.tool("get_supported_devices")
async def get_supported_devices(params: EmptyParams) -> Dict[str, Any]:
    """Get detailed information about supported and planned devices."""
    from .tools.about_tool import get_supported_devices as tool_func
    return await tool_func()

# ===== Main Entry Point =====

if __name__ == "__main__":
    # Handle --kill argument for MCP client compatibility
    if "--kill" in sys.argv:
        logger.info("Kill argument received - exiting gracefully")
        sys.exit(0)
    
    # Run the server
    logger.info("Starting Nest Protect MCP server with all 20 tools...")
    app.run()
