from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gal_chara_skill.conf.module.log import LogPathConfig
from gal_chara_skill.log.writer import LogWriter


@pytest.fixture
def project_root() -> Iterator[Path]:
    temp_dir = TemporaryDirectory()
    original_cwd = Path.cwd()
    os.chdir(temp_dir.name)
    try:
        yield Path(temp_dir.name)
    finally:
        os.chdir(original_cwd)
        temp_dir.cleanup()


@pytest.fixture
def log_path_config(project_root: Path) -> LogPathConfig:
    return LogPathConfig(root_dir=project_root / "tmp_logs", default_file_name="test.log")


@pytest.fixture(autouse=True)
def reset_log_locks() -> None:
    LogWriter._locks_by_path.clear()
