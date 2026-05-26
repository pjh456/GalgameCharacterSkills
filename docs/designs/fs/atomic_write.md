# fs.text._atomic_write_text 设计文档

### 设计原因

文本文件写入需要保证已有文件不被部分写入破坏。最简方案是先写临时文件，再用文件系统原子操作替换目标。在 Unix 上 `os.rename` 和 `os.replace` 始终原子；在 Windows 上 `os.replace` 调用 `MoveFileExW`，若目标文件被其他进程以 `FILE_SHARE_READ`（不含 `FILE_SHARE_DELETE`）打开，会抛 `PermissionError`。

### 两级降级链

```
tempfile.NamedTemporaryFile(dir=parent, delete=False)
    → os.replace(temp, target)          ← 首选：原子，失败返回完整原因
    → shutil.copy2(temp, target)        ← 降级：非原子但只需 WRITE 权限
    → 抛异常                             ← 两级都失败，调用方收到失败 Result
```

`shutil.copy2` 只需要 `WRITE` 权限（create → write → close），覆盖了防病毒软件、备份进程偶尔锁定目标文件的常见 Windows 场景。

### 临时文件清理

`finally` 块确保临时文件无论如何都会删除。`os.replace` 成功后文件已被移走，`exists()` 返回 `False`，`unlink(missing_ok=True)` 为空操作。降级路径（`copy2` 成功）后临时文件留在原地，由同一 `finally` 清理。

### 不采用的方案

- **始终使用 `shutil.copy2`** — 损失原子性，写入过程中崩溃会留下半写文件
- **`tempfile` 放在默认 `/tmp` 再 `os.replace`** — 跨文件系统 `os.replace` 在 Python 上回退到 `shutil.copy2` + `os.remove`，不原子
- **文件锁 + 原地写入** — 需要引入 `fcntl`/`msvcrt`，跨平台复杂度高，且不解决"写入过程中被读"的窗口问题
