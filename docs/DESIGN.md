# 设计文档

该文档记录了当前项目的设计抉择、取舍、副作用和可能造成混淆的边界情况。

建议开发者在详细阅读本文档之后再进行开发。

## core

模块内封装了最底层的数据结构：

- `Result[T]` 用于在返回值中显式传递异常，避免滥用 try-catch 和 throw
- `WorkspacePaths` 根据基准路径自动推导子路径
- 字典字段校验器作为装饰器封装了字段检查

### `Result[T]`

[core.result.py 设计文档](./designs/core/result.md)

### `WorkspacePaths`

项目包含大量单元测试，若不对执行路径加以区分，测试的并发就很难实现。同时，不写死路径还能为后续可能提供的“自定义输出路径”功能做预备，不过这只是额外的好处。

`WorkspacePaths` 的原理是指定一工作区目录为准，其他路径直接根据这一目录自行构造，把不同内容的路径构造逻辑收在了这块，避免后续改动的麻烦和疏漏。

整个项目是基于输入文件和输出文件展开的，在后续多个模块中也会大量需要进行路径的构造。故 `WorkspacePaths` 的集中化尤为重要，放在 core 模块是合理的。

### 字典字段校验器

[core.validate.py 设计文档](./designs/core/validate.md)

### 同步到异步桥接

[core.executors.py 设计文档](./designs/core/executors.md)

core 层提供 `executors` 模块，集中管理线程池与同步到异步的桥接。`to_async` 装饰器将同步函数在线程池中执行并返回协程，`get_pool` / `configure_pool` 管理共享线程池的生命周期与替换。

fs 模块的 `TextIO`、`JsonIO`、`JsonlIO`、`YamlIO`、`EnvIO` 和 log 模块的 `LogWriter`、`LogReader` 各在类内提供 `a` 前缀异步方法（如 `aread`、`awrite`、`aappend`），使用 `@to_async` 装饰同步方法，不改动原有同步接口。

对于静态方法，`@staticmethod` 和 `@to_async` 叠放时 `@staticmethod` 在外层；对于实例方法，仅 `@to_async` 包裹，`self` 通过闭包在线程池中绑定。

## conf

模块收集了其他同层或高层模块的配置，放在 conf.module 子模块中便于引用，避免了低层模块对高层模块可能的引用，同时也与 conf 模块完全负责配置的语义相符。

后续的高层模块中，多处需要注入运行时状态，目前设计也能避免循环引用或依赖不清晰的问题。

除了配置，模块还包含了大量通用的数据类：

- `TaskCheckpoint` 用于存储任务配置与状态，为断点重传提供支持
- `RuntimeConfig` 是运行时配置，未来会随着进度推进由直接存某个具体值改为存 conf.module 中的模块级配置对象
- `SliceState` 是单个切片文本的总结任务状态，此处是断点重传主要的恢复点，单独提取出来作为一个配置类
- `TaskState` 是整个任务本身的状态，其中包含多个切片总结任务和一个根据总结生成 skill 的任务
- `SliceConfig` 是将文件切片的配置，不涉及到 LLM 调用和重试，故自成一类
- `SliceSummaryTaskConfig/GenerationTaskConfig` 分别为切片总结任务和生成 skill 任务的配置，二者有一定相似性，故都继承自 `BaseTaskConfig`

### 持久化接口统一

`conf` 中的任务配置类目前统一收口为：

- `BaseTaskConfig.to_dict()`
- `BaseTaskConfig.from_dict()`

之所以将这两个能力同时挂在 `BaseTaskConfig` 上，而不是保留一个模块级函数，是为了把“任务配置的持久化入口”集中在同一抽象中。

这里的 `from_dict()` 本质上不是恢复 `BaseTaskConfig` 自身，而是根据 `kind` 分发到具体子类配置。因此它更接近“统一工厂入口”，而不是普通构造器。

对应地：

- 共享字段的持久化逻辑在父类统一处理
- 子类仅在外部表示与内部表示不同时覆写 `to_dict()`

当前 `SliceSummaryTaskConfig` 覆写 `to_dict()` 的唯一原因，就是 `input_files` 在内存中使用 `tuple[str, ...]`，在持久化时转换为 `list[str]` 更自然，也更符合 JSON 表示方式。

### 不可变配置与可变状态分离

`conf` 模块内部明确区分了两类数据：

- 不可变的静态配置
- 可变的运行时状态

前者包括：

- `BaseTaskConfig`
- `SliceConfig`
- `RuntimeConfig`

它们被设计为冻结的数据类，目的在于：

- 避免运行时逻辑无意间修改任务输入参数
- 降低并发场景下的共享状态污染风险
- 让 checkpoint 中“配置”和“状态”的边界更清楚

后者包括：

- `SliceState`
- `TaskState`

它们保留可变性，因为执行过程本身就需要不断更新：

- 当前切片是否完成
- 已尝试次数
- 当前阶段
- 已完成切片列表
- 扩展元数据

这种划分的设计理念是：

- 配置描述“任务应该如何执行”
- 状态描述“任务现在执行到了哪里”

两者在持久化时可以同处一个 checkpoint，但在建模上不能混为一谈。

### RuntimeConfig 的默认派生逻辑

`RuntimeConfig` 目前要求调用方显式提供：

- 网络配置
- 工作区路径
- 基础模型调用参数

其中 `log_path_config` 支持自动派生。

若调用方未显式指定日志路径配置，则默认根据 `workspace_paths.logs_dir` 构造 `LogPathConfig`。这样做的原因是：

- 避免每次初始化运行时都重复拼接日志目录
- 保持“工作区路径是根，其他运行产物路径从中推导”的一致原则
- 在默认情况下减少样板配置

但如果调用方显式传入 `log_path_config`，则以显式值为准。也就是说，该字段的设计目标并不是“强制默认”，而是“提供合理派生值，并允许覆盖”。

### 当前 checkpoint 的信任边界

虽然项目已经在 `from_dict()` 入口补充了基础字段校验，但当前设计仍然将 checkpoint 视为“项目内部产物”，而不是面对外部不可信输入的完整防御层。

这意味着：

- 会尽量拦截明显错误的结构与类型
- 会尽量在恢复入口暴露脏数据
- 但不会为了覆盖所有极端输入而引入过重的 schema 系统

这种取舍是有意为之。

对当前项目阶段而言，checkpoint 的主要目标是支持本地任务恢复与内部调试，不是作为一个完全开放的公共数据交换格式。因此，校验策略以“足够明确、足够便宜、能挡住常见错误”为主，而不是追求高度泛化的外部输入兼容性。


