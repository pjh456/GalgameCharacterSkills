from __future__ import annotations

import asyncio
from pathlib import Path

from gal_chara_skill.conf.module.executor import ExecutorConfig
from gal_chara_skill.conf.module.llm import LlmConfig
from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.conf.module.net import NetConfig
from gal_chara_skill.conf.task import SliceSummaryTaskConfig, SliceConfig
from gal_chara_skill.core.paths import WorkspacePaths
from gal_chara_skill.core.result import Result
from gal_chara_skill.executor.stages.prepare import PrepareStage
from gal_chara_skill.executor.task_executor import TaskExecutor
from gal_chara_skill.llm.client import LlmClient
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter
from gal_chara_skill.net.client import NetClient


class NullWriter(LogWriter):
    def write(self, record: LogRecord) -> Result[None]:
        return Result.success()


def test_prepare_stage(project_root: Path) -> None:
    input_dir = project_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_file = input_dir / "test.txt"
    input_file.write_text("Hello world. This is test content for slicing.", encoding="utf-8")

    workspace = WorkspacePaths(project_root=project_root)
    task_config = SliceSummaryTaskConfig(
        role_name="TestChar",
        input_files=("test.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=1),
    )
    llm_client = LlmClient(
        config=LlmConfig(base_url="http://localhost", api_key="test", model_name="test"),
        net_client=NetClient(NetConfig()),
    )
    log_writer = NullWriter(LogPolicy(), LogPathConfig(root_dir=project_root / "logs"))

    executor = TaskExecutor(
        config=task_config,
        llm_client=llm_client,
        workspace=workspace,
        log_writer=log_writer,
        executor_config=ExecutorConfig(),
    )

    stage = PrepareStage()
    assert isinstance(executor.config, SliceSummaryTaskConfig)
    result = asyncio.run(stage.execute(executor, executor.config))

    assert result.ok is True
    assert len(executor.state.slice_states) > 0
    assert "slice_contents" in executor.state.metadata
