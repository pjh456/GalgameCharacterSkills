from __future__ import annotations

from gal_chara_skill.net.request import RequestBuilder


def test_raw_body() -> None:
    """验证 raw_body 在传入字节串时会原样返回"""
    body = b"hello"

    result = RequestBuilder.raw_body(body, encoding="utf-8")

    assert result is body


def test_query_items() -> None:
    """验证 query_items 会把序列值保留为 doseq 可识别的列表"""
    items = RequestBuilder.query_items(
        {
            "tag": ("a", "b"),
            "page": 2,
        }
    )

    assert items == [("tag", ["a", "b"]), ("page", 2)]
