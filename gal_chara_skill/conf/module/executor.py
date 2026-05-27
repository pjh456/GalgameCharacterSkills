from __future__ import annotations

from dataclasses import dataclass

from numpydoc_decorator import doc


@doc(
    summary="阶段级工具调用配置，控制各阶段的 tool-calling 循环上限",
    parameters={
        "compress_max_iterations": "compress 去重最大轮数",
        "skills_max_iterations": "skills 生成最大轮数",
        "chara_card_max_iterations": "chara_card 生成最大轮数",
    },
)
@dataclass(frozen=True)
class ExecutorConfig:
    compress_max_iterations: int = 30
    skills_max_iterations: int = 15
    chara_card_max_iterations: int = 25


__all__ = ["ExecutorConfig"]
