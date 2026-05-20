"""
ASGI entry point for the Nest Protect MCP web backend.

Provides FastAPI REST API for fire/CO alarm devices (web_sota).
Use nest_protect_mcp.fastmcp_server:app for the MCP server itself (stdio/--http).
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

_log = logging.getLogger(__name__)


def _init_nest_app_state() -> bool:
    """Load .env and set Nest app state from NEST_* env vars. Returns True if all set."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    repo_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(repo_root / ".env")
    client_id = os.getenv("NEST_CLIENT_ID")
    client_secret = os.getenv("NEST_CLIENT_SECRET")
    project_id = os.getenv("NEST_PROJECT_ID")
    refresh_token = os.getenv("NEST_REFRESH_TOKEN")
    if not all([client_id, client_secret, project_id, refresh_token]):
        return False
    from .state_manager import get_app_state, initialize_app_state

    class _Config:
        pass

    config = _Config()
    config.client_id = client_id
    config.client_secret = client_secret
    config.project_id = project_id
    initialize_app_state(config)
    state = get_app_state()
    state.refresh_token = refresh_token
    return True


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup: refresh OAuth access token when refresh token exists."""
    await _startup_refresh_token()
    yield


async def _startup_refresh_token() -> None:
    """Refresh access token on startup so first API call works."""
    from .state_manager import get_app_state

    state = get_app_state()
    if not state.refresh_token:
        return
    try:
        from .tools.auth_tools import refresh_access_token

        await refresh_access_token(force=True)
    except Exception as e:
        _log.debug("Startup token refresh skipped or failed: %s", e)


_init_nest_app_state()


def _cors_allow_origins() -> list[str]:
    """Defaults plus LAN: set ``WIZARD_FRONTEND_ORIGIN`` and optional ``CORS_ALLOW_ORIGINS``."""
    origins = [
        "http://localhost:10752",
        "http://127.0.0.1:10752",
    ]
    wiz = os.getenv("WIZARD_FRONTEND_ORIGIN", "").strip().rstrip("/")
    if wiz:
        origins.append(wiz)
    extra = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if extra:
        for part in extra.split(","):
            p = part.strip().rstrip("/")
            if p:
                origins.append(p)
    seen: set[str] = set()
    out: list[str] = []
    for o in origins:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


app = FastAPI(
    title="Nest Protect MCP API",
    description="Fire and CO alarm backend for Nest Protect web_sota",
    version="0.1.0",
    lifespan=_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _unwrap(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize MCP tool result for REST: success + data or error."""
    if result.get("success") is True:
        return result
    if result.get("error") or result.get("error_code"):
        raise HTTPException(
            status_code=400
            if "AUTHENTICATION" in str(result.get("error_code", ""))
            else 500,
            detail=result.get("message") or result.get("error", "Request failed"),
        )
    return result


@app.get("/api/v1/health")
async def health() -> dict[str, Any]:
    """Health check for the backend."""
    from .tools.system_status import get_api_status

    api_result = await get_api_status()
    return {
        "success": True,
        "message": "Nest Protect MCP backend",
        "api_connected": api_result.get("status") == "success"
        or "connected" in str(api_result).lower(),
    }


@app.get("/api/v1/devices")
async def get_devices() -> dict[str, Any]:
    """List all Nest Protect (fire/CO) devices."""
    from .tools.device_status import list_devices

    result = await list_devices()
    _unwrap(result)
    inner = result.get("result", {})
    devices = inner.get("devices", [])
    stats = inner.get("stats", {})
    return {
        "success": True,
        "devices": devices,
        "count": len(devices),
        "stats": stats,
        "summary": result.get("summary", ""),
    }


@app.get("/api/v1/devices/{device_id}")
async def get_device(device_id: str) -> dict[str, Any]:
    """Get status of one Nest Protect device (fire/CO, battery, connectivity)."""
    from .tools.device_status import get_device_status

    result = await get_device_status(device_id)
    _unwrap(result)
    inner = result.get("result") or {}
    device = inner.get("device") if isinstance(inner, dict) else result
    return {"success": True, "device": device}


@app.get("/api/v1/devices/{device_id}/events")
async def get_device_events(device_id: str, limit: int = 10) -> dict[str, Any]:
    """Get recent events for a device."""
    from .tools.device_status import get_device_events as tool_events

    result = await tool_events(device_id, limit)
    _unwrap(result)
    inner = result.get("result") or {}
    events = inner.get("events", []) if isinstance(inner, dict) else []
    return {"success": True, "events": events, "count": len(events)}


