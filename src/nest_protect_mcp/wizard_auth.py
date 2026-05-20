"""In-memory PCM OAuth wizard sessions (browser callback → one-time .env retrieval)."""

from __future__ import annotations

import logging
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import aiohttp

from .constants import (
    GOOGLE_OAUTH_TOKEN_URL,
    NEST_SDM_OAUTH_SCOPE,
    partner_connections_auth_base,
)

logger = logging.getLogger(__name__)

PENDING_TTL_SEC = 900
COMPLETED_TTL_SEC = 300


@dataclass
class PendingWizard:
    client_id: str
    client_secret: str
    project_id: str
    redirect_uri: str
    scope: str
    created: float


@dataclass
class CompletedWizard:
    nest_client_id: str
    nest_client_secret: str
    nest_project_id: str
    nest_refresh_token: str
    scope_granted: str | None
    created: float


_pending: dict[str, PendingWizard] = {}
_completed: dict[str, CompletedWizard] = {}


def _purge_expired() -> None:
    now = time.time()
    for k, p in list(_pending.items()):
        if now - p.created > PENDING_TTL_SEC:
            del _pending[k]
    for k, c in list(_completed.items()):
        if now - c.created > COMPLETED_TTL_SEC:
            del _completed[k]


def wizard_callback_uri(backend_base: str) -> str:
    """Full redirect URI registered in Google OAuth client (must match exactly)."""
    base = backend_base.rstrip("/")
    return f"{base}/api/v1/auth/callback"


def start_wizard_session(
    *,
    client_id: str,
    client_secret: str,
    project_id: str,
    backend_base_url: str,
    scope: str | None = None,
) -> tuple[str, str]:
    """Store pending session; return (oauth_state, pcm_authorize_url).

    oauth_state maps the browser callback to client credentials stored in memory.
    """
    _purge_expired()
    oauth_state = secrets.token_urlsafe(32)
    redirect_uri = wizard_callback_uri(backend_base_url)
    eff_scope = (scope or NEST_SDM_OAUTH_SCOPE).strip()

    _pending[oauth_state] = PendingWizard(
        client_id=client_id.strip(),
        client_secret=client_secret.strip(),
        project_id=project_id.strip(),
        redirect_uri=redirect_uri,
        scope=eff_scope,
        created=time.time(),
    )

    auth_base = partner_connections_auth_base(project_id)
    params = {
        "client_id": client_id.strip(),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": eff_scope,
        "state": oauth_state,
        "access_type": "offline",
        "prompt": "consent",
    }
    authorize_url = f"{auth_base}?{urlencode(params)}"
    return oauth_state, authorize_url


async def _exchange_authorization_code(
    *,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            GOOGLE_OAUTH_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        ) as response:
            data: dict[str, Any] = await response.json()
            data["_http_status"] = response.status
            return data


async def complete_pcm_callback(
    *,
    oauth_state: str | None,
    code: str | None,
    oauth_error: str | None,
    oauth_error_description: str | None,
) -> tuple[str | None, str | None]:
    """Exchange code or return error. Returns (completion_id, error_message)."""
    _purge_expired()

    if oauth_error:
        msg = oauth_error_description or oauth_error
        logger.warning("PCM OAuth error: %s", msg)
        return None, msg

    if not oauth_state:
        return None, "missing_state"

    if not code:
        return None, "missing_code"

    pending = _pending.pop(oauth_state, None)
    if not pending:
        return None, "session_expired_or_invalid_state_retry_wizard"

    token_payload = await _exchange_authorization_code(
        code=code,
        redirect_uri=pending.redirect_uri,
        client_id=pending.client_id,
        client_secret=pending.client_secret,
    )

    if token_payload.get("_http_status") != 200:
        err = token_payload.get("error_description") or token_payload.get("error")
        return None, str(err or "token_exchange_failed")

    refresh_token = token_payload.get("refresh_token")
    if not refresh_token:
        return (
            None,
            "no_refresh_token: revoke this app under Google Account permissions "
            "and run the wizard again so Google issues a new refresh token.",
        )

    completion_id = secrets.token_urlsafe(24)
    _completed[completion_id] = CompletedWizard(
        nest_client_id=pending.client_id,
        nest_client_secret=pending.client_secret,
        nest_project_id=pending.project_id,
        nest_refresh_token=str(refresh_token),
        scope_granted=token_payload.get("scope"),
        created=time.time(),
    )
    return completion_id, None


def pop_completion(completion_id: str) -> CompletedWizard | None:
    """One-time read of wizard result."""
    _purge_expired()
    return _completed.pop(completion_id, None)


def format_dotenv(w: CompletedWizard) -> str:
    """Human-readable .env block (repo root)."""
    lines = [
        f"NEST_CLIENT_ID={w.nest_client_id}",
        f"NEST_CLIENT_SECRET={w.nest_client_secret}",
        f"NEST_PROJECT_ID={w.nest_project_id}",
        f"NEST_REFRESH_TOKEN={w.nest_refresh_token}",
    ]
    return "\n".join(lines) + "\n"
