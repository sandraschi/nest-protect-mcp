# 🔧 Nest Protect MCP Server - Tools Reference Guide

**Quick Reference**: All 24 available tools organized by category for easy lookup.

---

## 📊 Device Status Tools (3)

### 🔥 `list_devices`
**Purpose**: Discover all Nest Protect devices in your home  
**Parameters**: None  
**Returns**: Device IDs, names, models, locations, online status  
**Example Use**: "Show me all my Nest Protect devices"

### 📊 `get_device_status` 
**Purpose**: Get real-time status of a specific device  
**Parameters**: `device_id` (string)  
**Returns**: Battery level, sensor status, Wi-Fi connectivity, health info  
**Example Use**: "Check the battery level of my bedroom smoke detector"

### 📅 `get_device_events`
**Purpose**: View recent events and history for a device  
**Parameters**: `device_id` (string), `hours_back` (integer, default: 24)  
**Returns**: Event timeline, alerts, maintenance notifications  
**Example Use**: "What happened with my kitchen smoke detector yesterday?"

---

## 🎛️ Device Control Tools (5)

### 🔇 `hush_alarm`
**Purpose**: Silence false alarms on Nest Protect devices  
**Parameters**: `device_id` (string)  
**Returns**: Confirmation of alarm silencing  
**Example Use**: "Stop the smoke alarm in the kitchen - it's just cooking smoke"

### ✅ `run_safety_check`
**Purpose**: Trigger manual safety test on device  
**Parameters**: `device_id` (string)  
**Returns**: Test results and device health status  
**Example Use**: "Run a safety test on the living room smoke detector"

### 💡 `set_led_brightness`
**Purpose**: Adjust LED brightness for nightlight feature  
**Parameters**: `device_id` (string), `brightness` (integer, 0-100)  
**Returns**: Confirmation of brightness setting  
**Example Use**: "Dim the hallway smoke detector LED to 20%"

### 🚨 `sound_alarm` ⚠️
**Purpose**: Test alarm systems (USE RESPONSIBLY!)  
**Parameters**: `device_id` (string), `alarm_type` (smoke/co/security/emergency), `duration_seconds` (5-60), `volume` (50-100)  
**Returns**: Test confirmation and results  
**Example Use**: "Test the smoke alarm for 10 seconds" (Warn household first!)

### 🔒 `arm_disarm_security`
**Purpose**: Control Nest Guard security system  
**Parameters**: `device_id` (string), `action` (arm_home/arm_away/disarm), `passcode` (optional)  
**Returns**: Security system status confirmation  
**Example Use**: "Arm the security system for away mode"

---

## 📡 System Status Tools (3)

### 🖥️ `get_system_status`
**Purpose**: Check overall MCP server health  
**Parameters**: None  
**Returns**: Server status, uptime, resource usage  
**Example Use**: "Is the Nest server running properly?"

### ⚡ `get_process_status`
**Purpose**: Monitor server process and performance  
**Parameters**: None  
**Returns**: CPU usage, memory consumption, process info  
**Example Use**: "How much memory is the Nest server using?"

### 📶 `get_api_status`
**Purpose**: Check connectivity to Google Nest API  
**Parameters**: None  
**Returns**: API connectivity, authentication status, rate limits  
**Example Use**: "Can the server connect to Google's Nest API?"

---

## ❓ Help & Documentation Tools (3)

### 📋 `list_available_tools`
**Purpose**: Discover all available tools and their categories  
**Parameters**: `category` (optional filter)  
**Returns**: Complete tool listing with descriptions  
**Example Use**: "What tools are available for device control?"

### ❓ `get_tool_help`
**Purpose**: Get detailed help for a specific tool  
**Parameters**: `tool_name` (string)  
**Returns**: Detailed usage instructions, parameters, examples  
**Example Use**: "How do I use the sound_alarm tool safely?"

### 🔍 `search_tools`
**Purpose**: Search for tools by name or functionality  
**Parameters**: `query` (string), `limit` (optional)  
**Returns**: Matching tools with relevance scores  
**Example Use**: "Find tools related to battery monitoring"

---

## 🔐 Authentication Tools (3)

### 🚀 `initiate_oauth_flow`
**Purpose**: Start OAuth 2.0 authentication with Google  
**Parameters**: `redirect_uri` (optional), `state` (optional)  
**Returns**: Authorization URL for user to visit  
**Example Use**: "I need to connect my Google account to access Nest devices"

