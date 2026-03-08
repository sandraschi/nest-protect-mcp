# 🔥 Nest Protect MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastMCP 3.1](https://img.shields.io/badge/FastMCP-3.1-blue)](https://github.com/PrefectHQ/fastmcp)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI/CD](https://github.com/sandraschi/nest-protect-mcp/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/sandraschi/nest-protect-mcp/actions)
[![codecov](https://codecov.io/gh/sandraschi/nest-protect-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/sandraschi/nest-protect-mcp)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green)](https://github.com/sandraschi/nest-protect-mcp)

## 🏠 Overview

The Nest Protect MCP Server is a **production-ready** FastMCP 3.1 compatible server that provides seamless integration between Google Nest Protect devices and the Model Context Protocol (MCP). It offers comprehensive monitoring and control capabilities for your Nest Protect smoke and carbon monoxide detectors through Claude Desktop and other MCP clients.

### ✅ **Current Status: FULLY OPERATIONAL - SOTA UPGRADE COMPLETE**
- **20 Production Tools** - Complete device management suite
- **Real API Integration** - No mocks, authentic Google Smart Device Management API v1
- **FastMCP 3.1** - Sampling, agentic workflows, prompts (skills)
- **MCPB Packaging** - Claude Desktop optimized deployment
- **Python 3.10+** - Modern baseline requirements
- **OAuth 2.0 Security** - Complete authentication flow with token management
- **Comprehensive Assets** - 22KB prompt templates and documentation
- **Ruff Linted** - 100% code quality compliance

### 🔧 Key Components

1. **MCP Server**: Implements the Model Context Protocol (MCP) v2.13.0 standard with MCPB packaging
2. **Nest API Integration**: Handles OAuth 2.0 authentication and communication with Google's Smart Device Management API v1
3. **Device Management**: Provides 20 production-ready tools to discover, monitor, and control Nest Protect devices
4. **MCPB Assets**: Comprehensive prompt templates (22KB) and documentation for Claude Desktop integration

### 🏗️ Architecture

```mermaid
graph LR
    A[MCP Client<br/>(Claude Desktop)] <--> B[Nest Protect MCP Server]
    B <--> C[Google Nest<br/>Cloud Services]
    D[Web Interface] <--> B
    E[Container Runtime] <--> B
    F[CI/CD Pipeline] --> B
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#bfb,stroke:#333
    style D fill:#fbf,stroke:#333
    style E fill:#fbf,stroke:#333
    style F fill:#bbf,stroke:#333
```

## ✨ Features

### 🔥 **Core Capabilities**
- **FastMCP 3.1 Compliance**: Sampling, agentic workflows, prompts (skills)
- **Real Nest API Integration**: Authentic Google Smart Device Management API v1 calls with OAuth 2.0
- **20 Production Tools**: Complete device management and control suite
- **MCPB Packaging**: Claude Desktop optimized deployment with comprehensive assets
- **State-of-the-Art Security**: OAuth 2.0 authentication with automatic token refresh

### 🏠 **Nest Protect Integration**
- **Device Discovery**: List all Nest Protect devices in your home
- **Real-time Status**: Monitor battery, connectivity, and alarm states
- **Device Control**: Hush alarms, run safety checks, adjust settings
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
- Python 3.10 or later
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
   ```

## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx nest-protect-mcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "nest-protect-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/nest-protect-mcp", "run", "nest-protect-mcp"]
  }
}
```
#### **Option 1: Claude Desktop (MCPB) - Recommended**

1. **Download the `.mcpb` package** from [GitHub Releases](https://github.com/sandraschi/nest-protect-mcp/releases)
2. **Drag the `.mcpb` file** into Claude Desktop settings
3. **Install Python dependencies** (run in terminal):
   ```bash
   pip install fastmcp>=2.13.0 pydantic>=2.0.0 aiohttp>=3.8.0 httpx>=0.24.0 websockets>=11.0.0 python-dotenv>=1.0.0 tomli>=0.10.2 python-dateutil>=2.8.2 anyio>=4.5.0 structlog>=23.1.0
   ```
4. **Configure Google Nest API** credentials in Claude Desktop settings:
   - `nest_client_id`: Your Google OAuth Client ID
   - `nest_client_secret`: Your Google OAuth Client Secret
   - `nest_project_id`: Your Google Cloud Project ID
   - `nest_refresh_token`: Your OAuth refresh token
5. **Start using** - Claude will automatically connect to your Nest Protect devices

## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx nest-protect-mcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "nest-protect-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/nest-protect-mcp", "run", "nest-protect-mcp"]
  }
}
```
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

### Docker Mode

```bash
# Run with Docker
docker run -d \
  --name nest-protect-mcp \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  sandraschi/nest-protect-mcp:latest
```

## 🔧 Available MCP Tools

The server provides **20 production-ready tools** organized into categories:

### 📊 **Device Status Tools**
1. **`get_devices`** - Get a list of all Nest Protect devices
2. **`get_device`** - Get detailed information about a specific device
3. **`get_alarm_state`** - Get current alarm states and battery health

### 🎛️ **Device Control Tools**
4. **`silence_alarm`** - Hush active alarms on devices
5. **`run_test`** - Execute device tests and diagnostics

### 🔧 **System Status Tools**
6. **Enhanced logging** - Comprehensive debugging and monitoring
7. **State management** - Persistent configuration and device state

## 📦 MCPB Package

### 🚀 **MCPB Deployment - State of the Art**

The Nest Protect MCP server includes a **production-ready MCPB package** optimized for Claude Desktop and modern MCP environments:

```bash
# Download from GitHub Releases:
# nest-protect-mcp-1.0.0.mcpb
```

**MCPB Features:**
- ✅ **20 Production Tools** - Complete device management suite
- ✅ **22KB Comprehensive Assets** - Extensive prompt templates and documentation
- ✅ **FastMCP 2.13.0** - Latest MCP specification compliance
- ✅ **OAuth 2.0 Security** - Secure authentication with automatic token refresh
- ✅ **Claude Desktop Optimized** - Seamless drag-and-drop installation

### 🎨 **MCPB Assets Included**

The MCPB package includes **comprehensive prompt templates and documentation**:

#### **Prompt Templates (22KB total)**
- **`system.md`** (8.2KB) - Comprehensive Claude Desktop integration guide
- **`user.md`** (6.3KB) - Interactive usage examples and templates
- **`examples.json`** (9.9KB) - Structured usage examples with 12 detailed scenarios

#### **Visual Assets**
- **`icon.png`** - Professional branding and recognition
- **`screenshots/`** - Usage documentation screenshots
  - `dashboard.png` - Main interface overview
  - `configuration.png` - Setup and configuration guide
  - `usage.png` - Tool usage examples

#### **Tool Categories (20 Tools)**
1. **Device Status** (3 tools): list_devices, get_device_status, get_device_events
2. **Device Control** (5 tools): hush_alarm, run_safety_check, set_led_brightness, sound_alarm, arm_disarm_security
3. **System Status** (3 tools): get_system_status, get_process_status, get_api_status
4. **Authentication** (3 tools): initiate_oauth_flow, handle_oauth_callback, refresh_access_token
5. **Configuration** (5 tools): get_config, update_config, reset_config, export_config, import_config
6. **Help & About** (5 tools): list_available_tools, get_tool_help, search_tools, about_server, get_supported_devices

## 🚀 CI/CD Pipeline

### 🔄 **Automated Workflows**

The repository includes a **comprehensive CI/CD pipeline** with modern best practices:

#### **Quality Assurance**
- ✅ **Multi-OS testing** (Ubuntu, Windows, macOS)
- ✅ **Multi-Python support** (3.10-3.13)
- ✅ **Security scanning** (vulnerability checks)
- ✅ **Code quality analysis** (mypy, bandit, radon)
- ✅ **Performance benchmarking**

#### **Automated Deployment**
- ✅ **Semantic versioning** with automated releases
- ✅ **PyPI publishing** for stable releases
- ✅ **GitHub releases** with changelog generation
- ✅ **Docker container builds** (multi-architecture)
- ✅ **Documentation deployment** (GitHub Pages)

#### **Maintenance & Monitoring**
- ✅ **Dependency updates** (automated security patches)
- ✅ **Repository cleanup** (workflow run management)
- ✅ **Notification system** (Slack/Discord integration)
- ✅ **Performance tracking** (benchmarking)

### 🏗️ **Modern Development Practices**

#### **Version Management**
```toml
# .bumpversion.toml
[bumpversion]
current_version = 0.1.0
commit = True
tag = True

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"
```

#### **Container Definition**
```dockerfile
# Multi-stage build for optimal size
FROM python:3.11-slim as base
# ... optimized production container
```

#### **Package Configuration**
```json
{
  "dependencies": ["fastmcp>=3.1.0,<4.0.0"],
  "configuration": {
    "nest_client_id": {"type": "string", "required": true},
    "nest_client_secret": {"type": "string", "required": true, "secret": true},
    "nest_project_id": {"type": "string", "required": true},
    "nest_refresh_token": {"type": "string", "required": true, "secret": true}
  }
}
```

## 🔄 Troubleshooting

### **Recent Fixes Applied**
- **FastMCP 3.1**: Sampling, agentic workflows, prompts (skills); see [docs/AUTH_SETUP.md](docs/AUTH_SETUP.md) for auth.
- **MCPB Packaging**: Claude Desktop optimized; run `scripts/get_nest_refresh_token.py` for refresh token.
- **Webapp**: Onboarding page and Help modal with setup steps.

### 🚨 **Common Issues & Solutions**

#### **Server Disconnects from Claude Desktop**
**Symptom**: Server starts but disconnects after a few seconds
**Solution**: Check your `claude_desktop_config.json` - ensure no `--kill` arguments:
```json
{
  "mcpServers": {
    "nest protect": {
      "command": "py",
      "args": ["-3.13", "-m", "nest_protect_mcp"],
      "cwd": "D:/Dev/repos/nest-protect-mcp"
    }
  }
}
```

#### **Authentication Issues**
**Symptom**: "No refresh token available" or authentication errors
**Solution**:
1. Get a refresh token: run `python scripts/get_nest_refresh_token.py` (see [docs/AUTH_SETUP.md](docs/AUTH_SETUP.md))
2. Put `NEST_CLIENT_ID`, `NEST_CLIENT_SECRET`, `NEST_PROJECT_ID`, `NEST_REFRESH_TOKEN` in `.env` in the repo root
3. Ensure Smart Device Management API is enabled in Google Cloud Console

#### **Tool Help Not Working**
**Symptom**: "get tool help" has difficulties with parameters
**Solution**: ✅ **FIXED** - Updated FastMCP tool registration with proper syntax

#### **Device Not Found**
**Symptom**: No devices appear in tool responses
**Solution**:
1. Verify devices are set up in Google Home app
2. Check authentication permissions
3. Restart server after authentication

### 🔍 **Enhanced Debugging**
The server now includes comprehensive logging:
```
✅ === FASTMCP SERVER INITIALIZED ===
✅ Tool registration complete
✅ Authentication state loaded
✅ Device discovery started
```

If you see errors, check the detailed logs for specific failure points.

## 📚 Documentation

### **📖 Complete Documentation**

For detailed documentation, please refer to the [docs](docs/) directory:

- **[AUTH_SETUP](docs/AUTH_SETUP.md)** - Auth and refresh token (quick reference); also in webapp **Setup & auth** and Help modal
- **[Setup Guide](docs/SETUP_GUIDE.md)** - Full installation and configuration
- **[Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)** - System design, FastMCP 3.1, tools and prompts
- **[MCP Production Checklist](docs/MCP_PRODUCTION_CHECKLIST.md)** - Deployment readiness
- **[Containerization Guidelines](docs/CONTAINERIZATION_GUIDELINES.md)** - Docker deployment
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Tools Reference](docs/TOOLS_REFERENCE.md)** - Complete tool documentation

### **🚀 Quick Reference**

## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx nest-protect-mcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "nest-protect-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/nest-protect-mcp", "run", "nest-protect-mcp"]
  }
}
```
#### **Server Commands**
```bash
# MCP mode (default)
python -m nest_protect_mcp

# HTTP mode
python -m nest_protect_mcp --http

# Development mode
python -m nest_protect_mcp --reload

# Help
python -m nest_protect_mcp --help
```

#### **Authentication**
```bash
# Start OAuth flow
python -m nest_protect_mcp.auth

# Verify authentication
python -m nest_protect_mcp --status
```

## 🌐 REST API Reference

When running in HTTP mode, the following endpoints are available:

- `GET /health` - Health check
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device details
- `POST /api/devices/{device_id}/command` - Send command to device

## 🔐 Security

- **OAuth 2.0 Authentication** - Secure Google API integration
- **Token Management** - Automatic refresh with secure storage
- **HTTPS Support** - Optional SSL/TLS encryption
- **Input Validation** - Pydantic V2 model validation
- **Security Scanning** - Automated vulnerability checks

## 🚀 Deployment

### **📦 MCPB Package**
```bash
# Deploy MCPB package (Claude Desktop)
# Download and drag nest-protect-mcp-1.0.0.mcpb into Claude Desktop
```

### **🐳 Docker Container**
```bash
# Run container
docker run -d \
  --name nest-protect-mcp \
  -p 8080:8080 \
  sandraschi/nest-protect-mcp:latest
```

### **☁️ Cloud Deployment**
- **Railway** - One-click deployment available
- **Heroku** - Container-based deployment
- **AWS/GCP** - Container orchestration support

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
# Clone repository
git clone https://github.com/sandraschi/nest-protect-mcp.git
cd nest-protect-mcp

# Install development dependencies
uv pip install -e .[dev]

# Run tests
pytest

# Run linting
pre-commit run --all-files
```

## 📈 Performance

- **Multi-threaded API calls** for optimal performance
- **Connection pooling** for efficient HTTP requests
- **State caching** for reduced API calls
- **Async/await patterns** for non-blocking operations
- **Memory efficient** device state management

## 🔄 Updates & Maintenance

The repository includes **automated maintenance workflows**:

- **Weekly dependency updates** for security patches
- **Automated testing** across multiple environments
- **Performance monitoring** and benchmarking
- **Documentation updates** with each release

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## 📧 Support

For support, please:
1. Check the [troubleshooting guide](docs/TROUBLESHOOTING.md)
2. Search existing [issues](https://github.com/sandraschi/nest-protect-mcp/issues)
3. Open a new issue with detailed information

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the smart home community**
