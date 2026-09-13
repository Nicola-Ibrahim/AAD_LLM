# Complete LLaMEA Prompt Reference Manual

> Comprehensive collection of all prompt components, synthesis modes, strategy levels, and assembled prompts used in the AAD-LLM evolutionary synthesis pipeline.

## Table of Contents
- [1. Output Format Rules (`format.j2`)](#1-output-format-rules-formatj2)
- [2. Code Skeleton Example (`example.j2`)](#2-code-skeleton-example-examplej2)
- [3. The 3 Main Synthesis Modes (Landscape Nature)](#3-the-3-main-synthesis-modes-landscape-nature)
  - [3.1 Clean Mode](#31-clean-mode)
  - [3.2 Implicit Mode](#32-implicit-mode)
  - [3.3 Noisy Mode](#33-noisy-mode)
- [4. The 4 Strategy Levels (Noisy Landscape)](#4-the-4-strategy-levels-noisy-landscape)
  - [4.1 Baseline Strategy](#41-baseline-strategy)
  - [4.2 Vectorization Strategy](#42-vectorization-strategy)
  - [4.3 Guided Strategy (k=3)](#43-guided-strategy-k3)
  - [4.4 Thinking Strategy](#44-thinking-strategy)
- [5. Full Assembled Payloads (What LLaMEA Sends to the LLM)](#5-full-assembled-payloads-what-llamea-sends-to-the-llm)
  - [5.1 Clean Baseline](#51-clean-baseline)
  - [5.2 Implicit Baseline](#52-implicit-baseline)
  - [5.3 Noisy Baseline](#53-noisy-baseline)
  - [5.4 Noisy Vectorization](#54-noisy-vectorization)
  - [5.5 Noisy Guided](#55-noisy-guided)
  - [5.6 Noisy Thinking](#56-noisy-thinking)

---

## 1. Output Format Rules (`format.j2`)

Passed to LLaMEA as `output_format_prompt`:

```text
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
```

---

## 2. Code Skeleton Example (`example.j2`)

Passed to LLaMEA as `example_prompt`:

```python
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
            # BUDGET TRACKING: every call to problem(x) counts — including calls inside
            # min()/max(key=...) lambdas, list comprehensions, and helper functions.
            # Always increment `evaluations` immediately after every problem(x) call.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x)); evaluations += 1
            # Compare candidates and update best_x, best_y when improvement found.
            # NOTE: For noisy problems, a single raw comparison may be unreliable.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
```

---

## 3. The 3 Main Synthesis Modes (Landscape Nature)

### 3.1 Clean Mode

```text
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is entirely deterministic (noise-free). You can rely on precise evaluations, exact gradient approximations, and aggressive local search exploitation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noise-free landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
```

### 3.2 Implicit Mode

```text
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
This is an unknown real-world black-box objective function. You have no prior knowledge of its internal structure, smoothness, or evaluation consistency. Design a general-purpose, robust optimization algorithm that reliably finds the true optimum.

This is a bespoke algorithm tailored to optimize this specific unknown black-box landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
```

### 3.3 Noisy Mode

```text
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
```


---

## 4. The 4 Strategy Levels (Noisy Landscape)

### 4.1 Baseline Strategy

```text
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
```

### 4.2 Vectorization Strategy

```text
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
Strategy Guidance:
Design your algorithm to maintain a population of candidate solutions. At each step, balance exploration (probing new regions of the search space) and exploitation (refining the most promising solutions found so far).

Implement your algorithm using NumPy matrix operations on populations of shape `(pop_size, dim)` — batch candidate generation, batch evaluation, and vectorized updates — rather than scalar Python loops over individual solutions.

When deciding whether candidate x_new is better than x_best, do not rely on a single evaluation. Use a vectorized re-evaluation pattern:

    k_evals = np.array([problem(x) for _ in range(k)])  # k calls to get a sample
    score = float(k_evals.mean())                        # robust estimate

Each call to problem() inside this pattern counts against your budget. Choose k carefully so that re-evaluation stays within a reasonable fraction of your total budget (e.g., <= 20%).
```

### 4.3 Guided Strategy

```text
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
Strategy Guidance:
Design your algorithm to maintain a population of candidate solutions. At each step, balance exploration (probing new regions of the search space) and exploitation (refining the most promising solutions found so far).

Implement your algorithm using NumPy matrix operations on populations of shape `(pop_size, dim)` — batch candidate generation, batch evaluation, and vectorized updates — rather than scalar Python loops over individual solutions.

Use a re-evaluation strategy: call problem(x) k times per candidate and use the mean as your fitness estimate. Limit re-evaluation to at most 20% of your total budget. For example, if budget = 1,000,000 and pop_size = 50 and k = 3, you use 3 * pop_size = 150 calls per generation, far within budget.

Algorithm families that are naturally suited to noisy optimization:
- Population-based methods: noise averages over candidates across generations.
- Simulated annealing: accepts worse solutions probabilistically, robust to single-noise acceptance.
- CMA-ES / Covariance-adaptation variants: covariance adaptation smooths over noisy gradients.

A concrete starter for the selection step:
    def _robust_eval(x, k):
        return float(np.mean([problem(x) for _ in range(k)]))
    # Always compare _robust_eval(new_x, k) vs _robust_eval(best_x, k), not raw problem(x)

Do NOT return a smoothed/averaged value as best_y. Return float(problem(best_x)) — a single fresh evaluation — as the second element of the returned tuple.
```

### 4.4 Thinking Strategy

```text
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
Strategy Guidance:
Design your algorithm to maintain a population of candidate solutions. At each step, balance exploration (probing new regions of the search space) and exploitation (refining the most promising solutions found so far).

Before writing any code, reason through the following questions:
1. If a single evaluation at point x is unreliable, what property of a set of evaluations at x would be reliable?
2. If you cannot trust a single comparison, what statistical summary would let you make a robust ordering decision between two candidates?
3. How would you design your selection step to use that summary without exhausting your budget?

Your code must reflect the answers to these questions.
```


---

## 5. Full Assembled Payloads (What LLaMEA Sends to the LLM)

### 5.1 Clean Baseline

```text
=== 1. TASK PROMPT ===
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is entirely deterministic (noise-free). You can rely on precise evaluations, exact gradient approximations, and aggressive local search exploitation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noise-free landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)

=== 2. OUTPUT FORMAT RULES ===
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

=== 3. EXAMPLE CODE SKELETON ===
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
            # BUDGET TRACKING: every call to problem(x) counts — including calls inside
            # min()/max(key=...) lambdas, list comprehensions, and helper functions.
            # Always increment `evaluations` immediately after every problem(x) call.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x)); evaluations += 1
            # Compare candidates and update best_x, best_y when improvement found.
            # NOTE: For noisy problems, a single raw comparison may be unreliable.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
```

### 5.2 Implicit Baseline

```text
=== 1. TASK PROMPT ===
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
This is an unknown real-world black-box objective function. You have no prior knowledge of its internal structure, smoothness, or evaluation consistency. Design a general-purpose, robust optimization algorithm that reliably finds the true optimum.

This is a bespoke algorithm tailored to optimize this specific unknown black-box landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)

=== 2. OUTPUT FORMAT RULES ===
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

=== 3. EXAMPLE CODE SKELETON ===
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
            # BUDGET TRACKING: every call to problem(x) counts — including calls inside
            # min()/max(key=...) lambdas, list comprehensions, and helper functions.
            # Always increment `evaluations` immediately after every problem(x) call.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x)); evaluations += 1
            # Compare candidates and update best_x, best_y when improvement found.
            # NOTE: For noisy problems, a single raw comparison may be unreliable.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
```

### 5.3 Noisy Baseline

```text
=== 1. TASK PROMPT ===
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)

=== 2. OUTPUT FORMAT RULES ===
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

=== 3. EXAMPLE CODE SKELETON ===
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
            # BUDGET TRACKING: every call to problem(x) counts — including calls inside
            # min()/max(key=...) lambdas, list comprehensions, and helper functions.
            # Always increment `evaluations` immediately after every problem(x) call.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x)); evaluations += 1
            # Compare candidates and update best_x, best_y when improvement found.
            # NOTE: For noisy problems, a single raw comparison may be unreliable.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
```

### 5.4 Noisy Vectorization

```text
=== 1. TASK PROMPT ===
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
Strategy Guidance:
Design your algorithm to maintain a population of candidate solutions. At each step, balance exploration (probing new regions of the search space) and exploitation (refining the most promising solutions found so far).

Implement your algorithm using NumPy matrix operations on populations of shape `(pop_size, dim)` — batch candidate generation, batch evaluation, and vectorized updates — rather than scalar Python loops over individual solutions.

When deciding whether candidate x_new is better than x_best, do not rely on a single evaluation. Use a vectorized re-evaluation pattern:

    k_evals = np.array([problem(x) for _ in range(k)])  # k calls to get a sample
    score = float(k_evals.mean())                        # robust estimate

Each call to problem() inside this pattern counts against your budget. Choose k carefully so that re-evaluation stays within a reasonable fraction of your total budget (e.g., <= 20%).

=== 2. OUTPUT FORMAT RULES ===
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

=== 3. EXAMPLE CODE SKELETON ===
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
            # BUDGET TRACKING: every call to problem(x) counts — including calls inside
            # min()/max(key=...) lambdas, list comprehensions, and helper functions.
            # Always increment `evaluations` immediately after every problem(x) call.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x)); evaluations += 1
            # Compare candidates and update best_x, best_y when improvement found.
            # NOTE: For noisy problems, a single raw comparison may be unreliable.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
```

### 5.5 Noisy Guided

```text
=== 1. TASK PROMPT ===
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
Strategy Guidance:
Design your algorithm to maintain a population of candidate solutions. At each step, balance exploration (probing new regions of the search space) and exploitation (refining the most promising solutions found so far).

Implement your algorithm using NumPy matrix operations on populations of shape `(pop_size, dim)` — batch candidate generation, batch evaluation, and vectorized updates — rather than scalar Python loops over individual solutions.

Use a re-evaluation strategy: call problem(x) k times per candidate and use the mean as your fitness estimate. Limit re-evaluation to at most 20% of your total budget. For example, if budget = 1,000,000 and pop_size = 50 and k = 3, you use 3 * pop_size = 150 calls per generation, far within budget.

Algorithm families that are naturally suited to noisy optimization:
- Population-based methods: noise averages over candidates across generations.
- Simulated annealing: accepts worse solutions probabilistically, robust to single-noise acceptance.
- CMA-ES / Covariance-adaptation variants: covariance adaptation smooths over noisy gradients.

A concrete starter for the selection step:
    def _robust_eval(x, k):
        return float(np.mean([problem(x) for _ in range(k)]))
    # Always compare _robust_eval(new_x, k) vs _robust_eval(best_x, k), not raw problem(x)

Do NOT return a smoothed/averaged value as best_y. Return float(problem(best_x)) — a single fresh evaluation — as the second element of the returned tuple.

=== 2. OUTPUT FORMAT RULES ===
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

=== 3. EXAMPLE CODE SKELETON ===
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
            # BUDGET TRACKING: every call to problem(x) counts — including calls inside
            # min()/max(key=...) lambdas, list comprehensions, and helper functions.
            # Always increment `evaluations` immediately after every problem(x) call.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x)); evaluations += 1
            # Compare candidates and update best_x, best_y when improvement found.
            # NOTE: For noisy problems, a single raw comparison may be unreliable.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
```

### 5.6 Noisy Thinking

```text
=== 1. TASK PROMPT ===
You are a highly skilled computer scientist and an expert in meta-heuristic optimization.
Your task is to design a novel, continuous black-box optimization algorithm specialized for a specific target landscape (BBOB Problem ID: 1).

Landscape Characteristics:
The objective function is stochastic — every call to problem(x) returns a different value even at the same point x, due to random noise injected into the true objective value.

A single comparison `if y_new < y_best` may accept or reject candidates based on noise rather than true quality.

Common patterns that silently break under noise:
- Single-shot acceptance: `if trial_y < best_y` -> unreliable; may accept noise artifacts.
- Smoothed tracking: `best_y = 0.9*best_y + 0.1*trial_y` -> corrupts best_y; return becomes invalid.
- Hidden calls: `min(a, b, c, key=lambda x: problem(x))` -> uncounted budget calls per use.
- Misplaced counter: `evaluations += 1` outside the innermost problem() call -> budget count mismatch.

You MUST design a noise-resilient strategy where candidate selection decisions are based on more than a single noisy observation.

This is NOT a general-purpose solver. You are designing a bespoke algorithm tailored to exploit the specific features of this single noisy landscape.

Problem Parameters:
- The search space is 2-dimensional.
- Search Bounds: [[-5.0, -5.0], [5.0, 5.0]] (accessible via `problem.lower_bound` / `problem.upper_bound`)
- Total Evaluation Budget: 2000 calls to problem(x)
Strategy Guidance:
Design your algorithm to maintain a population of candidate solutions. At each step, balance exploration (probing new regions of the search space) and exploitation (refining the most promising solutions found so far).

Before writing any code, reason through the following questions:
1. If a single evaluation at point x is unreliable, what property of a set of evaluations at x would be reliable?
2. If you cannot trust a single comparison, what statistical summary would let you make a robust ordering decision between two candidates?
3. How would you design your selection step to use that summary without exhausting your budget?

Your code must reflect the answers to these questions.

=== 2. OUTPUT FORMAT RULES ===
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

=== 3. EXAMPLE CODE SKELETON ===
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
            # BUDGET TRACKING: every call to problem(x) counts — including calls inside
            # min()/max(key=...) lambdas, list comprehensions, and helper functions.
            # Always increment `evaluations` immediately after every problem(x) call.
            # Leverage NumPy matrix vectorization across populations of shape (pop_size, dim).
            # Example batch mutation: candidates = np.clip(pop + np.random.normal(0, 0.1, size=(pop_size, dim)), lb, ub)
            # Evaluate each candidate: for x in candidates: y = float(problem(x)); evaluations += 1
            # Compare candidates and update best_x, best_y when improvement found.
            # NOTE: For noisy problems, a single raw comparison may be unreliable.
            # --- YOUR ALGORITHM LOGIC ABOVE ---

            return best_x, float(best_y)  # MUST return tuple: (best_x_ndarray, best_y_float)
```
