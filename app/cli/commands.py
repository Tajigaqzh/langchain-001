from __future__ import annotations

from app.agents import is_gpt_model, list_supported_models

REASONING_LEVELS = ["low", "medium", "high", "extra_high"]
DEFAULT_GPT_MODEL = "gpt-5.5"


def format_model_changed_message(model_name: str, reasoning_level: str) -> str:
    """Render a model change message for the CLI."""
    if is_gpt_model(model_name):
        return f"Model changed to {model_name} {reasoning_level}"
    return f"Model changed to {model_name}"


def format_model_list(
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


def format_reasoning_list(current_level: str) -> str:
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


def handle_model_command(
    user_input: str,
    current_model: str,
    available_models: dict[str, bool],
    current_reasoning: str,
):
    """Handle the /model CLI command and return the updated model if changed."""
    model_entries = list_supported_models()
    parts = user_input.split(maxsplit=1)
    if len(parts) == 1:
        return current_model, format_model_list(current_model, available_models, current_reasoning), False

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

    return requested_model, format_model_changed_message(requested_model, current_reasoning), True


def handle_reasoning_command(user_input: str, current_level: str):
    """Handle the /reasoning CLI command."""
    parts = user_input.split(maxsplit=1)
    if len(parts) == 1:
        return current_level, format_reasoning_list(current_level), False

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
