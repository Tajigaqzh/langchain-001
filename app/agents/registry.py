from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agents.models.claude import build_claude_agent
from app.agents.models.deepseek import build_agent, build_deepseek_agent
from app.agents.models.gpt import build_gpt_agent
from app.config import Settings


@dataclass(frozen=True)
class ModelEntry:
    """A selectable CLI model entry."""

    name: str
    provider: str
    configured: callable
    builder: callable
    description: str


MODEL_ENTRIES: list[ModelEntry] = [
    ModelEntry(
        name="deepseek",
        provider="deepseek",
        configured=lambda settings: bool(settings.deepseek_api_key),
        builder=lambda settings, reasoning_effort=None, checkpointer=None: build_deepseek_agent(
            settings=settings,
            checkpointer=checkpointer,
        ),
        description="DeepSeek default model from your configuration.",
    ),
    ModelEntry(
        name="claude",
        provider="claude",
        configured=lambda settings: bool(settings.claude_api_key),
        builder=lambda settings, reasoning_effort=None, checkpointer=None: build_claude_agent(
            settings=settings,
            checkpointer=checkpointer,
        ),
        description="Claude default model from your configuration.",
    ),
    ModelEntry(
        name="gpt-5.5",
        provider="gpt",
        configured=lambda settings: bool(settings.gpt_api_key),
        builder=lambda settings, reasoning_effort=None, checkpointer=None: build_gpt_agent(
            settings=settings,
            model_name="gpt-5.5",
            reasoning_effort=reasoning_effort,
            checkpointer=checkpointer,
        ),
        description="Frontier model for complex coding, research, and real-world work.",
    ),
    ModelEntry(
        name="gpt-5.4",
        provider="gpt",
        configured=lambda settings: bool(settings.gpt_api_key),
        builder=lambda settings, reasoning_effort=None, checkpointer=None: build_gpt_agent(
            settings=settings,
            model_name="gpt-5.4",
            reasoning_effort=reasoning_effort,
            checkpointer=checkpointer,
        ),
        description="Strong model for everyday coding.",
    ),
    ModelEntry(
        name="gpt-5.4-mini",
        provider="gpt",
        configured=lambda settings: bool(settings.gpt_api_key),
        builder=lambda settings, reasoning_effort=None, checkpointer=None: build_gpt_agent(
            settings=settings,
            model_name="gpt-5.4-mini",
            reasoning_effort=reasoning_effort,
            checkpointer=checkpointer,
        ),
        description="Small, fast, and cost-efficient model for simpler coding tasks.",
    ),
    ModelEntry(
        name="gpt-5.3-codex",
        provider="gpt",
        configured=lambda settings: bool(settings.gpt_api_key),
        builder=lambda settings, reasoning_effort=None, checkpointer=None: build_gpt_agent(
            settings=settings,
            model_name="gpt-5.3-codex",
            reasoning_effort=reasoning_effort,
            checkpointer=checkpointer,
        ),
        description="Coding-optimized model.",
    ),
    ModelEntry(
        name="gpt-5.2",
        provider="gpt",
        configured=lambda settings: bool(settings.gpt_api_key),
        builder=lambda settings, reasoning_effort=None, checkpointer=None: build_gpt_agent(
            settings=settings,
            model_name="gpt-5.2",
            reasoning_effort=reasoning_effort,
            checkpointer=checkpointer,
        ),
        description="General-purpose GPT-5.2 model.",
    ),
]

MODEL_ENTRIES_BY_NAME = {entry.name: entry for entry in MODEL_ENTRIES}
DEFAULT_MODEL_NAME = "deepseek"


def build_agent_for_model(
    model_name: str,
    settings: Settings,
    reasoning_effort: str | None = None,
    checkpointer: Any | None = None,
):
    """Build an agent for a supported model name."""
    normalized_name = model_name.strip().lower()
    entry = MODEL_ENTRIES_BY_NAME.get(normalized_name)
    if entry is None:
        raise ValueError(f"Unsupported model: {model_name}")
    return entry.builder(
        settings,
        reasoning_effort=reasoning_effort,
        checkpointer=checkpointer,
    )


def get_available_models(settings: Settings) -> dict[str, bool]:
    """Return supported model names and whether they are configured."""
    return {entry.name: entry.configured(settings) for entry in MODEL_ENTRIES}


def list_supported_models() -> list[ModelEntry]:
    """Return supported model entries in display order."""
    return MODEL_ENTRIES


def is_gpt_model(model_name: str) -> bool:
    """Return whether a CLI model entry uses the GPT provider."""
    entry = MODEL_ENTRIES_BY_NAME.get(model_name.strip().lower())
    return bool(entry and entry.provider == "gpt")
