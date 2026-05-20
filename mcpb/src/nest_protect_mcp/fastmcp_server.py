#!/usr/bin/env python3
"""
Nest Protect MCP Server using FastMCP 3.2.x.
Tools, prompts (skills), sampling and agentic workflows.
"""

import logging
import sys
from typing import Any, Literal

from fastmcp import FastMCP
from fastmcp.apps import FastMCPApp
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

try:
    from prefab_ui.app import PrefabApp
    from prefab_ui.components import (
        Card,
        CardContent,
        CardHeader,
        CardTitle,
        Image,
        Text,
    )
except ImportError:
    PrefabApp = None
    Card = CardContent = CardHeader = CardTitle = Text = Image = None

from .tools.auth_tools import PCMUrlParams, ValidateNestAuthParams
from .transport import run_server

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger("nest_protect_mcp")

logger.info("=== INITIALIZING FASTMCP SERVER ===")
logger.info("Loading FastMCP framework...")

# Provider app (tools + UI meta); wrapped by FastMCP below for prompts and transport.
try:
    logger.info("Creating FastMCPApp instance...")
    protect_app = FastMCPApp("🔥 nest-protect")
    logger.info("FastMCPApp created successfully")
except Exception as e:
    logger.error(f"Failed to create FastMCPApp: {e}", exc_info=True)
    raise

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
    limit: int = Field(
        10, ge=1, le=100, description="Maximum number of events to return"
    )


class HushAlarmParams(BaseModel):
    """Parameters for hushing an alarm."""

    device_id: str = Field(..., description="ID of the device to hush")
    duration_seconds: int = Field(
        180, ge=30, le=300, description="Duration to hush in seconds (30-300)"
    )


class SafetyCheckParams(BaseModel):
    """Parameters for running a safety check."""

    device_id: str = Field(..., description="ID of the device to test")
    test_type: Literal["full", "smoke", "co", "heat"] = Field(
        "full", description="Type of test to run"
    )


class LedBrightnessParams(BaseModel):
    """Parameters for setting LED brightness."""

    device_id: str = Field(..., description="ID of the device")
    brightness: int = Field(..., ge=0, le=100, description="Brightness level (0-100)")


class ProcessStatusParams(BaseModel):
    """Parameters for process status."""

    pid: int | None = Field(
        None, description="Process ID to check (default: current process)"
    )


class ToolHelpParams(BaseModel):
    """Parameters for getting tool help."""

    tool_name: str = Field(..., description="Name of the tool to get help for")


class SearchToolsParams(BaseModel):
    """Parameters for searching tools."""

    query: str = Field(..., description="Search query")
    search_in: list[str] = Field(
        ["name", "description"], description="Fields to search in"
    )


class OAuthFlowParams(BaseModel):
    """Parameters for OAuth flow initiation."""

    redirect_uri: str = Field(
        "http://localhost:8000/auth/callback", description="Redirect URI for auth code"
    )
    state: str | None = Field(None, description="CSRF protection state")
    open_browser: bool = Field(True, description="Open auth URL in browser")


class OAuthCallbackParams(BaseModel):
    """Parameters for OAuth callback handling."""

    code: str = Field(..., description="Auth code from OAuth callback")
    state: str = Field(..., description="State param from OAuth")
    expected_state: str | None = Field(None, description="Expected CSRF state")
    redirect_uri: str = Field(
        "http://localhost:8000/auth/callback",
        description="Redirect URI used in auth request",
    )


class RefreshTokenParams(BaseModel):
    """Parameters for token refresh."""

    force: bool = Field(False, description="Force refresh even if token not expired")


class ConfigSectionParams(BaseModel):
    """Parameters for getting config section."""

    section: str | None = Field(
        None, description="Specific section to retrieve (optional)"
    )


class UpdateConfigParams(BaseModel):
    """Parameters for updating config."""

    updates: dict[str, Any] = Field(
        ..., description="Dictionary of configuration updates"
    )
    save_to_file: bool = Field(
        True, description="Whether to save changes to config file"
    )


class ResetConfigParams(BaseModel):
    """Parameters for resetting config."""

    confirm: bool = Field(False, description="Must be set to True to confirm reset")


