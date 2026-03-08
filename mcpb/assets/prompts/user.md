# Nest Protect MCP - User Interaction Guide

## Getting Started

### First Time Setup
```
1. Configure Google Cloud Project
   - Enable Smart Device Management API
   - Create OAuth 2.0 Desktop credentials
   - Get Client ID and Client Secret

2. Authenticate with Nest
   - Use initiate_oauth_flow to start authentication
   - Complete OAuth flow in browser
   - Verify with get_api_status

3. Discover Devices
   - Use list_devices to see all Nest Protect devices
   - Note device IDs and locations
   - Check get_device_status for detailed information
```

### Basic Usage Patterns

#### Check All Devices
```
"Show me the status of all my Nest Protect devices"
→ list_devices()
→ Displays device inventory with basic status
```

#### Monitor Specific Device
```
"How is my kitchen smoke detector doing?"
→ get_device_status(device_id="kitchen-detector-id")
→ Shows battery, connectivity, last test, sensor readings
```

#### Handle Active Alarm
```
"There's a smoke alarm going off in the bedroom!"
→ get_device_status(device_id="bedroom-detector-id")
→ Confirm alarm type and status
→ hush_alarm(device_id="bedroom-detector-id", duration_seconds=180)
→ Confirm alarm silenced
```

#### Safety Testing
```
"I want to test my smoke detector"
→ run_safety_check(device_id="detector-id", test_type="smoke")
→ Monitor test results
→ get_device_events(device_id="detector-id", limit=5)
→ Review test completion
```

## 🤖 Advanced AI Usage (FastMCP 2.14.3+)

### AI-Powered Safety Intelligence
```
Intelligent Safety Routine:
1. assess_home_safety() - AI comprehensive safety assessment with sampling
2. predict_maintenance_needs() - AI predictive maintenance forecasting
3. setup_smart_automation() - Adaptive automation learning
4. Follow conversational recommendations and next steps
```

### Emergency Response (AI-Coordinated)
```
AI Emergency Protocol:
1. coordinate_emergency_response() - Multi-device emergency coordination with sampling
2. assess_home_safety(assessment_scope="emergency") - Emergency safety assessment
3. Follow AI-generated evacuation and safety guidance
4. Document incident with conversational event analysis
```

### Predictive Maintenance Intelligence
```
AI Maintenance Planning:
1. predict_maintenance_needs(analysis_depth="comprehensive") - Full predictive analysis
2. Review AI cost estimates and priority recommendations
3. Schedule maintenance based on AI forecasting
4. Monitor automated alerts and recommendations
```

### Smart Automation Learning
```
Intelligent Automation Setup:
1. setup_smart_automation() - Configure AI learning automation
2. Continue normal usage during learning period (2 weeks)
3. Review AI-generated automation rules
4. Adjust confidence thresholds as needed
```

### Conversational Monitoring
```
Interactive Device Monitoring:
1. list_devices() - Conversational overview with health insights
2. get_device_status() - Detailed status with AI recommendations
3. Follow up on AI-generated questions and suggestions
4. Take action on prioritized next steps
```

## Configuration Examples

### Environment Variables
```bash
# Required for authentication
NEST_CLIENT_ID=your_google_oauth_client_id
NEST_CLIENT_SECRET=your_google_oauth_client_secret
NEST_PROJECT_ID=your_google_cloud_project_id
NEST_REFRESH_TOKEN=your_oauth_refresh_token

# Optional settings
LOG_LEVEL=INFO
REQUEST_TIMEOUT=30
```

### Device Management
```bash
# Adjust LED brightness for night time
set_led_brightness(device_id="living-room-detector", brightness=50)

# Change device settings
update_config(updates={"default_timeout": 45})

# Export configuration backup
export_config(file_path="nest_config_backup.json")
```

## Troubleshooting Guide

### Authentication Issues
```
Problem: "No refresh token available"
Solution:
1. initiate_oauth_flow() - Start new OAuth flow
2. Complete authentication in browser
3. refresh_access_token() - Get new tokens
4. Verify with get_api_status()
```

