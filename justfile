set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ../mcp-central-docs/scripts/just-dashboard.ps1 -Path .

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# Install dependencies and sync environment
sync:
    uv sync

# Run the MCP server in stdio mode
run:
    uv run python -m nest_protect_mcp.fastmcp_server

# Run the MCP server in HTTP mode (for web_sota)
serve port="10753":
    @uv run python -m nest_protect_mcp.fastmcp_server --http --port {{port}}

# ── Auth (Nest Device Access / PCM) ───────────────────────────────────────────

# Partner Connections CLI: opens browser; prints full NEST_* .env lines. Uses env NEST_PROJECT_ID if set — or pass flags, e.g. just auth --project-id YOUR_UUID
auth *ARGS:
    Set-Location '{{justfile_directory()}}'
    uv run python scripts/get_nest_refresh_token.py {{ARGS}}

# Open Google Cloud → Credentials (add authorized redirect URIs)
auth-console:
    Start-Process 'https://console.cloud.google.com/apis/credentials'

# Print redirect URIs to register for CLI vs web onboarding wizard
auth-help:
    Write-Host ''
    Write-Host 'OAuth Desktop client — Authorized redirect URIs:' -ForegroundColor Cyan
    Write-Host ''
    Write-Host '  CLI (just auth; default callback port 8080):'
    Write-Host '    http://127.0.0.1:8080/callback'
    Write-Host ''
    Write-Host '  Web wizard (/onboarding):'
    Write-Host '    http://127.0.0.1:10753/api/v1/auth/callback'
    Write-Host ''

# Run tests
test:
    uv run pytest

# Lint and format code
# Fix linting and formatting issues
# Start the web dashboard (Vite)
web:
    cd web_sota; npm run dev

# Comprehensive dev setup (sync, lint, test)
dev: sync lint test
