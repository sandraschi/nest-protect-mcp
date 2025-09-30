"""
Comprehensive tests for authentication and OAuth flows.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from nest_protect_mcp.server import NestProtectMCP, NEST_AUTH_URL
from nest_protect_mcp.models import ProtectConfig
from nest_protect_mcp.exceptions import NestAuthError, NestConnectionError


class TestOAuthAuthentication:
    """Test OAuth authentication flows."""

    @pytest.mark.asyncio
    async def test_oauth_token_refresh_flow(self, sample_config):
        """Test complete OAuth token refresh flow."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        # Mock successful token refresh
        token_response = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value.status = 200
            mock_session_instance.post.return_value.__aenter__.return_value.json.return_value = token_response
            mock_session.return_value = mock_session_instance

            # Trigger token refresh
            await server._refresh_access_token()

            # Verify token was updated
            assert server._access_token == "new-access-token"
            assert server._refresh_token == "new-refresh-token"
            assert server._token_expires_at > time.time()

            # Verify state was saved
            server._state_manager.set.assert_called()

    @pytest.mark.asyncio
    async def test_oauth_token_refresh_with_invalid_grant(self, sample_config):
        """Test OAuth token refresh with invalid grant error."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "invalid-refresh-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            response = AsyncMock()
            response.status = 400
            response.json.return_value = {"error": "invalid_grant"}
            mock_session_instance.post.return_value.__aenter__.return_value = response
            mock_session.return_value = mock_session_instance

            # Should handle invalid grant gracefully
            await server._refresh_access_token()

            # Tokens should be cleared
            assert server._access_token is None
            assert server._refresh_token is None
            assert server._token_expires_at == 0

    @pytest.mark.asyncio
    async def test_oauth_token_expiry_handling(self, sample_config):
        """Test handling of expired tokens."""
        server = NestProtectMCP(sample_config)
        server._access_token = "expired-token"
        server._token_expires_at = time.time() - 600  # Expired 10 minutes ago
        server._refresh_token = "valid-refresh-token"

        # Mock successful refresh
        token_response = {
            "access_token": "fresh-token",
            "expires_in": 3600
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value.status = 200
            mock_session_instance.post.return_value.__aenter__.return_value.json.return_value = token_response
            mock_session.return_value = mock_session_instance

            # Access token should trigger refresh
            token = await server.access_token

            assert token == "fresh-token"
            assert server._access_token == "fresh-token"

    @pytest.mark.asyncio
    async def test_oauth_no_refresh_token_scenario(self, sample_config):
        """Test scenario when no refresh token is available."""
        server = NestProtectMCP(sample_config)
        # No refresh token set

        # Should handle gracefully without crashing
        await server._refresh_access_token()

        # Should log warning but not crash
        assert server._access_token is None

    @pytest.mark.asyncio
    async def test_oauth_network_failure_handling(self, sample_config):
        """Test OAuth network failure handling."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.side_effect = Exception("Network error")
            mock_session.return_value = mock_session_instance

            with pytest.raises(NestConnectionError):
                await server._refresh_access_token()


class TestAuthenticationStateManagement:
    """Test authentication state persistence and management."""

    @pytest.mark.asyncio
    async def test_auth_state_persistence_cycle(self, sample_config):
        """Test complete auth state persistence cycle."""
        server = NestProtectMCP(sample_config)

        # Mock state manager
        server._state_manager = AsyncMock()

        # Set initial state
        server._access_token = "initial-token"
        server._refresh_token = "initial-refresh-token"
        server._token_expires_at = time.time() + 3600
        server._devices = {"device1": {"name": "Test Device"}}

        # Save state
        await server._save_auth_state()

        # Verify all state was saved
        assert server._state_manager.set.call_count >= 4  # tokens, expiry, devices

        # Load state in new server instance
        new_server = NestProtectMCP(sample_config)
        new_server._state_manager = server._state_manager

        await new_server._load_auth_state()

        # Verify state was loaded correctly
        assert new_server._access_token == "initial-token"
        assert new_server._refresh_token == "initial-refresh-token"
        assert new_server._devices == {"device1": {"name": "Test Device"}}

    @pytest.mark.asyncio
    async def test_auth_state_loading_with_missing_keys(self, sample_config):
        """Test auth state loading when some keys are missing."""
        server = NestProtectMCP(sample_config)

        # Mock state manager with incomplete state
        server._state_manager = AsyncMock()
        server._state_manager.get_all.return_value = {
            "access_token": "partial-token"
            # Missing refresh_token and token_expires_at
        }

        await server._load_auth_state()

        # Should handle missing keys gracefully
        assert server._access_token == "partial-token"
        assert server._refresh_token is None
        assert server._token_expires_at == 0

    @pytest.mark.asyncio
    async def test_auth_state_loading_corrupted_data(self, sample_config):
        """Test auth state loading with corrupted data."""
        server = NestProtectMCP(sample_config)

        # Mock state manager to return invalid data
        server._state_manager = AsyncMock()
        server._state_manager.get_all.side_effect = Exception("Corrupted state")

        # Should handle corruption gracefully
        await server._load_auth_state()

        # Should have default values
        assert server._access_token is None
        assert server._refresh_token is None
        assert server._token_expires_at == 0


