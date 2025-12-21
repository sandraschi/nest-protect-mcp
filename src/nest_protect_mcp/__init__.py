"""
Nest Protect MCP - A FastMCP 2.12 compliant server for Nest Protect integration.

This package provides a Message Control Protocol (MCP) server for interacting with
Nest Protect smoke and carbon monoxide detectors.
"""

__version__ = "0.1.0"
__author__ = "Sandra Schiessl"
__email__ = "sandra.schiessl@example.com"
__all__ = ["app", "ProtectConfig", "ProtectDeviceState", "ProtectCommand"]

# Initialize logging
import logging

from .fastmcp_server import app
from .models import ProtectCommand, ProtectConfig, ProtectDeviceState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Set default logging handler to avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
