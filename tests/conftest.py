from __future__ import annotations

from pathlib import Path

import pytest

from gal_chara_skill.conf import settings


@pytest.fixture(autouse=True)
def reset_global_settings() -> None:
    settings._settings_singleton = None
    yield
    settings._settings_singleton = None


@pytest.fixture
def project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path
