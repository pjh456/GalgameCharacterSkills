# 贡献指南

感谢你对本项目的关注！

为了更好地进行社区协作、提高开发和审查效率、增强代码可读性和可维护性，请 **严格按照** 以下规范进行贡献开发。

## 开发流程

1. **Fork 原仓库** 到自己的 Github 账号下。
2. **同步主仓库** 保持代码最新：
    ```bash
    git fetch upstream # upstream 是使用 origin add 添加的本项目主仓库源
    git checkout main # 切到项目主分支
    git pull upstream main # 同步更新项目代码到最新
    ```
3. **新建分支** 开发功能
    ```bash
    git checkout -b feat/your-feature-name # 创建按格式命名的分支，见下文
    ```
4. 在本地完成开发，**确保功能被测试过**，并与原有代码保持良好兼容性
5. **提交代码** 到自己 fork 的仓库
6. **发起 Pull Request**，目标分支为 `main`
7. **等待 Code Review**，将发现的问题一一修复后等待合并。

## 分支命名

- `main`: 保持运行稳定性的主分支
- `feat/*`: 新功能开发分支，例如 `feat/gemini-support`
- `bugfix/*`: Bug 修复分支，例如 `bugfix/frontend-undefined`
- `refactor`: 重构分支，例如 `refactor/core-rewrite`
- `docs/*`: 文档补充分支，例如 `docs/readme-improvement`
- `perf/*`: 性能优化分支，例如 `perf/faster-request`
- `test/*`：测试补充分支，例如 `test/cover-llm`

注意：在进行项目重构前，务必 **通过 Issue 向维护者确认是否接受该方向重构**

## 提交规范

每次的提交应当 **正交**，如测试补充和新增功能不应放入同一提交。

提交信息应当遵守 `<type>: <description>` 格式

常见 `type`：
- `feat`: 新增功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `test`: 增加、修改测试
- `refactor`: 代码重构
- `perf`: 性能优化
- `style`: 代码格式调整（缩进、空格等）
- `chore`: 配置、构建修改

示例：

`feat: 添加了断点重传支持`

`fix: 修复了前端页面阻塞问题`

良好的提交信息应当 **简明扼要** 地描述提交内容，反过来说，当无法简单描述一次提交信息时，考虑是否需要对提交进行细化。

## 测试与检查

项目使用 `pytest` 作为基础测试框架，所有单元测试置于 `test/` 目录下。

PR 提交信息中，应当写明本次修改 **通过何种方式进行验证**，如：完整执行过一遍流程，有完整覆盖的单元测试等。

## 其他守则

请保持尊重、开放和协作的态度。

任何形式的歧视或攻击性言行都不被允许。

最后，感谢你为这个项目做出的一切贡献！

