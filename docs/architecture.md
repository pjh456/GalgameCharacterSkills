# GalgameCharacterSkills 架构文档

## 1. 项目目标

本项目是一个基于 Flask 的本地工具，核心能力包括：

- 扫描与切片资源文本（`resource/`）
- 使用 LLM 对文本进行角色归纳（`summarize`）
- 基于归纳结果生成技能包（`generate_skills`）
- 生成角色卡 JSON/PNG（`generate_chara_card`）
- 提供断点持久化、失败恢复、任务列表管理

入口运行方式：

- `main.py` 启动 Flask 并自动打开浏览器
- Web UI 模板位于 `galgame_character_skills/web/index.html`


## 2. 分层结构

当前代码以 `galgame_character_skills/` 作为库根目录，按职责分层：

- `app.py`：HTTP 路由层（请求分发与 JSON 响应）
- `api/`：接口编排层（参数读取、调用 application、返回结果组装）
- `application/`：用例层（归纳/技能生成/角色卡生成核心流程）
- `domain/`：领域对象（请求数据类、统一结果模型）
- `utils/`：基础设施与实现细节（文件系统、checkpoint、LLM 交互、工具调用）
- `web/`：前端模板与页面逻辑

依赖方向约束：

- `app -> api -> application -> domain/utils`
- `domain` 不依赖外部层
- `utils` 不依赖 `api/app`


## 3. 目录与核心文件

### 3.1 路由入口

- `galgame_character_skills/app.py`
  - 注册所有 API 路由
  - 创建 `deps` 与 `task_runtime`
  - 使用 `_run_json/_run_json_with_body` 统一响应包装

### 3.2 API 层

- `galgame_character_skills/api/file_api_service.py`
- `galgame_character_skills/api/summary_api_service.py`
- `galgame_character_skills/api/task_api_service.py`
- `galgame_character_skills/api/checkpoint_service.py`
- `galgame_character_skills/api/context_api_service.py`
- `galgame_character_skills/api/vndb_api_service.py`
- `galgame_character_skills/api/vndb_service.py`

特点：

- 保持“薄编排”角色，不放业务算法
- 统一使用 `ok_result/fail_result`

### 3.3 Application 层

- `galgame_character_skills/application/summarize_service.py`
- `galgame_character_skills/application/skills_service.py`
- `galgame_character_skills/application/character_card_service.py`
- `galgame_character_skills/application/app_container.py`
- `galgame_character_skills/application/llm_gateway.py`
- `galgame_character_skills/application/tool_gateway.py`

特点：

- 用例流程完整闭环在此层实现
- 通过 runtime 注入 LLM/Tool/路径与 IO 依赖

### 3.4 Domain 层

- `galgame_character_skills/domain/task_requests.py`
  - `SummarizeRequest`
  - `GenerateSkillsRequest`
  - `GenerateCharacterCardRequest`
- `galgame_character_skills/domain/service_result.py`
  - `ServiceResult`
  - `ok_result(...)`
  - `fail_result(...)`

### 3.5 Utils 层（基础设施）

- Checkpoint：
  - `galgame_character_skills/utils/checkpoint_manager.py`
  - `galgame_character_skills/utils/checkpoint_utils.py`
- LLM 与工具：
  - `galgame_character_skills/utils/llm_interaction.py`
  - `galgame_character_skills/utils/llm_factory.py`
  - `galgame_character_skills/utils/tool_handler.py`
  - `galgame_character_skills/utils/tool_gateway.py`
- 文本处理与后处理：
  - `galgame_character_skills/utils/file_processor.py`
  - `galgame_character_skills/utils/compression_service.py`
  - `galgame_character_skills/utils/skills_context_builder.py`
  - `galgame_character_skills/utils/skills_postprocess.py`


## 4. 关键流程

### 4.1 summarize（归纳）

