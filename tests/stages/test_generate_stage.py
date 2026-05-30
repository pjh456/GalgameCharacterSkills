from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

from gal_chara_skill.conf.checkpoint import CheckpointStore
from gal_chara_skill.conf.module.executor import ExecutorConfig
from gal_chara_skill.conf.module.llm import LlmConfig
from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.conf.module.net import NetConfig
from gal_chara_skill.conf.stage import StageContext
from gal_chara_skill.conf.state import TaskState
from gal_chara_skill.conf.task import GenerationTaskConfig
from gal_chara_skill.core.paths import WorkspacePaths
from gal_chara_skill.core.result import Result
from gal_chara_skill.llm.client import LlmClient
from gal_chara_skill.llm.models import ChatCompletion, ChatMessage, TokenUsage
from gal_chara_skill.log.logger import Logger
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter
from gal_chara_skill.net.client import NetClient
from gal_chara_skill.stages import GenerateStage


class NullWriter(LogWriter):
    def write(self, record: LogRecord) -> Result[None]:
        return Result.success()


def _fake_completion(content: str = "") -> ChatCompletion:
    return ChatCompletion(
        message=ChatMessage(role="assistant", content=content),
        finish_reason="stop",
        id="fake-id",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        model="test-model",
    )


def _make_ctx(project_root: Path) -> StageContext:
    workspace = WorkspacePaths(project_root=project_root)
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
        state=TaskState(task_id="test-generate"),
        checkpoint_store=CheckpointStore(),
        workspace=workspace,
        executor_config=ExecutorConfig(),
    )


def test_generate_chara_card(project_root: Path) -> None:
    ctx = _make_ctx(project_root)
    ctx.state.metadata["summaries"] = ["Summary A.", "Summary B."]
    config = GenerationTaskConfig(role_name="Char", kind="chara_card", summary_task_id="sum-001")

    with patch.object(ctx.llm_client, "acomplete_with_tools") as mock_tools:
        mock_tools.return_value = Result.success(None)

        result = asyncio.run(GenerateStage().execute(ctx, config))

    assert result.ok is True
    assert "generation_output" in ctx.state.metadata


def test_generate_skills(project_root: Path) -> None:
    ctx = _make_ctx(project_root)
    ctx.state.metadata["summaries"] = ["Summary A.", "Summary B."]
    config = GenerationTaskConfig(role_name="Char", kind="skills", summary_task_id="sum-001")

    with patch.object(ctx.llm_client, "acomplete_with_tools") as mock_tools:
        mock_tools.return_value = Result.success(None)

        result = asyncio.run(GenerateStage().execute(ctx, config))

    assert result.ok is True
    output = ctx.state.metadata["generation_output"]
    assert "skill-main" in output


def test_generate_compress_skip_on_single(project_root: Path) -> None:
    ctx = _make_ctx(project_root)
    ctx.state.metadata["summaries"] = ["Single summary only."]
    config = GenerationTaskConfig(role_name="Char", kind="chara_card", summary_task_id="sum-001")

    with patch.object(ctx.llm_client, "acomplete_with_tools") as mock_tools:
        mock_tools.return_value = Result.success(None)

        result = asyncio.run(GenerateStage().execute(ctx, config))

    assert result.ok is True


def test_generate_compress_fallback(project_root: Path) -> None:
    ctx = _make_ctx(project_root)
    ctx.state.metadata["summaries"] = ["A.", "B.", "C."]
    config = GenerationTaskConfig(role_name="Char", kind="chara_card", summary_task_id="sum-001")

    with patch.object(ctx.llm_client, "acomplete_with_tools") as mock_tools:
        mock_tools.side_effect = [
            Result.failure("compress failed", code="test_failure"),
            Result.success(None),
        ]

        result = asyncio.run(GenerateStage().execute(ctx, config))

    assert result.ok is True
