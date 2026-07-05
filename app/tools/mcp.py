from __future__ import annotations

import asyncio
import inspect
import json
from importlib import import_module
from collections.abc import Awaitable
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT, Settings


class McpToolLoadError(RuntimeError):
    """Raised when configured MCP tools cannot be loaded."""


def resolve_mcp_config_path(config_path: str) -> Path:
    """Resolve an MCP config path relative to the project root."""
    path = Path(config_path).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_mcp_server_config(settings: Settings) -> dict[str, Any]:
    """Load MCP server definitions from the configured JSON file."""
    if not settings.mcp_config_path:
        return {}

    config_path = resolve_mcp_config_path(settings.mcp_config_path)
    if not config_path.exists():
        raise McpToolLoadError(f"MCP config file does not exist: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file_obj:
            raw_config = json.load(file_obj)
    except json.JSONDecodeError as exc:
        raise McpToolLoadError(f"MCP config file must be valid JSON: {config_path}") from exc

    if not isinstance(raw_config, dict):
        raise McpToolLoadError("MCP config file must contain a JSON object.")

    server_config = raw_config.get("mcpServers", raw_config.get("servers", raw_config))
    if not isinstance(server_config, dict):
        raise McpToolLoadError("MCP config must contain a server mapping.")

    return {
        name: normalize_mcp_server_entry(name, entry)
        for name, entry in server_config.items()
    }


def normalize_mcp_server_entry(name: str, entry: Any) -> dict[str, Any]:
    """Normalize one MCP server entry for langchain-mcp-adapters."""
    if not isinstance(name, str) or not name.strip():
        raise McpToolLoadError("MCP server names must be non-empty strings.")
    if not isinstance(entry, dict):
        raise McpToolLoadError(f"MCP server '{name}' must be a JSON object.")

    normalized = dict(entry)
    if "transport" not in normalized and "command" in normalized:
        normalized["transport"] = "stdio"
    return normalized


def load_mcp_tools(settings: Settings) -> list[Any]:
    """Load tools from configured MCP servers, if MCP is enabled."""
    server_config = load_mcp_server_config(settings)
    if not server_config:
        return []

    try:
        client_module = import_module("langchain_mcp_adapters.client")
    except ModuleNotFoundError as exc:
        raise McpToolLoadError(
            "MCP is configured but langchain-mcp-adapters is not installed. "
            "Install it with pip install langchain-mcp-adapters, or remove "
            "AGENT_MCP_CONFIG_PATH from .env."
        ) from exc

    mcp_client_class = getattr(client_module, "MultiServerMCPClient")
    client = mcp_client_class(server_config)
    tools = client.get_tools()
    if inspect.isawaitable(tools):
        tools = run_awaitable(tools)
    return list(tools)


def run_awaitable(awaitable: Awaitable[Any]) -> Any:
    """Run an async MCP adapter call from the synchronous CLI startup path."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    raise McpToolLoadError(
        "MCP tools cannot be loaded while an event loop is already running."
    )
