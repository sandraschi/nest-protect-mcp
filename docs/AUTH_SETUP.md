# Nest Protect auth: getting the API key / refresh token

Auth for the Nest (Smart Device Management) API is a few steps and easy to get wrong. This doc is the short, tricksy-bit reference.

## Why it's tricksy

1. **Google Cloud** – You need a project, enable one specific API, and create **OAuth 2.0 Desktop** credentials (not an API key).
2. **Refresh token, not API key** – The SDM API uses OAuth. You get a **refresh token** once (browser flow); the server then gets short-lived access tokens from it.
3. **No built-in `nest_protect_mcp.auth`** – The README mentions `python -m nest_protect_mcp.auth`; that module does not exist. Use the script below or the MCP tools `initiate_oauth_flow` / `handle_oauth_callback` with something listening on the redirect URI.

## Minimal steps

### 1. Google Cloud

- [Google Cloud Console](https://console.cloud.google.com/) → create or select a project.
- **APIs & Services → Library** → search **Smart Device Management API** → Enable.
- **APIs & Services → OAuth consent screen**:
  - User type: **External**.
  - App name, support email, developer email.
  - **Scopes**: Add `https://www.googleapis.com/auth/sdm.service`.
  - **Test users**: Add your Google account (the one that has Nest Protect in Google Home).
- **APIs & Services → Credentials** → **Create credentials** → **OAuth client ID**:
  - Application type: **Desktop app**.
  - Name e.g. "Nest Protect MCP".
  - Download the JSON (e.g. `client_secret_*.json`) and keep it safe.

### 2. Get the refresh token

From the repo root (where you have the client secret JSON):

```powershell
# Optional: create venv and install
uv run pip install google-auth-oauthlib

# Run the script (opens browser; after login you get the token in the terminal)
uv run python scripts/get_nest_refresh_token.py
```

Or with a specific client secret file:

```powershell
uv run python scripts/get_nest_refresh_token.py --client-secret path\to\client_secret_XXXX.json
```

The script starts a temporary local server on port **8080**, opens the browser, and after you sign in and approve, prints the **refresh token**. Copy it.

### 3. Env vars the server actually uses

The **web backend** and **MCP tools** that call the Nest API read credentials from the **environment** (and optionally `.env` in the project root). Use these names:

| Env var              | Meaning                          |
|----------------------|----------------------------------|
| `NEST_CLIENT_ID`     | From OAuth client JSON / Console |
| `NEST_CLIENT_SECRET` | From OAuth client JSON           |
| `NEST_PROJECT_ID`    | Google Cloud project ID          |
| `NEST_REFRESH_TOKEN` | From the script above            |

Create a `.env` in the repo root (do not commit it):

```bash
NEST_CLIENT_ID=xxxx.apps.googleusercontent.com
NEST_CLIENT_SECRET=xxxx
NEST_PROJECT_ID=your-project-id
NEST_REFRESH_TOKEN=1//xxxx
```

**Note:** `ProtectConfig` in the codebase uses prefix `NEST_PROTECT_` (e.g. `NEST_PROTECT_REFRESH_TOKEN`). The tools and server that talk to the Nest API are wired to the **`NEST_*`** set above; use those for this server.

### 4. Web backend (web_sota)

When you run `web_sota\start.ps1`, the FastAPI backend is started with `uvicorn nest_protect_mcp.server:app`. The server loads `.env` from the **project root** (parent of `web_sota`) and initializes Nest credentials and the refresh token so `/api/v1/devices` and `/api/v1/status` work. If you see "Authentication required" or no devices, check:

- `.env` is in the repo root with all four variables.
- The refresh token is from the script (or from an OAuth flow that uses the same client ID/secret and scope).

## Troubleshooting

- **invalid_client** – Wrong client ID/secret or they’re swapped; re-check the JSON and env.
- **access_denied** – Consent screen: add your account as a test user; use the account that owns the Nest Protects in Google Home.
- **invalid_scope** – Scope must be exactly `https://www.googleapis.com/auth/sdm.service`.
- **No refresh token in script output** – For Desktop apps, the first run of the flow usually returns a refresh token; if you already authorized the app before, revoke access for the app in your Google account and run the script again.
- **No devices** – Same Google account must have Nest Protect devices in Google Home; allow a few minutes after linking.

## References

- Full flow and device types: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- README: [../README.md](../README.md)
