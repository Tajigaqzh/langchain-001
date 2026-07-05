# 模型初始化方法总结

本文档总结了 LangChain 中创建聊天模型的几种写法及注意事项。

## 一、当前推荐方法：统一工厂模式

### 1.1 核心思路

使用 LangChain 的 `init_chat_model()` 函数 + 工厂模式，实现统一的模型创建接口。

### 1.2 实现代码

**工厂类定义** (`app/llms/factory.py`)：

```python
from langchain.chat_models import init_chat_model
from pydantic import SecretStr

class ChatModelFactory:
    """Factory for creating chat models through LangChain init_chat_model."""

    @staticmethod
    def create(spec: ChatModelSpec) -> BaseChatModel:
        """Create a chat model from a provider-specific model spec."""
        if not spec.api_key:
            raise RuntimeError(f"Missing API key for {spec.provider.value} model.")

        custom_fields = spec.model_kwargs or {}

        return init_chat_model(
            model=spec.model,
            model_provider=spec.provider.value,
            api_key=SecretStr(spec.api_key),
            base_url=spec.base_url,
            temperature=spec.temperature,
            **custom_fields,
        )
```

**配置规格** (`app/llms/factory.py`)：

```python
from enum import Enum
from dataclasses import dataclass

class ModelProvider(str, Enum):
    """Supported LangChain chat model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

@dataclass
class ChatModelSpec:
    """Configuration needed to initialize a chat model."""
    provider: ModelProvider
    model: str
    api_key: str
    base_url: str
    temperature: float
    model_kwargs: dict[str, Any] | None = None
```

### 1.3 使用示例

**DeepSeek 模型**：

```python
def build_deepseek_llm(settings: Settings) -> BaseChatModel:
    """Create a DeepSeek chat model from project settings."""
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.OPENAI,  # DeepSeek 使用 OpenAI 兼容接口
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=settings.temperature,
            model_kwargs=settings.deepseek_model_kwargs,
        )
    )
```

**Claude 模型**：

```python
def build_claude_llm(settings: Settings) -> BaseChatModel:
    """Create an Anthropic Claude chat model from project settings."""
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.ANTHROPIC,
            model=settings.claude_model,
            api_key=settings.claude_api_key,
            base_url=normalize_anthropic_base_url(settings.claude_base_url),
            temperature=settings.temperature,
            model_kwargs=settings.claude_model_kwargs,
        )
    )
```

**GPT 模型**：

```python
def build_gpt_llm(settings: Settings) -> BaseChatModel:
    """Create an OpenAI-compatible GPT chat model from project settings."""
    return ChatModelFactory.create(
        ChatModelSpec(
            provider=ModelProvider.OPENAI,
            model=settings.gpt_model,
            api_key=settings.gpt_api_key,
            base_url=settings.gpt_base_url,
            temperature=settings.temperature,
            model_kwargs=settings.gpt_model_kwargs,
        )
    )
```

### 1.4 优点

- **统一接口**：所有模型通过同一个工厂创建，易于维护
- **类型安全**：使用 `ChatModelSpec` 数据类和枚举保证参数正确
- **可扩展**：通过 `model_kwargs` 传递额外参数
- **自动适配**：`init_chat_model()` 根据 provider 自动选择对应的实现类

## 二、传统方法：直接实例化

### 2.1 OpenAI 兼容模型（DeepSeek、GPT）

```python
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

deepseek_llm = ChatOpenAI(
    model=settings.deepseek_model,
    api_key=SecretStr(settings.deepseek_api_key),
    base_url=settings.deepseek_base_url,
    temperature=settings.temperature,
)

gpt_llm = ChatOpenAI(
    model=settings.gpt_model,
    api_key=SecretStr(settings.gpt_api_key),
    base_url=settings.gpt_base_url,
    temperature=settings.temperature,
)
```

### 2.2 Claude 模型

```python
from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr

claude_llm = ChatAnthropic(
    model_name=settings.claude_model,  # 注意：这里是 model_name，不是 model
    api_key=SecretStr(settings.claude_api_key),
    base_url=normalize_anthropic_base_url(settings.claude_base_url),
    temperature=settings.temperature,
)
```

### 2.3 缺点

- 不同提供商的 API 不一致（如 `model` vs `model_name`）
- 需要手动导入不同的类
- 添加新模型需要修改多处代码
- 难以统一管理和测试

## 三、关键注意事项

### 3.1 API Key 安全

✅ **正确做法**：使用 `SecretStr` 包装 API Key

```python
from pydantic import SecretStr

api_key=SecretStr(settings.api_key)
```

❌ **错误做法**：直接传递字符串

```python
api_key=settings.api_key  # 可能在日志中泄露
```

### 3.2 Anthropic Base URL 规范化

Anthropic SDK 不接受带 `/v1` 后缀的 base URL，需要规范化：

```python
def normalize_anthropic_base_url(base_url: str) -> str:
    """Return an Anthropic SDK base URL without a duplicated /v1 path."""
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized.removesuffix("/v1")
    return normalized
```

**示例**：
- 输入：`https://api.anthropic.com/v1`
- 输出：`https://api.anthropic.com`

