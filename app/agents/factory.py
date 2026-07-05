from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel

from app.tools import get_tools


def build_chat_agent(llm: BaseChatModel, system_prompt: str):
    """Create a project agent from a configured chat model and system prompt."""
    return create_agent(
        model=llm,
        tools=get_tools(),
        system_prompt=system_prompt,
    )
