from enum import StrEnum
from pathlib import Path

import numpy as np
from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptMode(StrEnum):
    CLEAN = "clean"
    NOISY = "noisy"


class PromptStrategy(StrEnum):
    BASELINE = "baseline"
    THINKING = "thinking"
    VECTORIZATION = "vectorization"
    GUIDED = "guided"


_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape([]),
    trim_blocks=True,
    lstrip_blocks=True,
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
- Every variable you use MUST be defined before use. Never reference undefined names.
- Do NOT store `problem` or `budget` in `__init__` — they are provided to `__call__` directly.
- Do NOT include `if __name__ == '__main__':` blocks.
"""


def build_task_prompt(
    problem_id: int,
    dim: int,
    lower_bound: np.ndarray,
    upper_bound: np.ndarray,
    mode: PromptMode | str = PromptMode.CLEAN,
    strategy: PromptStrategy | str = PromptStrategy.BASELINE,
) -> str:
    """Constructs the structured task prompt based on explicit problem parameters, PromptMode enum, and prompt strategy."""
    mode_enum = PromptMode(mode) if isinstance(mode, str) else mode
    strategy_enum = PromptStrategy(strategy) if isinstance(strategy, str) else strategy
    template_name = "task_noisy.j2" if mode_enum == PromptMode.NOISY else "task_clean.j2"
    return _jinja_env.get_template(template_name).render(
        problem_id=problem_id,
        dim=dim,
        lower_bound=lower_bound.tolist(),
        upper_bound=upper_bound.tolist(),
        mode=mode_enum,
        strategy=strategy_enum,
    )