class ExportConfigParams(BaseModel):
    """Parameters for exporting config."""

    file_path: str = Field(
        "config/exported_config.toml", description="Path to save the config file"
    )
    format: str = Field("toml", description="Export format (toml, json)")


class ImportConfigParams(BaseModel):
    """Parameters for importing config."""

    file_path: str = Field(..., description="Path to the config file to import")
    merge: bool = Field(
        True, description="Merge with existing config (True) or replace (False)"
    )


class SoundAlarmParams(BaseModel):
    """Parameters for sounding an alarm for testing."""

    device_id: str = Field(..., description="ID of the device to test")
    alarm_type: Literal["smoke", "co", "security", "emergency"] = Field(
        "smoke", description="Type of alarm to sound"
    )
    duration_seconds: int = Field(
        10, ge=5, le=60, description="Duration to sound alarm in seconds (5-60)"
    )
    volume: int = Field(
        100, ge=50, le=100, description="Alarm volume percentage (50-100)"
    )


class ArmDisarmSecurityParams(BaseModel):
    """Parameters for arming/disarming security system."""

    device_id: str = Field(..., description="ID of the security device (Nest Guard)")
    action: Literal["arm_home", "arm_away", "disarm"] = Field(
        ..., description="Security action to perform"
    )
    passcode: str | None = Field(
        None, description="Security passcode (required for disarm)"
    )


class AboutParams(BaseModel):
    """Parameters for getting about information."""

    level: Literal["simple", "intermediate", "technical"] = Field(
        "simple", description="Level of detail (simple, intermediate, technical)"
    )


# ===== Device Status Tools =====


@protect_app.tool(name="list_nest_devices", model=True)
async def list_devices() -> ToolResult:
    """Discover Nest Protect Devices.

    List all detectors, room locations, and online status with rich UI cards for home safety overview.
    """
    try:
        from .tools.device_status import list_devices as tool_func

        result = await tool_func()

        if PrefabApp and "devices" in result:
            with Card(css_class="max-w-lg mb-4") as view:
                with CardHeader():
                    CardTitle("🏠 Your Nest Protect Devices")
                with CardContent():
                    for dev in result.get("devices", []):
                        name = dev.get("name", "Unknown Device")
                        status = "✅ Online" if dev.get("online") else "❌ Offline"
                        room = dev.get("where", "Unknown Location")
                        Text(f"• **{name}** ({room}) — {status}")

            return ToolResult(
                content=f"Found {len(result['devices'])} Nest Protect devices.",
                structured_content=PrefabApp(view=view, title="Device List"),
            )

        return ToolResult(content=str(result))
    except Exception as e:
        logger.error(f"Error in list_devices: {e}", exc_info=True)
        return ToolResult(content=f"Failed to list devices: {e}", is_error=True)


@protect_app.tool(name="get_device_health", model=True)
async def get_device_status(device_id: str) -> ToolResult:
    """Get Device Health Status.

    Real-time battery, smoke, CO, and connectivity metrics with visual health indicators in chat.
    """
    try:
        from .tools.device_status import get_device_status as tool_func

        result = await tool_func(device_id)

        if PrefabApp and "error" not in result:
            with Card(css_class="max-w-md border-l-4 border-green-500") as view:
                with CardHeader():
                    CardTitle(f"📊 Status: {result.get('name', 'Device')}")
                with CardContent():
                    battery = result.get("battery_level", "Unknown")
                    smoke = result.get("smoke_status", "Healthy")
                    co = result.get("co_status", "Healthy")
                    Text(f"🔋 **Battery**: {battery}")
                    Text(f"💨 **Smoke**: {smoke}")
                    Text(f"☁️ **CO**: {co}")
                    Text(f"📶 **Signal**: {result.get('wifi_signal', 'Good')}")

            return ToolResult(
                content=f"Status for {result.get('name')}: Battery {battery}, Smoke {smoke}, CO {co}.",
                structured_content=PrefabApp(view=view, title="Device Health"),
            )

        return ToolResult(content=str(result))
    except Exception as e:
        return ToolResult(content=f"Error getting status: {e}", is_error=True)


