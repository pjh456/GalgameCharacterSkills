from __future__ import annotations

import json
from pathlib import Path

import click

from ..core.paths import WorkspacePaths
from .config import resolve_config


@click.command()
@click.option("--task-id", required=True, help="要检查的任务 ID")
@click.option("--output-dir", default="./output", help="输出目录")
@click.option("--config", "config_file", default=None, help="配置文件路径 (YAML)")
@click.pass_context
def check(
    ctx: click.Context,
    task_id: str,
    output_dir: str,
    config_file: str | None,
) -> None:
    """查看任务执行状态"""

    resolve_config(ctx, value=config_file)

    workspace = WorkspacePaths(project_root=Path(output_dir))
    checkpoint_path = workspace.checkpoints_dir / f"{task_id}.json"
    summary_path = workspace.summaries_dir / f"{task_id}_summary.md"
    skills_dir = workspace.skills_dir

    click.echo(f"任务 ID: {task_id}")
    click.echo(f"Checkpoint: {checkpoint_path}")

    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)
            state = data.get("task_state", {})
            slices = state.get("slices", [])
            total = len(slices)
            completed = sum(1 for s in slices if s.get("status") == "completed")
            failed = sum(1 for s in slices if s.get("status") == "failed")
            click.echo(f"当前阶段: {state.get('stage', 'unknown')}")
            click.echo(f"切片进度: {completed}/{total} 完成, {failed} 失败")
            click.echo(f"状态: {state.get('status', 'unknown')}")
            if state.get("error_message"):
                click.echo(f"错误信息: {state['error_message']}")
        except Exception as e:
            click.echo(f"读取 checkpoint 失败: {e}")
    else:
        click.echo(f"Checkpoint 不存在: 任务 {task_id} 尚未运行")
        if summary_path.exists():
            click.echo(f"Summary 文件存在: {summary_path}")
        skills_exists = skills_dir.exists()
        if skills_exists and list(skills_dir.glob(f"{task_id}*")):
            click.echo(f"技能文件存在于: {skills_dir}")

    click.echo(f"Summary: {summary_path} ({'存在' if summary_path.exists() else '不存在'})")
