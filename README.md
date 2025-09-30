# 🔥 Nest Protect MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastMCP 2.12.0](https://img.shields.io/badge/FastMCP-2.12.0-blue)](https://github.com/modelcontextprotocol/fastmcp)
[![CI/CD](https://github.com/sandraschi/nest-protect-mcp/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/sandraschi/nest-protect-mcp/actions)
[![codecov](https://codecov.io/gh/sandraschi/nest-protect-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/sandraschi/nest-protect-mcp)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green)](https://github.com/sandraschi/nest-protect-mcp)

## 🏠 Overview

The Nest Protect MCP Server is a **production-ready** FastMCP 2.12.0 compatible server that provides seamless integration between Google Nest Protect devices and the Model Context Protocol (MCP). It offers comprehensive monitoring and control capabilities for your Nest Protect smoke and carbon monoxide detectors through Claude Desktop and other MCP clients.

### ✅ **Current Status: FULLY OPERATIONAL**
- **15 Production Tools** - Complete device management suite
- **Real API Integration** - No mocks, authentic Google Smart Device Management API
- **Enhanced Logging** - Comprehensive debugging and monitoring
- **Pydantic V2 Compatible** - Modern validation patterns
- **Claude Desktop Ready** - Tested and verified integration
- **DXT Package** - Ready for MCP deployment
- **Docker Support** - Multi-architecture containers

### 🔧 Key Components

1. **MCP Server**: Implements the Model Context Protocol (MCP) v2.12.0 standard
2. **Nest API Integration**: Handles authentication and communication with Google's Smart Device Management API
3. **Device Management**: Provides tools to discover, monitor, and control Nest Protect devices
4. **REST API**: Optional HTTP interface for web-based control and monitoring

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
- **FastMCP 2.12.0 Compliance**: Full implementation of the Model Context Protocol specification
- **Real Nest API Integration**: Authentic Google Smart Device Management API calls
- **15 Production Tools**: Comprehensive device management and monitoring
- **Enhanced Logging**: Detailed debugging and monitoring capabilities
- **DXT Package Support**: Ready for MCP deployment environments

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
- Python 3.9 or later
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

The server provides **15 production-ready tools** organized into categories:

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

## 📦 DXT Package

### 🚀 **DXT Deployment**

The Nest Protect MCP server includes a **production-ready DXT package** for easy deployment in MCP environments:

```bash
# The DXT package is available at:
# dist/nest-protect-mcp-0.1.0.dxt
```

**DXT Features:**
- ✅ **15 Extensive Prompt Templates** - Comprehensive interaction patterns
- ✅ **Lightweight Dependencies** - Only FastMCP 2.12.0 included
- ✅ **Runtime Installation** - Dependencies installed by MCP client at startup
- ✅ **Rich Configuration** - Detailed parameter validation and descriptions

### 🎨 **Prompt Templates Included**

The DXT package includes **15 sophisticated prompt templates**:

1. **Device Status Overview** - Comprehensive device monitoring
2. **Alarm Management** - Active alarm detection and control
3. **Device Testing** - Safety check execution
4. **Battery Monitoring** - Battery level tracking and alerts
5. **Device History** - Event log analysis
6. **Connectivity Status** - Network and device connectivity
7. **Environmental Monitoring** - Sensor readings and trends
8. **Device Maintenance** - Troubleshooting and diagnostics
9. **System Configuration** - Settings and preferences
10. **Emergency Response** - Crisis situation handling
11. **Device Information** - Technical specifications
12. **Integration Setup** - Smart home platform integration
13. **Performance Analysis** - System performance metrics
14. **Troubleshooting Assistance** - Problem diagnosis and resolution

## 🚀 CI/CD Pipeline

### 🔄 **Automated Workflows**

The repository includes a **comprehensive CI/CD pipeline** with modern best practices:

#### **Quality Assurance**
- ✅ **Multi-OS testing** (Ubuntu, Windows, macOS)
- ✅ **Multi-Python support** (3.9-3.12)
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
  "dependencies": ["fastmcp==2.12.0"],
  "configuration": {
    "project_id": {"type": "string", "required": true},
    "client_id": {"type": "string", "required": true}
  }
}
```

## 🔄 Troubleshooting

### ✅ **Recent Fixes Applied**
- **FastMCP 2.12.0 Migration**: Updated to latest MCP specification
- **Enhanced Tool Registration**: Fixed parameter handling for tool help
- **DXT Package Creation**: Proper lightweight packaging
- **CI/CD Pipeline**: Comprehensive automation and testing

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
1. Complete OAuth flow: `python -m nest_protect_mcp.auth`
2. Verify credentials in `.env` file
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

- **[📋 MCP Production Checklist](docs/MCP_PRODUCTION_CHECKLIST.md)** - Deployment readiness guide
- **[🔧 Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)** - System design and components
- **[🐳 Containerization Guidelines](docs/CONTAINERIZATION_GUIDELINES.md)** - Docker deployment
- **[🛠️ Setup Guide](docs/SETUP_GUIDE.md)** - Installation and configuration
- **[🔍 Troubleshooting](docs/TROUBLESHOOTING_FASTMCP_2.12.md)** - Common issues and solutions
- **[📊 Tools Reference](docs/TOOLS_REFERENCE.md)** - Complete tool documentation

### **🚀 Quick Reference**

#### **Installation Commands**
```bash
# Standard installation
pip install -e .

# Development installation
pip install -e .[dev]

# DXT deployment (MCP environments)
# Use nest-protect-mcp-0.1.0.dxt
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

### **📦 DXT Package**
```bash
# Deploy DXT package
nest-protect-mcp-0.1.0.dxt
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
pip install -e .[dev]

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
1. Check the [troubleshooting guide](docs/TROUBLESHOOTING_FASTMCP_2.12.md)
2. Search existing [issues](https://github.com/sandraschi/nest-protect-mcp/issues)
3. Open a new issue with detailed information

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the smart home community**
