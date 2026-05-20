"""Unit tests for auth_tools (hydration, refresh policy, helpers)."""

from unittest.mock import AsyncMock, MagicMock, patch

import nest_protect_mcp.state_manager as sm
import pytest


@pytest.fixture(autouse=True)
def reset_app_state():
    """Isolate AppState singleton between tests."""
    from nest_protect_mcp.tools import auth_tools

    sm._app_state = None
    auth_tools._REPO_DOTENV_DONE = False
    yield
    sm._app_state = None
    auth_tools._REPO_DOTENV_DONE = False


@pytest.mark.asyncio
async def test_refresh_skips_when_token_still_valid():
    """Do not call Google when access token exists and expires_in is far out."""
    from nest_protect_mcp.tools import auth_tools
    st = sm.get_app_state()
    st.refresh_token = "refresh"
    st.access_token = "access-token-value"
    st.token_expires_in = 3600
    st.config = MagicMock()
    st.config.client_id = "id"
    st.config.client_secret = "secret"

    with patch("aiohttp.ClientSession") as sess_cls:
        out = await auth_tools.refresh_access_token(force=False)
        assert out["status"] == "success"
        sess_cls.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_runs_when_access_token_missing():
    """Refresh when refresh token exists but access token is missing."""
    from nest_protect_mcp.tools import auth_tools
    st = sm.get_app_state()
    st.refresh_token = "rt"
    st.access_token = None
    st.token_expires_in = 3600
    st.config = MagicMock()
    st.config.client_id = "id"
    st.config.client_secret = "sec"

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "access_token": "new-at",
            "expires_in": 3599,
            "token_type": "Bearer",
        }
    )

    post_cm = MagicMock()
    post_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    post_cm.__aexit__ = AsyncMock(return_value=None)

    mock_sess = MagicMock()
    mock_sess.post = MagicMock(return_value=post_cm)

    sess_cm = MagicMock()
    sess_cm.__aenter__ = AsyncMock(return_value=mock_sess)
    sess_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "aiohttp.ClientSession",
        return_value=sess_cm,
    ):
        out = await auth_tools.refresh_access_token(force=False)

    assert out["status"] == "success"
    assert st.access_token == "new-at"


@pytest.mark.asyncio
async def test_get_oauth_redirect_reference_structure():
    from nest_protect_mcp.tools.auth_tools import get_oauth_redirect_reference

    out = await get_oauth_redirect_reference()
    assert out["status"] == "success"
    assert "authorized_redirect_uri_examples" in out
    assert "cli_just_auth_default" in out["authorized_redirect_uri_examples"]
    assert "links" in out


@pytest.mark.asyncio
async def test_get_nest_auth_status_masked():
    from nest_protect_mcp.tools import auth_tools
    st = sm.get_app_state()
    st.config = MagicMock()
    st.config.client_id = "client-id-long"
    st.config.client_secret = "s"
    st.config.project_id = "proj-uuid-here"
    st.refresh_token = "rt"
    st.access_token = "abcdefgh"

    out = await auth_tools.get_nest_auth_status()
    assert out["status"] == "success"
    assert out["nest_client_secret_configured"] is True
    assert out["access_token_suffix"] == "****efgh"


@pytest.mark.asyncio
async def test_validate_nest_credentials_missing_project():
    from nest_protect_mcp.tools import auth_tools

    def noop_hydrate() -> None:
        return None

    with patch.object(auth_tools, "_hydrate_app_state_from_nest_env", noop_hydrate):
        st = sm.get_app_state()

        class _Cfg:
            project_id = ""

        st.config = _Cfg()

        out = await auth_tools.validate_nest_credentials()
    assert out["status"] == "error"
    assert out["error"] == "missing_project_id"
