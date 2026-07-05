from __future__ import annotations

from dataclasses import replace
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings
from app.llms.client import BaseChatModelClient
from app.llms.factory import ChatModelFactory, ChatModelSpec, ModelProvider


def normalize_reasoning_effort(reasoning_effort: str | None) -> str | None:
    """Normalize CLI reasoning aliases to supported GPT reasoning effort values."""
    if reasoning_effort is None:
        return None
    normalized = reasoning_effort.strip().lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    if normalized in {"extra_high", "extra-high", "extra high"}:
        return "high"
    raise ValueError(f"Unsupported reasoning effort: {reasoning_effort}")


def build_gpt_llm(
    settings: Settings,
    model_name: str | None = None,
    reasoning_effort: str | None = None,
) -> BaseChatModel:
    """Create an OpenAI-compatible GPT chat model from project settings."""
    effective_settings = replace(settings, gpt_model=model_name) if model_name else settings
    model_kwargs: dict[str, Any] = dict(effective_settings.gpt_model_kwargs or {})
    normalized_reasoning = normalize_reasoning_effort(reasoning_effort)
    if normalized_reasoning is not None:
        model_kwargs["reasoning_effort"] = normalized_reasoning
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.OPENAI,
            model=effective_settings.gpt_model,
            api_key=effective_settings.gpt_api_key,
            base_url=effective_settings.gpt_base_url,
            temperature=effective_settings.temperature,
            model_kwargs=model_kwargs or None,
        )
    )


class GPTChatClient(BaseChatModelClient):
    """Project GPT client with shared invoke and stream methods."""

    def _build_llm(self) -> BaseChatModel:
        """Build the configured GPT model instance."""
        return build_gpt_llm(self.settings)
