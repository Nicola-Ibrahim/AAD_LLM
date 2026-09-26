from collections.abc import Callable

from evolution.application.campaign.models import CampaignResults, CampaignTask
from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.plan import CampaignPlanner
from evolution.application.interfaces.logger import BaseLogger
from shared.application.interfaces.problem_factory import ProblemFactory
from evolution.application.interfaces.task_dispatcher import TaskDispatcher
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.interfaces.synthesis_repository import SynthesisRepository
from evolution.application.synthesis.models import SessionResult
from evolution.application.synthesis_config import SynthesisConfig


class SynthesisCampaignCoordinator:
    """Coordinate synthesis campaign planning, audit, and dispatch."""

    def __init__(
        self,
        sqlite_repo: SynthesisRepository,
        config: SynthesisConfig,
        logger: BaseLogger,
        engine: SynthesisEngine,
        model_name: str,
        problem_factory: ProblemFactory,
        dispatcher: TaskDispatcher[CampaignTask, SessionResult],
        worker_fn: Callable[[CampaignTask], SessionResult],
    ) -> None:
        self.logger = logger
        self.engine = engine
        self.model_name = model_name
        self.dispatcher = dispatcher
        self.worker_fn = worker_fn
        self.config = config
        self.auditor = CampaignAuditor(
            sqlite_repo=sqlite_repo,
            config=self.config,
            logger=logger,
            model_name=model_name,
        )
        self.planner = CampaignPlanner(
            sqlite_repo=sqlite_repo,
            config=self.config,
            engine=engine,
            model_name=model_name,
            problem_factory=problem_factory,
            auditor=self.auditor,
        )

    # -------------------------------------------------------------------------

    def run_campaign(
        self,
        verbose: bool = True,
    ) -> CampaignResults:
        """Build tasks, dispatch them through the configured worker adapter, and aggregate results."""
        self.logger.verbose = verbose
        workers = self.config.num_processes

        tasks = self.planner.build_tasks()
        model_name = self.model_name

        if not tasks:
            self.logger.success(
                f"All requested experiments are already completed with valid champions for '{model_name}'! Nothing to run."
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
