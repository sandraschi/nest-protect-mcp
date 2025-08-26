# Nest Protect MCP Server

A FastMCP 2.11.3 compatible server for interacting with Nest Protect smoke and CO detectors via MCP (Message Control Protocol).

## Features

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

## Installation

### Prerequisites
- Python 3.8+
- FastMCP 2.11.3 or later
- Google Cloud Project with Smart Device Management API enabled

### Installation Options

1. **From Source**:
   ```bash
   git clone https://github.com/yourusername/nest-protect-mcp.git
   cd nest-protect-mcp
   pip install -e .
   ```

2. **From PyPI**:
   ```bash
   pip install nest-protect-mcp
   ```

3. **Using Docker**:
   ```bash
   docker pull yourusername/nest-protect-mcp:latest
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
   ssl_key = "path/to/key.pem"
   
   # Authentication
   auth_required = true
   
   [nest]
   # Google Cloud Project settings
   project_id = "your-project-id"
   client_id = "your-client-id"
   client_secret = "your-client-secret"
   refresh_token = "your-refresh-token"
   ```

3. Set up environment variables (optional, overrides config file):
   ```bash
   export NEST_PROJECT_ID=your-project-id
   export NEST_CLIENT_ID=your-client-id
   export NEST_CLIENT_SECRET=your-client-secret
   export NEST_REFRESH_TOKEN=your-refresh-token
   ```

## Usage

### Starting the Server

#### MCP Mode (stdio):
```bash
nest-protect-mcp --mcp
```

#### HTTP Mode:
```bash
nest-protect-mcp --http
```

#### Both MCP and HTTP:
```bash
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