1. `POST /api/summarize`
2. API 层调用 `run_summarize_task`
3. 创建或恢复 checkpoint
4. `FileProcessor` 切片
5. 并发执行 `_process_single_slice`
6. 每片成功后保存 slice 结果并原子更新进度
7. 全成功则 `mark_completed`，部分失败则返回 `can_resume=true`

### 4.2 generate_skills（生成技能包）

1. `POST /api/skills`（`mode=skills`）
2. 读取角色 summary 文件
3. 按上下文窗口决定是否压缩
4. 进入 LLM tool-call 循环
5. 写入 skill-main，追加 VNDB 信息，复制 skill-code
6. 更新 checkpoint 状态

### 4.3 generate_chara_card（生成角色卡）

1. `POST /api/skills`（`mode=chara_card`）
2. 读取分析汇总 JSON
3. 可选压缩 analyses
4. LLM 逐字段写角色卡
5. 产出 JSON；若有图片则尝试产出 PNG（嵌入 JSON）
6. 更新 checkpoint 状态，失败可恢复


## 5. 断点恢复机制

### 5.1 状态模型

Checkpoint 主要状态：

- `running`
- `failed`
- `completed`

恢复入口：

- `POST /api/checkpoints/<checkpoint_id>/resume`

当前约束：

- `running` 禁止恢复
- `completed` 禁止恢复
- 前端仅对 `failed` 显示“恢复”按钮

### 5.2 持久化内容

- `input_params`：任务输入
- `progress`：阶段、总步数、完成/待处理列表
- `intermediate_results`：切片输出路径、最终输出路径等
- `llm_conversation_state`：messages、iteration、all_results、fields_data

### 5.3 并发一致性

`summarize` 并发切片完成时，使用 `mark_slice_completed(...)` 原子更新：

- 将 `slice_index` 加入 `completed_items`
- 从 `pending_items` 移除
- 同步持久化


## 6. API 概览

主要接口：

- `GET /api/files`
- `POST /api/files/tokens`
- `POST /api/slice`
- `GET /api/summaries/roles`
- `POST /api/summaries/files`
- `POST /api/summarize`
- `POST /api/skills`
- `POST /api/context-limit`
- `POST /api/vndb`
- `GET /api/checkpoints`
- `GET /api/checkpoints/<id>`
- `DELETE /api/checkpoints/<id>`
- `POST /api/checkpoints/<id>/resume`

返回风格统一为：

- 成功：`{"success": true, ...}`
- 失败：`{"success": false, "message": "...", ...}`


## 7. 运行时依赖注入

`TaskRuntimeDependencies`（`application/app_container.py`）统一注入：

- `file_processor`
- `ckpt_manager`
- `clean_vndb_data`
- `get_base_dir`
- `estimate_tokens`
- `llm_gateway`
- `tool_gateway`
- `download_vndb_image`
- `embed_json_in_png`

目的：

- 业务流程与具体实现解耦
- 为 mock 与测试铺路


## 8. 资源与数据目录

- 文本输入目录：`resource/`
- checkpoint 目录：`checkpoints/`
- 任务临时目录：`checkpoints/temp/<checkpoint_id>/`
- 技能输出目录：`<role>-skill-main/`、`<role>-skill-code/`
- 角色卡输出目录：`<role>-character-card/`


## 9. 已知技术债

- `LLMInteraction` 仍较重，内部流程与 checkpoint/模板处理耦合偏高
- 自动化测试尚不完整，尤其是 checkpoint 恢复与并发边界
- 任务类型继续扩展时，现有流程存在重复编排代码


## 10. 文档清单（专题）

可按专题拆分为以下文档：

- `docs/checkpoint.md`：checkpoint 结构、状态机、恢复策略
- `docs/llm-flow.md`：LLM 请求链路、tool call 循环、压缩策略
- `docs/api-contract.md`：接口请求/响应字段约定
- `docs/testing-plan.md`：分阶段测试计划与 mock 策略
