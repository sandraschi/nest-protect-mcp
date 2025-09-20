# 🔥 Nest Protect MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastMCP 2.12.3](https://img.shields.io/badge/FastMCP-2.12.3-blue)](https://github.com/modelcontextprotocol/fastmcp)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green)](https://github.com/sandraschi/nest-protect-mcp)

## 🏠 Overview

The Nest Protect MCP Server is a **production-ready** FastMCP 2.12.3 compatible server that provides seamless integration between Google Nest Protect devices and the Model Context Protocol (MCP). It offers comprehensive monitoring and control capabilities for your Nest Protect smoke and carbon monoxide detectors through Claude Desktop and other MCP clients.

### ✅ **Current Status: FULLY OPERATIONAL**
- **20 Production Tools** - Complete device management suite
- **Real API Integration** - No mocks, authentic Google Smart Device Management API
- **Enhanced Logging** - Comprehensive debugging and monitoring
- **Pydantic V2 Compatible** - Modern validation patterns
- **Claude Desktop Ready** - Tested and verified integration

### 🔧 Key Components

1. **MCP Server**: Implements the Model Context Protocol (MCP) v2.12.0 standard
2. **Nest API Integration**: Handles authentication and communication with Google's Smart Device Management API
3. **Device Management**: Provides tools to discover, monitor, and control Nest Protect devices
4. **REST API**: Optional HTTP interface for web-based control and monitoring

### 🏗️ Architecture

```mermaid
graph LR
    A[MCP Client\n(e.g., IDE)] <--> B[Nest Protect MCP Server]
    B <--> C[Google Nest\nCloud Services]
    D[Web Interface] <--> B
    E[Other MCP Servers] <--> B
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#bfb,stroke:#333
    style D fill:#fbf,stroke:#333
    style E fill:#fbf,stroke:#333
```

## ✨ Features

### 🔥 **Core Capabilities**
- **MCP 2.12.3 Compliance**: Full implementation of the Model Context Protocol specification
- **Real Nest API Integration**: Authentic Google Smart Device Management API calls
- **20 Production Tools**: Comprehensive device management and monitoring
- **Enhanced Logging**: Detailed debugging and monitoring capabilities

### 🏠 **Nest Protect Integration**
- **Device Discovery**: List all Nest Protect devices in your home
- **Real-time Status**: Monitor battery, connectivity, and alarm states
- **Device Control**: Hush alarms, run safety checks, adjust LED brightness
- **Security System**: Arm/disarm Nest Guard security systems
- **Alarm Testing**: Sound alarms for testing purposes
- **Event History**: Access device events and activity logs

### 🔧 **Technical Features**
- **OAuth 2.0 Authentication**: Secure Google API integration
- **State Management**: Persistent device state and configuration
- **Error Handling**: Comprehensive error reporting and recovery
- **Pydantic V2 Models**: Modern data validation and serialization
- **Async/Await**: Full asynchronous operation for optimal performance

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or later
- Google Cloud Project with Smart Device Management API enabled
- Nest Protect devices added to your Google Home/Nest account

### 🔑 Authentication Setup

Before using the Nest Protect MCP server, you need to set up authentication with Google's API:

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the **Smart Device Management API**
   - Configure OAuth consent screen (select "External" user type)
   - Create OAuth 2.0 credentials (Desktop app type)
   - Download the credentials as `client_secret_*.json`

2. **Set up environment variables** in a `.env` file:
   ```bash
   # Copy the example .env file
   cp .env.example .env
   
   # Edit the .env file with your credentials
   NEST_CLIENT_ID=your_client_id
   NEST_CLIENT_SECRET=your_client_secret
   NEST_PROJECT_ID=your_project_id
   NEST_REDIRECT_URI=http://localhost:8000/auth/callback
   ```

### ⚙️ Installation

