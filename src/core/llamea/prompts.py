"""
Prompt constants and builder for LLaMEA optimization algorithm design.
"""

import numpy as np

BASE_TASK_PROMPT_CLEAN = """
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm that is highly specialized for a specific target landscape (BBOB Problem ID: {problem_id}).
The objective function you are optimizing is entirely deterministic (noise-free). You can rely on precise gradient approximations, exact local search, or aggressive exploitation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single landscape.

Write the Python code for a class that contains a `__call__(self, problem, budget)` method.
The `problem` is the objective function to be minimized. You can evaluate a point `x` by calling `y = problem(x)`, where `x` is a 1D vector or 1D array of coordinates (length = dimension) and `y` is a float scalar.
The `budget` is the maximum number of times you can evaluate `problem`.
The domain bounds for the search space are [{lower_bound}, {upper_bound}] for all dimensions (accessible via `problem.lower_bound` and `problem.upper_bound` or `problem.lb` and `problem.ub`).
{strategy_blocks}
Your goal is to find and return the lowest possible value of `problem(x)` within the budget.
"""

BASE_TASK_PROMPT_NOISY = """
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm that is highly specialized for a specific target landscape (BBOB Problem ID: {problem_id}).
Critically, the objective function you are optimizing contains statistical noise. Your algorithm must be resilient to this noise and avoid being trapped by false gradients.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Write the Python code for a class that contains a `__call__(self, problem, budget)` method.
The `problem` is the noisy objective function to be minimized. You can evaluate a point `x` by calling `y = problem(x)`, where `x` is a 1D vector or 1D array of coordinates (length = dimension) and `y` is a noisy float scalar.
The `budget` is the maximum number of times you can evaluate `problem`.
The domain bounds for the search space are [{lower_bound}, {upper_bound}] for all dimensions (accessible via `problem.lower_bound` and `problem.upper_bound` or `problem.lb` and `problem.ub`).
{strategy_blocks}
Your goal is to find and return the lowest possible value of `problem(x)` within the budget.
"""

PROMPT_BLOCK_MATH = "You may use standard mathematical and numerical computation libraries (`numpy` / `np`, `math`, `random`).\n"
PROMPT_BLOCK_VEC = "You are strongly encouraged to use population-level and matrix-level vectorization in NumPy (e.g., creating matrices of candidate vectors of shape `(pop_size, dim)` and applying vectorized mutations, linear algebra, or batch domain clipping `np.clip`) rather than scalar Python loops.\n"
PROMPT_BLOCK_NO_SOLVER = "Do NOT use pre-built, off-the-shelf optimizer solvers or wrapper functions — you MUST design and write your own custom optimization search logic.\n"

PROMPT_STRATEGIES: dict[str, list[str]] = {
    "baseline": [],
    "math_hints": [PROMPT_BLOCK_MATH],
    "vectorization": [PROMPT_BLOCK_MATH, PROMPT_BLOCK_VEC],
    "full_scaffold": [PROMPT_BLOCK_MATH, PROMPT_BLOCK_VEC, PROMPT_BLOCK_NO_SOLVER],
}

# Kept for backward compatibility with existing imports
TASK_PROMPT_CLEAN = BASE_TASK_PROMPT_CLEAN.format(
    problem_id="{problem_id}",
    lower_bound="{lower_bound}",
    upper_bound="{upper_bound}",
    strategy_blocks="\n" + "".join(PROMPT_STRATEGIES["full_scaffold"]) + "\n",
)

TASK_PROMPT_NOISY = BASE_TASK_PROMPT_NOISY.format(
    problem_id="{problem_id}",
    lower_bound="{lower_bound}",
    upper_bound="{upper_bound}",
    strategy_blocks="\n" + "".join(PROMPT_STRATEGIES["full_scaffold"]) + "\n",
)

EXAMPLE_PROMPT = """
Your algorithm will be instantiated and called as follows:
    optimizer = AlgorithmName()
    best_y = optimizer(problem, budget)

You MUST use the following class skeleton — fill in your algorithm logic in the marked section only.
Do NOT change the class structure, method signatures, or return statement:

    import numpy as np

    class AlgorithmName:
        def __init__(self):
            pass  # Add initialization state here if your algorithm needs it

        def __call__(self, problem, budget):
            lb = np.asarray(getattr(problem, 'lower_bound', -5.0), dtype=float)
            ub = np.asarray(getattr(problem, 'upper_bound', 5.0), dtype=float)
            dim = int(getattr(problem, 'dim', len(lb) if hasattr(lb, '__len__') else 3))

            # Always start with a random initial point using vectorization
            best_x = np.random.uniform(lb, ub, size=dim)
            best_y = float(problem(best_x))
            evaluations = 1

            # --- YOUR ALGORITHM LOGIC BELOW ---
            # Use `evaluations` to track calls. Stop when evaluations >= budget.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x))
            # Compare scalar floats: `if y < best_y:`
            # Update best_x and best_y when you find improvement.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return float(best_y)  # MUST return a float scalar
"""

FORMAT_PROMPT = """
Respond with EXACTLY the following format — no extra code blocks:

Feedback: <your reasoning and description of the algorithm>
Code:
```python
<your complete class and any required imports>
```

STRICT Rules — violating any rule will cause execution failure:
- There must be exactly ONE ```python ... ``` block in your response.
- The class MUST be named exactly one word (e.g., `class MyOptimizer:`).
- `__init__(self)` MUST take NO extra arguments beyond `self`.
- `__init__(self)` MUST have a non-empty body (use `pass` if nothing to initialize).
- The class MUST have a `__call__(self, problem, budget)` method.
- `__call__` MUST return `float(best_y)` — a scalar Python float.
- You may use standard math/vectorization libraries (`numpy`, `math`, `random`).
- Use matrix/population-level NumPy vectorization (e.g. shapes of `(pop_size, dim)`) for candidate generation and updates.
- Do NOT use pre-built optimizer packages or solver wrappers.
- Every variable you use MUST be defined before use. Never reference undefined names.
- Do NOT store `problem` or `budget` in `__init__` — they are provided to `__call__` directly.
- Do NOT include `if __name__ == '__main__':` blocks.
"""


def build_task_prompt(
    problem_id: int,
    dim: int,
    lower_bound: np.ndarray,
    upper_bound: np.ndarray,
    is_noisy: bool = False,
    strategy: str = "baseline",
) -> str:
    """Constructs the structured task prompt based on explicit problem parameters, noise flag, and prompt strategy."""
    blocks = PROMPT_STRATEGIES.get(strategy, PROMPT_STRATEGIES["baseline"])
    strategy_text = ("\n" + "".join(blocks) + "\n") if blocks else "\n"

    template = BASE_TASK_PROMPT_NOISY if is_noisy else BASE_TASK_PROMPT_CLEAN
    return template.format(
        problem_id=problem_id,
        dim=dim,
        lower_bound=lower_bound.tolist(),
        upper_bound=upper_bound.tolist(),
        strategy_blocks=strategy_text,
    )

