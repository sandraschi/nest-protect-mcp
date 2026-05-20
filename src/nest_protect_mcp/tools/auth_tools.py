"""Authentication tools for Nest Protect MCP."""

import logging
import os
import secrets
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from pydantic import BaseModel, Field

from ..constants import (
    GOOGLE_OAUTH_TOKEN_URL,
    NEST_SDM_OAUTH_SCOPE,
    partner_connections_auth_base,
)

_log = logging.getLogger(__name__)


class OAuthFlowParams(BaseModel):
    """Parameters for OAuth flow initiation."""

    redirect_uri: str = Field(
        "http://localhost:8000/auth/callback", description="Redirect URI for auth code"
    )
    state: str | None = Field(None, description="CSRF protection state")
    open_browser: bool = Field(True, description="Open auth URL in browser")


class OAuthCallbackParams(BaseModel):
    """Parameters for OAuth callback handling."""

    code: str = Field(..., description="Auth code from OAuth callback")
    state: str = Field(..., description="State param from OAuth")
    expected_state: str | None = Field(None, description="Expected CSRF state")
    redirect_uri: str = Field(
        "http://localhost:8000/auth/callback",
        description="Redirect URI used in auth request",
    )


class RefreshTokenParams(BaseModel):
    """Parameters for token refresh."""

    force: bool = Field(False, description="Force refresh even if token not expired")


class ValidateNestAuthParams(BaseModel):
    """Parameters for SDM credential validation."""

    force_refresh: bool = Field(
        False,
        description="Refresh access token before probing SDM (recommended if calls fail)",
    )


class PCMUrlParams(BaseModel):
    """Parameters to build a Partner Connections authorize URL."""

    redirect_uri: str = Field(
        "http://127.0.0.1:8080/callback",
        description="Must exactly match an authorized redirect URI in Google Cloud",
    )
    open_browser: bool = Field(False, description="Open the PCM URL in the default browser")


_REPO_DOTENV_DONE: bool = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_repo_dotenv() -> None:
    """Load repo root .env once so MCP stdio picks up NEST_* without FastAPI."""
    global _REPO_DOTENV_DONE
    if _REPO_DOTENV_DONE:
        return
    try:
        from dotenv import load_dotenv

        p = _repo_root() / ".env"
        if p.is_file():
            load_dotenv(p)
    except Exception as e:
        _log.debug("Could not load repo .env: %s", e)
    _REPO_DOTENV_DONE = True


def _hydrate_app_state_from_nest_env() -> None:
    """Copy NEST_* from the environment into AppState.config / refresh_token."""
    _load_repo_dotenv()
    from ..state_manager import get_app_state

    st = get_app_state()
    if st.config is None:

        class _Cfg:
            pass

        st.config = _Cfg()

    c = st.config
    mapping = (
        ("client_id", "NEST_CLIENT_ID"),
        ("client_secret", "NEST_CLIENT_SECRET"),
        ("project_id", "NEST_PROJECT_ID"),
    )
    for attr, ek in mapping:
        v = os.getenv(ek, "").strip()
        cur = getattr(c, attr, None)
        if v and (not cur or not str(cur).strip()):
            setattr(c, attr, v)

    rt = os.getenv("NEST_REFRESH_TOKEN", "").strip()
    if rt and not getattr(st, "refresh_token", None):
        st.refresh_token = rt


def _mask_suffix(value: str | None, tail: int = 4) -> str | None:
    if not value:
        return None
    if len(value) <= tail:
        return "****"
    return "****" + value[-tail:]


def _effective_sdm_scope() -> str:
    """SDM scope; consent screen lists this as Smart Device Management / home automation."""
    return os.getenv("NEST_SDM_OAUTH_SCOPE", NEST_SDM_OAUTH_SCOPE).strip()


