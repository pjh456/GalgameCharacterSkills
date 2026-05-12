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

__all__ = [
    "WorkspacePaths",
]
