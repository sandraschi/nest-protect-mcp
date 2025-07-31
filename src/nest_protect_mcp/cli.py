"""
Command-line interface for the Nest Protect MCP server.
"""
import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import uvicorn
from dotenv import load_dotenv

from . import __version__, NestProtectMCP
from .models import ProtectConfig, ProtectDeviceState, ProtectCommand, ProtectEvent
from .exceptions import NestProtectError, NestAuthError, NestConnectionError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("nest_protect_mcp.cli")

class NestProtectCLI:
    """Command-line interface for Nest Protect MCP."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = None
        self.server = None
        self.loop = asyncio.get_event_loop()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        # Set up argument parser
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="Nest Protect MCP - Control Nest Protect devices via MCP",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        
        # Global arguments
        parser.add_argument(
            "--config",
            type=str,
            default="config/default.toml",
            help="Path to configuration file",
        )
        parser.add_argument(
            "--env-file",
            type=str,
            default=".env",
            help="Path to .env file for environment variables",
        )
        parser.add_argument(
            "--log-level",
            type=str,
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="Set the logging level",
        )
        parser.add_argument(
            "--version",
            action="store_true",
            help="Show version and exit",
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
        
        # Server command
        server_parser = subparsers.add_parser("server", help="Run the MCP server")
        server_parser.add_argument(
            "--host",
            type=str,
            default="0.0.0.0",
            help="Host to bind the server to",
        )
        server_parser.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Port to bind the server to",
        )
        server_parser.add_argument(
            "--reload",
            action="store_true",
            help="Enable auto-reload for development",
        )
        
        # Devices command
        devices_parser = subparsers.add_parser("devices", help="List all devices")
        devices_parser.add_argument(
            "--format",
            type=str,
            choices=["table", "json"],
            default="table",
            help="Output format",
        )
        
        # Device command
        device_parser = subparsers.add_parser("device", help="Get device details")
        device_parser.add_argument(
            "device_id",
            type=str,
            help="Device ID",
        )
        device_parser.add_argument(
            "--format",
            type=str,
            choices=["table", "json"],
            default="table",
            help="Output format",
        )
        
        # Hush command
        hush_parser = subparsers.add_parser("hush", help="Hush an alarm")
        hush_parser.add_argument(
            "device_id",
            type=str,
            help="Device ID",
        )
        hush_parser.add_argument(
            "--duration",
            type=int,
            default=900,
            help="Hush duration in seconds (default: 900)",
        )
        
        # Test command
        test_parser = subparsers.add_parser("test", help="Run a device test")
        test_parser.add_argument(
            "device_id",
            type=str,
            help="Device ID",
        )
        test_parser.add_argument(
            "--type",
            type=str,
            choices=["full", "smoke", "co", "heat"],
            default="full",
            help="Test type",
        )
        
        # Web UI command
        web_parser = subparsers.add_parser("web", help="Run the web UI")
        web_parser.add_argument(
            "--host",
            type=str,
            default="0.0.0.0",
            help="Host to bind the web UI to",
        )
        web_parser.add_argument(
            "--port",
            type=int,
            default=8080,
            help="Port to bind the web UI to",
        )
        
        return parser
    
    def _load_config(self, config_file: str) -> ProtectConfig:
        """Load configuration from file."""
        try:
            # Check if file exists
            config_path = Path(config_file)
            if not config_path.exists():
                logger.warning(f"Config file {config_file} not found, using defaults")
                return ProtectConfig()
            
            # Load config based on file extension
            if config_path.suffix == ".toml":
                import toml
                with open(config_path) as f:
                    config_data = toml.load(f)
            elif config_path.suffix == ".json":
                import json
                with open(config_path) as f:
                    config_data = json.load(f)
            elif config_path.suffix in (".yaml", ".yml"):
                import yaml
                with open(config_path) as f:
                    config_data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
            
            return ProtectConfig(**config_data)
            
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            raise
    
    async def _init_server(self, args) -> NestProtectMCP:
        """Initialize the Nest Protect MCP server."""
        try:
            # Load environment variables
            if os.path.exists(args.env_file):
                load_dotenv(args.env_file)
            
            # Load configuration
            self.config = self._load_config(args.config)
            
            # Override log level from command line
            if args.log_level:
                logging.getLogger().setLevel(args.log_level)
                self.config.log_level = args.log_level
            
            # Create and initialize server
            server = NestProtectMCP(self.config)
            
            # Add event listener for logging
            def log_event(event: ProtectEvent) -> None:
                logger.info(f"Event: {event.event_type} from {event.device_id}")
                if event.event_data:
                    logger.debug(f"Event data: {event.event_data}")
            
            server.add_event_listener(log_event)
            
            # Start the server
            await server.start()
            
            return server
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}", exc_info=True)
            await self._shutdown()
            sys.exit(1)
    
    def _handle_signal(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.loop.create_task(self._shutdown())
    
    async def _shutdown(self) -> None:
        """Shut down the server and clean up."""
        if self.server:
            await self.server.stop()
        self.loop.stop()
    
    def _print_devices_table(self, devices: List[ProtectDeviceState]) -> None:
        """Print devices in a table format."""
        from tabulate import tabulate
        
        table = []
        for device in devices:
            table.append([
                device.device_id,
                device.name,
                device.model,
                "Online" if device.online else "Offline",
                device.co_alarm_state.value,
                device.smoke_alarm_state.value,
                device.heat_alarm_state.value,
                f"{device.battery_level}%" if device.battery_level is not None else "N/A",
                device.battery_health.value,
            ])
        
        headers = [
            "ID", "Name", "Model", "Status", "CO Alarm", "Smoke Alarm", 
            "Heat Alarm", "Battery", "Battery Health"
        ]
        print(tabulate(table, headers=headers, tablefmt="grid"))
    
    def _print_device_details(self, device: ProtectDeviceState) -> None:
        """Print detailed information about a device."""
        from tabulate import tabulate
        
        info = [
            ["ID", device.device_id],
            ["Name", device.name],
            ["Model", device.model],
            ["Serial Number", device.serial_number],
            ["Status", "Online" if device.online else "Offline"],
            ["CO Alarm", device.co_alarm_state.value],
            ["Smoke Alarm", device.smoke_alarm_state.value],
            ["Heat Alarm", device.heat_alarm_state.value],
            ["Battery Level", f"{device.battery_level}%" if device.battery_level is not None else "N/A"],
            ["Battery Health", device.battery_health.value],
            ["Temperature", f"{device.temperature}°C" if device.temperature is not None else "N/A"],
            ["Humidity", f"{device.humidity}%" if device.humidity is not None else "N/A"],
            ["WiFi IP", device.wifi_ip or "N/A"],
            ["WiFi SSID", device.wifi_ssid or "N/A"],
            ["Firmware", device.software_version or "N/A"],
            ["Last Connection", device.last_connection.isoformat() if device.last_connection else "N/A"],
            ["Last Test", device.last_manual_test.isoformat() if device.last_manual_test else "Never"],
        ]
        
        print(tabulate(info, tablefmt="grid"))
    
    async def run(self) -> None:
        """Run the CLI."""
        # Parse command line arguments
        args = self.parser.parse_args()
        
        # Handle version flag
        if args.version:
            print(f"Nest Protect MCP v{__version__}")
            return
        
        # Set log level
        logging.getLogger().setLevel(args.log_level)
        
        # If no command is provided, show help
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            # Initialize server for commands that need it
            if args.command in ["server", "devices", "device", "hush", "test"]:
                self.server = await self._init_server(args)
            
            # Handle commands
            if args.command == "server":
                await self._run_server(args)
            elif args.command == "devices":
                await self._list_devices(args)
            elif args.command == "device":
                await self._show_device(args)
            elif args.command == "hush":
                await self._hush_alarm(args)
            elif args.command == "test":
                await self._run_test(args)
            elif args.command == "web":
                await self._run_web_ui(args)
            else:
                self.parser.print_help()
        
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            sys.exit(1)
        finally:
            await self._shutdown()
    
    async def _run_server(self, args) -> None:
        """Run the MCP server."""
        logger.info(f"Starting Nest Protect MCP server on {args.host}:{args.port}")
        
        if args.reload:
            logger.info("Auto-reload enabled (development mode)")
            
            # For development with auto-reload
            config = uvicorn.Config(
                "nest_protect_mcp.server:app",
                host=args.host,
                port=args.port,
                reload=True,
                log_level=args.log_level.lower(),
            )
            server = uvicorn.Server(config)
            await server.serve()
        else:
            # For production
            try:
                # Keep the server running until interrupted
                while True:
                    await asyncio.sleep(3600)  # Sleep for 1 hour
            except asyncio.CancelledError:
                logger.info("Server shutdown requested")
    
    async def _list_devices(self, args) -> None:
        """List all Nest Protect devices."""
        devices = await self.server.get_devices()
        
        if args.format == "json":
            print(json.dumps([device.dict() for device in devices], indent=2))
        else:
            if not devices:
                print("No devices found")
                return
            self._print_devices_table(devices)
    
    async def _show_device(self, args) -> None:
        """Show details for a specific device."""
        device = await self.server.get_device(args.device_id)
        if not device:
            logger.error(f"Device {args.device_id} not found")
            sys.exit(1)
        
        if args.format == "json":
            print(json.dumps(device.dict(), indent=2))
        else:
            self._print_device_details(device)
    
    async def _hush_alarm(self, args) -> None:
        """Hush an alarm on a device."""
        logger.info(f"Hushing alarm on device {args.device_id} for {args.duration} seconds")
        
        try:
            success = await self.server.send_command({
                "command": "hush",
                "device_id": args.device_id,
                "params": {"duration": args.duration}
            })
            
            if success:
                print(f"Successfully hushed alarm on device {args.device_id}")
            else:
                logger.error(f"Failed to hush alarm on device {args.device_id}")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error hushing alarm: {e}", exc_info=True)
            sys.exit(1)
    
    async def _run_test(self, args) -> None:
        """Run a test on a device."""
        logger.info(f"Running {args.type} test on device {args.device_id}")
        
        try:
            success = await self.server.send_command({
                "command": "test",
                "device_id": args.device_id,
                "params": {"type": args.type}
            })
            
            if success:
                print(f"Successfully started {args.type} test on device {args.device_id}")
                print("The device will beep and flash during the test.")
            else:
                logger.error(f"Failed to start test on device {args.device_id}")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error running test: {e}", exc_info=True)
            sys.exit(1)
    
    async def _run_web_ui(self, args) -> None:
        """Run the web UI."""
        logger.info(f"Starting web UI on http://{args.host}:{args.port}")
        
        # This would be replaced with the actual web UI implementation
        print("Web UI is not yet implemented.")
        print(f"It would be available at http://{args.host}:{args.port}")
        
        # Keep the process running
        try:
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except asyncio.CancelledError:
            logger.info("Web UI shutdown requested")


def main() -> None:
    """Entry point for the CLI."""
    cli = NestProtectCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
