"""Synthesis Campaign Application Use Case (Hexagonal Architecture).

Coordinates synthesis configuration reading, database status reconciliation,
matrix auditing, task planning, and parallel multi-process dispatching.
"""

from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from evolution.application.interfaces import (
    BaseLogger,
    SessionConfig,
    SessionResult,
    SynthesisEngine,
)
from evolution.application.single_synthesis_usecase import SingleSynthesisUseCase
from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import BBOBFunction, NoiseModelEnum
from evolution.domain.services.noise_strategy import NoiseStrategyFactory
from evolution.infra.concurrency.runner import ProcessPoolRunner
from evolution.infra.llm.client import LLMClient
from evolution.infra.problems.bbob import BBOBProblem
from evolution.infra.storage.synthesis import SQLiteSynthesisRepository
from evolution.infra.storage.synthesis_config import (
    MatrixCondition,
    SynthesisConfig,
    SynthesisConfigRepository,
)


class CampaignResults(BaseModel):
    """Results from an evolutionary algorithm synthesis campaign."""

    results: dict[str, SessionResult] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def total_tasks(self) -> int:
        return len(self.results)

    @property
    def successful_tasks(self) -> int:
        return sum(
            1
            for r in self.results.values()
            if r.best_error is not None and np.isfinite(r.best_error)
        )

    @property
    def failed_tasks(self) -> int:
        return self.total_tasks - self.successful_tasks


class CampaignTask(dict[str, Any]):
    """Lightweight dictionary representation of a planned campaign task work item.

    Supports both dictionary key indexing (task["key"]) and attribute access (task.key).
    """

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"CampaignTask has no attribute {name!r}")


