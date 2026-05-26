# core.executors.py 设计文档

### 设计原因

项目内 fs 和 log 模块的 I/O 操作均为同步实现。Python 标准库不提供内核级异步文件 I/O，第三方库 `aiofiles` 底层同样使用线程池包装。因此，为同步 I/O 提供异步接口的唯一可行路径是将它们在线程池中执行。

net 模块已在内部使用 `asyncio.to_thread` 实现异步请求，fs 和 log 模块需要与其保持一致的模式。若将 `asyncio.to_thread` 直接散落在各模块中，线程池策略将无法集中管理，后续调整需要改动多个调用方。

### 设计目标

`executors` 模块承担以下职责：

- **`to_async` 装饰器** — 将同步函数声明式转化为异步函数，不改动原函数体，保留原始签名和元信息（通过 `functools.wraps`）
- **`get_pool()`** — 进程级单一共享线程池的懒初始化入口，所有异步 I/O 共用同一个池
- **`configure_pool(pool)`** — 注入自定义线程池的接口，由 `RuntimeConfig` 或上层入口调用，实现线程池策略的可替换性
- **`run_in_pool(fn, *args, **kwargs)`** — 直接在线程池中执行任意同步可调用对象，用于不适合装饰器的场景

该模块位于 core 层，不依赖任何项目业务模块，仅封装标准库 `asyncio` 和 `concurrent.futures` 的能力。

### 装饰器叠放规则

fs 模块的 I/O 类使用 `@staticmethod`，log 模块的 `LogWriter` 和 `LogReader` 为实例方法。`@to_async` 与 `@staticmethod` 叠放时顺序如下：

静态方法：
```python
@staticmethod
@to_async
def aread(path: FilePath, encoding: str = "utf-8") -> Result[str]:
    return TextIO.read(path, encoding)
```

`@to_async` 在内层先将 `TextIO.read` 转化为 async，`@staticmethod` 在外层将结果注册为类的静态属性。顺序不能反转，否则 async 函数不会正确解绑。

实例方法：
```python
@to_async
def awrite(self, record: LogRecord) -> Result[None]:
    return self.write(record)
```

`self` 在 `wrapper` 调用时被捕获到闭包中，传递给 `run_in_pool` 闭包。`LogWriter.write` 内部使用 `threading.Lock` 做文件级互斥，线程池内多个子线程调用时锁语义不变。

### 线程池设计

`_pool` 是模块级私有变量，初始为 `None`。首次调用 `get_pool()` 时创建标准 `ThreadPoolExecutor`（线程数由 `concurrent.futures` 默认策略决定）。后续调用返回同一实例。

`configure_pool(pool)` 允许替换当前池，传入 `None` 可重置状态。调用方（如 `RuntimeConfig` 初始化流程）可在首次 `get_pool()` 之前注入自定义池。

当前不按 I/O 类型或请求类型划分多池，因为项目并发量较低，单一共享池不会形成竞争。这一决策可在将来通过扩展 `get_pool(name)` 或前缀路由改变，而调用方不需要修改。

### 不采用的方案

- **按 I/O / HTTP / 主逻辑划分线程池** — 当前并发量不支持这种复杂度，预判性过度设计
- **使用第三方 `aiofiles`** — 其 `open` / `read` / `write` 底层也是 `asyncio.to_thread` 的封装，引入依赖换取零额外能力
- **使用 `ProcessPoolExecutor`** — 项目无 CPU 密集型计算，进程间序列化开销大于收益
- **在每个 I/O 类内部直接调用 `asyncio.to_thread`** — 线程策略散落各处，将来重构成本高

### 与 net 模块的关系

net 模块的 `RawRequestExecutor.arequest` 和 `JsonRequestExecutor.arequest` 在 `executors` 模块之前实现，内部直接使用 `asyncio.to_thread`。两者行为等价（都是默认线程池执行同步函数），当前并存不影响功能。将来可统一将 net 模块的 `asyncio.to_thread` 替换为 `run_in_pool`，集中管理线程池入口。
