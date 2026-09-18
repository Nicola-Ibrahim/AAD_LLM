"""LLaMEA Evolutionary Synthesis Engine & Session (Infrastructure Adapter).

Implements the evolutionary synthesis engine using the 3rd-party LLaMEA optimization library.
Manages the evolutionary synthesis loop, prompt injection, warm-start checkpointing,
sandboxed evaluation, and persistence of iteration telemetry and champion algorithms.
"""

import math
import shutil
import warnings
from types import SimpleNamespace

from llamea import LLaMEA

from shared.config import DATA_DIR
from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.interfaces import BaseProblem
from evolution.domain.vos import ProblemProfile
from evolution.application.interfaces import (
    BaseLogger,
    SessionConfig,
    SessionResult,
    SynthesisEngine,
)
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from evolution.infra.engines.llamea.prompts import (
    SynthesisPrompts,
    build_synthesis_prompts,
)
from evolution.infra.storage.base import SynthesisRepository
from evolution.infra.storage.code.repository import CodeRepository
from evolution.domain.services.algorithm_evaluator import AlgorithmEvaluator
from evolution.infra.engines.llamea.evaluator import Evaluator
from shared.execution import AlgorithmExecutor

# Suppress joblib warning when LLaMEA passes timeout to SequentialBackend
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r".*SequentialBackend.*does not support timeout.*",
)


