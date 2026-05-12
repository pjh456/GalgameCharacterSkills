from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from gal_chara_skill.log.models import LogRecord


def test_log_record_default_module() -> None:
    """验证 LogRecord 默认无模块名"""
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    assert record.module is None


def test_log_record_default_task_id() -> None:
    """验证 LogRecord 默认无任务编号"""
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    assert record.task_id is None


def test_log_record_default_data() -> None:
    """验证 LogRecord 默认附加数据为空字典"""
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    assert record.data == {}


def test_log_record_frozen() -> None:
    """验证 LogRecord 为不可变数据类"""
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    with pytest.raises(FrozenInstanceError):
        record.message = "updated"  # pyright: ignore[reportAttributeAccessIssue]
