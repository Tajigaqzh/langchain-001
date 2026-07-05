# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个支持多 LLM 提供商（DeepSeek、Claude、GPT）的 LangChain/LangGraph Agent 项目，通过统一的工厂模式管理。默认 Agent 使用 DeepSeek 并配置了可扩展的工具。

## 架构设计

### 多模型工厂模式

项目使用集中式工厂（`app/llms/factory.py`）创建聊天模型：

- `ChatModelSpec`：配置数据类，包含 provider、model、API key、base URL、temperature 和可选的 kwargs
- `ChatModelFactory.create()`：通过 LangChain 的 `init_chat_model()` 创建 `BaseChatModel` 实例
- 特定提供商的构建函数（`build_deepseek_llm`、`build_claude_llm`、`build_gpt_llm`）使用环境配置包装工厂

三个提供商都通过 LangChain 的 OpenAI 或 Anthropic 适配器：
- DeepSeek 和 GPT 使用 `ModelProvider.OPENAI`
- Claude 使用 `ModelProvider.ANTHROPIC`
- Claude 的 base URL 会被规范化以去除尾部 `/v1`（Anthropic SDK 要求）

### 配置层

`app/config.py` 使用 `python-dotenv` 和 dataclass 从 `.env` 加载所有设置：
- 共享的 `DEEPSEEK_TEMPERATURE`（默认 0.2）应用于所有模型
- 每个提供商有：`{PROVIDER}_API_KEY`、`{PROVIDER}_API_BASE`、`{PROVIDER}_MODEL`、`{PROVIDER}_MODEL_KWARGS`
- `MODEL_KWARGS` 字段接受 JSON 对象，用于向 `init_chat_model()` 传递额外参数
- 设置通过 `load_settings()` 加载一次并传递给构建函数

### Agent 构建

`app/agents/deepseek_agent.py` 中的 `build_agent()`：
1. 从环境加载设置
2. 通过工厂创建 DeepSeek LLM
3. 从 `app/tools/get_tools()` 获取工具列表
4. 返回带有模型、工具和系统提示的 `create_agent()`

工具在 `app/tools/basic.py` 中使用 LangChain 的 `@tool` 装饰器定义。当前工具：`current_time`、`calculator`。

## 命令

### 环境设置
```bash
conda activate langchain
pip install -r requirements.txt
```

### 运行 CLI Agent
```bash
python main.py
```

### 测试模型连通性
```bash
python -m tests.llms.test_deepseek_model  # DeepSeek
python -m tests.llms.test_claude_model    # Claude
python -m tests.llms.test_gpt_model       # GPT
python -m tests.agents.test_agent_tools   # Agent 工具集成
```

### 语法检查
```bash
python -m compileall app tests main.py
```

### Staged 文件检查
```bash
python scripts/check_staged_files.py
```

## 开发约定

### 提交信息类型
使用约定式提交类型：`feat`、`fix`、`refactor`、`docs`、`test`、`build`、`chore`、`ci`、`perf`、`style`、`revert`。

### 命名规范
- `snake_case`：模块、函数、变量
- `PascalCase`：类
- `UPPER_SNAKE_CASE`：常量

### 配置
- 业务逻辑中禁止直接读取 `.env`；使用 `app/config.py` 中的 `load_settings()`
- 模型创建必须通过 `app/llms/` 工厂模式
- 保持 `main.py` 薄层；仅处理 CLI 设置和调用

### 工具
- 在 `app/tools/basic.py` 中使用 `@tool` 装饰器添加新工具
- 在 `get_tools()` 返回列表中注册
- 工具应该单一职责明确，并有文档说明输入输出

### 测试
- 所有测试在 `tests/` 目录，使用 `test_*.py` 命名
- 模型连通性测试需要真实 API key，手动运行
- 测试需要覆盖正常和异常场景

### Staged 检查绕过
仅用于 `commented-code` 规则，必须包含原因：
```python
# staged-check-disable-next-line commented-code -- README 示例展示旧方法
# old_code_here
```

### CodeGraph 维护
- 项目已配置 CodeGraph MCP 用于结构化查询
- 在读取文件前，使用 `codegraph_context` 回答"X 如何工作"的问题
- 文件更改后，使用 `codegraph_status` 验证索引是否更新
- 同步：`codegraph sync .`（增量）
- 重建：`codegraph index --force .`（完全重建）
- `.codegraph/` 已 gitignore，禁止提交

## Staged 文件检查

`scripts/check_staged_files.py` 会阻断提交：
- Python 语法错误
- 尝试提交 `.env`、`.pyc`、`__pycache__`、`.idea`、`.codegraph`
- 大块被注释的代码（除非有原因绕过）

警告（不阻断）：
- 文件超过 1000 行
- 函数超过 80 行
- 函数/方法缺少 docstring
