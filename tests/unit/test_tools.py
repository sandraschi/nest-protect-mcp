"""
Unit tests for Nest Protect tools.
"""
import pytest
from pydantic import ValidationError

from nest_protect_mcp.tools import (
    DeviceType,
    AlarmState,
    BatteryState,
    DeviceInfo,
    GetDevicesTool,
    GetDeviceTool,
    SilenceAlarmTool,
    GetDeviceHistoryTool,
    tool_schemas
)


class TestDeviceType:
    """Test DeviceType enum."""

    def test_device_types(self):
        """Test all device type values."""
        assert DeviceType.SMOKE_ALARM == "sdm.devices.types.SMOKE_ALARM"
        assert DeviceType.CO_ALARM == "sdm.devices.types.COA_ALARM"
        assert DeviceType.CAMERA == "sdm.devices.types.CAMERA"
        assert DeviceType.THERMOSTAT == "sdm.devices.types.THERMOSTAT"
        assert DeviceType.DISPLAY == "sdm.devices.types.DISPLAY"
        assert DeviceType.DOORBELL == "sdm.devices.types.DOORBELL"


class TestAlarmState:
    """Test AlarmState enum."""

    def test_alarm_states(self):
        """Test all alarm state values."""
        assert AlarmState.OK == "OK"
        assert AlarmState.WARNING == "WARNING"
        assert AlarmState.CRITICAL == "CRITICAL"


class TestBatteryState:
    """Test BatteryState enum."""

    def test_battery_states(self):
        """Test all battery state values."""
        assert BatteryState.NORMAL == "NORMAL"
        assert BatteryState.LOW == "LOW"
        assert BatteryState.CRITICAL == "CRITICAL"


class TestDeviceInfo:
    """Test DeviceInfo model."""

    def test_device_info_creation(self):
        """Test creating device info."""
        device = DeviceInfo(
            id="device-123",
            name="Test Device",
            type=DeviceType.SMOKE_ALARM,
            online=True,
            battery_state=BatteryState.NORMAL,
            alarm_state=AlarmState.OK,
            last_connection="2023-01-01T12:00:00Z"
        )
        assert device.id == "device-123"
        assert device.name == "Test Device"
        assert device.type == DeviceType.SMOKE_ALARM
        assert device.online is True
        assert device.battery_state == BatteryState.NORMAL

    def test_device_info_optional_fields(self):
        """Test device info with optional fields."""
        device = DeviceInfo(
            id="device-456",
            name="Minimal Device",
            type=DeviceType.CAMERA,
            online=False
        )
        assert device.battery_state is None
        assert device.alarm_state is None
        assert device.last_connection is None


class TestGetDevicesTool:
    """Test GetDevicesTool model."""

    def test_get_devices_tool(self):
        """Test GetDevicesTool creation."""
        tool = GetDevicesTool()
        # This tool has no parameters, just test that it can be instantiated
        assert isinstance(tool, GetDevicesTool)


class TestGetDeviceTool:
    """Test GetDeviceTool model."""

    def test_get_device_tool(self):
        """Test GetDeviceTool with device_id."""
        tool = GetDeviceTool(device_id="device-123")
        assert tool.device_id == "device-123"

    def test_get_device_tool_validation(self):
        """Test GetDeviceTool validation."""
        with pytest.raises(ValidationError):
            GetDeviceTool()  # Missing required device_id


