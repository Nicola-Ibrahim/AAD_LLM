"""Run one synthesis session through the configured engine port.

Coordinates the in-process execution of a single evolutionary algorithm synthesis experiment,
isolated from multiprocessing orchestration.
"""

from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.interfaces.synthesis_repository import SynthesisRepository
from evolution.application.synthesis.models import SessionConfig, SessionResult
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.problem import BaseProblem


class SingleSynthesisUseCase:
    """Hexagonal application use case for executing a single evolutionary algorithm synthesis session.

    Encapsulates the end-to-end execution of a single synthesis run on an objective problem,
    managing telemetry logging and engine execution without any multiprocessing overhead.
    """

    def __init__(
        self,
        engine: SynthesisEngine,
        sqlite_repo: SynthesisRepository,
        logger: BaseLogger,
    ) -> None:
        """Initializes the single synthesis use case with required engine and repository.

        Args:
            engine: SynthesisEngine strategy (e.g. LLaMEAEngine).
            sqlite_repo: Repository for persisting experiment telemetry and champion algorithms.
            logger: BaseLogger implementation for session telemetry.
        """
        self.engine = engine
        self.sqlite_repo = sqlite_repo
        self.logger = logger

    def execute(
        self,
        problem: BaseProblem,
        experiment_id: int,
        config: SessionConfig,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
        initial_iteration: int = 0,
        key: str = "",
        verbose: bool = True,
        restart: bool = False,
    ) -> SessionResult:
        """Executes a single algorithm synthesis session.

        Args:
            problem: Target optimization problem.
            experiment_id: Unique database experiment identifier.
            config: SessionConfig runtime budget and iteration constraints.
            prompt_strategy: Mutation prompt strategy enum.
            synthesis_mode: Explicit vs implicit synthesis mode.
            initial_iteration: Starting iteration index (for resumption).
            key: Descriptive task key for logging.
            verbose: Whether verbose telemetry is enabled.
            restart: Replace this experiment's results and checkpoint before running.

        Returns:
            SessionResult: Final outcome of the synthesis run.
        """
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