@app.get("/api/v1/status")
async def get_status() -> dict[str, Any]:
    """System and safety overview (for dashboard)."""
    from .tools.device_status import list_devices
    from .tools.system_status import get_system_status

    devices_result = await list_devices()
    devices = []
    stats = {"total": 0, "online": 0}
    if devices_result.get("success") and devices_result.get("result"):
        devices = devices_result["result"].get("devices", [])
        stats = devices_result["result"].get("stats", stats)
    system_result = None
    try:
        system_result = await get_system_status()
    except Exception as e:
        _log.debug("get_system_status in /status failed: %s", e)
    return {
        "success": True,
        "status": {
            "total_devices": stats.get("total", len(devices)),
            "online_devices": stats.get("online", 0),
            "devices": devices,
        },
        "system": system_result
        if system_result and system_result.get("status") == "success"
        else None,
    }


class HushBody(BaseModel):
    """Body for hush alarm."""

    duration_seconds: int = Field(180, ge=30, le=300)


@app.post("/api/v1/devices/{device_id}/hush")
async def hush_alarm(device_id: str, body: HushBody | None = None) -> dict[str, Any]:
    """Hush (silence) an active fire/CO alarm."""
    from .tools.device_control import hush_alarm as tool_hush

    duration = (body or HushBody()).duration_seconds
    result = await tool_hush(device_id, duration)
    if result.get("status") == "error":
        raise HTTPException(
            status_code=400, detail=result.get("message", "Hush failed")
        )
    return {"success": True, "message": "Alarm hushed", "result": result}


class SafetyCheckBody(BaseModel):
    """Body for safety check."""

    test_type: str = Field("full", description="full, smoke, co, heat")


@app.post("/api/v1/devices/{device_id}/safety-check")
async def run_safety_check(
    device_id: str, body: SafetyCheckBody | None = None
) -> dict[str, Any]:
    """Run a safety check (test) on a Nest Protect device."""
    from .tools.device_control import run_safety_check as tool_safety

    test_type = (body or SafetyCheckBody()).test_type
    result = await tool_safety(device_id, test_type)
    if result.get("status") == "error":
        raise HTTPException(
            status_code=400, detail=result.get("message", "Safety check failed")
        )
    return {"success": True, "message": "Safety check completed", "result": result}


class WizardStartBody(BaseModel):
    """Start browser PCM OAuth wizard (credentials kept in memory until callback)."""

    client_id: str = Field(..., min_length=8)
    client_secret: str = Field(..., min_length=1)
    project_id: str = Field(
        ...,
        min_length=8,
        description="Nest Device Access project id (UUID)",
    )


@app.post("/api/v1/auth/wizard/start")
async def wizard_pcm_start(body: WizardStartBody) -> dict[str, Any]:
    """Returns PCM authorize URL; register ``redirect_uri_must_register`` in Google OAuth client."""
    from .wizard_auth import start_wizard_session, wizard_callback_uri

    backend_base = os.getenv(
        "WIZARD_BACKEND_BASE_URL", "http://127.0.0.1:10753"
    ).strip()
    _, authorize_url = start_wizard_session(
        client_id=body.client_id,
        client_secret=body.client_secret,
        project_id=body.project_id,
        backend_base_url=backend_base,
    )
    redirect_must = wizard_callback_uri(backend_base)
    return {
        "success": True,
        "authorize_url": authorize_url,
        "redirect_uri_must_register": redirect_must,
        "instructions": (
            "Add redirect_uri_must_register verbatim to Authorized redirect URIs "
            "(OAuth client → Google Cloud Console), then open authorize_url in this browser."
        ),
    }


@app.get("/api/v1/auth/callback")
async def wizard_pcm_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    """PCM / Google redirects here after user signs in."""
    from .wizard_auth import complete_pcm_callback

    frontend = os.getenv(
        "WIZARD_FRONTEND_ORIGIN", "http://127.0.0.1:10752"
    ).rstrip("/")

    completion_id, err_msg = await complete_pcm_callback(
        oauth_state=state,
        code=code,
        oauth_error=error,
        oauth_error_description=error_description,
    )

    if err_msg:
        return RedirectResponse(
            url=f"{frontend}/onboarding?wizard_error={quote(err_msg, safe='')}",
            status_code=302,
        )

    assert completion_id is not None
    return RedirectResponse(
        url=f"{frontend}/onboarding?wizard_complete={quote(completion_id, safe='')}",
        status_code=302,
    )


@app.get("/api/v1/auth/wizard/result/{completion_id}")
async def wizard_pcm_result(completion_id: str) -> dict[str, Any]:
    """Fetch generated credentials once (then invalidated). Localhost-only wizard."""
    from .wizard_auth import format_dotenv, pop_completion

    row = pop_completion(completion_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Expired or already retrieved — run the wizard again.",
        )

    return {
        "success": True,
        "nest_client_id": row.nest_client_id,
        "nest_client_secret": row.nest_client_secret,
        "nest_project_id": row.nest_project_id,
        "nest_refresh_token": row.nest_refresh_token,
        "scope_granted": row.scope_granted,
        "dotenv": format_dotenv(row),
    }
