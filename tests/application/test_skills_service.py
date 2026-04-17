from types import SimpleNamespace

from galgame_character_skills.application import skills_service


def test_generate_skills_task_resume_checkpoint_failure_passthrough(monkeypatch):
    runtime = SimpleNamespace(
        clean_vndb_data=lambda x: x,
        checkpoint_gateway=object(),
    )
    monkeypatch.setattr(
        skills_service,
        "load_resumable_checkpoint",
        lambda gateway, checkpoint_id: {"success": False, "message": "resume failed"},
    )

    result = skills_service.run_generate_skills_task(
        {"role_name": "A", "resume_checkpoint_id": "ckpt-1"},
        runtime,
    )
    assert result == {"success": False, "message": "resume failed"}


def test_generate_skills_task_fails_when_summary_files_missing(monkeypatch):
    runtime = SimpleNamespace(
        clean_vndb_data=lambda x: x,
        checkpoint_gateway=SimpleNamespace(create_checkpoint=lambda **kwargs: "ckpt-1"),
        estimate_tokens=lambda text: 10,
        get_base_dir=lambda: "/base",
    )
    monkeypatch.setattr(skills_service, "find_role_summary_markdown_files", lambda base, role: [])

    result = skills_service.run_generate_skills_task({"role_name": "A"}, runtime)

    assert result["success"] is False
    assert result["message"] == '未找到角色 "A" 的归纳文件，请先完成归纳'