@protect_app.tool(model=True, name="get_nest_events")
async def get_device_events(params: DeviceEventsParams) -> ToolResult:
    """Get Recent Device Events.

    Retrieve a list of recent smoke, CO, or connectivity events for a specific device.
    """
    from .tools.device_status import get_device_events as tool_func

    result = await tool_func(params.device_id, params.limit)
    return ToolResult(content=str(result))


# ===== Device Control Tools =====


@protect_app.tool(model=True, name="hush_active_alarm")
async def hush_alarm(params: HushAlarmParams) -> ToolResult:
    """Silence Active Alarm Device.

    Temporarily hush smoke or CO alarms for maintenance or false triggers (30-300 seconds).
    """
    from .tools.device_control import hush_alarm as tool_func

    result = await tool_func(params.device_id, params.duration_seconds)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="run_safety_test")
async def run_safety_check(params: SafetyCheckParams) -> ToolResult:
    """Execute Device Safety Test.

    Trigger full, smoke, or CO self-tests on the device to verify alarm functionality.
    """
    from .tools.device_control import run_safety_check as tool_func

    result = await tool_func(params.device_id, params.test_type)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="set_device_led")
async def set_led_brightness(params: LedBrightnessParams) -> ToolResult:
    """Set Device LED Brightness.

    Adjust the brightness level (0-100) of the Nest Protect status light ring.
    """
    from .tools.device_control import set_led_brightness as tool_func

    result = await tool_func(params.device_id, params.brightness)
    return ToolResult(content=str(result))


@protect_app.tool(
    name="trigger_test_alarm",
    model=True,
    description="""
    🚨 **Test Alarm Systems (Use Responsibly!)**

    Trigger real alarm sounds on your Nest Protect devices for testing purposes.

    **⚠️ IMPORTANT SAFETY NOTES:**
    • Only use for testing and maintenance
    • Warn household members before testing
    • Verify alarms work properly in emergencies
    • Keep duration short to avoid false emergency responses

    **Alarm Types:**
    • 🔥 **Smoke**: Fire detection alarm (loud, pulsing)
    • ☁️ **CO**: Carbon monoxide alarm (distinct pattern)
    • 🔒 **Security**: Intrusion/breach alarm (continuous)
    • 🆘 **Emergency**: Panic button (immediate response)

    **Parameters:**
    • device_id: Target Nest Protect device ID (enterprises/project-id/devices/device-id)
    • alarm_type: Type of alarm (smoke, co, security, emergency) - default: smoke
    • duration_seconds: How long to sound alarm (5-60 seconds) - default: 10
    • volume: Alarm volume percentage (50-100%) - default: 100
    """,
)
async def sound_alarm(
    device_id: str,
    alarm_type: str = "smoke",
    duration_seconds: int = 10,
    volume: int = 100,
) -> ToolResult:
    """Trigger Test Alarm Ring.

    Sound a simulated smoke, CO, or security alarm for system testing and maintenance.
    """
    from .tools.device_control import sound_alarm as tool_func

    result = await tool_func(device_id, alarm_type, duration_seconds, volume)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="set_security_mode")
async def arm_disarm_security(params: ArmDisarmSecurityParams) -> ToolResult:
    """Set Guard Security Mode.

    Arm (home/away) or disarm the Nest security system using an optional passcode.
    """
    from .tools.device_control import arm_disarm_security as tool_func

    result = await tool_func(params.device_id, params.action, params.passcode)
    return ToolResult(content=str(result))


# ===== System Status Tools =====


@protect_app.tool(model=True, name="get_server_status")
async def get_system_status(params: EmptyParams) -> ToolResult:
    """Get Server System Status.

    Retrieve host CPU, memory, and disk usage metrics for the MCP server process.
    """
    from .tools.system_status import get_system_status as tool_func

    result = await tool_func()
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="get_mcp_process")
async def get_process_status(params: ProcessStatusParams) -> ToolResult:
    """Get MCP Process Metrics.

    Retrieve detailed memory and CPU consumption for the specific Nest Protect MCP process.
    """
    from .tools.system_status import get_process_status as tool_func

    result = await tool_func(params.pid)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="check_api_connectivity")
