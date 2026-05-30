# Stage 设计文档

## StageHandler 泛型契约

`StageHandler(ABC, Generic[_C])` 是阶段处理器的抽象基类，以 `_C: TaskConfig` 作为泛型参数，子类声明自己接受的配置子类型（如 `PrepareStage` 继承 `StageHandler[SliceSummaryTaskConfig]`）。

唯一的抽象方法：

```python
async def execute(self, ctx: StageContext, config: _C) -> Result[None]
```

四个具体 stage 全部是异步方法。

## StageContext 依赖注入

`StageContext` 是 Engine 组装的 DI 容器，包含六个字段：

| 字段 | 用途 |
|------|------|
| `llm_client` | 发起 LLM 请求 |
| `logger` | 写入结构化日志 |
| `state` | 读写运行时状态（切片进度、聚合结果） |
| `checkpoint_store` | 保存/加载断点 |
| `workspace` | 确定输入输出文件路径 |
| `executor_config` | 获取并行度等运行时参数 |

Stage 通过 `ctx` 读取这些依赖，不创建任何运行时对象，不持有配置。

## 四个 stage 的职责与契约

### PrepareStage

- **来源**: `config.input_files`，`ctx.workspace.input_dir`
- **产出**: `ctx.state.slice_states`（切片状态列表），`ctx.state.metadata["slice_contents"]`（切片内容）
- **实现**: 在线程池中读取文件并切分文本，根据文件数量决定 `source` 字段
- **失败**: 文件读取失败或输入为空时返回 `Result.failure`

### SummarizeStage

- **来源**: `ctx.state.slice_states`（仅处理 status 为 pending 的切片），`ctx.state.metadata["slice_contents"]`
- **产出**: `ctx.state.metadata["summaries"]`（聚合的摘要列表），`ctx.state.completed_slices`
- **实现**: 按 `config.slice_config.parallelism` 分批并行调用 LLM，每批完成后保存 checkpoint
- **失败**: 切片索引越界、LLM 调用失败或空响应时返回错误（其他切片不受影响）

### GenerateStage

- **来源**: `ctx.state.metadata["summaries"]`
- **产出**: `ctx.state.metadata["generation_output"]`（skills 为目录路径，chara_card 为 JSON 字符串）
- **实现**: 先 compress 去重，再按 `config.kind` 分流
- **容错**: 压缩失败时退回原始拼接继续执行

### FinalizeStage

- **来源**: `ctx.state.metadata["generation_output"]`
- **产出**: skills 已由 tool-calling 直接落盘（本阶段仅记录日志）；chara_card 写入 JSON 到 `ctx.workspace.cards_dir`
- **实现**: 根据 `config.kind` 决定操作路径
- **失败**: 只有 chara_card 写入可能失败

## Slicer 和 ToolHandler 的位置

`Slicer` 和 `ToolHandler` 放在 `stages` 包内，但与 `StageHandler` 无继承关系：

- `Slicer` 是静态工具类，提供 `count_tokens()` 和 `slice_text()`，被 `PrepareStage` 和生成阶段的 token 统计使用
- `ToolHandler` 将 LLM tool_calls 转译为文件系统操作，被 `SummarizeStage` 和 `GenerateStage` 使用

两者没有 `execute(ctx, config)` 签名，不通过 `StageContext` 获取依赖——参数由调用方显式传入。