class TestSilenceAlarmTool:
    """Test SilenceAlarmTool model."""

    def test_silence_alarm_tool_default_duration(self):
        """Test SilenceAlarmTool with default duration."""
        tool = SilenceAlarmTool(device_id="device-123")
        assert tool.device_id == "device-123"
        assert tool.duration_seconds == 300  # Default value

    def test_silence_alarm_tool_custom_duration(self):
        """Test SilenceAlarmTool with custom duration."""
        tool = SilenceAlarmTool(device_id="device-123", duration_seconds=600)
        assert tool.duration_seconds == 600

    def test_silence_alarm_tool_validation(self):
        """Test SilenceAlarmTool validation."""
        # Test too short duration
        with pytest.raises(ValidationError):
            SilenceAlarmTool(device_id="device-123", duration_seconds=30)  # < 60

        # Test too long duration
        with pytest.raises(ValidationError):
            SilenceAlarmTool(device_id="device-123", duration_seconds=7200)  # > 3600

    def test_silence_alarm_tool_missing_device_id(self):
        """Test SilenceAlarmTool validation for missing device_id."""
        with pytest.raises(ValidationError):
            SilenceAlarmTool(duration_seconds=300)  # Missing device_id


class TestGetDeviceHistoryTool:
    """Test GetDeviceHistoryTool model."""

    def test_get_device_history_tool_defaults(self):
        """Test GetDeviceHistoryTool with default values."""
        tool = GetDeviceHistoryTool(device_id="device-123")
        assert tool.device_id == "device-123"
        assert tool.start_time is None
        assert tool.end_time is None
        assert tool.max_results == 10

    def test_get_device_history_tool_custom_values(self):
        """Test GetDeviceHistoryTool with custom values."""
        tool = GetDeviceHistoryTool(
            device_id="device-123",
            start_time="2023-01-01T00:00:00Z",
            end_time="2023-01-02T00:00:00Z",
            max_results=50
        )
        assert tool.start_time == "2023-01-01T00:00:00Z"
        assert tool.end_time == "2023-01-02T00:00:00Z"
        assert tool.max_results == 50

    def test_get_device_history_tool_validation(self):
        """Test GetDeviceHistoryTool validation."""
        # Test invalid max_results (too low)
        with pytest.raises(ValidationError):
            GetDeviceHistoryTool(device_id="device-123", max_results=0)

        # Test invalid max_results (too high)
        with pytest.raises(ValidationError):
            GetDeviceHistoryTool(device_id="device-123", max_results=150)

    def test_get_device_history_tool_missing_device_id(self):
        """Test GetDeviceHistoryTool validation for missing device_id."""
        with pytest.raises(ValidationError):
            GetDeviceHistoryTool(max_results=10)  # Missing device_id


class TestToolSchemas:
    """Test tool_schemas definitions."""

    def test_tool_schemas_structure(self):
        """Test that tool_schemas has the expected structure."""
        assert "get_devices" in tool_schemas
        assert "get_device" in tool_schemas

        # Check get_devices schema
        get_devices_schema = tool_schemas["get_devices"]
        assert get_devices_schema["name"] == "get_devices"
        assert "parameters" in get_devices_schema
        assert "returns" in get_devices_schema

        # Check get_device schema
        get_device_schema = tool_schemas["get_device"]
        assert get_device_schema["name"] == "get_device"
        assert "parameters" in get_device_schema
        assert "required" in get_device_schema["parameters"]

    def test_get_devices_schema_details(self):
        """Test get_devices schema details."""
        schema = tool_schemas["get_devices"]
        assert schema["description"] == "Get a list of all Nest Protect devices"
        assert schema["parameters"] == {}

        returns_schema = schema["returns"]
        assert returns_schema["type"] == "array"
        assert "items" in returns_schema

        # Check item properties
        item_props = returns_schema["items"]["properties"]
        required_fields = ["id", "name", "type", "online"]
        for field in required_fields:
            assert field in item_props

    def test_get_device_schema_details(self):
        """Test get_device schema details."""
        schema = tool_schemas["get_device"]
        assert schema["description"] == "Get detailed information about a specific Nest Protect device"

        params = schema["parameters"]
        assert params["type"] == "object"
        assert "device_id" in params["properties"]
        assert params["required"] == ["device_id"]

        returns_schema = schema["returns"]
        assert returns_schema["type"] == "object"
        assert "id" in returns_schema["properties"]
