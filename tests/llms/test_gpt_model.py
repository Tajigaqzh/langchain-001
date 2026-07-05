from __future__ import annotations

from app.config import load_settings
from app.llms.models.gpt import build_gpt_llm


def main() -> None:
    """Run a real OpenAI-compatible GPT smoke test using local settings."""
    settings = load_settings()
    llm = build_gpt_llm(settings)

    response = llm.invoke("请用一句中文回复：GPT 模型已接入成功。")
    print(response.content)


if __name__ == "__main__":
    main()
