#!/usr/bin/env python3
"""
Nest Protect MCP Server using FastMCP 3.1.
Tools, prompts (skills), sampling and agentic workflows.
"""

import logging
import sys
from typing import Any, Dict, List, Literal, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from .transport import run_server

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger("nest_protect_mcp")

logger.info("=== INITIALIZING FASTMCP SERVER ===")
logger.info("Loading FastMCP framework...")

# Create the FastMCP app with emoji icon
try:
    logger.info("Creating FastMCP app instance...")
    app = FastMCP("🔥 nest-protect", version="1.0.0")
    logger.info("FastMCP app created successfully")
except Exception as e:
    logger.error(f"Failed to create FastMCP app: {e}", exc_info=True)
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

    pid: Optional[int] = Field(
        None, description="Process ID to check (default: current process)"
    )


class ToolHelpParams(BaseModel):
    """Parameters for getting tool help."""

    tool_name: str = Field(..., description="Name of the tool to get help for")


class SearchToolsParams(BaseModel):
    """Parameters for searching tools."""

    query: str = Field(..., description="Search query")
    search_in: List[str] = Field(
        ["name", "description"], description="Fields to search in"
    )


class OAuthFlowParams(BaseModel):
    """Parameters for OAuth flow initiation."""

    redirect_uri: str = Field(
        "http://localhost:8000/auth/callback", description="Redirect URI for auth code"
    )
    state: Optional[str] = Field(None, description="CSRF protection state")
    open_browser: bool = Field(True, description="Open auth URL in browser")


class OAuthCallbackParams(BaseModel):
    """Parameters for OAuth callback handling."""

    code: str = Field(..., description="Auth code from OAuth callback")
    state: str = Field(..., description="State param from OAuth")
    expected_state: Optional[str] = Field(None, description="Expected CSRF state")
    redirect_uri: str = Field(
        "http://localhost:8000/auth/callback",
        description="Redirect URI used in auth request",
    )


class RefreshTokenParams(BaseModel):
    """Parameters for token refresh."""

    force: bool = Field(False, description="Force refresh even if token not expired")


class ConfigSectionParams(BaseModel):
    """Parameters for getting config section."""

    section: Optional[str] = Field(
        None, description="Specific section to retrieve (optional)"
    )


