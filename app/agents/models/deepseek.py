from __future__ import annotations

from typing import Any

from app.agents.factory import build_chat_agent
from app.config import Settings, load_settings
from app.llms import build_deepseek_llm

SYSTEM_PROMPT = """
You are a practical AI assistant powered by DeepSeek.
Answer in the user's language. Use tools when they help you calculate,
inspect time, or produce a more reliable answer.
If a tool reports that a path is outside the project root, ask the user for
approval before retrying with allow_outside_project=True.
""".strip()


def build_deepseek_agent(
    settings: Settings | None = None,
    checkpointer: Any | None = None,
):
    """Create the project DeepSeek agent with configured tools."""
    effective_settings = settings or load_settings()
    llm = build_deepseek_llm(effective_settings)
    return build_chat_agent(llm, SYSTEM_PROMPT, checkpointer=checkpointer)


def build_agent(checkpointer: Any | None = None):
    """Create the default project agent."""
    return build_deepseek_agent(checkpointer=checkpointer)
