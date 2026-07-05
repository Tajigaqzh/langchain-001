from __future__ import annotations

import sqlite3

from app.agents import registry
from app.config import Settings
from app.memory import DEFAULT_THREAD_ID, build_thread_config, open_memory_checkpointer


def test_build_thread_config_uses_normalized_thread_id() -> None:
    """Verify LangGraph thread config keeps short-term memory in the selected thread."""
    assert build_thread_config(" user-1 ") == {
        "configurable": {"thread_id": "user-1"}
    }
    assert build_thread_config("   ") == {
        "configurable": {"thread_id": DEFAULT_THREAD_ID}
    }


def test_open_memory_checkpointer_initializes_sqlite_database(tmp_path) -> None:
    """Verify SQLite short-term memory creates the local checkpoint database."""
    db_path = tmp_path / "memory.sqlite"

    with open_memory_checkpointer("sqlite", db_path) as checkpointer:
        assert checkpointer is not None

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {"checkpoints", "writes"}.issubset(tables)


def test_build_agent_for_model_passes_checkpointer(monkeypatch) -> None:
    """Verify model selection reuses the same LangGraph checkpointer."""
    captured = {}
    settings = Settings(deepseek_api_key="test-key")
    checkpointer = object()
    expected_agent = object()

    def fake_build_deepseek_agent(settings=None, checkpointer=None):
        """Capture the arguments passed by the model registry."""
        captured["settings"] = settings
        captured["checkpointer"] = checkpointer
        return expected_agent

    monkeypatch.setattr(registry, "build_deepseek_agent", fake_build_deepseek_agent)

    agent = registry.build_agent_for_model(
        "deepseek",
        settings,
        checkpointer=checkpointer,
    )

    assert agent is expected_agent
    assert captured == {
        "settings": settings,
        "checkpointer": checkpointer,
    }