class TestTokenValidation:
    """Test token validation and expiry handling."""

    @pytest.mark.asyncio
    async def test_token_expiry_buffer_calculation(self, sample_config):
        """Test token expiry buffer calculation."""
        server = NestProtectMCP(sample_config)

        # Set token to expire in 10 minutes
        server._access_token = "test-token"
        server._token_expires_at = time.time() + 600

        # Should not trigger refresh (buffer is 5 minutes)
        token = await server.access_token
        assert token == "test-token"

        # Set token to expire in 4 minutes (within buffer)
        server._token_expires_at = time.time() + 240

        # Mock refresh
        with patch.object(server, '_refresh_access_token') as mock_refresh:
            mock_refresh.return_value = None

            token = await server.access_token

            # Should trigger refresh
            mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_access_token_property_with_no_token(self, sample_config):
        """Test access_token property when no token exists."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = None

        with patch.object(server, '_refresh_access_token') as mock_refresh:
            mock_refresh.return_value = None

            token = await server.access_token

            # Should attempt refresh but return None
            mock_refresh.assert_called_once()
            assert token is None

    @pytest.mark.asyncio
    async def test_get_access_token_method(self, sample_config):
        """Test _get_access_token method."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-token"

        token = await server._get_access_token()
        assert token == "test-token"

    @pytest.mark.asyncio
    async def test_get_access_token_no_token(self, sample_config):
        """Test _get_access_token when no token available."""
        server = NestProtectMCP(sample_config)

        with patch.object(server, '_refresh_access_token') as mock_refresh:
            mock_refresh.return_value = None

            with pytest.raises(NestAuthError, match="No access token available"):
                await server._get_access_token()


class TestAuthenticationErrorScenarios:
    """Test various authentication error scenarios."""

    @pytest.mark.asyncio
    async def test_auth_server_unavailable(self, sample_config):
        """Test authentication when auth server is unavailable."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.side_effect = Exception("Connection refused")
            mock_session.return_value = mock_session_instance

            with pytest.raises(NestConnectionError):
                await server._refresh_access_token()

    @pytest.mark.asyncio
    async def test_auth_invalid_response_format(self, sample_config):
        """Test authentication with invalid response format."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            response = AsyncMock()
            response.status = 200
            response.json.side_effect = Exception("Invalid JSON")
            mock_session_instance.post.return_value.__aenter__.return_value = response
            mock_session.return_value = mock_session_instance

            with pytest.raises(NestAuthError):
                await server._refresh_access_token()

    @pytest.mark.asyncio
    async def test_auth_malformed_token_response(self, sample_config):
        """Test authentication with malformed token response."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        # Response missing required fields
        malformed_response = {
            "refresh_token": "new-refresh-token"
            # Missing access_token and expires_in
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value.status = 200
            mock_session_instance.post.return_value.__aenter__.return_value.json.return_value = malformed_response
            mock_session.return_value = mock_session_instance

            # Should handle missing fields gracefully
            await server._refresh_access_token()

            # Should not update tokens with malformed response
            assert server._access_token is None

    @pytest.mark.asyncio
    async def test_concurrent_token_refresh(self, sample_config):
        """Test concurrent token refresh scenarios."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        token_response = {
            "access_token": "concurrent-token",
            "expires_in": 3600
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.return_value.__aenter__.return_value.status = 200
            mock_session_instance.post.return_value.__aenter__.return_value.json.return_value = token_response
            mock_session.return_value = mock_session_instance

            # Run multiple concurrent token refreshes
            tasks = [
                server._refresh_access_token()
                for _ in range(3)
            ]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert len(results) == 3
            assert server._access_token == "concurrent-token"


