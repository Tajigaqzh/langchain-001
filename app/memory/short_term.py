from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

DEFAULT_THREAD_ID = "default"
DEFAULT_MEMORY_BACKEND = "sqlite"
DEFAULT_MEMORY_DB_PATH = Path(".data/agent_memory.sqlite")
MEMORY_BACKENDS = ("memory", "sqlite")


def build_memory_checkpointer() -> InMemorySaver:
    """Create an in-memory LangGraph checkpointer for one CLI process."""
    return InMemorySaver()


@contextmanager
def open_memory_checkpointer(
    backend: str = DEFAULT_MEMORY_BACKEND,
    sqlite_path: Path | str = DEFAULT_MEMORY_DB_PATH,
) -> Iterator[Any]:
    """Open a LangGraph checkpointer for the selected short-term memory backend."""
    normalized_backend = backend.strip().lower()
    if normalized_backend == "memory":
        yield build_memory_checkpointer()
        return
    if normalized_backend != "sqlite":
        supported = ", ".join(MEMORY_BACKENDS)
        raise ValueError(f"Unsupported memory backend: {backend}. Supported: {supported}")

    db_path = Path(sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        checkpointer.setup()
        yield checkpointer


def build_thread_config(thread_id: str = DEFAULT_THREAD_ID) -> dict[str, dict[str, Any]]:
    """Build the LangGraph config that selects a short-term memory thread."""
    normalized_thread_id = thread_id.strip() or DEFAULT_THREAD_ID
    return {"configurable": {"thread_id": normalized_thread_id}}
