"""
Main entry point for the Nest Protect MCP server (FastMCP 2.12).

This module implements the command-line interface for the Nest Protect MCP server,
providing FastMCP 2.12 compatibility and STDIO communication for Claude Desktop.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

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
            with open(config_file) as f:
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

    parser = argparse.ArgumentParser(
        description="Nest Protect MCP Server (FastMCP 2.12)"
    )

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
    """Run the Nest Protect MCP server with unified transport (FastMCP 2.14.4+)."""
    from .transport import create_argument_parser, run_server

    # Enhanced logging setup
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # Ensure logs go to stderr
        ],
    )

    logger.info("=== NEST PROTECT MCP SERVER STARTUP ===")

    try:
        # Create parser with custom arguments
        parser = create_argument_parser(server_name="NestProtectMCP")
        parser.add_argument("--config", type=str, help="Path to configuration file")
        parser.add_argument("--client-id", type=str, help="Nest OAuth client ID")
        parser.add_argument(
            "--client-secret", type=str, help="Nest OAuth client secret"
        )
        parser.add_argument("--project-id", type=str, help="Google Cloud project ID")
        parser.add_argument(
            "--kill", action="store_true", help="Kill any running instance"
        )

        args = parser.parse_args()

        # Handle --kill argument for MCP client compatibility
        if args.kill:
            logger.warning("=== KILL ARGUMENT RECEIVED ===")
            sys.exit(0)

        # Load and apply configuration
        config = load_config()
        if hasattr(args, "config") and args.config:
            import json

            with open(args.config) as f:
                config.update(json.load(f))

        logger.info("Starting Nest Protect MCP server (FastMCP 2.14.4+)")
        run_server(app, server_name="nest-protect-mcp")

    except KeyboardInterrupt:
        logger.info("=== SERVER STOPPED BY USER ===")
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
