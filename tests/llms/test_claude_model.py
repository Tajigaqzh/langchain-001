from __future__ import annotations

from app.config import load_settings
from app.llms.models.claude import build_claude_llm


def main() -> None:
    """Run a real Claude-compatible model smoke test using local settings."""
    settings = load_settings()
    llm = build_claude_llm(settings)

    response = llm.invoke("请用一句中文回复：Claude 模型已接入成功。")
    print(response.content)


if __name__ == "__main__":
    main()
