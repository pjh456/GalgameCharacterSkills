from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

from gal_chara_skill.conf.checkpoint import CheckpointStore, TaskCheckpoint
from gal_chara_skill.conf.module.executor import ExecutorConfig
from gal_chara_skill.conf.module.llm import LlmConfig
from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.conf.module.net import NetConfig
from gal_chara_skill.conf.runtime import RuntimeConfig
from gal_chara_skill.conf.state import TaskState
from gal_chara_skill.conf.task import GenerationTaskConfig, SliceSummaryTaskConfig, SliceConfig
from gal_chara_skill.core.paths import WorkspacePaths
from gal_chara_skill.core.result import Result
from gal_chara_skill.engine.engine import Engine
from gal_chara_skill.llm.models import ChatCompletion, ChatMessage, TokenUsage


def _fake_completion(content: str = "Fake response.") -> ChatCompletion:
    return ChatCompletion(
        message=ChatMessage(role="assistant", content=content),
        finish_reason="stop",
        id="fake-id",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        model="test-model",
    )


def _make_runtime(project_root: Path) -> RuntimeConfig:
    workspace = WorkspacePaths(project_root=project_root)
    workspace.input_dir.mkdir(parents=True, exist_ok=True)
    return RuntimeConfig(
        net_config=NetConfig(),
        llm_config=LlmConfig(base_url="http://localhost", api_key="test", model_name="test"),
        workspace_paths=workspace,
        log_policy=LogPolicy(level="debug"),
        log_path_config=LogPathConfig(root_dir=project_root / "logs"),
        executor_config=ExecutorConfig(),
    )


