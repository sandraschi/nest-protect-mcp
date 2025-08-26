"""Authentication tools for Nest Protect MCP."""

import os
import webbrowser
from typing import Dict, Any, Optional
from urllib.parse import urlencode, parse_qs, urlparse

from ..tools import tool

@tool(name="initiate_oauth_flow", description="Start OAuth 2.0 flow for Nest API", parameters={"redirect_uri": {"type": "string", "description": "Redirect URI for auth code", "default": "http://localhost:8000/auth/callback"}, "state": {"type": "string", "description": "CSRF protection state", "required": False}, "open_browser": {"type": "boolean", "description": "Open auth URL in browser", "default": True}}, examples=["initiate_oauth_flow()"])
async def initiate_oauth_flow(redirect_uri: str = "http://localhost:8000/auth/callback", state: Optional[str] = None, open_browser: bool = True) -> Dict[str, Any]:
    """Initiate OAuth 2.0 flow for Nest API."""
    from ..server import app
    
    if not state:
        import secrets
        state = secrets.token_urlsafe(16)
    
    app.state.oauth_state = state
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": app.state.config.nest_client_id,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/sdm.service",
        "redirect_uri": redirect_uri,
        "state": state,
    }
    
    url = f"{auth_url}?{urlencode(params)}"
    
    if open_browser:
        webbrowser.open(url)
    
    return {"status": "success", "message": "OAuth flow initiated", "auth_url": url, "state": state}

@tool(name="handle_oauth_callback", description="Handle OAuth 2.0 callback from Nest API", parameters={"code": {"type": "string", "description": "Auth code from OAuth callback", "required": True}, "state": {"type": "string", "description": "State param from OAuth", "required": True}, "expected_state": {"type": "string", "description": "Expected CSRF state", "required": False}, "redirect_uri": {"type": "string", "description": "Redirect URI used in auth request", "default": "http://localhost:8000/auth/callback"}}, examples=["handle_oauth_callback(code='abc123', state='xyz456')"])
async def handle_oauth_callback(code: str, state: str, expected_state: Optional[str] = None, redirect_uri: str = "http://localhost:8000/auth/callback") -> Dict[str, Any]:
    """Handle OAuth 2.0 callback from Nest API."""
    from ..server import app
    
    if expected_state and state != expected_state:
        return {"status": "error", "message": "Invalid state parameter", "error": "state_mismatch"}
    
    try:
        token_url = "https://www.googleapis.com/oauth2/v4/token"
        data = {
            "client_id": app.state.config.nest_client_id,
            "client_secret": app.state.config.nest_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        async with app.state.http_session.post(token_url, data=data) as response:
            token_data = await response.json()
            
            if response.status != 200:
                return {
                    "status": "error",
                    "message": "Failed to exchange authorization code",
                    "error": token_data.get("error"),
                    "error_description": token_data.get("error_description")
                }
            
            app.state.access_token = token_data["access_token"]
            app.state.refresh_token = token_data.get("refresh_token")
            app.state.token_expires_in = token_data.get("expires_in")
            
            return {
                "status": "success",
                "message": "Successfully authenticated with Nest API",
                "access_token": "****" + (app.state.access_token[-4:] if app.state.access_token else ""),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in"),
                "scope": token_data.get("scope"),
                "refresh_token": "****" if "refresh_token" in token_data else None
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to complete OAuth flow: {str(e)}", "error": "oauth_error"}

@tool(name="refresh_access_token", description="Refresh OAuth 2.0 access token", parameters={"force": {"type": "boolean", "description": "Force refresh even if token not expired", "default": False}}, examples=["refresh_access_token()", "refresh_access_token(force=True)"])
async def refresh_access_token(force: bool = False) -> Dict[str, Any]:
    """Refresh OAuth 2.0 access token using refresh token."""
    from ..server import app
    
    if not hasattr(app.state, 'refresh_token') or not app.state.refresh_token:
        return {"status": "error", "message": "No refresh token available", "error": "no_refresh_token"}
    
    if not force and not getattr(app.state, 'token_expires_in', 0) < 300:  # 5 minutes
        return {"status": "success", "message": "Token not expired, refresh not needed"}
    
    try:
        token_url = "https://www.googleapis.com/oauth2/v4/token"
        data = {
            "client_id": app.state.config.nest_client_id,
            "client_secret": app.state.config.nest_client_secret,
            "refresh_token": app.state.refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with app.state.http_session.post(token_url, data=data) as response:
            token_data = await response.json()
            
            if response.status != 200:
                return {
                    "status": "error",
                    "message": "Failed to refresh access token",
                    "error": token_data.get("error"),
                    "error_description": token_data.get("error_description")
                }
            
            app.state.access_token = token_data["access_token"]
            app.state.token_expires_in = token_data.get("expires_in")
            
            return {
                "status": "success",
                "message": "Access token refreshed",
                "access_token": "****" + (app.state.access_token[-4:] if app.state.access_token else ""),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in"),
                "scope": token_data.get("scope")
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to refresh access token: {str(e)}", "error": "refresh_failed"}
