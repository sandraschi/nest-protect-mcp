"""
Nest Protect MCP - A FastMCP 2.11.3 compliant server for Nest Protect integration.

This package provides a Message Control Protocol (MCP) server for interacting with
Nest Protect smoke and carbon monoxide detectors.
"""

__version__ = "0.1.0"
__author__ = "Your Name <your.email@example.com>"
__all__ = ["NestProtectMCP"]

from .server import NestProtectMCP

# Initialize logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Set default logging handler to avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
