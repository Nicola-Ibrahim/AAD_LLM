"""LLaMEA Algorithm Synthesis Application Service (Campaign & Execution Facade).

Coordinates synthesis configuration reading, database status reconciliation,
task construction, upfront synthesis session persistence, and parallel multi-process dispatching.
"""

from typing import Any

import numpy as np
import pandas as pd
from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import BBOBFunction, NoiseModelEnum, PromptStrategy, SynthesisMode
from evolution.domain.services.noise_strategy import NoiseStrategyFactory
from evolution.domain.vos import ProblemProfile
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from evolution.infra.problems.bbob import BBOBProblem
from evolution.infra.storage.synthesis_config import (
    MatrixCondition,
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisConfig,
    SynthesisConfigRepository,
    SynthesisModeConfig,
)
from evolution.infra.storage.synthesis import SQLiteSynthesisRepository
from evolution.application.synthesis.session import SessionResult
from evolution.application.tasks import EvolutionTask, TaskOrchestrator


class LLaMEASynthesisService:
    """Application use case service managing algorithm synthesis campaigns."""

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisRepository,
        config_repo: SynthesisConfigRepository,
        llm_client: LLMClient,
        logger: SynthesisLogger,
    ):
        self.sqlite_repo = sqlite_repo
        self.config_repo = config_repo
        self.llm_client = llm_client
        self.logger = logger

        # 1. Load strongly-typed synthesis configuration directly from repository
        self.config: SynthesisConfig = self.config_repo.load_config()
        self.cfg = self.config  # Preserved for backward compatibility

        # 2. Execution knobs & parameters (direct dot-access from dataclass)
        self.budget: int = self.config.budget
        self.iterations: int = self.config.iterations
        self.runs_per_config: int = self.config.runs_per_config
        self.num_processes: int = self.config.num_processes
        self.auto_resume: bool = self.config.auto_resume
        self.skip_completed: bool = self.config.skip_completed
        self.retry_failed_synthesis: bool = self.config.retry_failed_synthesis
        self.only_incomplete: bool = self.config.only_incomplete
        self.target_exp_ids: list[int] | None = self.config.target_exp_ids

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
        llm_name = self.llm_client.model.name

        all_db_exps = self.sqlite_repo.load(llm_name=llm_name)
        db_comp, db_run, db_fail = self._group_experiments_by_condition(
            experiments=all_db_exps,
            retry_failed_synthesis=self.retry_failed_synthesis,
        )

        matrix_rows = []
        for item in self.config.matrix_conditions:
            n_comp = len(db_comp.get(item, []))
            n_fail = len(db_fail.get(item, []))
            n_run = len(db_run.get(item, []))

            if n_comp >= self.runs_per_config:
                status_label = "✅ Completed (Valid Champion)"
            elif n_fail > 0 and self.retry_failed_synthesis:
                status_label = f"⚠️ Failed Synthesis (To Retry, {n_fail} run)"
            elif n_run > 0:
                status_label = f"🔄 Incomplete/Running ({n_run})"
            else:
                status_label = "⏳ Pending"

            matrix_rows.append({
                "Problem": f"f{item.problem_id} ({BBOBFunction.get_short_name(item.problem_id)})",
                "Dimension": f"{item.dim}D",
                "Environment": item.env_label,
                "Strategy": item.strategy.capitalize(),
                "Target Runs": self.runs_per_config,
                "Completed": n_comp,
                "Status": status_label,
            })

        df_matrix = pd.DataFrame(matrix_rows)
        total_cfg = len(df_matrix)
        total_done = sum(1 for r in matrix_rows if "✅" in r["Status"])
        total_retry = sum(1 for r in matrix_rows if "⚠️" in r["Status"])

        summary = {
            "model_name": llm_name,
            "total_conditions": total_cfg,
            "completed_conditions": total_done,
            "retry_conditions": total_retry,
            "progress_pct": (total_done / max(1, total_cfg)) * 100,
            "retry_failed_synthesis": self.retry_failed_synthesis,
            "auto_resume": self.auto_resume,
            "skip_completed": self.skip_completed,
            "problem_targets": self.problem_targets,
            "problem_ids": self.problems,
            "dimensions": self.dimensions,
            "noise_stds": self.noise_stds,
            "synthesis_modes": [m.value for m in self.synthesis_modes],
            "prompt_strategies": [s for s in self.prompt_strategies],
            "target_exp_ids": self.target_exp_ids,
        }
        self.logger.audit_summary(
            model_name=llm_name,
            total_conditions=total_cfg,
            completed=total_done,
            pending=total_cfg - total_done,
            retry=total_retry,
            progress_pct=summary["progress_pct"],
        )
        return df_matrix, summary

    def build_tasks(self) -> list[EvolutionTask]:
        """Constructs the list of EvolutionTask units to execute based on configuration."""
        # Fast path: targeted experiment IDs
        if self.target_exp_ids:
            return self._build_targeted_tasks(target_ids=self.target_exp_ids)

        all_db_exps = self.sqlite_repo.load(llm_name=self.llm_client.model.name)
        db_comp, db_run, _ = self._group_experiments_by_condition(
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
                for run_idx in range(
                    accounted_runs + 1, accounted_runs + remaining_needed + 1
                ):
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

    def run_synthesis(
        self,
        verbose: bool = True,
    ) -> dict[str, SessionResult]:
        """Builds tasks and executes the evolutionary synthesis in parallel using TaskOrchestrator."""
        self.logger.verbose = verbose
        workers = self.num_processes

        tasks = self.build_tasks()
        model_name = self.llm_client.model.name

        if not tasks:
            self.logger.success(
                f"All requested experiments are already completed with valid champions for '{model_name}'! Nothing to run."
            )
            return {}

        self.logger.header(
            title="LLaMEA Evolutionary Algorithm Synthesis",
            subtitle=f"Model: {model_name} | Pending Tasks: {len(tasks)} | Concurrency: {workers} workers",
        )

        orchestrator = TaskOrchestrator(max_workers=workers)
        results = orchestrator.run(tasks)

        successful_count = sum(
            1
            for r in results.values()
            if r.best_error is not None and np.isfinite(r.best_error)
        )
        failed_count = len(results) - successful_count

        self.logger.summary(
            title="Synthesis Campaign Complete",
            stats={
                "Model Target": model_name,
                "Total Tasks Executed": len(results),
                "Valid Champions Found": successful_count,
                "Failed / Incomplete": failed_count,
            },
        )
        return results

    # -------------------------------------------------------------------------
    # Private Helpers (Single Responsibility)
    # -------------------------------------------------------------------------

    def _group_experiments_by_condition(
        self,
        experiments: list[ExperimentSummary],
        retry_failed_synthesis: bool,
    ) -> tuple[dict[MatrixCondition, list[ExperimentSummary]], dict[MatrixCondition, list[ExperimentSummary]], dict[MatrixCondition, list[ExperimentSummary]]]:
        """Partitions database experiment records into completed, running, and failed groups."""
        db_completed: dict[MatrixCondition, list[ExperimentSummary]] = {}
        db_running: dict[MatrixCondition, list[ExperimentSummary]] = {}
        db_failed_synthesis: dict[MatrixCondition, list[ExperimentSummary]] = {}

        for exp in experiments:
            noise_val = round(exp.problem.noise_std, 4) if exp.problem.noise_std else 0.0
            cond = MatrixCondition(
                problem_id=exp.problem.problem_id,
                dim=exp.problem.dim,
                mode=exp.mode,
                noise_std=noise_val,
                noise_model=exp.problem.noise_model,
                strategy=exp.prompt_strategy,
            )

            has_valid_champion = (
                exp.best_final_error is not None and np.isfinite(exp.best_final_error)
            )
            if exp.status == "completed":
                if has_valid_champion or not retry_failed_synthesis:
                    db_completed.setdefault(cond, []).append(exp)
                else:
                    db_failed_synthesis.setdefault(cond, []).append(exp)
            elif exp.status == "running":
                db_running.setdefault(cond, []).append(exp)

        return db_completed, db_running, db_failed_synthesis

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
            tasks.append(
                EvolutionTask(
                    key=f"f{p_id}_{dim}D_{'clean' if noise_std == 0.0 else f'noisy_std_{noise_std}'}_{exp.prompt_strategy}_target_exp{exp.id}",
                    problem=problem,
                    llm_client=self.llm_client,
                    experiment_id=exp.id,
                    initial_iteration=initial_iter,
                    budget=self.budget,
                    iterations=exp.max_iterations or self.iterations,
                    prompt_strategy=exp.prompt_strategy,
                    synthesis_mode=exp.mode,
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
        synthesis_mode: SynthesisMode | None = None,
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
        return EvolutionTask(
            key=f"f{p_id}_{dim}D_{mode_label}_{strat}_resume_exp{exp.id}",
            problem=resume_problem,
            llm_client=self.llm_client,
            experiment_id=exp.id,
            initial_iteration=initial_iter,
            budget=self.budget,
            iterations=exp.max_iterations or self.iterations,
            prompt_strategy=strat,
            synthesis_mode=synthesis_mode or exp.mode,
        )

    def _build_fresh_task(
        self,
        p_id: int,
        dim: int,
        noise_std: float,
        mode_label: str,
        strat: PromptStrategy,
        run_idx: int,
        noise_model: NoiseModelEnum | None = None,
        key_prefix: str = "",
        synthesis_mode: SynthesisMode | None = None,
    ) -> EvolutionTask:
        """Registers a new experiment record in the database and returns a fresh EvolutionTask."""
        effective_noise_model = noise_model or self.noise_model
        noise_strat = NoiseStrategyFactory.create(
            noise_model=effective_noise_model,
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
        exp_mode = synthesis_mode or problem.mode
        exp_id = self.sqlite_repo.create_experiment(
            problem=problem_profile,
            mode=exp_mode,
            llm_name=self.llm_client.model.name,
            prompt_strategy=strat,
            budget=self.budget,
            iterations=self.iterations,
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
            budget=self.budget,
            iterations=self.iterations,
            prompt_strategy=strat,
            synthesis_mode=exp_mode,
        )
