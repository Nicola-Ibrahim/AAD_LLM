from collections.abc import Callable, Sequence

from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.models import CampaignResults, CampaignTask
from evolution.application.campaign.plan import CampaignPlanner
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.interfaces.synthesis_repository import SynthesisRepository
from evolution.application.interfaces.task_dispatcher import TaskDispatcher
from evolution.application.synthesis.models import SessionResult
from evolution.application.synthesis_config import SynthesisConfig
from shared.application.interfaces.problem_factory import ProblemFactory


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
        *,
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
        workers = self.config.num_processes

        tasks = self.planner.build_tasks(
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
