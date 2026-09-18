"""Unit tests for AlgorithmEvaluator domain service."""

import numpy as np
import pytest

from evolution.domain.enums import SynthesisMode
from evolution.domain.interfaces.problem import BaseProblem
from evolution.domain.services.algorithm_evaluator import AlgorithmEvaluator


class DummyProblem(BaseProblem):
    """Simple 2D sphere test problem for domain evaluator tests."""

    def __init__(self, noise_std: float = 0.0, true_optimum: float = 0.0):
        self.problem_id = 1
        self.dim = 2
        self.instance_id = 1
        self.noise_std = noise_std
        self.noise_model = "clean" if noise_std == 0.0 else "additive_gaussian"
        self.true_optimum = true_optimum
        self._evals = 0

    @property
    def mode(self) -> SynthesisMode:
        return SynthesisMode.CLEAN if self.noise_std == 0.0 else SynthesisMode.EXPLICIT

    @property
    def lower_bound(self) -> np.ndarray:
        return np.array([-5.0, -5.0])

    @property
    def upper_bound(self) -> np.ndarray:
        return np.array([5.0, 5.0])

    def __call__(self, x: np.ndarray) -> float:
        self._evals += 1
        arr = np.asarray(x, dtype=float)
        val = float(np.sum(arr**2)) + self.true_optimum
        if self.noise_std > 0.0:
            val += float(np.random.normal(0, self.noise_std))
        return val

    def reset(self) -> None:
        self._evals = 0

    def is_in_bounds(self, x: np.ndarray, tol: float = 1e-5) -> bool:
        arr = np.asarray(x, dtype=float)
        return bool(np.all(arr >= self.lower_bound - tol) and np.all(arr <= self.upper_bound + tol))

    def clip(self, x: np.ndarray) -> np.ndarray:
        return np.clip(x, self.lower_bound, self.upper_bound)

    @property
    def evaluations(self) -> int:
        return self._evals

    def eval_clean(self, x: np.ndarray) -> float:
        arr = np.asarray(x, dtype=float)
        return float(np.sum(arr**2)) + self.true_optimum


def test_is_failure_classification():
    """Verify classification of failure score tiers vs valid fitness scores."""
    assert AlgorithmEvaluator.is_failure(AlgorithmEvaluator.FAILURE_FITNESS) is True
    assert AlgorithmEvaluator.is_failure(AlgorithmEvaluator.RUNTIME_FAILURE_FITNESS) is True
    assert AlgorithmEvaluator.is_failure(AlgorithmEvaluator.TIMEOUT_FAILURE_FITNESS) is True
    assert AlgorithmEvaluator.is_failure(float("-inf")) is True
    assert AlgorithmEvaluator.is_failure(float("nan")) is True

    assert AlgorithmEvaluator.is_failure(0.0) is False
    assert AlgorithmEvaluator.is_failure(-0.05) is False
    assert AlgorithmEvaluator.is_failure(-1000.0) is False
    assert AlgorithmEvaluator.is_failure(-1e6) is False


def test_evaluate_successful_candidate():
    """Verify evaluation of an optimal candidate code."""
    problem = DummyProblem()
    evaluator = AlgorithmEvaluator(problem=problem, budget=100)

    code = """
import numpy as np

class OptimumFinder:
    def __call__(self, problem, budget):
        best_x = np.array([0.0, 0.0])
        best_y = problem(best_x)
        return best_x, best_y
"""
    result = evaluator.evaluate(code=code, name="OptimumFinder")

    assert result.is_failure is False
    assert result.final_error == pytest.approx(0.0, abs=1e-6)
    assert result.fitness_score == pytest.approx(0.0, abs=1e-6)
    assert result.metadata.execution.evaluations_used == 1
    assert result.metadata.convergence.converged is True
    assert result.is_stagnated is False


def test_evaluate_out_of_bounds_candidate():
    """Verify that candidate returning best_x outside domain bounds is penalized."""
    problem = DummyProblem()
    evaluator = AlgorithmEvaluator(problem=problem, budget=100)

    code = """
import numpy as np

class OutOfBoundsSearch:
    def __call__(self, problem, budget):
        # Returns out of bounds coordinate [10.0, 10.0]
        best_x = np.array([10.0, 10.0])
        best_y = problem(best_x)
        return best_x, best_y
"""
    result = evaluator.evaluate(code=code, name="OutOfBoundsSearch")

    assert result.is_failure is True
    assert result.fitness_score == AlgorithmEvaluator.RUNTIME_FAILURE_FITNESS
    assert result.metadata.error.error_type == "ValueError"
    assert "outside search space bounds" in (result.metadata.error.error_message or "")


def test_evaluate_dimension_mismatch():
    """Verify that candidate returning best_x of incorrect dimension is penalized."""
    problem = DummyProblem()
    evaluator = AlgorithmEvaluator(problem=problem, budget=100)

    code = """
import numpy as np

class DimMismatchSearch:
    def __call__(self, problem, budget):
        # Returns 3D coordinate for 2D problem
        best_x = np.array([1.0, 1.0, 1.0])
        best_y = problem(best_x)
        return best_x, best_y
"""
    result = evaluator.evaluate(code=code, name="DimMismatchSearch")

    assert result.is_failure is True
    assert result.fitness_score == AlgorithmEvaluator.RUNTIME_FAILURE_FITNESS
    assert result.metadata.error.error_type == "ValueError"
    assert "expected problem dimension" in (result.metadata.error.error_message or "")


def test_evaluate_runtime_error_feedback():
    """Verify that candidate throwing a runtime error generates structured diagnostics and code context."""
    problem = DummyProblem()
    evaluator = AlgorithmEvaluator(problem=problem, budget=100)

    code = """
class CrashingSearch:
    def __call__(self, problem, budget):
        x = 1 / 0
        return [0.0, 0.0], 0.0
"""
    result = evaluator.evaluate(code=code, name="CrashingSearch")

    assert result.is_failure is True
    assert result.fitness_score == AlgorithmEvaluator.RUNTIME_FAILURE_FITNESS
    assert result.metadata.error.error_type == "ZeroDivisionError"
    assert "division by zero" in (result.metadata.error.error_message or "")
    assert "line   4:" in result.code_context


def test_stagnation_detection_and_meta_feedback():
    """Verify that consecutive failures trigger stagnation detection."""
    problem = DummyProblem()
    evaluator = AlgorithmEvaluator(problem=problem, budget=100, stagnation_threshold=2)

    crashing_code = """
class CrashingSearch:
    def __call__(self, problem, budget):
        raise RuntimeError("Intentional failure")
"""

    # Run 1: first failure
    res1 = evaluator.evaluate(code=crashing_code, name="Crash1")
    assert res1.is_failure is True
    assert res1.is_stagnated is False

    # Run 2: second failure reaches stagnation threshold (2)
    res2 = evaluator.evaluate(code=crashing_code, name="Crash2")
    assert res2.is_failure is True
    assert res2.is_stagnated is True