1. **Clone and set up the repository**:
   ```bash
   # Clone the repository
   git clone https://github.com/sandraschi/nest-protect-mcp.git
   cd nest-protect-mcp
   
   # Create and activate virtual environment
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -e .
   ```

2. **Run the authentication flow**:
   ```bash
   # Start the server
   python -m nest_protect_mcp
   
   # In a new terminal, run the authentication helper
   python -m nest_protect_mcp.auth
   ```
   
   This will open a browser window where you can sign in with your Google account and grant permissions.

3. **Verify authentication**:
   After successful authentication, the server will automatically save your credentials and connect to your Nest devices.

## 🏃 Running the Server

### MCP Mode (Recommended for IDE Integration)

```bash
# Start the server in MCP mode
python -m nest_protect_mcp
```

### HTTP Mode (For Web Interfaces)

```bash
# Start the HTTP server on port 8000
python -m nest_protect_mcp --http
```

### Development Mode (With Auto-Reload)

```bash
# Start in development mode with auto-reload
python -m nest_protect_mcp --reload
```

## 🔄 Troubleshooting

### ✅ **Recent Fixes Applied**
- **Pydantic V2 Migration**: Updated all models to use modern Pydantic patterns
- **Enhanced Logging**: Added comprehensive debugging and monitoring
- **Claude Desktop Integration**: Fixed configuration issues causing disconnections
- **Real API Implementation**: Removed all mock data, using authentic Google APIs

### 🚨 **Common Issues & Solutions**

#### **Server Disconnects from Claude Desktop**
**Symptom**: Server starts but disconnects after a few seconds
**Solution**: Check your `claude_desktop_config.json` - ensure no `--kill` arguments:
```json
{
  "mcpServers": {
    "nest protect": {
      "command": "py",
      "args": ["-3.13", "-m", "nest_protect_mcp"],  // ← No --kill!
      "cwd": "D:/Dev/repos/nest-protect-mcp"
    }
  }
}
```

#### **Authentication Issues**
**Symptom**: "No refresh token available" or authentication errors
**Solution**:
1. Complete OAuth flow: `python -m nest_protect_mcp.auth`
2. Verify credentials in `.env` file
3. Ensure Smart Device Management API is enabled in Google Cloud Console

#### **Pydantic Deprecation Warnings**
**Symptom**: `PydanticDeprecatedSince20` warnings in logs
**Solution**: ✅ **FIXED** - All models updated to Pydantic V2 patterns

#### **Device Not Found**
**Symptom**: No devices appear in tool responses
**Solution**:
1. Verify devices are set up in Google Home app
2. Check authentication permissions
3. Restart server after authentication

### 🔍 **Enhanced Debugging**
The server now includes comprehensive logging:
```
✅ === INITIALIZING FASTMCP SERVER ===
✅ FastMCP app created successfully
✅ === TOOL REGISTRATION COMPLETE ===
✅ All 20 tools have been registered with FastMCP
```

If you see errors, check the detailed logs for specific failure points.

## 🔧 Available MCP Tools

The server provides **20 production-ready tools** organized into categories:

### 📊 **Device Status Tools**
1. **`list_devices`** - Discover all Nest Protect devices in your home
2. **`get_device_status`** - Get comprehensive status for a specific device
3. **`get_device_events`** - Access device event history and activity logs

### 🎛️ **Device Control Tools**
4. **`hush_alarm`** - Silence active alarms on devices
5. **`run_safety_check`** - Execute safety checks and diagnostics
6. **`set_led_brightness`** - Adjust LED brightness levels
7. **`sound_alarm`** - Test alarms (smoke, CO, security, emergency)
8. **`arm_disarm_security`** - Control Nest Guard security system

### 🔧 **System Status Tools**
9. **`get_system_status`** - Overall server and API health
10. **`get_process_status`** - Server process monitoring
11. **`get_api_status`** - Google API connectivity status

