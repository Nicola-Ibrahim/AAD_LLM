"""Application synthesis session result contract.

Defines the strongly-typed DTO returned upon completion of an algorithm synthesis run.
"""

from dataclasses import dataclass, field
from typing import Any

from evolution.domain.enums import SynthesisMode


@dataclass
class SessionResult:
    """Contract returned per-problem run by an evolutionary synthesis engine."""

    problem_id: int
    dim: int
    mode: SynthesisMode
    noise_std: float
    experiment_id: int
    best_error: float | None = None
    run_history: list[Any] = field(default_factory=list)
    experiment_name: str = ""
    llm_name: str = ""
    error_msg: str = ""
    best_solution: Any = None
    problem_profile: Any = None
