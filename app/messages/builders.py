from __future__ import annotations

from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

SUPPORTED_ROLES = {"system", "user", "assistant"}


def build_role_message(role: str, content: str) -> BaseMessage:
    """Build a LangChain message object from a supported chat role."""
    normalized_role = role.strip().lower()
    if normalized_role not in SUPPORTED_ROLES:
        raise ValueError(f"Unsupported role: {role}")

    if normalized_role == "system":
        return SystemMessage(content=content)
    if normalized_role == "user":
        return HumanMessage(content=content)
    return AIMessage(content=content)


def build_chat_messages(
    *,
    system_prompt: str | None = None,
    user_input: str | None = None,
    assistant_output: str | None = None,
    history: Sequence[tuple[str, str]] | None = None,
) -> list[BaseMessage]:
    """Build an ordered LangChain message list from role/content inputs."""
    messages: list[BaseMessage] = []

    if system_prompt:
        messages.append(build_role_message("system", system_prompt))

    if history:
        messages.extend(build_role_message(role, content) for role, content in history)

    if user_input:
        messages.append(build_role_message("user", user_input))

    if assistant_output:
        messages.append(build_role_message("assistant", assistant_output))

    return messages


def build_role_tuples(
    *,
    system_prompt: str | None = None,
    user_input: str | None = None,
    assistant_output: str | None = None,
    history: Sequence[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """Build role/content tuples for APIs that accept lightweight chat message pairs."""
    messages: list[tuple[str, str]] = []

    if system_prompt:
        messages.append(("system", system_prompt))

    if history:
        messages.extend((role.strip().lower(), content) for role, content in history)

    if user_input:
        messages.append(("user", user_input))

    if assistant_output:
        messages.append(("assistant", assistant_output))

    return messages
