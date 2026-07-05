# 模型调用方法总结

本文档总结了 LangChain 中调用聊天模型的几种方法及其使用场景。

## 一、调用方法概览

LangChain 的 `BaseChatModel` 提供了多种调用方法：

| 方法 | 类型 | 返回值 | 使用场景 |
|------|------|--------|----------|
| `invoke()` | 同步 | 完整响应 | 简单的单次调用，等待完整结果 |
| `ainvoke()` | 异步 | 完整响应 | 异步环境下的单次调用 |
| `stream()` | 同步 | 流式迭代器 | 需要实时显示生成内容 |
| `astream()` | 异步 | 异步流式迭代器 | 异步环境下的流式输出 |
| `batch()` | 同步 | 批量结果列表 | 批量处理多个请求 |
| `abatch()` | 异步 | 批量结果列表 | 异步环境下的批量处理 |

## 二、invoke() - 同步调用

### 2.1 基本用法

最简单的调用方式，等待模型返回完整结果。

```python
from app.llms import build_deepseek_llm
from app.config import load_settings

settings = load_settings()
llm = build_deepseek_llm(settings)

# 方式 1: 传递字符串
response = llm.invoke("请用一句话介绍你自己")
print(response.content)

# 方式 2: 传递消息列表
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="你是一个友好的助手"),
    HumanMessage(content="你好，介绍一下自己")
]
response = llm.invoke(messages)
print(response.content)
```

### 2.2 响应对象

`invoke()` 返回 `AIMessage` 对象：

```python
response = llm.invoke("你好")

# 访问内容
print(response.content)  # 文本内容

# 访问元数据
print(response.response_metadata)  # 包含 token 使用量、模型名等信息

# 完整响应结构
print(response.dict())
```

### 2.3 传递 config 参数

`invoke()` 除了接收输入内容，还可以接收运行时 `config` 参数。

这个参数通常用于：

- 给本次调用设置 `run_name`
- 添加 `tags`、`metadata` 方便 LangSmith 或日志追踪
- 传递 `callbacks` 挂载回调
- 在可并发执行的 Runnable 中控制运行时行为

```python
from app.llms import build_deepseek_llm
from app.config import load_settings

settings = load_settings()
llm = build_deepseek_llm(settings)

response = llm.invoke(
    "总结一下 LangChain 的 invoke 方法",
    config={
        "run_name": "deepseek_invoke_demo",
        "tags": ["docs", "invoke"],
        "metadata": {
            "feature": "model-call",
            "provider": "deepseek",
        },
    },
)

print(response.content)
```

如果你在链、Agent 或更复杂的 Runnable 组合中调用模型，`config` 会沿调用链继续向下传递，因此很适合做统一追踪。

### 2.4 使用示例

项目中的实际使用（`tests/test_deepseek_model.py`）：

```python
def main() -> None:
    """Run a real DeepSeek model smoke test using local environment settings."""
    settings = load_settings()
    llm = build_deepseek_llm(settings)

    response = llm.invoke("请用一句话介绍你自己")
    print(response.content)
```

### 2.5 适用场景

- ✅ 简单的问答场景
- ✅ 不需要实时反馈的任务
- ✅ 脚本和批处理任务
- ❌ 需要实时显示的 Web 应用
- ❌ 长文本生成（用户会等待较久）

## 三、ainvoke() - 异步调用

### 3.1 基本用法

在异步环境中调用模型，不会阻塞事件循环。

```python
import asyncio
from app.llms import build_deepseek_llm
from app.config import load_settings

async def main():
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    # 异步调用
    response = await llm.ainvoke("请用一句话介绍你自己")
    print(response.content)

# 运行异步函数
asyncio.run(main())
```

### 3.2 并发调用

异步调用的主要优势是可以并发处理多个请求：