class SynthesisCampaignUseCase:
    """Hexagonal application use case managing algorithm synthesis campaigns and multiprocessing.

    Workflow Architecture:
    ┌────────────────────────────────────────────────────────┐
    │              SynthesisConfigRepository                 │
    │         (YAML Configuration -> SynthesisConfig)        │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │               SynthesisCampaignUseCase                 │
    │                                                        │
    │  1. audit_matrix()                                     │
    │     Reconcile Config Conditions vs SQLite DB Records   │
    │     ├── Completed (Valid Champions)                    │
    │     ├── Failed Synthesis (Candidates for Retry)        │
    │     └── Running / Incomplete (Candidates for Resume)   │
    │                                                        │
    │  2. build_tasks()                                      │
    │     Generate Concrete Work Item Parameter Dictionaries │
    │     ├── Targeted Tasks  ──> Target Experiment IDs      │
    │     ├── Resume Tasks    ──> Interrupted DB Experiments │
    │     └── Fresh Tasks     ──> Upfront DB Record Created  │
    │                                                        │
    │  3. run_campaign()                                     │
    │     Direct ProcessPoolRunner Concurrency               │
    │     Worker Subprocess ──> SingleSynthesisUseCase      │
    │                                                        │
    │  4. Results Aggregation & Logging                      │
    │     Harvest SessionResult, summarize champion metrics  │
    └────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisRepository,
        config_repo: SynthesisConfigRepository,
        logger: BaseLogger,
        engine: SynthesisEngine | None = None,
        llm_client: LLMClient | None = None,
    ):
        self.sqlite_repo = sqlite_repo
        self.config_repo = config_repo
        self.logger = logger
        self.engine = engine
        self.llm_client = llm_client
        self.config: SynthesisConfig = self.config_repo.load_config()

    # -------------------------------------------------------------------------
    # Matrix Auditing & Grouping
    # -------------------------------------------------------------------------

    @staticmethod
    def _condition_from_summary(exp: ExperimentSummary) -> MatrixCondition:
        """Constructs a MatrixCondition from an ExperimentSummary entity."""
        return MatrixCondition(
            problem_id=exp.problem.problem_id,
            dim=exp.problem.dim,
            mode=exp.mode,
            noise_std=round(exp.problem.noise_std, 4) if exp.problem.noise_std else 0.0,
            noise_model=exp.problem.noise_model,
            strategy=exp.prompt_strategy,
        )

    def group_experiments_by_condition(
        self,
        experiments: list[ExperimentSummary],
        retry_failed_synthesis: bool = False,
    ) -> tuple[
        dict[MatrixCondition, list[ExperimentSummary]],
        dict[MatrixCondition, list[ExperimentSummary]],
        dict[MatrixCondition, list[ExperimentSummary]],
    ]:
        """Groups experiments by their matrix condition into completed, running, and failed categories."""
        completed: defaultdict[MatrixCondition, list[ExperimentSummary]] = defaultdict(list)
        running: defaultdict[MatrixCondition, list[ExperimentSummary]] = defaultdict(list)
        failed: defaultdict[MatrixCondition, list[ExperimentSummary]] = defaultdict(list)

        for exp in experiments:
            cond = self._condition_from_summary(exp)
            has_valid_champion = (
                exp.best_final_error is not None and np.isfinite(exp.best_final_error)
            )
            if exp.status == "completed":
                if has_valid_champion or not retry_failed_synthesis:
                    completed[cond].append(exp)
                else:
                    failed[cond].append(exp)
            elif exp.status == "failed":
                if retry_failed_synthesis:
                    failed[cond].append(exp)
                else:
                    completed[cond].append(exp)
            elif exp.status == "running":
                running[cond].append(exp)

        return dict(completed), dict(running), dict(failed)

    def audit_matrix(self, model_name: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Audits database records against configured matrix conditions.

        Reconciles completed experiments with valid champions against planned matrix targets,
        producing a comprehensive MultiIndex audit DataFrame and coverage summary statistics.
        """
        llm_name = model_name or (self.llm_client.model.name if self.llm_client else "unknown")
        all_db_exps = self.sqlite_repo.load(llm_name=llm_name)

        db_completed, db_running, db_failed = self.group_experiments_by_condition(
            experiments=all_db_exps,
            retry_failed_synthesis=self.config.retry_failed_synthesis,
        )

        matrix_rows = []
        total_done = 0
        total_retry = 0

        for item in self.config.matrix_conditions:
            comp_list = db_completed.get(item, [])
            run_list = db_running.get(item, [])
            fail_list = db_failed.get(item, [])

            n_comp = len(comp_list)
            n_running = len(run_list)
            n_fail = len(fail_list)

            if n_comp >= self.config.runs_per_config:
                status_label = "✅ Complete"
                total_done += 1
            elif n_running > 0 and self.config.auto_resume:
                status_label = f"🔄 Incomplete ({n_running} to resume)"
            elif n_fail > 0 and self.config.retry_failed_synthesis:
                status_label = f"⚠️ Retry ({n_fail} failed)"
                total_retry += 1
            else:
                status_label = "⏳ Pending"

            matrix_rows.append({
                "Problem": f"f{item.problem_id} ({BBOBFunction.get_short_name(item.problem_id)})",
                "Dimension": f"{item.dim}D",
                "Environment": item.env_label,
                "Strategy": item.strategy.capitalize(),
                "Target Runs": self.config.runs_per_config,
                "Completed": n_comp,
                "Status": status_label,
            })

        if matrix_rows:
            df_matrix = pd.DataFrame(matrix_rows).set_index(
                ["Problem", "Dimension", "Environment", "Strategy"]
            )
        else:
            df_matrix = pd.DataFrame(
                columns=["Problem", "Dimension", "Environment", "Strategy", "Target Runs", "Completed", "Status"]
            ).set_index(["Problem", "Dimension", "Environment", "Strategy"])

        total_cfg = len(df_matrix)
        progress_pct = (total_done / max(1, total_cfg)) * 100

        summary: dict[str, Any] = {
            "model_name": llm_name,
            "total_conditions": total_cfg,
            "completed_conditions": total_done,
            "retry_conditions": total_retry,
            "progress_pct": progress_pct,
            "retry_failed_synthesis": self.config.retry_failed_synthesis,
            "auto_resume": self.config.auto_resume,
            "skip_completed": self.config.skip_completed,
            "problem_targets": self.config.problem_targets,
            "problem_ids": self.config.problem_ids,
            "dimensions": self.config.dimensions,
            "noise_stds": self.config.noise_stds,
            "synthesis_modes": self.config.synthesis_mode_names,
            "prompt_strategies": [s.value if hasattr(s, "value") else str(s) for s in self.config.prompt_strategies],
            "target_exp_ids": self.config.target_experiment_ids,
        }

        self.logger.audit_summary(
            model_name=llm_name,
            total_conditions=total_cfg,
            completed=total_done,
            pending=total_cfg - total_done,
            retry=total_retry,
            progress_pct=progress_pct,
        )
        return df_matrix, summary


    # -------------------------------------------------------------------------
    # Task Building & Planning
    # -------------------------------------------------------------------------

    def build_tasks(self) -> list[CampaignTask]:
        """Constructs the list of work item parameter dictionaries to execute based on configuration."""
        if self.engine is None:
            raise ValueError("SynthesisEngine must be configured to build executable tasks.")

        # Fast path: targeted experiment IDs
        if self.config.target_experiment_ids:
            return self._build_targeted_tasks(target_ids=self.config.target_experiment_ids)

        model_name = self.llm_client.model.name if self.llm_client else "unknown"
        all_db_exps = self.sqlite_repo.load(llm_name=model_name)
        db_comp, db_run, _ = self.group_experiments_by_condition(
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
    # Execution
    # -------------------------------------------------------------------------

    @staticmethod
    def run_worker(item: dict[str, Any]) -> SessionResult:
        """Worker entrypoint executed in an isolated worker process during multiprocessing."""
        from shared.database.engine import initialize_sqlite_storage

        repo = initialize_sqlite_storage()
        usecase = SingleSynthesisUseCase(
            engine=item["engine"],
            sqlite_repo=repo,
        )
        return usecase.execute(
            problem=item["problem"],
            experiment_id=item["experiment_id"],
            config=item["config"],
            prompt_strategy=item["prompt_strategy"],
            synthesis_mode=item["synthesis_mode"],
            initial_iteration=item["initial_iteration"],
            key=item["key"],
            verbose=False,
        )

    def run_campaign(
        self,
        verbose: bool = True,
    ) -> CampaignResults:
        """Builds tasks and executes the evolutionary synthesis campaign in parallel using ProcessPoolRunner."""
        if self.engine is None:
            raise ValueError("SynthesisEngine must be configured to run campaigns.")

        self.logger.verbose = verbose
        workers = self.config.num_processes

        tasks = self.build_tasks()
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

        runner = ProcessPoolRunner(max_workers=workers)
        raw_results = runner.run(
            fn=self.run_worker,
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
    # Private Task Builder Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _create_problem(
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: NoiseModelEnum = NoiseModelEnum.HETEROSCEDASTIC,
        instance_id: int = 1,
        seed: int = 42,
    ) -> BBOBProblem:
        """Helper to create a configured BBOBProblem with appropriate noise strategy."""
        noise_strat = NoiseStrategyFactory.create(
            noise_model=noise_model,
            noise_std=noise_std,
        )
        return BBOBProblem(
            problem_id=problem_id,
            dim=dim,
            instance_id=instance_id,
            noise_strategy=noise_strat,
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
