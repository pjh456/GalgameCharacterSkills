# Engine 设计文档

## 汇编逻辑

`Engine` 持有 `RuntimeConfig`，通过 `_execute()` 组装运行依赖：

1. `NetClient` → `LlmClient`
2. 可选的预检（`executor_config.preflight_check`）
3. `Logger` + `LogWriter`
4. `StageContext`（注入上述所有依赖 + `TaskState` + `CheckpointStore`）

装配顺序确保了依赖在注入 StageContext 之前全部就绪。

## 两路分发

根据 `TaskConfig` 子类型选择 stage 序列：

| TaskConfig | stage 序列 | 后处理 |
|------------|-----------|--------|
| `SliceSummaryTaskConfig` | `PrepareStage()` → `SummarizeStage()` | 合并摘要写入文件 |
| `GenerationTaskConfig` | `GenerateStage()` → `FinalizeStage()` | 无 |

无法识别的 TaskConfig 子类型返回 `engine_unknown_config` 错误。

## 摘要合并

`SliceSummaryTaskConfig` 执行完毕后，Engine 从 `ctx.state.metadata["summaries"]` 读取聚合结果，以 `\n\n---\n\n` 拼接后写入 `summaries_dir/{role_name}_summary.md`。

合并不在 SummarizeStage 内完成，因为 stage 的职责是生成切片级摘要；跨切片的聚合与文件组织属于编排层职责。

## resume 恢复路径

`resume()` 通过 `CheckpointStore.load()` 尝试加载已有 checkpoint：

1. checkpoint 存在 → 取 `checkpoint.task_state`，注入 StageContext，`SummarizeStage` 自动跳过 status 为 completed 的切片
2. checkpoint 不存在 → 创建新 `TaskState`，退化为从零执行

CheckpointStore 不是单例——每次调用 `_execute()` 创建新实例，不同任务之间 checkpoint 隔离。

## TaskExecutor 异常处理

`TaskExecutor` 按序迭代 stage 列表，逐个 `await stage.execute(ctx, config)`。首个失败立即返回对应错误。

整个执行过程包裹在 `try/except` 中：

- 成功: `ctx.state.status = "completed"`
- stage 失败: 透传 `Result.failure`
- 异常: `ctx.state.status = "failed"`，`error_message` 记录 traceback，返回 `executor_failed`

无论成功或失败，均由 Engine 的调用方决定是否继续处理。
