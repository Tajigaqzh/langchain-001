"""Reference notes for legacy direct model initialization styles."""

# The project now uses ChatModelFactory with LangChain init_chat_model.
# The examples below document the previous direct initialization style only.

# staged-check-disable commented-code -- 保留历史调用方式示例，便于对比 init_chat_model 工厂封装
# from langchain_anthropic import ChatAnthropic
# from langchain_openai import ChatOpenAI
# from pydantic import SecretStr
#
# deepseek_llm = ChatOpenAI(
#     model=settings.deepseek_model,
#     api_key=SecretStr(settings.deepseek_api_key),
#     base_url=settings.deepseek_base_url,
#     temperature=settings.temperature,
# )
#
# gpt_llm = ChatOpenAI(
#     model=settings.gpt_model,
#     api_key=SecretStr(settings.gpt_api_key),
#     base_url=settings.gpt_base_url,
#     temperature=settings.temperature,
# )
#
# claude_llm = ChatAnthropic(
#     model_name=settings.claude_model,
#     api_key=SecretStr(settings.claude_api_key),
#     base_url=normalize_anthropic_base_url(settings.claude_base_url),
#     temperature=settings.temperature,
# )
# staged-check-enable commented-code
