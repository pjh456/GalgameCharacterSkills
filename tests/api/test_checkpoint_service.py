from galgame_character_skills.api import checkpoint_service as svc


class DummyCheckpointGateway:
    def __init__(self):
        self._ckpt = {"checkpoint_id": "c1", "task_type": "summarize", "input_params": {"role_name": "r"}}
        self._llm_state = {"messages": []}
        self.deleted = False

    def list_checkpoints(self, task_type=None, status=None):
        return [{"checkpoint_id": "c1", "task_type": task_type, "status": status}]

    def load_checkpoint(self, checkpoint_id):
        if checkpoint_id == "missing":
            return None
        return dict(self._ckpt, checkpoint_id=checkpoint_id)

    def load_llm_state(self, checkpoint_id):
        return self._llm_state

    def delete_checkpoint(self, checkpoint_id):
        if checkpoint_id == "missing":
            return False
        self.deleted = True
        return True


def test_list_get_delete_checkpoint_result():
    gw = DummyCheckpointGateway()

    listed = svc.list_checkpoints_result(gw, task_type="summarize", status="failed")
    assert listed["success"] is True
    assert listed["checkpoints"][0]["task_type"] == "summarize"

    got = svc.get_checkpoint_result(gw, "c1")
    assert got["success"] is True
    assert got["checkpoint"]["checkpoint_id"] == "c1"

    missing = svc.get_checkpoint_result(gw, "missing")
    assert missing["success"] is False

    deleted = svc.delete_checkpoint_result(gw, "c1")
    assert deleted["success"] is True

    del_missing = svc.delete_checkpoint_result(gw, "missing")
    assert del_missing["success"] is False


def test_resume_checkpoint_result_dispatch(monkeypatch):
    gw = DummyCheckpointGateway()

    monkeypatch.setattr(
        svc,
        "load_resumable_checkpoint",
        lambda _gw, _cid: {"success": True, "checkpoint": {"task_type": "generate_skills", "input_params": {"role_name": "a"}}},
    )

    captured = {}

    def summarize_handler(data):
        captured["summarize"] = data
        return {"success": True, "kind": "summarize"}

    def skills_handler(data):
        captured["skills"] = data
        return {"success": True, "kind": "skills"}

    def card_handler(data):
        captured["card"] = data
        return {"success": True, "kind": "card"}

    result = svc.resume_checkpoint_result(
        ckpt_manager=gw,
        checkpoint_id="c9",
        extra_params={"modelname": "m1"},
        summarize_handler=summarize_handler,
        generate_skills_handler=skills_handler,
        generate_chara_card_handler=card_handler,
    )
    assert result["success"] is True
    assert result["kind"] == "skills"
    assert captured["skills"]["resume_checkpoint_id"] == "c9"
    assert captured["skills"]["modelname"] == "m1"


def test_resume_checkpoint_result_unknown_task(monkeypatch):
    gw = DummyCheckpointGateway()
    monkeypatch.setattr(
        svc,
        "load_resumable_checkpoint",
        lambda _gw, _cid: {"success": True, "checkpoint": {"task_type": "unknown", "input_params": {}}},
    )
    result = svc.resume_checkpoint_result(gw, "cx", {}, lambda _: {}, lambda _: {}, lambda _: {})
    assert result["success"] is False
