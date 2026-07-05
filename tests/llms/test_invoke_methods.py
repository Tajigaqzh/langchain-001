from __future__ import annotations

import asyncio
import pytest
from app.config import load_settings
from app.llms import build_deepseek_llm


def test_invoke():
    """测试同步调用"""
    print("=== 测试 invoke() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    response = llm.invoke("用一句话介绍 Python")
    print(f"回答: {response.content}\n")


def test_stream():
    """测试同步流式调用"""
    print("=== 测试 stream() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    print("回答: ", end="", flush=True)
    for chunk in llm.stream("写一首五言绝句"):
        print(chunk.content, end="", flush=True)
    print("\n")


def test_batch():
    """测试同步批量调用"""
    print("=== 测试 batch() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    prompts = ["1+1=?", "2+2=?", "3+3=?"]
    responses = llm.batch(prompts)

    for prompt, response in zip(prompts, responses):
        print(f"{prompt} → {response.content}")
    print()


@pytest.mark.asyncio
async def test_ainvoke():
    """测试异步调用"""
    print("=== 测试 ainvoke() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    response = await llm.ainvoke("用一句话介绍 JavaScript")
    print(f"回答: {response.content}\n")


@pytest.mark.asyncio
async def test_astream():
    """测试异步流式调用"""
    print("=== 测试 astream() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    print("回答: ", end="", flush=True)
    async for chunk in llm.astream("写一首七言绝句"):
        print(chunk.content, end="", flush=True)
    print("\n")


@pytest.mark.asyncio
async def test_abatch():
    """测试异步批量调用"""
    print("=== 测试 abatch() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    prompts = ["介绍 Go", "介绍 Rust", "介绍 C++"]
    responses = await llm.abatch(prompts)

    for prompt, response in zip(prompts, responses):
        print(f"{prompt} → {response.content[:50]}...")
    print()


def main():
    """运行所有测试"""
    print("开始测试所有模型调用方法...\n")

    # 同步测试
    test_invoke()
    test_stream()
    test_batch()

    # 异步测试
    asyncio.run(test_ainvoke())
    asyncio.run(test_astream())
    asyncio.run(test_abatch())

    print("所有测试完成！")


if __name__ == "__main__":
    main()
