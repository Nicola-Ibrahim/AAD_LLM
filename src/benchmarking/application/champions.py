"""Typed champion records shared by champion selection and persistence."""

from typing import TypedDict
from enum import StrEnum


class GenerationMode(StrEnum):
    """Recorded candidate origin; not a synthesis prompting policy."""

    EXPLICIT = "explicit"
    IMPLICIT = "implicit"


class Champion(TypedDict, total=False):
    problem_id: int
    dim: int
    mode: str
    noise_std: float
    prompt_strategy: str
    experiment_id: int
    iteration_id: int
    algorithm_name: str
    final_error: float
    evaluations_used: int | None
    code_path: str
    llm_name: str


ChampionCatalog = dict[str, dict[str, Champion]]
