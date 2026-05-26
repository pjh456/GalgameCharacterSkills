# llm.providers.py 设计文档

### 设计原因

net 模块提供了完整的 HTTP 能力（请求发送、重试、错误映射），但每个 AI API 的请求体和响应体格式不同。直接让上层模块（executor）处理这些差异会导致每个调用点都需要知道目标 API 的格式细节。

选择 Provider 抽象而非引入第三方库（如 LiteLLM、openai-python）的原因：
- net 模块已处理 HTTP 层，额外引入只会增加依赖和抽象层重叠
- 后续可能有本地模型或非标准兼容接口，它们不完全遵循任何官方 SDK 的路由
- 项目中已存在 `ChatCompletionRequest` / `ChatCompletion` 作为唯一的请求/响应规范，Provider 只需要在这两者与外部格式之间做双向翻译

### 设计目标

`BaseProvider` Protocol 定义四个方法，构成完整的请求/响应翻译合约：

- **`chat_path(config)`** — 返回完整的请求地址，内部调用 `_dedup_path` 处理 `base_url` 与路径中版本前缀的重复拼接
- **`chat_headers(config)`** — 返回 HTTP 请求头，至少包含鉴权与内容类型
- **`build_chat_request(request)`** — 将 `ChatCompletionRequest` 翻译为该 API 的请求体字典
- **`parse_chat_response(data, url)`** — 将该 API 返回的 JSON 数据解析为 `ChatCompletion`

文档注释放基类，子类不重复。新增 provider 只需实现四个方法，不需要写文档。

### _dedup_path 容错

用户可能将 API 地址配置为 `https://api.openai.com` 或 `https://api.openai.com/v1`。Provider 内部固定路径为 `/v1/chat/completions`。`_dedup_path` 在拼接时检查 `base_url` 是否已以版本前缀结尾——若是则截断后再拼接，避免产生 `/v1/v1/chat/completions`：

| `base_url` | Provider 路径 | 结果 |
|---|---|---|
| `https://api.openai.com` | `/v1/chat/completions` | `https://api.openai.com/v1/chat/completions` |
| `https://api.openai.com/v1` | `/v1/chat/completions` | `https://api.openai.com/v1/chat/completions` |
| `https://api.openai.com/v1/` | `/v1/chat/completions` | `https://api.openai.com/v1/chat/completions` |

每个 Provider 在调用 `_dedup_path` 时显式传入自己的 `version_prefix`——无全局常量，逻辑随 Provider 走。

### ChatCompletionRequest 设计

与 `ChatCompletion` 对称。不在 `LlmClient` 中用裸字典构造请求体，而是声明为不可变数据类，通过 `to_dict()` 序列化。`TokenUsage` / `ChatChoice` / `ChatMessage` 全部支持 `from_dict` + 字段校验，形成从 API 原始 JSON 到 `ChatCompletion` 的完整链路。

### 不采用的方案

- **OpenAI 官方 SDK** — 引入与 net 模块重叠的 HTTP 层，且不能适配非标准兼容接口（如 Ollama、LocalAI 的部分实现差异）
- **LiteLLM** — 统一了 100+ provider 的接口但增加依赖复杂度；当前项目只需要 3-5 个 provider，自身 Protocol 已足够
- **流式响应** — 当前仅支持非流式 `completion`，流式需要不同的响应模型和回调接口，首版不做
- **多 provider 自动路由** — 由 `LlmConfig.provider` 显式指定，不做自动检测

### 与 net 模块关系

`LlmClient` 通过 `NetClient.request_json(method, url, headers, json_data)` 发送请求。net 模块已提供以下能力，llm 不重复实现：
- 请求体重试（指数退避，默认 3 次）
- HTTP 错误到 `Result.failure` 的映射（`@catch_result` 处理 HTTPError/URLError/TimeoutError）
- JSON 序列化/反序列化
- 请求头合并
