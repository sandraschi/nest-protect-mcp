# nest-protect-mcp — Copilot instructions

FastMCP server (`src/nest_protect_mcp/fastmcp_server.py`, 32 tools) for Google
Nest Protect devices. Tool names: `list_nest_devices`, `get_device_health`,
`hush_active_alarm`, `run_safety_test`, `start_google_oauth`, ... (see manifest).

- Before starting work: read `pyproject.toml` + `fastmcp_server.py`; auth via `just auth`.
- Never add `allow_origins=["*"]` (fleet CORS standard: explicit origins + regex).
- Returns: `ToolResult(content=...)`; keep Pydantic v2 (`.model_dump()`, never `.dict()`).
- Verify: `uv run ruff check src/` + `uv run pytest tests/ -q`.