async def get_api_status(params: EmptyParams) -> ToolResult:
    """Check API Connection Health.

    Verify real-time connectivity and latency to the Google Smart Device Management API.
    """
    from .tools.system_status import get_api_status as tool_func

    result = await tool_func()
    return ToolResult(content=str(result))


# ===== Help Tools =====


@protect_app.tool(model=True, name="list_server_tools")
async def list_available_tools(params: EmptyParams) -> ToolResult:
    """List Available MCP Tools.

    Retrieve a comprehensive list of all registered tools and their functional descriptions.
    """
    from .tools.help_tool import list_available_tools as tool_func

    result = await tool_func()
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="get_tool_details")
async def get_tool_help(params: ToolHelpParams) -> ToolResult:
    """Get Tool Practical Help.

    Retrieve detailed parameters, usage examples, and safety constraints for a specific tool.
    """
    from .tools.help_tool import get_tool_help as tool_func

    result = await tool_func(params.tool_name)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="search_mcp_tools")
async def search_tools(params: SearchToolsParams) -> ToolResult:
    """Search Tools by Keyword.

    Discovery helper to find relevant tools based on name, description, or capability keywords.
    """
    from .tools.help_tool import search_tools as tool_func

    result = await tool_func(params.query, params.search_in)
    return ToolResult(content=str(result))


# ===== Authentication Tools =====


@protect_app.tool(model=True, name="start_google_oauth")
async def initiate_oauth_flow(params: OAuthFlowParams) -> ToolResult:
    """Initiate Google OAuth Flow.

    Start the secure OAuth 2.0 authorization process to link your Nest account.
    """
    from .tools.auth_tools import initiate_oauth_flow as tool_func

    result = await tool_func(params.redirect_uri, params.state, params.open_browser)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="finish_google_oauth")
async def handle_oauth_callback(params: OAuthCallbackParams) -> ToolResult:
    """Complete Google OAuth Callback.

    Process the authorization code and exchange it for persistent access and refresh tokens.
    """
    from .tools.auth_tools import handle_oauth_callback as tool_func

    result = await tool_func(
        params.code, params.state, params.expected_state, params.redirect_uri
    )
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="refresh_nest_token")
async def refresh_access_token(params: RefreshTokenParams) -> ToolResult:
    """Refresh Nest Access Token.

    Force or verify the renewal of the current OAuth 2.0 access token for API calls.
    """
    from .tools.auth_tools import refresh_access_token as tool_func

    result = await tool_func(params.force)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="get_nest_auth_status")
async def nest_auth_status(params: EmptyParams) -> ToolResult:
    """Get Nest Auth Configuration Status.

    Summarize whether NEST_* credentials and tokens are loaded (masked); reads repo ``.env`` when needed.
    """
    from .tools.auth_tools import get_nest_auth_status as tool_func

    result = await tool_func()
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="get_oauth_redirect_reference")
async def oauth_redirect_reference(params: EmptyParams) -> ToolResult:
    """Get OAuth Redirect URI Reference.

    Return example redirect URIs (CLI vs web wizard), doc links, and ``just auth`` hints for PCM setup.
    """
    from .tools.auth_tools import get_oauth_redirect_reference as tool_func

    result = await tool_func()
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="get_pcm_authorize_url")
async def pcm_authorize_url(params: PCMUrlParams) -> ToolResult:
    """Get PCM Authorize URL.

    Build the Partner Connections Manager authorization URL (same as start_google_oauth); optional browser.
    """
    from .tools.auth_tools import get_pcm_authorize_url as tool_func

    result = await tool_func(params.redirect_uri, params.open_browser)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="validate_nest_credentials")
async def validate_nest_credentials_tool(params: ValidateNestAuthParams) -> ToolResult:
    """Validate Nest SDM Credentials.

    Optionally refresh the access token, then call SDM ``devices?pageSize=1`` to verify the stack works.
    """
    from .tools.auth_tools import validate_nest_credentials as tool_func

    result = await tool_func(params.force_refresh)
    return ToolResult(content=str(result))


# ===== Configuration Tools =====


