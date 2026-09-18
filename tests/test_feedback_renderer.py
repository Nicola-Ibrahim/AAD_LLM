"""Unit tests for FeedbackRenderer prompt infrastructure."""

import numpy as np

from evolution.domain.enums import SynthesisMode
from evolution.domain.interfaces.problem import BaseProblem
from evolution.domain.vos.evaluation_result import AlgorithmEvaluationResult
from evolution.domain.vos.iteration import IterationMetadata
from evolution.domain.vos.metrics import (
    Code,
    Convergence,
    Error,
    Execution,
    Fitness,
)
from evolution.infra.engines.llamea.prompts.feedback import (
    FeedbackRenderer,
)


class DummyProblem(BaseProblem):
    """Simple test problem fixture for feedback rendering tests."""

    def __init__(
        self, noise_std: float = 0.0, true_optimum: float = 0.0, problem_id: int = 1, dim: int = 2
    ):
        self.problem_id = problem_id
        self.dim = dim
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
        return np.array([-5.0] * self.dim)

    @property
    def upper_bound(self) -> np.ndarray:
        return np.array([5.0] * self.dim)

    def __call__(self, x: np.ndarray) -> float:
        self._evals += 1
        return float(np.sum(np.asarray(x) ** 2)) + self.true_optimum

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
        return float(np.sum(np.asarray(x) ** 2)) + self.true_optimum


def _make_metadata(
    timed_out: bool = False,
    error_type: str | None = None,
    error_message: str | None = None,
    final_error: float | None = None,
) -> IterationMetadata:
    return IterationMetadata(
        algorithm_name="TestAlgo",
        execution=Execution(
            timed_out=timed_out,
            runtime_seconds=0.1,
            llm_generation_time=0.5,
            evaluations_used=10,
            budget_consumed_pct=1.0,
            evals_per_second=100.0,
        ),
        fitness=Fitness(
            raw_fitness=0.0 if final_error is not None else None,
            final_error=final_error,
            relative_error=final_error,
            error_per_evaluation=final_error / 10 if final_error is not None else None,
        ),
        code=Code(code_lines=15, code_length=200, code_path=None),
        error=Error(error_type=error_type, error_message=error_message, error_traceback=None),
        convergence=Convergence.evaluate(final_error, 1e-6),
    )


def test_render_clean_success():
    """Verify clean success feedback formatting without warnings."""
    renderer = FeedbackRenderer()
    problem = DummyProblem(noise_std=0.0)
    metadata = _make_metadata(final_error=0.005)

    result = AlgorithmEvaluationResult(
        fitness_score=-0.005,
        final_error=0.005,
        is_failure=False,
        is_stagnated=False,
        metadata=metadata,
    )

    feedback = renderer.render(result, problem)
    assert "[RESULT]" in feedback
    assert "The generated algorithm executed successfully." in feedback
    assert "Final objective error:\n0.0050" in feedback
    assert "[META-FEEDBACK]" not in feedback
    assert "NumPy/Runtime Warnings" not in feedback


def test_render_stochastic_success():
    """Verify stochastic success feedback formatting."""
    renderer = FeedbackRenderer()
    problem = DummyProblem(noise_std=0.5)
    metadata = _make_metadata(final_error=1.2e-5)

    result = AlgorithmEvaluationResult(
        fitness_score=-1.2e-5,
        final_error=1.2e-5,
        is_failure=False,
        is_stagnated=False,
        metadata=metadata,
    )

    feedback = renderer.render(result, problem)
    assert "[RESULT]" in feedback
    assert "executed successfully on a stochastic objective" in feedback
    assert "Final objective error:\n1.200000e-05" in feedback


def test_render_timeout_failure():
    """Verify timeout failure feedback formatting with problem context footer."""
    renderer = FeedbackRenderer()
    problem = DummyProblem(problem_id=3, dim=5)
    metadata = _make_metadata(
        timed_out=True, error_type="AlgorithmTimeoutException", error_message="Timed out"
    )

    result = AlgorithmEvaluationResult(
        fitness_score=-4.0e8,
        final_error=None,
        is_failure=True,
        is_stagnated=False,
        metadata=metadata,
    )

    feedback = renderer.render(result, problem)
    assert "[TIMEOUT]" in feedback
    assert "exceeded the execution time limit" in feedback
    assert "Problem context: BBOB-3, dim=5, bounds=[-5.0, 5.0]." in feedback


def test_render_runtime_error_with_code_context():
    """Verify runtime error feedback formatting with extracted code lines."""
    renderer = FeedbackRenderer()
    problem = DummyProblem(problem_id=8, dim=3)
    metadata = _make_metadata(
        timed_out=False,
        error_type="ZeroDivisionError",
        error_message="division by zero",
    )

    result = AlgorithmEvaluationResult(
        fitness_score=-4.5e8,
        final_error=None,
        is_failure=True,
        is_stagnated=False,
        metadata=metadata,
        code_context="  -> line   8: x = 1 / 0",
    )

    feedback = renderer.render(result, problem)
    assert "[RUNTIME ERROR]" in feedback
    assert "ZeroDivisionError: division by zero" in feedback
    assert "Relevant code:\n  -> line   8: x = 1 / 0" in feedback
    assert "Problem context: BBOB-8, dim=3, bounds=[-5.0, 5.0]." in feedback


def test_render_captured_warnings():
    """Verify NumPy warning footer appending."""
    renderer = FeedbackRenderer()
    problem = DummyProblem()
    metadata = _make_metadata(final_error=0.1)

    result = AlgorithmEvaluationResult(
        fitness_score=-0.1,
        final_error=0.1,
        is_failure=False,
        is_stagnated=False,
        metadata=metadata,
        captured_warnings=["RuntimeWarning: invalid value encountered in sqrt"],
    )

    feedback = renderer.render(result, problem)
    assert "NumPy/Runtime Warnings raised during execution" in feedback
    assert "invalid value encountered in sqrt" in feedback


def test_render_stagnation_meta_feedback():
    """Verify [META-FEEDBACK] diversity injection appending when stagnated."""
    renderer = FeedbackRenderer()
    problem = DummyProblem()
    metadata = _make_metadata(error_type="ValueError", error_message="Bad value")

    result = AlgorithmEvaluationResult(
        fitness_score=-4.5e8,
        final_error=None,
        is_failure=True,
        is_stagnated=True,
        metadata=metadata,
    )

    feedback = renderer.render(result, problem)
    assert "[META-FEEDBACK]" in feedback
    assert "The last several generated algorithms failed to execute correctly." in feedback
    assert "Try a substantially different search mechanism" in feedback


def test_render_noisy_failure_context():
    """Verify [NOISY PROBLEM CONTEXT] footer when problem is stochastic."""
    renderer = FeedbackRenderer()
    problem = DummyProblem(noise_std=1.0)
    metadata = _make_metadata(error_type="RuntimeError", error_message="Execution failed")

    result = AlgorithmEvaluationResult(
        fitness_score=-5.0e8,
        final_error=None,
        is_failure=True,
        is_stagnated=False,
        metadata=metadata,
    )

    feedback = renderer.render(result, problem)
    assert "[NOISY PROBLEM CONTEXT]" in feedback
    assert "The objective function is stochastic." in feedback
