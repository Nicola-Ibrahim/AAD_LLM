from collections.abc import Callable, Sequence

import pandas as pd
from pydantic import validate_call

from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.models import CampaignResults, CampaignTask
from evolution.application.campaign.plan import CampaignPlanner
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.interfaces.task_dispatcher import TaskDispatcher
from evolution.application.synthesis.models import SessionResult
from evolution.application.synthesis_config import (
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisConfig,
    SynthesisModeConfig,
)
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from shared.domain.interfaces.problem_factory import ProblemFactory


class SynthesisCampaignCoordinator:
    """Coordinate synthesis campaign planning, audit, and dispatch."""

    def __init__(
        self,
        sqlite_repo: SynthesisRepository,
        logger: BaseLogger,
        engine: SynthesisEngine,
        model_name: str,
        problem_factory: ProblemFactory,
        dispatcher: TaskDispatcher[CampaignTask, SessionResult],
        worker_fn: Callable[[CampaignTask], SessionResult],
        worker_count: int,
    ) -> None:
        self.logger = logger
        self.engine = engine
        self.model_name = model_name
        self.dispatcher = dispatcher
        self.worker_fn = worker_fn
        self.sqlite_repo = sqlite_repo
        self.problem_factory = problem_factory
        self.worker_count = worker_count

    def _build_planner(self, config: SynthesisConfig) -> CampaignPlanner:
        auditor = CampaignAuditor(self.sqlite_repo, config, self.logger, self.model_name)
        return CampaignPlanner(
            self.sqlite_repo, config, self.engine, self.model_name, self.problem_factory, auditor
        )

    @validate_call(config={"strict": True})
    def audit_matrix(
        self,
        *,
        problem_targets: list[ProblemTarget],
        noise_conditions: list[NoiseConditionConfig],
        synthesis_modes: list[SynthesisModeConfig],
        iterations: int,
        budget: int,
        timeout_seconds: float,
        runs_per_config: int,
        auto_resume: bool,
        skip_completed: bool,
        retry_failed_synthesis: bool,
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        """Inspect the same explicit study parameters without dispatching work."""
        config = SynthesisConfig(
            problem_targets=problem_targets,
            noise_conditions=noise_conditions,
            synthesis_modes=synthesis_modes,
            iterations=iterations,
            budget=budget,
            timeout_seconds=timeout_seconds,
            runs_per_config=runs_per_config,
            auto_resume=auto_resume,
            skip_completed=skip_completed,
            retry_failed_synthesis=retry_failed_synthesis,
            num_processes=self.worker_count,
        )
        return self._build_planner(config).auditor.audit_matrix()

    # -------------------------------------------------------------------------

    @validate_call(config={"strict": True})
    def run_campaign(
        self,
        *,
        problem_targets: list[ProblemTarget],
        noise_conditions: list[NoiseConditionConfig],
        synthesis_modes: list[SynthesisModeConfig],
        iterations: int,
        budget: int,
        timeout_seconds: float,
        runs_per_config: int,
        auto_resume: bool,
        skip_completed: bool,
        retry_failed_synthesis: bool,
        verbose: bool = True,
        recover: bool = False,
        rerun_experiment_ids: Sequence[int] = (),
        resume_experiment_ids: Sequence[int] = (),
    ) -> CampaignResults:
        """Run an invocation-scoped request using the unchanged protocol configuration.

        No selections means full-matrix scheduling. ``recover`` discovers pending
        and failed synthesis; manual rerun IDs replace those exact records. Explicit resume
        IDs select running sessions only and cannot be combined with recovery.
        """
        self.logger.verbose = verbose
        config = SynthesisConfig(
            problem_targets=problem_targets,
            noise_conditions=noise_conditions,
            synthesis_modes=synthesis_modes,
            iterations=iterations,
            budget=budget,
            timeout_seconds=timeout_seconds,
            runs_per_config=runs_per_config,
            auto_resume=auto_resume,
            skip_completed=skip_completed,
            retry_failed_synthesis=retry_failed_synthesis,
            num_processes=self.worker_count,
        )
        workers = self.worker_count

        tasks = self._build_planner(config).build_tasks(
            recover=recover,
            rerun_experiment_ids=rerun_experiment_ids,
            resume_experiment_ids=resume_experiment_ids,
        )
        model_name = self.model_name

        if not tasks:
            self.logger.success(
                f"No eligible tasks for this request and active model '{model_name}'. Nothing to run."
            )
            return CampaignResults()

        self.logger.header(
            title="LLaMEA Evolutionary Algorithm Synthesis",
            subtitle=f"Model: {model_name} | Pending Tasks: {len(tasks)} | Concurrency: {workers} workers",
        )

        raw_results = self.dispatcher.run(
            fn=self.worker_fn,
            items=tasks,
            key_fn=lambda item: item["key"],
        )
        campaign_results = CampaignResults(results=raw_results)

        self.logger.summary(
            title="Synthesis Campaign Complete",
            stats={
                "Model Target": model_name,
                "Total Tasks Executed": campaign_results.total_tasks,
                "Valid Champions Found": campaign_results.successful_tasks,
                "Failed / Incomplete": campaign_results.failed_tasks,
            },
        )
        return campaign_results

    # -------------------------------------------------------------------------
