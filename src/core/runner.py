"""
Runner script executing the LLaMEA evolution loop across BBOB problem IDs.
"""

from dataclasses import dataclass, field
import sys
from pathlib import Path
from typing import Any
from llamea import LLaMEA, LLM

from problems.bbob import BBOBProblem
from llm.prompts import TASK_PROMPT_CLEAN, TASK_PROMPT_NOISY, EXAMPLE_PROMPT, FORMAT_PROMPT
from core.evaluator import Evaluator


@dataclass
class ProblemEvolutionResult:
    """
    Immutable contract returned per-problem by run_evolution_for_problems and run_evolution_for_problem.
    """

    problem_id: int
    dim: int
    mode: str
    noise_std: float
    best_error: float | None
    run_history: list[Any] = field(default_factory=list)
    experiment_name: str = ""
    llm_name: str = ""
    error_msg: str | None = None
    best_solution: Any = None

    @property
    def best_so_far(self) -> Any:
        """Keeps backward compatibility with the optimizer.best_so_far property."""
        return self.best_solution


def run_evolution_for_problem(
    problem: BBOBProblem,
    llm: LLM,
    budget: int = 1000,
    iterations: int = 10,
    noise_std: float = 0.0,
    log: bool = True,
    output_dir: str | Path = "experiments",
    llm_name: str = "unknown",
) -> ProblemEvolutionResult:
    """
    Run LLaMEA evolution to synthesize an optimization algorithm for a single BBOB problem.

    Parameters
    ----------
    problem : BBOBProblem
        The configured BBOB problem to solve.
    llm : LLM
        The Large Language Model interface used by LLaMEA.
    budget : int, optional
        Maximum number of evaluations per algorithm run, by default 1000.
    iterations : int, optional
        Number of LLaMEA evolution iterations, by default 10.
    noise_std : float, optional
        Standard deviation of Gaussian noise added to objective evaluations, by default 0.0.
    log : bool, optional
        Whether to log results and code at each iteration, by default False.
    """
    problem_id = problem.problem_id
    dim = problem.dim
    mode = "noisy" if noise_std > 0.0 else "clean"

    # 1. Setup Prompt
    task_prompt = (TASK_PROMPT_NOISY if mode == "noisy" else TASK_PROMPT_CLEAN).format(
        problem_id=problem_id,
        dim=dim,
        lower_bound=problem.lower_bound,
        upper_bound=problem.upper_bound,
    )

    print(f"\n--- Starting LLaMEA Evolution for BBOB-{problem_id} (Dim {dim}, Mode {mode}) ---")

    # 2. Setup Evaluator
    evaluator = Evaluator(problem=problem, budget=budget, noise_std=noise_std)

    # 3. Initialize LLaMEA
    experiment_name = f"bbob_{problem_id}_dim{dim}_{mode}"
    optimizer = LLaMEA(
        f=evaluator,
        llm=llm,
        n_parents=1,
        n_offspring=1,
        budget=iterations,
        task_prompt=task_prompt,
        example_prompt=EXAMPLE_PROMPT,
        output_format_prompt=FORMAT_PROMPT,
        experiment_name=experiment_name,
        elitism=True,
        log=False,  # Set log=False initially to prevent default exp-* folder creation
    )

    # 4. Run the evolution loop
    optimizer.run()

    # 5. Display human-readable evolution summary
    best_sol = optimizer.best_so_far
    best_error = float("inf")
    if best_sol is not None:
        meta: Any = getattr(best_sol, "metadata", None)
        try:
            # Access assuming best_sol.metadata is an IterationMetadata model
            returned_val = meta.fitness.raw_fitness
            true_opt = problem.true_optimum
            final_err = meta.fitness.final_error
        except AttributeError:
            # Fallback for dictionaries or legacy structures
            meta = getattr(best_sol, "metadata", {})
            returned_val = meta.get("raw_fitness", "N/A")
            true_opt = meta.get("true_optimum", "N/A")
            final_err = meta.get("final_error", getattr(best_sol, "fitness", "N/A"))

        if isinstance(final_err, (int, float)):
            best_error = final_err

        err_str = f"{final_err:.6e}" if isinstance(final_err, (int, float)) else str(final_err)
        val_str = (
            f"{returned_val:.6f}" if isinstance(returned_val, (int, float)) else str(returned_val)
        )
        opt_str = f"{true_opt:.6f}" if isinstance(true_opt, (int, float)) else str(true_opt)
        fit_str = (
            f"{best_sol.fitness:.6e}"
            if hasattr(best_sol, "fitness") and isinstance(best_sol.fitness, (int, float))
            else "N/A"
        )

        print("\n" + "=" * 65)
        print(f"=== BBOB-{problem_id} Evolution Best Solution Summary ({mode.upper()}) ===")
        print(f"  Best Algorithm Name:       {best_sol.name}")
        print(f"  Returned Objective Value:  {val_str}")
        print(f"  True Global Optimum:       {opt_str}")
        print(f"  Final Absolute Error:       {err_str} (Target = 0.0)")
        print(f"  Negated Error (LLaMEA Fitness): {fit_str} [= -|error|, higher is better]")
        print("=" * 65 + "\n")

    return ProblemEvolutionResult(
        problem_id=problem_id,
        dim=dim,
        mode=mode,
        noise_std=noise_std,
        best_error=best_error if best_error != float("inf") else None,
        run_history=optimizer.run_history,
        experiment_name=experiment_name,
        llm_name=llm_name,
        best_solution=best_sol,
        error_msg=None,
    )


