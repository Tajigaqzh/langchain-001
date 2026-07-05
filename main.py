from __future__ import annotations

import argparse

from app.agents import (
    build_agent_for_model,
    get_available_models,
    is_gpt_model,
    list_supported_models,
)
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

REASONING_LEVELS = ["low", "medium", "high", "extra_high"]
DEFAULT_GPT_MODEL = "gpt-5.5"


def _format_model_list(
    current_model: str,
    available_models: dict[str, bool],
    current_reasoning: str,
) -> str:
    """Render a human-readable model list for the CLI."""
    lines = [f"Current model: {current_model}"]
    if is_gpt_model(current_model):
        lines.append(f"Current reasoning: {current_reasoning}")
    lines.append("")
    lines.append("Available models:")
    for index, entry in enumerate(list_supported_models(), start=1):
        current_label = " (current)" if entry.name == current_model else ""
        default_label = " (default)" if entry.name == DEFAULT_GPT_MODEL else ""
        status = "" if available_models.get(entry.name, False) else "  [not configured: missing API key]"
        lines.append(
            f"{index}. {entry.name}{default_label}{current_label}  {entry.description}{status}"
        )
    lines.append("Use `/model <name>` to switch.")
    return "\n".join(lines)


def _format_reasoning_list(current_level: str) -> str:
    """Render a human-readable reasoning level list for the CLI."""
    descriptions = {
        "low": "Fast responses with lighter reasoning.",
        "medium": "Balances speed and reasoning depth for everyday tasks.",
        "high": "Greater reasoning depth for complex problems.",
        "extra_high": "CLI alias for the highest supported reasoning effort.",
    }
    lines = [f"Current reasoning: {current_level}", "", "Available reasoning levels:"]
    for index, level in enumerate(REASONING_LEVELS, start=1):
        current_label = " (current)" if level == current_level else ""
        default_label = " (default)" if level == "medium" else ""
        lines.append(f"{index}. {level}{default_label}{current_label}  {descriptions[level]}")
    lines.append("Use `/reasoning <level>` to switch.")
    return "\n".join(lines)


def _format_model_changed_message(model_name: str, reasoning_level: str) -> str:
    """Render a Codex-style model change message."""
    if is_gpt_model(model_name):
        return f"Model changed to {model_name} {reasoning_level}"
    return f"Model changed to {model_name}"


def _get_model_entry(model_name: str):
    """Return the supported model entry for a CLI model name."""
    normalized_name = model_name.strip().lower()
    for entry in list_supported_models():
        if entry.name == normalized_name:
            return entry
    raise ValueError(f"Unsupported model: {model_name}")


def _build_model_profile(
    model_name: str,
    reasoning_level: str,
    thread_id: str,
    memory_label: str,
) -> dict[str, object]:
    """Build structured model metadata for local logs and LangSmith traces."""
    entry = _get_model_entry(model_name)
    return {
        "model": entry.name,
        "provider": entry.provider,
        "reasoning_effort": reasoning_level if entry.provider == "gpt" else None,
        "description": entry.description,
        "thread_id": thread_id,
        "memory_backend": memory_label,
    }


