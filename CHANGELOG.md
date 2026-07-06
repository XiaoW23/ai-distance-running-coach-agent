# Changelog

## [Unreleased] - 2026-07-06

### Fixed

#### 类型安全修复 (`backend/agent.py`)
- **`BaseMessage.content` 联合类型处理**: 新增 `_get_last_text()` 辅助函数，处理 `content` 可能为 `str | list` 的类型问题。`math_node`、`rag_node`、`data_node`、`route_request` 四个节点统一改用此函数获取消息文本，消除 14 个 Pylance 类型检查错误。
- **`ChatOpenAI` 参数更新**: 将已废弃的 `openai_api_key` / `openai_api_base` 替换为新版参数 `api_key` / `base_url`。
- **API Key 空值校验**: 在 `llm_node` 中添加 `DEEPSEEK_API_KEY` 的 `None` 检查，未设置时抛出明确的 `ValueError`，避免运行时隐蔽错误。

#### 类型安全修复 (`backend/main.py`)
- **API Key 空值校验**: `generate_title_async` 中添加 `DEEPSEEK_API_KEY` 的 `None` 检查，并用 `SecretStr` 包装以兼容新版 `langchain-openai` 类型签名。
- **`response.content` 类型处理**: 使用 `str()` 包裹 `response.content`，处理其 `str | list` 联合类型。
- **`RunnableConfig` 类型注解**: 为 `get_history`、`truncate_history`、`delete_messages`、`chat_endpoint` 四个端点的 `config` 变量添加 `: RunnableConfig` 类型注解，消除类型不匹配警告。
- **`inputs` 类型注解**: 为 `chat_endpoint` 中 `astream_events` 的 `inputs` 参数添加 `: dict` 类型注解。

#### 启动脚本修复 (`start.bat`)
- **虚拟环境激活**: 在脚本开头添加 `call .venv\Scripts\activate.bat`，解决直接运行时找不到 `pip` 和 `uvicorn` 的问题（`'uvicorn' 不是内部或外部命令`）。
- **环境故障提示**: 添加虚拟环境不存在的检测和中文错误提示。

### Known Issues
- Pylance 对 `langchain-openai` 新版 `ChatOpenAI.__init__` 的参数检查存在误报（`model`、`api_key`、`base_url`、`temperature` 被误判为不存在），这是因为该类使用 `**kwargs` 动态传参，运行时完全正常，属于第三方库类型桩不完整问题。