### 3.3 Provider 选择

| 模型 | Provider | 说明 |
|------|----------|------|
| DeepSeek | `ModelProvider.OPENAI` | 使用 OpenAI 兼容接口 |
| GPT | `ModelProvider.OPENAI` | OpenAI 官方接口 |
| Claude | `ModelProvider.ANTHROPIC` | Anthropic 官方接口 |

### 3.4 模型额外参数

通过 `model_kwargs` 传递特定模型的额外参数：

**环境变量配置** (`.env`)：

```bash
DEEPSEEK_MODEL_KWARGS={"max_retries": 3, "timeout": 60}
CLAUDE_MODEL_KWARGS={"max_tokens": 4096}
```

**代码使用**：

```python
ChatModelFactory.create(
    ChatModelSpec(
        # ... 其他参数
        model_kwargs=settings.deepseek_model_kwargs,  # 自动展开传递
    )
)
```

### 3.5 默认配置

在 `app/config.py` 中定义默认值：

```python
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_CLAUDE_BASE_URL = "https://api.anthropic.com"
DEFAULT_CLAUDE_MODEL = "claude-opus-4-6"
DEFAULT_GPT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_GPT_MODEL = "gpt-5.5"
DEFAULT_TEMPERATURE = 0.2
```

### 3.6 错误处理

工厂模式在创建前验证必需参数：

```python
if not spec.api_key:
    raise RuntimeError(f"Missing API key for {spec.provider.value} model.")
```

这样可以在启动时立即发现配置问题，而不是在运行时才报错。

## 四、最佳实践

### 4.1 配置管理

- 使用 `pydantic-settings` 从 `.env` 加载配置
- 统一通过 `load_settings()` 获取配置
- 禁止在业务代码中直接读取环境变量

### 4.2 模型创建

- 使用工厂模式统一创建
- 特定提供商的逻辑封装在 `build_xxx_llm()` 函数中
- 保持工厂方法纯粹，只做参数组装和调用

### 4.3 测试

为每个模型提供独立的连通性测试：

```python
def main() -> None:
    """Run a real DeepSeek model smoke test using local environment settings."""
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    response = llm.invoke("请用一句话介绍你自己")
    print(response.content)
```

## 五、迁移指南

### 从直接实例化迁移到工厂模式

**旧代码**：

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="deepseek-chat", api_key=SecretStr(key), ...)
```

**新代码**：

```python
from app.llms import build_deepseek_llm
from app.config import load_settings

settings = load_settings()
llm = build_deepseek_llm(settings)
```

### 优势

1. 配置集中管理
2. 无需关心具体实现类
3. 统一的错误处理
4. 易于测试和模拟

## 六、常用模型服务平台

### 6.1 官方平台

| 平台 | 链接 | 说明 |
|------|------|------|
| OpenAI | https://platform.openai.com | OpenAI 官方平台，提供 GPT 系列模型 |
| Anthropic | https://console.anthropic.com | Anthropic 官方平台，提供 Claude 系列模型 |
| DeepSeek | https://platform.deepseek.com | DeepSeek 官方平台，提供 DeepSeek 系列模型 |

### 6.2 聚合平台

| 平台 | 链接 | 说明 |
|------|------|------|
| OpenRouter | https://openrouter.ai | 多模型聚合平台，一个 API 访问多家模型提供商 |
| CloseAI | https://platform.closeai-asia.com | 亚洲区 OpenAI 兼容服务，提供多种模型访问 |
| 阿里云百炼 | https://bailian.console.aliyun.com | 阿里云大模型服务平台，提供通义千问等模型 |

### 6.3 使用聚合平台的配置示例

**OpenRouter 配置**：

```bash
# .env
GPT_API_KEY=your_openrouter_api_key
GPT_API_BASE=https://openrouter.ai/api/v1
GPT_MODEL=openai/gpt-4
```

**CloseAI 配置**：

```bash
# .env
GPT_API_KEY=your_closeai_api_key
GPT_API_BASE=https://api.closeai-asia.com/v1
GPT_MODEL=gpt-4
```

**阿里云百炼配置**：

```bash
# .env
GPT_API_KEY=your_aliyun_api_key
GPT_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
GPT_MODEL=qwen-max
```

### 6.4 聚合平台优势

1. **统一接口**：使用 OpenAI 兼容的 API 格式
2. **模型切换**：只需修改 `base_url` 和 `model` 即可切换不同提供商
3. **负载均衡**：部分平台支持自动负载均衡和故障转移
4. **成本优化**：可以根据价格和性能选择最优模型

## 七、参考资料

### 官方文档

- **LangChain 官网**：https://www.langchain.com
- **LangChain Python 文档**：https://python.langchain.com
- **LangChain Chat Models**：https://python.langchain.com/docs/integrations/chat/
- **init_chat_model() 文档**：https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html

### 项目代码

- 工厂模式实现：`app/llms/factory.py`
- 配置管理：`app/config.py`
- 旧写法参考：`app/llms/legacy_examples.py`
- DeepSeek 构建器：`app/llms/deepseek.py`
- Claude 构建器：`app/llms/claude.py`
- GPT 构建器：`app/llms/gpt.py`