```python
import asyncio

async def call_multiple_models():
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    # 并发调用多个问题
    tasks = [
        llm.ainvoke("介绍一下 Python"),
        llm.ainvoke("介绍一下 JavaScript"),
        llm.ainvoke("介绍一下 Go"),
    ]
    
    # 等待所有任务完成
    responses = await asyncio.gather(*tasks)
    
    for i, response in enumerate(responses, 1):
        print(f"回答 {i}: {response.content}\n")

asyncio.run(call_multiple_models())
```

### 3.3 适用场景

- ✅ FastAPI、Sanic 等异步 Web 框架
- ✅ 需要并发处理多个请求
- ✅ 异步任务队列（Celery、Dramatiq）
- ✅ 长时间运行的后台任务

## 四、stream() - 同步流式输出

### 4.1 基本用法

逐块接收模型输出，适合实时显示生成内容。

```python
from app.llms import build_deepseek_llm
from app.config import load_settings

settings = load_settings()
llm = build_deepseek_llm(settings)

# 流式调用
for chunk in llm.stream("写一首关于春天的诗"):
    print(chunk.content, end="", flush=True)  # 实时打印每个块

print()  # 换行
```

### 4.2 处理流式响应

```python
# 收集完整响应
full_response = ""
for chunk in llm.stream("解释一下机器学习"):
    content = chunk.content
    full_response += content
    print(content, end="", flush=True)

print(f"\n\n完整响应长度: {len(full_response)} 字符")
```

### 4.3 实时 Web 应用示例

```python
from flask import Flask, Response

app = Flask(__name__)

@app.route('/chat')
def chat():
    def generate():
        settings = load_settings()
        llm = build_deepseek_llm(settings)
        
        for chunk in llm.stream("介绍一下人工智能的发展历史"):
            yield f"data: {chunk.content}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')
```

### 4.4 适用场景

- ✅ 聊天界面（ChatGPT 风格的逐字显示）
- ✅ 长文本生成（文章、代码、翻译）
- ✅ 提升用户体验（避免长时间等待）
- ✅ Server-Sent Events (SSE) 流式传输

## 五、astream() - 异步流式输出

### 5.1 基本用法

异步环境下的流式输出。

```python
import asyncio
from app.llms import build_deepseek_llm
from app.config import load_settings

async def main():
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    # 异步流式调用
    async for chunk in llm.astream("写一个快速排序算法"):
        print(chunk.content, end="", flush=True)
    
    print()

asyncio.run(main())
```

### 5.2 FastAPI 集成示例

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.llms import build_deepseek_llm
from app.config import load_settings

app = FastAPI()

@app.get("/stream")
async def stream_chat(prompt: str):
    async def generate():
        settings = load_settings()
        llm = build_deepseek_llm(settings)
        
        async for chunk in llm.astream(prompt):
            yield f"data: {chunk.content}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 5.3 并发流式处理

```python
import asyncio

async def stream_multiple():
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    async def stream_one(prompt: str, label: str):
        print(f"\n{label} 开始:")
        async for chunk in llm.astream(prompt):
            print(f"[{label}] {chunk.content}", end="", flush=True)
        print(f"\n{label} 完成")
    
    # 并发流式输出
    await asyncio.gather(
        stream_one("介绍 Python", "任务1"),
        stream_one("介绍 Rust", "任务2"),
    )

asyncio.run(stream_multiple())
```

### 5.4 适用场景

- ✅ FastAPI、Sanic 异步 Web 框架
- ✅ WebSocket 实时通信
- ✅ 异步聊天应用
- ✅ 高并发流式服务

## 六、batch() - 同步批量调用

### 6.1 基本用法

一次性处理多个输入，提高吞吐量。

```python
from app.llms import build_deepseek_llm
from app.config import load_settings

settings = load_settings()
llm = build_deepseek_llm(settings)

# 批量调用
prompts = [
    "1+1等于几？",
    "2+2等于几？",
    "3+3等于几？",
]

responses = llm.batch(prompts)

for prompt, response in zip(prompts, responses):
    print(f"问题: {prompt}")
    print(f"回答: {response.content}\n")
```

### 6.2 批量处理消息列表

