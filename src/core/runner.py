"""
Runner script executing the LLaMEA evolution loop across BBOB problem IDs.
"""

from dataclasses import dataclass, field
import sys
from pathlib import Path
from typing import Any
from llamea import LLaMEA, LLM
from llamea.loggers import ExperimentLogger

from problems.bbob import BBOBProblem
from llm.prompts import TASK_PROMPT_CLEAN, TASK_PROMPT_NOISY, EXAMPLE_PROMPT, FORMAT_PROMPT
from core.evaluator import Evaluator


@dataclass
class ProblemEvolutionResult:
    """
    Immutable contract returned per-problem by run_evolution_for_problems.
    """
    problem_id: int
    dim: int
    mode: str
    noise_std: float
    best_error: float | None
    run_history: list[Any] = field(default_factory=list)
    experiment_name: str = ""
    error_msg: str | None = None


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
    mode = mode or ("noisy" if noise_std > 0.0 else "clean")
    
    # 1. Setup Prompt
    task_prompt = (
        TASK_PROMPT_NOISY if mode == "noisy" else TASK_PROMPT_CLEAN
    ).format(
        problem_id=problem_id,
        dim=dim,
        lower_bound=problem.lower_bound,
        upper_bound=problem.upper_bound
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
    verbose: bool = True,
    log: bool = False,
    mode: str | None = None,
    budget: int | None = None
) -> list[ProblemEvolutionResult]:
    """
    Run LLaMEA optimization algorithm evolution across a list of BBOB problem IDs or pre-built BBOBProblem instances.

    Returns a list of ProblemEvolutionResult contracts containing run history and metrics.

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
    verbose : bool, optional
        Print progress messages, by default True.
    log : bool, optional
        Enable detailed logging, by default False.
    mode : str | None, optional
        Experiment mode ("clean" or "noisy"). If None, auto-derived from noise_std.
    budget : int | None, optional
        Alias for max_evaluations.
    """
    eval_budget = budget if budget is not None else max_evaluations

    results: list[ProblemEvolutionResult] = []
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
        mode_str = mode or ("noisy" if noise_std > 0.0 else "clean")

        if verbose:
            print(f"\n>>> Evolving algorithm for BBOB Problem {problem_id} (noise_std={noise_std})...")
        try:
            optimizer = run_evolution_for_problem(
                problem=problem,
                llm=llm,
                budget=eval_budget,
                iterations=iterations,
                mode=mode_str,
                noise_std=noise_std,
                log=log
            )
            
            # Reset the problem so it can accept more evaluations in the future
            problem.reset()
            
            best_sol = optimizer.best_so_far
            best_error = getattr(best_sol, 'metadata', {}).get("final_error", float('inf'))
            experiment_name = f"bbob_{problem_id}_dim{problem.dim}_{mode_str}"
            
            results.append(
                ProblemEvolutionResult(
                    problem_id=problem_id,
                    dim=problem.dim,
                    mode=mode_str,
                    noise_std=noise_std,
                    best_error=best_error,
                    run_history=optimizer.run_history,
                    experiment_name=experiment_name,
                    error_msg=None,
                )
            )
            
            if verbose:
                print(f"--- Completed BBOB Problem {problem_id}! Best Final Error: {best_error:.4f} ---")
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
                    error_msg=str(e),
                )
            )
    return results


