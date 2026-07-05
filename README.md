# LangChain Multi-Provider Agent

这是一个基于 LangChain / LangGraph 的多提供商 Agent 项目，支持 DeepSeek、Claude、GPT 等多个 LLM 提供商，采用统一的工厂模式和注册表管理。

## 特性

- **多提供商支持**：通过统一接口支持 DeepSeek、Claude、GPT
- **工厂模式**：集中式 LLM 和 Agent 创建
- **注册表管理**：动态 Agent 注册和查找
- **模块化工具**：按功能分类的工具集（文件系统、Git、网络、Python、Shell、Web）
- **灵活配置**：基于环境变量的配置管理

## 目录结构

```text
.
├── app
│   ├── agents          # Agent 管理
│   │   ├── factory.py       # Agent 工厂
│   │   ├── registry.py      # Agent 注册表
│   │   ├── models/          # 各提供商的 Agent 实现
│   │   │   ├── deepseek.py
│   │   │   ├── claude.py
│   │   │   └── gpt.py
│   │   └── __init__.py
│   ├── llms            # LLM 模型管理
│   │   ├── client.py        # 统一客户端接口
│   │   ├── factory.py       # LLM 工厂
│   │   ├── models/          # 各提供商的模型配置
│   │   │   ├── deepseek.py
│   │   │   ├── claude.py
│   │   │   └── gpt.py
│   │   └── __init__.py
│   ├── tools           # Agent 工具集
│   │   ├── common.py        # 通用工具（时间、计算器等）
│   │   ├── filesystem.py    # 文件系统操作
│   │   ├── git_tools.py     # Git 操作
│   │   ├── network_tools.py # 网络工具
│   │   ├── python_tools.py  # Python 执行
│   │   ├── shell_tools.py   # Shell 命令
│   │   ├── web_tools.py     # Web 搜索与抓取
│   │   ├── utility.py       # 实用工具
│   │   └── __init__.py
│   ├── messages        # 消息构建
│   │   ├── builders.py      # 消息构建器
│   │   └── __init__.py
│   └── config.py       # 配置管理
├── docs                # 文档
│   ├── 01_model_init.md
│   └── 02_model_invoke.md
├── tests               # 测试
│   ├── agents/
│   ├── llms/
│   └── tools/
├── scripts             # 辅助脚本
│   └── check_staged_files.py
├── main.py             # CLI 入口
├── requirements.txt
├── .env.example
└── CLAUDE.md           # 项目开发指南
```

## 快速开始

### 1. 配置环境

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写你需要使用的提供商的 API 密钥：

```bash
# DeepSeek 配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.2
DEEPSEEK_MODEL_KWARGS={}

# Claude 配置
CLAUDE_API_KEY=your_claude_api_key
CLAUDE_API_BASE=https://api.anthropic.com
CLAUDE_MODEL=claude-opus-4-8
CLAUDE_MODEL_KWARGS={}

# GPT 配置
GPT_API_KEY=your_gpt_api_key
GPT_API_BASE=https://api.openai.com/v1
GPT_MODEL=gpt-5.5
GPT_MODEL_KWARGS={}
```

也可以直接使用环境变量：

```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 2. 安装依赖

```bash
# 创建 conda 环境（如果还没有）
conda create -n langchain python=3.13
conda activate langchain

# 安装依赖
pip install -r requirements.txt
```

### 3. 运行 Agent

```bash
python main.py
```

默认使用 DeepSeek Agent。可以通过修改 `main.py` 切换提供商。

## 架构说明

### LLM 工厂模式

项目使用集中式工厂创建 LLM 实例：

```python
from app.llms.factory import ChatModelFactory, ChatModelSpec
from langchain_core.language_models import ModelProvider

# 创建 DeepSeek 模型
spec = ChatModelSpec(
    provider=ModelProvider.OPENAI,
    model="deepseek-chat",
    api_key="your_key",
    base_url="https://api.deepseek.com"
)
llm = ChatModelFactory.create(spec)
```

也可以使用便捷函数：

```python
from app.llms.models.deepseek import build_deepseek_llm
from app.llms.models.claude import build_claude_llm
from app.llms.models.gpt import build_gpt_llm

llm = build_deepseek_llm()  # 自动从环境变量加载配置
```

### Agent 注册表

Agent 使用注册表模式管理：

```python
from app.agents.registry import agent_registry

# 获取 Agent
agent = agent_registry.get("deepseek")  # 或 "claude", "gpt"

# 运行 Agent
result = agent.invoke({"messages": [{"role": "user", "content": "你好"}]})
```

### 工具系统

工具按功能分类，使用 LangChain 的 `@tool` 装饰器：

```python
from app.tools import get_all_tools

# 获取所有工具
tools = get_all_tools()

# 获取特定类别的工具
from app.tools.filesystem import list_directory, read_file
from app.tools.common import current_time, calculator
```

## 测试

### 模型连通性测试

```bash
# DeepSeek
python -m tests.llms.test_deepseek_model

# Claude
python -m tests.llms.test_claude_model

# GPT
python -m tests.llms.test_gpt_model
```

### Agent 工具测试

```bash
python -m tests.agents.test_agent_tools
```

### Staged 文件检查

```bash
python scripts/check_staged_files.py
```

此脚本会检查：
- Python 语法错误
- 敏感文件（`.env`, `.pyc`, `__pycache__`, `.idea`, `.codegraph`）
- 大块注释代码
- 文件和函数大小警告

## 开发指南

### 添加新工具

1. 在对应的工具文件中添加 `@tool` 函数（如 `app/tools/utility.py`）
2. 在 `app/tools/__init__.py` 的 `get_all_tools()` 中注册
3. 编写测试

示例：

```python
from langchain_core.tools import tool

@tool
def my_new_tool(param: str) -> str:
    """工具描述，Agent 会看到这个描述。
    
    Args:
        param: 参数说明
        
    Returns:
        返回值说明
    """
    return f"Result: {param}"
```

### 添加新 Agent 提供商

1. 在 `app/llms/models/` 创建新的 LLM 配置文件
2. 在 `app/agents/models/` 创建新的 Agent 实现
3. 在 `app/agents/registry.py` 中注册
4. 添加对应的测试

### 代码规范

- 命名：`snake_case`（函数/变量）、`PascalCase`（类）、`UPPER_SNAKE_CASE`（常量）
- 提交信息：使用约定式提交（`feat:`, `fix:`, `refactor:`, `docs:` 等）
- 配置：必须通过 `app/config.py`，禁止直接读取 `.env`
- 测试：所有新功能需要测试覆盖

详细开发规范见 `CLAUDE.md`。

## 文档

- [`docs/01_model_init.md`](docs/01_model_init.md) - 模型初始化指南
- [`docs/02_model_invoke.md`](docs/02_model_invoke.md) - 模型调用方法
- [`CLAUDE.md`](CLAUDE.md) - 完整的项目开发指南

## License

MIT