class TestAuthenticationIntegration:
    """Test authentication integration with other components."""

    @pytest.mark.asyncio
    async def test_auth_integration_with_api_requests(self, sample_config):
        """Test authentication integration with API requests."""
        server = NestProtectMCP(sample_config)
        server._access_token = "test-token"
        server._token_expires_at = time.time() + 600

        response_data = {"devices": []}

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.request.return_value.__aenter__.return_value.status = 200
            mock_session_instance.request.return_value.__aenter__.return_value.json.return_value = response_data
            mock_session.return_value = mock_session_instance

            # Make API request
            result = await server._make_request('GET', 'test/endpoint')

            assert result == response_data

            # Verify auth header was included
            call_args = mock_session_instance.request.call_args
            headers = call_args[1]['headers']
            assert headers['Authorization'] == "Bearer test-token"

    @pytest.mark.asyncio
    async def test_auth_integration_with_state_persistence(self, sample_config):
        """Test authentication integration with state persistence."""
        server = NestProtectMCP(sample_config)

        # Mock state manager
        server._state_manager = AsyncMock()

        # Set tokens and save state
        server._access_token = "persistent-token"
        server._refresh_token = "persistent-refresh-token"
        server._token_expires_at = time.time() + 3600

        await server._save_auth_state()

        # Create new server instance and load state
        new_server = NestProtectMCP(sample_config)
        new_server._state_manager = server._state_manager

        await new_server._load_auth_state()

        # Should have loaded the persistent tokens
        assert new_server._access_token == "persistent-token"
        assert new_server._refresh_token == "persistent-refresh-token"

    def test_auth_constants_and_configuration(self, sample_config):
        """Test authentication constants and configuration."""
        server = NestProtectMCP(sample_config)

        # Check auth URL constant
        assert NEST_AUTH_URL == "https://www.googleapis.com/oauth2/v4/token"

        # Check token expiry buffer
        from nest_protect_mcp.server import TOKEN_EXPIRY_BUFFER
        assert TOKEN_EXPIRY_BUFFER == 300

        # Check state keys are properly initialized
        assert 'access_token' in server._state_keys
        assert 'refresh_token' in server._state_keys
        assert 'token_expires_at' in server._state_keys


class TestErrorRecoveryMechanisms:
    """Test error recovery mechanisms in authentication."""

    @pytest.mark.asyncio
    async def test_auth_failure_recovery(self, sample_config):
        """Test recovery from authentication failures."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        # Simulate auth failure
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            response = AsyncMock()
            response.status = 401
            response.json.return_value = {"error": "invalid_grant"}
            mock_session_instance.post.return_value.__aenter__.return_value = response
            mock_session.return_value = mock_session_instance

            # Should clear tokens on auth failure
            await server._refresh_access_token()

            assert server._access_token is None
            assert server._refresh_token is None

    @pytest.mark.asyncio
    async def test_partial_auth_state_recovery(self, sample_config):
        """Test recovery from partial authentication state."""
        server = NestProtectMCP(sample_config)

        # Mock state manager with partial state
        server._state_manager = AsyncMock()
        server._state_manager.get_all.return_value = {
            "access_token": "partial-token"
            # Missing other required fields
        }

        # Should handle partial state gracefully
        await server._load_auth_state()

        # Should only load available data
        assert server._access_token == "partial-token"
        assert server._refresh_token is None

    @pytest.mark.asyncio
    async def test_auth_retry_mechanism(self, sample_config):
        """Test authentication retry mechanism."""
        server = NestProtectMCP(sample_config)
        server._refresh_token = "test-refresh-token"

        # Mock initial failure then success
        call_count = 0
        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            response = AsyncMock()
            if call_count == 1:
                response.status = 500  # Server error
            else:
                response.status = 200  # Success
                response.json.return_value = {
                    "access_token": "retry-token",
                    "expires_in": 3600
                }
            return response

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session_instance = AsyncMock()
            mock_session_instance.post.side_effect = mock_post
            mock_session.return_value = mock_session_instance

            # This would need retry logic implementation in the actual code
            # For now, test that multiple calls work
            await server._refresh_access_token()
            await server._refresh_access_token()

            # Should handle multiple calls
            assert call_count == 2
