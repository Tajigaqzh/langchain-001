from __future__ import annotations

from app.agents import list_supported_models
from app.memory import build_thread_config


def get_model_entry(model_name: str):
    """Return the supported model entry for a CLI model name."""
    normalized_name = model_name.strip().lower()
    for entry in list_supported_models():
        if entry.name == normalized_name:
            return entry
    raise ValueError(f"Unsupported model: {model_name}")


def build_model_profile(
    model_name: str,
    reasoning_level: str,
    thread_id: str,
    memory_label: str,
) -> dict[str, object]:
    """Build structured model metadata for local logs and LangSmith traces."""
    entry = get_model_entry(model_name)
    return {
        "model": entry.name,
        "provider": entry.provider,
        "reasoning_effort": reasoning_level if entry.provider == "gpt" else None,
        "description": entry.description,
        "thread_id": thread_id,
        "memory_backend": memory_label,
    }


def build_agent_config(
    thread_id: str,
    model_profile: dict[str, object],
) -> dict[str, object]:
    """Build LangGraph config with memory routing and trace metadata."""
    config = build_thread_config(thread_id)
    model_name = str(model_profile["model"])
    provider = str(model_profile["provider"])
    memory_backend = str(model_profile["memory_backend"]).split(" ", maxsplit=1)[0]
    config["tags"] = [
        "cli-agent",
        f"model:{model_name}",
        f"provider:{provider}",
        f"memory:{memory_backend}",
    ]
    config["metadata"] = {"model_profile": model_profile}
    return config
