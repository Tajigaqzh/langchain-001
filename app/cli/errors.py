from __future__ import annotations

import re


def extract_status_code(error: Exception) -> int | None:
    """Best-effort extraction of an HTTP status code from model errors."""
    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    response = getattr(error, "response", None)
    response_status = getattr(response, "status_code", None)
    if isinstance(response_status, int):
        return response_status

    match = re.search(r"\b([1-5][0-9]{2})\b", str(error))
    if match:
        return int(match.group(1))
    return None


def describe_model_error(error: Exception) -> str:
    """Return a user-facing explanation for common model call failures."""
    status_code = extract_status_code(error)
    if status_code in {401, 403}:
        return f"HTTP {status_code}: authentication or permission denied. Check the API key, base URL, and model access."
    if status_code == 404:
        return "HTTP 404: model or endpoint was not found. Check the model name and base URL."
    if status_code == 408:
        return "HTTP 408: request timed out before the model responded."
    if status_code == 429:
        return "HTTP 429: rate limit or quota exceeded. Wait before retrying or check your quota."
    if status_code and 500 <= status_code <= 599:
        return f"HTTP {status_code}: provider server error. Retrying may recover."
    if status_code:
        return f"HTTP {status_code}: model call failed."
    return f"{type(error).__name__}: {error}"
