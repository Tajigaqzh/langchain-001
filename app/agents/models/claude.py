from __future__ import annotations

from app.agents.factory import build_chat_agent
from app.config import Settings, load_settings
from app.llms import build_claude_llm

SYSTEM_PROMPT = """
You are a practical AI assistant powered by Claude.
Answer in the user's language. Use tools when they help you calculate,
inspect time, or produce a more reliable answer.
If a tool reports that a path is outside the project root, ask the user for
approval before retrying with allow_outside_project=True.
""".strip()


def build_claude_agent(settings: Settings | None = None):
    """Create the project Claude agent with configured tools."""
    effective_settings = settings or load_settings()
    llm = build_claude_llm(effective_settings)
    return build_chat_agent(llm, SYSTEM_PROMPT)
