import math
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from llamea import LLaMEA

from config import DATA_DIR
from domain.interfaces import BaseProblem
from domain.vos import ProblemProfile
from synthesis.evaluator import Evaluator
from synthesis.prompts import (
    EXAMPLE_PROMPT,
    FORMAT_PROMPT,
    PromptStrategy,
    build_task_prompt,
)
from infra.llm.client import LLMClient
from infra.problems.bbob import BBOBProblem
from infra.storage.base import ExperimentRepository
from infra.storage.code.repository import CodeRepository
from domain.services.noise_strategy import NoiseStrategyFactory


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
        problem: BaseProblem,
        experiment_id: int,
        initial_iteration: int,
        prompt_strategy: PromptStrategy,
        llm_client: LLMClient,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        budget: int,
        iterations: int,
    ):
        """Initializes the synthesis session instance directly with fully resolved domain objects.

        Note: Use factory methods `LLaMEASession.create(...)` or `LLaMEASession.resume(...)`.
        """
        if llm_client is None:
            raise ValueError("LLaMEASession requires a valid LLMClient")

        self._problem = problem
        self._experiment_id = experiment_id
        self._initial_iteration = initial_iteration
        self._prompt_strategy = prompt_strategy
        self._llm_client = llm_client
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._budget = budget
        self._iterations = iterations

        self._archive_dir = (
            DATA_DIR
            / "evolution_state"
            / self._experiment_name
            / f"experiment_{self._experiment_id}"
        )
        self._archive_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create(
        cls,
        problem: BaseProblem,
        llm_client: LLMClient,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        budget: int = 1000,
        iterations: int = 10,
        prompt_strategy: PromptStrategy | str = PromptStrategy.BASELINE,
    ) -> "LLaMEASession":
        """Factory method for creating a brand-new synthesis session."""
        if llm_client is None:
            raise ValueError("LLaMEASession requires a valid LLMClient")
        if problem is None:
            raise ValueError("LLaMEASession.create requires a valid problem")
        strategy = (
            PromptStrategy(prompt_strategy) if isinstance(prompt_strategy, str) else prompt_strategy
        )
        problem_profile = ProblemProfile(
            problem_id=problem.problem_id,
            dim=problem.dim,
            noise_std=problem.noise_std,
            noise_model=problem.noise_model,
            instance_id=problem.instance_id,
            true_optimum=problem.true_optimum,
        )
        exp_id = db_repo.create_experiment(
            problem=problem_profile,
            mode=problem.mode,
            llm_name=llm_client.model.name,
            prompt_strategy=strategy,
            budget=budget,
            iterations=iterations,
        )
        return cls(
            problem=problem,
            experiment_id=exp_id,
            initial_iteration=0,
            prompt_strategy=strategy,
            llm_client=llm_client,
            db_repo=db_repo,
            code_repo=code_repo,
            budget=budget,
            iterations=iterations,
        )

    @classmethod
    def resume(
        cls,
        experiment_id: int,
        llm_client: LLMClient,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        iterations: int | None = None,
    ) -> "LLaMEASession":
        """Factory method for resuming an existing synthesis session from database state."""
        if llm_client is None:
            raise ValueError("LLaMEASession requires a valid LLMClient")
        exps = db_repo.load(experiment_id=experiment_id)
        if not exps:
            raise ValueError(f"Experiment ID {experiment_id} was not found in the database.")
        exp = exps[0]
        if exp.status != "running":
            raise ValueError(
                f"Cannot resume experiment {experiment_id} because its status is '{exp.status}'."
            )

        strat = NoiseStrategyFactory.create(
            noise_model=exp.problem.noise_model,
            noise_std=exp.problem.noise_std or 0.0,
        )

        problem = BBOBProblem(
            problem_id=exp.problem.problem_id,
            dim=exp.problem.dim,
            instance_id=exp.problem.instance_id,
            noise_strategy=strat,
        )
        strategy = PromptStrategy(exp.prompt_strategy)
        budget = exp.budget if exp.budget is not None else 1000
        total_iterations = (
            iterations
            if iterations is not None
            else (exp.max_iterations if exp.max_iterations is not None else 10)
        )

        return cls(
            problem=problem,
            experiment_id=experiment_id,
            initial_iteration=len(exp.iterations),
            prompt_strategy=strategy,
            llm_client=llm_client,
            db_repo=db_repo,
            code_repo=code_repo,
            budget=budget,
            iterations=total_iterations,
        )

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
            self._cleanup_archive_dir()

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

    def _cleanup_archive_dir(self) -> None:
        """Silently removes the temporary evolution_state checkpoint directory upon successful experiment completion."""
        if self._archive_dir.exists():
            import shutil

            shutil.rmtree(self._archive_dir, ignore_errors=True)
