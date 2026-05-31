from __future__ import annotations

import os
from typing import Any

import click

from ..fs.yaml import YamlIO


def resolve_config(
    ctx: click.Context,
    param: click.Parameter | None = None,
    value: str | None = None,
) -> None:
    """解析配置文件并将值合并到 ctx.default_map（优先级最低的 layer）。"""

    if value is not None:
        try:
            read_result = YamlIO.read(value)
            config_data = read_result.unwrap() if read_result.ok else {}
        except Exception as e:
            raise click.BadParameter(f"无法读取配置文件: {value}") from e

        if ctx.default_map is None:
            ctx.default_map = {}
        if isinstance(ctx.default_map, dict):
            _merge_defaults(ctx.default_map, config_data)


def _merge_defaults(dest: dict[str, Any] | Any, src: dict[str, Any]) -> None:
    if not isinstance(dest, dict):
        return
    for key, val in src.items():
        if key not in dest:
            dest[key] = val


def resolve_env_defaults(ctx: click.Context) -> None:
    """从环境变量注入 LLM 默认值（优先级在 CLI 之下、config file 之上）。"""
    env_defaults: dict[str, Any] = {}
    if os.environ.get("OPENAI_API_KEY"):
        env_defaults["api_key"] = os.environ["OPENAI_API_KEY"]
    if os.environ.get("OPENAI_BASE_URL"):
        env_defaults["base_url"] = os.environ["OPENAI_BASE_URL"]
    if os.environ.get("OPENAI_MODEL"):
        env_defaults["model"] = os.environ["OPENAI_MODEL"]
    if os.environ.get("PROVIDER"):
        env_defaults["provider"] = os.environ["PROVIDER"]
    if os.environ.get("LOG_LEVEL"):
        env_defaults["log_level"] = os.environ["LOG_LEVEL"]
    if os.environ.get("OUTPUT_DIR"):
        env_defaults["output_dir"] = os.environ["OUTPUT_DIR"]

    if env_defaults:
        if ctx.default_map is None:
            ctx.default_map = {}
        if isinstance(ctx.default_map, dict):
            _merge_defaults(ctx.default_map, env_defaults)
