from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.config import Settings


class BaseChatModelClient(ABC):
    """Shared invoke helpers for project chat models."""

    def __init__(self, settings: Settings) -> None:
        """Store settings for deferred model construction."""
        self.settings = settings
        self._llm: BaseChatModel | None = None

    @abstractmethod
    def _build_llm(self) -> BaseChatModel:
        """Build the concrete chat model instance."""

    @property
    def llm(self) -> BaseChatModel:
        """Return a cached chat model instance."""
        if self._llm is None:
            self._llm = self._build_llm()
        return self._llm

    def invoke(
        self,
        input_data: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        """Run a synchronous single-turn invocation."""
        return self.llm.invoke(input_data, config=config, **kwargs)

    async def ainvoke(
        self,
        input_data: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AIMessage:
        """Run an asynchronous single-turn invocation."""
        return await self.llm.ainvoke(input_data, config=config, **kwargs)

    def stream(
        self,
        input_data: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ):
        """Stream synchronous response chunks from the model."""
        return self.llm.stream(input_data, config=config, **kwargs)

    def astream(
        self,
        input_data: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ):
        """Stream asynchronous response chunks from the model."""
        return self.llm.astream(input_data, config=config, **kwargs)

    def batch(
        self,
        inputs: list[Any],
        config: RunnableConfig | list[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Any,
    ) -> list[AIMessage]:
        """Run synchronous batch model invocations."""
        return self.llm.batch(
            inputs,
            config=config,
            return_exceptions=return_exceptions,
            **kwargs,
        )

    async def abatch(
        self,
        inputs: list[Any],
        config: RunnableConfig | list[RunnableConfig] | None = None,
        *,
        return_exceptions: bool = False,
        **kwargs: Any,
    ) -> list[AIMessage]:
        """Run asynchronous batch model invocations."""
        return await self.llm.abatch(
            inputs,
            config=config,
            return_exceptions=return_exceptions,
            **kwargs,
        )
