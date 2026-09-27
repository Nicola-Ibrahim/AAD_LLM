from collections.abc import Sequence

from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.models import CampaignTask
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.interfaces.synthesis_repository import SynthesisRepository
from evolution.application.synthesis.models import SessionConfig
from evolution.application.synthesis_config import MatrixCondition, SynthesisConfig
from evolution.domain.entities import ExperimentSummary
from evolution.domain.vos.problem_profile import ProblemProfile
from shared.application.interfaces.problem_factory import ProblemFactory


class CampaignPlanner:
    """Build synthesis tasks from campaign configuration and repository state."""

    def __init__(
        self,
        sqlite_repo: SynthesisRepository,
        config: SynthesisConfig,
        engine: SynthesisEngine,
        model_name: str,
        problem_factory: ProblemFactory,
        auditor: CampaignAuditor,
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.config = config
        self.engine = engine
        self.model_name = model_name
        self.problem_factory = problem_factory
        self.auditor = auditor

    def build_tasks(
        self,
        *,
        recover: bool = False,
        rerun_experiment_ids: Sequence[int] = (),
        rerun_repeats: int = 1,
        resume_experiment_ids: Sequence[int] = (),
    ) -> list[CampaignTask]:
        """Plan one invocation without storing its selection in protocol configuration."""
        if any(
            type(identifier) is not int or identifier <= 0
            for identifier in (*rerun_experiment_ids, *resume_experiment_ids)
        ):
            raise ValueError("Experiment IDs must be positive integers")
        if type(rerun_repeats) is not int or rerun_repeats < 1:
            raise ValueError("rerun_repeats must be a positive integer")
        if resume_experiment_ids and (recover or rerun_experiment_ids):
            raise ValueError("Explicit resume IDs cannot be combined with recovery or fresh reruns")
        if recover or rerun_experiment_ids:
            return self._build_recovery_tasks(rerun_experiment_ids, rerun_repeats)
        if resume_experiment_ids:
            return self._build_targeted_tasks(target_ids=list(dict.fromkeys(resume_experiment_ids)))

        all_db_exps = self.sqlite_repo.load(llm_name=self.model_name)
        db_comp, db_run, db_failed = self.auditor.group_experiments_by_condition(
            experiments=all_db_exps,
        )

        tasks: list[CampaignTask] = []
        for item in self.config.matrix_conditions:
            completed_list = db_comp.get(item, [])
            running_list = db_run.get(item, [])

            if self.config.skip_completed and len(completed_list) >= self.config.runs_per_config:
                continue

            # Step A: Resume interrupted/running runs from DB if AUTO_RESUME enabled
            if self.config.auto_resume:
                for exp in running_list:
                    tasks.append(self._build_task_from_summary(exp, tag="resume"))

            # Step B: Calculate accounted count
            accounted_runs = (
                (len(completed_list) if self.config.skip_completed else 0)
                + (len(running_list) if self.config.auto_resume else 0)
                + (len(db_failed.get(item, [])) if not self.config.retry_failed_synthesis else 0)
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

    def _build_recovery_tasks(
        self, rerun_experiment_ids: Sequence[int], rerun_repeats: int
    ) -> list[CampaignTask]:
        """Combine explicit repeats with active-model recovery, not matrix expansion."""
        requested = set(rerun_experiment_ids)
        selected = self.sqlite_repo.load_by_ids(sorted(requested)) if requested else []
        found = {experiment.id for experiment in selected}
        if missing := requested - found:
            raise ValueError(f"Unknown rerun experiment IDs: {sorted(missing)}")
        # Validate every ID before creating any database records. A campaign
        # for another active model must never dispatch these experiments.
        selected = [experiment for experiment in selected if experiment.llm_name == self.model_name]
        existing = self.sqlite_repo.load(llm_name=self.model_name)
        manual_conditions = dict.fromkeys(
            self.auditor._condition_from_summary(exp) for exp in selected
        )
        eligible = set(self.config.matrix_conditions) | set(manual_conditions)
        completed, running, failed = self.auditor.group_experiments_by_condition(
            experiments=existing,
        )
        tasks: list[CampaignTask] = []
        resumed: dict[MatrixCondition, int] = {}
        if self.config.auto_resume:
            for condition, experiments in running.items():
                if condition in eligible and (
                    condition in manual_conditions or not completed.get(condition)
                ):
                    for experiment in experiments:
                        tasks.append(self._build_task_from_summary(experiment, tag="resume"))
                    resumed[condition] = len(experiments)

        # Any completed valid champion satisfies automatic recovery, regardless
        # of failures in its candidate iterations or other historical sessions.
        requested_repeats = dict.fromkeys(manual_conditions, rerun_repeats)
        if self.config.retry_failed_synthesis and not self.config.only_incomplete:
            for condition, experiments in failed.items():
                if condition not in eligible or completed.get(condition):
                    continue
                requested_repeats.setdefault(condition, 1)

        for condition, repeats in requested_repeats.items():
            # Existing interrupted sessions satisfy the requested repair slots.
            remaining = max(0, repeats - resumed.get(condition, 0))
            count = sum(self.auditor._condition_from_summary(exp) == condition for exp in existing)
            for repeat in range(1, remaining + 1):
                tasks.append(self._build_fresh_task(condition, count + repeat, key_prefix="rerun_"))
        return tasks

    # -------------------------------------------------------------------------

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
        if exp.id is None:
            raise ValueError(f"Cannot build task without a valid database id: {exp}")
        noise_std = exp.problem.noise_std or 0.0
        problem = self.problem_factory.create(
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
        targeted_experiments = self.sqlite_repo.load_by_ids(target_ids)
        found = {experiment.id for experiment in targeted_experiments}
        if missing := set(target_ids) - found:
            raise ValueError(f"Unknown resume experiment IDs: {sorted(missing)}")
        return [
            self._build_task_from_summary(exp, tag="target")
            for exp in targeted_experiments
            if exp.id is not None and exp.llm_name == self.model_name and exp.status == "running"
        ]

    def _build_fresh_task(
        self,
        condition: MatrixCondition,
        run_idx: int,
        key_prefix: str = "",
    ) -> CampaignTask:
        """Registers a new experiment record in the database and returns a fresh work item dictionary."""
        problem = self.problem_factory.create(
            problem_id=condition.problem_id,
            dim=condition.dim,
            noise_std=condition.noise_std,
            noise_model=condition.noise_model,
            instance_id=1,
            seed=42 + run_idx,
        )
        fresh_cfg = self._build_session_config()
        exp_id = self.sqlite_repo.create_experiment(
            problem=ProblemProfile(
                problem_id=problem.problem_id,
                dim=problem.dim,
                noise_std=problem.noise_std,
                noise_model=problem.noise_model,
                instance_id=problem.instance_id,
                true_optimum=problem.true_optimum,
            ),
            mode=condition.mode,
            llm_name=self.model_name,
            prompt_strategy=condition.strategy,
            budget=fresh_cfg.budget,
            max_iterations=fresh_cfg.iterations,
            synthesis_seed=42 + run_idx,
        )
        key = (
            f"{key_prefix}f{condition.problem_id}_{condition.dim}D_{condition.task_mode_label}_{condition.strategy}_run{run_idx}_exp{exp_id}"
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
            synthesis_mode=condition.mode,
        )
