#!/usr/bin/env python3
"""
Obtain a Nest (Smart Device Management) OAuth refresh token.

Run from repo root. Requires client_secret_*.json from Google Cloud Console
(OAuth 2.0 Desktop client). Opens browser; after sign-in the refresh token
is printed. Put it in .env as NEST_REFRESH_TOKEN.

Usage:
  python scripts/get_nest_refresh_token.py
  python scripts/get_nest_refresh_token.py --client-secret path/to/client_secret_XXX.json
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

# Default port for local redirect (must match OAuth client redirect URI)
REDIRECT_PORT = 8080
SCOPE = "https://www.googleapis.com/auth/sdm.service"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Get Nest SDM OAuth refresh token (for NEST_REFRESH_TOKEN)"
    )
    parser.add_argument(
        "--client-secret",
        type=str,
        default=None,
        help="Path to client_secret_*.json from Google Cloud Console",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=REDIRECT_PORT,
        help=f"Port for local redirect (default {REDIRECT_PORT})",
    )
    args = parser.parse_args()

    client_secret_path = args.client_secret
    if not client_secret_path:
        repo_root = Path(__file__).resolve().parent.parent
        os.chdir(repo_root)
        candidates = glob.glob("client_secret_*.json")
        if not candidates:
            print(
                "No client_secret_*.json found. Download from Google Cloud Console:"
            )
            print(
                "  APIs & Services -> Credentials -> Create OAuth client ID (Desktop app)"
            )
            print(
                "  Save the JSON as client_secret_XXXX.json in the repo root."
            )
            sys.exit(1)
        client_secret_path = candidates[0]

    path = Path(client_secret_path)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install: pip install google-auth-oauthlib")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        creds_data = json.load(f)

    if "installed" in creds_data:
        client_config = creds_data
    else:
        client_config = {
            "installed": {
                "client_id": creds_data.get("client_id"),
                "client_secret": creds_data.get("client_secret"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": creds_data.get(
                    "auth_provider_x509_cert_url",
                    "https://www.googleapis.com/oauth2/v1/certs",
                ),
                "redirect_uris": [
                    "urn:ietf:wg:oauth:2.0:oob",
                    "http://localhost",
                    f"http://localhost:{args.port}",
                ],
            }
        }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=[SCOPE])
    print(f"Opening browser for sign-in (redirect port {args.port})...")
    creds = flow.run_local_server(port=args.port)

    if not getattr(creds, "refresh_token", None):
        print(
            "No refresh_token in response. Revoke app access for your Google account"
        )
        print("and run this script again to get a new consent.")
        sys.exit(1)

    print("Authentication successful.")
    print("")
    print("Add to .env in the repo root:")
    print(f"  NEST_REFRESH_TOKEN={creds.refresh_token}")
    print("")
    print("Keep this token secret; do not commit .env.")


if __name__ == "__main__":
    main()
