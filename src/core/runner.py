"""
Runner script executing the LLaMEA evolution loop across BBOB problem IDs.
"""

import sys
from pathlib import Path
from typing import Any
from llamea import LLaMEA, LLM
from llamea.loggers import ExperimentLogger

from problems.bbob import BBOBProblem
from llm.prompts import TASK_PROMPT_CLEAN, TASK_PROMPT_NOISY, EXAMPLE_PROMPT, FORMAT_PROMPT
from core.evaluator import Evaluator
from analysis.results import save_summary


class ProblemLogger(ExperimentLogger):
    def __init__(self, base_dir: str | Path, name: str = ""):
        self._base_dir = str(base_dir)
        # Calling super().__init__(name) creates the directory structure
        super().__init__(name)

    def create_log_dir(self, name: str = "") -> str:
        base_path = Path(self._base_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        (base_path / "configspace").mkdir(parents=True, exist_ok=True)
        (base_path / "code").mkdir(parents=True, exist_ok=True)
        return str(base_path)


def run_evolution_for_problem(
    problem: BBOBProblem,
    llm: LLM,
    budget: int = 1000,
    iterations: int = 10,
    mode: str | None = None,
    noise_std: float = 0.0,
    log: bool = False
) -> LLaMEA:
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
    mode : str | None, optional
        Experiment mode ("clean" or "noisy"). If None, automatically derived from noise_std.
    noise_std : float, optional
        Standard deviation of Gaussian noise added to objective evaluations, by default 0.0.
    log : bool, optional
        Whether to log results and code at each iteration, by default False.
    """
    problem_id = problem.problem_id
    dim = problem.dim
    effective_noise_std = noise_std if noise_std > 0.0 else getattr(problem, "noise_std", 0.0)
    effective_mode = mode if mode is not None else ("noisy" if effective_noise_std > 0.0 else "clean")
    
    # 1. Setup Prompt
    task_prompt = (
        TASK_PROMPT_NOISY if effective_mode == "noisy" else TASK_PROMPT_CLEAN
    ).format(
        problem_id=problem_id,
        dim=dim,
        lower_bound=problem.lower_bound,
        upper_bound=problem.upper_bound
    )
        
    print(f"\n--- Starting LLaMEA Evolution for BBOB-{problem_id} (Dim {dim}, Mode {effective_mode}) ---")
    
    # 2. Setup Evaluator
    evaluator = Evaluator(problem=problem, budget=budget, noise_std=effective_noise_std)

    # 3. Initialize LLaMEA
    experiment_name = f"bbob_{problem_id}_dim{dim}_{effective_mode}"
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
        log=log
    )

    # 4. Inject custom logger to keep outputs organized
    if log:
        base_dir = Path("logs") / experiment_name
        optimizer.logger = ProblemLogger(base_dir=base_dir, name=experiment_name)
        optimizer.llm.set_logger(optimizer.logger)

    # 5. Run the evolution loop
    optimizer.run()
    
    # Return the optimizer instance so the caller can access optimizer.run_history and optimizer.best_so_far
    return optimizer


def run_evolution_for_problems(
    problems: list[int | BBOBProblem],
    dim: int = 2,
    noise_std: float = 0.0,
    llm: LLM = None,
    max_evaluations: int = 1000,
    iterations: int = 10,
    output_dir: str | Path = "generated_algorithms",
    log_dir: str | Path = "logs",
    verbose: bool = True,
    log: bool = False,
    mode: str | None = None,
    budget: int | None = None
) -> dict[int, float | None]:
    """
    Run LLaMEA optimization algorithm evolution across a list of BBOB problem IDs or pre-built BBOBProblem instances.

    Parameters
    ----------
    problems : list[int | BBOBProblem]
        List of BBOB problem IDs (e.g. [1, 2, 3]) or pre-configured BBOBProblem instances.
    dim : int, optional
        Dimensionality of the search space (used if problem IDs are passed).
    noise_std : float, optional
        Standard deviation of Gaussian noise added to objective evaluations (used if problem IDs are passed).
    llm : LLM
        The LLM object used for evolution.
    max_evaluations : int, optional
        Maximum evaluation budget per candidate algorithm run, by default 1000.
    iterations : int, optional
        Number of LLaMEA evolution steps, by default 10.
    output_dir : str | Path, optional
        Directory to store results summaries, by default "generated_algorithms".
    log_dir : str | Path, optional
        Directory for logs, by default "logs".
    verbose : bool, optional
        Print progress messages, by default True.
    log : bool, optional
        Enable detailed logging, by default False.
    mode : str | None, optional
        Experiment mode ("clean" or "noisy"). If None, auto-derived from problem.is_noisy.
    budget : int | None, optional
        Alias for max_evaluations.
    """
    eval_budget = budget if budget is not None else max_evaluations

    results: dict[int, float | None] = {}
    for item in problems:
        if isinstance(item, int):
            problem = BBOBProblem(
                problem_id=item,
                dim=dim,
                instance_id=1
            )
        else:
            problem = item

        problem_id = problem.problem_id
        effective_noise_std = noise_std if noise_std > 0.0 else getattr(problem, "noise_std", 0.0)
        effective_mode = mode if mode is not None else ("noisy" if effective_noise_std > 0.0 else "clean")

        if verbose:
            print(f"\n>>> Evolving algorithm for BBOB Problem {problem_id} (noise_std={effective_noise_std})...")
        try:
            optimizer = run_evolution_for_problem(
                problem=problem,
                llm=llm,
                budget=eval_budget,
                iterations=iterations,
                mode=effective_mode,
                noise_std=effective_noise_std,
                log=log
            )
            
            # Reset the problem so it can accept more evaluations in the future
            problem.reset()
            
            best_sol = optimizer.best_so_far
            
            # Save the summary of all runs
            experiment_name = f"bbob_{problem_id}_dim{problem.dim}_{effective_mode}"
            target_base = Path(log_dir) if log else Path(output_dir)
            problem_dir = target_base / experiment_name
                
            summary_path = save_summary(
                history=optimizer.run_history,
                problem_id=problem_id,
                dim=dim,
                output_dir=problem_dir,
                mode=mode
            )
                
            best_error = getattr(best_sol, 'metadata', {}).get("final_error", float('inf'))
            results[problem_id] = best_error
            
            if verbose:
                print(f"--- Completed BBOB Problem {problem_id}! Best Final Error: {best_error:.4f} ---")
                print(f"Saved summary to: {summary_path}\n")
        except Exception as e:
            if verbose:
                print(f"Error evolving algorithm for problem {problem_id}: {e}", file=sys.stderr)
            results[problem_id] = None
    return results


def run_cross_evaluation(code: str, name: str, problem: BBOBProblem, budget: int = 1000, noise_std: float = 0.0) -> dict[str, Any]:
    """
    Cross-evaluate an already generated algorithm code against a problem environment
    (clean or noisy).
    """
    from core.executor import AlgorithmExecutor
    
    executor = AlgorithmExecutor()
    problem.reset()
    eval_func = (lambda x: problem(x, noise_std=noise_std)[noise_std]) if noise_std > 0.0 else problem
    try:
        returned_fitness = executor.execute_algorithm(
            code=code, 
            name=name, 
            dim=problem.dim, 
            problem=eval_func, 
            budget=budget
        )
        true_optimum = problem.true_optimum
        final_error = abs(returned_fitness - true_optimum)
        return {
            "success": True,
            "final_error": final_error,
            "algorithm_returned_fitness": returned_fitness,
            "true_optimum": true_optimum,
            "noise_std": noise_std
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
