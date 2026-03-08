"""
FastAPI backend for Nest Protect MCP Testing Webapp

This backend provides REST API endpoints and WebSocket connections
for the MCP testing webapp, integrating with the Nest Protect MCP server.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import socketio

# Add the MCP server to the path
mcp_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(mcp_path))

from nest_protect_mcp.fastmcp_server import app as mcp_app
from nest_protect_mcp.state_manager import get_app_state
from nest_protect_mcp.tools import device_status, device_control, ai_orchestration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Nest Protect MCP Testing API",
    description="FastAPI backend for MCP testing webapp with conversational AI support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7770", "http://127.0.0.1:7770"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:7770", "http://127.0.0.1:7770"]
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)
combined_app = socket_app

# Pydantic models for API requests
class DeviceTestRequest(BaseModel):
    device_id: str
    test_type: str = "full"

class AlarmControlRequest(BaseModel):
    device_id: str
    action: str = "hush"
    duration_seconds: int = 180

class SafetyAssessmentRequest(BaseModel):
    include_recommendations: bool = True
    assessment_scope: str = "comprehensive"
    focus_areas: Optional[List[str]] = None

class EmergencyRequest(BaseModel):
    emergency_type: str
    affected_devices: List[str]
    response_priority: str = "high"

class PredictiveMaintenanceRequest(BaseModel):
    analysis_depth: str = "detailed"
    time_horizon: str = "1_month"
    include_cost_estimates: bool = True

# Global state for MCP integration
mcp_state = get_app_state()

# WebSocket event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit('status', {'message': 'Connected to MCP testing server'}, to=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def test_device(sid, data):
    """Handle device testing requests via WebSocket."""
    try:
        device_id = data.get('device_id')
        test_type = data.get('test_type', 'full')

        # Run safety check
        result = await device_control.run_safety_check(device_id, test_type)

        await sio.emit('test_result', {
            'device_id': device_id,
            'test_type': test_type,
            'result': result
        }, to=sid)

    except Exception as e:
        await sio.emit('error', {
            'message': f'Device test failed: {str(e)}'
        }, to=sid)

# REST API endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Nest Protect MCP Testing API",
        "version": "1.0.0",
        "mcp_version": "2.14.3",
        "features": [
            "Device discovery and monitoring",
            "Safety testing and diagnostics",
            "Conversational AI responses",
            "Emergency coordination",
            "Predictive maintenance"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_connected": mcp_state.access_token is not None
    }

@app.get("/api/devices")
async def list_devices():
    """List all Nest Protect devices."""
    try:
        result = await device_status.list_devices()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to list devices: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to retrieve devices",
                "message": str(e)
            }
        )

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Get detailed status for a specific device."""
    try:
        result = await device_status.get_device_status(device_id)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to get device status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to retrieve device status",
                "message": str(e)
            }
        )

@app.get("/api/devices/{device_id}/events")
async def get_device_events(device_id: str, limit: int = 10):
    """Get recent events for a specific device."""
    try:
        result = await device_status.get_device_events(device_id, limit)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to get device events: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to retrieve device events",
                "message": str(e)
            }
        )

@app.post("/api/devices/{device_id}/hush")
async def hush_alarm(device_id: str, request: AlarmControlRequest):
    """Hush an active alarm on a device."""
    try:
        result = await device_control.hush_alarm(device_id, request.duration_seconds)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to hush alarm: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to hush alarm",
                "message": str(e)
            }
        )

@app.post("/api/devices/{device_id}/test")
async def run_safety_test(device_id: str, request: DeviceTestRequest):
    """Run a safety test on a device."""
    try:
        result = await device_control.run_safety_check(device_id, request.test_type)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to run safety test: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to run safety test",
                "message": str(e)
            }
        )

@app.post("/api/devices/{device_id}/brightness")
async def set_led_brightness(device_id: str, brightness: int):
    """Set LED brightness for a device."""
    try:
        result = await device_control.set_led_brightness(device_id, brightness)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to set LED brightness: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to set LED brightness",
                "message": str(e)
            }
        )

@app.post("/api/devices/{device_id}/alarm")
async def sound_alarm(device_id: str, alarm_type: str = "smoke", duration_seconds: int = 10, volume: int = 100):
    """Sound an alarm for testing purposes."""
    try:
        result = await device_control.sound_alarm(device_id, alarm_type, duration_seconds, volume)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to sound alarm: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to sound alarm",
                "message": str(e)
            }
        )

# AI Orchestration endpoints (FastMCP 2.14.3 features)
@app.post("/api/ai/assess-safety")
async def assess_home_safety(request: SafetyAssessmentRequest):
    """AI-powered home safety assessment with sampling capabilities."""
    try:
        result = await ai_orchestration.assess_home_safety(
            include_recommendations=request.include_recommendations,
            assessment_scope=request.assessment_scope,
            focus_areas=request.focus_areas
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to assess home safety: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to perform safety assessment",
                "message": str(e)
            }
        )

