"""Checkpoint 路由注册模块。"""

from flask import request

from ..api.checkpoint_api import CheckpointApi


def register_checkpoint_routes(app, runtime, adapter) -> None:
    """注册 checkpoint 相关路由。"""
    checkpoint_api = CheckpointApi(runtime)

    @app.route("/api/checkpoints", methods=["GET"])
    def list_checkpoints():
        task_type = request.args.get("task_type")
        status = request.args.get("status")
        return adapter.run(checkpoint_api.list_checkpoints, task_type=task_type, status=status)

    @app.route("/api/checkpoints/<checkpoint_id>", methods=["GET"])
    def get_checkpoint(checkpoint_id):
        return adapter.run(checkpoint_api.get_checkpoint, checkpoint_id)

    @app.route("/api/checkpoints/<checkpoint_id>", methods=["DELETE"])
    def delete_checkpoint(checkpoint_id):
        return adapter.run(checkpoint_api.delete_checkpoint, checkpoint_id)

    @app.route("/api/checkpoints/<checkpoint_id>/resume", methods=["POST"])
    def resume_checkpoint(checkpoint_id):
        return adapter.run_with_body(checkpoint_api.resume_checkpoint, checkpoint_id)


__all__ = ["register_checkpoint_routes"]
