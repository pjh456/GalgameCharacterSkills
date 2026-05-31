from __future__ import annotations

import click

from .check import check
from .ping import ping
from .resume import resume
from .run import run


@click.group()
@click.version_option()
def main() -> None:
    """GalgameCharacterSkills — Galgame 角色人设蒸馏工具"""
    pass


main.add_command(run)
main.add_command(resume)
main.add_command(check)
main.add_command(ping)

__all__ = ["main"]
