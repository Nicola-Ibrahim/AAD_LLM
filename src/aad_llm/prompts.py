"""
Prompt constants for LLaMEA optimization algorithm design.
"""

TASK_PROMPT_TEMPLATE = """
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm that is highly specialized for a specific target landscape (BBOB Problem ID: {problem_id}).
Critically, the objective function you are optimizing contains statistical noise. Your algorithm must be resilient to this noise and avoid being trapped by false gradients.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Write the Python code for a class that contains a `__call__(self, func, budget)` method.
The `func` is the noisy objective function to be minimized, taking a numpy array (the search point) and returning a float (the fitness).
The `budget` is the maximum number of times you can call `func`.
The domain bounds for the search space are [-5.0, 5.0] for all dimensions.
Your goal is to find and return the lowest possible value of `func` within the budget.
"""

EXAMPLE_PROMPT = """
An example code structure for a simple Random Search algorithm is as follows:
```python
import numpy as np

class AlgorithmName:
    "Template for a noisy BBOB optimization algorithm"

    def __init__(self):
        self.lower_bound = -5.0
        self.upper_bound = 5.0
        self.dim = 3 # Example dimension

    def __call__(self, func, budget):
        best_y = float('inf')
        
        for _ in range(budget):
            # Sample a random point in the domain
            x = np.random.uniform(self.lower_bound, self.upper_bound, self.dim)
            
            # Evaluate the noisy function
            y = func(x)
            
            # Keep track of the best minimum found
            if y < best_y:
                best_y = y
                
        return best_y
```
"""

FORMAT_PROMPT = """
Give an excellent and novel optimization algorithm to solve this specific noisy task.
Classify the core mathematical strategy or algorithm family your code belongs to (e.g., Gradient-Based, Evolutionary, Swarm Intelligence, Simulated Annealing, Surrogate-Assisted).
Provide a one-line description detailing your main noise-handling idea (e.g., "Using moving averages to smooth the noisy landscape").
Give the response in the exact format below:

# Algorithm Family: <Algorithm-Type>
# Description: <short-description>

# Code:

```python
<code>
```
"""
