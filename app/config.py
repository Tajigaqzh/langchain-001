from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    temperature: float = 0.2


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
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", Settings.deepseek_base_url),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", Settings.deepseek_model),
        temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", Settings.temperature)),
    )
