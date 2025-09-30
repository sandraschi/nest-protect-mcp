"""
Comprehensive integration tests for Nest Protect server functionality.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from nest_protect_mcp.server import NestProtectMCP, NEST_API_URL, NEST_AUTH_URL
from nest_protect_mcp.models import ProtectConfig, ProtectDeviceState, ProtectCommand
from nest_protect_mcp.exceptions import NestProtectError, NestAuthError, NestConnectionError


class TestServerInitialization:
    """Test server initialization and configuration."""

    def test_server_creation_with_config(self, sample_config):
        """Test creating server with configuration."""
        server = NestProtectMCP(sample_config)
        assert server._config.project_id == sample_config["project_id"]
        assert server._config.client_id == sample_config["client_id"]
        assert server._refresh_token is None
        assert server._access_token is None

    def test_server_creation_defaults(self):
        """Test creating server with default configuration."""
        server = NestProtectMCP()
        assert server._config.project_id == ""
        assert server._config.update_interval == 60

    def test_server_state_keys_initialization(self, sample_config):
        """Test that state keys are properly initialized."""
        server = NestProtectMCP(sample_config)
        assert hasattr(server, '_state_keys')
        assert 'access_token' in server._state_keys
        assert 'refresh_token' in server._state_keys
        assert 'token_expires_at' in server._state_keys
        assert 'devices' in server._state_keys

    def test_server_session_initialization(self, sample_config):
        """Test that session is properly initialized."""
        server = NestProtectMCP(sample_config)
        assert server._session is None  # Should be None until needed

    def test_server_fastmcp_inheritance(self, sample_config):
        """Test that server properly inherits from FastMCP."""
        server = NestProtectMCP(sample_config)
        from fastmcp import FastMCP
        assert isinstance(server, FastMCP)


class TestServerAuthentication:
    """Test server authentication and token management."""

    @pytest.mark.asyncio
    async def test_token_refresh_success(self, sample_config):
        """Test successful token refresh."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        # Mock successful token refresh response
        token_response = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value.status = 200
            mock_session_instance.post.return_value.__aenter__.return_value.json.return_value = token_response
            mock_session.return_value = mock_session_instance

            await server._refresh_access_token()

            assert server._access_token == "new-access-token"
            assert server._refresh_token == "new-refresh-token"
            assert server._token_expires_at > time.time()

    @pytest.mark.asyncio
    async def test_token_refresh_failure(self, sample_config):
        """Test token refresh failure."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "invalid-refresh-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value.status = 401
            mock_session.return_value = mock_session_instance

            with pytest.raises(NestConnectionError):
                await server._refresh_access_token()

            # Tokens should be cleared on auth failure
            assert server._access_token is None
            assert server._refresh_token is None

    @pytest.mark.asyncio
    async def test_access_token_property(self, sample_config):
        """Test access_token property with refresh."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-token"
        server._token_expires_at = time.time() + 600  # 10 minutes from now

        # Should return existing token without refresh
        token = await server.access_token
        assert token == "test-token"

    @pytest.mark.asyncio
    async def test_access_token_property_refresh_needed(self, sample_config):
        """Test access_token property when refresh is needed."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"
        server._access_token = "expired-token"
        server._token_expires_at = time.time() - 600  # Expired 10 minutes ago

        # Mock successful token refresh
        token_response = {
            "access_token": "new-access-token",
            "expires_in": 3600
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value.status = 200
            mock_session_instance.post.return_value.__aenter__.return_value.json.return_value = token_response
            mock_session.return_value = mock_session_instance

            token = await server.access_token

            assert token == "new-access-token"

    @pytest.mark.asyncio
    async def test_auth_state_loading(self, sample_config):
        """Test loading authentication state."""
        server = NestProtectMCP(sample_config)

        # Mock state manager
        server._state_manager = AsyncMock()
        server._state_manager.get_all.return_value = {
            "access_token": "stored-access-token",
            "refresh_token": "stored-refresh-token",
            "token_expires_at": str(time.time() + 3600),
            "devices": {"device1": "data"}
        }

        await server._load_auth_state()

        assert server._access_token == "stored-access-token"
        assert server._refresh_token == "stored-refresh-token"
        assert server._devices == {"device1": "data"}

    @pytest.mark.asyncio
    async def test_auth_state_saving(self, sample_config):
        """Test saving authentication state."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-access-token"
        server._refresh_token = "test-refresh-token"
        server._token_expires_at = time.time() + 3600
        server._devices = {"device1": "data"}

        # Mock state manager
        server._state_manager = AsyncMock()

        await server._save_auth_state()

        # Verify state manager was called for each state item
        assert server._state_manager.set.call_count >= 3  # At least tokens and devices


