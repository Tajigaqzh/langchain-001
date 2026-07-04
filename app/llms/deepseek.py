from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import Settings


def build_deepseek_llm(settings: Settings) -> ChatOpenAI:
    """Create a DeepSeek chat model from project settings."""
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=settings.temperature,
    )
