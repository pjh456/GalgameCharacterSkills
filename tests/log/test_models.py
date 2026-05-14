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


def test_log_record_to_text() -> None:
    """验证 LogRecord.to_text 会输出基础字段、可选字段与排序后的结构化数据"""
    base_record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )
    optional_record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="fs",
        task_id="task-001",
        data={"b": 2, "a": 1},
    )

    base_text = base_record.to_text()
    optional_text = optional_record.to_text()

    assert base_text == f"{base_record.timestamp.isoformat(timespec='seconds')} | {base_record.level.upper()} | {base_record.message}"
    assert optional_text.startswith(
        f"{optional_record.timestamp.isoformat(timespec='seconds')} | {optional_record.level.upper()}"
    )
    assert f" | {optional_record.module} | " in optional_text
    assert f"task={optional_record.task_id}" in optional_text
    assert optional_text.index('"a": 1') < optional_text.index('"b": 2')


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
