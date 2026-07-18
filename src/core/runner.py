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
    run_id: int = 1
    run_history: list[Any] = field(default_factory=list)
    experiment_name: str = ""
    llm_name: str = ""
    error_msg: str | None = None
    best_solution: Any = None
    problem_profile: Any = None

    @property
    def best_so_far(self) -> Any:
        """Keeps backward compatibility with the optimizer.best_so_far property."""
        return self.best_solution


class CheckpointLogger:
    """
    Logger shim that gives LLaMEA a dirname so pickle_archive() fires,
    and optionally flushes accumulated solutions to SQLite every N generations.
    """
    def __init__(
        self,
        dirname: str | Path,
        storage_manager: Any = None,      # ExperimentManager — pass None to skip DB flush
        flush_every: int = 5,             # how many generations between DB flushes
        problem_profile: Any = None,      # ProblemProfile for DB record
        mode: str | None = None,
        llm_name: str | None = None,
        run_id: int = 1,
    ):
        self.dirname = str(dirname)   # ← LLaMEA needs this attr for pickle_archive()
        self.attempt = 0
        self._storage_manager = storage_manager
        self._flush_every = flush_every
        self._problem_profile = problem_profile
        self._mode = mode
        self._llm_name = llm_name
        self._run_id = run_id
        self._pending_history: list = []
        self._generation = 0

    def log_population(self, population):
        """Called by LLaMEA after every generation."""
        self._generation += 1
        self._pending_history.extend(population)
        if self._storage_manager and self._generation % self._flush_every == 0:
            self._flush_to_db()

    def flush_remaining(self):
        """Called manually at the end of a full run to save any leftover generations."""
        if self._storage_manager and self._pending_history:
            self._flush_to_db()

    def _flush_to_db(self):
        if not self._pending_history:
            return
        try:
            self._storage_manager.save_experiment(
                history=list(self._pending_history),
                problem=self._problem_profile,
                mode=self._mode,
                llm_name=self._llm_name,
                run_id=self._run_id,
            )
            self._pending_history = []
        except Exception as e:
            print(f"[!] Periodic DB flush failed (data still in memory): {e}")

    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude storage manager from pickle since it contains DB connections
        state["_storage_manager"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    # Stubs for LLaMEA methods we don't need
    def log_individual(self, ind): pass
    def log_code(self, attempt, name, code): pass
    def log_conversation(self, role, content): pass
    def log_import_fails(self, fails): pass
    def set_attempt(self, attempt): self.attempt = attempt


def run_evolution_for_problem(
    problem: BBOBProblem,
    llm: LLM,
    budget: int = 1000,
    iterations: int = 10,
    noise_std: float = 0.0,
    log: bool = True,
    output_dir: str | Path = "experiments",
    llm_name: str = "unknown",
    run_id: int = 1,
    checkpoint_dir: Path | None = None,
    storage_manager: Any = None,
    flush_every: int = 5,
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
    ckpt_path = None
    experiment_name = f"bbob_{problem_id}_dim{dim}_{mode}"
    archive_dir: Path | None = None

    if checkpoint_dir is not None:
        archive_dir = Path(checkpoint_dir) / experiment_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        ckpt_path = archive_dir / f"run{run_id}_p{problem_id}_d{dim}_{mode}.ckpt.json"

    experiment_meta = {
        "run_id": run_id,
        "problem_id": problem_id,
        "dim": dim,
        "mode": mode,
        "noise_std": noise_std,
        "llm_name": llm_name,
    }

    evaluator = Evaluator(
        problem=problem,
        budget=budget,
        noise_std=noise_std,
        run_id=run_id,
        json_checkpoint_path=ckpt_path,
        experiment_meta=experiment_meta,
    )

    # 3. Attempt warm start (crash recovery)
    is_resumed = False
    optimizer = None
    if archive_dir and (archive_dir / "llamea_config.pkl").exists():
        print(f"[i] Checkpoint found — resuming from {archive_dir}")
        try:
            optimizer = LLaMEA.warm_start(str(archive_dir))
            if optimizer is not None:
                optimizer.f = evaluator   # re-inject fresh evaluator
                optimizer.llm = llm       # re-inject fresh LLM connection
                is_resumed = True
                print(f"[i] Resumed at generation {optimizer.generation}, "
                      f"history size {len(optimizer.run_history)}")
        except Exception as e:
            print(f"[!] Warm start failed, starting fresh: {e}")
            optimizer = None

    # 4. Fresh start if no checkpoint or warm_start failed
    if optimizer is None:
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
            log=False,                  # prevent default exp-* folder creation
            max_workers=1,
            parallel_backend="sequential",
        )

    # 5. Attach CheckpointLogger to enable pickle_archive() + periodic DB flush
    if archive_dir is not None:
        ckpt_logger = CheckpointLogger(
            dirname=archive_dir,
            storage_manager=storage_manager,
            flush_every=flush_every,
            problem_profile=evaluator.problem_profile,
            mode=mode,
            llm_name=llm_name,
            run_id=run_id,
        )
        optimizer.logger = ckpt_logger
        optimizer.log = True
        if is_resumed:
            # If resumed, restore the accumulated run history to CheckpointLogger
            ckpt_logger._pending_history = list(optimizer.run_history)
            ckpt_logger._generation = optimizer.generation

    # 6. Run evolution (pass archive_path only on resume)
    optimizer.run(archive_path=str(archive_dir) if is_resumed else None)

    # 7. Flush any remaining unsaved generations to DB
    if archive_dir and optimizer.logger:
        optimizer.logger.flush_remaining()

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
        run_id=run_id,
        run_history=optimizer.run_history,
        experiment_name=experiment_name,
        llm_name=llm_name,
        best_solution=best_sol,
        error_msg=None,
        problem_profile=evaluator.problem_profile,
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
    checkpoint_dir: Path | None = None,
    storage_manager: Any = None,
    flush_every: int = 5,
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
                checkpoint_dir=checkpoint_dir,
                storage_manager=storage_manager,
                flush_every=flush_every,
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