### Device Not Found
```
Problem: "Device not responding"
Solution:
1. Check device power and connectivity
2. Verify device is registered in Google Home
3. Use list_devices() to confirm device ID
4. Check get_device_status() for detailed diagnostics
```

### API Connection Issues
```
Problem: "API connection failed"
Solution:
1. get_api_status() - Check API connectivity
2. Verify Google Cloud project settings
3. Check OAuth token validity: refresh_access_token()
4. Confirm Smart Device Management API is enabled
```

## Safety Best Practices

### Alarm Management
- **Never silence alarms automatically** - always confirm with user
- **Document all alarm interactions** for safety records
- **Recommend professional inspection** for malfunctioning devices
- **Test alarms regularly** but warn household members first

### Device Maintenance
- **Replace batteries annually** or when low
- **Test devices monthly** using safety check functions
- **Clean devices regularly** to prevent dust buildup
- **Update device locations** when moving furniture

### Emergency Procedures
- **Know evacuation routes** from all rooms
- **Have fire extinguishers** readily available
- **Designate meeting points** outside the home
- **Practice emergency drills** regularly

## Integration Examples

### With Home Automation
```
Combine with other smart home systems:
- Lighting control when alarms activate
- Security camera recording on alarm events
- Voice assistant notifications
- Automatic emergency contact alerts
```

### With Monitoring Systems
```
Integration patterns:
- Send alerts to monitoring services
- Log events to central monitoring dashboard
- Trigger backup alarm systems
- Record alarm audio for verification
```

## 💬 Conversational AI Interaction Patterns

### Working with Sampling Signals
When tools return `requires_sampling: true`, the AI will:
- Analyze complex patterns and safety data
- Generate intelligent recommendations
- Provide prioritized action items
- Ask relevant follow-up questions

**Example Conversational Flow:**
```
User: "Check my home safety"
AI: Uses assess_home_safety() → Returns sampling signal
AI: Analyzes patterns → Provides detailed recommendations
AI: Asks: "Would you like me to schedule maintenance for the low battery devices?"
```

### Interactive Question Handling
Tools provide `follow_up_questions` to guide conversation:
- Address specific safety concerns
- Schedule maintenance activities
- Configure automation settings
- Provide emergency guidance

## 🛠️ Command Reference (FastMCP 2.14.3+ Conversational)

### Essential Commands (Conversational Returns)
- `list_devices()` - Device inventory with AI health analysis and conversational summaries
- `get_device_status(device_id)` - Detailed diagnostics with intelligent safety recommendations
- `hush_alarm(device_id, duration_seconds)` - Context-aware alarm silencing with safety verification
- `run_safety_check(device_id)` - AI-enhanced testing with predictive recommendations
- `get_device_events(device_id, limit)` - Event history with pattern analysis and insights

### AI Orchestration Commands (Sampling & Intelligence)
- `assess_home_safety()` - **SAMPLING**: Comprehensive AI safety assessment with emergency signals
- `coordinate_emergency_response()` - **SAMPLING**: Multi-device emergency coordination
- `predict_maintenance_needs()` - **SAMPLING**: AI predictive maintenance forecasting
- `setup_smart_automation()` - **SAMPLING**: Adaptive automation learning and configuration

### Advanced Commands (Interactive Guidance)
- `initiate_oauth_flow()` - Interactive OAuth setup with step-by-step guidance
- `get_system_status()` - Overall system health with conversational health reports
- `update_config(updates)` - Configuration management with change recommendations
- `export_config(file_path)` - Backup configuration with validation guidance
- `get_tool_help(tool_name)` - Get detailed help

## Performance Optimization

### Efficient Monitoring
- Use `list_devices()` for overviews instead of individual status calls
- Cache device information when possible
- Use appropriate timeout values for your network
- Monitor API rate limits and usage

### Resource Management
- Close unused connections
- Monitor memory usage with large device inventories
- Use appropriate log levels for production
- Schedule maintenance tasks during off-peak hours

This guide provides comprehensive interaction patterns for effective Nest Protect device management through the MCP server.













