from __future__ import annotations

import time
from contextlib import AbstractContextManager

from rich.console import Console
from rich.markdown import Markdown
from rich.status import Status


class CliConsole:
    """Render CLI input and Agent output with Rich."""

    def __init__(self, console: Console | None = None) -> None:
        """Create a console wrapper around Rich's Console."""
        self.console = console or Console()

    def print_startup(
        self,
        model_name: str,
        thread_id: str,
        memory_label: str,
    ) -> None:
        """Render initial session information."""
        self.console.print(
            f"[bold green]{model_name.capitalize()} Agent[/bold green] is ready. "
            "Type [bold]exit[/bold] or [bold]quit[/bold] to stop."
        )
        self.console.print("Use [cyan]/model[/cyan] to list models, or [cyan]/model <name>[/cyan] to switch.")
        self.console.print("Use [cyan]/reasoning[/cyan] to list reasoning levels for GPT models.")
        self.console.print("Use [cyan]/mcp reload[/cyan] to reload MCP tools without restarting.")
        self.console.print(f"[dim]Memory thread:[/dim] {thread_id}")
        self.console.print(f"[dim]Memory backend:[/dim] {memory_label}")

    def print_model_profile(self, profile: dict[str, object]) -> None:
        """Render the active model profile."""
        reasoning = profile.get("reasoning_effort") or "n/a"
        self.console.print(
            "[dim]Model profile:[/dim] "
            f"name={profile['model']} "
            f"provider={profile['provider']} "
            f"reasoning={reasoning}"
        )

    def ask_user(self) -> str:
        """Prompt for one user message."""
        self.console.print()
        self.console.print("[bold cyan]>[/bold cyan] ", end="")
        return input().strip()

    def print_message(self, message: str) -> None:
        """Render a plain CLI status message."""
        self.console.print()
        self.console.print(message)

    def print_error(self, error: Exception) -> None:
        """Render an Agent error."""
        self.console.print()
        self.console.print(f"[bold red]Agent error:[/bold red] {error}")

    def print_model_error(self, message: str) -> None:
        """Render a classified model error."""
        self.console.print()
        self.console.print(f"[bold red]Model error:[/bold red] {message}")

    def print_retry_notice(
        self,
        error: Exception,
        retry_number: int,
        max_retries: int,
        delay: float,
    ) -> None:
        """Render a transient model retry notice."""
        self.console.print()
        self.console.print(
            "[yellow]Model call failed; "
            f"retrying {retry_number}/{max_retries} in {delay:g}s:[/yellow] {error}"
        )

    def working_status(self, detail: str = "thinking") -> AbstractContextManager[Status]:
        """Render a transient Working status while the Agent is preparing output."""
        return self.console.status(
            f"[bold cyan]Working[/bold cyan] [dim]({detail})[/dim]",
            spinner="dots",
        )

    def print_agent_answer(self, answer: str) -> None:
        """Render an Agent answer as Markdown."""
        self.console.print()
        self.console.print("[bold green]Agent[/bold green] [dim]›[/dim]")
        self.console.print(Markdown(answer))

    def begin_stream_answer(self) -> None:
        """Render the heading for a streamed Agent answer."""
        self.console.print()
        self.console.print("[bold green]Agent[/bold green] [dim]›[/dim]")

    def print_stream_delta(
        self,
        text: str,
        chunk_size: int = 4,
        delay: float = 0.015,
    ) -> None:
        """Render one streamed text delta in small flushed chunks."""
        safe_chunk_size = max(chunk_size, 1)
        for start in range(0, len(text), safe_chunk_size):
            chunk = text[start : start + safe_chunk_size]
            self.console.print(chunk, end="")
            self.console.file.flush()
            if delay > 0 and start + safe_chunk_size < len(text):
                time.sleep(delay)

    def end_stream_answer(self) -> None:
        """Finish a streamed Agent answer."""
        self.console.print()
