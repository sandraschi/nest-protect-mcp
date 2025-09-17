"""
Main entry point for the Nest Protect MCP server.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union

import uvicorn
from fastapi import FastAPI

from .server import NestProtectMCP, create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("nest_protect_mcp")

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables and config file."""
    # Default configuration
    config = {
        "client_id": "",
        "client_secret": "",
        "project_id": "",
        "refresh_token": "",
        "redirect_uri": "http://localhost:8090/auth/callback",
        "server": {
            "host": "0.0.0.0",
            "port": 8090,  # Changed from 8080 to avoid conflicts
            "log_level": "info",
            "reload": False,
            "workers": 1,
        }
    }
    
    # Update from environment variables
    env_config = {
        "client_id": os.getenv("NEST_CLIENT_ID"),
        "client_secret": os.getenv("NEST_CLIENT_SECRET"),
        "project_id": os.getenv("NEST_PROJECT_ID"),
        "refresh_token": os.getenv("NEST_REFRESH_TOKEN"),
        "redirect_uri": os.getenv("NEST_REDIRECT_URI"),
        "server": {
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "8080")),
            "log_level": os.getenv("LOG_LEVEL", "info"),
            "reload": os.getenv("RELOAD", "false").lower() == "true",
            "workers": int(os.getenv("WORKERS", "1")),
        }
    }
    
    # Update config with non-None environment values
    for key, value in env_config.items():
        if value is not None:
            if isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
    
    return config

def create_server() -> FastAPI:
    """Create and configure the FastAPI application."""
    try:
        # Load configuration
        config = load_config()
        
        logger.info("Creating Nest Protect MCP server...")
        
        # Create and configure the FastAPI app
        app = create_app(config)
        
        logger.info("Server application created successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create server: {e}", exc_info=True)
        raise

async def initialize_server() -> bool:
    """Initialize the Nest Protect MCP server."""
    try:
        # Create the server application
        app = create_server()
        
        # The actual initialization happens in the lifespan handler
        logger.info("Server initialization scheduled")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}", exc_info=True)
        return False

def main():
    """Run the Nest Protect MCP server."""
    try:
        # Create and configure the application
        app = create_server()
        
        # Get server configuration
        server_config = app.state.config.get("server", {})
        
        # Configure uvicorn
        uvicorn.run(
            app,
            host=server_config.get("host", "0.0.0.0"),
            port=server_config.get("port", 8080),
            log_level=server_config.get("log_level", "info"),
            reload=server_config.get("reload", False),
            workers=server_config.get("workers", 1),
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
