"""根路径路由注册模块。"""

from flask import render_template


def register_root_routes(app) -> None:
    """注册根路径路由。"""

    @app.route("/")
    def index():
        return render_template("index.html")


__all__ = ["register_root_routes"]
