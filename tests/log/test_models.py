from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from gal_chara_skill.log.models import LogRecord


def test_log_record() -> None:
    """验证 LogRecord 为不可变数据类"""
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    with pytest.raises(FrozenInstanceError):
        record.message = "updated"  # pyright: ignore[reportAttributeAccessIssue]
