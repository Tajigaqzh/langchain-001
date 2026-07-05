from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings
from app.ui import CliConsole


@dataclass
class CliRuntime:
    """Mutable runtime state for one CLI session."""

    agent: Any
    agent_config: dict[str, object]
    checkpointer: object
    default_model: str
    memory_label: str
    model_profile: dict[str, object]
    retry_attempts: int
    retry_delay: float
    settings: Settings
    stream_chunk_size: int
    stream_delay: float
    thread_id: str

    def replace_agent(
        self,
        agent: Any,
        model_profile: dict[str, object],
        agent_config: dict[str, object],
    ) -> None:
        """Replace the active Agent and matching trace context."""
        self.agent = agent
        self.model_profile = model_profile
        self.agent_config = agent_config


@dataclass
class CliSessionState:
    """Mutable command state for one CLI session."""

    available_models: dict[str, bool]
    cli_console: CliConsole
    current_model: str
    current_reasoning: str
    runtime: CliRuntime

    def handle_model(self, user_input: str) -> None:
        """Handle a /model command and update the active model when needed."""
        from app.cli.session import process_model_command

        self.current_model = process_model_command(
            user_input,
            self.current_model,
            self.current_reasoning,
            self.available_models,
            self.runtime,
            self.cli_console,
        )

    def handle_reasoning(self, user_input: str) -> None:
        """Handle a /reasoning command and update reasoning when needed."""
        from app.cli.session import process_reasoning_command

        self.current_reasoning = process_reasoning_command(
            user_input,
            self.current_model,
            self.current_reasoning,
            self.runtime,
            self.cli_console,
        )

    def handle_mcp(self, user_input: str) -> None:
        """Handle an /mcp command and refresh MCP tools when requested."""
        from app.cli.session import process_mcp_command

        process_mcp_command(
            user_input,
            self.current_model,
            self.current_reasoning,
            self,
        )
