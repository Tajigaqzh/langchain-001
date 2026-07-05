from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings
from app.llms.client import BaseChatModelClient
from app.llms.factory import ChatModelFactory, ChatModelSpec, ModelProvider


def build_deepseek_llm(settings: Settings) -> BaseChatModel:
    """Create a DeepSeek chat model from project settings."""
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.OPENAI,
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=settings.temperature,
            model_kwargs=settings.deepseek_model_kwargs,
        )
    )


class DeepSeekChatClient(BaseChatModelClient):
    """Project DeepSeek client with shared invoke and stream methods."""

    def _build_llm(self) -> BaseChatModel:
        """Build the configured DeepSeek model instance."""
        return build_deepseek_llm(self.settings)
