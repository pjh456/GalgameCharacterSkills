from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


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