def test_engine_run_slice_summary(project_root: Path) -> None:
    input_dir = project_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "test.txt").write_text("Hello world. This is test content for slicing.", encoding="utf-8")

    runtime = _make_runtime(project_root)
    engine = Engine(runtime)
    task_config = SliceSummaryTaskConfig(
        role_name="TestChar",
        input_files=("test.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=1),
    )

    with patch("gal_chara_skill.llm.client.LlmClient.complete",
               return_value=Result.success(_fake_completion("Summary content."))):
        result = engine.run(task_config)

    assert result.ok is True
    summary_path = runtime.workspace_paths.summaries_dir / "TestChar_summary.md"
    assert summary_path.exists()
    content = summary_path.read_text(encoding="utf-8")
    assert "Summary content." in content


def test_engine_run_generation(project_root: Path) -> None:
    runtime = _make_runtime(project_root)
    runtime.workspace_paths.cards_dir.mkdir(parents=True, exist_ok=True)

    engine = Engine(runtime)
    task_config = GenerationTaskConfig(role_name="Char", kind="chara_card", summary_task_id="sum-001")

    with patch("gal_chara_skill.llm.client.LlmClient.complete_with_tools",
               return_value=Result.success(None)):
        result = engine.run(task_config)

    assert result.ok is True


def test_engine_resume_with_checkpoint(project_root: Path) -> None:
    input_dir = project_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "test.txt").write_text("Hello world.", encoding="utf-8")

    runtime = _make_runtime(project_root)
    workspace = runtime.workspace_paths

    task_config = SliceSummaryTaskConfig(
        role_name="ResumeChar",
        input_files=("test.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=1),
    )
    state = TaskState(task_id="ResumeChar")
    checkpoint = TaskCheckpoint(task_config=task_config, task_state=state)
    store = CheckpointStore()
    store.save(checkpoint, workspace)

    engine = Engine(runtime)

    with patch("gal_chara_skill.llm.client.LlmClient.complete",
               return_value=Result.success(_fake_completion("Resumed content."))):
        result = engine.resume(task_config)

    assert result.ok is True


def test_engine_resume_after_partial_failure(project_root: Path) -> None:
    """CHK-01: SummarizeStage resumes from partial checkpoint, processes only pending slices."""
    from gal_chara_skill.conf.state import SliceState
    from gal_chara_skill.conf.stage import StageContext
    from gal_chara_skill.llm.client import LlmClient
    from gal_chara_skill.log.logger import Logger
    from gal_chara_skill.log.writer import LogWriter
    from gal_chara_skill.net.client import NetClient
    from gal_chara_skill.stages import SummarizeStage
    from tests.stages.test_summarize_stage import NullWriter

    workspace = WorkspacePaths(project_root=project_root)
    workspace.summaries_dir.mkdir(parents=True, exist_ok=True)

    llm_client = LlmClient(
        config=LlmConfig(base_url="http://localhost", api_key="test", model_name="test"),
        net_client=NetClient(NetConfig()),
    )
    logger = Logger(
        policy=LogPolicy(level="debug"),
        writer=NullWriter(LogPolicy(), LogPathConfig(root_dir=project_root / "logs")),
    )

    num_slices = 3
    state = TaskState(task_id="PartialChar")
    state.slice_states = [
        SliceState(slice_index=0, source_file="s.txt", source_slice_index=0, status="completed"),
        SliceState(slice_index=1, source_file="s.txt", source_slice_index=1, status="completed"),
        SliceState(slice_index=2, source_file="s.txt", source_slice_index=2, status="pending"),
    ]
    state.completed_slices = [0, 1]
    state.metadata["slice_contents"] = [f"content{i}" for i in range(num_slices)]

    task_config = SliceSummaryTaskConfig(
        role_name="PartialChar",
        input_files=("s.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=1),
    )

    call_count = 0

    async def mock_acomplete(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return Result.success(_fake_completion("Summary content."))

    ctx = StageContext(
        llm_client=llm_client,
        logger=logger,
        state=state,
        checkpoint_store=CheckpointStore(),
        workspace=workspace,
        executor_config=ExecutorConfig(),
    )

    with patch.object(ctx.llm_client, "acomplete", side_effect=mock_acomplete):
        asyncio.run(SummarizeStage().execute(ctx, task_config))

    assert call_count == 1
    assert len(state.completed_slices) == 3
    assert state.slice_states[2].status == "completed"


def test_engine_resume_empty_checkpoint(project_root: Path) -> None:
    """CHK-02: empty {} checkpoint — resume falls back to fresh run."""
    input_dir = project_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "input.txt").write_text("Content.", encoding="utf-8")

    runtime = _make_runtime(project_root)
    workspace = runtime.workspace_paths
    workspace.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    ckpt_file = workspace.checkpoints_dir / "EmptyChar.json"
    ckpt_file.write_text("{}", encoding="utf-8")

    task_config = SliceSummaryTaskConfig(
        role_name="EmptyChar",
        input_files=("input.txt",),
        slice_config=SliceConfig(max_tokens=1000),
    )

    engine = Engine(runtime)
    with patch("gal_chara_skill.llm.client.LlmClient.complete",
               return_value=Result.success(_fake_completion("ok"))):
        result = engine.resume(task_config)

    assert result.ok is True


def test_engine_resume_corrupt_checkpoint(project_root: Path) -> None:
    """CHK-02: corrupt JSON checkpoint — resume falls back to fresh run."""
    input_dir = project_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "input.txt").write_text("Content.", encoding="utf-8")

    runtime = _make_runtime(project_root)
    workspace = runtime.workspace_paths
    workspace.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    ckpt_file = workspace.checkpoints_dir / "CorruptChar.json"
    ckpt_file.write_text("{broken", encoding="utf-8")

    task_config = SliceSummaryTaskConfig(
        role_name="CorruptChar",
        input_files=("input.txt",),
        slice_config=SliceConfig(max_tokens=1000),
    )

    engine = Engine(runtime)
    with patch("gal_chara_skill.llm.client.LlmClient.complete",
               return_value=Result.success(_fake_completion("ok"))):
        result = engine.resume(task_config)

    assert result.ok is True
