from __future__ import annotations

from app.config import load_bool_env, load_settings


def test_load_bool_env_accepts_common_truthy_values(monkeypatch) -> None:
    """Verify boolean env parsing accepts common enabled values."""
    for value in ["1", "true", "yes", "on", "TRUE"]:
        monkeypatch.setenv("AGENT_STREAM", value)
        assert load_bool_env("AGENT_STREAM") is True


def test_load_bool_env_defaults_and_false_values(monkeypatch) -> None:
    """Verify boolean env parsing handles missing and disabled values."""
    monkeypatch.delenv("AGENT_STREAM", raising=False)
    assert load_bool_env("AGENT_STREAM", default=True) is True

    monkeypatch.setenv("AGENT_STREAM", "false")
    assert load_bool_env("AGENT_STREAM", default=True) is False


def test_load_settings_reads_agent_stream(monkeypatch) -> None:
    """Verify project settings include the CLI streaming preference."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("GPT_API_KEY", "test-gpt-key")
    monkeypatch.setenv("AGENT_STREAM", "true")
    monkeypatch.setenv("AGENT_STREAM_CHUNK_SIZE", "3")
    monkeypatch.setenv("AGENT_STREAM_DELAY", "0.02")
    monkeypatch.setenv("AGENT_MODEL_RETRY_ATTEMPTS", "7")
    monkeypatch.setenv("AGENT_MODEL_RETRY_DELAY", "1.5")
    monkeypatch.setenv("AGENT_SQLITE_CACHE_DAYS", "12")
    monkeypatch.setenv("AGENT_MCP_CONFIG_PATH", ".data/mcp.json")

    settings = load_settings()

    assert settings.deepseek_api_key == ""
    assert settings.gpt_api_key == "test-gpt-key"
    assert settings.agent_stream is True
    assert settings.agent_stream_chunk_size == 3
    assert settings.agent_stream_delay == 0.02
    assert settings.model_retry_attempts == 7
    assert settings.model_retry_delay == 1.5
    assert settings.sqlite_cache_days == 12
    assert settings.mcp_config_path == ".data/mcp.json"