class LLaMEASession:
    """Manages the lifecycle and execution of a single LLaMEA synthesis session on an optimization problem.

    Orchestrates the evolutionary loop:
        1. Pre-warm session from existing snapshots (if available)
        2. Run LLaMEA synthesis loop
        3. Persist final ExperimentSummary
               │
               ▼
        Print Summary Report & Return SessionResult
    """

    def __init__(
        self,
        problem: BaseProblem,
        experiment_id: int,
        prompt_strategy: PromptStrategy,
        llm_client: LLMClient,
        db_repo: SynthesisRepository,
        code_repo: CodeRepository,
        config: SessionConfig,
        initial_iteration: int = 0,
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
    ):
        """Initializes the synthesis session with pre-resolved domain objects and execution configuration."""
        self._problem = problem
        self._experiment_id = experiment_id
        self._prompt_strategy = PromptStrategy(prompt_strategy)
        self._llm_client = llm_client
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._config = config
        self._initial_iteration = initial_iteration
        self._logger: BaseLogger = SynthesisLogger()
        self._synthesis_mode = SynthesisMode(synthesis_mode)

        problem_profile = ProblemProfile(
            problem_id=self._problem.problem_id,
            dim=self._problem.dim,
            noise_std=self._problem.noise_std,
            noise_model=self._problem.noise_model,
            instance_id=self._problem.instance_id,
            true_optimum=self._problem.true_optimum,
        )
        self._experiment = ExperimentSummary.new(
            experiment_id=self._experiment_id,
            problem=problem_profile,
            mode=self._synthesis_mode,
            llm_name=self._llm_client.model.name,
            prompt_strategy=self._prompt_strategy,
            budget=self._config.budget,
            max_iterations=self._config.iterations,
        )

        self._archive_dir = (
            DATA_DIR
            / "evolution_state"
            / f"{self._problem.dim}D"
            / f"std_{self._problem.noise_std}"
            / f"f{self._problem.problem_id}"
            / f"experiment_{self._experiment_id}"
        )
        self._archive_dir.mkdir(parents=True, exist_ok=True)

    @property
    def logger(self) -> BaseLogger:
        """Expose the session synthesis logger."""
        return self._logger

    @logger.setter
    def logger(self, value: BaseLogger) -> None:
        self._logger = value

    @property
    def _experiment_name(self) -> str:
        """Derived name string for the experiment context."""
        return f"bbob_{self._problem.problem_id}_dim{self._problem.dim}_{self._problem.mode}"

    def _print_start_banner(self) -> None:
        """Prints the initialization banner for the evolution run."""
        self._logger.task_start(
            index=1,
            total=1,
            model_name=self._llm_client.model.name,
            dim=self._problem.dim,
            noise_std=self._problem.noise_std,
            problem_id=self._problem.problem_id,
            strategy=self._prompt_strategy,
            experiment_id=self._experiment_id,
            problem_name=getattr(self._problem, "name", ""),
        )

    def _process_session_result(
        self, synthesis_engine: LLaMEA, evaluator: Evaluator
    ) -> SessionResult:
        """Extracts best candidate metrics, prints summary report, and builds SessionResult."""
        best_so_far = synthesis_engine.best_so_far
        fitness_score = best_so_far.fitness  # This is -final_error (LLaMEA convention)

        if (
            fitness_score is not None
            and math.isfinite(fitness_score)
            and not AlgorithmEvaluator.is_failure(fitness_score)
        ):
            best_error = -fitness_score
            raw_fitness = self._db_repo.get_best_raw_fitness(self._experiment_id)
        else:
            best_error = None
            raw_fitness = None

        algorithm_name = best_so_far.name or "None"
        self._print_report(algorithm_name, raw_fitness, best_error)

        return SessionResult(
            problem_id=self._problem.problem_id,
            dim=self._problem.dim,
            mode=self._synthesis_mode,
            noise_std=self._problem.noise_std,
            best_error=best_error,
            experiment_id=self._experiment_id,
            run_history=synthesis_engine.run_history,
            experiment_name=self._experiment_name,
            llm_name=self._llm_client.model.name,
            best_solution=synthesis_engine.best_so_far,
            error_msg="",
            problem_profile=evaluator.problem_profile,
        )

    def _execute_loop(self) -> tuple[LLaMEA, Evaluator]:
        """Executes the LLaMEA evolutionary loop with lifecycle status tracking."""
        try:
            prompts = build_synthesis_prompts(
                problem=self._problem,
                mode=self._synthesis_mode,
                strategy=self._prompt_strategy,
                budget_hint=self._config.budget,
            )
            evaluator = self._setup_evaluator()
            synthesis_engine = self._create_synthesis_engine(evaluator, prompts)
            synthesis_engine.run()
        except Exception as e:
            self._experiment.fail()
            self._db_repo.mark_failed(self._experiment_id, str(e))
            raise
        else:
            self._experiment.complete()
            self._db_repo.save_experiment_summary(self._experiment)
            return synthesis_engine, evaluator

    def run(self) -> SessionResult:
        """Runs the complete evolution loop for the problem."""
        self._print_start_banner()
        synthesis_engine, evaluator = self._execute_loop()

        self._cleanup_archive_dir()
        return self._process_session_result(synthesis_engine, evaluator)

    def _create_synthesis_engine(
        self, evaluator: Evaluator, prompts: SynthesisPrompts
    ) -> LLaMEA:
        """Creates a new LLaMEA synthesis engine or resumes from a warm-start session state if it exists."""
        state_file = self._archive_dir / "llamea_config.pkl"

        if state_file.exists():
            try:
                synthesis_engine = LLaMEA.warm_start(str(self._archive_dir))
                if synthesis_engine is not None:
                    synthesis_engine.f = evaluator
                    synthesis_engine.llm = self._llm_client
                    self._logger.resuming(
                        self._experiment_id,
                        synthesis_engine.generation,
                        self._config.iterations,
                    )
                    synthesis_engine.logger = SimpleNamespace(dirname=str(self._archive_dir))
                    return synthesis_engine
            except Exception as e:
                self._logger.warning(f"Warm start failed, starting fresh: {e}")

        synthesis_engine = LLaMEA(
            f=evaluator,
            llm=self._llm_client,
            n_parents=1,
            n_offspring=1,
            budget=self._config.iterations,
            task_prompt=prompts.task,
            example_prompt=prompts.example,
            output_format_prompt=prompts.format,
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
        algorithm_evaluator = AlgorithmEvaluator(
            problem=self._problem,
            budget=self._config.budget,
            timeout_seconds=self._config.timeout_seconds,
            stagnation_threshold=self._config.stagnation_threshold,
            convergence_threshold=self._config.convergence_threshold,
            executor=AlgorithmExecutor(timeout_seconds=self._config.timeout_seconds),
        )
        evaluator = Evaluator(
            problem=self._problem,
            db_repo=self._db_repo,
            code_repo=self._code_repo,
            experiment_id=self._experiment_id,
            config=self._config,
            algorithm_evaluator=algorithm_evaluator,
            initial_iteration=self._initial_iteration,
        )
        evaluator.experiment = self._experiment
        evaluator.logger = self._logger
        return evaluator

    def _print_report(
        self,
        algorithm_name: str,
        raw_fitness: float | None,
        final_error: float | None,
    ) -> None:
        """Prints a structured console report highlighting objective value and error metrics of the best candidate."""
        self._logger.task_complete(
            exp_id=self._experiment_id,
            best_algo_name=algorithm_name,
            best_error=final_error,
            raw_obj=raw_fitness,
            true_opt=self._problem.true_optimum,
        )

    def _cleanup_archive_dir(self) -> None:
        """Silently removes the temporary evolution_state checkpoint directory upon successful experiment completion."""
        if self._archive_dir.exists():
            shutil.rmtree(self._archive_dir, ignore_errors=True)


class LLaMEAEngine(SynthesisEngine):
    """Infrastructure synthesis engine using LLaMEASession."""

    def __init__(
        self,
        llm_client: LLMClient,
        code_repo: CodeRepository | None = None,
        config: SessionConfig | None = None,
        db_repo: SynthesisRepository | None = None,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
    ) -> None:
        super().__init__(
            config=config,
            db_repo=db_repo,
            prompt_strategy=prompt_strategy,
            synthesis_mode=synthesis_mode,
        )
        self.llm_client = llm_client
        self.code_repo = code_repo or CodeRepository()

    def run(
        self,
        problem: BaseProblem,
        experiment_id: int,
        config: SessionConfig | None = None,
        db_repo: SynthesisRepository | None = None,
        prompt_strategy: PromptStrategy | None = None,
        synthesis_mode: SynthesisMode | None = None,
        initial_iteration: int = 0,
    ) -> SessionResult:
        """Executes a single algorithm synthesis run using LLaMEASession."""
        resolved_config = config or self.config
        if resolved_config is None:
            raise ValueError("SessionConfig must be provided either in __init__ or in run().")

        resolved_db_repo = db_repo or self.db_repo
        if resolved_db_repo is None:
            raise ValueError("SynthesisRepository must be provided either in __init__ or in run().")

        resolved_strategy = prompt_strategy if prompt_strategy is not None else self.prompt_strategy
        resolved_mode = synthesis_mode if synthesis_mode is not None else self.synthesis_mode

        session = LLaMEASession(
            problem=problem,
            experiment_id=experiment_id,
            prompt_strategy=resolved_strategy,
            llm_client=self.llm_client,
            db_repo=resolved_db_repo,
            code_repo=self.code_repo,
            config=resolved_config,
            initial_iteration=initial_iteration,
            synthesis_mode=resolved_mode,
        )
        return session.run()

