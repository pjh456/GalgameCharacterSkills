from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from gal_chara_skill.conf.checkpoint import CheckpointStore
from gal_chara_skill.conf.module.executor import ExecutorConfig
from gal_chara_skill.conf.module.llm import LlmConfig
from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.conf.module.net import NetConfig
from gal_chara_skill.conf.stage import StageContext
from gal_chara_skill.conf.state import SliceState, TaskState
from gal_chara_skill.conf.task import SliceSummaryTaskConfig, SliceConfig
from gal_chara_skill.core.paths import WorkspacePaths
from gal_chara_skill.core.result import Result
from gal_chara_skill.llm.client import LlmClient
from gal_chara_skill.llm.models import ChatCompletion, ChatMessage, TokenUsage
from gal_chara_skill.log.logger import Logger
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter
from gal_chara_skill.net.client import NetClient
from gal_chara_skill.stages import SummarizeStage


class NullWriter(LogWriter):
    def write(self, record: LogRecord) -> Result[None]:
        return Result.success()


def _fake_completion(content: str) -> ChatCompletion:
    return ChatCompletion(
        message=ChatMessage(role="assistant", content=content),
        finish_reason="stop",
        id="fake-id",
        usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        model="test-model",
    )


def _make_ctx(project_root: Path) -> StageContext:
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
    return StageContext(
        llm_client=llm_client,
        logger=logger,
        state=TaskState(task_id="test-summarize"),
        checkpoint_store=CheckpointStore(),
        workspace=workspace,
        executor_config=ExecutorConfig(),
    )


def test_summarize_single_slice(project_root: Path) -> None:
    ctx = _make_ctx(project_root)
    ctx.state.slice_states = [SliceState(slice_index=0, source_file="test.txt", source_slice_index=0)]
    ctx.state.metadata["slice_contents"] = ["This is slice content."]

    config = SliceSummaryTaskConfig(
        role_name="Char",
        input_files=("test.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=1),
    )

    with patch.object(ctx.llm_client, "acomplete", return_value=Result.success(
        _fake_completion("Summary of the slice.")
    )):
        result = asyncio.run(SummarizeStage().execute(ctx, config))

    assert result.ok is True
    assert "summaries" in ctx.state.metadata
    assert len(ctx.state.metadata["summaries"]) == 1
    assert ctx.state.metadata["summaries"][0] == "Summary of the slice."
    assert ctx.state.slice_states[0].status == "completed"
    assert 0 in ctx.state.completed_slices


def test_summarize_skip_completed(project_root: Path) -> None:
    ctx = _make_ctx(project_root)
    ctx.state.slice_states = [
        SliceState(slice_index=0, source_file="test.txt", source_slice_index=0, status="completed"),
        SliceState(slice_index=1, source_file="test.txt", source_slice_index=1),
    ]
    ctx.state.metadata["slice_contents"] = ["slice0", "slice1"]

    config = SliceSummaryTaskConfig(
        role_name="Char",
        input_files=("test.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=1),
    )

    with patch.object(ctx.llm_client, "acomplete", return_value=Result.success(
        _fake_completion("Summary 1.")
    )):
        result = asyncio.run(SummarizeStage().execute(ctx, config))

    assert result.ok is True
    assert len(ctx.state.metadata["summaries"]) == 1
    assert ctx.state.slice_states[1].status == "completed"


def test_summarize_parallel(project_root: Path) -> None:
    ctx = _make_ctx(project_root)
    ctx.state.slice_states = [
        SliceState(slice_index=i, source_file="test.txt", source_slice_index=i)
        for i in range(4)
    ]
    ctx.state.metadata["slice_contents"] = [f"content{i}" for i in range(4)]

    config = SliceSummaryTaskConfig(
        role_name="Char",
        input_files=("test.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=2),
    )

    call_count = 0

    def _mock_acomplete(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return Result.success(_fake_completion(f"Summary {call_count}."))

    with patch.object(ctx.llm_client, "acomplete", side_effect=_mock_acomplete):
        result = asyncio.run(SummarizeStage().execute(ctx, config))

    assert result.ok is True
    assert len(ctx.state.metadata["summaries"]) == 4
    assert ctx.state.completed_slices == [0, 1, 2, 3]


@pytest.mark.asyncio
async def test_summarize_concurrent_event_barrier(project_root: Path) -> None:
    """asyncio.Event barrier: 10 coroutines released simultaneously, verify _SUMMARIES complete."""
    ctx = _make_ctx(project_root)

    num_slices = 10
    ctx.state.slice_states = [
        SliceState(slice_index=i, source_file="s.txt", source_slice_index=i)
        for i in range(num_slices)
    ]
    ctx.state.metadata["slice_contents"] = [f"content{i}" for i in range(num_slices)]

    config = SliceSummaryTaskConfig(
        role_name="Barrier",
        input_files=("s.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=num_slices),
    )

    barrier = asyncio.Event()

    async def mock_acomplete(*args, **kwargs):
        await barrier.wait()
        return Result.success(_fake_completion("summary"))

    stage = SummarizeStage()

    with patch.object(ctx.llm_client, "acomplete", side_effect=mock_acomplete):
        task = asyncio.create_task(stage.execute(ctx, config))
        await asyncio.sleep(0)
        barrier.set()
        result = await task

    assert result.ok is True
    assert "summaries" in ctx.state.metadata
    assert len(ctx.state.metadata["summaries"]) == num_slices
    assert ctx.state.completed_slices == list(range(num_slices))


@pytest.mark.asyncio
@pytest.mark.parametrize("round_num", list(range(50)))
async def test_summarize_concurrent_stress(round_num: int, project_root: Path) -> None:
    """50-round parametrized stress test with random interleaving, 5 coroutines per round."""
    ctx = _make_ctx(project_root)

    num_slices = 5
    ctx.state.slice_states = [
        SliceState(slice_index=i, source_file="s.txt", source_slice_index=i)
        for i in range(num_slices)
    ]
    ctx.state.metadata["slice_contents"] = [f"content{i}" for i in range(num_slices)]

    config = SliceSummaryTaskConfig(
        role_name="Stress",
        input_files=("s.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=num_slices),
    )

    async def mock_acomplete(*args, **kwargs):
        await asyncio.sleep(0)
        return Result.success(_fake_completion(f"summary_{round_num}"))

    stage = SummarizeStage()
    with patch.object(ctx.llm_client, "acomplete", side_effect=mock_acomplete):
        result = await stage.execute(ctx, config)

    assert result.ok is True
    assert "summaries" in ctx.state.metadata
    assert len(ctx.state.metadata["summaries"]) == num_slices
    assert ctx.state.completed_slices == list(range(num_slices))
