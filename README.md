# DeepSeek Agent

这是一个基于 LangChain / LangGraph 的通用 Agent 项目结构，默认使用
DeepSeek 的 OpenAI-compatible API。

## 目录结构

```text
.
├── app
│   ├── agents          # Agent 组装
│   ├── llms            # 模型配置，统一通过 init_chat_model 初始化
│   ├── tools           # Agent 可调用工具
│   └── config.py       # 环境变量配置
├── main.py             # CLI 入口
├── requirements.txt
└── .env.example
```

## 配置

```bash
cp .env.example .env
```

然后填写：

```text
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MODEL_KWARGS={}
CLAUDE_API_KEY=your_claude_api_key
CLAUDE_API_BASE=https://api.anthropic.com
CLAUDE_MODEL=claude-opus-4-6
CLAUDE_MODEL_KWARGS={}
GPT_API_KEY=your_gpt_api_key
GPT_API_BASE=https://api.openai.com/v1
GPT_MODEL=gpt-5.5
GPT_MODEL_KWARGS={}
```

如果使用 shell 环境变量，也可以直接执行：

```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 运行

```bash
conda activate langchain
conda install -y python-dotenv
pip install -r requirements.txt
python main.py
```

当前项目默认使用 conda 环境 `langchain`。如果还没有创建环境，可以先执行：

```bash
conda create -n langchain python=3.13
conda activate langchain
pip install -r requirements.txt
```

## 测试

测试文件统一放在 `tests/` 目录下。

模型连通测试：

```bash
python -m tests.llms.test_deepseek_model
```

Anthropic Claude 连通测试：

```bash
python -m tests.llms.test_claude_model
```

GPT 兼容接口连通测试：

```bash
python -m tests.llms.test_gpt_model
```

staged 文件检查：

```bash
python scripts/check_staged_files.py
```

## 扩展工具

在 `app/tools/basic.py` 中添加新的 `@tool` 函数，然后把它加入
`get_tools()` 返回列表即可。
