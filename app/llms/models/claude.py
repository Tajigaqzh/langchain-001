from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings
from app.llms.client import BaseChatModelClient
from app.llms.factory import ChatModelFactory, ChatModelSpec, ModelProvider


def build_claude_llm(settings: Settings) -> BaseChatModel:
    """Create an Anthropic Claude chat model from project settings."""
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.ANTHROPIC,
            model=settings.claude_model,
            api_key=settings.claude_api_key,
            base_url=settings.claude_base_url,
            temperature=settings.temperature,
            model_kwargs=settings.claude_model_kwargs,
        )
    )


class ClaudeChatClient(BaseChatModelClient):
    """Project Claude client with shared invoke and stream methods."""

    def _build_llm(self) -> BaseChatModel:
        """Build the configured Claude model instance."""
        return build_claude_llm(self.settings)
