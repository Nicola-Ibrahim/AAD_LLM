import numpy as np
import pytest

from evolution.domain.enums import NoiseEnvironment, PromptStrategy, SynthesisMode
from evolution.domain.services.noise_strategy import (
    HeteroscedasticNoiseStrategy,
    NoNoiseStrategy,
)
from evolution.infra.problems.bbob import BBOBProblem
from evolution.infra.engines.llamea.prompts import (
    SynthesisPrompts,
    assemble_full_prompt,
    build_synthesis_prompts,
    build_task_prompt,
)

BANNED_KEYWORDS = [
    "cma-es",
    "cma",
    "differential evolution",
    "particle swarm",
    "pso",
    "genetic algorithm",
    "simulated annealing",
    "hill climbing",
    "hill-climber",
    "_robust_eval",
    "k = 3",
    "k=3",
    "20% of the budget",
    "mean of k",
    "median of k",
    "return best_x and best_y",
]


def test_build_task_prompt_with_array_bounds():
    problem = BBOBProblem(problem_id=1, dim=3, noise_strategy=NoNoiseStrategy(), instance_id=1)
    assert isinstance(problem.lower_bound, np.ndarray)
    assert isinstance(problem.upper_bound, np.ndarray)
    assert problem.lower_bound.shape == (3,)
    assert problem.upper_bound.shape == (3,)

    prompt = build_task_prompt(
        problem=problem,
        mode=SynthesisMode.EXPLICIT,
        noise_environment=NoiseEnvironment.CLEAN,
    )

    assert "- BBOB function ID: 1" in prompt
    assert "[-5.0, -5.0, -5.0]" in prompt
    assert "The objective function is deterministic" in prompt


def test_build_task_prompt_noisy():
    problem = BBOBProblem(
        problem_id=2,
        dim=5,
        noise_strategy=HeteroscedasticNoiseStrategy(0.1),
        instance_id=1,
    )
    prompt = build_task_prompt(
        problem=problem,
        mode=SynthesisMode.EXPLICIT,
    )

    assert "The objective function is stochastic" in prompt
    assert "- BBOB function ID: 2" in prompt
    assert "- Dimension: 5" in prompt


def test_build_task_prompt_implicit():
    problem = BBOBProblem(problem_id=1, dim=3, noise_strategy=NoNoiseStrategy(), instance_id=1)

    for strat in [
        PromptStrategy.BASELINE,
        PromptStrategy.GUIDED,
        PromptStrategy.THINKING,
        PromptStrategy.VECTORIZATION,
    ]:
        prompt = build_task_prompt(problem=problem, mode=SynthesisMode.IMPLICIT, strategy=strat)
        assert "The objective function may return different values when evaluated at the same point" in prompt
        assert "No further information about the source or magnitude of this variation is available" in prompt
        assert "noisy" not in prompt.lower()
        assert "noise-free" not in prompt.lower()
        assert "deterministic" not in prompt.lower()
        assert "stochastic" not in prompt.lower()


def test_build_task_prompt_scaffolds():
    problem = BBOBProblem(problem_id=1, dim=3, noise_strategy=NoNoiseStrategy(), instance_id=1)

    # Baseline: no strategy scaffold text added
    baseline_prompt = build_task_prompt(
        problem=problem, mode=SynthesisMode.EXPLICIT, noise_environment=NoiseEnvironment.CLEAN, strategy=PromptStrategy.BASELINE
    )
    assert "numpy array operations" not in baseline_prompt.lower()
    assert "exploration and exploitation" not in baseline_prompt.lower()
    assert "briefly reason" not in baseline_prompt.lower()

    # Vectorization
    vec_prompt = build_task_prompt(
        problem=problem, mode=SynthesisMode.EXPLICIT, noise_environment=NoiseEnvironment.CLEAN, strategy=PromptStrategy.VECTORIZATION
    )
    assert "population-based representations" in vec_prompt.lower()
    assert "numpy array operations" in vec_prompt.lower()

    # Guided
    guided_prompt = build_task_prompt(
        problem=problem, mode=SynthesisMode.EXPLICIT, noise_environment=NoiseEnvironment.CLEAN, strategy=PromptStrategy.GUIDED
    )
    assert "balance between exploration and exploitation" in guided_prompt.lower()
    assert "allocating evaluations between discovering promising regions" in guided_prompt.lower()

    # Thinking
    thinking_prompt = build_task_prompt(
        problem=problem, mode=SynthesisMode.EXPLICIT, noise_environment=NoiseEnvironment.CLEAN, strategy=PromptStrategy.THINKING
    )
    assert "briefly reason about the main search mechanism" in thinking_prompt.lower()
    assert "directly reflect this reasoning" in thinking_prompt.lower()


@pytest.mark.parametrize(
    "mode,noise_env",
    [
        (SynthesisMode.EXPLICIT, NoiseEnvironment.CLEAN),
        (SynthesisMode.EXPLICIT, NoiseEnvironment.NOISY),
        (SynthesisMode.IMPLICIT, NoiseEnvironment.CLEAN),
    ],
)
@pytest.mark.parametrize(
    "strategy",
    [
        PromptStrategy.BASELINE,
        PromptStrategy.VECTORIZATION,
        PromptStrategy.GUIDED,
        PromptStrategy.THINKING,
    ],
)
def test_all_12_factorial_conditions_clean_of_banned_keywords(mode, noise_env, strategy):
    problem = BBOBProblem(problem_id=1, dim=3, noise_strategy=NoNoiseStrategy(), instance_id=1)

    prompt = build_task_prompt(problem=problem, mode=mode, noise_environment=noise_env, strategy=strategy)
    prompt_lower = prompt.lower()

    for banned in BANNED_KEYWORDS:
        assert banned not in prompt_lower, f"Banned keyword '{banned}' found in {mode} x {noise_env} x {strategy}"


def test_build_task_prompt_from_base_problem():
    problem = BBOBProblem(problem_id=1, dim=3, noise_strategy=NoNoiseStrategy(), instance_id=1)
    prompt = build_task_prompt(
        problem=problem,
        mode=SynthesisMode.EXPLICIT,
        strategy=PromptStrategy.BASELINE,
        budget_hint=2000,
    )
    assert "- Dimension: 3" in prompt
    assert "- BBOB function ID: 1" in prompt
    assert "- Evaluation budget: 2000" in prompt


def test_build_synthesis_prompts_bundle():
    problem = BBOBProblem(problem_id=8, dim=5, noise_strategy=NoNoiseStrategy(), instance_id=1)
    prompts = build_synthesis_prompts(
        problem=problem,
        mode=SynthesisMode.EXPLICIT,
        strategy=PromptStrategy.GUIDED,
        budget_hint=5000,
    )
    assert isinstance(prompts, SynthesisPrompts)
    assert "- Dimension: 5" in prompts.task
    assert "- BBOB function ID: 8" in prompts.task
    assert "class AlgorithmName:" in prompts.example
    assert "def __call__(self, problem, budget):" in prompts.example
    assert "RULES" in prompts.format or "rules" in prompts.format.lower()


def test_assemble_full_prompt():
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)
    prompts = build_synthesis_prompts(problem=problem)
    full = assemble_full_prompt(prompts)

    assert "TASK PROMPT" in full
    assert "OUTPUT FORMAT RULES" in full
    assert "CODE SKELETON EXAMPLE" in full
    assert "- Dimension: 2" in full
    assert "class AlgorithmName:" in full





