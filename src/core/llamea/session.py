import math
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from llamea import LLaMEA

from core.config import DATA_DIR
from core.llamea.evaluator import Evaluator
from core.llamea.prompts import (
    EXAMPLE_PROMPT,
    FORMAT_PROMPT,
    PromptStrategy,
    build_task_prompt,
)
from core.problems.bbob import BBOBProblem
from infra.llm.client import LLMClient
from infra.storage.base import ExperimentRepository
from infra.storage.code.repository import CodeRepository


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
    """
    Manages the lifecycle of a single LLaMEA synthesis session on a BBOB problem.

    Workflow:
                   LLaMEASession(problem, llm, db, budget, iterations)
                                        │
                                        ▼
                    Initialize DB Experiment (Create / Resume ID)
                                        │
                                        ▼
                               LLaMEASession.run()
                                        │
               ┌────────────────────────┴────────────────────────┐
               ▼                                                 ▼
       Build Task Prompt                                 Setup Evaluator & Engine
               │                                                 │
               └────────────────────────┬────────────────────────┘
                                        ▼
               ┌──────────────────────────────────────────────────┐
               │ ↺ Evolutionary Synthesis Loop (for N iterations) │
               │                                                  │
               │   LLM Generates / Mutates Code ─────────┐        │
               │            ▲                            │        │
               │            │ (Feedback:                 ▼        │
               │            │  error / score)   Evaluator Scores  │
               │            └─────────────────── & Logs Iteration │
               └────────────────────────┬─────────────────────────┘
                                        │
               ┌────────────────────────┴────────────────────────┐
            Success                                           Failure
      (mark DB completed)                              (mark DB failed)
             │                                                 │
             ▼                                                 ▼
       Extract Best Solution                            Raise Exception / Log Error
       Return SessionResult
    """

    def __init__(
        self,
        problem: BBOBProblem,
        llm_client: LLMClient,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        budget: int = 1000,
        iterations: int = 10,
        resume_experiment_id: int | None = None,
        prompt_strategy: PromptStrategy | str = PromptStrategy.BASELINE,
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
        self._prompt_strategy = (
            PromptStrategy(prompt_strategy) if isinstance(prompt_strategy, str) else prompt_strategy
        )

        self._init_experiment_context(resume_experiment_id)

    def _init_experiment_context(self, resume_experiment_id: int | None) -> None:
        """Determines whether to resume an existing experiment or initialize a fresh one, setting state accordingly."""
        if resume_experiment_id is not None:
            status, max_iter = self._db_repo.get_experiment_status(resume_experiment_id)
            if status != "running":
                incomplete = self._db_repo.get_incomplete_experiments(
                    self._problem.problem_id,
                    self._problem.dim,
                    self._problem.mode,
                    self._llm_client.model.name,
                    self._problem.noise_std,
                    instance_id=self._problem.instance_id,
                    prompt_strategy=self._prompt_strategy,
                )
                raise ValueError(
                    f"Cannot resume experiment {resume_experiment_id} because its status is '{status}'.\n"
                    f"Please start a new experiment without passing an ID, or choose from these "
                    f"incomplete experiments matching your parameters: {incomplete}"
                )

            self._initial_iteration = max_iter
            self._experiment_id = resume_experiment_id
        else:
            self._initial_iteration = 0
            self._experiment_id = self._db_repo.create_experiment(
                problem_id=self._problem.problem_id,
                instance_id=self._problem.instance_id,
                dim=self._problem.dim,
                mode=self._problem.mode,
                llm_name=self._llm_client.model.name,
                noise_std=self._problem.noise_std,
                true_optimum=self._problem.true_optimum,
                prompt_strategy=self._prompt_strategy,
            )

        self._archive_dir = (
            DATA_DIR
            / "evolution_state"
            / self._experiment_name
            / f"experiment_{self._experiment_id}"
        )
        self._archive_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _experiment_name(self) -> str:
        """Derived name string for the experiment context."""
        return f"bbob_{self._problem.problem_id}_dim{self._problem.dim}_{self._problem.mode}"

    def run(self) -> SessionResult:
        """Runs the complete evolution loop for the problem."""
        print(
            f"\n=== Starting LLaMEA Evolution: BBOB-{self._problem.problem_id} (Dim {self._problem.dim}, Mode {self._problem.mode}, Exp {self._experiment_id}, Strategy {self._prompt_strategy}) [Budget: {self._budget} evals | Max Iterations: {self._iterations}] ===",
            flush=True,
        )

        try:
            task_prompt = build_task_prompt(
                problem_id=self._problem.problem_id,
                dim=self._problem.dim,
                lower_bound=self._problem.lower_bound,
                upper_bound=self._problem.upper_bound,
                mode=self._problem.mode,
                strategy=self._prompt_strategy,
            )
            evaluator = self._setup_evaluator()
            synthesis_engine = self._create_synthesis_engine(evaluator, task_prompt)

            synthesis_engine.run()
        except Exception as e:
            self._db_repo.mark_failed(self._experiment_id, str(e))
            raise
        else:
            self._db_repo.mark_completed(self._experiment_id)

            best_so_far = synthesis_engine.best_so_far
            fitness_score = best_so_far.fitness  # This is -final_error (LLaMEA convention)
            if (
                fitness_score is not None
                and not math.isnan(fitness_score)
                and not math.isinf(fitness_score)
            ):
                # fitness_score = -final_error, so final_error = -fitness_score
                best_error = -fitness_score
                # Reconstruct the raw algorithm objective value for display:
                # final_error = |raw_obj - true_optimum|, and raw_obj ≈ true_optimum - final_error
                # but we don't have the sign, so we retrieve from DB
                raw_fitness = self._db_repo.get_best_raw_fitness(self._experiment_id)
            else:
                fitness_score = None
                best_error = None
                raw_fitness = None

            algorithm_name = best_so_far.name or "None"

            self._print_report(algorithm_name, raw_fitness, best_error)

            return SessionResult(
                problem_id=self._problem.problem_id,
                dim=self._problem.dim,
                mode=self._problem.mode,
                noise_std=self._problem.noise_std,
                best_error=best_error,
                experiment_id=self._experiment_id,
                run_history=synthesis_engine.run_history,
                experiment_name=self._experiment_name,
                llm_name=self._llm_client.model.name,
                best_solution=synthesis_engine.best_so_far,
                error_msg=None,
                problem_profile=evaluator.problem_profile,
            )

    def _create_synthesis_engine(self, evaluator: Evaluator, task_prompt: str) -> LLaMEA:
        """Creates a new LLaMEA synthesis engine or resumes from a warm-start session state if it exists."""
        synthesis_engine = None
        state_file = self._archive_dir / "llamea_config.pkl"

        if state_file.exists():
            print(f"[i] Existing session state found — resuming from {self._archive_dir}")
            try:
                synthesis_engine = LLaMEA.warm_start(str(self._archive_dir))
                if synthesis_engine is not None:
                    synthesis_engine.f = evaluator
                    synthesis_engine.llm = self._llm_client
                    print(
                        f"[i] Resumed at generation {synthesis_engine.generation}, "
                        f"history size {len(synthesis_engine.run_history)}"
                    )
            except Exception as e:
                print(f"[!] Warm start failed, starting fresh: {e}")
                synthesis_engine = None

        if synthesis_engine is None:
            synthesis_engine = LLaMEA(
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

        synthesis_engine.logger = SimpleNamespace(dirname=str(self._archive_dir))

        return synthesis_engine

    def _setup_evaluator(self) -> Evaluator:
        """Initializes the problem evaluator with experiment metadata and budget limits."""
        return Evaluator(
            problem=self._problem,
            db_repo=self._db_repo,
            code_repo=self._code_repo,
            budget=self._budget,
            experiment_id=self._experiment_id,
            initial_iteration=self._initial_iteration,
            experiment_meta={
                "experiment_id": self._experiment_id,
                "problem_id": self._problem.problem_id,
                "dim": self._problem.dim,
                "mode": self._problem.mode,
                "noise_std": self._problem.noise_std,
                "llm_name": self._llm_client.model.name,
                "instance_id": self._problem.instance_id,
            },
        )

    def _print_report(
        self,
        algorithm_name: str,
        raw_fitness: float | None,
        final_error: float | None,
    ) -> None:
        """Prints a human-readable console report highlighting objective value and error metrics of the best candidate."""
        true_opt = self._problem.true_optimum
        fit_val = -final_error if final_error is not None else float("-inf")
        raw_str = f"{raw_fitness:.6f}" if raw_fitness is not None else "N/A (All Executions Failed)"
        err_str = f"{final_error:.6e}" if final_error is not None else "N/A"
        fit_str = f"{fit_val:.6e}" if fit_val != float("-inf") else "-inf"

        print("\n" + "=" * 70)
        print(
            f"=== BBOB-{self._problem.problem_id} Evolution Best Solution Summary ({self._problem.mode.upper()}) ==="
        )
        print(f"  Best Algorithm Name:            {algorithm_name}")
        print(f"  Returned Objective Value (Obj): {raw_str}")
        print(f"  True Global Optimum (Opt):      {true_opt:.6f}")
        print(f"  Final Absolute Error (|Obj-Opt|): {err_str} (Target = 0.0)")
        print(f"  LLaMEA Fitness Score (-Error):  {fit_str} (Higher is better, Max = 0.0)")
        print("=" * 70 + "\n")
