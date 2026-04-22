"""归纳与配置相关路由注册模块。"""

from ..api.config_api_service import get_config_result
from ..api.context_api_service import get_context_limit_result
from ..api.summary_api_service import get_summary_files_result, scan_summary_roles_result
from ..files import discover_summary_roles, find_summary_files_for_role
from ..llm.budget import get_model_context_limit
from ..workspace import get_workspace_summaries_dir


def register_summary_routes(app, adapter, get_app_settings_fn) -> None:
    """注册归纳与配置相关路由。"""

    @app.route("/api/config", methods=["GET"])
    def get_config():
        return adapter.run(get_config_result, get_app_settings_fn)

    @app.route("/api/summaries/roles", methods=["GET"])
    def scan_summary_roles():
        return adapter.run(scan_summary_roles_result, get_workspace_summaries_dir, discover_summary_roles)

    @app.route("/api/summaries/files", methods=["POST"])
    def get_summary_files():
        return adapter.run_with_body(get_summary_files_result, get_workspace_summaries_dir, find_summary_files_for_role)

    @app.route("/api/context-limit", methods=["POST"])
    def get_context_limit():
        return adapter.run_with_body(get_context_limit_result, get_model_context_limit)


__all__ = ["register_summary_routes"]
