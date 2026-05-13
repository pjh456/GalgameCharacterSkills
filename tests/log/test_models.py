from __future__ import annotations

from datetime import datetime

from gal_chara_skill.log.models import LogRecord


def test_log_record_to_dict_and_from_dict() -> None:
    """验证 LogRecord 可以在字典与模型之间往返转换"""
    source = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="fs",
        task_id="task-001",
        data={"count": 2},
    )

    restored = LogRecord.from_dict(source.to_dict()).unwrap()

    assert restored == source


def test_log_record_from_dict_invalid_shape() -> None:
    """验证 LogRecord.from_dict 会拒绝非法结构"""
    not_dict_result = LogRecord.from_dict([])
    invalid_data_result = LogRecord.from_dict(
        {
            "level": "info",
            "message": "hello",
            "timestamp": "2026-05-12T10:30:45",
            "data": [],
        }
    )
    missing_field_result = LogRecord.from_dict(
        {
            "level": "info",
            "message": "hello",
        }
    )

    assert not_dict_result.ok is False
    assert invalid_data_result.ok is False
    assert missing_field_result.ok is False
