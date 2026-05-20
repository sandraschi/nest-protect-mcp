"""CLI entry compatibility with FastMCP ``__main__``."""

from unittest.mock import patch

import pytest


def test_cli_main_delegates_to_package_main():
    calls = []

    def fake_main():
        calls.append(1)

    with patch("nest_protect_mcp.__main__.main", fake_main):
        from nest_protect_mcp.cli import main

        main()

    assert calls == [1]


def test_legacy_server_init_raises():
    import asyncio

    from nest_protect_mcp.cli import NestProtectCLI

    cli = NestProtectCLI()

    async def run():
        await cli._init_server(None)

    with pytest.raises(RuntimeError, match="python -m nest_protect_mcp"):
        asyncio.run(run())
