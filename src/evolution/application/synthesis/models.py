"""Data models shared by the single-session and campaign synthesis workflows."""

from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict, Field

from evolution.domain.enums import SynthesisMode
from evolution.domain.vos import ProblemProfile


class SessionConfig(BaseModel):
    """Runtime budgets and stopping criteria for one synthesis session."""

    budget: int = Field(default=1_000_000, ge=1)
    timeout_seconds: float = Field(default=30.0, gt=0.0)
    iterations: int = Field(default=10, ge=1)
    stagnation_threshold: int = Field(default=3, ge=1)
    convergence_threshold: float = Field(default=1e-6, ge=0.0)

    model_config = ConfigDict(frozen=True)


@dataclass(slots=True)
class SessionResult:
    """Outcome and summary metadata for one synthesis session."""

    problem_id: int
    dim: int
    mode: SynthesisMode
    noise_std: float
    experiment_id: int
    best_error: float | None = None
    run_history: list[object] = field(default_factory=list)
    experiment_name: str = ""
    llm_name: str = ""
    error_msg: str = ""
    best_solution: object | None = None
    problem_profile: ProblemProfile | None = None
