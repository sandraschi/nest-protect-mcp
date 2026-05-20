#!/usr/bin/env python3
"""
Obtain a Nest (Smart Device Management) OAuth refresh token.

Uses **Partner Connections Manager** (PCM) — required for Nest Device Access —
not the generic Google accounts OAuth URL. Scope ``sdm.service`` appears on the
Google consent screen under Smart Device Management / home automation.

Run from repo root. Requires OAuth Desktop client JSON from Google Cloud Console.

Usage:
  python scripts/get_nest_refresh_token.py
  python scripts/get_nest_refresh_token.py --project-id YOUR_DEVICE_ACCESS_PROJECT_ID
  python scripts/get_nest_refresh_token.py --client-secret path/to/client_secret_XXX.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

# Repo src on path when run as script
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from nest_protect_mcp.constants import (  # noqa: E402
    GOOGLE_OAUTH_TOKEN_URL,
    NEST_SDM_OAUTH_SCOPE,
    partner_connections_auth_base,
)


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Captures ?code= from redirect once."""

    auth_code: str | None = None
    oauth_error: str | None = None

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if "error" in qs:
            _OAuthCallbackHandler.oauth_error = qs["error"][0]
        elif "code" in qs:
            _OAuthCallbackHandler.auth_code = qs["code"][0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        body = (
            "<html><body><p>You can close this tab and return to the terminal.</p></body></html>"
        )
        self.wfile.write(body.encode("utf-8"))
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def _exchange_code(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    data = urlencode(
        {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    req = Request(
        GOOGLE_OAUTH_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(err_body)
        except json.JSONDecodeError:
            return {"error": str(e), "error_description": err_body}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Get Nest SDM OAuth refresh token (PCM flow; NEST_SDM_OAUTH_SCOPE)"
    )
    parser.add_argument(
        "--client-secret",
        type=str,
        default=None,
        help="Path to client_secret_*.json from Google Cloud Console",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=os.getenv("NEST_PROJECT_ID", ""),
        help="Device Access project id (same as NEST_PROJECT_ID / SDM enterprise id)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("NEST_OAUTH_LOCAL_PORT", "8080")),
        help="Local redirect port (must match an authorized redirect URI for the client)",
    )
    parser.add_argument(
        "--scope",
        type=str,
        default=os.getenv("NEST_SDM_OAUTH_SCOPE", NEST_SDM_OAUTH_SCOPE),
        help="OAuth scope (default: SDM / home automation API)",
    )
    args = parser.parse_args()

    client_secret_path = args.client_secret
    if not client_secret_path:
        repo_root = Path(__file__).resolve().parent.parent
        os.chdir(repo_root)
        candidates = glob.glob("client_secret_*.json")
        if not candidates:
            print("No client_secret_*.json found. Download from Google Cloud Console:")
            print(
                "  APIs & Services -> Credentials -> Create OAuth client ID (Desktop app)"
            )
            print("  Save the JSON as client_secret_XXXX.json in the repo root.")
            sys.exit(1)
        client_secret_path = candidates[0]

    path = Path(client_secret_path)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    project_id = (args.project_id or "").strip()
    if not project_id:
        print(
            "Set --project-id or NEST_PROJECT_ID to your Google Nest **Device Access** "
            "project id (UUID from console.nest.google)."
        )
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        creds_data = json.load(f)

    if "installed" in creds_data:
        installed = creds_data["installed"]
    else:
        installed = creds_data

    client_id = installed.get("client_id")
    client_secret = installed.get("client_secret")
    if not client_id or not client_secret:
        print("client_id / client_secret missing in JSON")
        sys.exit(1)

    redirect_uri = f"http://127.0.0.1:{args.port}/callback"
    state = os.urandom(16).hex()

    auth_base = partner_connections_auth_base(project_id)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": args.scope.strip(),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{auth_base}?{urlencode(params)}"

    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.oauth_error = None

    httpd = HTTPServer(("127.0.0.1", args.port), _OAuthCallbackHandler)
    serve_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    serve_thread.start()

    print(f"PCM auth (scope: {params['scope']})")
    print(f"Opening browser — local callback {redirect_uri}")
    print("Add this exact URI to OAuth client Authorized redirect URIs in Google Cloud.")
    webbrowser.open(auth_url)

    for _ in range(300):
        if _OAuthCallbackHandler.auth_code or _OAuthCallbackHandler.oauth_error:
            break
        time.sleep(1)

    httpd.shutdown()
    serve_thread.join(timeout=5)

    if _OAuthCallbackHandler.oauth_error:
        print(f"OAuth error: {_OAuthCallbackHandler.oauth_error}")
        sys.exit(1)

    code = _OAuthCallbackHandler.auth_code
    if not code:
        print("Timed out waiting for authorization callback.")
        sys.exit(1)

    token_payload = _exchange_code(
        code=code,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    if token_payload.get("error"):
        print("Token exchange failed:", token_payload)
        sys.exit(1)

    refresh = token_payload.get("refresh_token")
    if not refresh:
        print(
            "No refresh_token in response. Revoke app access at "
            "https://myaccount.google.com/permissions and run again with prompt=consent."
        )
        sys.exit(1)

    print("Authentication successful.")
    print("")
    print("Add to .env in the repo root (example):")
    print("")
    print(f"NEST_CLIENT_ID={client_id}")
    print(f"NEST_CLIENT_SECRET={client_secret}")
    print(f"NEST_PROJECT_ID={project_id}")
    print(f"NEST_REFRESH_TOKEN={refresh}")
    print("")
    print("Keep this token secret; do not commit .env.")


if __name__ == "__main__":
    main()
