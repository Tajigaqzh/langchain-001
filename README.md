# DeepSeek Agent

这是一个基于 LangChain / LangGraph 的通用 Agent 项目结构，默认使用
DeepSeek 的 OpenAI-compatible API。

## 目录结构

```text
.
├── app
│   ├── agents          # Agent 组装
│   ├── llms            # 模型配置
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
python -m tests.test_model
```

staged 文件检查：

```bash
python scripts/check_staged_files.py
```

## 扩展工具

在 `app/tools/basic.py` 中添加新的 `@tool` 函数，然后把它加入
`get_tools()` 返回列表即可。
