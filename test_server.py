import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from src.nest_protect_mcp.server import NestProtectMCP
from src.nest_protect_mcp.models import ProtectConfig

async def main():
    # Create a test configuration
    config = {
        "project_id": "test-project",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "refresh_token": "test-refresh-token"
    }
    
    # Initialize the server
    server = NestProtectMCP(config)
    
    try:
        # Test getting devices
        print("Testing get_devices...")
        devices = await server.get_devices()
        print(f"Found {len(devices)} devices")
        
        # Test getting a specific device if available
        if devices:
            device_id = devices[0].device_id
            print(f"\nTesting get_device for device {device_id}...")
            device = await server.get_device(device_id)
            print(f"Device info: {device}")
        
        print("\nServer test completed successfully!")
        
    except Exception as e:
        print(f"Error during server test: {e}")
        raise
    finally:
        # Cleanup
        if hasattr(server, '_session') and server._session:
            await server._session.close()

if __name__ == "__main__":
    asyncio.run(main())
