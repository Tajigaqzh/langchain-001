from __future__ import annotations

from datetime import datetime

from langchain_core.tools import tool


@tool
def current_time() -> str:
    """Return the current local time."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@tool
def calculator(expression: str) -> str:
    """Evaluate a simple arithmetic expression."""
    allowed_chars = set("0123456789+-*/(). %")
    if not expression or any(char not in allowed_chars for char in expression):
        return "Only simple arithmetic expressions are supported."

    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as exc:
        return f"Calculation failed: {exc}"


def get_tools():
    """Return all tools available to the default Agent."""
    return [current_time, calculator]
