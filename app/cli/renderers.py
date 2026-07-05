from __future__ import annotations

from typing import Protocol

from app.cli.retry import retry_model_call
from app.cli.runtime import CliRuntime
from app.messages import build_role_tuples
from app.ui import CliConsole


class ResponseRenderer(Protocol):
    """Render an Agent response for one user input."""

    def render(
        self,
        user_input: str,
        runtime: CliRuntime,
        cli_console: CliConsole,
    ) -> None:
        """Invoke the Agent and render its response."""


class FullResponseRenderer:
    """Render Agent output after the full response is available."""

    def render(
        self,
        user_input: str,
        runtime: CliRuntime,
        cli_console: CliConsole,
    ) -> None:
        """Invoke the Agent once and render the final Markdown answer."""
        input_data = {"messages": build_role_tuples(user_input=user_input)}
        with cli_console.working_status("calling model"):
            result = retry_model_call(
                lambda: runtime.agent.invoke(
                    input_data,
                    config=runtime.agent_config,
                ),
                runtime,
                cli_console,
            )
        answer = result["messages"][-1].content
        cli_console.print_agent_answer(answer)


class StreamResponseRenderer:
    """Render Agent output as streamed text deltas."""

    def render(
        self,
        user_input: str,
        runtime: CliRuntime,
        cli_console: CliConsole,
    ) -> None:
        """Stream Agent response chunks and render them smoothly."""
        input_data = {"messages": build_role_tuples(user_input=user_input)}
        events = retry_model_call(
            lambda: runtime.agent.stream(
                input_data,
                config=runtime.agent_config,
                stream_mode="messages",
            ),
            runtime,
            cli_console,
        )
        with cli_console.working_status("waiting for first token"):
            first_text = retry_model_call(
                lambda: consume_until_first_text(events),
                runtime,
                cli_console,
            )

        cli_console.begin_stream_answer()
        if first_text:
            self._print_delta(first_text, runtime, cli_console)
        for event in events:
            text = extract_stream_text(event)
            if text:
                self._print_delta(text, runtime, cli_console)
        cli_console.end_stream_answer()

    @staticmethod
    def _print_delta(
        text: str,
        runtime: CliRuntime,
        cli_console: CliConsole,
    ) -> None:
        """Render one text delta using the configured smoothing settings."""
        cli_console.print_stream_delta(
            text,
            chunk_size=runtime.stream_chunk_size,
            delay=runtime.stream_delay,
        )


def build_response_renderer(stream: bool) -> ResponseRenderer:
    """Create the response renderer for the selected output mode."""
    if stream:
        return StreamResponseRenderer()
    return FullResponseRenderer()


def extract_stream_text(event: object) -> str:
    """Extract displayable text from a LangGraph stream event."""
    message = event[0] if isinstance(event, tuple) and event else event
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        return "".join(text_parts)
    return ""


def consume_until_first_text(events) -> str:
    """Consume stream events until the first displayable text chunk appears."""
    for event in events:
        text = extract_stream_text(event)
        if text:
            return text
    return ""
