from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator

import pytest
from langchain_core.messages import AIMessage

from app.config import Settings, load_settings
from app.llms.client import BaseChatModelClient
from app.llms.models.deepseek import DeepSeekChatClient


class FakeChatModel:
    """Test double that records all delegated chat model calls."""

    def __init__(self) -> None:
        """Initialize call history for each supported method."""
        self.calls: list[tuple[str, object, object, dict[str, object]]] = []

    def invoke(self, input_data, config=None, **kwargs):
        """Record a synchronous single-turn invocation."""
        self.calls.append(("invoke", input_data, config, kwargs))
        return AIMessage(content=f"invoke:{input_data}")

    async def ainvoke(self, input_data, config=None, **kwargs):
        """Record an asynchronous single-turn invocation."""
        self.calls.append(("ainvoke", input_data, config, kwargs))
        return AIMessage(content=f"ainvoke:{input_data}")

    def stream(self, input_data, config=None, **kwargs) -> Iterator[AIMessage]:
        """Record a synchronous streaming invocation."""
        self.calls.append(("stream", input_data, config, kwargs))
        yield AIMessage(content="stream:")
        yield AIMessage(content=str(input_data))

    async def astream(
        self, input_data, config=None, **kwargs
    ) -> AsyncIterator[AIMessage]:
        """Record an asynchronous streaming invocation."""
        self.calls.append(("astream", input_data, config, kwargs))
        yield AIMessage(content="astream:")
        yield AIMessage(content=str(input_data))

    def batch(self, inputs, config=None, return_exceptions=False, **kwargs):
        """Record a synchronous batch invocation."""
        self.calls.append(
            (
                "batch",
                inputs,
                config,
                {
                    "return_exceptions": return_exceptions,
                    **kwargs,
                },
            )
        )
        return [AIMessage(content=f"batch:{item}") for item in inputs]

    async def abatch(self, inputs, config=None, return_exceptions=False, **kwargs):
        """Record an asynchronous batch invocation."""
        self.calls.append(
            (
                "abatch",
                inputs,
                config,
                {
                    "return_exceptions": return_exceptions,
                    **kwargs,
                },
            )
        )
        return [AIMessage(content=f"abatch:{item}") for item in inputs]


class FakeChatClient(BaseChatModelClient):
    """Concrete test client for verifying shared delegation behavior."""

    def __init__(self) -> None:
        """Initialize the client with empty test settings."""
        super().__init__(Settings(deepseek_api_key="test-key"))
        self.fake_llm = FakeChatModel()

    def _build_llm(self):
        """Return the fake chat model used by the tests."""
        return self.fake_llm


def test_invoke() -> None:
    """测试同步调用会通过客户端抽象层执行。"""
    print("=== 测试 invoke() ===")
    settings = load_settings()
    client = DeepSeekChatClient(settings)

    response = client.invoke("用一句话介绍 Python")
    print(f"回答: {response.content}\n")


def test_stream() -> None:
    """测试同步流式调用会通过客户端抽象层执行。"""
    print("=== 测试 stream() ===")
    settings = load_settings()
    client = DeepSeekChatClient(settings)

    print("回答: ", end="", flush=True)
    for chunk in client.stream("写一首五言绝句"):
        print(chunk.content, end="", flush=True)
    print("\n")


def test_batch() -> None:
    """测试同步批量调用会通过客户端抽象层执行。"""
    print("=== 测试 batch() ===")
    settings = load_settings()
    client = DeepSeekChatClient(settings)

    prompts = ["1+1=?", "2+2=?", "3+3=?"]
    responses = client.batch(prompts)

    for prompt, response in zip(prompts, responses):
        print(f"{prompt} → {response.content}")
    print()


@pytest.mark.asyncio
async def test_ainvoke() -> None:
    """测试异步调用会通过客户端抽象层执行。"""
    print("=== 测试 ainvoke() ===")
    settings = load_settings()
    client = DeepSeekChatClient(settings)

    response = await client.ainvoke("用一句话介绍 JavaScript")
    print(f"回答: {response.content}\n")


@pytest.mark.asyncio
async def test_astream() -> None:
    """测试异步流式调用会通过客户端抽象层执行。"""
    print("=== 测试 astream() ===")
    settings = load_settings()
    client = DeepSeekChatClient(settings)

    print("回答: ", end="", flush=True)
    async for chunk in client.astream("写一首七言绝句"):
        print(chunk.content, end="", flush=True)
    print("\n")


@pytest.mark.asyncio
async def test_abatch() -> None:
    """测试异步批量调用会通过客户端抽象层执行。"""
    print("=== 测试 abatch() ===")
    settings = load_settings()
    client = DeepSeekChatClient(settings)

    prompts = ["介绍 Go", "介绍 Rust", "介绍 C++"]
    responses = await client.abatch(prompts)

    for prompt, response in zip(prompts, responses):
        print(f"{prompt} → {response.content[:50]}...")
    print()


def test_base_client_delegates_sync_methods() -> None:
    """测试抽象客户端会把同步方法委托给底层模型实例。"""
    client = FakeChatClient()

    invoke_response = client.invoke("hello", config={"run_name": "sync"})
    stream_response = "".join(chunk.content for chunk in client.stream("poem"))
    batch_response = client.batch(["a", "b"], config={"max_concurrency": 2})

    assert invoke_response.content == "invoke:hello"
    assert stream_response == "stream:poem"
    assert [item.content for item in batch_response] == ["batch:a", "batch:b"]
    assert [call[0] for call in client.fake_llm.calls] == ["invoke", "stream", "batch"]


@pytest.mark.asyncio
async def test_base_client_delegates_async_methods() -> None:
    """测试抽象客户端会把异步方法委托给底层模型实例。"""
    client = FakeChatClient()

    ainvoke_response = await client.ainvoke("hello", config={"run_name": "async"})
    astream_chunks = [chunk.content async for chunk in client.astream("story")]
    abatch_response = await client.abatch(
        ["x", "y"],
        config={"max_concurrency": 2},
        return_exceptions=True,
    )

    assert ainvoke_response.content == "ainvoke:hello"
    assert "".join(astream_chunks) == "astream:story"
    assert [item.content for item in abatch_response] == ["abatch:x", "abatch:y"]
    assert [call[0] for call in client.fake_llm.calls] == [
        "ainvoke",
        "astream",
        "abatch",
    ]


def main() -> None:
    """运行所有真实调用测试。"""
    print("开始测试所有模型调用方法...\n")

    test_invoke()
    test_stream()
    test_batch()
    asyncio.run(test_ainvoke())
    asyncio.run(test_astream())
    asyncio.run(test_abatch())

    print("所有测试完成！")


if __name__ == "__main__":
    main()
