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

## Advanced Usage

### Routine Monitoring
```
Daily Check Routine:
1. list_devices() - Overview of all devices
2. Check battery levels and connectivity
3. Review recent events: get_device_events(limit=10)
4. Run safety checks monthly: run_safety_check()
```

### Emergency Response
```
Alarm Response Protocol:
1. Identify device: list_devices() or get_device_status()
2. Assess situation: Check alarm type and severity
3. Silence if appropriate: hush_alarm(duration_seconds=300)
4. Investigate cause and resolve
5. Document: get_device_events() for incident log
```

### Maintenance Tasks
```
Monthly Maintenance:
1. Test all devices: run_safety_check() for each device
2. Check battery levels: get_device_status() for each device
3. Review event history: get_device_events(limit=50)
4. Clean devices and update locations if needed
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

## Command Reference

### Essential Commands
- `list_devices()` - Device inventory and status
- `get_device_status(device_id)` - Detailed device information
- `hush_alarm(device_id, duration_seconds)` - Silence alarms
- `run_safety_check(device_id)` - Test device functionality
- `get_device_events(device_id, limit)` - Review activity logs

### Advanced Commands
- `initiate_oauth_flow()` - Start authentication
- `get_system_status()` - Overall system health
- `update_config(updates)` - Modify settings
- `export_config(file_path)` - Backup configuration
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
