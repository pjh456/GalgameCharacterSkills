"""VNDB 路由注册模块。"""

from ..api.vndb_api_service import get_vndb_info_result
from ..api.vndb_service import fetch_vndb_character


def register_vndb_routes(app, deps, runtime, adapter) -> None:
    """注册 VNDB 相关路由。"""

    @app.route("/api/vndb", methods=["POST"])
    def get_vndb_info():
        return adapter.run_with_body(
            get_vndb_info_result,
            deps.r18_traits,
            runtime.vndb_gateway,
            fetch_vndb_character,
        )


__all__ = ["register_vndb_routes"]
