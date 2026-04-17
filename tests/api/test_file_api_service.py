from galgame_character_skills.api.file_api_service import (
    scan_files_result,
    calculate_tokens_result,
    slice_file_result,
)


class DummyFileProcessor:
    def __init__(self):
        self.raise_error = False

    def scan_resource_files(self):
        return ["a.md", "b.txt"]

    def calculate_tokens(self, file_path):
        if self.raise_error:
            raise RuntimeError("boom")
        return 12345

    def calculate_slices(self, token_count, slice_size_k=50):
        return 3

    def slice_multiple_files(self, file_paths, slice_size_k=50):
        if self.raise_error:
            raise RuntimeError("slice boom")
        return ["s1", "s2"]


def test_scan_files_result_success():
    result = scan_files_result(DummyFileProcessor())
    assert result["success"] is True
    assert result["files"] == ["a.md", "b.txt"]


def test_calculate_tokens_result_validation_and_error():
    fp = DummyFileProcessor()
    no_path = calculate_tokens_result(fp, {})
    assert no_path["success"] is False

    fp.raise_error = True
    failed = calculate_tokens_result(fp, {"file_path": "x.md"})
    assert failed["success"] is False
    assert "boom" in failed["message"]


def test_calculate_tokens_result_success():
    result = calculate_tokens_result(DummyFileProcessor(), {"file_path": "x.md", "slice_size_k": 40})
    assert result["success"] is True
    assert result["token_count"] == 12345
    assert result["slice_count"] == 3


def test_slice_file_result_validation_and_success():
    fp = DummyFileProcessor()
    extract = lambda data: []
    result = slice_file_result(fp, {}, extract)
    assert result["success"] is False

    extract_ok = lambda data: ["a.md", "b.md"]
    ok = slice_file_result(fp, {"slice_size_k": 50}, extract_ok)
    assert ok["success"] is True
    assert ok["slice_count"] == 2
    assert ok["file_count"] == 2
