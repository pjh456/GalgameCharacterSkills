from __future__ import annotations

import tiktoken
from typing import ClassVar

from numpydoc_decorator import doc


@doc(summary="文本切片工具类")
class Slicer:
    _TOKENIZER: ClassVar = tiktoken.get_encoding("cl100k_base")

    @staticmethod
    @doc(
        summary="计算文本的 token 数量",
        parameters={"text": "需要计算的文本"},
        returns="token 数量",
    )
    def count_tokens(text: str) -> int:
        return len(Slicer._TOKENIZER.encode(text))

    @staticmethod
    @doc(
        summary="将文本按 token 上限切分为多个片段，均分行以保持语义完整",
        parameters={
            "text": "需要切分的文本",
            "max_tokens": "每个切片允许的最大 token 数",
        },
        returns="切片文本列表",
    )
    def slice_text(text: str, max_tokens: int) -> list[str]:
        if max_tokens <= 0:
            return [text]

        total_tokens = Slicer.count_tokens(text)
        slice_count = max(1, (total_tokens // max_tokens) + 1)
        lines = text.splitlines(keepends=True)

        if not lines:
            return [""]

        lines_per_slice = max(1, len(lines) // slice_count)
        slices: list[str] = []

        for i in range(slice_count):
            start = i * lines_per_slice
            end = (i + 1) * lines_per_slice if i < slice_count - 1 else len(lines)
            slices.append("".join(lines[start:end]))

        return slices


__all__ = ["Slicer"]
