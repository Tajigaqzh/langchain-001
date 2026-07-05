from __future__ import annotations

import argparse

from app.agents import build_agent_for_model, get_available_models, is_gpt_model
from app.cli.commands import (
    format_model_changed_message,
    handle_model_command,
    handle_reasoning_command,
)
from app.cli.model_profile import build_agent_config, build_model_profile
from app.config import load_settings
from app.memory import (
    DEFAULT_MEMORY_BACKEND,
    DEFAULT_MEMORY_DB_PATH,
    DEFAULT_THREAD_ID,
    MEMORY_BACKENDS,
    build_thread_config,
    open_memory_checkpointer,
)
from app.messages import build_role_tuples
from app.ui import CliConsole


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
        default=DEFAULT_THREAD_ID,
        help="Conversation memory thread id for this CLI process.",
    )
    parser.add_argument(
        "--memory-backend",
        choices=MEMORY_BACKENDS,
        default=DEFAULT_MEMORY_BACKEND,
        help="Short-term memory backend.",
    )
    parser.add_argument(
        "--memory-path",
        default=str(DEFAULT_MEMORY_DB_PATH),
        help="SQLite file path when --memory-backend sqlite is used.",
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
    runtime: dict[str, object],
    cli_console: CliConsole,
) -> str:
    """Handle /model and update the mutable CLI runtime when needed."""
    next_model, message, changed = handle_model_command(
        user_input,
        current_model,
        available_models,
        current_reasoning,
    )
    if changed:
        agent, model_profile, agent_config = refresh_model_agent(
            next_model,
            current_reasoning,
            str(runtime["thread_id"]),
            str(runtime["memory_label"]),
            runtime["settings"],
            runtime["checkpointer"],
        )
        runtime.update(
            agent=agent,
            model_profile=model_profile,
            agent_config=agent_config,
        )
    cli_console.print_message(message)
    if changed:
        cli_console.print_model_profile(runtime["model_profile"])
    return next_model


def process_reasoning_command(
    user_input: str,
    current_model: str,
    current_reasoning: str,
    runtime: dict[str, object],
    cli_console: CliConsole,
) -> str:
    """Handle /reasoning and update the mutable CLI runtime when needed."""
    next_reasoning, message, changed = handle_reasoning_command(user_input, current_reasoning)
    if changed and is_gpt_model(current_model):
        agent, model_profile, agent_config = refresh_model_agent(
            current_model,
            next_reasoning,
            str(runtime["thread_id"]),
            str(runtime["memory_label"]),
            runtime["settings"],
            runtime["checkpointer"],
        )
        runtime.update(
            agent=agent,
            model_profile=model_profile,
            agent_config=agent_config,
        )
        message = format_model_changed_message(current_model, next_reasoning)
    elif changed:
        message = f"{message}\nIt will take effect after switching to a GPT model."
    cli_console.print_message(message)
    if changed and is_gpt_model(current_model):
        cli_console.print_model_profile(runtime["model_profile"])
    return next_reasoning


def run_cli_session(
    thread_id: str,
    checkpointer: object,
    memory_label: str,
    console: CliConsole | None = None,
) -> None:
    """Run the interactive Agent session with an opened checkpointer."""
    cli_console = console or CliConsole()
    settings = load_settings()
    available_models = get_available_models(settings)
    current_model = "deepseek"
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
    runtime = {
        "agent": agent,
        "agent_config": agent_config,
        "checkpointer": checkpointer,
        "memory_label": memory_label,
        "model_profile": model_profile,
        "settings": settings,
        "thread_id": normalized_thread_id,
    }

    cli_console.print_startup(current_model, normalized_thread_id, memory_label)
    cli_console.print_model_profile(model_profile)
    while True:
        user_input = cli_console.ask_user()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        if user_input.startswith("/model"):
            current_model = process_model_command(
                user_input,
                current_model,
                current_reasoning,
                available_models,
                runtime,
                cli_console,
            )
            continue
        if user_input.startswith("/reasoning"):
            current_reasoning = process_reasoning_command(
                user_input,
                current_model,
                current_reasoning,
                runtime,
                cli_console,
            )
            continue

        try:
            result = runtime["agent"].invoke(
                {"messages": build_role_tuples(user_input=user_input)},
                config=runtime["agent_config"],
            )
        except Exception as exc:
            cli_console.print_error(exc)
            continue

        answer = result["messages"][-1].content
        cli_console.print_agent_answer(answer)


def run_cli(
    thread_id: str = DEFAULT_THREAD_ID,
    memory_backend: str = DEFAULT_MEMORY_BACKEND,
    memory_path: str = str(DEFAULT_MEMORY_DB_PATH),
) -> None:
    """Start the interactive command-line Agent session."""
    if memory_backend == "sqlite":
        memory_label = f"sqlite ({memory_path})"
    else:
        memory_label = memory_backend

    with open_memory_checkpointer(memory_backend, memory_path) as checkpointer:
        run_cli_session(thread_id, checkpointer, memory_label)
