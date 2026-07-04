from __future__ import annotations

from app.config import load_settings
from app.llms import build_deepseek_llm


def main() -> None:
    """Run a real DeepSeek model smoke test using local environment settings."""
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    response = llm.invoke("请用一句话介绍你自己")
    print(response.content)


if __name__ == "__main__":
    main()