async def initiate_oauth_flow(
    redirect_uri: str = "http://localhost:8000/auth/callback",
    state: str | None = None,
    open_browser: bool = True,
) -> dict[str, Any]:
    """Initiate OAuth 2.0 flow for Nest Device Access (Partner Connections Manager).

    Uses the PCM authorization URL (not accounts.google.com). Requires
    ``NEST_PROJECT_ID`` — the Device Access project id (enterprise id for SDM API).
    """
    _hydrate_app_state_from_nest_env()
    from ..state_manager import get_app_state

    if not state:
        state = secrets.token_urlsafe(16)

    app_state = get_app_state()
    app_state.oauth_state = state

    project_id = getattr(app_state.config, "project_id", "") or ""
    if not str(project_id).strip():
        return {
            "status": "error",
            "message": (
                "NEST_PROJECT_ID is not set. Use your Google Nest **Device Access** "
                "project id (same id as in SDM enterprise paths)."
            ),
            "error": "missing_project_id",
        }

    client_id = getattr(app_state.config, "client_id", "") or ""
    if not str(client_id).strip():
        return {
            "status": "error",
            "message": "NEST_CLIENT_ID is not set.",
            "error": "missing_client_id",
        }

    scope = _effective_sdm_scope()
    auth_base = partner_connections_auth_base(project_id)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    url = f"{auth_base}?{urlencode(params)}"

    if open_browser:
        webbrowser.open(url)

    return {
        "status": "success",
        "message": (
            "OAuth flow initiated (Partner Connections / SDM scope; "
            "labeled Home automation on Google consent when applicable)."
        ),
        "auth_url": url,
        "state": state,
        "scope": scope,
    }


