from __future__ import annotations

from app.cli.model_profile import build_agent_config, build_model_profile


def test_build_model_profile_for_gpt_includes_reasoning() -> None:
    """Verify GPT model profile records provider, reasoning, and memory context."""
    profile = build_model_profile(
        "gpt-5.5",
        "high",
        "user-123",
        "sqlite (.data/agent_memory.sqlite)",
    )

    assert profile["model"] == "gpt-5.5"
    assert profile["provider"] == "gpt"
    assert profile["reasoning_effort"] == "high"
    assert profile["thread_id"] == "user-123"
    assert profile["memory_backend"] == "sqlite (.data/agent_memory.sqlite)"


def test_build_agent_config_logs_model_profile_metadata() -> None:
    """Verify LangGraph config carries model profile data for LangSmith traces."""
    profile = build_model_profile(
        "deepseek",
        "medium",
        "default",
        "memory",
    )

    config = build_agent_config("default", profile)

    assert config["configurable"] == {"thread_id": "default"}
    assert config["metadata"] == {"model_profile": profile}
    assert config["tags"] == [
        "cli-agent",
        "model:deepseek",
        "provider:deepseek",
        "memory:memory",
    ]