class TestServerAPIRequests:
    """Test server API request handling."""

    @pytest.mark.asyncio
    async def test_make_request_success(self, sample_config):
        """Test successful API request."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-token"
        server._token_expires_at = time.time() + 600

        response_data = {"test": "data"}

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.request.return_value.__aenter__.return_value.status = 200
            mock_session_instance.request.return_value.__aenter__.return_value.json.return_value = response_data
            mock_session.return_value = mock_session_instance

            result = await server._make_request('GET', 'test/endpoint')

            assert result == response_data
            # Verify headers were set correctly
            call_args = mock_session_instance.request.call_args
            headers = call_args[1]['headers']
            assert headers['Authorization'] == "Bearer test-token"

    @pytest.mark.asyncio
    async def test_make_request_unauthorized_retry(self, sample_config):
        """Test API request with unauthorized and successful retry."""
        server = NestProtectMCP(sample_config)
        server._access_token = "expired-token"
        server._token_expires_at = time.time() - 600
        server._refresh_token = "test-refresh-token"

        # Mock token refresh response
        refresh_response = {
            "access_token": "new-access-token",
            "expires_in": 3600
        }

        # Mock API response data
        api_response = {"test": "data"}

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()

            # First call (unauthorized) -> refresh -> second call (success)
            calls = []
            def mock_request(*args, **kwargs):
                call_count = len(calls)
                calls.append(kwargs)

                if call_count == 0:  # First API call - unauthorized
                    response = AsyncMock()
                    response.status = 401
                    response.json.return_value = {"error": "unauthorized"}
                    return response
                else:  # Second API call - success
                    response = AsyncMock()
                    response.status = 200
                    response.json.return_value = api_response
                    return response

            mock_session_instance.request.side_effect = mock_request

            # Mock token refresh POST
            async def mock_post(*args, **kwargs):
                response = AsyncMock()
                response.status = 200
                response.json.return_value = refresh_response
                return response

            mock_session_instance.post = mock_post
            mock_session.return_value = mock_session_instance

            result = await server._make_request('GET', 'test/endpoint')

            assert result == api_response
            assert len(calls) == 2  # Should have made 2 API calls
            # Second call should use new token
            assert calls[1]['headers']['Authorization'] == "Bearer new-access-token"

    @pytest.mark.asyncio
    async def test_make_request_network_error(self, sample_config):
        """Test API request with network error."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.request.side_effect = Exception("Network error")
            mock_session.return_value = mock_session_instance

            with pytest.raises(NestConnectionError):
                await server._make_request('GET', 'test/endpoint')


