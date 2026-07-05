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
An example code structure for a simple Random Search algorithm is as follows:
```python
import numpy as np

class AlgorithmName:
    "Template for a BBOB optimization algorithm"

    def __init__(self):
        pass

    def __call__(self, problem, budget):
        # Fetch search space bounds directly from the problem object
        lb = getattr(problem, 'lower_bound', -5.0)
        ub = getattr(problem, 'upper_bound', 5.0)
        dim = getattr(problem, 'dim', 3)
        best_y = float('inf')
        
        for _ in range(budget):
            # Sample a random point within the problem domain bounds
            x = np.random.uniform(lb, ub, dim)
            
            # Evaluate the function
            y = problem(x)
            
            # Keep track of the best minimum found
            if y < best_y:
                best_y = y
                
        return best_y
```
"""

FORMAT_PROMPT = """
Write your output as:
Feedback: <thought process / explanation of changes>
Code:
```python
<code block containing the complete Python class>
```
"""
