#!/usr/bin/env python3
"""Simple MCP server for Nest Protect using FastMCP 2.12."""

import asyncio
import logging
from typing import Dict, Any, List
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nest_protect_simple")

class EmptyParams(BaseModel):
    pass

class DeviceIdParams(BaseModel):
    device_id: str = Field(..., description="Device ID")

# Create the FastMCP app
app = FastMCP("nest-protect", version="1.0.0")

@app.tool("list_devices")
async def list_devices(params: EmptyParams) -> Dict[str, Any]:
    """List all Nest Protect devices."""
    return {
        "status": "success",
        "devices": [
            {
                "id": "demo-device-1",
                "name": "Demo Nest Protect",
                "type": "smoke_detector", 
                "online": True,
                "battery_state": "ok"
            }
        ]
    }

@app.tool("get_device_status")
async def get_device_status(params: DeviceIdParams) -> Dict[str, Any]:
    """Get status of a specific device."""
    return {
        "status": "success",
        "device": {
            "id": params.device_id,
            "name": "Demo Nest Protect",
            "online": True,
            "battery_state": "ok",
            "alarm_state": "off"
        }
    }

@app.tool("get_system_status")  
async def get_system_status(params: EmptyParams) -> Dict[str, Any]:
    """Get system status."""
    return {
        "status": "success",
        "system": {
            "server": "running",
            "tools": 3
        }
    }

if __name__ == "__main__":
    import sys
    
    # Handle --kill argument
    if "--kill" in sys.argv:
        logger.info("Kill argument received - exiting gracefully")
        sys.exit(0)
    
    # Run the server
    logger.info("Starting simple Nest Protect MCP server...")
    app.run()
