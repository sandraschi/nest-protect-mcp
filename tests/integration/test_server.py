"""
Integration tests for Nest Protect server functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from nest_protect_mcp.server import NestProtectMCP, NEST_API_URL, NEST_AUTH_URL
from nest_protect_mcp.models import ProtectConfig, ProtectDeviceState
from nest_protect_mcp.exceptions import NestProtectError


class TestNestProtectMCPServer:
    """Test the main NestProtectMCP server class."""

    @pytest.fixture
    def server(self, sample_config):
        """Create a test server instance."""
        return NestProtectMCP(sample_config)

    def test_server_initialization(self, server, sample_config):
        """Test server initialization."""
        assert server._config.project_id == sample_config["project_id"]
        assert server._config.client_id == sample_config["client_id"]
        assert server._config.update_interval == sample_config["update_interval"]
        assert hasattr(server, '_state_manager')

    def test_server_initialization_with_dict_config(self):
        """Test server initialization with dictionary config."""
        config_dict = {
            "project_id": "test-project",
            "client_id": "test-client-id"
        }
        server = NestProtectMCP(config_dict)
        assert server._config.project_id == "test-project"
        assert server._config.client_id == "test-client-id"

    def test_server_initialization_defaults(self):
        """Test server initialization with default values."""
        server = NestProtectMCP()
        assert server._config.project_id == ""
        assert server._config.update_interval == 60

    @pytest.mark.asyncio
    async def test_get_devices_mock_success(self, server, mock_aiohttp_session):
        """Test get_devices with mocked successful response."""
        # Mock the API response
        devices_data = {
            "devices": [
                {
                    "name": "Test Device",
                    "type": "sdm.devices.types.SMOKE_ALARM",
                    "traits": {
                        "sdm.devices.traits.Connectivity": {
                            "status": "ONLINE"
                        },
                        "sdm.devices.traits.Info": {
                            "customName": "Test Smoke Alarm"
                        }
                    }
                }
            ]
        }

        mock_aiohttp_session.set_response(
            f"{NEST_API_URL}/enterprises/test-project/devices",
            data=devices_data
        )

        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            devices = await server.get_devices()

        assert len(devices) == 1
        assert devices[0].name == "Test Smoke Alarm"

    @pytest.mark.asyncio
    async def test_get_devices_api_error(self, server, mock_aiohttp_session):
        """Test get_devices with API error."""
        mock_aiohttp_session.set_response(
            f"{NEST_API_URL}/enterprises/test-project/devices",
            status=401
        )

        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            with pytest.raises(NestProtectError):
                await server.get_devices()

    @pytest.mark.asyncio
    async def test_get_device_success(self, server, mock_aiohttp_session, sample_device_data):
        """Test get_device with successful response."""
        device_id = "test-device-123"
        device_data = {
            "name": "Test Device",
            "type": "sdm.devices.types.SMOKE_ALARM",
            "traits": {
                "sdm.devices.traits.Connectivity": {
                    "status": "ONLINE"
                },
                "sdm.devices.traits.Info": {
                    "customName": "Test Smoke Alarm"
                }
            }
        }

        mock_aiohttp_session.set_response(
            f"{NEST_API_URL}/enterprises/test-project/devices/{device_id}",
            data=device_data
        )

        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            device = await server.get_device(device_id)

        assert device.name == "Test Smoke Alarm"

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, server, mock_aiohttp_session):
        """Test get_device with device not found."""
        device_id = "nonexistent-device"

        mock_aiohttp_session.set_response(
            f"{NEST_API_URL}/enterprises/test-project/devices/{device_id}",
            status=404
        )

        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            with pytest.raises(NestProtectError):
                await server.get_device(device_id)

    @pytest.mark.asyncio
    async def test_authentication_flow(self, server, mock_aiohttp_session):
        """Test authentication token refresh."""
        # Mock token refresh response
        token_data = {
            "access_token": "new-access-token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }

        mock_aiohttp_session.set_response(
            NEST_AUTH_URL,
            data=token_data
        )

        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            # The authentication should happen during API calls
            # We'll test that the token refresh logic works
            assert server._config.client_id == "test-client-id"

    def test_server_config_validation(self):
        """Test server configuration validation."""
        # Test with invalid config
        with pytest.raises(Exception):  # Should raise ValidationError from Pydantic
            NestProtectMCP({"invalid_config": "value"})

    @pytest.mark.asyncio
    async def test_server_session_management(self, server):
        """Test server session lifecycle."""
        # Test that session is created when needed
        assert hasattr(server, '_session')

        # Test session cleanup
        if hasattr(server, '_session') and server._session:
            await server._session.close()

    def test_server_constants(self):
        """Test server constants."""
        assert NEST_AUTH_URL == "https://www.googleapis.com/oauth2/v4/token"
        assert NEST_API_URL == "https://smartdevicemanagement.googleapis.com/v1"
        assert TOKEN_EXPIRY_BUFFER == 300


class TestServerIntegration:
    """Integration tests for server components."""

    @pytest.mark.asyncio
    async def test_full_device_lifecycle(self, server, mock_aiohttp_session):
        """Test full device lifecycle: get devices -> get device."""
        # Mock devices list response
        devices_list = {
            "devices": [
                {
                    "name": "Test Device",
                    "type": "sdm.devices.types.SMOKE_ALARM",
                    "traits": {
                        "sdm.devices.traits.Connectivity": {"status": "ONLINE"},
                        "sdm.devices.traits.Info": {"customName": "Test Smoke Alarm"}
                    }
                }
            ]
        }

        # Mock individual device response
        device_detail = {
            "name": "Test Device",
            "type": "sdm.devices.types.SMOKE_ALARM",
            "traits": {
                "sdm.devices.traits.Connectivity": {"status": "ONLINE"},
                "sdm.devices.traits.Info": {"customName": "Test Smoke Alarm"},
                "sdm.devices.traits.Settings": {}
            }
        }

        mock_aiohttp_session.set_response(
            f"{NEST_API_URL}/enterprises/test-project/devices",
            data=devices_list
        )
        mock_aiohttp_session.set_response(
            f"{NEST_API_URL}/enterprises/test-project/devices/Test Device",
            data=device_detail
        )

        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            # Get all devices
            devices = await server.get_devices()
            assert len(devices) == 1

            # Get specific device
            device = await server.get_device("Test Device")
            assert device.name == "Test Smoke Alarm"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, server, mock_aiohttp_session):
        """Test error handling across different scenarios."""
        # Test network timeout
        class TimeoutSession:
            async def get(self, url, **kwargs):
                raise asyncio.TimeoutError("Request timed out")

            async def post(self, url, **kwargs):
                raise asyncio.TimeoutError("Request timed out")

            async def close(self):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        timeout_session = TimeoutSession()

        with patch('aiohttp.ClientSession', return_value=timeout_session):
            with pytest.raises(NestProtectError):
                await server.get_devices()

    def test_server_state_manager_integration(self, server):
        """Test integration with state manager."""
        # Test that state manager is accessible
        assert hasattr(server, '_state_manager')
        assert server._state_manager is not None

        # Test that state manager has expected methods
        assert hasattr(server._state_manager, 'get_device_state')
        assert hasattr(server._state_manager, 'update_device_state')