async def handle_oauth_callback(
    code: str,
    state: str,
    expected_state: str | None = None,
    redirect_uri: str = "http://localhost:8000/auth/callback",
) -> dict[str, Any]:
    """Handle OAuth 2.0 callback from Nest API."""
    import aiohttp

    from ..state_manager import get_app_state

    if expected_state and state != expected_state:
        return {
            "status": "error",
            "message": "Invalid state parameter",
            "error": "state_mismatch",
        }

    try:
        app_state = get_app_state()
        token_url = GOOGLE_OAUTH_TOKEN_URL
        data = {
            "client_id": app_state.config.client_id,
            "client_secret": app_state.config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                token_data = await response.json()

                if response.status != 200:
                    return {
                        "status": "error",
                        "message": "Failed to exchange authorization code",
                        "error": token_data.get("error"),
                        "error_description": token_data.get("error_description"),
                    }

                app_state.access_token = token_data["access_token"]
                app_state.refresh_token = token_data.get("refresh_token")
                app_state.token_expires_in = token_data.get("expires_in")

                return {
                    "status": "success",
                    "message": "Successfully authenticated with Nest API",
                    "access_token": "****"
                    + (app_state.access_token[-4:] if app_state.access_token else ""),
                    "token_type": token_data.get("token_type"),
                    "expires_in": token_data.get("expires_in"),
                    "scope": token_data.get("scope"),
                    "refresh_token": "****" if "refresh_token" in token_data else None,
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to complete OAuth flow: {e!s}",
            "error": "oauth_error",
        }


async def get_nest_auth_status() -> dict[str, Any]:
    """Summarize configured credentials and tokens (masked). Does not call Google."""
    _hydrate_app_state_from_nest_env()
    from ..state_manager import get_app_state

    st = get_app_state()
    cfg = st.config
    cid = getattr(cfg, "client_id", None) if cfg else None
    secret_set = bool(getattr(cfg, "client_secret", None) if cfg else None)
    pid = getattr(cfg, "project_id", None) if cfg else None

    return {
        "status": "success",
        "nest_client_id_suffix": _mask_suffix((cid or "").strip() or None, 10),
        "nest_client_secret_configured": secret_set,
        "nest_project_id_configured": bool(pid and str(pid).strip()),
        "nest_project_id_suffix": _mask_suffix((str(pid).strip() if pid else "") or None, 6),
        "has_refresh_token": bool(getattr(st, "refresh_token", None)),
        "has_access_token": bool(getattr(st, "access_token", None)),
        "access_token_suffix": _mask_suffix(getattr(st, "access_token", None)),
        "token_expires_in_seconds": getattr(st, "token_expires_in", None),
        "pending_oauth_state": bool(getattr(st, "oauth_state", None)),
        "sdm_scope": _effective_sdm_scope(),
    }


async def get_oauth_redirect_reference() -> dict[str, Any]:
    """Return redirect URIs, doc links, and CLI hints for Google OAuth (PCM)."""
    return {
        "status": "success",
        "sdm_scope": _effective_sdm_scope(),
        "authorized_redirect_uri_examples": {
            "cli_just_auth_default": "http://127.0.0.1:8080/callback",
            "web_wizard_backend": "http://127.0.0.1:10753/api/v1/auth/callback",
        },
        "links": {
            "google_cloud_credentials": "https://console.cloud.google.com/apis/credentials",
            "revoke_app_access": "https://myaccount.google.com/permissions",
            "nest_pcm_authorization_docs": (
                "https://developers.google.com/nest/device-access/api/authorization"
            ),
        },
        "cli": {
            "just": "just auth",
            "uv": "uv run python scripts/get_nest_refresh_token.py --project-id YOUR_DEVICE_ACCESS_UUID",
        },
    }


async def get_pcm_authorize_url(
    redirect_uri: str = "http://127.0.0.1:8080/callback",
    open_browser: bool = False,
) -> dict[str, Any]:
    """Build Partner Connections authorize URL (optional browser); same flow as start_google_oauth."""
    return await initiate_oauth_flow(
        redirect_uri=redirect_uri,
        state=None,
        open_browser=open_browser,
    )


async def validate_nest_credentials(
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Refresh token if requested, then GET SDM enterprises/{{project}}/devices?pageSize=1."""
    import aiohttp

    _hydrate_app_state_from_nest_env()
    from ..state_manager import get_app_state

    st = get_app_state()
    pid = getattr(st.config, "project_id", "") if st.config else ""
    if not str(pid).strip():
        return {
            "status": "error",
            "message": "NEST_PROJECT_ID missing",
            "error": "missing_project_id",
        }
    if not getattr(st, "refresh_token", None):
        return {
            "status": "error",
            "message": "NEST_REFRESH_TOKEN missing",
            "error": "missing_refresh_token",
        }

    rr = await refresh_access_token(force=force_refresh)
    if rr.get("status") == "error":
        return {
            "status": "error",
            "message": rr.get("message", "refresh_failed"),
            "error": rr.get("error", "refresh_failed"),
            "details": rr,
        }

    if not st.access_token:
        rr2 = await refresh_access_token(force=True)
        if rr2.get("status") == "error":
            return {
                "status": "error",
                "message": rr2.get("message", "refresh_failed"),
                "error": rr2.get("error", "refresh_failed"),
            }

    url = (
        "https://smartdevicemanagement.googleapis.com/v1/"
        f"enterprises/{pid.strip()}/devices?pageSize=1"
    )
    headers = {"Authorization": f"Bearer {st.access_token}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                body = await response.text()
                if response.status == 200:
                    return {
                        "status": "success",
                        "message": "SDM API accepted credentials (devices endpoint reachable)",
                        "http_status": response.status,
                        "token_refreshed": force_refresh,
                    }
                return {
                    "status": "error",
                    "message": f"SDM returned HTTP {response.status}",
                    "http_status": response.status,
                    "body_preview": body[:500],
                    "error": "sdm_probe_failed",
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"SDM probe failed: {e!s}",
            "error": "sdm_probe_exception",
        }


async def refresh_access_token(force: bool = False) -> dict[str, Any]:
    """Refresh OAuth 2.0 access token using refresh token."""
    import aiohttp

    _hydrate_app_state_from_nest_env()
    from ..state_manager import get_app_state

    app_state = get_app_state()

    if not app_state.refresh_token:
        return {
            "status": "error",
            "message": "No refresh token available",
            "error": "no_refresh_token",
        }

    exp = getattr(app_state, "token_expires_in", None)
    if (
        not force
        and getattr(app_state, "access_token", None)
        and exp is not None
        and not exp < 300
    ):
        return {"status": "success", "message": "Token not expired, refresh not needed"}

    try:
        token_url = GOOGLE_OAUTH_TOKEN_URL
        data = {
            "client_id": app_state.config.client_id,
            "client_secret": app_state.config.client_secret,
            "refresh_token": app_state.refresh_token,
            "grant_type": "refresh_token",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                token_data = await response.json()

                if response.status != 200:
                    return {
                        "status": "error",
                        "message": "Failed to refresh access token",
                        "error": token_data.get("error"),
                        "error_description": token_data.get("error_description"),
                    }

                app_state.access_token = token_data["access_token"]
                app_state.token_expires_in = token_data.get("expires_in")

                return {
                    "status": "success",
                    "message": "Access token refreshed",
                    "access_token": "****"
                    + (app_state.access_token[-4:] if app_state.access_token else ""),
                    "token_type": token_data.get("token_type"),
                    "expires_in": token_data.get("expires_in"),
                    "scope": token_data.get("scope"),
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to refresh access token: {e!s}",
            "error": "refresh_failed",
        }
