from __future__ import annotations

import asyncio
from pathlib import Path

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
from gal_chara_skill.log.logger import Logger
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter
from gal_chara_skill.net.client import NetClient
from gal_chara_skill.stages import FinalizeStage


class NullWriter(LogWriter):
    def write(self, record: LogRecord) -> Result[None]:
        return Result.success()


def _make_ctx(project_root: Path, metadata: dict) -> StageContext:
    workspace = WorkspacePaths(project_root=project_root)
    workspace.cards_dir.mkdir(parents=True, exist_ok=True)
    llm_client = LlmClient(
        config=LlmConfig(base_url="http://localhost", api_key="test", model_name="test"),
        net_client=NetClient(NetConfig()),
    )
    logger = Logger(
        policy=LogPolicy(level="debug"),
        writer=NullWriter(LogPolicy(), LogPathConfig(root_dir=project_root / "logs")),
    )
    state = TaskState(task_id="test-task")
    state.metadata.update(metadata)
    return StageContext(
        llm_client=llm_client,
        logger=logger,
        state=state,
        checkpoint_store=CheckpointStore(),
        workspace=workspace,
        executor_config=ExecutorConfig(),
    )


def test_finalize_skills_branch(project_root: Path) -> None:
    ctx = _make_ctx(project_root, {"generation_output": "/fake/skills/Char-skill-main"})
    config = GenerationTaskConfig(role_name="Char", kind="skills", summary_task_id="sum-001")
    result = asyncio.run(FinalizeStage().execute(ctx, config))
    assert result.ok is True


def test_finalize_chara_card_success(project_root: Path) -> None:
    ctx = _make_ctx(project_root, {"generation_output": '{"name":"Char"}'})
    config = GenerationTaskConfig(role_name="Char", kind="chara_card", summary_task_id="sum-001")
    result = asyncio.run(FinalizeStage().execute(ctx, config))
    assert result.ok is True
    card_path = ctx.workspace.cards_dir / "Char.json"
    assert card_path.exists()
    assert '"name":"Char"' in card_path.read_text(encoding="utf-8")
