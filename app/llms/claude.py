from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings
from app.llms.factory import ChatModelFactory, ChatModelSpec, ModelProvider


def build_claude_llm(settings: Settings) -> BaseChatModel:
    """Create an Anthropic Claude chat model from project settings."""
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.ANTHROPIC,
            model=settings.claude_model,
            api_key=settings.claude_api_key,
            base_url=normalize_anthropic_base_url(settings.claude_base_url),
            temperature=settings.temperature,
            model_kwargs=settings.claude_model_kwargs,
        )
    )


def normalize_anthropic_base_url(base_url: str) -> str:
    """Return an Anthropic SDK base URL without a duplicated /v1 path."""
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized.removesuffix("/v1")
    return normalized