class UpdateConfigParams(BaseModel):
    """Parameters for updating config."""

    updates: Dict[str, Any] = Field(
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


class ArmDisarmParams(BaseModel):
    """Parameters for arming/disarming security system."""

    device_id: str = Field(..., description="ID of the security device (Nest Guard)")
    action: Literal["arm_home", "arm_away", "disarm"] = Field(
        ..., description="Security action to perform"
    )
    passcode: Optional[str] = Field(
        None, description="Security passcode (required for disarm)"
    )


class AboutParams(BaseModel):
    """Parameters for getting about information."""

    level: Literal["simple", "intermediate", "technical"] = Field(
        "simple", description="Level of detail (simple, intermediate, technical)"
    )


# ===== Device Status Tools =====


@app.tool(
    name="list_devices",
    description="""
    🔥 **Discover Your Nest Protect Devices**
    
    Get a comprehensive list of all Nest Protect smoke and CO detectors in your home.
    
    **Returns:**
    • Device IDs and friendly names
    • Device models (1st Gen, 2nd Gen, etc.)
    • Room locations and assignments
    • Online/offline status
    • Last activity timestamps
    
    Perfect for getting an overview of your entire Nest Protect ecosystem.
    """,
)
async def list_devices() -> Dict[str, Any]:
    """Get a list of all Nest Protect devices."""
    try:
        logger.debug("=== LIST_DEVICES TOOL CALLED ===")
        logger.debug("Importing device_status.list_devices...")
        from .tools.device_status import list_devices as tool_func

        logger.debug("Successfully imported device_status.list_devices")

        logger.debug("Calling list_devices tool function...")
        result = await tool_func()
        logger.debug(f"list_devices returned: {result}")
        return result
    except Exception as e:
        logger.error("=== ERROR IN LIST_DEVICES ===", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {e}")
        return {"error": f"Failed to list devices: {e}", "status": "error"}


@app.tool(
    name="get_device_status",
    description="""
    📊 **Get Real-Time Device Status**
    
    Get comprehensive status information for a specific Nest Protect device.
    
    **What You'll See:**
    • 🔋 Battery level and health status
    • 💨 Smoke detector status and sensitivity
    • ☁️ Carbon monoxide sensor readings
    • 📶 Wi-Fi connectivity and signal strength
    • 🔧 Device health and diagnostic info
    • 📅 Last test date and maintenance alerts
    
    Essential for monitoring device health and troubleshooting issues.
    
    **Parameters:**
    • device_id: Full device ID (format: enterprises/project-id/devices/device-id)
    """,
)
async def get_device_status(device_id: str) -> Dict[str, Any]:
    """Get status of a specific Nest Protect device."""
    from .tools.device_status import get_device_status as tool_func

    return await tool_func(device_id)


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


@app.tool(
    name="sound_alarm",
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
) -> Dict[str, Any]:
    """Sound an alarm on a Nest device for testing purposes."""
    from .tools.device_control import sound_alarm as tool_func

    return await tool_func(device_id, alarm_type, duration_seconds, volume)


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

    return await tool_func(
        params.code, params.state, params.expected_state, params.redirect_uri
    )


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


# ===== Advanced AI Orchestration Tools =====


@app.tool(
    name="assess_home_safety",
    description="""
    🏠 **AI-Powered Home Safety Assessment**

    Perform comprehensive safety evaluation using advanced AI orchestration.
    This tool analyzes all your Nest Protect devices, identifies safety issues,
    and provides intelligent recommendations with sampling signals for complex analysis.

    **AI Orchestration Features:**
    • 🔍 **Comprehensive Analysis**: Evaluates all safety systems simultaneously
    • 🧠 **Intelligent Recommendations**: AI-generated safety improvement suggestions
    • 📊 **Risk Assessment**: Prioritizes safety issues by severity and impact
    • 🚨 **Emergency Detection**: Identifies critical safety situations requiring immediate attention

    **Sampling Capabilities:**
    • Signals for AI reasoning when complex safety patterns are detected
    • Emergency coordination when critical issues found
    • Predictive maintenance recommendations

    **What It Analyzes:**
    • Smoke and CO detector functionality and status
    • Battery levels and power health across all devices
    • Device connectivity and communication status
    • Alarm system integrity and response times
    • Overall home safety coverage and gaps

    **Parameters:**
    • include_recommendations: Include AI-generated safety recommendations (default: true)
    • assessment_scope: Scope of assessment - basic, comprehensive, or emergency (default: comprehensive)
    • focus_areas: Specific safety areas to focus on (default: all areas)
    """,
)
async def assess_home_safety(
    include_recommendations: bool = True,
    assessment_scope: str = "comprehensive",
    focus_areas: List[str] = None,
) -> Dict[str, Any]:
    """AI-powered home safety assessment with sampling capabilities."""
    from .tools.ai_orchestration import assess_home_safety as tool_func

    return await tool_func(include_recommendations, assessment_scope, focus_areas)


@app.tool(
    name="coordinate_emergency_response",
    description="""
    🚨 **AI Emergency Response Coordination**

    Coordinate intelligent emergency response when safety incidents are detected.
    Uses advanced AI orchestration with sampling signals for complex emergency decision-making.

    **Emergency Types Handled:**
    • 🔥 **Smoke**: Fire detection and evacuation coordination
    • ☁️ **CO**: Carbon monoxide emergency response
    • 🔒 **Security**: Intrusion and safety breach response
    • 🆘 **Medical**: Health emergency assistance coordination
    • ❓ **Unknown**: Unidentified emergency assessment

    **AI Coordination Features:**
    • 🎯 **Priority Assessment**: Determines response urgency and priority
    • 📞 **Emergency Contacts**: Coordinates with emergency services if needed
    • 🏃 **Evacuation Guidance**: Provides safe evacuation route recommendations
    • 📍 **Safety Zones**: Identifies safe areas within the home
    • 📱 **Communication**: Coordinates family/household notifications

    **Sampling Triggers:**
    • Critical decision-making during emergency situations
    • Complex evacuation planning and coordination
    • Emergency service priority assessment

    **Parameters:**
    • emergency_type: Type of emergency detected (smoke, co, security, medical, unknown)
    • affected_devices: List of device IDs involved in the emergency
    • response_priority: Response priority level (low, medium, high, critical) - default: high
    """,
)
async def coordinate_emergency_response(
    emergency_type: str, affected_devices: List[str], response_priority: str = "high"
) -> Dict[str, Any]:
    """Coordinate emergency response using AI orchestration and sampling."""
    from .tools.ai_orchestration import coordinate_emergency_response as tool_func

    return await tool_func(emergency_type, affected_devices, response_priority)


@app.tool(
    name="predict_maintenance_needs",
    description="""
    🔮 **Predictive Maintenance Intelligence**

    Use AI to predict future maintenance needs and schedule optimal service times.
    Analyzes device usage patterns, failure history, and environmental factors.

    **Predictive Capabilities:**
    • 🔋 **Battery Life Prediction**: Estimates when batteries need replacement
    • 🔧 **Device Health Forecasting**: Predicts potential device failures
    • 📅 **Maintenance Scheduling**: Recommends optimal service times
    • 💰 **Cost Estimation**: Provides maintenance cost projections
    • 📊 **Failure Risk Analysis**: Identifies devices at higher risk

    **Analysis Depths:**
    • ⚡ **Quick**: Basic pattern analysis (5-10 minutes)
    • 📋 **Detailed**: Comprehensive device history analysis (15-30 minutes)
    • 🔬 **Comprehensive**: Full environmental and usage pattern analysis (30-60 minutes)

    **Time Horizons:**
    • 1_week: Immediate maintenance needs
    • 1_month: Short-term planning
    • 3_months: Medium-term scheduling
    • 1_year: Long-term maintenance planning

    **Sampling Features:**
    • Complex pattern recognition for failure prediction
    • Cost-benefit analysis for maintenance scheduling
    • Risk assessment for critical safety devices

    **Parameters:**
    • analysis_depth: Depth of analysis - quick, detailed, comprehensive (default: detailed)
    • time_horizon: Prediction timeframe - 1_week, 1_month, 3_months, 1_year (default: 1_month)
    • include_cost_estimates: Include maintenance cost projections (default: true)
    """,
)
async def predict_maintenance_needs(
    analysis_depth: str = "detailed",
    time_horizon: str = "1_month",
    include_cost_estimates: bool = True,
) -> Dict[str, Any]:
    """Predict future maintenance needs using AI analysis and sampling."""
    from .tools.ai_orchestration import predict_maintenance_needs as tool_func

    return await tool_func(analysis_depth, time_horizon, include_cost_estimates)


@app.tool(
    name="setup_smart_automation",
    description="""
    🤖 **Intelligent Home Automation Setup**

    Configure smart automation that learns your patterns and adapts to your lifestyle.
    Uses AI to create personalized automation rules for safety and convenience.

    **Automation Types:**
    • 🛡️ **Safety**: Automated safety checks and alerts based on your schedule
    • 🔧 **Maintenance**: Automated testing and maintenance reminders
    • ⚡ **Energy**: Smart energy management and device optimization
    • 🔒 **Security**: Intelligent security monitoring and alerts

    **AI Learning Process:**
    • 📚 **Pattern Recognition**: Learns your daily routines and device usage
    • 🎯 **Intelligent Triggers**: Creates automation based on learned behavior
    • 📈 **Adaptive Rules**: Adjusts automation as your patterns change
    • 🎛️ **Confidence Scoring**: Only triggers automation when confidence is high

    **Learning Periods:**
    • 1_week: Quick setup with basic pattern recognition
    • 2_weeks: Balanced learning period (recommended)
    • 1_month: Comprehensive pattern learning for complex automation

    **Sampling Integration:**
    • Complex pattern analysis during learning phase
    • Intelligent rule generation from learned behaviors
    • Adaptive automation adjustment over time

    **Parameters:**
    • automation_type: Type of automation - safety, maintenance, energy, security
    • learning_period: AI learning period - 1_week, 2_weeks, 1_month (default: 2_weeks)
    • confidence_threshold: Minimum confidence for triggers (0.5-0.95, default: 0.8)
    """,
)
async def setup_smart_automation(
    automation_type: str,
    learning_period: str = "2_weeks",
    confidence_threshold: float = 0.8,
) -> Dict[str, Any]:
    """Set up intelligent automation using AI learning and sampling."""
    from .tools.ai_orchestration import setup_smart_automation as tool_func

    return await tool_func(automation_type, learning_period, confidence_threshold)


# ===== About & General Help Tools =====


@app.tool(
    name="about_server",
    description="""
    🔥 **Learn About Your Nest Protect MCP Server**

    Get comprehensive information about this server's capabilities, supported devices,
    and how to get started with home automation using your Nest Protect devices.

    **Information Levels:**
    • 📋 **Simple**: Quick overview and basic capabilities
    • ⚙️ **Intermediate**: Detailed features and tool categories
    • 🔬 **Technical**: Implementation details and API integration

    Perfect for understanding what this server can do before diving into specific tools!

    **Parameters:**
    • level: Detail level (simple, intermediate, technical) - default: simple
    """,
)
async def about_server(level: str = "simple") -> Dict[str, Any]:
    """Get information about what this MCP server is and what it can do."""
    from .tools.about_tool import about_server as tool_func

    return await tool_func(level)


@app.tool("get_supported_devices")
async def get_supported_devices(params: EmptyParams) -> Dict[str, Any]:
    """Get detailed information about supported and planned devices."""
    from .tools.about_tool import get_supported_devices as tool_func

    return await tool_func()


# ===== Prompts (skills) for agentic workflows =====

try:
    from fastmcp.prompts import Message
except ImportError:
    Message = None  # type: ignore[misc, assignment]


if Message is not None:

    @app.prompt(name="nest_protect_setup", description="Guide to set up Nest Protect MCP auth (Google OAuth, refresh token).")
    def prompt_nest_protect_setup() -> "Message":
        return Message(
            "To use Nest Protect MCP you need one-time Google OAuth setup: "
            "1) Google Cloud: enable Smart Device Management API, create OAuth Desktop client, download client_secret JSON. "
            "2) Run scripts/get_nest_refresh_token.py from repo root; sign in in browser; copy the refresh token. "
            "3) Create .env with NEST_CLIENT_ID, NEST_CLIENT_SECRET, NEST_PROJECT_ID, NEST_REFRESH_TOKEN. "
            "4) Start the server or web_sota; it will load .env and use the refresh token for API access."
        )

    @app.prompt(name="nest_protect_safety_check", description="How to run a safety test on a Nest Protect device.")
    def prompt_nest_protect_safety_check() -> "Message":
        return Message(
            "Use the run_safety_check tool with device_id (from list_devices) and test_type: full, smoke, co, or heat. "
            "This triggers the device self-test. Prefer test_type 'full' for a complete check."
        )

    @app.prompt(name="nest_protect_overview", description="Overview of Nest Protect MCP tools and capabilities.")
    def prompt_nest_protect_overview() -> "Message":
        return Message(
            "Nest Protect MCP provides: list_devices, get_device_status, get_device_events for status; "
            "hush_alarm, run_safety_check, set_led_brightness for control; get_system_status, get_api_status for health; "
            "initiate_oauth_flow, handle_oauth_callback, refresh_access_token for auth; "
            "list_available_tools, get_tool_help, about_server for help. Use list_devices first to get device IDs."
        )


# ===== Main Entry Point =====

logger.info("=== TOOL REGISTRATION COMPLETE ===")
logger.info("All 20 tools have been registered with FastMCP")
logger.info("Tools registered:")
logger.info("  • Device Status: list_devices, get_device_status, get_device_events")
logger.info(
    "  • Device Control: hush_alarm, run_safety_check, set_led_brightness, sound_alarm, arm_disarm_security"
)
logger.info("  • System Status: get_system_status, get_process_status, get_api_status")
logger.info(
    "  • Authentication: initiate_oauth_flow, handle_oauth_callback, refresh_access_token"
)
logger.info(
    "  • Configuration: get_config, update_config, reset_config, export_config, import_config"
)
logger.info(
    "  • AI Orchestration: assess_home_safety, coordinate_emergency_response, predict_maintenance_needs, setup_smart_automation"
)
logger.info(
    "  • Help & About: list_available_tools, get_tool_help, search_tools, about_server, get_supported_devices"
)

if __name__ == "__main__":
    # Handle --kill argument for MCP client compatibility
    if "--kill" in sys.argv:
        logger.info("Kill argument received - exiting gracefully")
        sys.exit(0)

    # Run the server
    logger.info("Starting Nest Protect MCP server with all 20 tools...")
    run_server(app, server_name="🔥 nest-protect")