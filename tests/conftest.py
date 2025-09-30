"""
Pytest configuration for Nest Protect MCP tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "project_id": "test-project",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "refresh_token": "test-refresh-token",
        "update_interval": 30
    }

@pytest.fixture
def sample_device_data():
    """Sample device data for testing."""
    from datetime import datetime, timezone
    from nest_protect_mcp.models import ProtectBatteryState, ProtectAlarmState
    return {
        "device_id": "test-device-123",
        "name": "Test Smoke Alarm",
        "model": "Nest Protect",
        "serial_number": "123456789",
        "online": True,
        "battery_health": ProtectBatteryState.OK,
        "co_alarm_state": ProtectAlarmState.OK,
        "smoke_alarm_state": ProtectAlarmState.OK,
        "heat_alarm_state": ProtectAlarmState.OK,
        "battery_level": 85,
        "co_ppm": 0.0,
        "temperature": 22.5,
        "humidity": 45.0,
        "last_connection": datetime.now(timezone.utc),
        "software_version": "1.2.3",
        "wifi_ip": "192.168.1.100",
        "wifi_ssid": "TestNetwork"
    }

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing."""
    class MockResponse:
        def __init__(self, status=200, data=None):
            self.status = status
            self._data = data or {}

        async def json(self):
            return self._data

        async def text(self):
            return str(self._data)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockSession:
        def __init__(self):
            self.responses = {}

        def set_response(self, url, status=200, data=None):
            self.responses[url] = MockResponse(status, data)

        async def get(self, url, **kwargs):
            return self.responses.get(url, MockResponse(404))

        async def post(self, url, **kwargs):
            return self.responses.get(url, MockResponse(404))

        async def close(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockSession()
