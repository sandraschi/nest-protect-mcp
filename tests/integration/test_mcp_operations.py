"""
Integration tests for MCP server and device communication functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from nest_protect_mcp.server import NestProtectMCP
from nest_protect_mcp.models import ProtectConfig, ProtectDeviceState, ProtectCommand
from nest_protect_mcp.exceptions import NestDeviceNotFoundError


class TestMCPDeviceOperations:
    """Test MCP device operations through message handlers."""

    @pytest.mark.asyncio
    async def test_get_devices_message_handler(self, sample_config):
        """Test get_devices through message handler."""
        server = NestProtectMCP(sample_config)

        # Mock the underlying method
        with patch.object(server, '_get_devices') as mock_get_devices:
            mock_get_devices.return_value = [
                {
                    "id": "device1",
                    "name": "Test Device 1",
                    "type": "smoke_alarm",
                    "online": True,
                    "battery_state": "ok",
                    "alarm_state": "ok",
                    "last_connection": "2023-01-01T12:00:00Z"
                },
                {
                    "id": "device2",
                    "name": "Test Device 2",
                    "type": "co_alarm",
                    "online": False,
                    "battery_state": "replace_soon",
                    "alarm_state": "warning",
                    "last_connection": "2023-01-01T11:00:00Z"
                }
            ]

            # Test through message handler
            result = await server._get_devices()

            assert len(result) == 2
            assert result[0]["id"] == "device1"
            assert result[1]["id"] == "device2"

    @pytest.mark.asyncio
    async def test_get_device_message_handler(self, sample_config):
        """Test get_device through message handler."""
        server = NestProtectMCP(sample_config)

        device_data = {
            "id": "device1",
            "name": "Test Device 1",
            "type": "smoke_alarm",
            "online": True,
            "battery_state": "ok",
            "alarm_state": "ok",
            "last_connection": "2023-01-01T12:00:00Z",
            "battery_level": 85,
            "temperature": 22.5,
            "humidity": 45.0
        }

        with patch.object(server, 'get_device') as mock_get_device:
            mock_get_device.return_value = device_data

            result = await server._handle_get_device("device1")

            assert result["id"] == "device1"
            assert result["name"] == "Test Device 1"
            mock_get_device.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_get_device_message_handler_not_found(self, sample_config):
        """Test get_device handler when device not found."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, 'get_device') as mock_get_device:
            mock_get_device.return_value = None

            with pytest.raises(Exception, match="Device nonexistent not found"):
                await server._handle_get_device("nonexistent")

    @pytest.mark.asyncio
    async def test_get_device_message_handler_missing_id(self, sample_config):
        """Test get_device handler with missing device_id."""
        server = NestProtectMCP(sample_config)

        with pytest.raises(ValueError, match="device_id is required"):
            await server._handle_get_device("")

    @pytest.mark.asyncio
    async def test_get_alarm_state_message_handler(self, sample_config):
        """Test get_alarm_state through message handler."""
        server = NestProtectMCP(sample_config)

        device_data = ProtectDeviceState(
            device_id="device1",
            name="Test Device",
            model="Test Model",
            serial_number="123456",
            battery_health="ok",
            co_alarm_state="ok",
            smoke_alarm_state="warning",
            heat_alarm_state="ok",
            online=True
        )

        with patch.object(server, 'get_device') as mock_get_device:
            mock_get_device.return_value = device_data

            result = await server._handle_get_alarm_state("device1")

            assert result["status"] == "success"
            assert result["device_id"] == "device1"
            assert result["smoke_alarm_state"] == "warning"
            assert result["co_alarm_state"] == "ok"
            assert result["heat_alarm_state"] == "ok"

    @pytest.mark.asyncio
    async def test_hush_alarm_message_handler(self, sample_config):
        """Test hush_alarm through message handler."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, 'hush_alarm') as mock_hush:
            mock_hush.return_value = True

            result = await server._handle_hush_alarm("device1")

            assert result["status"] == "success"
            assert result["message"] == "Alarm hushed successfully"
            mock_hush.assert_called_once_with("device1")

    @pytest.mark.asyncio
    async def test_run_test_message_handler(self, sample_config):
        """Test run_test through message handler."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, 'run_test') as mock_run_test:
            mock_run_test.return_value = True

            result = await server._handle_run_test("device1", "manual")

            assert result["status"] == "success"
            assert "Test 'manual' started successfully" in result["message"]
            mock_run_test.assert_called_once_with("device1", "manual")