@protect_app.tool(model=True, name="get_mcp_config")
async def get_config(params: ConfigSectionParams) -> ToolResult:
    """Get Current Server Configuration.

    Retrieve the active configuration values for API endpoints, timeouts, and device filters.
    """
    from .tools.config_tools import get_config as tool_func

    result = await tool_func(params.section)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="update_mcp_config")
async def update_config(params: UpdateConfigParams) -> ToolResult:
    """Update Server Configuration Values.

    Modify active settings and optionally persist them to the config.toml file.
    """
    from .tools.config_tools import update_config as tool_func

    result = await tool_func(params.updates, params.save_to_file)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="reset_mcp_config")
async def reset_config(params: ResetConfigParams) -> ToolResult:
    """Reset Configuration to Defaults.

    Revert all server settings to their original factory values (requires confirmation).
    """
    from .tools.config_tools import reset_config as tool_func

    result = await tool_func(params.confirm)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="export_config_file")
async def export_config(params: ExportConfigParams) -> ToolResult:
    """Export Config To File.

    Save the current active configuration to a local file in TOML or JSON format.
    """
    from .tools.config_tools import export_config as tool_func

    result = await tool_func(params.file_path, params.format)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="import_config_file")
async def import_config(params: ImportConfigParams) -> ToolResult:
    """Import Config From File.

    Load configuration settings from a local file and merge them into the server state.
    """
    from .tools.config_tools import import_config as tool_func

    result = await tool_func(params.file_path, params.merge)
    return ToolResult(content=str(result))


# ===== Advanced AI Orchestration Tools =====


@protect_app.tool(model=True, name="analyze_home_safety")
async def assess_home_safety(
    include_recommendations: bool = True,
    assessment_scope: str = "comprehensive",
    focus_areas: list[str] | None = None,
) -> ToolResult:
    """Assess Home Safety AI.

    Perform comprehensive safety evaluation using advanced AI orchestration and sampling patterns.
    """
    from .tools.ai_orchestration import assess_home_safety as tool_func

    result = await tool_func(include_recommendations, assessment_scope, focus_areas)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="coordinate_emergency_ai")
async def coordinate_emergency_response(
    emergency_type: str, affected_devices: list[str], response_priority: str = "high"
) -> ToolResult:
    """Coordinate Emergency AI Response.

    Execute intelligent coordination during safety incidents using sampling for complex decisions.
    """
    from .tools.ai_orchestration import coordinate_emergency_response as tool_func

    result = await tool_func(emergency_type, affected_devices, response_priority)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="forecast_maintenance_needs")
async def predict_maintenance_needs(
    analysis_depth: str = "detailed",
    time_horizon: str = "1_month",
    include_cost_estimates: bool = True,
) -> ToolResult:
    """Forecast Device Maintenance Needs.

    Predict future battery replacements and sensor failures using environmental AI analysis.
    """
    from .tools.ai_orchestration import predict_maintenance_needs as tool_func

    result = await tool_func(analysis_depth, time_horizon, include_cost_estimates)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="configure_smart_automation")
async def setup_smart_automation(
    automation_type: str,
    learning_period: str = "2_weeks",
    confidence_threshold: float = 0.8,
) -> ToolResult:
    """Configure Smart Safety Automation.

    Set up adaptive automation rules that learn your lifestyle patterns for proactive safety.
    """
    from .tools.ai_orchestration import setup_smart_automation as tool_func

    result = await tool_func(automation_type, learning_period, confidence_threshold)
    return ToolResult(content=str(result))


# ===== About & General Help Tools =====


@protect_app.tool(model=True, name="get_server_info")
async def about_server(level: str = "simple") -> ToolResult:
    """Get Server Information.

    Retrieve version, capabilities, and operational documentation for this Nest Protect MCP instance.
    """
    from .tools.about_tool import about_server as tool_func

    result = await tool_func(level)
    return ToolResult(content=str(result))


@protect_app.tool(model=True, name="list_supported_hardware")
async def get_supported_devices(params: EmptyParams) -> ToolResult:
    """List Supported Nest Hardware.

    Retrieve detailed technical specifications for supported Nest Protect generations and models.
    """
    from .tools.about_tool import get_supported_devices as tool_func

    result = await tool_func()
    return ToolResult(content=str(result))


