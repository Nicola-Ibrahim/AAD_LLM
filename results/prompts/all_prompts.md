# LLaMEA Prompts & Evolutionary Feedback Reference Manual

> **Project:** Automated Algorithm Design under Stochastic Fitness (AAD-LLM)  
> **Framework:** Large Language Model Evolutionary Algorithm (LLaMEA)  
> **Storage File:** `results/prompts/all_prompts.md`  
> **Source Directory:** `src/evolution/infra/prompts/templates/`  
> **Engine Evaluator:** `src/evolution/infra/engines/llamea/evaluator.py`  

---

## 📑 Table of Contents

- [1. Synthesis Architecture & Factorial Design](#1-synthesis-architecture--factorial-design)
- [2. Core Invariant Templates (Shared Across All Conditions)](#2-core-invariant-templates-shared-across-all-conditions)
  - [2.1 Output Format Enforcement (`shared/format.j2`)](#21-output-format-enforcement-sharedformatj2)
  - [2.2 Algorithm Code Skeleton & API Contract (`shared/example.j2`)](#22-algorithm-code-skeleton--api-contract-sharedexamplej2)
- [3. Universal Task Layout Template (`layout.j2`)](#3-universal-task-layout-template-layoutj2)
- [4. Environment Modes (Environmental Priors)](#4-environment-modes-environmental-priors)
  - [4.1 Clean Landscape Mode (`modes/clean.j2`)](#41-clean-landscape-mode-modescleanj2)
  - [4.2 Implicit Landscape Mode (`modes/implicit.j2`)](#42-implicit-landscape-mode-modesimplicitj2)
  - [4.3 Noisy Landscape Mode (`modes/noisy.j2`)](#43-noisy-landscape-mode-modesnoisyj2)
- [5. Strategy Scaffolds (Algorithmic Inductive Biases)](#5-strategy-scaffolds-algorithmic-inductive-biases)
  - [5.1 Baseline Strategy (`strategies/baseline.j2`)](#51-baseline-strategy-strategiesbaselinej2)
  - [5.2 Vectorization Strategy (`strategies/vectorization.j2`)](#52-vectorization-strategy-strategiesvectorizationj2)
  - [5.3 Guided Strategy (`strategies/guided.j2`)](#53-guided-strategy-strategiesguidedj2)
  - [5.4 Thinking Strategy (`strategies/thinking.j2`)](#54-thinking-strategy-strategiesthinkingj2)
- [6. Evolutionary Feedback Taxonomy (Sections 10–14)](#6-evolutionary-feedback-taxonomy-sections-1014)
  - [6.1 Successful Candidate Feedback (`[RESULT]`)](#61-successful-candidate-feedback-result)
  - [6.2 Runtime Error Diagnostic Feedback (`[RUNTIME ERROR]`)](#62-runtime-error-diagnostic-feedback-runtime-error)
  - [6.3 Execution Timeout Feedback (`[TIMEOUT]`)](#63-execution-timeout-feedback-timeout)
  - [6.4 Stochastic Failure Context (`[NOISY PROBLEM CONTEXT]`)](#64-stochastic-failure-context-noisy-problem-context)
  - [6.5 Stagnation Meta-Feedback (`[META-FEEDBACK]`)](#65-stagnation-meta-feedback-meta-feedback)
- [7. Complete 12 Factorial Rendered Prompt Payloads](#7-complete-12-factorial-rendered-prompt-payloads)
  - [Payload: Clean × Baseline](#payload-clean-baseline)
  - [Payload: Clean × Vectorization](#payload-clean-vectorization)
  - [Payload: Clean × Guided](#payload-clean-guided)
  - [Payload: Clean × Thinking](#payload-clean-thinking)
  - [Payload: Implicit × Baseline](#payload-implicit-baseline)
  - [Payload: Implicit × Vectorization](#payload-implicit-vectorization)
  - [Payload: Implicit × Guided](#payload-implicit-guided)
  - [Payload: Implicit × Thinking](#payload-implicit-thinking)
  - [Payload: Noisy × Baseline](#payload-noisy-baseline)
  - [Payload: Noisy × Vectorization](#payload-noisy-vectorization)
  - [Payload: Noisy × Guided](#payload-noisy-guided)
  - [Payload: Noisy × Thinking](#payload-noisy-thinking)
- [8. Verification & Keyword Absence Audit](#8-verification--keyword-absence-audit)

---

## 1. Synthesis Architecture & Factorial Design

The prompt system follows a strict three-tier separation of concerns:

```text
                 LLaMEA
                   │
        ┌──────────┼──────────┐
        │          │          │
       TASK      EXAMPLE     FORMAT
        │          │          │
   ┌────┴────┐     │          │
   │         │     │          │
 MODE     SCAFFOLD │          │
   │         │     │          │
 clean    baseline │          │
 implicit vectorization       │
 noisy    guided   │          │
          thinking │          │
                              │
                    universal interface
                    best_x / best_y
                    budget / bounds
                    class / call signature
```

### Key Principles:
1. **Strict Decoupling**: `TASK = layout + environment mode + scaffold` changes across experimental conditions. `EXAMPLE` and `FORMAT` are invariant across all 12 conditions.
2. **Canonical Naming**: Strategy name is strictly unified as `vectorization` matching database schemas, enums, and logs. No aliases or legacy shims.
3. **External Baselines Preserved**: Prompts and feedback never suggest specific optimizer names (`CMA-ES`, `Differential Evolution`, `PSO`, `GA`, `Simulated Annealing`, `Hill Climbing`). Those algorithms serve as objective benchmark baselines for scientific evaluation, not suggestions given to the LLM.
4. **No Rigid Recipes**: All fixed formulas (e.g. $k=3$, 20% budget, `_robust_eval`) have been removed from prompts and evolutionary feedback.
5. **Experimental Matrix**: Exactly $3 \text{ Environment Modes} \times 4 \text{ Strategy Scaffolds} = 12$ factorial conditions.

---

## 2. Core Invariant Templates (Shared Across All Conditions)

### 2.1 Output Format Enforcement (`shared/format.j2`)

Enforces strict markdown structure, class naming, argument handling, and bans external solver wrappers.

```jinja2
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

### 2.2 Algorithm Code Skeleton & API Contract (`shared/example.j2`)

Provides the common API contract, bounds extraction, initial evaluation, and evaluation counting skeleton.

```jinja2
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

## 3. Universal Task Layout Template (`layout.j2`)

Assembles problem metadata, environmental prior, strategy guidance, and universal goal:

```jinja2
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: {{ problem_id }}
- Dimension: {{ dimension }}
- Lower bound: {{ lower_bound }}
- Upper bound: {{ upper_bound }}
- Evaluation budget: {{ budget }}

{{ mode_prompt }}

{{ strategy_prompt }}

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

---

## 4. Environment Modes (Environmental Priors)

### 4.1 Clean Landscape Mode (`modes/clean.j2`)

```jinja2
Environment:

The objective function is deterministic. Repeated evaluations at the same point return consistent objective values.

You do not need to account for stochastic evaluation noise when making optimization decisions.
```

### 4.2 Implicit Landscape Mode (`modes/implicit.j2`)

```jinja2
Environment:

The objective function may return different values when evaluated at the same point.

No further information about the source or magnitude of this variation is available.

Design the algorithm using only the information available through objective evaluations.
```

### 4.3 Noisy Landscape Mode (`modes/noisy.j2`)

```jinja2
Environment:

The objective function is stochastic. Evaluating the same point multiple times may produce different objective values because of random variation.

Therefore, a single objective evaluation may be an unreliable basis for deciding which candidate is better.

Design the algorithm so that its optimization decisions account for this stochasticity.
```

---

## 5. Strategy Scaffolds (Algorithmic Inductive Biases)

### 5.1 Baseline Strategy (`strategies/baseline.j2`)

*Empty template* — provides zero additional algorithmic bias, testing the model's unprompted prior under the environmental condition.

### 5.2 Vectorization Strategy (`strategies/vectorization.j2`)

```jinja2
Strategy guidance:

Use population-based representations where they are appropriate for the optimization problem.

Represent multiple candidate solutions together and use NumPy array operations for candidate generation, transformation, and population updates where practical.

The implementation should remain within the available evaluation budget.
```

### 5.3 Guided Strategy (`strategies/guided.j2`)

```jinja2
Strategy guidance:

Design the search around a clear balance between exploration and exploitation.

Use information from previously evaluated candidate solutions to guide subsequent search steps.

Consider maintaining and updating multiple candidate solutions when this supports the search strategy.

Adapt the search behavior as the optimization progresses rather than using a fixed search step throughout the entire budget.

Use the available evaluation budget deliberately, allocating evaluations between discovering promising regions and refining promising solutions.

The algorithm should use objective evaluations as the primary source of information and should not assume access to gradients or internal properties of the objective function.
```

### 5.4 Thinking Strategy (`strategies/thinking.j2`)

```jinja2
Strategy guidance:

Before writing the code, briefly reason about the main search mechanism, how candidate solutions will be generated and selected, and how the evaluation budget will be allocated.

The implementation should directly reflect this reasoning.

Keep the reasoning focused on decisions that affect the algorithm rather than explaining general optimization concepts.
```

---

## 6. Evolutionary Feedback Taxonomy (Sections 10–14)

All feedback messages in `src/evolution/infra/engines/llamea/evaluator.py` adhere strictly to the neutral feedback specification.

### 6.1 Successful Candidate Feedback (`[RESULT]`)

#### Clean Landscape (Section 10.1):

```text
[RESULT]

The generated algorithm executed successfully.

Final objective error:
0.0012

Use this result together with the previous algorithm history when designing the next candidate.
```

#### Stochastic Objective (Section 10.2):

```text
[RESULT]

The generated algorithm executed successfully on a stochastic objective.

Final objective error:
0.8420

The result indicates that the current search strategy may not have handled the stochastic evaluations effectively.

Use the observed result and previous algorithm history to improve the next candidate.
```

### 6.2 Runtime Error Diagnostic Feedback (`[RUNTIME ERROR]`)

#### Section 11 Specification:

```text
[RUNTIME ERROR]

The generated algorithm failed during execution.

Error:
ValueError: shapes (10, 2) and (3, 10) not aligned: 2 != 3

Relevant code:
  -> line   8:     arr = pop @ weights

Fix the cause of the failure in the next candidate.

Ensure that:
- array shapes and dimensions are valid;
- numerical operations are well-defined;
- all variables are initialized before use;
- the search stays within the provided bounds;
- every objective evaluation is counted;
- the total number of objective evaluations does not exceed the budget.
```

### 6.3 Execution Timeout Feedback (`[TIMEOUT]`)

#### Section 12 Specification:

```text
[TIMEOUT]

The generated algorithm exceeded the execution time limit.

Reduce unnecessary computation and ensure that the implementation can complete within the available execution time and evaluation budget.
```

### 6.4 Stochastic Failure Context (`[NOISY PROBLEM CONTEXT]`)

#### Section 13 Specification:

```text
[NOISY PROBLEM CONTEXT]

The objective function is stochastic.

Ensure that optimization decisions are not based on invalid or inconsistently stored objective values.

Keep any internal statistical estimates separate from the objective value required by the optimizer interface.

Ensure that every call to problem(x) is counted against the evaluation budget.
```

### 6.5 Stagnation Meta-Feedback (`[META-FEEDBACK]`)

#### Section 14 Specification:

```text
[META-FEEDBACK]

The last several generated algorithms failed to execute correctly.

Try a substantially different search mechanism rather than making only minor modifications to the previous approach.

Check the previous implementation for the source of the failure and ensure that the new algorithm respects the objective interface, search bounds, evaluation budget, and numerical constraints.
```

---

## 7. Complete 12 Factorial Rendered Prompt Payloads

Below are the exact rendered prompts across all 12 factorial conditions for **BBOB Function 1, Dimension 3, Budget 500, Bounds [-5.0, 5.0]**.

### Payload: Clean × Baseline

- **Environment Mode:** `clean`
- **Strategy Scaffold:** `baseline`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is deterministic. Repeated evaluations at the same point return consistent objective values.

You do not need to account for stochastic evaluation noise when making optimization decisions.



Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Clean × Vectorization

- **Environment Mode:** `clean`
- **Strategy Scaffold:** `vectorization`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is deterministic. Repeated evaluations at the same point return consistent objective values.

You do not need to account for stochastic evaluation noise when making optimization decisions.

Strategy guidance:

Use population-based representations where they are appropriate for the optimization problem.

Represent multiple candidate solutions together and use NumPy array operations for candidate generation, transformation, and population updates where practical.

The implementation should remain within the available evaluation budget.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Clean × Guided

- **Environment Mode:** `clean`
- **Strategy Scaffold:** `guided`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is deterministic. Repeated evaluations at the same point return consistent objective values.

You do not need to account for stochastic evaluation noise when making optimization decisions.

Strategy guidance:

Design the search around a clear balance between exploration and exploitation.

Use information from previously evaluated candidate solutions to guide subsequent search steps.

Consider maintaining and updating multiple candidate solutions when this supports the search strategy.

Adapt the search behavior as the optimization progresses rather than using a fixed search step throughout the entire budget.

Use the available evaluation budget deliberately, allocating evaluations between discovering promising regions and refining promising solutions.

The algorithm should use objective evaluations as the primary source of information and should not assume access to gradients or internal properties of the objective function.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Clean × Thinking

- **Environment Mode:** `clean`
- **Strategy Scaffold:** `thinking`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is deterministic. Repeated evaluations at the same point return consistent objective values.

You do not need to account for stochastic evaluation noise when making optimization decisions.

Strategy guidance:

Before writing the code, briefly reason about the main search mechanism, how candidate solutions will be generated and selected, and how the evaluation budget will be allocated.

The implementation should directly reflect this reasoning.

Keep the reasoning focused on decisions that affect the algorithm rather than explaining general optimization concepts.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Implicit × Baseline

- **Environment Mode:** `implicit`
- **Strategy Scaffold:** `baseline`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function may return different values when evaluated at the same point.

No further information about the source or magnitude of this variation is available.

Design the algorithm using only the information available through objective evaluations.



Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Implicit × Vectorization

- **Environment Mode:** `implicit`
- **Strategy Scaffold:** `vectorization`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function may return different values when evaluated at the same point.

No further information about the source or magnitude of this variation is available.

Design the algorithm using only the information available through objective evaluations.

Strategy guidance:

Use population-based representations where they are appropriate for the optimization problem.

Represent multiple candidate solutions together and use NumPy array operations for candidate generation, transformation, and population updates where practical.

The implementation should remain within the available evaluation budget.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Implicit × Guided

- **Environment Mode:** `implicit`
- **Strategy Scaffold:** `guided`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function may return different values when evaluated at the same point.

No further information about the source or magnitude of this variation is available.

Design the algorithm using only the information available through objective evaluations.

Strategy guidance:

Design the search around a clear balance between exploration and exploitation.

Use information from previously evaluated candidate solutions to guide subsequent search steps.

Consider maintaining and updating multiple candidate solutions when this supports the search strategy.

Adapt the search behavior as the optimization progresses rather than using a fixed search step throughout the entire budget.

Use the available evaluation budget deliberately, allocating evaluations between discovering promising regions and refining promising solutions.

The algorithm should use objective evaluations as the primary source of information and should not assume access to gradients or internal properties of the objective function.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Implicit × Thinking

- **Environment Mode:** `implicit`
- **Strategy Scaffold:** `thinking`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function may return different values when evaluated at the same point.

No further information about the source or magnitude of this variation is available.

Design the algorithm using only the information available through objective evaluations.

Strategy guidance:

Before writing the code, briefly reason about the main search mechanism, how candidate solutions will be generated and selected, and how the evaluation budget will be allocated.

The implementation should directly reflect this reasoning.

Keep the reasoning focused on decisions that affect the algorithm rather than explaining general optimization concepts.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Noisy × Baseline

- **Environment Mode:** `noisy`
- **Strategy Scaffold:** `baseline`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is stochastic. Evaluating the same point multiple times may produce different objective values because of random variation.

Therefore, a single objective evaluation may be an unreliable basis for deciding which candidate is better.

Design the algorithm so that its optimization decisions account for this stochasticity.



Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Noisy × Vectorization

- **Environment Mode:** `noisy`
- **Strategy Scaffold:** `vectorization`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is stochastic. Evaluating the same point multiple times may produce different objective values because of random variation.

Therefore, a single objective evaluation may be an unreliable basis for deciding which candidate is better.

Design the algorithm so that its optimization decisions account for this stochasticity.

Strategy guidance:

Use population-based representations where they are appropriate for the optimization problem.

Represent multiple candidate solutions together and use NumPy array operations for candidate generation, transformation, and population updates where practical.

The implementation should remain within the available evaluation budget.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Noisy × Guided

- **Environment Mode:** `noisy`
- **Strategy Scaffold:** `guided`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is stochastic. Evaluating the same point multiple times may produce different objective values because of random variation.

Therefore, a single objective evaluation may be an unreliable basis for deciding which candidate is better.

Design the algorithm so that its optimization decisions account for this stochasticity.

Strategy guidance:

Design the search around a clear balance between exploration and exploitation.

Use information from previously evaluated candidate solutions to guide subsequent search steps.

Consider maintaining and updating multiple candidate solutions when this supports the search strategy.

Adapt the search behavior as the optimization progresses rather than using a fixed search step throughout the entire budget.

Use the available evaluation budget deliberately, allocating evaluations between discovering promising regions and refining promising solutions.

The algorithm should use objective evaluations as the primary source of information and should not assume access to gradients or internal properties of the objective function.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

### Payload: Noisy × Thinking

- **Environment Mode:** `noisy`
- **Strategy Scaffold:** `thinking`
- **Prompt Component:** `TASK`

```text
You are designing a continuous black-box optimization algorithm.

The algorithm will be evaluated on the specified optimization problem using only calls to problem(x).

Problem information:

- BBOB function ID: 1
- Dimension: 3
- Lower bound: [-5.0, -5.0, -5.0]
- Upper bound: [5.0, 5.0, 5.0]
- Evaluation budget: 500

Environment:

The objective function is stochastic. Evaluating the same point multiple times may produce different objective values because of random variation.

Therefore, a single objective evaluation may be an unreliable basis for deciding which candidate is better.

Design the algorithm so that its optimization decisions account for this stochasticity.

Strategy guidance:

Before writing the code, briefly reason about the main search mechanism, how candidate solutions will be generated and selected, and how the evaluation budget will be allocated.

The implementation should directly reflect this reasoning.

Keep the reasoning focused on decisions that affect the algorithm rather than explaining general optimization concepts.

Design an effective optimization algorithm for this setting.

The algorithm must respect the provided search bounds and evaluation budget.
```

---

## 8. Verification & Keyword Absence Audit

All 12 prompt configurations and evolutionary feedback messages are verified to be free of external solver names, parameter recipes, and interface leaks:

| Factorial Condition | Banned Algorithms | Banned Recipes (`k=3`, `_robust_eval`) | Duplicated Interface | Audit Status |
| :--- | :---: | :---: | :---: | :---: |
| `clean` × `baseline` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `clean` × `vectorization` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `clean` × `guided` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `clean` × `thinking` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `implicit` × `baseline` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `implicit` × `vectorization` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `implicit` × `guided` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `implicit` × `thinking` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `noisy` × `baseline` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `noisy` × `vectorization` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `noisy` × `guided` | 0 found | 0 found | 0 found | PASSED (0 leaks) |
| `noisy` × `thinking` | 0 found | 0 found | 0 found | PASSED (0 leaks) |

*Audit verified via `tests/test_prompts.py`.*
