"""Pure scoring rules for synthesized optimization candidates."""

from dataclasses import dataclass
from enum import Enum
import math


class FailureKind(str, Enum):
    """Failure categories that receive fixed fitness penalties."""

    EXECUTION = "execution"
    RUNTIME = "runtime"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class ScoringResult:
    """Objective gap and fitness derived from a clean objective value."""

    objective_gap: float
    fitness: float


class AlgorithmScoringService:
    """Domain scoring policy, independent of execution, storage, and benchmark adapters."""

    FAILURE_FITNESS = -5.0e8
    RUNTIME_FAILURE_FITNESS = -4.5e8
    TIMEOUT_FAILURE_FITNESS = -4.0e8

    @staticmethod
    def is_failure(score: float) -> bool:
        return not math.isfinite(score) or score <= -4.0e8

    @staticmethod
    def objective_gap(clean_objective: float, true_optimum: float) -> float:
        """Return the nonnegative minimization gap, clamped at zero for roundoff."""
        return max(0.0, float(clean_objective) - float(true_optimum))

    @staticmethod
    def success(clean_objective: float, true_optimum: float) -> ScoringResult:
        gap = AlgorithmScoringService.objective_gap(clean_objective, true_optimum)
        return ScoringResult(objective_gap=gap, fitness=-gap)

    @classmethod
    def failure_score(cls, failure_kind: FailureKind) -> float:
        return {
            FailureKind.EXECUTION: cls.FAILURE_FITNESS,
            FailureKind.RUNTIME: cls.RUNTIME_FAILURE_FITNESS,
            FailureKind.TIMEOUT: cls.TIMEOUT_FAILURE_FITNESS,
        }[failure_kind]
