from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.models import CampaignTask
from evolution.application.ports import (
    LanguageModelClient,
    ProblemFactory,
    SynthesisEngine,
    SynthesisRepository,
)
from evolution.application.ports.engine import SessionConfig
from evolution.application.synthesis_config import MatrixCondition, SynthesisConfig
from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import NoiseModelEnum
from evolution.domain.interfaces import BaseProblem


class CampaignPlanner:
    """Build synthesis tasks from campaign configuration and repository state."""

    def __init__(
        self,
        sqlite_repo: SynthesisRepository,
        config: SynthesisConfig,
        engine: SynthesisEngine | None,
        llm_client: LanguageModelClient | None,
        problem_factory: ProblemFactory | None,
        auditor: CampaignAuditor,
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.config = config
        self.engine = engine
        self.llm_client = llm_client
        self.problem_factory = problem_factory
        self.auditor = auditor

    def build_tasks(self) -> list[CampaignTask]:
        """Constructs the list of work item parameter dictionaries to execute based on configuration."""
        if self.engine is None:
            raise ValueError("SynthesisEngine must be configured to build executable tasks.")

        # Fast path: targeted experiment IDs
        if self.config.target_experiment_ids:
            return self._build_targeted_tasks(target_ids=self.config.target_experiment_ids)

        model_name = self.llm_client.model.name if self.llm_client else "unknown"
        all_db_exps = self.sqlite_repo.load(llm_name=model_name)
        db_comp, db_run, _ = self.auditor.group_experiments_by_condition(
            experiments=all_db_exps,
            retry_failed_synthesis=self.config.retry_failed_synthesis,
        )

        tasks: list[CampaignTask] = []
        for item in self.config.matrix_conditions:
            completed_list = db_comp.get(item, [])
            running_list = db_run.get(item, [])

            # Step A: Resume interrupted/running runs from DB if AUTO_RESUME enabled
            if self.config.auto_resume:
                for exp in running_list:
                    tasks.append(self._build_resume_task(exp=exp))

            # Step B: Calculate accounted count
            accounted_runs = (len(completed_list) if self.config.skip_completed else 0) + (
                len(running_list) if self.config.auto_resume else 0
            )

            # Step C: Schedule remaining fresh / retry runs
            if not self.config.only_incomplete:
                remaining_needed = max(0, self.config.runs_per_config - accounted_runs)
                for run_idx in range(accounted_runs + 1, accounted_runs + remaining_needed + 1):
                    tasks.append(
                        self._build_fresh_task(
                            condition=item,
                            run_idx=run_idx,
                        )
                    )
        return tasks

    # -------------------------------------------------------------------------

    def _create_problem(
        self,
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: NoiseModelEnum = NoiseModelEnum.HETEROSCEDASTIC,
        instance_id: int = 1,
        seed: int = 42,
    ) -> BaseProblem:
        """Create a problem through the configured application port."""
        if self.problem_factory is None:
            raise RuntimeError("Problem factory must be configured.")
        return self.problem_factory.create(
            problem_id=problem_id,
            dim=dim,
            noise_std=noise_std,
            noise_model=noise_model,
            instance_id=instance_id,
            seed=seed,
        )

    def _build_session_config(self, max_iterations: int | None = None) -> SessionConfig:
        """Constructs a SessionConfig from campaign settings, optionally overriding iterations."""
        cfg = SessionConfig(**self.config.to_session_config_dict())
        if max_iterations:
            cfg = cfg.model_copy(update={"iterations": max_iterations})
        return cfg

    def _build_task_from_summary(
        self,
        exp: ExperimentSummary,
        tag: str = "resume",
    ) -> CampaignTask:
        """Constructs a work item for an existing experiment in the database."""
        assert self.engine is not None
        if exp.id is None:
            raise ValueError(f"Cannot build task without a valid database id: {exp}")
        noise_std = exp.problem.noise_std or 0.0
        problem = self._create_problem(
            problem_id=exp.problem.problem_id,
            dim=exp.problem.dim,
            noise_std=noise_std,
            noise_model=exp.problem.noise_model,
            instance_id=exp.problem.instance_id or 1,
            seed=42 + (exp.id or 0),
        )
        initial_iter = len(exp.iterations) if exp.iterations else 0
        cfg = self._build_session_config(exp.max_iterations)
        mode_label = f"{exp.mode}_std_{noise_std}"
        key = f"f{exp.problem.problem_id}_{exp.problem.dim}D_{mode_label}_{exp.prompt_strategy}_{tag}_exp{exp.id}"
        return CampaignTask(
            key=key,
            problem=problem,
            experiment_id=exp.id,
            config=cfg,
            engine=self.engine,
            initial_iteration=initial_iter,
            prompt_strategy=exp.prompt_strategy,
            synthesis_mode=exp.mode,
        )

    def _build_targeted_tasks(
        self,
        target_ids: list[int],
    ) -> list[CampaignTask]:
        assert self.engine is not None
        targeted_experiments = self.sqlite_repo.load_by_ids(target_ids)
        return [
            self._build_task_from_summary(exp, tag="target")
            for exp in targeted_experiments
            if exp.id is not None
        ]

    def _build_resume_task(
        self,
        exp: ExperimentSummary,
    ) -> CampaignTask:
        """Constructs a resume work item dictionary from an active running experiment in the database."""
        return self._build_task_from_summary(exp, tag="resume")

    def _build_fresh_task(
        self,
        condition: MatrixCondition,
        run_idx: int,
        key_prefix: str = "",
    ) -> CampaignTask:
        """Registers a new experiment record in the database and returns a fresh work item dictionary."""
        assert self.engine is not None
        if self.llm_client is None:
            raise ValueError("LLMClient must be configured to register fresh experiments in DB.")

        problem = self._create_problem(
            problem_id=condition.problem_id,
            dim=condition.dim,
            noise_std=condition.noise_std,
            noise_model=condition.noise_model,
            instance_id=1,
            seed=42 + run_idx,
        )
        fresh_cfg = self._build_session_config()
        exp_id = self.sqlite_repo.create_experiment(
            problem=problem.profile,
            mode=condition.synthesis_mode,
            llm_name=self.llm_client.model.name,
            prompt_strategy=condition.strategy,
            budget=fresh_cfg.budget,
            max_iterations=fresh_cfg.iterations,
            synthesis_seed=42 + run_idx,
        )
        key = (
            f"{key_prefix}f{condition.problem_id}_{condition.dim}D_{condition.task_mode_label}_{condition.strategy}"
            if key_prefix
            else f"f{condition.problem_id}_{condition.dim}D_{condition.task_mode_label}_{condition.strategy}_run{run_idx}"
        )
        return CampaignTask(
            key=key,
            problem=problem,
            experiment_id=exp_id,
            config=fresh_cfg,
            engine=self.engine,
            initial_iteration=0,
            prompt_strategy=condition.strategy,
            synthesis_mode=condition.synthesis_mode,
        )
