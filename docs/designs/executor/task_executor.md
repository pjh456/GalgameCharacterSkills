# executor.task_executor 设计文档

### 设计原因

任务执行器需要处理两种不同类型的任务：

- **summarize 任务**（`SliceSummaryTaskConfig`）：读取文本文件，切片，对每个切片调用 LLM 蒸馏角色特征
- **generation 任务**（`GenerationTaskConfig`）：基于已有切片总结，调用 LLM 生成 skill 文件夹或角色卡

两者走不同的阶段序列。将路由逻辑分散在 4 个阶段处理器中时，每个处理器都需要判断"我是否应该在这一步执行"，导致 guard 代码重复。

### 两路分发

`TaskExecutor.arun` 是唯一的 routing point：

```python
async def arun(self) -> Result[None]:
    if isinstance(self.config, SliceSummaryTaskConfig):
        return await self._run_summarize()
    elif isinstance(self.config, GenerationTaskConfig):
        return await self._run_generation()
    else:
        return Result.failure(
            f"Unknown task config type: {type(self.config).__name__}",
            code="executor_invalid_config",
        )
```

`_run_summarize` 和 `_run_generation` 各自持有固定的阶段处理器列表，调用时直接传入窄化后的 config 类型。路由知识集中在 arun 中的三路 if/elif/else。

### StageHandler 泛型基类

`StageHandler(Generic[_C])` 是纯泛型标记。每个处理器声明自己的类型参数：

```python
class PrepareStage(StageHandler[SliceSummaryTaskConfig]):
    def execute(self, executor, config: SliceSummaryTaskConfig) -> Result[None]:
```

`StageHandler` 不强制 execute 签名——各处理器自行定义。Prepare/Finalize 是同步，Summarize/Generate 是异步。pyright 通过泛型继承跟踪 config 类型，在 _run_summarize 中传递 `self.config` 时确认类型一致。

### CheckpointStore 独立于阶段

`CheckpointStore` 与阶段处理器无直接耦合。序列化和反序列化走 `JsonIO.write` / `JsonIO.read`，通过 `WorkspacePaths.checkpoints_dir` 确定路径。阶段处理器只关心 `executor.checkpoint_store.save(checkpoint, workspace)`。

### 依赖注入

`TaskExecutor` 持有 6 个依赖，不读取 `RuntimeConfig`：

| 依赖 | 来源 | 用途 |
|---|---|---|
| `config: TaskConfig` | engine 传入 | 任务参数：角色名/prompt/token 等 |
| `llm_client: LlmClient` | engine 从 `RuntimeConfig.llm_config` 构造 | LLM 调用 |
| `workspace: WorkspacePaths` | engine 从 `RuntimeConfig.workspace_paths` 传入 | 输入/输出路径 |
| `log_writer: LogWriter` | engine 从 `RuntimeConfig.log_policy` 构造 | 进度日志 |
| `state: TaskState` | engine 传入（新任务=TaskState()，恢复=从 checkpoint 加载） | 运行时状态 |
| `checkpoint_store: CheckpointStore` | `__init__` 内初始化 | 断点持久化 |

### 不采用的方案

- **字典映射 stage name → processor** — 引入字符串耦合，且无法做类型窄化（所有 processor 被 erase 为 `StageHandler[TaskConfig]`）
- **为 summarize 任务加空 generate/finalize 阶段** — 阶段处理器不应包含"本任务跳过"逻辑，路由决策属于编排器
- **在 TaskExecutor 内定义 `_STAGE_ORDER` 列表** — 列表假设所有任务走相同阶段链，实际上两种任务的阶段链不同
