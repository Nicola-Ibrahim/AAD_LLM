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
from infra.storage.code_store.code import CodeRepository


@dataclass
class SessionResult:
    """Immutable contract returned per-problem by LLaMEASession.run()."""

    problem_id: int
    dim: int
    mode: str
    noise_std: float
    best_error: float
    experiment_id: int = 1
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
        llm_client: LLMClient,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        budget: int = 1000,
        iterations: int = 10,
        noise_std: float = 0.0,
    ):
        """Initializes the synthesis session with its parameters and required repositories."""
        if llm_client is None:
            raise ValueError("LLaMEASession requires a valid LLMClient")

        self._problem = problem
        self._llm_client = llm_client
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._budget = budget
        self._iterations = iterations
        self._noise_std = noise_std

        # Derived fields
        self._problem_id = problem.problem_id
        self._dim = problem.dim
        self._mode = "noisy" if noise_std > 0.0 else "clean"
        self._experiment_name = f"bbob_{self._problem_id}_dim{self._dim}_{self._mode}"

        # Initialize the experiment context via the DB
        self._experiment_id = self._db_repo.create_experiment(
            problem_id=self._problem_id,
            dim=self._dim,
            mode=self._mode,
            llm_name=self._llm_client.model.name,
            noise_std=self._noise_std,
            true_optimum=self._problem.true_optimum,
        )

        self._archive_dir = self._init_archive_dir()

    def _init_archive_dir(self) -> Path:
        """Initializes and creates the session evolution state archive directory."""
        from core.config import DATA_DIR

        archive_dir = (
            DATA_DIR
            / "evolution_state"
            / self._experiment_name
            / f"experiment_{self._experiment_id}"
        )
        archive_dir.mkdir(parents=True, exist_ok=True)
        return archive_dir

    def run(self) -> SessionResult:
        """Runs the complete evolution loop for the problem."""
        print(
            f"\n--- Starting LLaMEA Evolution for BBOB-{self._problem_id} (Dim {self._dim}, Mode {self._mode}, Experiment {self._experiment_id}) ---"
        )

        try:
            task_prompt = build_task_prompt(
                problem_id=self._problem_id,
                dim=self._dim,
                lower_bound=self._problem.lower_bound,
                upper_bound=self._problem.upper_bound,
                is_noisy=self._noise_std > 0.0,
            )
            evaluator = self._setup_evaluator()
            optimizer = self._create_optimizer(evaluator, task_prompt)

            optimizer.run()
        except Exception as e:
            self._db_repo.mark_failed(self._experiment_id, str(e))
            raise
        else:
            # Final persistence and cleanup via db_repo
            self._db_repo.mark_completed(self._experiment_id)

            # Report and return result
            self._print_report(optimizer.best_so_far)

            return SessionResult(
                problem_id=self._problem_id,
                dim=self._dim,
                mode=self._mode,
                noise_std=self._noise_std,
                best_error=optimizer.best_so_far.metadata.fitness.final_error,
                experiment_id=self._experiment_id,
                run_history=optimizer.run_history,
                experiment_name=self._experiment_name,
                llm_name=self._llm_client.model.name,
                best_solution=optimizer.best_so_far,
                error_msg=None,
                problem_profile=evaluator.problem_profile,
            )

    def _create_optimizer(self, evaluator: Evaluator, task_prompt: str) -> LLaMEA:
        """Creates a new LLaMEA optimizer or resumes from a warm-start session state if it exists."""
        optimizer = None
        state_file = self._archive_dir / "llamea_config.pkl"

        if state_file.exists():
            print(f"[i] Existing session state found — resuming from {self._archive_dir}")
            try:
                optimizer = LLaMEA.warm_start(str(self._archive_dir))
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

        optimizer.logger = SimpleNamespace(dirname=str(self._archive_dir))

        return optimizer

    def _setup_evaluator(self) -> Evaluator:
        """Initializes the problem evaluator with experiment metadata and budget limits."""
        return Evaluator(
            problem=self._problem,
            db_repo=self._db_repo,
            code_repo=self._code_repo,
            budget=self._budget,
            noise_std=self._noise_std,
            experiment_id=self._experiment_id,
            experiment_meta={
                "experiment_id": self._experiment_id,
                "problem_id": self._problem_id,
                "dim": self._dim,
                "mode": self._mode,
                "noise_std": self._noise_std,
                "llm_name": self._llm_client.model.name,
                "instance_id": self._problem.instance_id,
            },
        )

    def _print_report(self, best_sol: Any) -> None:
        """Prints a human-readable console report highlighting objective value and error metrics of the best candidate."""
        if best_sol is None or not hasattr(best_sol, "metadata") or not best_sol.metadata:
            return

        meta = best_sol.metadata
        returned_val = meta.fitness.raw_fitness
        true_opt = self._problem.true_optimum
        final_err = meta.fitness.final_error
        fit_val = best_sol.fitness if hasattr(best_sol, "fitness") else -final_err

        print("\n" + "=" * 65)
        print(
            f"=== BBOB-{self._problem_id} Evolution Best Solution Summary ({self._mode.upper()}) ==="
        )
        print(f"  Best Algorithm Name:       {best_sol.name}")
        print(f"  Returned Objective Value:  {returned_val:.6f}")
        print(f"  True Global Optimum:       {true_opt:.6f}")
        print(f"  Final Absolute Error:       {final_err:.6e} (Target = 0.0)")
        print(f"  Negated Error (LLaMEA Fitness): {fit_val:.6e} [= -|error|, higher is better]")
        print("=" * 65 + "\n")