def run_evolution_for_problems(
    problems: list[BBOBProblem],
    noise_std: float = 0.0,
    llm: LLM | None = None,
    max_evaluations: int = 1000,
    iterations: int = 10,
    verbose: bool = True,
    log: bool = False,
    budget: int | None = None,
    output_dir: str | Path = "experiments",
) -> list[ProblemEvolutionResult]:
    """
    Run LLaMEA optimization algorithm evolution across a list of pre-built BBOBProblem instances.

    Returns a list of ProblemEvolutionResult contracts containing run history and metrics.

    Parameters
    ----------
    problems : list[BBOBProblem]
        List of pre-configured BBOBProblem instances.
    noise_std : float, optional
        Standard deviation of Gaussian noise added to objective evaluations.
    llm : LLM | None, optional
        The LLM object used for evolution.
    max_evaluations : int, optional
        Maximum evaluation budget per candidate algorithm run, by default 1000.
    iterations : int, optional
        Number of LLaMEA evolution steps, by default 10.
    verbose : bool, optional
        Print progress messages, by default True.
    log : bool, optional
        Enable detailed logging, by default False.
    budget : int | None, optional
        Alias for max_evaluations.
    """
    if llm is None:
        raise ValueError("LLM client must be provided to run evolution.")

    eval_budget = budget if budget is not None else max_evaluations
    llm_name = getattr(llm, "model", "unknown") if llm else "unknown"

    results: list[ProblemEvolutionResult] = []
    for problem in problems:
        problem_id = problem.problem_id
        mode_str = "noisy" if noise_std > 0.0 else "clean"

        if verbose:
            print(
                f"\n>>> Evolving algorithm for BBOB Problem {problem_id} (noise_std={noise_std})..."
            )
        try:
            result = run_evolution_for_problem(
                problem=problem,
                llm=llm,
                budget=eval_budget,
                iterations=iterations,
                noise_std=noise_std,
                log=log,
                output_dir=output_dir,
                llm_name=llm_name,
            )
            results.append(result)

            if verbose:
                print(
                    f"--- Completed BBOB Problem {problem_id}! Best Final Error: {result.best_error:.4f} ---"
                )
        except Exception as e:
            if verbose:
                print(f"Error evolving algorithm for problem {problem_id}: {e}", file=sys.stderr)
            results.append(
                ProblemEvolutionResult(
                    problem_id=problem_id,
                    dim=problem.dim,
                    mode=mode_str,
                    noise_std=noise_std,
                    best_error=None,
                    run_history=[],
                    experiment_name=f"bbob_{problem_id}_dim{problem.dim}_{mode_str}",
                    llm_name=llm_name,
                    error_msg=str(e),
                )
            )
    return results
