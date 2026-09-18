"""LLaMEA Algorithm Synthesis Application Service (Campaign & Execution Facade).

Coordinates synthesis configuration reading, database status reconciliation,
task construction, upfront synthesis session persistence, and parallel multi-process dispatching.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import NoiseModelEnum, PromptStrategy, SynthesisMode
from evolution.domain.interfaces import BaseProblem
from evolution.domain.services.noise_strategy import NoiseStrategyFactory
from evolution.domain.vos import ProblemProfile
from evolution.infra.llm.client import LLMClient
from evolution.infra.problems.bbob import BBOBProblem
from evolution.infra.storage.synthesis_config import (
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisConfig,
    SynthesisConfigRepository,
    SynthesisModeConfig,
)
from evolution.infra.storage.synthesis import SQLiteSynthesisRepository
from evolution.application.audit_service import SynthesisAuditService
from evolution.application.interfaces import BaseLogger


class SessionConfig(BaseModel):
    """Runtime configuration for an evolutionary synthesis session.

    Serves as the strongly-typed parameter object for runtime budgets, timeouts,
    iterations, stagnation thresholds, and convergence criteria.
    """

    budget: int = Field(
        default=1_000_000,
        ge=1,
        description="Maximum objective function evaluations allowed per algorithm candidate run.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Maximum wall-clock execution time allowed per candidate algorithm in seconds.",
    )
    iterations: int = Field(
        default=10,
        ge=1,
        description="Total number of evolutionary iterations / generations to execute.",
    )
    stagnation_threshold: int = Field(
        default=3,
        ge=1,
        description="Consecutive unimproved iterations before triggering mutation escalation or reset.",
    )
    convergence_threshold: float = Field(
        default=1e-6,
        ge=0.0,
        description="Final error threshold below which optimization is considered successfully converged.",
    )

    model_config = ConfigDict(frozen=True)


@dataclass(slots=True)
class SessionResult:
    """Contract returned per-problem run by an evolutionary synthesis engine."""

    problem_id: int
    dim: int
    mode: SynthesisMode
    noise_std: float
    experiment_id: int
    best_error: float | None = None
    run_history: list[Any] = field(default_factory=list)
    experiment_name: str = ""
    llm_name: str = ""
    error_msg: str = ""
    best_solution: Any = None
    problem_profile: Any = None


@dataclass(slots=True)
class EvolutionTask:
    """A single picklable specification of an evolution work unit.

    Encapsulates all necessary parameters and dependencies to execute
    a single synthesis run inside a worker process.
    """

    key: str
    problem: BaseProblem
    llm_client: LLMClient
    experiment_id: int
    config: SessionConfig
    initial_iteration: int = 0
    prompt_strategy: PromptStrategy = PromptStrategy.BASELINE
    synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT
    db_path: Path | None = None


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


class SynthesisService:
    """Application use case service managing algorithm synthesis campaigns.

    Workflow Architecture:
    ┌────────────────────────────────────────────────────────┐
    │              SynthesisConfigRepository                 │
    │         (YAML Configuration -> SynthesisConfig)        │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │                    SynthesisService                    │
    │                                                        │
    │  1. audit_matrix()                                     │
    │     Reconcile Config Conditions vs SQLite DB Records   │
    │     ├── Completed (Valid Champions)                    │
    │     ├── Failed Synthesis (Candidates for Retry)        │
    │     └── Running / Incomplete (Candidates for Resume)   │
    │                                                        │
    │  2. build_tasks()                                      │
    │     Generate Concrete Task Dispatch Matrix             │
    │     ├── Targeted Tasks  ──> Target Experiment IDs      │
    │     ├── Resume Tasks    ──> Interrupted DB Experiments │
    │     └── Fresh Tasks     ──> Upfront DB Record Created  │
    │                                                        │
    │  3. run_campaign() / run_task()                        │
    │     ┌──────────────────────────────────────────────┐   │
    │     │               TaskOrchestrator               │   │
    │     │       ProcessPoolExecutor (N Workers)        │   │
    │     └──────────────┬───────────────────────────────┘   │
    │                    │                                   │
    │         ┌──────────┴──────────┐                        │
    │         ▼                     ▼                        │
    │   EvolutionTask 1       EvolutionTask N                │
    │         │                     │                        │
    │         ▼                     ▼                        │
    │   LLaMEASession         LLaMEASession                  │
    │                                                        │
    │  4. Results Aggregation & Logging                      │
    │     Harvest SessionResult, summarize champion metrics  │
    └────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisRepository,
        config_repo: SynthesisConfigRepository,
        llm_client: LLMClient,
        logger: BaseLogger,
    ):
        self.sqlite_repo = sqlite_repo
        self.config_repo = config_repo
        self.llm_client = llm_client
        self.logger = logger
        self.audit_service = SynthesisAuditService(
            sqlite_repo=sqlite_repo,
            config_repo=config_repo,
            logger=logger,
        )

        # 1. Load strongly-typed synthesis configuration directly from repository
        self.config: SynthesisConfig = self.config_repo.load_config()

        # 2. Execution knobs & parameters (direct dot-access from dataclass)
        self.budget: int = self.config.budget
        self.timeout_seconds: float = self.config.timeout_seconds
        self.iterations: int = self.config.iterations
        self.runs_per_config: int = self.config.runs_per_config
        self.num_processes: int = self.config.num_processes
        self.auto_resume: bool = self.config.auto_resume
        self.skip_completed: bool = self.config.skip_completed
        self.retry_failed_synthesis: bool = self.config.retry_failed_synthesis
        self.only_incomplete: bool = self.config.only_incomplete
        self.target_exp_ids: list[int] = self.config.target_exp_ids

        # 3. Search space targets, noise conditions, and synthesis modes
        self.problem_targets: list[ProblemTarget] = self.config.problem_targets
        self.problems: list[int] = self.config.problems
        self.dimensions: list[int] = self.config.dimensions

        self.noise_conditions: list[NoiseConditionConfig] = self.config.noise_conditions
        self.noise_stds: list[float] = self.config.noise_stds
        self.noise_model: NoiseModelEnum = self.config.noise_model

        self.synthesis_mode_configs: list[SynthesisModeConfig] = self.config.synthesis_modes
        self.synthesis_modes: list[SynthesisMode] = self.config.mode_enums
        self.synthesis_mode: SynthesisMode | None = self.config.synthesis_mode
        self.prompt_strategies: list[PromptStrategy] = self.config.prompt_strategies

    # -------------------------------------------------------------------------
    # Public Use Cases
    # -------------------------------------------------------------------------

    def audit_matrix(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Reconciles configured matrix against SQLite experiments for the configured LLM model."""
        return self.audit_service.audit_matrix(model_name=self.llm_client.model.name)

    def build_tasks(self) -> list[EvolutionTask]:
        """Constructs the list of EvolutionTask units to execute based on configuration."""
        # Fast path: targeted experiment IDs
        if self.target_exp_ids:
            return self._build_targeted_tasks(target_ids=self.target_exp_ids)

        all_db_exps = self.sqlite_repo.load(llm_name=self.llm_client.model.name)
        db_comp, db_run, _ = self.audit_service.group_experiments_by_condition(
            experiments=all_db_exps,
            retry_failed_synthesis=self.retry_failed_synthesis,
        )

        tasks: list[EvolutionTask] = []
        for item in self.config.matrix_conditions:
            completed_list = db_comp.get(item, [])
            running_list = db_run.get(item, [])

            # Step A: Resume interrupted/running runs from DB if AUTO_RESUME enabled
            if self.auto_resume:
                for exp in running_list:
                    tasks.append(
                        self._build_resume_task(
                            exp=exp,
                            p_id=item.problem_id,
                            dim=item.dim,
                            noise_std=item.noise_std,
                            mode_label=item.task_mode_label,
                            strat=item.strategy,
                            synthesis_mode=item.synthesis_mode,
                        )
                    )

            # Step B: Calculate accounted count
            accounted_runs = (len(completed_list) if self.skip_completed else 0) + (
                len(running_list) if self.auto_resume else 0
            )

            # Step C: Schedule remaining fresh / retry runs
            if not self.only_incomplete:
                remaining_needed = max(0, self.runs_per_config - accounted_runs)
                for run_idx in range(accounted_runs + 1, accounted_runs + remaining_needed + 1):
                    tasks.append(
                        self._build_fresh_task(
                            p_id=item.problem_id,
                            dim=item.dim,
                            noise_std=item.noise_std,
                            noise_model=item.noise_model,
                            mode_label=item.task_mode_label,
                            strat=item.strategy,
                            run_idx=run_idx,
                            synthesis_mode=item.synthesis_mode,
                        )
                    )
        return tasks

    def run_task(
        self,
        task: EvolutionTask,
        verbose: bool = True,
    ) -> SessionResult:
        """Executes a single evolution task in the current process."""
        from evolution.application.worker import run_evolution_worker

        self.logger.verbose = verbose
        self.logger.header(
            title="LLaMEA Synthesis",
            subtitle=f"Single run: {task.key}",
        )
        result = run_evolution_worker(task)
        self.logger.summary(
            title="Task Complete",
            stats={
                "Key": task.key,
                "Best Error": result.best_error,
            },
        )
        return result

    def run_campaign(
        self,
        verbose: bool = True,
    ) -> CampaignResults:
        """Builds tasks and executes the evolutionary synthesis campaign in parallel using TaskOrchestrator."""
        from evolution.application.orchestrator import TaskOrchestrator

        self.logger.verbose = verbose
        workers = self.num_processes

        tasks = self.build_tasks()
        model_name = self.llm_client.model.name

        if not tasks:
            self.logger.success(
                f"All requested experiments are already completed with valid champions for '{model_name}'! Nothing to run."
            )
            return CampaignResults()

        self.logger.header(
            title="LLaMEA Evolutionary Algorithm Synthesis",
            subtitle=f"Model: {model_name} | Pending Tasks: {len(tasks)} | Concurrency: {workers} workers",
        )

        orchestrator = TaskOrchestrator(max_workers=workers)
        raw_results = orchestrator.run(tasks)
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
    # Private Helpers (Single Responsibility)
    # -------------------------------------------------------------------------

    def _build_session_config(self) -> SessionConfig:
        return SessionConfig(**self.config.to_session_config_dict())

    def _build_targeted_tasks(
        self,
        target_ids: list[int],
    ) -> list[EvolutionTask]:
        targeted_experiments = self.sqlite_repo.load_by_ids(target_ids)
        tasks: list[EvolutionTask] = []
        for exp in targeted_experiments:
            p_id = exp.problem.problem_id
            dim = exp.problem.dim
            noise_std = exp.problem.noise_std or 0.0
            noise_strat = NoiseStrategyFactory.create(
                noise_model=exp.problem.noise_model,
                noise_std=noise_std,
            )

            problem = BBOBProblem(
                problem_id=p_id,
                dim=dim,
                instance_id=exp.problem.instance_id or 1,
                noise_strategy=noise_strat,
            )
            initial_iter = len(exp.iterations) if exp.iterations else 0
            target_cfg = self._build_session_config()
            if exp.max_iterations:
                target_cfg = target_cfg.model_copy(update={"iterations": exp.max_iterations})

            mode_label = f"{exp.mode}_std_{noise_std}"
            tasks.append(
                EvolutionTask(
                    key=f"f{p_id}_{dim}D_{mode_label}_{exp.prompt_strategy}_target_exp{exp.id}",
                    problem=problem,
                    llm_client=self.llm_client,
                    experiment_id=exp.id,
                    initial_iteration=initial_iter,
                    prompt_strategy=exp.prompt_strategy,
                    synthesis_mode=exp.mode,
                    config=target_cfg,
                )
            )
        return tasks

    def _build_resume_task(
        self,
        exp: ExperimentSummary,
        p_id: int,
        dim: int,
        noise_std: float,
        mode_label: str,
        strat: PromptStrategy,
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
    ) -> EvolutionTask:
        """Constructs a resume EvolutionTask from an active running experiment in the database."""
        noise_strat = NoiseStrategyFactory.create(
            noise_model=exp.problem.noise_model,
            noise_std=noise_std,
        )
        resume_problem = BBOBProblem(
            problem_id=p_id,
            dim=dim,
            instance_id=exp.problem.instance_id or 1,
            noise_strategy=noise_strat,
        )
        initial_iter = len(exp.iterations) if exp.iterations else 0
        resume_cfg = self._build_session_config()
        if exp.max_iterations:
            resume_cfg = resume_cfg.model_copy(update={"iterations": exp.max_iterations})

        resolved_mode = synthesis_mode
        return EvolutionTask(
            key=f"f{p_id}_{dim}D_{mode_label}_{strat}_resume_exp{exp.id}",
            problem=resume_problem,
            llm_client=self.llm_client,
            experiment_id=exp.id,
            initial_iteration=initial_iter,
            prompt_strategy=strat,
            synthesis_mode=resolved_mode,
            config=resume_cfg,
        )

    def _build_fresh_task(
        self,
        p_id: int,
        dim: int,
        noise_std: float,
        mode_label: str,
        strat: PromptStrategy,
        run_idx: int,
        noise_model: NoiseModelEnum = NoiseModelEnum.HETEROSCEDASTIC,
        key_prefix: str = "",
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
    ) -> EvolutionTask:
        """Registers a new experiment record in the database and returns a fresh EvolutionTask."""
        noise_strat = NoiseStrategyFactory.create(
            noise_model=noise_model,
            noise_std=noise_std,
        )
        problem = BBOBProblem(
            problem_id=p_id,
            dim=dim,
            instance_id=1,
            noise_strategy=noise_strat,
        )

        problem_profile = ProblemProfile(
            problem_id=problem.problem_id,
            dim=problem.dim,
            noise_std=problem.noise_std,
            noise_model=problem.noise_model,
            instance_id=problem.instance_id,
            true_optimum=problem.true_optimum,
        )
        exp_mode = synthesis_mode
        fresh_cfg = self._build_session_config()
        exp_id = self.sqlite_repo.create_experiment(
            problem=problem_profile,
            mode=exp_mode,
            llm_name=self.llm_client.model.name,
            prompt_strategy=strat,
            budget=fresh_cfg.budget,
            max_iterations=fresh_cfg.iterations,
        )

        key = (
            f"{key_prefix}f{p_id}_{dim}D_{mode_label}_{strat}"
            if key_prefix
            else f"f{p_id}_{dim}D_{mode_label}_{strat}_run{run_idx}"
        )
        return EvolutionTask(
            key=key,
            problem=problem,
            llm_client=self.llm_client,
            experiment_id=exp_id,
            initial_iteration=0,
            prompt_strategy=strat,
            synthesis_mode=exp_mode,
            config=fresh_cfg,
        )
