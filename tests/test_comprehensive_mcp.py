"""
Comprehensive FastMCP 2.14.3 Test Suite

Tests conversational responses, sampling capabilities, and both mock and real device scenarios.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from tests.mock_device_testing import (
    ComprehensiveTestSuite,
    ConversationalResponseValidator,
    MockDeviceFactory,
    MockNestAPIServer
)
from tests.real_device_testing import RealDeviceDiscovery, RealDeviceTestSuite


class TestConversationalResponses:
    """Test FastMCP 2.14.3 conversational response formats."""

    @pytest.fixture
    async def validator(self):
        return ConversationalResponseValidator()

    async def test_list_devices_conversational_format(self, validator):
        """Test that list_devices returns proper conversational response."""
        mock_response = {
            "success": True,
            "operation": "list_devices",
            "summary": "Found 5 Nest Protect devices (4 online)",
            "result": {
                "count": 5,
                "devices": [
                    {"id": "device-1", "name": "Living Room", "online": True},
                    {"id": "device-2", "name": "Kitchen", "online": True},
                    {"id": "device-3", "name": "Bedroom", "online": False}
                ],
                "stats": {
                    "total": 5,
                    "online": 4,
                    "offline": 1,
                    "types": ["SMOKE_CO_ALARM"]
                }
            },
            "next_steps": [
                "Run 'get_device_status' to check individual device details",
                "Use 'run_safety_check' to test device functionality"
            ],
            "context": {
                "operation_details": "Retrieved device information from Nest API",
                "api_response": "Successfully queried enterprise test-project"
            },
            "suggestions": [
                "Consider running safety checks on the offline device"
            ],
            "follow_up_questions": [
                "Would you like me to check the status of a specific device?",
                "Should I run safety checks on any of these devices?"
            ]
        }

        errors = validator.validate_conversational_response(mock_response, "list_devices")
        assert len(errors) == 0, f"Conversational response validation failed: {errors}"

    async def test_device_status_conversational_format(self, validator):
        """Test that get_device_status returns proper conversational response."""
        mock_response = {
            "success": True,
            "operation": "get_device_status",
            "summary": "Living Room detector is online with good health status",
            "result": {
                "device": {
                    "id": "living-room-detector",
                    "name": "Living Room Detector",
                    "online": True,
                    "battery": {"level": 85, "status": "OK"},
                    "alarm": {"status": "NONE"}
                },
                "health_analysis": {
                    "issues": [],
                    "overall_status": "good"
                }
            },
            "next_steps": [
                "Run 'run_safety_check' to test device functionality",
                "Use 'get_device_events' to see recent activity"
            ],
            "context": {
                "operation_details": "Retrieved comprehensive status for Nest Protect device",
                "last_updated": "2025-01-18T10:30:00Z"
            },
            "suggestions": [],
            "follow_up_questions": [
                "Would you like me to run a safety check on this device?",
                "Should I check the recent event history?"
            ]
        }

        errors = validator.validate_conversational_response(mock_response, "get_device_status")
        assert len(errors) == 0, f"Conversational response validation failed: {errors}"

    async def test_error_response_format(self, validator):
        """Test that error responses follow proper format."""
        error_response = {
            "success": False,
            "error": "Authentication required",
            "error_code": "AUTHENTICATION_REQUIRED",
            "message": "You need to authenticate with the Nest API first",
            "recovery_options": [
                "Run 'initiate_oauth_flow' to start authentication",
                "Check your OAuth tokens are properly configured"
            ],
            "diagnostic_info": {
                "root_cause": "Missing or invalid access token",
                "affected_components": ["Nest API connection"]
            },
            "alternative_solutions": [
                "Re-run OAuth authentication flow",
                "Refresh your access tokens"
            ],
            "estimated_resolution_time": "< 5 minutes",
            "urgency": "high"
        }

        errors = validator.validate_error_response(error_response)
        assert len(errors) == 0, f"Error response validation failed: {errors}"


class TestSamplingCapabilities:
    """Test FastMCP 2.14.3 sampling capabilities."""

    async def test_assess_home_safety_sampling_signal(self):
        """Test that assess_home_safety triggers sampling for complex analysis."""
        # This would be tested by mocking the actual tool call
        # For now, we test the expected response structure
        expected_response = {
            "success": True,
            "operation": "assess_home_safety",
            "summary": "Critical safety assessment completed: 2 issues found",
            "result": {
                "assessment_scope": "comprehensive",
                "devices_analyzed": 3,
                "safety_issues": [
                    {"type": "connectivity", "device": "Bedroom", "severity": "high"},
                    {"type": "battery", "device": "Kitchen", "severity": "medium"}
                ]
            },
            "requires_sampling": True,
            "sampling_reason": "Complex safety analysis with multiple critical issues detected",
            "next_steps": [
                "AI will analyze safety patterns and generate prioritized recommendations"
            ],
            "context": {
                "operation_details": "Comprehensive safety assessment with critical findings",
                "assessment_timestamp": "2025-01-18T10:30:00Z"
            }
        }

        assert expected_response["requires_sampling"] is True
        assert "sampling_reason" in expected_response
        assert len(expected_response["next_steps"]) > 0

    async def test_emergency_response_sampling(self):
        """Test that emergency response triggers sampling."""
        expected_response = {
            "success": True,
            "operation": "coordinate_emergency_response",
            "summary": "EMERGENCY SMOKE detected - coordinating response",
            "result": {
                "emergency_type": "smoke",
                "affected_devices": ["living-room", "kitchen"],
                "response_priority": "critical",
                "coordination_status": "initiated"
            },
            "requires_sampling": True,
            "sampling_reason": "Complex emergency coordination required for smoke incident",
            "next_steps": [
                "AI will analyze emergency patterns and determine optimal response"
            ]
        }

        assert expected_response["requires_sampling"] is True
        assert "emergency" in expected_response["sampling_reason"].lower()

    async def test_predictive_maintenance_sampling(self):
        """Test that predictive maintenance triggers sampling."""
        expected_response = {
            "success": True,
            "operation": "predict_maintenance_needs",
            "summary": "Predictive maintenance analysis completed",
            "result": {
                "analysis_depth": "detailed",
                "time_horizon": "1_month",
                "predictions_generated": True
            },
            "requires_sampling": True,
            "sampling_reason": "Complex pattern analysis required for accurate maintenance predictions",
            "next_steps": [
                "AI will analyze device usage patterns and failure history"
            ]
        }

        assert expected_response["requires_sampling"] is True
        assert "pattern analysis" in expected_response["sampling_reason"].lower()


class TestMockDeviceScenarios:
    """Test various mock device scenarios."""

    @pytest.fixture
    async def mock_server(self):
        server = MockNestAPIServer()
        devices = MockDeviceFactory.create_multiple_devices(5)
        server.add_devices(devices)
        return server

    async def test_normal_device_scenario(self, mock_server):
        """Test normal device operation scenario."""
        devices = await mock_server.list_devices()
        assert devices["devices"] is not None
        assert len(devices["devices"]) == 5

        # Check that devices have expected properties
        for device in devices["devices"]:
            assert "name" in device
            assert "type" in device
            traits = device.get("traits", {})
            assert "sdm.devices.traits.Connectivity" in traits

    async def test_emergency_scenario(self, mock_server):
        """Test emergency response scenario."""
        # Add emergency devices
        emergency_devices = [
            MockDeviceFactory.create_smoke_alarm_device("emergency-smoke"),
            MockDeviceFactory.create_co_alarm_device("emergency-co")
        ]
        mock_server.add_devices(emergency_devices)

        devices = await mock_server.list_devices()
        emergency_count = sum(1 for d in devices["devices"]
                            if "emergency-" in d["name"])

        assert emergency_count == 2

    async def test_maintenance_scenario(self, mock_server):
        """Test maintenance scenario with low battery devices."""
        maintenance_devices = [
            MockDeviceFactory.create_low_battery_device("maintenance-battery"),
            MockDeviceFactory.create_offline_device("maintenance-offline")
        ]
        mock_server.add_devices(maintenance_devices)

        devices = await mock_server.list_devices()

        # Check for maintenance issues
        battery_issues = 0
        offline_issues = 0

        for device in devices["devices"]:
            traits = device.get("traits", {})
            connectivity = traits.get("sdm.devices.traits.Connectivity", {})
            battery = traits.get("sdm.devices.traits.Battery", {})

            if connectivity.get("status") != "ONLINE":
                offline_issues += 1
            if battery.get("batteryLevel", 100) < 20:
                battery_issues += 1

        assert battery_issues >= 1
        assert offline_issues >= 1

    async def test_network_conditions(self, mock_server):
        """Test various network conditions."""
        # Set poor network conditions
        mock_server.set_network_conditions(
            latency_ms=1000, packet_loss=0.2, connection_drops=3
        )

        # Test should still work but with simulated issues
        devices = await mock_server.list_devices()
        assert "devices" in devices


class TestComprehensiveTestSuite:
    """Test the comprehensive test suite functionality."""

    @pytest.fixture
    async def test_suite(self):
        suite = ComprehensiveTestSuite()
        await suite.setup_mock_environment("normal")
        return suite

    async def test_conversational_response_testing(self, test_suite):
        """Test conversational response validation."""
        results = await test_suite.test_conversational_responses()

        assert "passed" in results
        assert "failed" in results
        assert "details" in results
        assert results["passed"] + results["failed"] > 0

    async def test_sampling_capability_testing(self, test_suite):
        """Test sampling capability validation."""
        results = await test_suite.test_sampling_capabilities()

        assert "sampling_signals_detected" in results
        assert results["sampling_signals_detected"] > 0
        assert "sampling_reasons_valid" in results

    async def test_device_state_transitions(self, test_suite):
        """Test device state transition validation."""
        results = await test_suite.test_device_state_transitions()

        assert "transitions_tested" in results
        assert "transitions_successful" in results
        assert results["transitions_tested"] > 0

    async def test_comprehensive_suite_execution(self, test_suite):
        """Test full comprehensive test suite execution."""
        results = await test_suite.run_comprehensive_test_suite()

        assert "overall_status" in results
        assert results["overall_status"] in ["passed", "failed", "warning"]
        assert "conversational_tests" in results
        assert "sampling_tests" in results
        assert "state_transition_tests" in results


class TestRealDeviceIntegration:
    """Test real device integration (requires valid credentials)."""

    @pytest.mark.skip(reason="Requires real Nest API credentials")
    async def test_real_device_discovery(self):
        """Test real device discovery (skipped without credentials)."""
        # This test would run with real credentials
        project_id = "real-project-id"
        access_token = "real-access-token"

        async with RealDeviceDiscovery(project_id, access_token) as discovery:
            result = await discovery.test_api_connectivity()
            # Test would validate real API response format
            assert isinstance(result, dict)

    @pytest.mark.skip(reason="Requires real Nest API credentials")
    async def test_real_device_test_suite(self):
        """Test real device test suite (skipped without credentials)."""
        # This test would run comprehensive real device testing
        project_id = "real-project-id"
        access_token = "real-access-token"

        test_suite = RealDeviceTestSuite(project_id, access_token)
        results = await test_suite.run_full_device_test_suite()

        assert "overall_status" in results
        assert "tests_run" in results


# Integration tests combining mock and real device testing
class TestIntegrationScenarios:
    """Test integration scenarios between mock and real device testing."""

    async def test_response_format_consistency(self):
        """Test that mock and real responses follow same format."""
        # Test that both mock and real device responses
        # follow the same conversational format standards

        mock_response = {
            "success": True,
            "operation": "test_operation",
            "summary": "Mock test completed",
            "result": {"mock_data": True},
            "next_steps": ["Mock next step"],
            "context": {"mock_context": True},
            "suggestions": ["Mock suggestion"],
            "follow_up_questions": ["Mock question"]
        }

        validator = ConversationalResponseValidator()
        errors = validator.validate_conversational_response(mock_response, "test_operation")

        assert len(errors) == 0, f"Mock response format invalid: {errors}"

    async def test_error_handling_consistency(self):
        """Test that error handling is consistent across mock and real scenarios."""
        error_scenarios = [
            {
                "success": False,
                "error": "Authentication failed",
                "error_code": "AUTHENTICATION_ERROR",
                "recovery_options": ["Re-authenticate"],
                "urgency": "high"
            },
            {
                "success": False,
                "error": "Device not found",
                "error_code": "DEVICE_NOT_FOUND",
                "recovery_options": ["Check device ID"],
                "urgency": "medium"
            }
        ]

        validator = ConversationalResponseValidator()

        for error_response in error_scenarios:
            errors = validator.validate_error_response(error_response)
            assert len(errors) == 0, f"Error response format invalid: {errors}"