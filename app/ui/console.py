from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt


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
        return Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

    def print_message(self, message: str) -> None:
        """Render a plain CLI status message."""
        self.console.print()
        self.console.print(message)

    def print_error(self, error: Exception) -> None:
        """Render an Agent error."""
        self.console.print()
        self.console.print(f"[bold red]Agent error:[/bold red] {error}")

    def print_agent_answer(self, answer: str) -> None:
        """Render an Agent answer as Markdown."""
        self.console.print()
        self.console.print("[bold green]Agent:[/bold green]")
        self.console.print(Markdown(answer))