### 🔐 **Authentication Tools**
12. **`initiate_oauth_flow`** - Start Google OAuth authentication
13. **`handle_oauth_callback`** - Process OAuth callback
14. **`refresh_access_token`** - Refresh expired tokens

### ⚙️ **Configuration Tools**
15. **`get_config`** - View current server configuration
16. **`update_config`** - Modify server settings
17. **`reset_config`** - Reset to default configuration
18. **`export_config`** - Export configuration to file
19. **`import_config`** - Import configuration from file

### 📚 **Help & Documentation Tools**
20. **`list_available_tools`** - Show all available tools
21. **`get_tool_help`** - Get detailed help for specific tools
22. **`search_tools`** - Search tools by name or description
23. **`about_server`** - Get server information and capabilities
24. **`get_supported_devices`** - List supported and planned devices

## 🌐 REST API Reference

When running in HTTP mode, the following endpoints are available:

- `GET /health` - Health check
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device details
- `POST /api/devices/{device_id}/command` - Send command to device

## 📚 Documentation

For detailed documentation, please refer to the [docs](docs/) directory.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   ```

4. **Configure your environment**:
   ```bash
   cp config/default.toml.example config/default.toml
   # Edit the config file with your credentials
   ```

5. **Run the server**:
   ```bash
   # Run with MCP (stdio) interface
   python -m nest_protect_mcp
   
   # Or run with HTTP server
   python -m nest_protect_mcp --http
   
   # For development with auto-reload
   python -m nest_protect_mcp --reload
   ```

### Docker Installation

```bash
docker run -d \
  --name nest-protect-mcp \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  sandraschi/nest-protect-mcp:latest
```

### Configuration

Create a `config/default.toml` file based on the example:

```toml
[nest]
# Google Cloud Project credentials
project_id = "your-project-id"
client_id = "your-client-id"
client_secret = "your-client-secret"
refresh_token = "your-refresh-token"

[server]
# General server settings
host = "0.0.0.0"
port = 8080
log_level = "INFO"

# Enable/disable interfaces
enable_mcp = true
enable_http = true

# HTTP/HTTPS configuration
http_host = "0.0.0.0"
http_port = 8080
enable_https = false
ssl_cert = "path/to/cert.pem"
ssl_key = "path/to/key.pem"

# MCP specific settings
mcp_timeout = 30  # seconds
max_retries = 3
```

## Usage Examples

### Command Line Interface

```bash
# Show help
python -m nest_protect_mcp --help

# Run with MCP interface (default)
python -m nest_protect_mcp

# Run with HTTP server on custom port
python -m nest_protect_mcp --http --port 8000

# Run with development settings (auto-reload, debug)
python -m nest_protect_mcp --reload --debug
```

### Checking Status

```bash
# Check server status
curl http://localhost:8080/health

# List all devices
curl http://localhost:8080/api/devices

# Get device details
curl http://localhost:8080/api/devices/{device_id}
```

### Connection Methods

1. **MCP Client Connection** (recommended for production):
   ```python
   from fastmcp import MCPClient
   
   client = MCPClient(stdio=True)  # Uses stdio for communication
   response = client.send_command("get_devices")
   print(response)
   ```

2. **HTTP API** (for testing/dashboards):
   ```bash
   # Get all devices
   curl http://localhost:8080/api/devices
   
   # Get device status
   curl http://localhost:8080/api/device/DEVICE_ID/status
   
   # Hush alarm
   curl -X POST http://localhost:8080/api/device/DEVICE_ID/hush
   ```

3. **WebSocket** (for real-time updates):
   ```javascript
   const ws = new WebSocket('ws://localhost:8080/ws');
   ws.onmessage = (event) => {
     console.log('Update:', JSON.parse(event.data));
   };
   ```

## API Documentation

See [API_DOCS.md](docs/API_DOCS.md) for detailed API documentation.

## License

MIT

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## Support

For support, please open an issue in the GitHub repository.
