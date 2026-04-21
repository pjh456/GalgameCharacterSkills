from dataclasses import dataclass
from typing import Generic, TypeVar

from ..domain import SummarizeRequest, GenerateSkillsRequest, GenerateCharacterCardRequest

RequestT = TypeVar("RequestT")


@dataclass(frozen=True)
class BasePreparedTask(Generic[RequestT]):
    request_data: RequestT
    config: dict
    checkpoint_id: str


@dataclass(frozen=True)
class PreparedSummarizeTask(BasePreparedTask[SummarizeRequest]):
    pass


@dataclass(frozen=True)
class PreparedGenerateSkillsTask(BasePreparedTask[GenerateSkillsRequest]):
    messages: list
    all_results: list
    iteration: int


@dataclass(frozen=True)
class PreparedGenerateCharacterCardTask(BasePreparedTask[GenerateCharacterCardRequest]):
    fields_data: dict
    messages: list
    iteration_count: int


__all__ = [
    "BasePreparedTask",
    "PreparedSummarizeTask",
    "PreparedGenerateSkillsTask",
    "PreparedGenerateCharacterCardTask",
]