def _build_agent_config(
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


def _handle_model_command(
    user_input: str,
    current_model: str,
    available_models: dict[str, bool],
    current_reasoning: str,
):
    """Handle the /model CLI command and return the updated model if changed."""
    model_entries = list_supported_models()
    parts = user_input.split(maxsplit=1)
    if len(parts) == 1:
        return current_model, _format_model_list(current_model, available_models, current_reasoning), False

    requested_model = parts[1].strip().lower()
    if requested_model.isdigit():
        index = int(requested_model) - 1
        if 0 <= index < len(model_entries):
            requested_model = model_entries[index].name
        else:
            supported = ", ".join(str(i) for i in range(1, len(model_entries) + 1))
            return current_model, f"Unsupported model index: {parts[1]}\nSupported indexes: {supported}", False
    if requested_model not in available_models:
        supported = ", ".join(entry.name for entry in model_entries)
        return current_model, f"Unsupported model: {requested_model}\nSupported: {supported}", False

    if not available_models[requested_model]:
        return current_model, f"Model `{requested_model}` is not configured in your environment.", False

    if requested_model == current_model:
        return current_model, f"Already using `{requested_model}`.", False

    if is_gpt_model(requested_model):
        return requested_model, _format_model_changed_message(requested_model, current_reasoning), True
    return requested_model, _format_model_changed_message(requested_model, current_reasoning), True


def _handle_reasoning_command(user_input: str, current_level: str):
    """Handle the /reasoning CLI command."""
    parts = user_input.split(maxsplit=1)
    if len(parts) == 1:
        return current_level, _format_reasoning_list(current_level), False

    requested_level = parts[1].strip().lower().replace("-", "_").replace(" ", "_")
    if requested_level.isdigit():
        index = int(requested_level) - 1
        if 0 <= index < len(REASONING_LEVELS):
            requested_level = REASONING_LEVELS[index]
        else:
            supported = ", ".join(str(i) for i in range(1, len(REASONING_LEVELS) + 1))
            return current_level, f"Unsupported reasoning index: {parts[1]}\nSupported indexes: {supported}", False
    if requested_level not in REASONING_LEVELS:
        supported = ", ".join(REASONING_LEVELS)
        return current_level, f"Unsupported reasoning level: {requested_level}\nSupported: {supported}", False
    if requested_level == current_level:
        return current_level, f"Already using `{requested_level}`.", False
    return requested_level, f"Reasoning changed to {requested_level}", True


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


def _run_cli_session(
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
    model_profile = _build_model_profile(
        current_model,
        current_reasoning,
        normalized_thread_id,
        memory_label,
    )
    agent_config = _build_agent_config(normalized_thread_id, model_profile)
    agent = build_agent_for_model(
        current_model,
        settings,
        reasoning_effort=current_reasoning,
        checkpointer=checkpointer,
    )

    cli_console.print_startup(
        current_model,
        normalized_thread_id,
        memory_label,
    )
    cli_console.print_model_profile(model_profile)
    while True:
        user_input = cli_console.ask_user()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        if user_input.startswith("/model"):
            current_model, message, changed = _handle_model_command(
                user_input,
                current_model,
                available_models,
                current_reasoning,
            )
            if changed:
                agent = build_agent_for_model(
                    current_model,
                    settings,
                    reasoning_effort=current_reasoning,
                    checkpointer=checkpointer,
                )
                model_profile = _build_model_profile(
                    current_model,
                    current_reasoning,
                    normalized_thread_id,
                    memory_label,
                )
                agent_config = _build_agent_config(normalized_thread_id, model_profile)
            cli_console.print_message(message)
            if changed:
                cli_console.print_model_profile(model_profile)
            continue
        if user_input.startswith("/reasoning"):
            current_reasoning, message, changed = _handle_reasoning_command(
                user_input,
                current_reasoning,
            )
            if changed and is_gpt_model(current_model):
                agent = build_agent_for_model(
                    current_model,
                    settings,
                    reasoning_effort=current_reasoning,
                    checkpointer=checkpointer,
                )
                model_profile = _build_model_profile(
                    current_model,
                    current_reasoning,
                    normalized_thread_id,
                    memory_label,
                )
                agent_config = _build_agent_config(normalized_thread_id, model_profile)
                message = _format_model_changed_message(current_model, current_reasoning)
            elif changed:
                message = f"{message}\nIt will take effect after switching to a GPT model."
            cli_console.print_message(message)
            if changed and is_gpt_model(current_model):
                cli_console.print_model_profile(model_profile)
            continue

        try:
            result = agent.invoke(
                {"messages": build_role_tuples(user_input=user_input)},
                config=agent_config,
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
        _run_cli_session(thread_id, checkpointer, memory_label)


if __name__ == "__main__":
    args = parse_args()
    run_cli(
        thread_id=args.thread_id,
        memory_backend=args.memory_backend,
        memory_path=args.memory_path,
    )
