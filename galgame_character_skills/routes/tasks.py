"""任务相关路由注册模块。"""

from ..api.task_api import TaskApi


def register_task_routes(app, runtime, adapter) -> None:
    """注册任务相关路由。"""
    task_api = TaskApi(runtime)

    @app.route("/api/summarize", methods=["POST"])
    def summarize():
        return adapter.run_with_body(task_api.summarize)

    @app.route("/api/skills", methods=["POST"])
    def generate_skills():
        return adapter.run_with_body(task_api.dispatch_skills_mode)


__all__ = ["register_task_routes"]
