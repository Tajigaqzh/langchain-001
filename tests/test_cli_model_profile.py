from __future__ import annotations

from langchain_core.messages import AIMessageChunk

from app.config import DEFAULT_AGENT_DEFAULT_MODEL, Settings
from app.cli.commands import default_commands
from app.cli.model_profile import build_agent_config, build_model_profile
from app.cli.renderers import extract_stream_text
from app.cli.retry import retry_model_call
from app.cli.runtime import CliRuntime
from app.cli.session import process_mcp_command


def test_default_model_is_gpt() -> None:
    """Verify the CLI default model points at the GPT profile."""
    assert DEFAULT_AGENT_DEFAULT_MODEL == "gpt-5.5"


def test_default_commands_include_mcp() -> None:
    """Verify the CLI exposes MCP management commands."""
    assert [command.prefix for command in default_commands()] == [
        "/model",
        "/reasoning",
        "/mcp",
    ]


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


def test_extract_stream_text_from_message_chunk() -> None:
    """Verify streamed AI message chunks render only text content."""
    assert extract_stream_text((AIMessageChunk(content="hello"), {"node": "model"})) == "hello"
    assert extract_stream_text(AIMessageChunk(content=[{"type": "text", "text": "world"}])) == "world"
    assert extract_stream_text({"not": "a message"}) == ""


class RetryConsole:
    """Test double for retry notices."""

    def __init__(self) -> None:
        """Collect retry notices."""
        self.notices = []
        self.errors = []

    def print_retry_notice(self, error, retry_number, max_retries, delay) -> None:
        """Record retry notice arguments."""
        self.notices.append((str(error), retry_number, max_retries, delay))

    def print_model_error(self, message) -> None:
        """Record the final model error message."""
        self.errors.append(message)


def build_retry_runtime(retry_attempts: int) -> CliRuntime:
    """Build a minimal runtime for retry helper tests."""
    return CliRuntime(
        agent=object(),
        agent_config={},
        checkpointer=object(),
        default_model="gpt-5.5",
        memory_label="memory",
        model_profile={},
        retry_attempts=retry_attempts,
        retry_delay=0,
        settings=Settings(),
        stream_chunk_size=4,
        stream_delay=0,
        thread_id="default",
    )


class MessageConsole(RetryConsole):
    """Test double for command messages and model profile output."""

    def __init__(self) -> None:
        """Collect CLI command output."""
        super().__init__()
        self.messages = []
        self.profiles = []

    def print_message(self, message) -> None:
        """Record plain CLI messages."""
        self.messages.append(message)

    def print_model_profile(self, profile) -> None:
        """Record rendered model profiles."""
        self.profiles.append(profile)


class CommandContext:
    """Minimal command context for MCP reload tests."""

    def __init__(self, runtime, console) -> None:
        """Store mutable command state."""
        self.available_models = {"gpt-5.5": True}
        self.cli_console = console
        self.current_model = "gpt-5.5"
        self.current_reasoning = "medium"
        self.runtime = runtime


def test_process_mcp_reload_rebuilds_agent(monkeypatch) -> None:
    """Verify /mcp reload refreshes settings and replaces the active Agent."""
    runtime = build_retry_runtime(retry_attempts=1)
    console = MessageConsole()
    context = CommandContext(runtime, console)
    next_agent = object()
    next_profile = {"model": "gpt-5.5", "provider": "gpt", "reasoning_effort": "medium"}
    next_config = {"configurable": {"thread_id": "default"}}
    next_settings = Settings(
        gpt_api_key="key",
        mcp_config_path=".data/mcp.json",
        model_retry_attempts=5,
        model_retry_delay=2,
        agent_stream_chunk_size=8,
        agent_stream_delay=0.01,
    )

    monkeypatch.setattr("app.cli.session.load_settings", lambda: next_settings)
    monkeypatch.setattr(
        "app.cli.session.refresh_model_agent",
        lambda *args: (next_agent, next_profile, next_config),
    )
    monkeypatch.setattr(
        "app.cli.session.get_available_models",
        lambda settings: {"gpt-5.5": True, "deepseek": False},
    )

    process_mcp_command("/mcp reload", "gpt-5.5", "medium", context)

    assert runtime.agent is next_agent
    assert runtime.settings is next_settings
    assert runtime.retry_attempts == 5
    assert runtime.retry_delay == 2
    assert runtime.stream_chunk_size == 8
    assert runtime.stream_delay == 0.01
    assert context.available_models == {"gpt-5.5": True, "deepseek": False}
    assert console.messages == ["MCP reloaded from: .data/mcp.json"]
    assert console.profiles == [next_profile]


def test_retry_model_call_succeeds_after_transient_failures() -> None:
    """Verify model retry helper retries transient failures before succeeding."""
    attempts = {"count": 0}
    runtime = build_retry_runtime(retry_attempts=3)
    console = RetryConsole()

    def flaky_operation():
        """Fail twice, then succeed."""
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary")
        return "ok"

    assert retry_model_call(flaky_operation, runtime, console) == "ok"
    assert attempts["count"] == 3
    assert console.notices == [
        ("RuntimeError: temporary", 1, 3, 0),
        ("RuntimeError: temporary", 2, 3, 0),
    ]


def test_retry_model_call_raises_after_retry_budget() -> None:
    """Verify model retry helper raises the final error after retries are exhausted."""
    runtime = build_retry_runtime(retry_attempts=2)
    console = RetryConsole()

    def failing_operation():
        """Always fail."""
        raise RuntimeError("down")

    try:
        retry_model_call(failing_operation, runtime, console)
    except RuntimeError as exc:
        assert str(exc) == "down"
    else:
        raise AssertionError("retry_model_call should raise after retry budget")

    assert console.notices == [
        ("RuntimeError: down", 1, 2, 0),
        ("RuntimeError: down", 2, 2, 0),
    ]
    assert console.errors == ["RuntimeError: down"]
