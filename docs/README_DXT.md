# Nest Protect MCP DXT Package

This document provides instructions for building, installing, and using the Nest Protect MCP DXT package.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- Nest Developer Account with access to the Nest API
- Google Cloud Project with the Nest Device Access API enabled
- OAuth 2.0 credentials for Nest API access

## Building the DXT Package

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/sandraschi/nest-protect-mcp.git
   cd nest-protect-mcp
   ```

2. **Build the DXT package** using the provided build script:
   ```powershell
   # Windows (PowerShell)
   .\build_dxt.ps1
   
   # Linux/macOS
   chmod +x build_dxt.ps1
   pwsh -File build_dxt.ps1
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Run tests (can be skipped with `-NoTests`)
   - Generate the DXT package in the `dist` directory

3. **Verify the DXT package** was created:
   ```
   dist/nest-protect-mcp-{version}.dxt
   ```

## Installing the DXT Package

1. **Copy the DXT file** to your Claude Desktop packages directory:
   - Windows: `%APPDATA%\Claude\packages\`
   - macOS: `~/Library/Application Support/Claude/packages/`
   - Linux: `~/.config/claude/packages/`

2. **Create a configuration file** at `~/.nest/config` with your Nest API credentials:
   ```json
   {
     "project_id": "your-project-id",
     "client_id": "your-client-id",
     "client_secret": "your-client-secret",
     "refresh_token": "your-refresh-token"
   }
   ```

3. **Restart Claude Desktop** to load the new package

4. **Verify installation** by checking the Claude Desktop logs or using the MCP client to list available services

## Using the Nest Protect MCP Service

Once installed, you can interact with the Nest Protect MCP service using the Claude Desktop MCP client or any HTTP client.

### Example: Getting Device Status

```python
# Using Python requests
import requests

# Get all devices
response = requests.get("http://localhost:8080/devices")
devices = response.json()
print("Available devices:", devices)

# Get status of a specific device
device_id = devices[0]["device_id"]
response = requests.get(f"http://localhost:8080/device/{device_id}/status")
status = response.json()
print(f"Status of {device_id}:", status)
```

### Example: Handling Alarms

```python
# Check for active alarms
response = requests.get("http://localhost:8080/alarms")
alarms = response.json()
print("Active alarms:", alarms)

# Hush an alarm (if supported by the device)
if alarms:
    device_id = alarms[0]["device_id"]
    response = requests.post(
        f"http://localhost:8080/device/{device_id}/hush",
        json={"duration": 10}  # Hush for 10 minutes
    )
    print("Hush response:", response.json())
```

## Available Prompts

The following prompts are available for natural language interaction:

- **Device Status**: "Show me the status of {device_name} including {details}."
- **Check Alarms**: "Are there any active {alarm_type} alarms? Show me {details_level} information."
- **Test Device**: "Run a {test_type} test on the {location} Nest Protect."
- **Hush Alarm**: "{action} the alarm on the {location} Nest Protect for {duration} minutes."
- **Battery Status**: "Show me the battery status of {device_filter} devices, sorted by {sort_by}."
- **Device History**: "Show me {event_type} events for {device_name} from {start_time} to {end_time}."
- **Connectivity Check**: "Which Nest Protects are currently {status}? Show me {details}."
- **Alert Preferences**: "{action} {alert_type} alerts for {device_name} via {notification_method}."
- **Device Information**: "Show me {details_level} information about the {location} Nest Protect."
- **Environment Check**: "What are the current {sensor_type} readings from {device_filter}?"

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure your OAuth 2.0 credentials are correct and have the necessary permissions
   - Verify that your refresh token is still valid
   - Check that your Google Cloud Project has the Nest Device Access API enabled

2. **Connection Issues**:
   - Make sure your Nest Protect devices are online and connected to the internet
   - Verify that your network allows connections to the Nest API
   - Check the Claude Desktop logs for connection errors

3. **Missing Permissions**:
   - Ensure your OAuth 2.0 client has the required scopes:
     - `https://www.googleapis.com/auth/sdm.service`
     - `https://www.googleapis.com/auth/pubsub`

### Viewing Logs

Logs can be found in the standard Claude Desktop log location:
- Windows: `%APPDATA%\Claude\logs\`
- macOS: `~/Library/Logs/Claude/`
- Linux: `~/.local/share/claude/logs/`

## Development

### Testing Changes

1. Make your changes to the code
2. Run tests:
   ```bash
   pytest -v
   ```
3. Rebuild the DXT package
4. Copy to Claude Desktop packages directory and restart

### Directory Structure

```
nest-protect-mcp/
├── config/                    # Configuration files
│   └── default.toml          # Default configuration
├── src/
│   └── nest_protect_mcp/     # Main package
│       ├── __init__.py       # Package initialization
│       ├── server.py         # Main server implementation
│       ├── models.py         # Data models
│       ├── exceptions.py     # Custom exceptions
│       └── cli.py           # Command-line interface
├── tests/                    # Test files
├── dxt_build.py              # DXT package builder
├── build_dxt.ps1             # Build script (PowerShell)
├── dxt_manifest.json         # DXT package manifest
└── pyproject.toml            # Project configuration
```

## License

MIT License - See [LICENSE](LICENSE) for details.
