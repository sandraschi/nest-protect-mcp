"""
Main entry point for the Nest Protect MCP server.
"""
import asyncio
import logging
import os
import sys
from .server import NestProtectMCP

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("nest_protect_mcp")

async def create_server():
    """Create and initialize the Nest Protect MCP server."""
    # Load configuration from environment variables or use defaults
    config = {
        "client_id": os.getenv("NEST_CLIENT_ID", ""),
        "client_secret": os.getenv("NEST_CLIENT_SECRET", ""),
        "project_id": os.getenv("NEST_PROJECT_ID", ""),
        "refresh_token": os.getenv("NEST_REFRESH_TOKEN", ""),
        "redirect_uri": os.getenv("NEST_REDIRECT_URI", "http://localhost:8000/auth/callback"),
    }
    
    # Create the server
    server = NestProtectMCP(config)
    
    # Initialize the server asynchronously
    if hasattr(server, 'initialize'):
        await server.initialize()
    
    return server

def main():
    """Run the Nest Protect MCP server."""
    try:
        logger.info("Starting Nest Protect MCP server...")
        
        # Create and initialize the server in an async context
        server = asyncio.run(create_server())
        
        # Start the server
        import uvicorn
        logger.info("Configuring uvicorn...")
        config = uvicorn.Config(
            server.app,
            host="0.0.0.0",
            port=8000,
            log_level="debug",
            log_config=None
        )
        
        logger.info("Creating uvicorn server...")
        server = uvicorn.Server(config)
        
        logger.info("Running server...")
        server.run()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        # Cleanup if needed
        if 'server' in locals() and hasattr(server, 'cleanup'):
            logger.info("Cleaning up...")
            asyncio.run(server.cleanup())
            logger.info("Cleanup complete")

if __name__ == "__main__":
    main()
