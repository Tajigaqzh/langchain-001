from __future__ import annotations

from app.agents import build_agent


def main() -> None:
    """Test agent tool invocation."""
    agent = build_agent()

    print("=== 测试 1: 时间工具 ===")
    result = agent.invoke({"messages": [("user", "现在几点了？")]})
    answer = result["messages"][-1].content
    print(f"回答: {answer}\n")

    print("=== 测试 2: 计算器工具 ===")
    result = agent.invoke({"messages": [("user", "帮我计算 123 * 456")]})
    answer = result["messages"][-1].content
    print(f"回答: {answer}\n")

    print("=== 测试 3: 混合问题 ===")
    result = agent.invoke({"messages": [("user", "如果我每天工作8小时，30天一共工作多少小时？")]})
    answer = result["messages"][-1].content
    print(f"回答: {answer}\n")


if __name__ == "__main__":
    main()