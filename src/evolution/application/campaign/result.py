"""Calculated outcomes of a synthesis campaign."""

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from evolution.application.synthesis.result import SynthesisResult


class CampaignResults(BaseModel):
    """Results from an evolutionary algorithm synthesis campaign."""

    results: dict[str, SynthesisResult] = Field(default_factory=dict)

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
