from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from app.config import (
    DEFAULT_AGENT_THREAD_ID,
    DEFAULT_MEMORY_BACKEND,
    DEFAULT_MEMORY_PATH,
    DEFAULT_SQLITE_CACHE_DAYS,
)

DEFAULT_THREAD_ID = DEFAULT_AGENT_THREAD_ID
DEFAULT_MEMORY_DB_PATH = Path(DEFAULT_MEMORY_PATH)
_UUID_EPOCH_OFFSET_100NS = 0x01B21DD213814000
MEMORY_BACKENDS = ("memory", "sqlite")


def build_memory_checkpointer() -> InMemorySaver:
    """Create an in-memory LangGraph checkpointer for one CLI process."""
    return InMemorySaver()


@contextmanager
def open_memory_checkpointer(
    backend: str = DEFAULT_MEMORY_BACKEND,
    sqlite_path: Path | str = DEFAULT_MEMORY_DB_PATH,
    sqlite_cache_days: int = DEFAULT_SQLITE_CACHE_DAYS,
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
        prune_sqlite_checkpoints(checkpointer.conn, sqlite_cache_days)
        yield checkpointer


def checkpoint_id_for_datetime(timestamp: datetime) -> str:
    """Build the lowest UUIDv6 checkpoint id for a timestamp."""
    timestamp_utc = timestamp.astimezone(timezone.utc)
    timestamp_100ns = int(timestamp_utc.timestamp() * 10_000_000) + _UUID_EPOCH_OFFSET_100NS
    time_high_and_time_mid = (timestamp_100ns >> 12) & 0xFFFFFFFFFFFF
    time_low = timestamp_100ns & 0x0FFF
    uuid_int = time_high_and_time_mid << 80
    uuid_int |= 0x6 << 76
    uuid_int |= time_low << 64
    uuid_int |= 0x80 << 56
    return str(UUID(int=uuid_int))


def prune_sqlite_checkpoints(connection: Any, cache_days: int) -> tuple[int, int]:
    """Delete SQLite checkpoint rows older than the configured retention window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=cache_days)
    cutoff_checkpoint_id = checkpoint_id_for_datetime(cutoff)
    old_checkpoints = list(
        connection.execute(
            """
            SELECT thread_id, checkpoint_ns, checkpoint_id
            FROM checkpoints
            WHERE checkpoint_id < ?
            """,
            (cutoff_checkpoint_id,),
        )
    )
    if not old_checkpoints:
        return (0, 0)

    deleted_writes = 0
    for thread_id, checkpoint_ns, checkpoint_id in old_checkpoints:
        cursor = connection.execute(
            """
            DELETE FROM writes
            WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
            """,
            (thread_id, checkpoint_ns, checkpoint_id),
        )
        deleted_writes += cursor.rowcount

    cursor = connection.execute(
        "DELETE FROM checkpoints WHERE checkpoint_id < ?",
        (cutoff_checkpoint_id,),
    )
    deleted_checkpoints = cursor.rowcount
    connection.commit()
    return (deleted_checkpoints, deleted_writes)


def build_thread_config(thread_id: str = DEFAULT_THREAD_ID) -> dict[str, dict[str, Any]]:
    """Build the LangGraph config that selects a short-term memory thread."""
    normalized_thread_id = thread_id.strip() or DEFAULT_THREAD_ID
    return {"configurable": {"thread_id": normalized_thread_id}}
