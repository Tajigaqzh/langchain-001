from __future__ import annotations

import argparse

from app.agents import build_agent_for_model, get_available_models, is_gpt_model
from app.cli.commands import (
    CliCommand,
    default_commands,
    format_model_changed_message,
    handle_model_command,
    handle_reasoning_command,
)
from app.cli.model_profile import build_agent_config, build_model_profile
from app.cli.renderers import build_response_renderer
from app.cli.runtime import CliRuntime, CliSessionState
from app.config import Settings, load_settings
from app.tools.mcp import McpToolLoadError
from app.memory import (
    MEMORY_BACKENDS,
    build_thread_config,
    open_memory_checkpointer,
)
from app.ui import CliConsole


def find_command(user_input: str, commands: tuple[CliCommand, ...]) -> CliCommand | None:
    """Return the slash command matching user input, if any."""
    for command in commands:
        if user_input == command.prefix or user_input.startswith(f"{command.prefix} "):
            return command
    return None


def build_model_agent(
    model_name: str,
    reasoning_level: str,
    settings: object,
    checkpointer: object,
):
    """Build an Agent for the selected model and reasoning level."""
    return build_agent_for_model(
        model_name,
        settings,
        reasoning_effort=reasoning_level,
        checkpointer=checkpointer,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI options for the interactive Agent session."""
    parser = argparse.ArgumentParser(description="Start the interactive LangChain Agent CLI.")
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Conversation memory thread id for this CLI process. Overrides AGENT_THREAD_ID.",
    )
    parser.add_argument(
        "--memory-backend",
        choices=MEMORY_BACKENDS,
        default=None,
        help="Short-term memory backend. Overrides AGENT_MEMORY_BACKEND.",
    )
    parser.add_argument(
        "--memory-path",
        default=None,
        help="SQLite file path when --memory-backend sqlite is used. Overrides AGENT_MEMORY_PATH.",
    )
    stream_group = parser.add_mutually_exclusive_group()
    stream_group.add_argument(
        "--stream",
        dest="stream",
        action="store_true",
        default=None,
        help="Stream Agent output, overriding AGENT_STREAM.",
    )
    stream_group.add_argument(
        "--no-stream",
        dest="stream",
        action="store_false",
        help="Disable streamed Agent output, overriding AGENT_STREAM.",
    )
    return parser.parse_args()


def refresh_agent_context(
    model_name: str,
    reasoning_level: str,
    thread_id: str,
    memory_label: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build fresh model profile and invocation config for the active model."""
    model_profile = build_model_profile(
        model_name,
        reasoning_level,
        thread_id,
        memory_label,
    )
    return model_profile, build_agent_config(thread_id, model_profile)


def refresh_model_agent(
    model_name: str,
    reasoning_level: str,
    thread_id: str,
    memory_label: str,
    settings: object,
    checkpointer: object,
):
    """Rebuild the Agent and trace context after model profile changes."""
    agent = build_model_agent(model_name, reasoning_level, settings, checkpointer)
    model_profile, agent_config = refresh_agent_context(
        model_name,
        reasoning_level,
        thread_id,
        memory_label,
    )
    return agent, model_profile, agent_config


def process_model_command(
    user_input: str,
    current_model: str,
    current_reasoning: str,
    available_models: dict[str, bool],
    runtime: CliRuntime,
    cli_console: CliConsole,
) -> str:
    """Handle /model and update the mutable CLI runtime when needed."""
    next_model, message, changed = handle_model_command(
        user_input,
            current_model,
            available_models,
            current_reasoning,
            runtime.default_model,
        )
    if changed:
        agent, model_profile, agent_config = refresh_model_agent(
            next_model,
            current_reasoning,
            runtime.thread_id,
            runtime.memory_label,
            runtime.settings,
            runtime.checkpointer,
        )
        runtime.replace_agent(agent, model_profile, agent_config)
    cli_console.print_message(message)
    if changed:
        cli_console.print_model_profile(runtime.model_profile)
    return next_model


def process_reasoning_command(
    user_input: str,
    current_model: str,
    current_reasoning: str,
    runtime: CliRuntime,
    cli_console: CliConsole,
) -> str:
    """Handle /reasoning and update the mutable CLI runtime when needed."""
    next_reasoning, message, changed = handle_reasoning_command(user_input, current_reasoning)
    if changed and is_gpt_model(current_model):
        agent, model_profile, agent_config = refresh_model_agent(
            current_model,
            next_reasoning,
            runtime.thread_id,
            runtime.memory_label,
            runtime.settings,
            runtime.checkpointer,
        )
        runtime.replace_agent(agent, model_profile, agent_config)
        message = format_model_changed_message(current_model, next_reasoning)
    elif changed:
        message = f"{message}\nIt will take effect after switching to a GPT model."
    cli_console.print_message(message)
    if changed and is_gpt_model(current_model):
        cli_console.print_model_profile(runtime.model_profile)
    return next_reasoning


def format_mcp_command_help(settings: Settings) -> str:
    """Render MCP command help and current configuration state."""
    config_path = settings.mcp_config_path or "disabled"
    return (
        f"MCP config: {config_path}\n"
        "Use `/mcp reload` after changing AGENT_MCP_CONFIG_PATH or the MCP JSON file."
    )


def process_mcp_command(
    user_input: str,
    current_model: str,
    current_reasoning: str,
    command_context: CliSessionState,
) -> None:
    """Handle /mcp commands and reload configured MCP tools without restarting."""
    runtime = command_context.runtime
    cli_console = command_context.cli_console
    parts = user_input.split(maxsplit=1)
    if len(parts) == 1:
        cli_console.print_message(format_mcp_command_help(runtime.settings))
        return

    action = parts[1].strip().lower()
    if action != "reload":
        cli_console.print_message("Unsupported MCP command. Use `/mcp reload`.")
        return

    try:
        next_settings = load_settings()
        agent, model_profile, agent_config = refresh_model_agent(
            current_model,
            current_reasoning,
            runtime.thread_id,
            runtime.memory_label,
            next_settings,
            runtime.checkpointer,
        )
    except McpToolLoadError as exc:
        cli_console.print_message(f"MCP reload failed: {exc}")
        return

    runtime.settings = next_settings
    runtime.retry_attempts = next_settings.model_retry_attempts
    runtime.retry_delay = next_settings.model_retry_delay
    runtime.stream_chunk_size = next_settings.agent_stream_chunk_size
    runtime.stream_delay = next_settings.agent_stream_delay
    runtime.replace_agent(agent, model_profile, agent_config)
    command_context.available_models = get_available_models(next_settings)
    cli_console.print_message(
        f"MCP reloaded from: {next_settings.mcp_config_path or 'disabled'}"
    )
    cli_console.print_model_profile(runtime.model_profile)


def run_cli_session(
    thread_id: str,
    checkpointer: object,
    memory_label: str,
    stream: bool,
    settings: Settings,
    console: CliConsole | None = None,
) -> None:
    """Run the interactive Agent session with an opened checkpointer."""
    cli_console = console or CliConsole()
    available_models = get_available_models(settings)
    current_model = settings.agent_default_model
    current_reasoning = "medium"
    normalized_thread_id = build_thread_config(thread_id)["configurable"]["thread_id"]
    agent, model_profile, agent_config = refresh_model_agent(
        current_model,
        current_reasoning,
        normalized_thread_id,
        memory_label,
        settings,
        checkpointer,
    )
    runtime = CliRuntime(
        agent=agent,
        agent_config=agent_config,
        checkpointer=checkpointer,
        default_model=settings.agent_default_model,
        memory_label=memory_label,
        model_profile=model_profile,
        retry_attempts=settings.model_retry_attempts,
        retry_delay=settings.model_retry_delay,
        settings=settings,
        stream_chunk_size=settings.agent_stream_chunk_size,
        stream_delay=settings.agent_stream_delay,
        thread_id=normalized_thread_id,
    )
    command_context = CliSessionState(
        available_models=available_models,
        cli_console=cli_console,
        current_model=current_model,
        current_reasoning=current_reasoning,
        runtime=runtime,
    )
    commands = default_commands()
    response_renderer = build_response_renderer(stream)

    cli_console.print_startup(current_model, normalized_thread_id, memory_label)
    cli_console.print_model_profile(model_profile)
    while True:
        user_input = cli_console.ask_user()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        command = find_command(user_input, commands)
        if command is not None:
            command.execute(user_input, command_context)
            continue

        try:
            response_renderer.render(user_input, runtime, cli_console)
        except Exception as exc:
            cli_console.print_error(exc)


def run_cli(
    thread_id: str | None = None,
    memory_backend: str | None = None,
    memory_path: str | None = None,
    stream: bool | None = None,
) -> None:
    """Start the interactive command-line Agent session."""
    settings = load_settings()
    effective_thread_id = thread_id or settings.agent_thread_id
    effective_memory_backend = memory_backend or settings.memory_backend
    effective_memory_path = memory_path or settings.memory_path
    effective_stream = settings.agent_stream if stream is None else stream
    if effective_memory_backend == "sqlite":
        memory_label = f"sqlite ({effective_memory_path})"
    else:
        memory_label = effective_memory_backend

    with open_memory_checkpointer(
        effective_memory_backend,
        effective_memory_path,
        sqlite_cache_days=settings.sqlite_cache_days,
    ) as checkpointer:
        run_cli_session(
            effective_thread_id,
            checkpointer,
            memory_label,
            stream=effective_stream,
            settings=settings,
        )