@app.post("/api/ai/emergency-response")
async def coordinate_emergency(request: EmergencyRequest):
    """Coordinate emergency response with AI orchestration."""
    try:
        result = await ai_orchestration.coordinate_emergency_response(
            emergency_type=request.emergency_type,
            affected_devices=request.affected_devices,
            response_priority=request.response_priority
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to coordinate emergency response: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to coordinate emergency response",
                "message": str(e)
            }
        )

@app.post("/api/ai/predict-maintenance")
async def predict_maintenance(request: PredictiveMaintenanceRequest):
    """Predict future maintenance needs using AI analysis."""
    try:
        result = await ai_orchestration.predict_maintenance_needs(
            analysis_depth=request.analysis_depth,
            time_horizon=request.time_horizon,
            include_cost_estimates=request.include_cost_estimates
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to predict maintenance: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to predict maintenance needs",
                "message": str(e)
            }
        )

@app.post("/api/ai/smart-automation")
async def setup_smart_automation(
    automation_type: str,
    learning_period: str = "2_weeks",
    confidence_threshold: float = 0.8
):
    """Set up intelligent automation with AI learning."""
    try:
        result = await ai_orchestration.setup_smart_automation(
            automation_type=automation_type,
            learning_period=learning_period,
            confidence_threshold=confidence_threshold
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Failed to setup smart automation: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to setup smart automation",
                "message": str(e)
            }
        )

# System management endpoints
@app.get("/api/system/status")
async def get_system_status():
    """Get overall system status."""
    try:
        # This would integrate with system monitoring
        # For now, return basic status
        return {
            "success": True,
            "operation": "get_system_status",
            "summary": "System status check completed",
            "result": {
                "mcp_server": "running",
                "api_server": "running",
                "websocket_server": "running",
                "device_count": 0,  # Would be populated from actual device count
                "last_health_check": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to get system status",
                "message": str(e)
            }
        )

@app.get("/api/mcp/status")
async def get_mcp_status():
    """Get MCP server status and capabilities."""
    try:
        # Check if MCP server is accessible
        mcp_connected = mcp_state.access_token is not None

        return {
            "success": True,
            "operation": "get_mcp_status",
            "summary": f"MCP server is {'connected' if mcp_connected else 'disconnected'}",
            "result": {
                "connected": mcp_connected,
                "version": "2.14.3",
                "tools_count": 20,  # Total tools in the MCP server
                "features": [
                    "conversational_responses",
                    "sampling_capabilities",
                    "ai_orchestration",
                    "device_management",
                    "safety_testing"
                ]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to get MCP status",
                "message": str(e)
            }
        )

@app.get("/api/mcp/tools")
async def get_available_tools():
    """Get list of available MCP tools."""
    try:
        # Return information about available tools
        tools = [
            {
                "name": "list_devices",
                "description": "Discover all Nest Protect devices",
                "category": "device_discovery"
            },
            {
                "name": "get_device_status",
                "description": "Get detailed device status and health",
                "category": "device_monitoring"
            },
            {
                "name": "hush_alarm",
                "description": "Silence active alarms safely",
                "category": "alarm_control"
            },
            {
                "name": "run_safety_check",
                "description": "Execute comprehensive safety tests",
                "category": "safety_testing"
            },
            {
                "name": "assess_home_safety",
                "description": "AI-powered safety assessment with sampling",
                "category": "ai_orchestration"
            },
            {
                "name": "coordinate_emergency_response",
                "description": "Intelligent emergency response coordination",
                "category": "ai_orchestration"
            }
        ]

        return {
            "success": True,
            "operation": "get_available_tools",
            "summary": f"Retrieved {len(tools)} available MCP tools",
            "result": {
                "tools": tools,
                "categories": list(set(tool["category"] for tool in tools)),
                "total_count": len(tools)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get available tools: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to retrieve tools",
                "message": str(e)
            }
        )

# Authentication endpoints
@app.post("/api/auth/initiate")
async def initiate_oauth():
    """Initiate OAuth authentication flow."""
    try:
        # This would normally start the OAuth flow
        # For testing, return mock response
        return {
            "success": True,
            "operation": "initiate_oauth_flow",
            "summary": "OAuth authentication flow initiated",
            "result": {
                "auth_url": "https://accounts.google.com/oauth/authorize?client_id=test",
                "state": "test_state_123",
                "flow_started": True
            }
        }
    except Exception as e:
        logger.error(f"Failed to initiate OAuth: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to initiate authentication",
                "message": str(e)
            }
        )

@app.post("/api/auth/refresh")
async def refresh_access_token():
    """Refresh OAuth access token."""
    try:
        # This would normally refresh the token
        # For testing, return mock response
        return {
            "success": True,
            "operation": "refresh_access_token",
            "summary": "Access token refreshed successfully",
            "result": {
                "token_refreshed": True,
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        }
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to refresh access token",
                "message": str(e)
            }
        )

if __name__ == "__main__":
    logger.info("Starting Nest Protect MCP Testing API server...")
    uvicorn.run(
        "main:combined_app",
        host="0.0.0.0",
        port=7771,
        reload=True,
        log_level="info"
    )