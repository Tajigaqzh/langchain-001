# Repository Guidelines

## Commit 类型参考规范

commit message 的 type 必须从以下类型中选择：

- `build`：构建系统、依赖版本、环境配置相关变更。
- `chore`：不影响业务逻辑的仓库维护变更。
- `ci`：持续集成、发布流程、hook 配置相关变更。
- `docs`：README、AGENTS、注释型说明文档等文档变更。
- `feat`：新增功能或新增用户可见能力。
- `fix`：修复 bug 或纠正错误行为。
- `perf`：性能优化，且不改变既有功能行为。
- `refactor`：代码重构，不新增功能也不修复 bug。
- `revert`：回退之前的提交。
- `style`：格式、空白、命名整理等不影响逻辑的变更。
- `test`：新增或修改测试相关内容。

## 项目结构与模块组织

这是一个 Python LangChain / LangGraph Agent 项目。

- `app/`：应用主包。
- `app/agents/`：Agent 组装入口，例如 DeepSeek ReAct Agent。
- `app/llms/`：模型接入与模型实例创建。
- `app/tools/`：Agent 可调用工具，工具函数应保持小而明确。
- `app/config.py`：环境变量、`.env` 和运行配置读取。
- `main.py`：命令行入口，只负责启动流程，不堆业务逻辑。
- `tests/`：测试文件统一目录，所有测试脚本都放在这里。
- `scripts/`：仓库治理脚本，例如 staged 文件检查。
- `.env.example`：可提交的环境变量示例。
- `.env`：本地密钥文件，必须忽略，禁止提交。

## 本地开发命令

本项目默认使用 conda 环境 `langchain`。

- `conda activate langchain`：进入项目环境。
- `conda install -y python-dotenv`：通过 conda 安装 dotenv 支持。
- `pip install -r requirements.txt`：安装 Python 依赖。
- `python main.py`：启动 CLI Agent。
- `python -m tests.llms.test_deepseek_model`：执行 DeepSeek 模型连通测试。
- `python scripts/check_staged_files.py`：检查本次 staged 文件。
- `python -m compileall app tests main.py`：执行 Python 语法编译检查。

## 编码风格与命名约定

- Python 文件使用 UTF-8 编码。
- 包、模块、函数、变量使用 `snake_case`。
- 类名使用 `PascalCase`。
- 常量使用 `UPPER_SNAKE_CASE`。
- 入口文件保持薄层，只做参数读取、对象组装和流程启动。
- 配置读取集中在 `app/config.py`，不要在业务代码中散落读取 `.env`。
- 模型接入集中在 `app/llms/`，不要在工具函数里直接创建模型实例。
- Agent 可调用工具放在 `app/tools/`，工具函数应有清晰输入输出。
- 避免提交被注释掉的旧代码；确实需要保留示例时，写成文档说明。

## 注释规范

- 方法、函数、工具函数必须加注释，优先使用 docstring 说明用途。
- docstring 至少说明该方法做什么；参数或返回值不直观时，也要说明参数含义和返回结果。
- 复杂流程前可以加少量行内注释，说明为什么这样做，而不是重复代码本身。
- 不要用注释保留废弃代码。需要临时绕过 staged 检查时，必须写明原因。

示例：

```python
def build_deepseek_llm(settings: Settings) -> ChatOpenAI:
    """Create a DeepSeek chat model from project settings."""
    ...
```

## 测试规范

- 测试文件统一放在 `tests/` 目录下。
- 测试脚本命名使用 `test_*.py`。
- 新增或修改模型接入、配置读取、工具函数、Agent 组装时，应补充或更新对应测试。
- 测试应覆盖正常场景、异常场景和关键边界条件，不能只覆盖 happy path。
- 每个测试方法或测试脚本入口必须写注释，说明覆盖的场景。
- 需要真实 API Key 的连通测试应单独运行，不应作为无密钥环境下的默认必跑测试。

## staged 检查与绕过规则

本项目使用 `python scripts/check_staged_files.py` 检查已经 staged 的文件。

检查内容：

- Python 文件语法编译失败会阻断提交。
- `.env`、`.pyc`、`__pycache__`、`.idea`、`.codegraph` 等本地文件进入 staged 会阻断提交。
- 大段疑似被注释掉的代码会阻断提交。
- 单个 staged 文件超过 1000 行只输出警告，不阻断提交。
- 函数或方法超过 80 行只输出警告，提醒拆分。
- 函数或方法缺少 docstring 只输出警告，提醒补充方法注释。

如果用户明确要求保留某一段注释代码，可以使用下一行绕过标记，并必须写明原因：

```python
# staged-check-disable-next-line commented-code -- 文档示例需要展示旧写法
# old_result = agent.invoke({"messages": [("user", "hello")]})
```

也可以使用成对绕过标记：

```python
# staged-check-disable commented-code -- README 示例需要展示多行代码
# def old_demo():
#     return "demo"
# staged-check-enable commented-code
```

绕过标记只允许用于 `commented-code` 规则，不得用于规避语法错误、密钥提交、本地缓存文件提交等硬性问题。

## Agent 提交失败处理规则

- 未经用户明确授权，禁止为了通过检查而主动删除或重写用户代码。
- 执行提交时，如果 staged 检查失败或 commit 失败，必须立即中断提交流程。
- 提交失败总结必须列出失败命令、失败文件、关键错误信息，以及“未修改代码、未完成提交”的状态说明。
- 提交成功或失败都要列出 staged 检查输出的非阻断 warning，便于审计。

## CodeGraph 维护规则

- 本项目配置了 CodeGraph MCP，结构性问题优先使用 CodeGraph 查询。
- 修改、移动或新增少量文件后，优先调用 CodeGraph MCP 的 status/files 能力确认索引是否已同步；如果索引仍旧，自动执行 `codegraph sync .`。
- 新增、移动大量文件，或发现 CodeGraph 仍返回旧文件路径时，自动执行 `codegraph index --force .` 重建索引。
- 执行同步或重建后，再调用 CodeGraph MCP 的 status/files 能力确认索引文件数和文件列表正常。
- 当前 CodeGraph MCP 主要用于查询和确认索引状态；刷新或重建索引使用本地 CLI 命令。
- `.codegraph/` 是本地索引目录，必须保持 git 忽略，不能提交数据库文件。

## 代码修改与验证

- 每次需求改动完毕后，至少执行与变更范围匹配的验证命令。
- 普通 Python 代码改动优先执行 `python -m compileall app tests main.py`。
- 修改模型接入后，可以执行 `python -m tests.llms.test_deepseek_model` 做真实连通测试。
- 修改 staged 检查脚本后，应执行 `python scripts/check_staged_files.py`。
- 不要求每次都执行完整构建或真实 API 连通测试。
