from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkillsResumeState:
    messages: list = field(default_factory=list)
    all_results: list = field(default_factory=list)
    iteration: int = 0


@dataclass(frozen=True)
class CharacterCardResumeState:
    fields_data: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    iteration_count: int = 0


__all__ = ["SkillsResumeState", "CharacterCardResumeState"]
