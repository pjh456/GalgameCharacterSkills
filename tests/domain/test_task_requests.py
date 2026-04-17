from galgame_character_skills.domain.task_requests import (
    SummarizeRequest,
    GenerateSkillsRequest,
    GenerateCharacterCardRequest,
)


def _clean_vndb_data(raw):
    if not raw:
        return None
    return {"cleaned": True, "raw": raw}


def _extract_file_paths(payload):
    return payload.get("file_paths", [])


def test_summarize_request_from_payload_and_checkpoint_roundtrip():
    payload = {
        "role_name": "A",
        "instruction": "I",
        "concurrency": 2,
        "mode": "skills",
        "resume_checkpoint_id": "ckpt1",
        "output_language": "zh",
        "vndb_data": {"id": 1},
        "slice_size_k": 80,
        "file_paths": ["a.md"],
    }
    req = SummarizeRequest.from_payload(payload, _clean_vndb_data, _extract_file_paths)
    assert req.role_name == "A"
    assert req.vndb_data["cleaned"] is True
    assert req.file_paths == ["a.md"]

    req.apply_checkpoint({"role_name": "B", "concurrency": 4, "file_paths": ["b.md"]})
    ckpt_input = req.to_checkpoint_input()
    assert ckpt_input["role_name"] == "B"
    assert ckpt_input["concurrency"] == 4
    assert ckpt_input["file_paths"] == ["b.md"]


def test_generate_skills_request_maps_modelname_field():
    req = GenerateSkillsRequest.from_payload(
        {"role_name": "R", "vndb_data": {"x": 1}, "modelname": "m1"},
        _clean_vndb_data,
    )
    assert req.role_name == "R"
    assert req.model_name == "m1"
    assert req.vndb_data["cleaned"] is True


def test_generate_character_card_request_checkpoint_io():
    req = GenerateCharacterCardRequest.from_payload(
        {
            "role_name": "R",
            "creator": "C",
            "vndb_data": {"img": "u"},
            "output_language": "en",
            "compression_mode": "llm",
            "force_no_compression": True,
            "resume_checkpoint_id": "x1",
            "modelname": "gpt",
        },
        _clean_vndb_data,
    )
    req.apply_checkpoint({"creator": "C2", "compression_mode": "original"})
    ckpt_input = req.to_checkpoint_input()
    assert ckpt_input["creator"] == "C2"
    assert ckpt_input["compression_mode"] == "original"
    assert "vndb_data_raw" in ckpt_input
