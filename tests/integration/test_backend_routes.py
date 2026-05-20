"""Integration tests for FastAPI web backend (web_sota)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from nest_protect_mcp.server import app

    with TestClient(app) as c:
        yield c


def test_health_returns_json(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True
    assert "api_connected" in body


def test_devices_requires_or_handles_auth(client):
    """Devices route returns 200 with structure or error-shaped JSON without crashing."""
    r = client.get("/api/v1/devices")
    assert r.status_code in (200, 400, 500)
    assert r.headers.get("content-type", "").startswith("application/json")


def test_cors_allow_origins_helper(monkeypatch):
    monkeypatch.delenv("WIZARD_FRONTEND_ORIGIN", raising=False)
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    from nest_protect_mcp.server import _cors_allow_origins

    assert "http://127.0.0.1:10752" in _cors_allow_origins()

    monkeypatch.setenv("WIZARD_FRONTEND_ORIGIN", "http://192.168.0.185:10752")
    assert "http://192.168.0.185:10752" in _cors_allow_origins()
