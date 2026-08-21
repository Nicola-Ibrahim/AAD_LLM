import numpy as np

from domain.enums import ProblemMode
from domain.services.noise_strategy import NoNoiseStrategy
from infra.problems.bbob import BBOBProblem
from synthesis.prompts import PromptStrategy, build_task_prompt


def test_build_task_prompt_with_array_bounds():
    problem = BBOBProblem(problem_id=1, dim=3, noise_strategy=NoNoiseStrategy(), instance_id=1)
    assert isinstance(problem.lower_bound, np.ndarray)
    assert isinstance(problem.upper_bound, np.ndarray)
    assert problem.lower_bound.shape == (3,)
    assert problem.upper_bound.shape == (3,)

    prompt = build_task_prompt(
        problem_id=problem.problem_id,
        dim=problem.dim,
        lower_bound=problem.lower_bound,
        upper_bound=problem.upper_bound,
        mode=ProblemMode.CLEAN,
    )

    assert "BBOB Problem ID: 1" in prompt
    assert "[-5.0, -5.0, -5.0]" in prompt or "[-5.0, -5.0, -5.0]" in str(
        problem.lower_bound.tolist()
    )
    assert prompt is not None


def test_build_task_prompt_noisy():
    prompt = build_task_prompt(
        problem_id=2,
        dim=5,
        lower_bound=np.array([-5.0] * 5),
        upper_bound=np.array([5.0] * 5),
        mode=ProblemMode.NOISY,
    )

    assert "stochastic" in prompt or "noise" in prompt
    assert "BBOB Problem ID: 2" in prompt
    assert "5-dimensional" in prompt


def test_build_task_prompt_strategies():
    lb = np.array([-5.0] * 3)
    ub = np.array([5.0] * 3)

    baseline_prompt = build_task_prompt(1, 3, lb, ub, strategy=PromptStrategy.BASELINE)
    assert "population" not in baseline_prompt.lower()
    assert "vectorized updates" not in baseline_prompt.lower()

    thinking_prompt = build_task_prompt(1, 3, lb, ub, strategy=PromptStrategy.THINKING)
    assert "population" in thinking_prompt.lower()
    assert "vectorized updates" not in thinking_prompt.lower()

    vectorization_prompt = build_task_prompt(1, 3, lb, ub, strategy=PromptStrategy.VECTORIZATION)
    assert "population" in vectorization_prompt.lower()
    assert "vectorized updates" in vectorization_prompt.lower()

    guided_prompt = build_task_prompt(1, 3, lb, ub, strategy=PromptStrategy.GUIDED)
    assert "population" in guided_prompt.lower()
    assert "vectorized updates" in guided_prompt.lower()
    assert "differential evolution" in guided_prompt.lower()


def test_build_task_prompt_noisy_strategies():
    lb = np.array([-5.0] * 3)
    ub = np.array([5.0] * 3)

    baseline_noisy = build_task_prompt(
        15, 3, lb, ub, mode=ProblemMode.NOISY, strategy=PromptStrategy.BASELINE
    )
    assert "stochastic" in baseline_noisy
    assert "Single-shot acceptance" in baseline_noisy

    thinking_noisy = build_task_prompt(
        15, 3, lb, ub, mode=ProblemMode.NOISY, strategy=PromptStrategy.THINKING
    )
    assert "statistical summary" in thinking_noisy

    vector_noisy = build_task_prompt(
        15, 3, lb, ub, mode=ProblemMode.NOISY, strategy=PromptStrategy.VECTORIZATION
    )
    assert "k_evals = np.array" in vector_noisy

    guided_noisy = build_task_prompt(
        15, 3, lb, ub, mode=ProblemMode.NOISY, strategy=PromptStrategy.GUIDED
    )
    assert "re-evaluation strategy" in guided_noisy
    assert "_robust_eval" in guided_noisy
