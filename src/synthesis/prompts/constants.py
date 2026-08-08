EXAMPLE_PROMPT = """
Your algorithm will be instantiated and called as follows:
    optimizer = AlgorithmName()
    best_x, best_y = optimizer(problem, budget)

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

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
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
- `__call__` MUST return `(best_x, float(best_y))` — a tuple of the best search coordinates array and best scalar float value.
- Do NOT import or call `scipy.optimize` (e.g. `scipy.optimize.minimize`, `differential_evolution`, etc.) — pre-built solver wrappers are strictly banned. Write your search algorithm logic from scratch using NumPy.
- Every variable you use MUST be defined before use. Never reference undefined names.
- Do NOT store `problem` or `budget` in `__init__` — they are provided to `__call__` directly.
- Do NOT include `if __name__ == '__main__':` blocks.
"""