```python
from langchain_core.messages import HumanMessage, SystemMessage

# 准备多个对话
conversations = [
    [SystemMessage(content="你是数学助手"), HumanMessage(content="1+1=?")],
    [SystemMessage(content="你是历史助手"), HumanMessage(content="秦朝何时建立？")],
    [SystemMessage(content="你是科技助手"), HumanMessage(content="什么是量子计算？")],
]

responses = llm.batch(conversations)

for i, response in enumerate(responses, 1):
    print(f"对话 {i}: {response.content}\n")
```

### 6.3 配置批量参数

```python
# 设置并发数和其他参数
responses = llm.batch(
    prompts,
    config={
        "max_concurrency": 5,  # 最大并发数
    }
)
```

### 6.4 适用场景

- ✅ 批量数据处理（分类、摘要、翻译）
- ✅ 离线任务（报告生成、内容审核）
- ✅ 数据标注
- ✅ A/B 测试（同时测试多个 prompt）

## 七、abatch() - 异步批量调用

### 7.1 基本用法

异步环境下的批量处理。

```python
import asyncio
from app.llms import build_deepseek_llm
from app.config import load_settings

async def main():
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    prompts = [
        "介绍 Python",
        "介绍 JavaScript",
        "介绍 Go",
    ]
    
    # 异步批量调用
    responses = await llm.abatch(prompts)
    
    for prompt, response in zip(prompts, responses):
        print(f"问题: {prompt}")
        print(f"回答: {response.content}\n")

asyncio.run(main())
```

### 7.2 大规模批量处理

```python
import asyncio

async def process_large_batch():
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    # 准备大量数据
    prompts = [f"生成第 {i} 个标题" for i in range(100)]
    
    # 分批处理
    batch_size = 10
    all_responses = []
    
    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i+batch_size]
        responses = await llm.abatch(batch)
        all_responses.extend(responses)
        print(f"已处理 {len(all_responses)}/{len(prompts)}")
    
    return all_responses

asyncio.run(process_large_batch())
```

### 7.3 适用场景

- ✅ 异步任务队列的批量处理
- ✅ 高并发批量 API 服务
- ✅ 大规模数据处理管道
- ✅ 后台批量任务

## 八、方法对比与选择

### 8.1 同步 vs 异步

| 特性 | 同步方法 | 异步方法 |
|------|----------|----------|
| 阻塞 | 阻塞当前线程 | 不阻塞事件循环 |
| 并发 | 需要多线程/多进程 | 单线程高并发 |
| 适用框架 | Flask, Django | FastAPI, Sanic |
| 代码复杂度 | 简单直观 | 需要理解 async/await |

### 8.2 完整 vs 流式

| 特性 | 完整返回 (invoke) | 流式返回 (stream) |
|------|-------------------|-------------------|
| 响应时间 | 等待完整生成 | 立即开始输出 |
| 用户体验 | 可能等待较久 | 实时反馈更好 |
| 实现复杂度 | 简单 | 需要处理流 |
| 适用场景 | 短文本、API | 长文本、聊天界面 |

### 8.3 单次 vs 批量

| 特性 | 单次调用 | 批量调用 |
|------|----------|----------|
| 效率 | 低（多次网络请求） | 高（复用连接） |
| 内存占用 | 低 | 较高 |
| 适用场景 | 实时交互 | 批量处理 |
| 错误处理 | 单个失败影响小 | 需要处理部分失败 |

### 8.4 选择决策树

```
需要实时显示生成内容？
├─ 是 → 使用 stream() 或 astream()
└─ 否 → 需要处理多个请求？
    ├─ 是 → 批量处理
    │   ├─ 异步环境 → abatch()
    │   └─ 同步环境 → batch()
    └─ 否 → 单次调用
        ├─ 异步环境 → ainvoke()
        └─ 同步环境 → invoke()
```

## 九、完整示例

### 9.1 测试所有调用方法

创建一个测试脚本 `tests/test_invoke_methods.py`：

