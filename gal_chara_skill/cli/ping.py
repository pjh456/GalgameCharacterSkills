from __future__ import annotations

import asyncio

import click

from ..conf.module.llm import LlmConfig
from ..conf.module.net import NetConfig
from ..llm.client import LlmClient
from ..llm.models import ChatMessage
from ..llm.providers.registry import resolve_provider
from ..net.client import NetClient


@click.command()
@click.option("--provider", default="openai", help="LLM provider 名称")
@click.option("--api-key", envvar="OPENAI_API_KEY", required=True, help="API 密钥")
@click.option("--base-url", default="https://api.openai.com", help="API 基础地址")
@click.option("--model", default="gpt-4o", help="模型名称")
def ping(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
) -> None:
    """测试 LLM 连接"""

    llm_config = LlmConfig(base_url=base_url, api_key=api_key, model_name=model, provider=provider)
    resolve_provider(provider)

    net_client = NetClient(NetConfig())
    client = LlmClient(config=llm_config, net_client=net_client)

    click.echo(f"Provider: {provider}")
    click.echo(f"Model: {model}")
    click.echo(f"Base URL: {base_url}")
    click.echo("连接测试中...")

    async def _ping() -> None:
        result = await client.acomplete(
            [ChatMessage(role="user", content="Hi")],
            max_tokens=5,
        )
        if result.ok:
            click.echo("✓ 连接成功")
        else:
            click.echo(f"✗ 连接失败: {result.error}", err=True)
            raise SystemExit(1)

    asyncio.run(_ping())
