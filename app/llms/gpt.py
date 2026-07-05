from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings
from app.llms.factory import ChatModelFactory, ChatModelSpec, ModelProvider


def build_gpt_llm(settings: Settings) -> BaseChatModel:
    """Create an OpenAI-compatible GPT chat model from project settings."""
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.OPENAI,
            model=settings.gpt_model,
            api_key=settings.gpt_api_key,
            base_url=settings.gpt_base_url,
            temperature=settings.temperature,
            model_kwargs=settings.gpt_model_kwargs,
        )
    )
