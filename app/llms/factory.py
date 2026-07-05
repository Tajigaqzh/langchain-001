from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr


class ModelProvider(str, Enum):
    """Supported LangChain chat model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass(frozen=True)
class ChatModelSpec:
    """Configuration needed to initialize a chat model."""

    provider: ModelProvider
    model: str
    api_key: str
    base_url: str
    temperature: float
    model_kwargs: dict[str, Any] | None = None


class ChatModelFactory:
    """Factory for creating chat models through LangChain init_chat_model."""

    @staticmethod
    def create(spec: ChatModelSpec) -> BaseChatModel:
        """Create a chat model from a provider-specific model spec."""
        if not spec.api_key:
            raise RuntimeError(f"Missing API key for {spec.provider.value} model.")

        custom_fields = spec.model_kwargs or {}

        return init_chat_model(
            model=spec.model,
            model_provider=spec.provider.value,
            api_key=SecretStr(spec.api_key),
            base_url=spec.base_url,
            temperature=spec.temperature,
            **custom_fields,
        )
