# start.ps1 - Nest Protect MCP SOTA Startup
# 1. Clear port from zombies/squatters
# 2. Build and run

$PORT = 10753
Write-Host "--- Nest Protect MCP Startup ---" -ForegroundColor Cyan

# Clear port
Write-Host "Checking for port $PORT squatters..." -ForegroundColor Yellow
$netsat = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue
if ($netsat) {
    Write-Host "Found squatter on port $PORT. Terminating..." -ForegroundColor Red
    $netsat | ForEach-Object {
        $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "Stopping process $($p.Name) ($($p.Id))..."
            Stop-Process -Id $p.Id -Force
        }
    }
}

# Sync environment
Write-Host "Syncing environment with uv..." -ForegroundColor Yellow
uv sync --all-extras

# Start backend
Write-Host "Starting Nest Protect MCP server on port $PORT..." -ForegroundColor Green
# uv run python -m nest_protect_mcp.fastmcp_server --http --port $PORT
Start-Process "uv" -ArgumentList "run", "python", "-m", "nest_protect_mcp.fastmcp_server", "--http", "--port", "$PORT" -NoNewWindow
