from typing import TypedDict

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.synthesis.models import SessionConfig, SessionResult
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.problem import BaseProblem


class CampaignResults(BaseModel):
    """Results from an evolutionary algorithm synthesis campaign."""

    results: dict[str, SessionResult] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def total_tasks(self) -> int:
        return len(self.results)

    @property
    def successful_tasks(self) -> int:
        return sum(
            1
            for r in self.results.values()
            if r.best_error is not None and np.isfinite(r.best_error)
        )

    @property
    def failed_tasks(self) -> int:
        return self.total_tasks - self.successful_tasks


class CampaignTask(TypedDict):
    """Typed, picklable payload passed from campaign planning to worker processes."""

    key: str
    problem: BaseProblem
    experiment_id: int
    config: SessionConfig
    engine: SynthesisEngine
    initial_iteration: int
    prompt_strategy: PromptStrategy
    synthesis_mode: SynthesisMode
