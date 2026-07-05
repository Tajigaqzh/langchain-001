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


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
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


def load_settings() -> Settings:
    """Load project settings from the root .env file and process environment."""
    load_dotenv(ENV_FILE)

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Missing DEEPSEEK_API_KEY. Set it in your shell or create a local .env file."
        )

    return Settings(
        deepseek_api_key=api_key,
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
    )


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