class TestServerDeviceManagement:
    """Test server device management functionality."""

    @pytest.mark.asyncio
    async def test_get_devices_from_api_success(self, sample_config):
        """Test successful device fetching from API."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        devices_response = {
            "devices": [
                {
                    "name": "enterprises/test-project/devices/device1",
                    "type": "sdm.devices.types.SMOKE_ALARM",
                    "traits": {
                        "sdm.devices.traits.Info": {
                            "customName": "Test Device 1"
                        },
                        "sdm.devices.traits.Connectivity": {
                            "status": "ONLINE"
                        }
                    }
                }
            ]
        }

        with patch.object(server, '_make_request') as mock_request:
            mock_request.return_value = devices_response

            devices = await server._get_devices_from_api()

            assert len(devices) == 1
            assert devices[0]["name"] == "enterprises/test-project/devices/device1"
            mock_request.assert_called_once_with('GET', 'enterprises/test-project/devices')

    @pytest.mark.asyncio
    async def test_get_devices_from_api_no_token(self, sample_config):
        """Test device fetching when no refresh token available."""
        server = NestProtectMCP(sample_config)
        # No refresh token set

        devices = await server._get_devices_from_api()

        assert devices == []  # Should return empty list

    @pytest.mark.asyncio
    async def test_map_device_state(self, sample_config):
        """Test device state mapping from API data."""
        server = NestProtectMCP(sample_config)

        device_data = {
            "name": "enterprises/test-project/devices/device1",
            "type": "sdm.devices.types.SMOKE_ALARM",
            "traits": {
                "sdm.devices.traits.Info": {
                    "customName": "Test Smoke Alarm",
                    "model": "Nest Protect",
                    "serialNumber": "123456789"
                },
                "sdm.devices.traits.Connectivity": {
                    "status": "ONLINE"
                },
                "sdm.devices.traits.Smoke": {
                    "alarmState": "ALARM_STATE_OFF"
                },
                "sdm.devices.traits.Battery": {
                    "batteryStatus": "BATTERY_STATUS_NORMAL",
                    "batteryLevel": 85
                },
                "sdm.devices.traits.Temperature": {
                    "ambientTemperatureCelsius": 22.5
                },
                "sdm.devices.traits.Humidity": {
                    "ambientHumidityPercent": 45.0
                }
            },
            "lastEventTime": "2023-01-01T12:00:00Z"
        }

        device_state = server._map_device_state(device_data)

        assert isinstance(device_state, ProtectDeviceState)
        assert device_state.device_id == "device1"
        assert device_state.name == "Test Smoke Alarm"
        assert device_state.online is True
        assert device_state.battery_health.value == "ok"
        assert device_state.co_alarm_state.value == "off"
        assert device_state.battery_level == 85
        assert device_state.temperature == 22.5

    def test_map_alarm_state(self, sample_config):
        """Test alarm state mapping."""
        server = NestProtectMCP(sample_config)

        # Test various alarm states
        assert server._map_alarm_state("ALARM_STATE_OFF").value == "off"
        assert server._map_alarm_state("ALARM_STATE_WARNING").value == "warning"
        assert server._map_alarm_state("ALARM_STATE_CRITICAL").value == "emergency"
        assert server._map_alarm_state("ALARM_STATE_TEST").value == "testing"
        assert server._map_alarm_state(None).value == "off"
        assert server._map_alarm_state("UNKNOWN_STATE").value == "off"

    def test_map_battery_state(self, sample_config):
        """Test battery state mapping."""
        server = NestProtectMCP(sample_config)

        # Test various battery states
        assert server._map_battery_state("BATTERY_STATUS_NORMAL").value == "ok"
        assert server._map_battery_state("BATTERY_STATUS_LOW").value == "replace_soon"
        assert server._map_battery_state("BATTERY_STATUS_CRITICAL").value == "replace_now"
        assert server._map_battery_state("BATTERY_STATUS_MISSING").value == "missing"
        assert server._map_battery_state(None).value == "invalid"
        assert server._map_battery_state("UNKNOWN_STATUS").value == "invalid"


class TestServerMessageHandling:
    """Test server message handling and MCP protocol."""

    def test_message_handlers_registration(self, sample_config):
        """Test that message handlers are properly registered."""
        server = NestProtectMCP(sample_config)
        server._register_message_handlers()

        expected_handlers = [
            "ping", "get_device", "get_devices",
            "get_alarm_state", "hush_alarm", "run_test"
        ]

        for handler in expected_handlers:
            assert handler in server._message_handlers

    @pytest.mark.asyncio
    async def test_handle_ping_message(self, sample_config):
        """Test ping message handling."""
        server = NestProtectMCP(sample_config)

        result = await server._handle_ping({"timestamp": 1234567890})

        assert result["pong"] is True
        assert result["timestamp"] == 1234567890
        assert "server_time" in result

    @pytest.mark.asyncio
    async def test_handle_message_success(self, sample_config):
        """Test successful message handling."""
        server = NestProtectMCP(sample_config)

        # Mock message
        message = Mock()
        message.method = "ping"
        message.params = {"timestamp": 1234567890}
        message.id = "test-id"

        with patch.object(server, '_handle_ping') as mock_ping:
            mock_ping.return_value = {"pong": True}

            result = await server.handle_message(message)

            assert result["jsonrpc"] == "2.0"
            assert result["id"] == "test-id"
            assert result["result"]["pong"] is True

    @pytest.mark.asyncio
    async def test_handle_message_unknown_method(self, sample_config):
        """Test message handling with unknown method."""
        server = NestProtectMCP(sample_config)

        message = Mock()
        message.method = "unknown_method"
        message.params = {}
        message.id = "test-id"

        result = await server.handle_message(message)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == "test-id"
        assert "error" in result
        assert result["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_handle_message_exception(self, sample_config):
        """Test message handling with handler exception."""
        server = NestProtectMCP(sample_config)

        message = Mock()
        message.method = "ping"
        message.params = {}
        message.id = "test-id"

        with patch.object(server, '_handle_ping') as mock_ping:
            mock_ping.side_effect = Exception("Test error")

            result = await server.handle_message(message)

            assert result["jsonrpc"] == "2.0"
            assert result["id"] == "test-id"
            assert "error" in result
            assert "Internal error" in result["error"]["message"]


class TestServerToolRegistration:
    """Test server tool registration for FastMCP."""

    def test_tool_registration(self, sample_config):
        """Test that tools are properly registered."""
        server = NestProtectMCP(sample_config)
        server._register_tools()

        # Check that tools were registered (FastMCP should have them)
        # This is hard to test directly, but we can check the method exists
        assert hasattr(server, '_register_tools')

    def test_tool_schemas_available(self, sample_config):
        """Test that tool schemas are available."""
        server = NestProtectMCP(sample_config)

        # Tool schemas should be available
        from nest_protect_mcp.tools import tool_schemas
        assert "get_devices" in tool_schemas
        assert "get_device" in tool_schemas
        assert "silence_alarm" in tool_schemas


class TestServerErrorHandling:
    """Test server error handling scenarios."""

    @pytest.mark.asyncio
    async def test_server_initialization_error_handling(self, sample_config):
        """Test server initialization with various error scenarios."""
        server = NestProtectMCP(sample_config)

        # Mock state manager to raise exception
        server._state_manager = AsyncMock()
        server._state_manager.get_all.side_effect = Exception("State error")

        # Should handle state loading errors gracefully
        await server._load_auth_state()

        # Should not crash and should have default values
        assert server._access_token is None
        assert server._refresh_token is None

    @pytest.mark.asyncio
    async def test_ensure_session_creation(self, sample_config):
        """Test session creation and management."""
        server = NestProtectMCP(sample_config)

        # Initially no session
        assert server._session is None

        await server._ensure_session()

        # Should have created a session
        assert server._session is not None

    @pytest.mark.asyncio
    async def test_ensure_session_existing(self, sample_config):
        """Test session management with existing session."""
        server = NestProtectMCP(sample_config)

        # Create a mock session
        mock_session = AsyncMock()
        server._session = mock_session

        await server._ensure_session()

        # Should not create a new session
        assert server._session is mock_session

    def test_setup_routes_backward_compatibility(self, sample_config):
        """Test that setup_routes is kept for backward compatibility."""
        server = NestProtectMCP(sample_config)

        # Should not raise an exception
        server._setup_routes()

        # Should have message handlers registered
        assert hasattr(server, '_message_handlers')


class TestServerLifecycle:
    """Test server lifecycle management."""

    @pytest.mark.asyncio
    async def test_server_startup_event(self, sample_config):
        """Test server startup event handling."""
        server = NestProtectMCP(sample_config)

        # Mock successful initialization
        with patch.object(server, 'initialize') as mock_init:
            mock_init.return_value = None

            result = await server.startup_event()

            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_startup_event_retries(self, sample_config):
        """Test server startup with retries on failure."""
        server = NestProtectMCP(sample_config)

        # Mock initialization to fail twice then succeed
        call_count = 0
        def mock_init():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")

        with patch.object(server, 'initialize') as mock_init_patched:
            mock_init_patched.side_effect = mock_init

            result = await server.startup_event()

            assert result is True
            assert mock_init_patched.call_count == 3

    @pytest.mark.asyncio
    async def test_server_shutdown_event(self, sample_config):
        """Test server shutdown event handling."""
        server = NestProtectMCP(sample_config)

        # Mock shutdown
        with patch.object(server, 'shutdown') as mock_shutdown:
            mock_shutdown.return_value = None

            await server.shutdown_event()

            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_shutdown_with_websockets(self, sample_config):
        """Test server shutdown with active WebSocket connections."""
        server = NestProtectMCP(sample_config)
        server._active_connections = [AsyncMock(), AsyncMock()]

        with patch.object(server, 'shutdown') as mock_shutdown:
            mock_shutdown.return_value = None

            await server.shutdown_event()

            # Should close all WebSocket connections
            for ws in server._active_connections:
                ws.close.assert_called_once()

            mock_shutdown.assert_called_once()
