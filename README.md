# Nest Protect MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A FastMCP 2.11.3 compatible server for interacting with Nest Protect smoke and CO detectors via MCP (Message Control Protocol). This server provides a unified interface to monitor and control your Nest Protect devices programmatically.

## 🚀 Features

- **FastMCP 2.11.3 Compatibility**: Full support for MCP protocol with stdio and HTTP/S connections
- **Dual Connectivity**:
  - **MCP Protocol** (stdio) for client-server communication
  - **REST API** (HTTP/HTTPS) for testing and dashboard integration
- **Real-time Monitoring**: Event-driven updates for all Nest Protect devices
- **Multi-protocol Support**:
  - MCP over stdio (primary)
  - HTTP/HTTPS for web access
  - WebSocket for real-time updates
- **Device Management**:
  - Support for all Nest Protect models (wired and battery)
  - Device discovery and status monitoring
  - Alarm control and testing
- **Security**:
  - OAuth 2.0 authentication
  - Role-based access control
  - Secure token management
- **Stateful Operation**: Maintains device state between restarts
- **Extensible Architecture**: Easy to add new device types and features

## 🛠️ Installation

### Prerequisites
- Python 3.8 or later
- Google Cloud Project with Smart Device Management API enabled
- Nest Developer Account

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sandraschi/nest-protect-mcp.git
   cd nest-protect-mcp
   ```

2. **Set up a virtual environment (recommended)**:
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
   python -m nest_protect_mcp.cli
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
project_id = "your-project-id"
client_id = "your-client-id"
client_secret = "your-client-secret"
refresh_token = "your-refresh-token"

[server]
host = "0.0.0.0"
port = 8080
log_level = "INFO"
```

## Configuration

1. Copy the example configuration file:
   ```bash
   cp config/default.toml.example config/default.toml
   ```

2. Configure the server (default values shown):
   ```toml
   [server]
   # MCP Protocol (stdio)
   enable_mcp = true
   
   # HTTP Server
   enable_http = true
   http_host = "0.0.0.0"
   http_port = 8080
   
   # HTTPS (enable for production)
   enable_https = false
   ssl_cert = "path/to/cert.pem"
nest-protect-mcp status

# Run a safety test on a device
nest-protect-mcp test --device-id <device_id>
nest-protect-mcp --mcp --http
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
