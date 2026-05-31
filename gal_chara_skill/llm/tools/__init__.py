from __future__ import annotations

from typing import Any

from .remove_duplicates import REMOVE_DUPLICATES
from .write_field import write_field as _write_field_def
from .write_file import WRITE_FILE


def write_file_tool(provider: Any) -> dict[str, Any]:
    return provider.build_tool_request(WRITE_FILE)


def remove_duplicates_tool(provider: Any) -> dict[str, Any]:
    return provider.build_tool_request(REMOVE_DUPLICATES)


def write_field_tool(field_names: list[str], provider: Any) -> dict[str, Any]:
    return provider.build_tool_request(_write_field_def(field_names))


__all__ = ["write_file_tool", "remove_duplicates_tool", "write_field_tool"]
