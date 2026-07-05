"""
Prompt constants for LLaMEA optimization algorithm design.
"""

TASK_PROMPT_CLEAN = """
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm that is highly specialized for a specific target landscape (BBOB Problem ID: {problem_id}).
The objective function you are optimizing is entirely deterministic (noise-free). You can rely on precise gradient approximations, exact local search, or aggressive exploitation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single landscape.

Write the Python code for a class that contains a `__call__(self, problem, budget)` method.
The `problem` is the objective function to be minimized. You can evaluate a point `x` by calling `y = problem(x)`, where `x` is a numpy array and `y` is a float.
The `budget` is the maximum number of times you can evaluate `problem`.
The domain bounds for the search space are [{lower_bound}, {upper_bound}] for all dimensions (accessible via `problem.lower_bound` and `problem.upper_bound` or `problem.lb` and `problem.ub`).
Your goal is to find and return the lowest possible value of `problem(x)` within the budget.
"""

TASK_PROMPT_NOISY = """
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm that is highly specialized for a specific target landscape (BBOB Problem ID: {problem_id}).
Critically, the objective function you are optimizing contains statistical noise. Your algorithm must be resilient to this noise and avoid being trapped by false gradients.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Write the Python code for a class that contains a `__call__(self, problem, budget)` method.
The `problem` is the noisy objective function to be minimized. You can evaluate a point `x` by calling `y = problem(x)`, where `x` is a numpy array and `y` is a noisy float.
The `budget` is the maximum number of times you can evaluate `problem`.
The domain bounds for the search space are [{lower_bound}, {upper_bound}] for all dimensions (accessible via `problem.lower_bound` and `problem.upper_bound` or `problem.lb` and `problem.ub`).
Your goal is to find and return the lowest possible value of `problem(x)` within the budget.
"""

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
            lb = getattr(problem, 'lower_bound', -5.0)
            ub = getattr(problem, 'upper_bound', 5.0)
            dim = getattr(problem, 'dim', 3)

            # Always start with a random initial point
            best_x = np.random.uniform(lb, ub, dim)
            best_y = problem(best_x)
            evaluations = 1

            # --- YOUR ALGORITHM LOGIC BELOW ---
            # Use `evaluations` to track calls. Stop when evaluations >= budget.
            # Always call `y = problem(x)` where x is a 1D numpy array of shape (dim,).
            # Compare only scalar floats: `if y < best_y:` (not arrays).
            # Update best_x and best_y when you find improvement.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return float(best_y)  # MUST return a float scalar
"""

FORMAT_PROMPT = """
Respond with EXACTLY the following format — no extra code blocks:

Feedback: <your reasoning and description of the algorithm>
Code:
```python
<import numpy as np first, then your complete class>
```

STRICT Rules — violating any rule will cause execution failure:
- There must be exactly ONE ```python ... ``` block in your response.
- The class MUST be named exactly one word (e.g., `class MyOptimizer:`).
- `__init__(self)` MUST take NO extra arguments beyond `self`.
- `__init__(self)` MUST have a non-empty body (use `pass` if nothing to initialize).
- The class MUST have a `__call__(self, problem, budget)` method.
- `__call__` MUST return `float(best_y)` — a scalar Python float, NOT a numpy array.
- Every variable you use MUST be defined before use. Never reference undefined names.
- Do NOT store `problem` or `budget` in `__init__` — they are provided to `__call__` directly.
- `x` is a 1D numpy array of shape `(dim,)`. Never use bare `if x < value:` — use `np.all()`, `np.any()`, or `np.clip(x, lb, ub)`.
- The `import numpy as np` statement MUST appear at the top of your code block.
- Do NOT include `if __name__ == '__main__':` blocks.
"""
