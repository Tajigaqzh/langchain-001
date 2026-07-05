from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_CLAUDE_BASE_URL = "https://api.anthropic.com"
DEFAULT_CLAUDE_MODEL = "claude-opus-4-6"
DEFAULT_GPT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_GPT_MODEL = "gpt-5.5"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_AGENT_DEFAULT_MODEL = "gpt-5.5"
DEFAULT_AGENT_THREAD_ID = "default"
DEFAULT_MEMORY_BACKEND = "sqlite"
DEFAULT_MEMORY_PATH = ".data/agent_memory.sqlite"
DEFAULT_MODEL_RETRY_ATTEMPTS = 10
DEFAULT_MODEL_RETRY_DELAY = 3.0
DEFAULT_SQLITE_CACHE_DAYS = 10
DEFAULT_STREAM_CHUNK_SIZE = 4
DEFAULT_STREAM_DELAY = 0.015
DEFAULT_MCP_CONFIG_PATH = ""
TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = ""
    deepseek_base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    deepseek_model: str = DEFAULT_DEEPSEEK_MODEL
    deepseek_model_kwargs: dict[str, Any] | None = None
    claude_api_key: str = ""
    claude_base_url: str = DEFAULT_CLAUDE_BASE_URL
    claude_model: str = DEFAULT_CLAUDE_MODEL
    claude_model_kwargs: dict[str, Any] | None = None
    gpt_api_key: str = ""
    gpt_base_url: str = DEFAULT_GPT_BASE_URL
    gpt_model: str = DEFAULT_GPT_MODEL
    gpt_model_kwargs: dict[str, Any] | None = None
    temperature: float = DEFAULT_TEMPERATURE
    agent_default_model: str = DEFAULT_AGENT_DEFAULT_MODEL
    agent_thread_id: str = DEFAULT_AGENT_THREAD_ID
    memory_backend: str = DEFAULT_MEMORY_BACKEND
    memory_path: str = DEFAULT_MEMORY_PATH
    model_retry_attempts: int = DEFAULT_MODEL_RETRY_ATTEMPTS
    model_retry_delay: float = DEFAULT_MODEL_RETRY_DELAY
    sqlite_cache_days: int = DEFAULT_SQLITE_CACHE_DAYS
    agent_stream: bool = False
    agent_stream_chunk_size: int = DEFAULT_STREAM_CHUNK_SIZE
    agent_stream_delay: float = DEFAULT_STREAM_DELAY
    mcp_config_path: str = DEFAULT_MCP_CONFIG_PATH


def load_settings() -> Settings:
    """Load project settings from the root .env file and process environment."""
    load_dotenv(ENV_FILE)

    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_base_url=os.getenv(
            "DEEPSEEK_API_BASE",
            os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL),
        ),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
        deepseek_model_kwargs=load_json_env("DEEPSEEK_MODEL_KWARGS"),
        claude_api_key=os.getenv("CLAUDE_API_KEY", "").strip(),
        claude_base_url=os.getenv("CLAUDE_API_BASE", DEFAULT_CLAUDE_BASE_URL),
        claude_model=os.getenv("CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL),
        claude_model_kwargs=load_json_env("CLAUDE_MODEL_KWARGS"),
        gpt_api_key=os.getenv("GPT_API_KEY", "").strip(),
        gpt_base_url=os.getenv("GPT_API_BASE", DEFAULT_GPT_BASE_URL),
        gpt_model=os.getenv("GPT_MODEL", DEFAULT_GPT_MODEL),
        gpt_model_kwargs=load_json_env("GPT_MODEL_KWARGS"),
        temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", DEFAULT_TEMPERATURE)),
        agent_default_model=os.getenv("AGENT_DEFAULT_MODEL", DEFAULT_AGENT_DEFAULT_MODEL).strip(),
        agent_thread_id=os.getenv("AGENT_THREAD_ID", DEFAULT_AGENT_THREAD_ID).strip(),
        memory_backend=os.getenv("AGENT_MEMORY_BACKEND", DEFAULT_MEMORY_BACKEND).strip(),
        memory_path=os.getenv("AGENT_MEMORY_PATH", DEFAULT_MEMORY_PATH).strip(),
        model_retry_attempts=load_int_env(
            "AGENT_MODEL_RETRY_ATTEMPTS",
            default=DEFAULT_MODEL_RETRY_ATTEMPTS,
            minimum=0,
        ),
        model_retry_delay=load_float_env(
            "AGENT_MODEL_RETRY_DELAY",
            default=DEFAULT_MODEL_RETRY_DELAY,
            minimum=0.0,
        ),
        sqlite_cache_days=load_int_env(
            "AGENT_SQLITE_CACHE_DAYS",
            default=DEFAULT_SQLITE_CACHE_DAYS,
            minimum=0,
        ),
        agent_stream=load_bool_env("AGENT_STREAM", default=False),
        agent_stream_chunk_size=load_int_env(
            "AGENT_STREAM_CHUNK_SIZE",
            default=DEFAULT_STREAM_CHUNK_SIZE,
            minimum=1,
        ),
        agent_stream_delay=load_float_env(
            "AGENT_STREAM_DELAY",
            default=DEFAULT_STREAM_DELAY,
            minimum=0.0,
        ),
        mcp_config_path=os.getenv("AGENT_MCP_CONFIG_PATH", DEFAULT_MCP_CONFIG_PATH).strip(),
    )


def load_bool_env(name: str, default: bool = False) -> bool:
    """Load a boolean environment variable using common truthy strings."""
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in TRUE_VALUES


def load_float_env(name: str, default: float, minimum: float | None = None) -> float:
    """Load a float environment variable with optional lower bound validation."""
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a valid number.") from exc
    if minimum is not None and parsed < minimum:
        raise RuntimeError(f"{name} must be greater than or equal to {minimum}.")
    return parsed


def load_int_env(name: str, default: int, minimum: int | None = None) -> int:
    """Load an integer environment variable with optional lower bound validation."""
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a valid integer.") from exc
    if minimum is not None and parsed < minimum:
        raise RuntimeError(f"{name} must be greater than or equal to {minimum}.")
    return parsed


def load_json_env(name: str) -> dict[str, Any] | None:
    """Load an optional JSON object from an environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        return None

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} must be a valid JSON object.") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError(f"{name} must be a JSON object.")

    return parsed
