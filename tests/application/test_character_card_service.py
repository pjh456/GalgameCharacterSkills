from types import SimpleNamespace

from galgame_character_skills.application import character_card_service


def test_generate_character_card_task_resume_checkpoint_failure_passthrough(monkeypatch):
    runtime = SimpleNamespace(
        clean_vndb_data=lambda x: x,
        checkpoint_gateway=object(),
    )
    monkeypatch.setattr(
        character_card_service,
        "load_resumable_checkpoint",
        lambda gateway, checkpoint_id: {"success": False, "message": "resume failed"},
    )

    result = character_card_service.run_generate_character_card_task(
        {"role_name": "A", "resume_checkpoint_id": "ckpt-1"},
        runtime,
    )
    assert result == {"success": False, "message": "resume failed"}


def test_generate_character_card_task_fails_when_analysis_file_missing(monkeypatch):
    runtime = SimpleNamespace(
        clean_vndb_data=lambda x: x,
        checkpoint_gateway=SimpleNamespace(create_checkpoint=lambda **kwargs: "ckpt-1"),
        get_base_dir=lambda: "/base",
    )
    monkeypatch.setattr(character_card_service, "find_role_analysis_summary_file", lambda base, role: "")

    result = character_card_service.run_generate_character_card_task({"role_name": "A"}, runtime)

    assert result["success"] is False
    assert result["message"] == '未找到角色 "A" 的分析文件，请先完成归纳'


def test_generate_character_card_task_fails_when_analysis_read_error(monkeypatch):
    runtime = SimpleNamespace(
        clean_vndb_data=lambda x: x,
        checkpoint_gateway=SimpleNamespace(create_checkpoint=lambda **kwargs: "ckpt-1"),
        get_base_dir=lambda: "/base",
        storage_gateway=SimpleNamespace(read_json=lambda _: (_ for _ in ()).throw(RuntimeError("bad read"))),
    )
    monkeypatch.setattr(
        character_card_service,
        "find_role_analysis_summary_file",
        lambda base, role: "/tmp/analysis.json",
    )

    result = character_card_service.run_generate_character_card_task({"role_name": "A"}, runtime)

    assert result["success"] is False
    assert result["message"] == "读取分析文件失败: bad read"
