"""Picklable work items passed from campaign planning to synthesis workers."""

from typing import NotRequired, TypedDict

from evolution.application.model_selection import ModelSelection
from evolution.application.synthesis.settings import SynthesisSettings
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.problem import BaseProblem


class ExperimentTask(TypedDict):
    """Typed, picklable payload passed from campaign planning to worker processes."""

    key: str
    problem: BaseProblem
    experiment_id: int
    config: SynthesisSettings
    model: ModelSelection
    initial_iteration: int
    prompt_strategy: PromptStrategy
    synthesis_mode: SynthesisMode
    restart: NotRequired[bool]