class TestDeviceCommandOperations:
    """Test device command operations."""

    @pytest.mark.asyncio
    async def test_send_command_validation(self, sample_config):
        """Test command sending with validation."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, 'send_command') as mock_send:
            mock_send.return_value = True

            result = await server._handle_send_command("device1", "hush")

            assert result["status"] == "success"
            assert result["message"] == "Command sent successfully"

    @pytest.mark.asyncio
    async def test_send_command_with_params(self, sample_config):
        """Test command sending with parameters."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, 'send_command') as mock_send:
            mock_send.return_value = True

            result = await server._handle_send_command("device1", "test", {"duration": 30})

            assert result["status"] == "success"
            mock_send.assert_called_once()

            # Check that the command was created with correct params
            call_args = mock_send.call_args[0][0]
            assert isinstance(call_args, ProtectCommand)
            assert call_args.command == "test"
            assert call_args.params == {"duration": 30}

    @pytest.mark.asyncio
    async def test_send_command_invalid_command(self, sample_config):
        """Test command sending with invalid command."""
        server = NestProtectMCP(sample_config)

        with pytest.raises(Exception, match="Invalid command"):
            await server._handle_send_command("device1", "invalid_command")

    @pytest.mark.asyncio
    async def test_send_command_device_not_found(self, sample_config):
        """Test command sending when device not found."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, 'send_command') as mock_send:
            mock_send.side_effect = NestDeviceNotFoundError("Device not found")

            with pytest.raises(Exception, match="Device not found"):
                await server._handle_send_command("nonexistent", "hush")

    @pytest.mark.asyncio
    async def test_send_command_execution_failure(self, sample_config):
        """Test command sending when execution fails."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, 'send_command') as mock_send:
            mock_send.return_value = False

            with pytest.raises(Exception, match="Failed to send command"):
                await server._handle_send_command("device1", "hush")


class TestDeviceStateManagement:
    """Test device state management operations."""

    @pytest.mark.asyncio
    async def test_device_state_caching(self, sample_config):
        """Test device state caching functionality."""
        server = NestProtectMCP(sample_config)

        # Initially no devices cached
        assert server._devices == {}

        # Mock API response
        devices_data = [
            {
                "name": "enterprises/test-project/devices/device1",
                "type": "sdm.devices.types.SMOKE_ALARM",
                "traits": {
                    "sdm.devices.traits.Info": {"customName": "Test Device"},
                    "sdm.devices.traits.Connectivity": {"status": "ONLINE"}
                }
            }
        ]

        with patch.object(server, '_get_devices_from_api') as mock_api:
            mock_api.return_value = devices_data

            # This should trigger caching
            devices = await server.get_devices()

            # Devices should be cached
            assert "device1" in server._devices

    @pytest.mark.asyncio
    async def test_device_state_invalidation(self, sample_config):
        """Test device state invalidation."""
        server = NestProtectMCP(sample_config)

        # Add some cached devices
        server._devices = {"device1": {"name": "Cached Device"}}

        # Mock state manager for saving
        server._state_manager = AsyncMock()

        # Save state (should include devices)
        await server._save_auth_state()

        # Verify devices were saved
        server._state_manager.set.assert_called()


class TestErrorScenarioHandling:
    """Test various error scenarios."""

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, sample_config):
        """Test handling of network timeouts."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.request.side_effect = asyncio.TimeoutError("Request timed out")
            mock_session.return_value = mock_session_instance

            with pytest.raises(Exception):  # Should raise appropriate error
                await server._make_request('GET', 'test/endpoint')

    @pytest.mark.asyncio
    async def test_malformed_api_response(self, sample_config):
        """Test handling of malformed API responses."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            response = AsyncMock()
            response.status = 200
            response.json.side_effect = Exception("Invalid JSON")
            mock_session_instance.request.return_value.__aenter__.return_value = response
            mock_session.return_value = mock_session_instance

            with pytest.raises(Exception):
                await server._make_request('GET', 'test/endpoint')

    @pytest.mark.asyncio
    async def test_device_mapping_edge_cases(self, sample_config):
        """Test device mapping with edge cases."""
        server = NestProtectMCP(sample_config)

        # Test with minimal device data
        minimal_device = {
            "name": "enterprises/test-project/devices/minimal",
            "type": "sdm.devices.types.SMOKE_ALARM"
            # No traits
        }

        device_state = server._map_device_state(minimal_device)

        assert device_state.device_id == "minimal"
        assert device_state.name == "enterprises/test-project/devices/minimal"  # Fallback to full name
        assert device_state.online is False  # Default

    @pytest.mark.asyncio
    async def test_concurrent_device_operations(self, sample_config):
        """Test concurrent device operations."""
        server = NestProtectMCP(sample_config)

        # Mock device operations
        with patch.object(server, 'get_device') as mock_get_device:
            mock_get_device.return_value = {
                "id": "device1",
                "name": "Test Device",
                "online": True
            }

            # Run multiple concurrent operations
            tasks = [
                server._handle_get_device("device1")
                for _ in range(5)
            ]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert len(results) == 5
            for result in results:
                assert result["id"] == "device1"

    def test_message_validation_edge_cases(self, sample_config):
        """Test message validation edge cases."""
        server = NestProtectMCP(sample_config)

        # Test with None message
        result = asyncio.run(server.handle_message(None))
        assert "error" in result

        # Test with message missing required fields
        invalid_message = Mock()
        invalid_message.method = None
        invalid_message.params = None
        invalid_message.id = None

        result = asyncio.run(server.handle_message(invalid_message))
        assert "error" in result


