from galgame_character_skills.utils.request_config import build_llm_config


def test_build_llm_config_maps_fields_and_keeps_defaults():
    data = {"baseurl": "http://x", "modelname": "m1", "apikey": "k"}
    result = build_llm_config(data)
    assert result == {
        "baseurl": "http://x",
        "modelname": "m1",
        "apikey": "k",
        "max_retries": None,
    }


def test_build_llm_config_converts_zero_like_max_retries_to_none():
    assert build_llm_config({"max_retries": 0})["max_retries"] is None
    assert build_llm_config({"max_retries": ""})["max_retries"] is None


def test_build_llm_config_keeps_positive_max_retries():
    assert build_llm_config({"max_retries": 3})["max_retries"] == 3
