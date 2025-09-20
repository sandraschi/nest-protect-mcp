"""
Main entry point for the Nest Protect MCP server (FastMCP 2.12).

This module implements the command-line interface for the Nest Protect MCP server,
providing FastMCP 2.12 compatibility and STDIO communication for Claude Desktop.
"""
import logging
import os
import sys
import json
from typing import Dict, List, Optional, Any

from .fastmcp_server import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("nest_protect_mcp")

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables and config file."""
    # Default configuration
    config = {
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
        "state_file": os.path.expanduser(
            os.getenv("NEST_PROTECT_STATE_FILE", "~/.nest_protect_mcp/state.json")
        ),
        "client_id": os.getenv("NEST_CLIENT_ID"),
        "client_secret": os.getenv("NEST_CLIENT_SECRET"),
        "project_id": os.getenv("NEST_PROJECT_ID"),
    }
    
    # Load from config file if specified
    config_file = os.getenv("NEST_PROTECT_CONFIG")
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")
    
    # Set log level
    logging.getLogger().setLevel(config["log_level"])
    
    return config

def parse_args():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nest Protect MCP Server (FastMCP 2.12)")
    
    # Server options
    server_group = parser.add_argument_group("Server Options")
    server_group.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        default=os.getenv("NEST_PROTECT_CONFIG"),
    )
    server_group.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set the logging level",
    )
    
    # Authentication options
    auth_group = parser.add_argument_group("Authentication")
    auth_group.add_argument(
        "--client-id",
        type=str,
        help="Nest OAuth client ID",
        default=os.getenv("NEST_CLIENT_ID"),
    )
    auth_group.add_argument(
        "--client-secret",
        type=str,
        help="Nest OAuth client secret",
        default=os.getenv("NEST_CLIENT_SECRET"),
    )
    auth_group.add_argument(
        "--project-id",
        type=str,
        help="Google Cloud project ID",
        default=os.getenv("NEST_PROJECT_ID"),
    )
    
    # MCP client management options
    parser.add_argument(
        "--kill",
        action="store_true",
        help="Kill any running server instance (for MCP client compatibility)",
    )
    
    return parser.parse_args()

def main():
    """Run the Nest Protect MCP server."""
    # Enhanced logging setup
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # Ensure logs go to stderr for Claude Desktop
        ]
    )
    
    logger.info("=== NEST PROTECT MCP SERVER STARTUP ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Command line args: {sys.argv}")
    
    try:
        args = parse_args()
        logger.info(f"Parsed arguments: {vars(args)}")
        
        # Handle --kill argument for MCP client compatibility
        if args.kill:
            logger.warning("=== KILL ARGUMENT RECEIVED ===")
            logger.warning("This indicates Claude Desktop is trying to restart the server")
            logger.warning("Server will exit gracefully to allow restart")
            print("KILL argument received - server exiting for restart", file=sys.stderr)
            sys.exit(0)
        
        logger.info("Loading configuration...")
        config = load_config()
        logger.info(f"Configuration loaded: {config}")
        
        # Override config with command line arguments
        if args.log_level:
            config["log_level"] = args.log_level
            logging.getLogger().setLevel(args.log_level)
        
        if args.config:
            config["config_file"] = args.config
        
        # Override auth config if provided via command line
        if args.client_id:
            config["client_id"] = args.client_id
        if args.client_secret:
            config["client_secret"] = args.client_secret
        if args.project_id:
            config["project_id"] = args.project_id
        
        logger.info("=== STARTING FASTMCP SERVER ===")
        logger.info("Starting Nest Protect MCP server (FastMCP 2.12)")
        logger.info("Server will use STDIO transport for Claude Desktop")
        logger.info("Press Ctrl+C to stop the server")
        
        # Add error handling around app.run()
        try:
            # Run the FastMCP server (this is a blocking call)
            logger.info("Calling app.run() - server should start listening...")
            app.run()
            logger.info("app.run() completed normally")
            
        except Exception as app_error:
            logger.error(f"FastMCP app.run() failed: {app_error}", exc_info=True)
            print(f"FastMCP server error: {app_error}", file=sys.stderr)
            raise
        
    except KeyboardInterrupt:
        logger.info("=== SERVER STOPPED BY USER (Ctrl+C) ===")
        print("Server stopped by user", file=sys.stderr)
    except SystemExit as e:
        logger.info(f"=== SYSTEM EXIT: {e.code} ===")
        print(f"System exit: {e.code}", file=sys.stderr)
        raise
    except Exception as e:
        logger.error(f"=== FATAL ERROR ===", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {e}")
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    logger.info("=== MAIN FUNCTION COMPLETE ===")
    print("Main function completed", file=sys.stderr)

if __name__ == "__main__":
    main()
