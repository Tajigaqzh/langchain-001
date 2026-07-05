from __future__ import annotations

import json
import sys

import pytest

from app.config import Settings
from app.tools import get_tools
from app.tools.mcp import (
    McpToolLoadError,
    load_mcp_server_config,
    load_mcp_tools,
)


def test_load_mcp_server_config_accepts_mcp_servers_shape(tmp_path) -> None:
    """Verify MCP config loading accepts the common mcpServers JSON shape."""
    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    settings = Settings(mcp_config_path=str(config_path))

    assert load_mcp_server_config(settings) == {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            "transport": "stdio",
        }
    }


def test_load_mcp_tools_returns_empty_when_disabled() -> None:
    """Verify MCP loading is a no-op without AGENT_MCP_CONFIG_PATH."""
    assert load_mcp_tools(Settings(mcp_config_path="")) == []


def test_load_mcp_tools_reports_missing_optional_dependency(tmp_path, monkeypatch) -> None:
    """Verify configured MCP fails with a clear optional dependency message."""
    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        json.dumps({"test": {"command": "python", "args": ["server.py"]}}),
        encoding="utf-8",
    )
    monkeypatch.setitem(sys.modules, "langchain_mcp_adapters", None)
    monkeypatch.setitem(sys.modules, "langchain_mcp_adapters.client", None)

    with pytest.raises(McpToolLoadError, match="langchain-mcp-adapters is not installed"):
        load_mcp_tools(Settings(mcp_config_path=str(config_path)))


def test_get_tools_appends_mcp_tools(monkeypatch) -> None:
    """Verify configured MCP tools are appended to the local tool list."""
    mcp_tool = object()
    monkeypatch.setattr("app.tools.load_mcp_tools", lambda settings: [mcp_tool])

    tools = get_tools(Settings(mcp_config_path="mcp.json"))

    assert mcp_tool in tools