# Wire transport, version, and prompts; tools live on protect_app.
app = FastMCP(
    "🔥 nest-protect",
    version="1.0.0",
    providers=[protect_app],
)


# ===== Prompts (skills) for agentic workflows =====

try:
    from fastmcp.prompts import Message
except ImportError:
    Message = None  # type: ignore[misc, assignment]


if Message is not None:

    @app.prompt(
        name="nest_protect_setup",
        description="Guide to set up Nest Protect MCP auth (Google OAuth, refresh token).",
    )
    def prompt_nest_protect_setup() -> "Message":
        return Message(
            "To use Nest Protect MCP you need one-time Google OAuth setup for Smart Device Management "
            "(OAuth consent lists this scope under home automation / Smart Device Management): "
            "1) Register for Device Access and note your Device Access project id "
            "(NEST_PROJECT_ID — SDM enterprise UUID). "
            "2) Google Cloud: enable Smart Device Management API; OAuth Desktop client; "
            "add redirect URI matching scripts/get_nest_refresh_token.py "
            "(default http://127.0.0.1:8080/). "
            "3) Run scripts/get_nest_refresh_token.py — it uses Partner Connections Manager (PCM), "
            "not accounts.google.com. "
            "4) Put NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_PROJECT_ID, NEST_REFRESH_TOKEN "
            "in .env at repo root."
        )

    @app.prompt(
        name="nest_protect_safety_check",
        description="How to run a safety test on a Nest Protect device.",
    )
    def prompt_nest_protect_safety_check() -> "Message":
        return Message(
            "Use the run_safety_check tool with device_id (from list_devices) and test_type: full, smoke, co, or heat. "
            "This triggers the device self-test. Prefer test_type 'full' for a complete check."
        )

    @app.prompt(
        name="nest_protect_overview",
        description="Overview of Nest Protect MCP tools and capabilities.",
    )
    def prompt_nest_protect_overview() -> "Message":
        return Message(
            "Nest Protect MCP provides: list_nest_devices, get_device_health, get_nest_events for status; "
            "hush_active_alarm, run_safety_test, set_device_led for control; "
            "get_server_status, check_api_connectivity for health; "
            "start_google_oauth, finish_google_oauth, refresh_nest_token, get_nest_auth_status, "
            "get_oauth_redirect_reference, get_pcm_authorize_url, validate_nest_credentials for auth; "
            "list_server_tools, get_tool_details, get_server_info for help. "
            "Use list_nest_devices first to get device IDs."
        )


# ===== Main Entry Point =====

logger.info("=== TOOL REGISTRATION COMPLETE ===")
logger.info("All 32 tools have been registered with FastMCP")
logger.info("Tools registered:")
logger.info(
    "  • Device Status: list_nest_devices, get_device_health, get_nest_events"
)
logger.info(
    "  • Device Control: hush_active_alarm, run_safety_test, set_device_led, trigger_test_alarm, set_security_mode"
)
logger.info(
    "  • System Status: get_server_status, get_mcp_process, check_api_connectivity"
)
logger.info(
    "  • Authentication: start_google_oauth, finish_google_oauth, refresh_nest_token, "
    "get_nest_auth_status, get_oauth_redirect_reference, get_pcm_authorize_url, validate_nest_credentials"
)
logger.info(
    "  • Configuration: get_mcp_config, update_mcp_config, reset_mcp_config, export_config_file, import_config_file"
)
logger.info(
    "  • AI Orchestration: analyze_home_safety, coordinate_emergency_ai, "
    "forecast_maintenance_needs, configure_smart_automation"
)
logger.info(
    "  • Help & About: list_server_tools, get_tool_details, search_mcp_tools, "
    "get_server_info, list_supported_hardware"
)

if __name__ == "__main__":
    # Handle --kill argument for MCP client compatibility
    if "--kill" in sys.argv:
        logger.info("Kill argument received - exiting gracefully")
        sys.exit(0)

    # Run the server
    logger.info("Starting Nest Protect MCP server with all 32 tools...")
    run_server(app, server_name="🔥 nest-protect")
