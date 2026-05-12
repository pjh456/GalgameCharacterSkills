from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gal_chara_skill.conf import settings


@pytest.fixture(autouse=True)
def reset_global_settings() -> None:
    settings._settings_singleton = None
    yield
    settings._settings_singleton = None


@pytest.fixture
def project_root() -> Path:
    temp_dir = TemporaryDirectory()
    original_cwd = Path.cwd()
    os.chdir(temp_dir.name)
    try:
        yield Path(temp_dir.name)
    finally:
        os.chdir(original_cwd)
        temp_dir.cleanup()
