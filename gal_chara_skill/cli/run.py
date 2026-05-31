from __future__ import annotations

from pathlib import Path
from typing import Literal

import click

from ..conf.module.executor import ExecutorConfig
from ..conf.module.llm import LlmConfig
from ..conf.module.log import LogPathConfig, LogPolicy
from ..conf.module.net import NetConfig
from ..conf.runtime import RuntimeConfig
from ..conf.task import GenerationTaskConfig, SliceConfig, SliceSummaryTaskConfig
from ..core.paths import WorkspacePaths
from ..engine.engine import Engine
from ..llm.providers.registry import resolve_provider
from .config import resolve_config, resolve_env_defaults


@click.command()
@click.option("--input", "input_files", required=True, help="输入文本文件路径")
@click.option("--task-type", type=click.Choice(["summarize", "generate", "both"]), default="summarize", help="任务类型")
@click.option("--provider", default="openai", help="LLM provider 名称")
@click.option("--api-key", envvar="OPENAI_API_KEY", help="API 密钥")
@click.option("--base-url", default="https://api.openai.com", help="API 基础地址")
@click.option("--model", default="gpt-4o", help="模型名称")
@click.option("--role-name", required=True, help="角色名称")
@click.option("--output-dir", default="./output", help="输出目录")
@click.option("--parallelism", type=int, default=1, help="并发切片数")
@click.option("--max-iterations", type=int, default=20, help="工具调用最大轮数")
@click.option("--temperature", type=float, default=0.7, help="模型采样温度")
@click.option("--max-tokens", type=int, default=4096, help="单次输出最大 token 数")
@click.option("--slice-size", type=int, default=16000, help="切片大小 (tokens)")
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    help="日志级别",
)
@click.option("--config", "config_file", default=None, help="配置文件路径 (YAML)")
@click.pass_context
def run(
    ctx: click.Context,
    input_files: str,
    task_type: str,
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    role_name: str,
    output_dir: str,
    parallelism: int,
    max_iterations: int,
    temperature: float,
    max_tokens: int,
    slice_size: int,
    log_level: str,
    config_file: str | None,
) -> None:
    """运行角色人设蒸馏流水线"""

    resolve_config(ctx, value=config_file)
    resolve_env_defaults(ctx)

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
        executor_config=ExecutorConfig(skills_max_iterations=max_iterations),
        log_policy=log_policy,
        log_path_config=log_path_config,
    )

    engine = Engine(runtime)

    if task_type in ("summarize", "both"):
        task_config = SliceSummaryTaskConfig(
            role_name=role_name,
            input_files=(input_files,),
            slice_config=SliceConfig(max_tokens=slice_size, parallelism=parallelism),
        )
        result = engine.run(task_config)
        if not result.ok:
            click.echo(f"Summarize 失败: {result.error}", err=True)
            raise SystemExit(1)
        click.echo(f"Summarize 完成: {role_name}")

    if task_type in ("generate", "both"):
        summary_task_id = role_name
        task_config = GenerationTaskConfig(role_name=role_name, kind="chara_card", summary_task_id=summary_task_id)
        result = engine.run(task_config)
        if not result.ok:
            click.echo(f"Generate 失败: {result.error}", err=True)
            raise SystemExit(1)
        click.echo(f"角色卡生成完成: {role_name}")
