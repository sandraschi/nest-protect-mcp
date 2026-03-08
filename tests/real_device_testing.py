"""
Real Device Testing Framework for Nest Protect MCP

This module provides comprehensive testing capabilities for real Nest Protect devices,
including device discovery, connectivity validation, and live system testing.
"""

import asyncio
import json
import socket
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import aiohttp
import pytest

from tests.mock_device_testing import ConversationalResponseValidator


class RealDeviceDiscovery:
    """Discover and validate real Nest Protect devices."""

    def __init__(self, project_id: str, access_token: str):
        self.project_id = project_id
        self.access_token = access_token
        self.base_url = "https://smartdevicemanagement.googleapis.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_api_connectivity(self) -> Dict[str, Any]:
        """Test basic API connectivity and authentication."""
        if not self.session:
            return {
                "success": False,
                "error": "Session not initialized",
                "error_code": "SESSION_ERROR"
            }

        try:
            url = f"{self.base_url}/enterprises/{self.project_id}/devices"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            start_time = time.time()
            async with self.session.get(url, headers=headers) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    device_count = len(data.get("devices", []))

                    return {
                        "success": True,
                        "operation": "test_api_connectivity",
                        "summary": f"API connectivity confirmed - found {device_count} devices",
                        "result": {
                            "response_time_ms": round(response_time * 1000, 2),
                            "device_count": device_count,
                            "api_status": "healthy"
                        },
                        "next_steps": [
                            "Run individual device tests",
                            "Validate device connectivity",
                            "Test device control functions"
                        ],
                        "context": {
                            "api_endpoint": url,
                            "authentication": "valid",
                            "response_time": f"{response_time:.3f}s"
                        }
                    }
                elif response.status == 401:
                    return {
                        "success": False,
                        "error": "Authentication failed",
                        "error_code": "AUTHENTICATION_ERROR",
                        "message": "Invalid or expired access token",
                        "recovery_options": [
                            "Refresh access token",
                            "Re-run OAuth authentication flow",
                            "Verify token expiration"
                        ]
                    }
                elif response.status == 403:
                    return {
                        "success": False,
                        "error": "Authorization failed",
                        "error_code": "AUTHORIZATION_ERROR",
                        "message": "Insufficient permissions for device access",
                        "recovery_options": [
                            "Check Google Cloud project permissions",
                            "Verify Smart Device Management API is enabled",
                            "Confirm project ownership"
                        ]
                    }
                else:
                    error_data = await response.json()
                    return {
                        "success": False,
                        "error": "API request failed",
                        "error_code": f"API_ERROR_{response.status}",
                        "message": f"Nest API returned status {response.status}",
                        "diagnostic_info": {
                            "http_status": response.status,
                            "error_details": error_data.get("error", {}).get("message", "Unknown error")
                        }
                    }

        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": "Network connectivity failed",
                "error_code": "NETWORK_ERROR",
                "message": "Cannot reach Nest API servers",
                "diagnostic_info": {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                "recovery_options": [
                    "Check internet connection",
                    "Verify DNS resolution",
                    "Test firewall settings"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Unexpected error",
                "error_code": "INTERNAL_ERROR",
                "message": f"Unexpected error during API test: {str(e)}",
                "diagnostic_info": {
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            }

    async def discover_devices(self) -> Dict[str, Any]:
        """Discover all available Nest Protect devices."""
        if not self.session:
            return {
                "success": False,
                "error": "Session not initialized",
                "error_code": "SESSION_ERROR"
            }

        try:
            url = f"{self.base_url}/enterprises/{self.project_id}/devices"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": "Device discovery failed",
                        "error_code": f"DISCOVERY_ERROR_{response.status}",
                        "message": "Cannot retrieve device list from Nest API"
                    }

                data = await response.json()
                devices = data.get("devices", [])

                # Analyze discovered devices
                device_analysis = self._analyze_discovered_devices(devices)

                return {
                    "success": True,
                    "operation": "discover_devices",
                    "summary": f"Discovered {len(devices)} Nest Protect devices",
                    "result": {
                        "devices": devices,
                        "analysis": device_analysis
                    },
                    "next_steps": [
                        "Test connectivity for each device",
                        "Validate device functionality",
                        "Check device health status"
                    ],
                    "context": {
                        "total_devices": len(devices),
                        "online_devices": device_analysis["online_count"],
                        "offline_devices": device_analysis["offline_count"]
                    },
                    "suggestions": device_analysis["recommendations"],
                    "follow_up_questions": [
                        "Would you like me to test connectivity for all devices?",
                        "Should I run health checks on the offline devices?",
                        "Do you want me to validate device functionality?"
                    ]
                }

        except Exception as e:
            return {
                "success": False,
                "error": "Device discovery failed",
                "error_code": "DISCOVERY_ERROR",
                "message": f"Failed to discover devices: {str(e)}"
            }

    def _analyze_discovered_devices(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze discovered devices for health and connectivity."""
        analysis = {
            "total_count": len(devices),
            "online_count": 0,
            "offline_count": 0,
            "device_types": set(),
            "models": set(),
            "recommendations": [],
            "health_concerns": []
        }

        for device in devices:
            traits = device.get("traits", {})

            # Check connectivity
            connectivity = traits.get("sdm.devices.traits.Connectivity", {})
            if connectivity.get("status") == "ONLINE":
                analysis["online_count"] += 1
            else:
                analysis["offline_count"] += 1
                analysis["health_concerns"].append({
                    "device_id": device["name"].split("/")[-1],
                    "issue": "Device offline",
                    "severity": "high"
                })

            # Collect device info
            info = traits.get("sdm.devices.traits.Info", {})
            if info.get("modelNumber"):
                analysis["models"].add(info["modelNumber"])

            # Device type from name
            device_type = device.get("type", "").split(".")[-1]
            analysis["device_types"].add(device_type)

            # Check battery levels
            battery = traits.get("sdm.devices.traits.Battery", {})
            battery_level = battery.get("batteryLevel")
            if battery_level and battery_level < 20:
                analysis["health_concerns"].append({
                    "device_id": device["name"].split("/")[-1],
                    "issue": f"Low battery ({battery_level}%)",
                    "severity": "medium"
                })

        # Generate recommendations
        if analysis["offline_count"] > 0:
            analysis["recommendations"].append("Check power and connectivity for offline devices")

        if analysis["health_concerns"]:
            analysis["recommendations"].append("Address device health concerns promptly")

        if len(analysis["models"]) > 1:
            analysis["recommendations"].append("Consider standardizing device models for consistency")

        return analysis

    async def test_device_connectivity(self, device_id: str) -> Dict[str, Any]:
        """Test connectivity and responsiveness of a specific device."""
        if not self.session:
            return {
                "success": False,
                "error": "Session not initialized",
                "error_code": "SESSION_ERROR"
            }

        try:
            url = f"{self.base_url}/enterprises/{self.project_id}/devices/{device_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            start_time = time.time()
            async with self.session.get(url, headers=headers) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    device_data = await response.json()
                    connectivity_analysis = self._analyze_device_connectivity(device_data, response_time)

                    return {
                        "success": True,
                        "operation": "test_device_connectivity",
                        "summary": f"Device {device_id} connectivity test completed",
                        "result": {
                            "device_id": device_id,
                            "connectivity": connectivity_analysis,
                            "response_time_ms": round(response_time * 1000, 2)
                        },
                        "next_steps": [
                            "Run device functionality tests",
                            "Check device health metrics",
                            "Validate command execution"
                        ],
                        "context": {
                            "device_id": device_id,
                            "test_timestamp": datetime.now(timezone.utc).isoformat(),
                            "response_time": f"{response_time:.3f}s"
                        },
                        "suggestions": connectivity_analysis.get("recommendations", []),
                        "follow_up_questions": [
                            "Should I run a safety test on this device?",
                            "Would you like me to check the device health status?",
                            "Do you want to test device control functions?"
                        ]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Device connectivity test failed",
                        "error_code": f"CONNECTIVITY_ERROR_{response.status}",
                        "message": f"Cannot access device {device_id}",
                        "diagnostic_info": {
                            "device_id": device_id,
                            "http_status": response.status
                        }
                    }

        except Exception as e:
            return {
                "success": False,
                "error": "Device connectivity test failed",
                "error_code": "CONNECTIVITY_TEST_ERROR",
                "message": f"Failed to test device {device_id} connectivity: {str(e)}",
                "diagnostic_info": {
                    "device_id": device_id,
                    "error_type": type(e).__name__
                }
            }

    def _analyze_device_connectivity(self, device_data: Dict[str, Any], response_time: float) -> Dict[str, Any]:
        """Analyze device connectivity and performance."""
        traits = device_data.get("traits", {})
        connectivity = traits.get("sdm.devices.traits.Connectivity", {})

        analysis = {
            "status": connectivity.get("status", "UNKNOWN"),
            "signal_strength": connectivity.get("signalStrength", 0),
            "response_time_ms": round(response_time * 1000, 2),
            "last_event_time": device_data.get("lastEventTime"),
            "recommendations": []
        }

        # Performance analysis
        if response_time > 2.0:
            analysis["performance"] = "slow"
            analysis["recommendations"].append("Device response time is slow - check network conditions")
        elif response_time > 1.0:
            analysis["performance"] = "moderate"
            analysis["recommendations"].append("Device response time is acceptable but could be faster")
        else:
            analysis["performance"] = "good"

        # Connectivity analysis
        if analysis["status"] != "ONLINE":
            analysis["recommendations"].append("Device is offline - check power and network connection")

        signal_strength = analysis["signal_strength"]
        if signal_strength < 30:
            analysis["recommendations"].append("Weak Wi-Fi signal - consider moving device closer to router")
        elif signal_strength < 50:
            analysis["recommendations"].append("Moderate Wi-Fi signal - monitor for connectivity issues")

        # Last event analysis
        last_event = analysis["last_event_time"]
        if last_event:
            try:
                # Parse ISO timestamp
                last_event_dt = datetime.fromisoformat(last_event.replace('Z', '+00:00'))
                time_since_event = datetime.now(timezone.utc) - last_event_dt

                if time_since_event > timedelta(hours=24):
                    analysis["recommendations"].append("Device hasn't reported events recently - check connectivity")
                elif time_since_event > timedelta(hours=1):
                    analysis["recommendations"].append("Device event reporting is delayed")
            except:
                analysis["recommendations"].append("Cannot parse device event timestamps")

        return analysis


class RealDeviceTestSuite:
    """Comprehensive test suite for real Nest Protect devices."""

    def __init__(self, project_id: str, access_token: str):
        self.project_id = project_id
        self.access_token = access_token
        self.validator = ConversationalResponseValidator()

    async def run_full_device_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive tests on real devices."""
        results = {
            "test_suite": "Real Device Test Suite",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests_run": [],
            "overall_status": "running"
        }

        async with RealDeviceDiscovery(self.project_id, self.access_token) as discovery:
            # Test 1: API Connectivity
            api_test = await discovery.test_api_connectivity()
            results["tests_run"].append({
                "test_name": "api_connectivity",
                "result": api_test
            })

            if not api_test["success"]:
                results["overall_status"] = "failed"
                results["failure_reason"] = "API connectivity test failed"
                return results

            # Test 2: Device Discovery
            discovery_test = await discovery.discover_devices()
            results["tests_run"].append({
                "test_name": "device_discovery",
                "result": discovery_test
            })

            if not discovery_test["success"]:
                results["overall_status"] = "failed"
                results["failure_reason"] = "Device discovery failed"
                return results

            devices = discovery_test["result"]["devices"]
            if not devices:
                results["overall_status"] = "warning"
                results["warning_reason"] = "No devices discovered"
                return results

            # Test 3: Individual Device Connectivity
            device_tests = []
            for device in devices[:3]:  # Test first 3 devices to avoid rate limits
                device_id = device["name"].split("/")[-1]
                connectivity_test = await discovery.test_device_connectivity(device_id)
                device_tests.append({
                    "device_id": device_id,
                    "connectivity_test": connectivity_test
                })

            results["tests_run"].append({
                "test_name": "device_connectivity_tests",
                "result": {
                    "tested_devices": len(device_tests),
                    "device_results": device_tests
                }
            })

            # Validate conversational responses
            validation_results = self._validate_all_responses(results["tests_run"])
            results["conversational_validation"] = validation_results

            # Overall assessment
            all_passed = all(test["result"]["success"] for test in results["tests_run"])
            results["overall_status"] = "passed" if all_passed else "partial_failure"

        return results

    def _validate_all_responses(self, tests_run: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that all test responses follow conversational format."""
        validation_results = {
            "total_responses": 0,
            "valid_responses": 0,
            "invalid_responses": 0,
            "validation_errors": []
        }

        for test in tests_run:
            result = test["result"]
            if isinstance(result, dict) and "success" in result:
                validation_results["total_responses"] += 1

                operation = result.get("operation", test["test_name"])
                errors = self.validator.validate_conversational_response(result, operation)

                if errors:
                    validation_results["invalid_responses"] += 1
                    validation_results["validation_errors"].append({
                        "test": test["test_name"],
                        "operation": operation,
                        "errors": errors
                    })
                else:
                    validation_results["valid_responses"] += 1

        return validation_results

    async def test_device_responsiveness(self, device_ids: List[str]) -> Dict[str, Any]:
        """Test device responsiveness under load."""
        responsiveness_results = {
            "devices_tested": len(device_ids),
            "response_times": [],
            "success_rate": 0.0,
            "average_response_time": 0.0
        }

        async with RealDeviceDiscovery(self.project_id, self.access_token) as discovery:
            successful_requests = 0
            total_response_time = 0.0

            for device_id in device_ids:
                # Run multiple requests to test consistency
                for _ in range(3):
                    start_time = time.time()
                    result = await discovery.test_device_connectivity(device_id)
                    response_time = time.time() - start_time

                    responsiveness_results["response_times"].append({
                        "device_id": device_id,
                        "response_time": response_time,
                        "success": result["success"]
                    })

                    if result["success"]:
                        successful_requests += 1
                        total_response_time += response_time

                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)

            if successful_requests > 0:
                responsiveness_results["average_response_time"] = total_response_time / successful_requests
                responsiveness_results["success_rate"] = successful_requests / (len(device_ids) * 3)

        return responsiveness_results


# Test fixtures for real device testing
@pytest.fixture
async def real_device_discovery():
    """Fixture for real device discovery (requires valid credentials)."""
    # This would need real credentials in a real test environment
    project_id = "test-project-id"
    access_token = "test-access-token"

    return RealDeviceDiscovery(project_id, access_token)

@pytest.fixture
async def real_device_test_suite():
    """Fixture for real device test suite."""
    # This would need real credentials in a real test environment
    project_id = "test-project-id"
    access_token = "test-access-token"

    return RealDeviceTestSuite(project_id, access_token)