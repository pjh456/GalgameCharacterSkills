from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from numpydoc_decorator import doc


@doc(
    summary="描述项目运行使用的标准工作区路径布局",
    parameters={"project_root": "工作区根目录"},
)
@dataclass(frozen=True)
class WorkspacePaths:
    project_root: Path

    @property
    def input_dir(self) -> Path:
        return self.project_root / "input"

    @property
    def output_dir(self) -> Path:
        return self.project_root / "output"

    @property
    def slices_dir(self) -> Path:
        return self.output_dir / "slices"

    @property
    def checkpoints_dir(self) -> Path:
        return self.output_dir / "checkpoints"

    @property
    def summaries_dir(self) -> Path:
        return self.output_dir / "summaries"

    @property
    def skills_dir(self) -> Path:
        return self.output_dir / "skills"

    @property
    def cards_dir(self) -> Path:
        return self.output_dir / "cards"

    @property
    def logs_dir(self) -> Path:
        return self.output_dir / "logs"


DEFAULT_WORKSPACE_PATHS = WorkspacePaths(project_root=Path("."))

PROJECT_ROOT = DEFAULT_WORKSPACE_PATHS.project_root  # 根目录
INPUT_DIR = DEFAULT_WORKSPACE_PATHS.input_dir  # 输入文件夹
OUTPUT_DIR = DEFAULT_WORKSPACE_PATHS.output_dir  # 输出文件夹

SLICES_DIR = DEFAULT_WORKSPACE_PATHS.slices_dir  # 切片文件夹
CHECKPOINTS_DIR = DEFAULT_WORKSPACE_PATHS.checkpoints_dir  # 检查点文件夹
SUMMARIES_DIR = DEFAULT_WORKSPACE_PATHS.summaries_dir  # 总结文件夹
SKILLS_DIR = DEFAULT_WORKSPACE_PATHS.skills_dir  # skill 文件夹
CARDS_DIR = DEFAULT_WORKSPACE_PATHS.cards_dir  # 角色卡文件夹
LOGS_DIR = DEFAULT_WORKSPACE_PATHS.logs_dir  # 日志文件夹

__all__ = [
    "WorkspacePaths",
    "DEFAULT_WORKSPACE_PATHS",
    "PROJECT_ROOT",
    "INPUT_DIR",
    "OUTPUT_DIR",
    "SLICES_DIR",
    "CHECKPOINTS_DIR",
    "SUMMARIES_DIR",
    "SKILLS_DIR",
    "CARDS_DIR",
    "LOGS_DIR",
]
