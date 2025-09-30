"""
Unit tests for Nest Protect models.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from nest_protect_mcp.models import (
    ProtectConfig,
    ProtectDeviceState,
    ProtectCommand,
    ProtectEvent,
    ProtectAlarmState,
    ProtectAlarmType,
    ProtectBatteryState,
    ProtectHushState
)


class TestProtectAlarmState:
    """Test ProtectAlarmState enum."""

    def test_alarm_states(self):
        """Test all alarm state values."""
        assert ProtectAlarmState.OK == "ok"
        assert ProtectAlarmState.WARNING == "warning"
        assert ProtectAlarmState.EMERGENCY == "emergency"
        assert ProtectAlarmState.TESTING == "testing"
        assert ProtectAlarmState.OFF == "off"


class TestProtectAlarmType:
    """Test ProtectAlarmType enum."""

    def test_alarm_types(self):
        """Test all alarm type values."""
        assert ProtectAlarmType.SMOKE == "smoke"
        assert ProtectAlarmType.CO == "carbon_monoxide"
        assert ProtectAlarmType.HEAT == "heat"
        assert ProtectAlarmType.BATTERY == "battery"
        assert ProtectAlarmType.POWER == "power"
        assert ProtectAlarmType.WIFI == "wifi"
        assert ProtectAlarmType.TEST == "test"


class TestProtectBatteryState:
    """Test ProtectBatteryState enum."""

    def test_battery_states(self):
        """Test all battery state values."""
        assert ProtectBatteryState.OK == "ok"
        assert ProtectBatteryState.REPLACE == "replace_soon"
        assert ProtectBatteryState.CRITICAL == "replace_now"
        assert ProtectBatteryState.MISSING == "missing"
        assert ProtectBatteryState.INVALID == "invalid"


class TestProtectConfig:
    """Test ProtectConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ProtectConfig()
        assert config.project_id == ""
        assert config.client_id == ""
        assert config.client_secret == ""
        assert config.refresh_token == ""
        assert config.update_interval == 60
        assert config.mqtt_enabled is False
        assert config.log_level == "INFO"

    def test_config_with_values(self, sample_config):
        """Test configuration with provided values."""
        config = ProtectConfig(**sample_config)
        assert config.project_id == "test-project"
        assert config.client_id == "test-client-id"
        assert config.client_secret == "test-client-secret"
        assert config.refresh_token == "test-refresh-token"
        assert config.update_interval == 30

    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid update_interval
        with pytest.raises(ValidationError):
            ProtectConfig(update_interval=-1)

        with pytest.raises(ValidationError):
            ProtectConfig(update_interval=0)

    def test_env_prefix(self):
        """Test environment variable prefix configuration."""
        config = ProtectConfig()
        # The env_prefix should be configured in model_config
        assert hasattr(config, 'model_config')
        assert config.model_config.get('env_prefix') == "NEST_PROTECT_"


class TestProtectDeviceState:
    """Test ProtectDeviceState model."""

    def test_device_state_creation(self, sample_device_data):
        """Test creating device state with sample data."""
        device = ProtectDeviceState(**sample_device_data)
        assert device.device_id == "test-device-123"
        assert device.name == "Test Smoke Alarm"
        assert device.online is True
        assert device.battery_level == 85
        assert device.temperature == 22.5
        assert isinstance(device.last_connection, datetime)

    def test_device_state_validation(self):
        """Test device state validation."""
        # Test invalid battery level
        with pytest.raises(ValidationError):
            ProtectDeviceState(
                device_id="test",
                name="test",
                model="test",
                serial_number="test",
                battery_health="ok",
                co_alarm_state="ok",
                smoke_alarm_state="ok",
                heat_alarm_state="ok",
                battery_level=150  # Invalid: > 100
            )

        # Test invalid humidity
        with pytest.raises(ValidationError):
            ProtectDeviceState(
                device_id="test",
                name="test",
                model="test",
                serial_number="test",
                battery_health="ok",
                co_alarm_state="ok",
                smoke_alarm_state="ok",
                heat_alarm_state="ok",
                humidity=150  # Invalid: > 100
            )

    def test_optional_fields(self):
        """Test device state with minimal required fields."""
        device = ProtectDeviceState(
            device_id="test-device",
            name="Test Device",
            model="Test Model",
            serial_number="123456",
            battery_health="ok",
            co_alarm_state="ok",
            smoke_alarm_state="ok",
            heat_alarm_state="ok"
        )
        assert device.battery_level is None
        assert device.co_ppm is None
        assert device.temperature is None
        assert device.humidity is None


class TestProtectCommand:
    """Test ProtectCommand model."""

    def test_valid_commands(self):
        """Test valid command creation."""
        # Test hush command
        command = ProtectCommand(command="hush", device_id="device-123")
        assert command.command == "hush"
        assert command.device_id == "device-123"
        assert command.params == {}

        # Test test command with parameters
        command = ProtectCommand(
            command="test",
            params={"duration": 30}
        )
        assert command.command == "test"
        assert command.params == {"duration": 30}

    def test_invalid_command(self):
        """Test invalid command validation."""
        with pytest.raises(ValidationError):
            ProtectCommand(command="invalid_command")

    def test_command_without_device_id(self):
        """Test command without device_id (should apply to all devices)."""
        command = ProtectCommand(command="update")
        assert command.device_id is None


class TestProtectEvent:
    """Test ProtectEvent model."""

    def test_event_creation(self):
        """Test event creation with default timestamp."""
        event = ProtectEvent(
            event_id="event-123",
            device_id="device-456",
            event_type="alarm_triggered",
            event_data={"alarm_type": "smoke"}
        )
        assert event.event_id == "event-123"
        assert event.device_id == "device-456"
        assert event.event_type == "alarm_triggered"
        assert event.event_data == {"alarm_type": "smoke"}
        assert isinstance(event.timestamp, datetime)

    def test_event_with_custom_timestamp(self):
        """Test event with custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event = ProtectEvent(
            event_id="event-123",
            device_id="device-456",
            timestamp=custom_time,
            event_type="device_connected"
        )
        assert event.timestamp == custom_time

    def test_event_default_timestamp(self):
        """Test event with default timestamp."""
        event = ProtectEvent(
            event_id="event-456",
            device_id="device-789",
            event_type="alarm_triggered"
        )
        # The timestamp should be set automatically
        assert isinstance(event.timestamp, datetime)
        # Should be close to current time (within 1 second)
        now = datetime.now(timezone.utc)
        time_diff = abs((now - event.timestamp).total_seconds())
        assert time_diff < 1.0