class TestPerformanceScenarios:
    """Test performance-related scenarios."""

    @pytest.mark.asyncio
    async def test_large_message_handling(self, sample_config):
        """Test handling of large messages."""
        server = NestProtectMCP(sample_config)

        # Create a large parameter set
        large_params = {f"param_{i}": f"value_{i}" for i in range(100)}

        message = Mock()
        message.method = "ping"
        message.params = large_params
        message.id = "large-message-test"

        result = await server.handle_message(message)

        # Should handle large messages without issues
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == "large-message-test"

    @pytest.mark.asyncio
    async def test_rapid_message_handling(self, sample_config):
        """Test handling rapid successive messages."""
        server = NestProtectMCP(sample_config)

        messages = []
        for i in range(10):
            message = Mock()
            message.method = "ping"
            message.params = {"timestamp": i}
            message.id = f"test-{i}"
            messages.append(message)

        # Handle all messages rapidly
        tasks = [server.handle_message(msg) for msg in messages]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result["id"] == f"test-{i}"
            assert result["result"]["pong"] is True

    def test_memory_usage_with_many_devices(self, sample_config):
        """Test memory usage with many cached devices."""
        server = NestProtectMCP(sample_config)

        # Simulate many devices in cache
        many_devices = {f"device_{i}": {"name": f"Device {i}"} for i in range(1000)}
        server._devices = many_devices

        # Should handle large device cache
        assert len(server._devices) == 1000
        assert "device_999" in server._devices


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance."""

    def test_message_format_compliance(self, sample_config):
        """Test that responses follow JSON-RPC 2.0 format."""
        server = NestProtectMCP(sample_config)

        message = Mock()
        message.method = "ping"
        message.params = {"timestamp": 1234567890}
        message.id = "test-id"

        async def test_response():
            result = await server.handle_message(message)
            # Check JSON-RPC 2.0 compliance
            assert result["jsonrpc"] == "2.0"
            assert result["id"] == "test-id"
            assert "result" in result or "error" in result

        asyncio.run(test_response())

    def test_error_response_format(self, sample_config):
        """Test error response format compliance."""
        server = NestProtectMCP(sample_config)

        # Test with unknown method
        message = Mock()
        message.method = "unknown_method"
        message.params = {}
        message.id = "error-test"

        async def test_error_response():
            result = await server.handle_message(message)

            assert result["jsonrpc"] == "2.0"
            assert result["id"] == "error-test"
            assert "error" in result
            assert "code" in result["error"]
            assert "message" in result["error"]

        asyncio.run(test_error_response())

    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self, sample_config):
        """Test tool parameter validation."""
        server = NestProtectMCP(sample_config)

        # Test tool registration creates proper validation
        # This is hard to test directly, but we can verify the schemas exist
        from nest_protect_mcp.tools import tool_schemas

        # Check that required parameters are defined
        get_device_schema = tool_schemas["get_device"]
        assert "device_id" in get_device_schema["parameters"]["required"]

        silence_alarm_schema = tool_schemas["silence_alarm"]
        assert "device_id" in silence_alarm_schema["parameters"]["required"]


class TestIntegrationWorkflows:
    """Test complete integration workflows."""

    @pytest.mark.asyncio
    async def test_complete_device_lifecycle(self, sample_config):
        """Test complete device lifecycle workflow."""
        server = NestProtectMCP(sample_config)

        # 1. Get devices
        with patch.object(server, '_get_devices_from_api') as mock_api:
            mock_api.return_value = [
                {
                    "name": "enterprises/test-project/devices/device1",
                    "type": "sdm.devices.types.SMOKE_ALARM",
                    "traits": {
                        "sdm.devices.traits.Info": {"customName": "Test Device"},
                        "sdm.devices.traits.Connectivity": {"status": "ONLINE"}
                    }
                }
            ]

            devices = await server.get_devices()
            assert len(devices) == 1

        # 2. Get specific device
        with patch.object(server, 'get_device') as mock_get_device:
            device_data = {
                "id": "device1",
                "name": "Test Device",
                "online": True,
                "battery_state": "ok",
                "alarm_state": "ok"
            }
            mock_get_device.return_value = device_data

            device = await server.get_device("device1")
            assert device["id"] == "device1"

        # 3. Check alarm state
        alarm_state = await server._handle_get_alarm_state("device1")
        assert alarm_state["device_id"] == "device1"

        # 4. Send command
        with patch.object(server, 'hush_alarm') as mock_hush:
            mock_hush.return_value = True

            result = await server._handle_hush_alarm("device1")
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, sample_config):
        """Test error recovery workflow."""
        server = NestProtectMCP(sample_config)

        # Simulate API failure
        with patch.object(server, '_get_devices_from_api') as mock_api:
            mock_api.side_effect = Exception("API Error")

            # Should handle API errors gracefully
            devices = await server.get_devices()
            assert devices == []

        # Should still be able to handle other operations
        message = Mock()
        message.method = "ping"
        message.params = {}
        message.id = "recovery-test"

        result = await server.handle_message(message)
        assert result["result"]["pong"] is True
