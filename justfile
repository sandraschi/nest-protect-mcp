set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# â”€â”€ Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Open the interactive recipe dashboard in the browser
default:
    @just --list


# Synchronize deps, pre-commit hooks, and web frontend
bootstrap:
    uv sync --extra dev --group dev
    uv run pre-commit install
    Set-Location webapp/frontend; npm ci; if ($LASTEXITCODE -ne 0) { npm install }
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green
# â”€â”€ Quality â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

# â”€â”€ Hardening â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

# â”€â”€ Auth (Nest Device Access / PCM) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Partner Connections CLI: opens browser; prints full NEST_* .env lines. Uses env NEST_PROJECT_ID if set â€” or pass flags, e.g. just auth --project-id YOUR_UUID
auth *ARGS:
    Set-Location '{{justfile_directory()}}'
    uv run python scripts/get_nest_refresh_token.py {{ARGS}}

# Open Google Cloud â†’ Credentials (add authorized redirect URIs)
auth-console:
    Start-Process 'https://console.cloud.google.com/apis/credentials'

# Print redirect URIs to register for CLI vs web onboarding wizard
auth-help:
    Write-Host ''
    Write-Host 'OAuth Desktop client â€” Authorized redirect URIs:' -ForegroundColor Cyan
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

e2e:
    powershell.exe -NoProfile -NoProfile -ExecutionPolicy Bypass -File "D:\Dev\repos\mcp-central-docs\scripts\playwright-audit.ps1" -RepoPath "{{justfile_directory()}}"

# Lint and format code
# Fix linting and formatting issues
# Start the web dashboard (Vite)
web:
    cd web_sota; npm run dev

# Comprehensive dev setup (sync, lint, test)
dev: sync lint test

