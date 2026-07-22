from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from llamea import LLaMEA

from core.llamea.evaluator import Evaluator
from core.llamea.prompts import (
    EXAMPLE_PROMPT,
    FORMAT_PROMPT,
    build_task_prompt,
)
from core.problems.bbob import BBOBProblem
from infra.llm.client import LLMClient
from infra.storage.base import ExperimentRepository
from infra.storage.filesystem.code import CodeRepository
from infra.storage.run_context import RunContext


@dataclass
class SessionResult:
    """Immutable contract returned per-problem by LLaMEASession.run()."""

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


class LLaMEASession:
    """Manages the lifecycle of a single LLaMEA synthesis session on a BBOB problem."""

    def __init__(
        self,
        problem: BBOBProblem,
        llm: LLMClient,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        run_context: RunContext,
        budget: int = 1000,
        iterations: int = 10,
        noise_std: float = 0.0,
        cleanup_on_completion: bool = True,
    ):
        """Initializes the synthesis session with its parameters and required repositories."""
        self._problem = problem
        self._llm_client = llm
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._run_context = run_context
        self._run_id = run_context.run_id
        self._archive_dir = run_context.archive_dir
        self._budget = budget
        self._iterations = iterations
        self._noise_std = noise_std
        self._cleanup_on_completion = cleanup_on_completion

        # Resolve llm_name explicitly from the LLM provider
        self._llm_name = getattr(llm, "name", getattr(llm, "model", "unknown"))

        # Derived fields
        self._problem_id = problem.problem_id
        self._dim = problem.dim
        self._mode = "noisy" if noise_std > 0.0 else "clean"
        self._experiment_name = f"bbob_{self._problem_id}_dim{self._dim}_{self._mode}"

    def run(self) -> SessionResult:
        """Runs the complete evolution loop for the problem."""
        print(
            f"\n--- Starting LLaMEA Evolution for BBOB-{self._problem_id} (Dim {self._dim}, Mode {self._mode}, Run {self._run_id}) ---"
        )

        task_prompt = build_task_prompt(
            problem_id=self._problem_id,
            dim=self._dim,
            lower_bound=self._problem.lower_bound,
            upper_bound=self._problem.upper_bound,
            is_noisy=self._noise_std > 0.0,
        )
        evaluator = self._setup_evaluator()

        is_resumed = (self._archive_dir / "llamea_config.pkl").exists()

        optimizer = self._create_optimizer(evaluator, self._archive_dir, is_resumed, task_prompt)
        self._configure_pickle_archive(optimizer)

        # Run loop
        optimizer.run()

        # Final persistence and cleanup via db_repo
        self._save_final_results()

        # Report and return result
        self._print_report(optimizer.best_so_far)

        return self._build_session_result(optimizer.best_so_far, optimizer, evaluator)

    def _create_optimizer(
        self, evaluator: Evaluator, archive_dir: Path, is_resumed: bool, task_prompt: str
    ) -> LLaMEA:
        """Creates a new LLaMEA optimizer or resumes from a warm-start pickle checkpoint if it exists."""
        optimizer = None

        if is_resumed:
            print(f"[i] Checkpoint found — resuming from {archive_dir}")
            try:
                optimizer = LLaMEA.warm_start(str(archive_dir))
                if optimizer is not None:
                    optimizer.f = evaluator
                    optimizer.llm = self._llm_client
                    print(
                        f"[i] Resumed at generation {optimizer.generation}, "
                        f"history size {len(optimizer.run_history)}"
                    )
            except Exception as e:
                print(f"[!] Warm start failed, starting fresh: {e}")
                optimizer = None

        if optimizer is None:
            optimizer = LLaMEA(
                f=evaluator,
                llm=self._llm_client,
                n_parents=1,
                n_offspring=1,
                budget=self._iterations,
                task_prompt=task_prompt,
                example_prompt=EXAMPLE_PROMPT,
                output_format_prompt=FORMAT_PROMPT,
                experiment_name=self._experiment_name,
                elitism=True,
                log=False,
                max_workers=1,
                parallel_backend="sequential",
            )

        return optimizer

    def _setup_evaluator(self) -> Evaluator:
        """Initializes the problem evaluator with experiment metadata and budget limits."""
        experiment_meta = {
            "run_id": self._run_id,
            "problem_id": self._problem_id,
            "dim": self._dim,
            "mode": self._mode,
            "noise_std": self._noise_std,
            "llm_name": self._llm_name,
        }
        return Evaluator(
            problem=self._problem,
            db_repo=self._db_repo,
            code_repo=self._code_repo,
            budget=self._budget,
            noise_std=self._noise_std,
            run_id=self._run_id,
            experiment_meta=experiment_meta,
        )

    def _configure_pickle_archive(self, optimizer: LLaMEA) -> None:
        """Sets a minimal logger shim so LLaMEA's pickle_archive() writes to our archive_dir."""
        optimizer.logger = SimpleNamespace(dirname=str(self._archive_dir))
        optimizer.log = False

    def _save_final_results(self) -> None:
        """Commits the JSONL checkpoint cache to SQLite DB. Candidate code files are saved per-iteration in Evaluator."""
        if self._cleanup_on_completion:
            self._db_repo.commit_and_cleanup(self._problem_id, self._dim, self._mode, self._run_id)
        else:
            self._db_repo.commit_without_cleanup(
                self._problem_id, self._dim, self._mode, self._run_id
            )

    def _build_session_result(
        self, best_sol: Any, optimizer: LLaMEA, evaluator: Evaluator
    ) -> SessionResult:
        """Constructs and returns the immutable SessionResult contract summarizing the optimization run."""
        best_error = float("inf")
        if best_sol is not None:
            meta = getattr(best_sol, "metadata", None)
            try:
                final_err = meta.fitness.final_error
            except AttributeError:
                meta = getattr(best_sol, "metadata", {})
                final_err = meta.get("final_error", getattr(best_sol, "fitness", "N/A"))

            if isinstance(final_err, (int, float)):
                best_error = final_err

        return SessionResult(
            problem_id=self._problem_id,
            dim=self._dim,
            mode=self._mode,
            noise_std=self._noise_std,
            best_error=best_error if best_error != float("inf") else None,
            run_id=self._run_id,
            run_history=optimizer.run_history,
            experiment_name=self._experiment_name,
            llm_name=self._llm_name,
            best_solution=best_sol,
            error_msg=None,
            problem_profile=evaluator.problem_profile,
        )

    def _print_report(self, best_sol: Any) -> None:
        """Prints a human-readable console report highlighting objective value and error metrics of the best candidate."""
        if best_sol is not None:
            meta = getattr(best_sol, "metadata", None)
            try:
                returned_val = meta.fitness.raw_fitness
                true_opt = self._problem.true_optimum
                final_err = meta.fitness.final_error
            except AttributeError:
                meta = getattr(best_sol, "metadata", {})
                returned_val = meta.get("raw_fitness", "N/A")
                true_opt = meta.get("true_optimum", "N/A")
                final_err = meta.get("final_error", getattr(best_sol, "fitness", "N/A"))

            err_str = f"{final_err:.6e}" if isinstance(final_err, (int, float)) else str(final_err)
            val_str = (
                f"{returned_val:.6f}"
                if isinstance(returned_val, (int, float))
                else str(returned_val)
            )
            opt_str = f"{true_opt:.6f}" if isinstance(true_opt, (int, float)) else str(true_opt)
            fit_str = (
                f"{best_sol.fitness:.6e}"
                if hasattr(best_sol, "fitness") and isinstance(best_sol.fitness, (int, float))
                else "N/A"
            )

            print("\n" + "=" * 65)
            print(
                f"=== BBOB-{self._problem_id} Evolution Best Solution Summary ({self._mode.upper()}) ==="
            )
            print(f"  Best Algorithm Name:       {best_sol.name}")
            print(f"  Returned Objective Value:  {val_str}")
            print(f"  True Global Optimum:       {opt_str}")
            print(f"  Final Absolute Error:       {err_str} (Target = 0.0)")
            print(f"  Negated Error (LLaMEA Fitness): {fit_str} [= -|error|, higher is better]")
            print("=" * 65 + "\n")
