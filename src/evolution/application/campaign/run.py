from collections.abc import Callable

from evolution.application.campaign.models import CampaignResults, CampaignTask
from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.plan import CampaignPlanner
from evolution.application.ports import (
    BaseLogger,
    LanguageModelClient,
    SessionResult,
    SynthesisEngine,
    SynthesisRepository,
    SynthesisConfigReader,
    ProblemFactory,
    TaskDispatcher,
)
from evolution.application.synthesis_config import SynthesisConfig


class SynthesisCampaignCoordinator:
    """Coordinate synthesis campaign planning, audit, and dispatch."""

    def __init__(
        self,
        sqlite_repo: SynthesisRepository,
        config_repo: SynthesisConfigReader,
        logger: BaseLogger,
        engine: SynthesisEngine | None = None,
        llm_client: LanguageModelClient | None = None,
        problem_factory: ProblemFactory | None = None,
        dispatcher: TaskDispatcher[CampaignTask, SessionResult] | None = None,
        worker_fn: Callable[[CampaignTask], SessionResult] | None = None,
    ) -> None:
        self.logger = logger
        self.engine = engine
        self.llm_client = llm_client
        self.dispatcher = dispatcher
        self.worker_fn = worker_fn
        self.config: SynthesisConfig = config_repo.load_config()
        self.auditor = CampaignAuditor(
            sqlite_repo=sqlite_repo,
            config=self.config,
            logger=logger,
            llm_client=llm_client,
        )
        self.planner = CampaignPlanner(
            sqlite_repo=sqlite_repo,
            config=self.config,
            engine=engine,
            llm_client=llm_client,
            problem_factory=problem_factory,
            auditor=self.auditor,
        )

    # -------------------------------------------------------------------------

    def run_campaign(
        self,
        verbose: bool = True,
    ) -> CampaignResults:
        """Build tasks, dispatch them through the configured worker adapter, and aggregate results."""
        if self.engine is None:
            raise ValueError("SynthesisEngine must be configured to run campaigns.")

        self.logger.verbose = verbose
        workers = self.config.num_processes

        tasks = self.planner.build_tasks()
        model_name = self.llm_client.model.name if self.llm_client else "unknown"

        if not tasks:
            self.logger.success(
                f"All requested experiments are already completed with valid champions for '{model_name}'! Nothing to run."
            )
            return CampaignResults()

        self.logger.header(
            title="LLaMEA Evolutionary Algorithm Synthesis",
            subtitle=f"Model: {model_name} | Pending Tasks: {len(tasks)} | Concurrency: {workers} workers",
        )

        if self.dispatcher is None or self.worker_fn is None:
            raise RuntimeError("Campaign dispatcher and worker function must be configured.")
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
