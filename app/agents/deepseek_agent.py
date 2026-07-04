from __future__ import annotations

from langchain.agents import create_agent

from app.config import load_settings
from app.llms import build_deepseek_llm
from app.tools import get_tools

SYSTEM_PROMPT = """
You are a practical AI assistant powered by DeepSeek.
Answer in the user's language. Use tools when they help you calculate,
inspect time, or produce a more reliable answer.
""".strip()


def build_agent():
    """Create the project DeepSeek agent with configured tools."""
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    return create_agent(
        model=llm,
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
    )
