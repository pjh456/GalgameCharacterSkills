"""文件相关路由注册模块。"""

from flask import request

from ..api.file_api_service import (
    calculate_tokens_result,
    scan_files_result,
    slice_file_result,
    upload_files_result,
)
from ..utils.input_normalization import extract_file_paths


def register_file_routes(app, deps, adapter) -> None:
    """注册文件相关路由。"""

    @app.route("/api/files", methods=["GET"])
    def scan_files():
        return adapter.run(scan_files_result, deps.file_processor)

    @app.route("/api/files/upload", methods=["POST"])
    def upload_files():
        files = request.files.getlist("files")
        return adapter.response(upload_files_result(deps.file_processor, files))

    @app.route("/api/files/tokens", methods=["POST"])
    def calculate_tokens():
        return adapter.run_with_body(lambda data: calculate_tokens_result(deps.file_processor, data))

    @app.route("/api/slice", methods=["POST"])
    def slice_file():
        return adapter.run_with_body(lambda data: slice_file_result(deps.file_processor, data, extract_file_paths))


__all__ = ["register_file_routes"]
