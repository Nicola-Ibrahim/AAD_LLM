"""Generate one optimizer using the configured synthesis engine."""

import math

from pydantic import validate_call

from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.synthesis.result import SynthesisResult
from evolution.application.synthesis.settings import SynthesisSettings
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.domain.vos import ProblemProfile
from shared.application.diagnostics import diagnostic_context
from shared.application.result import Result
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.domain.noise_model import NoiseModelEnum
from shared.domain.problem import BaseProblem


class Synthesis:
    """Generate and improve an optimizer for one problem condition."""

    def __init__(
        self,
        engine: SynthesisEngine,
        sqlite_repo: SynthesisRepository,
        logger: BaseLogger,
        problem_factory: ProblemFactory,
    ) -> None:
        """Initializes the single synthesis use case with required engine and repository.

        Args:
            engine: SynthesisEngine strategy (e.g. LLaMEAEngine).
            sqlite_repo: Repository for persisting experiment telemetry and champion algorithms.
            logger: BaseLogger implementation for synthesis progress.
            problem_factory: Objective construction for a new experiment.
        """
        self.engine = engine
        self.sqlite_repo = sqlite_repo
        self.logger = logger
        self.problem_factory = problem_factory

    @validate_call(config={"strict": True})
    def run(
        self,
        *,
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: NoiseModelEnum | str,
        mode: SynthesisMode | str,
        prompt_strategy: PromptStrategy | str,
        budget: int,
        iterations: int,
        timeout_seconds: float,
        synthesis_seed: int,
        instance_id: int = 1,
        stagnation_threshold: int = 3,
        convergence_threshold: float = 1e-6,
    ) -> Result[SynthesisResult]:
        """Start one new experiment and run its full LLaMEA loop, without a pool.

        Model identity comes from the connected engine. One fixed instance is used
        for all generations. Use the campaign workflow for discovery and recovery.
        """
        try:
            with self.logger.operation("single synthesis"):
                if not 1 <= problem_id <= 24 or dim <= 0:
                    raise ValueError(
                        "Choose a BBOB problem ID from 1 to 24 and a positive dimension"
                    )
                if not math.isfinite(noise_std) or noise_std < 0:
                    raise ValueError("Noise standard deviation must be finite and nonnegative")
                noise_model = NoiseModelEnum(noise_model)
                mode = SynthesisMode(mode)
                strategy = PromptStrategy(prompt_strategy)
                if instance_id < 1:
                    raise ValueError("Instance ID must be a positive integer")
                settings = SynthesisSettings(
                    budget=budget,
                    iterations=iterations,
                    timeout_seconds=timeout_seconds,
                    stagnation_threshold=stagnation_threshold,
                    convergence_threshold=convergence_threshold,
                )
                problem = self.problem_factory.create(
                    problem_id=problem_id,
                    dim=dim,
                    noise_std=noise_std,
                    noise_model=noise_model,
                    instance_id=instance_id,
                    seed=synthesis_seed,
                )
                experiment_id = self.sqlite_repo.create_experiment(
                    problem=ProblemProfile(
                        problem_id=problem.problem_id,
                        dim=problem.dim,
                        noise_std=problem.noise_std,
                        noise_model=problem.noise_model,
                        instance_id=problem.instance_id,
                        true_optimum=problem.true_optimum,
                    ),
                    mode=mode,
                    prompt_strategy=strategy,
                    llm_name=self.engine.model_name,
                    budget=settings.budget,
                    max_iterations=settings.iterations,
                    synthesis_seed=synthesis_seed,
                )
                return Result.success(
                    self.execute(
                        problem=problem,
                        experiment_id=experiment_id,
                        config=settings,
                        prompt_strategy=strategy,
                        synthesis_mode=mode,
                    )
                )
        except Exception as error:
            return Result.failure("single synthesis", error)

    def execute(
        self,
        problem: BaseProblem,
        experiment_id: int,
        config: SynthesisSettings,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
        initial_iteration: int = 0,
        key: str = "",
        verbose: bool = True,
        restart: bool = False,
    ) -> SynthesisResult:
        """Execute a registered experiment, including resume and restart work.

        Args:
            problem: Target optimization problem.
            experiment_id: Unique database experiment identifier.
            config: SynthesisSettings runtime budget and iteration constraints.
            prompt_strategy: Mutation prompt strategy enum.
            synthesis_mode: Explicit vs implicit synthesis mode.
            initial_iteration: Starting iteration index (for resumption).
            key: Descriptive task key for logging.
            verbose: Whether verbose telemetry is enabled.
            restart: Replace this experiment's results and checkpoint before running.

        Returns:
            SynthesisResult: Final outcome of the synthesis run.
        """
        with diagnostic_context(
            experiment_id=experiment_id, task=key, problem_id=problem.problem_id, dim=problem.dim
        ):
            task_label = key or f"exp_{experiment_id}"

            self.logger.verbose = verbose
            self.logger.header(
                title="LLaMEA Synthesis",
                subtitle=f"Single run: {task_label}",
            )

            result = self.engine.run(
                problem=problem,
                experiment_id=experiment_id,
                config=config,
                db_repo=self.sqlite_repo,
                prompt_strategy=prompt_strategy,
                synthesis_mode=synthesis_mode,
                initial_iteration=initial_iteration,
                restart=restart,
            )

            self.logger.summary(
                title="Task Complete",
                stats={
                    "Key": task_label,
                    "Best Error": result.best_error,
                },
            )

            return result