```python
from __future__ import annotations

import asyncio
from app.config import load_settings
from app.llms import build_deepseek_llm


def test_invoke():
    """测试同步调用"""
    print("=== 测试 invoke() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    response = llm.invoke("用一句话介绍 Python")
    print(f"回答: {response.content}\n")


def test_stream():
    """测试同步流式调用"""
    print("=== 测试 stream() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    print("回答: ", end="", flush=True)
    for chunk in llm.stream("写一首五言绝句"):
        print(chunk.content, end="", flush=True)
    print("\n")


def test_batch():
    """测试同步批量调用"""
    print("=== 测试 batch() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    prompts = ["1+1=?", "2+2=?", "3+3=?"]
    responses = llm.batch(prompts)
    
    for prompt, response in zip(prompts, responses):
        print(f"{prompt} → {response.content}")
    print()


async def test_ainvoke():
    """测试异步调用"""
    print("=== 测试 ainvoke() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    response = await llm.ainvoke("用一句话介绍 JavaScript")
    print(f"回答: {response.content}\n")


async def test_astream():
    """测试异步流式调用"""
    print("=== 测试 astream() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    print("回答: ", end="", flush=True)
    async for chunk in llm.astream("写一首七言绝句"):
        print(chunk.content, end="", flush=True)
    print("\n")


async def test_abatch():
    """测试异步批量调用"""
    print("=== 测试 abatch() ===")
    settings = load_settings()
    llm = build_deepseek_llm(settings)
    
    prompts = ["介绍 Go", "介绍 Rust", "介绍 C++"]
    responses = await llm.abatch(prompts)
    
    for prompt, response in zip(prompts, responses):
        print(f"{prompt} → {response.content[:50]}...")
    print()


def main():
    """运行所有测试"""
    # 同步测试
    test_invoke()
    test_stream()
    test_batch()
    
    # 异步测试
    asyncio.run(test_ainvoke())
    asyncio.run(test_astream())
    asyncio.run(test_abatch())


if __name__ == "__main__":
    main()
```

### 9.2 运行测试

```bash
python -m tests.test_invoke_methods
```

## 十、注意事项与最佳实践

### 10.1 错误处理

```python
from langchain_core.exceptions import LangChainException

try:
    response = llm.invoke("你好")
except LangChainException as e:
    print(f"模型调用失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 10.2 超时设置

```python
# 在创建模型时设置超时
llm = ChatModelFactory.create(
    ChatModelSpec(
        # ... 其他参数
        model_kwargs={"timeout": 30}  # 30 秒超时
    )
)
```

### 10.3 Token 使用量统计

```python
response = llm.invoke("你好")

# 获取 token 使用量
metadata = response.response_metadata
if "token_usage" in metadata:
    usage = metadata["token_usage"]
    print(f"输入 tokens: {usage.get('prompt_tokens')}")
    print(f"输出 tokens: {usage.get('completion_tokens')}")
    print(f"总计 tokens: {usage.get('total_tokens')}")
```

### 10.4 重试机制

```python
# 在创建模型时配置重试
llm = ChatModelFactory.create(
    ChatModelSpec(
        # ... 其他参数
        model_kwargs={"max_retries": 3}  # 最多重试 3 次
    )
)
```

### 10.5 批量处理的错误恢复

```python
def safe_batch_process(llm, prompts):
    """带错误处理的批量调用"""
    results = []
    
    for prompt in prompts:
        try:
            response = llm.invoke(prompt)
            results.append(response.content)
        except Exception as e:
            print(f"处理失败: {prompt}, 错误: {e}")
            results.append(None)  # 或使用默认值
    
    return results
```

## 十一、参考资料

### 官方文档

- **LangChain Chat Models**: https://python.langchain.com/docs/integrations/chat/
- **Runnable Interface**: https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html
- **Streaming**: https://python.langchain.com/docs/how_to/streaming/
- **Async**: https://python.langchain.com/docs/how_to/async/

### 项目代码

- 模型创建: `app/llms/factory.py`
- 基本调用示例: `tests/test_deepseek_model.py`
- Agent 调用示例: `tests/test_agent_tools.py`
