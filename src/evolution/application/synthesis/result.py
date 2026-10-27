"""Outcome of generating one optimizer."""

from dataclasses import dataclass, field

from evolution.domain.enums import SynthesisMode
from evolution.domain.vos import ProblemProfile


@dataclass(slots=True)
class SynthesisResult:
    """Outcome and summary metadata for one synthesis experiment."""

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
