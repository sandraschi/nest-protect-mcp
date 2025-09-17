# Nest Protect MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastMCP 2.12.0](https://img.shields.io/badge/FastMCP-2.12.0-blue)](https://github.com/modelcontextprotocol/fastmcp)

## 🏠 Overview

The Nest Protect MCP Server is a FastMCP 2.12.0 compatible server that acts as a bridge between the Google Nest API and the Model Context Protocol (MCP). It allows you to monitor and control your Nest Protect smoke and carbon monoxide detectors programmatically through a standardized interface.

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

- **MCP 2.12.0 Compliance**: Full implementation of the Model Context Protocol specification
- **Nest Protect Integration**:
  - Real-time status monitoring of all Nest Protect devices
  - Support for both wired and battery-powered models
  - Alarm state management and control
- **Multiple Interface Options**:
  - **MCP Protocol** (stdio) - Primary interface for MCP clients
  - **REST API** - For web-based control and integration
  - **WebSocket** - For real-time device updates
- **Security Features**:
  - OAuth 2.0 authentication with Google
  - Secure token storage and refresh
  - Configurable access controls
- **State Management**:
  - Persistent device state
  - Automatic reconnection
  - Configurable update intervals
- **Extensible Design**:
  - Plugin architecture for adding new device types
  - Webhook support for event notifications
  - MQTT bridge for Home Assistant integration

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

### No Refresh Token Available
If you see the error "No refresh token available", you need to complete the authentication process:

1. Make sure the server is running
2. In a separate terminal, run:
   ```bash
   python -m nest_protect_mcp.auth
   ```
3. Follow the browser prompts to authenticate with your Google account

### Authentication Errors
If you encounter authentication errors:
1. Check that your OAuth credentials are correct in the `.env` file
2. Make sure you've enabled the Smart Device Management API in Google Cloud Console
3. Try deleting the `.tokens.json` file and re-authenticating

### Device Not Found
If your Nest Protect devices aren't showing up:
1. Make sure they're properly set up in the Google Home app
2. Check that you've granted all necessary permissions during authentication
3. Restart the server after completing authentication

## 🔧 Available MCP Tools

The server provides the following MCP tools:

1. **get_devices** - List all Nest Protect devices
2. **get_device** - Get details for a specific device
3. **send_command** - Send a command to a device
4. **get_alarm_state** - Get current alarm state
5. **hush_alarm** - Hush the alarm on a device
6. **run_test** - Run a test on a device

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