### ✅ `handle_oauth_callback`
**Purpose**: Process OAuth callback after user authorization  
**Parameters**: `code` (string), `state` (optional), `expected_state` (optional), `redirect_uri` (optional)  
**Returns**: Authentication success and token storage confirmation  
**Example Use**: Called automatically after user authorizes access

### 🔄 `refresh_access_token`
**Purpose**: Renew expired OAuth access tokens  
**Parameters**: `force` (boolean, default: false)  
**Returns**: New token information and expiration time  
**Example Use**: "My authentication expired - refresh the connection"

---

## ⚙️ Configuration Tools (5)

### 📖 `get_config`
**Purpose**: View current server configuration  
**Parameters**: `section` (optional filter)  
**Returns**: Current configuration settings  
**Example Use**: "Show me the current OAuth settings"

### ✏️ `update_config`
**Purpose**: Modify server configuration settings  
**Parameters**: `section` (string), `settings` (object), `merge` (boolean)  
**Returns**: Updated configuration confirmation  
**Example Use**: "Update the API timeout to 30 seconds"

### 🔄 `reset_config`
**Purpose**: Reset configuration to default values  
**Parameters**: `section` (optional, or 'all')  
**Returns**: Reset confirmation and new settings  
**Example Use**: "Reset all settings to defaults"

### 💾 `export_config`
**Purpose**: Backup current configuration to file  
**Parameters**: `file_path` (optional), `format` (json/toml)  
**Returns**: Export confirmation and file location  
**Example Use**: "Backup my configuration before making changes"

### 📥 `import_config`
**Purpose**: Restore configuration from backup file  
**Parameters**: `file_path` (string), `merge` (boolean)  
**Returns**: Import confirmation and applied settings  
**Example Use**: "Restore my configuration from backup"

---

## 📖 About & Information Tools (2)

### 🔥 `about_server`
**Purpose**: Learn about the MCP server capabilities  
**Parameters**: `level` (simple/intermediate/technical)  
**Returns**: Multi-level information about server features  
**Example Use**: "Give me a technical overview of what this server can do"

### 📱 `get_supported_devices`
**Purpose**: See which Nest devices are supported  
**Parameters**: None  
**Returns**: Current and planned device support information  
**Example Use**: "What Nest devices work with this server?"

---

## 🚀 Quick Start Examples

### **First Time Setup**
1. `about_server` - Learn what the server can do
2. `get_supported_devices` - Check device compatibility  
3. `initiate_oauth_flow` - Connect your Google account
4. `list_devices` - Discover your Nest devices

### **Daily Monitoring**
1. `get_system_status` - Check server health
2. `list_devices` - See all device status at a glance
3. `get_device_status` - Deep dive into specific devices
4. `get_device_events` - Review recent alerts

### **Device Control**
1. `get_device_status` - Check current state first
2. `set_led_brightness` - Adjust nightlight
3. `run_safety_check` - Test device functionality
4. `hush_alarm` - Handle false alarms

### **Troubleshooting**
1. `get_api_status` - Check Google API connectivity
2. `get_process_status` - Monitor server performance
3. `refresh_access_token` - Fix authentication issues
4. `get_tool_help` - Get detailed usage instructions

---

## ⚠️ Safety Notes

### **🚨 sound_alarm Tool**
- **⚠️ WARNING**: This triggers real alarms on real devices
- **Always warn household members** before testing
- **Keep duration short** (5-10 seconds recommended)
- **Use only for testing and maintenance**
- **Emergency services may respond** to excessive alarm testing

### **🔒 Security Tools**
- **Passcode required** for disarming security systems
- **Physical access** may be needed for some operations
- **Test during safe hours** to avoid false emergencies

### **🔑 Authentication**
- **Keep OAuth tokens secure** - they provide full device access
- **Refresh tokens periodically** for security
- **Revoke access** through Google Account settings if compromised

---

## 🔍 Tool Categories Summary

| Category | Tools | Purpose |
|----------|--------|---------|
| **Device Status** | 3 | Monitor and discover devices |
| **Device Control** | 5 | Direct device manipulation |
| **System Status** | 3 | Server health and diagnostics |
| **Help & Docs** | 3 | Tool discovery and assistance |
| **Authentication** | 3 | OAuth 2.0 flow management |
| **Configuration** | 5 | Settings and preferences |
| **About/Info** | 2 | Server and device information |
| **TOTAL** | **24** | **Complete smart home control** |

---

**Pro Tip**: Start with `about_server` to get oriented, then use `list_available_tools` to explore what's possible with your specific setup! 🎯
