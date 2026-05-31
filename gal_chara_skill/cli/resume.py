from __future__ import annotations

from pathlib import Path
from typing import Literal

import click

from ..conf.module.executor import ExecutorConfig
from ..conf.module.llm import LlmConfig
from ..conf.module.log import LogPathConfig, LogPolicy
from ..conf.module.net import NetConfig
from ..conf.runtime import RuntimeConfig
from ..conf.task import SliceSummaryTaskConfig
from ..core.paths import WorkspacePaths
from ..engine.engine import Engine
from ..llm.providers.registry import resolve_provider
from .config import resolve_config, resolve_env_defaults


@click.command()
@click.option("--task-id", required=True, help="要恢复的任务 ID")
@click.option("--provider", default="openai", help="LLM provider 名称（覆盖 checkpoint 配置）")
@click.option("--api-key", envvar="OPENAI_API_KEY", default=None, help="API 密钥（覆盖 checkpoint 配置）")
@click.option("--base-url", default=None, help="API 基础地址（覆盖 checkpoint 配置）")
@click.option("--model", default=None, help="模型名称（覆盖 checkpoint 配置）")
@click.option("--output-dir", default="./output", help="输出目录")
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    help="日志级别",
)
@click.option("--config", "config_file", default=None, help="配置文件路径 (YAML)")
@click.pass_context
def resume(
    ctx: click.Context,
    task_id: str,
    provider: str,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    output_dir: str,
    log_level: str,
    config_file: str | None,
) -> None:
    """从 checkpoint 恢复任务执行"""

    resolve_config(ctx, value=config_file)
    resolve_env_defaults(ctx)

    api_key = api_key or "dummy-key"
    base_url = base_url or "https://api.openai.com"
    model = model or "gpt-4o"

    llm_config = LlmConfig(base_url=base_url, api_key=api_key, model_name=model, provider=provider)
    resolve_provider(provider)

    project_root = Path(output_dir)
    workspace_paths = WorkspacePaths(project_root=project_root)

    log_path_config = LogPathConfig(root_dir=project_root)
    log_level_typed: Literal["debug", "info", "warning", "error"] = log_level  # type: ignore[assignment]
    log_policy = LogPolicy(level=log_level_typed, write_to_console=True, write_to_file=True)

    runtime = RuntimeConfig(
        llm_config=llm_config,
        net_config=NetConfig(),
        workspace_paths=workspace_paths,
        executor_config=ExecutorConfig(),
        log_policy=log_policy,
        log_path_config=log_path_config,
    )

    engine = Engine(runtime)

    task_config = SliceSummaryTaskConfig(role_name=task_id, input_files=("",))
    result = engine.resume(task_config)
    if not result.ok:
        click.echo(f"Resume 失败: {result.error}", err=True)
        raise SystemExit(1)
    click.echo(f"Resume 完成: {task_id}")
