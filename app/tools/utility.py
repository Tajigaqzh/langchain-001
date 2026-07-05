from __future__ import annotations

from datetime import datetime
import time

from langchain_core.tools import tool


def _now() -> datetime:
    """Return the current local timezone-aware datetime."""
    return datetime.now().astimezone()


@tool
def current_time() -> str:
    """Return the current local time."""
    return _now().isoformat(timespec="seconds")


@tool
def current_date() -> str:
    """Return the current local date in YYYY-MM-DD format."""
    return _now().strftime("%Y-%m-%d")


@tool
def current_weekday() -> str:
    """Return the current local weekday name."""
    return _now().strftime("%A")


@tool
def current_time_parts() -> str:
    """Return current month/day and time parts in a readable format."""
    now = _now()
    return "\n".join(
        [
            f"month: {now.month}",
            f"day: {now.day}",
            f"hour: {now.hour}",
            f"minute: {now.minute}",
            f"second: {now.second}",
        ]
    )


@tool
def current_timestamp(unit: str = "seconds") -> str:
    """Return the current Unix timestamp in seconds or milliseconds."""
    now = time.time()
    if unit == "seconds":
        return str(int(now))
    if unit == "milliseconds":
        return str(int(now * 1000))
    return "unit must be 'seconds' or 'milliseconds'."


@tool
def current_datetime_info() -> str:
    """Return several common current date and time formats."""
    now = _now()
    return "\n".join(
        [
            f"iso: {now.isoformat(timespec='seconds')}",
            f"date: {now.strftime('%Y-%m-%d')}",
            f"time: {now.strftime('%H:%M:%S')}",
            f"weekday: {now.strftime('%A')}",
            f"month_day: {now.strftime('%m-%d')}",
            f"timestamp_seconds: {int(now.timestamp())}",
            f"timestamp_milliseconds: {int(now.timestamp() * 1000)}",
        ]
    )


@tool
def format_current_time(format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Return the current local time formatted with strftime syntax."""
    try:
        return _now().strftime(format_string)
    except Exception as exc:
        return f"Time formatting failed: {exc}"


@tool
def convert_timestamp(timestamp: str, unit: str = "seconds") -> str:
    """Convert a Unix timestamp to local datetime formats."""
    try:
        raw = int(timestamp)
    except ValueError:
        return "timestamp must be an integer string."

    if unit == "milliseconds":
        raw = raw / 1000
    elif unit != "seconds":
        return "unit must be 'seconds' or 'milliseconds'."

    dt = datetime.fromtimestamp(raw).astimezone()
    return "\n".join(
        [
            f"iso: {dt.isoformat(timespec='seconds')}",
            f"date: {dt.strftime('%Y-%m-%d')}",
            f"time: {dt.strftime('%H:%M:%S')}",
            f"weekday: {dt.strftime('%A')}",
        ]
    )


@tool
def parse_datetime_string(
    value: str,
    format_string: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Parse a datetime string with strptime syntax and return normalized values."""
    if not value.strip():
        return "value must not be empty."

    try:
        dt = datetime.strptime(value, format_string).astimezone()
    except ValueError as exc:
        return f"Datetime parsing failed: {exc}"

    return "\n".join(
        [
            f"iso: {dt.isoformat(timespec='seconds')}",
            f"timestamp_seconds: {int(dt.timestamp())}",
            f"timestamp_milliseconds: {int(dt.timestamp() * 1000)}",
            f"weekday: {dt.strftime('%A')}",
        ]
    )


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
