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
from evolution.infra.storage.synthesis_config import SynthesisConfigRepository
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

        # 1. Load and extract synthesis configuration upfront
        self.cfg: dict[str, Any] = self.config_repo.load_config()

        # 2. Execution knobs & parameters
        self.budget: int = int(self.cfg["budget"])
        self.iterations: int = int(self.cfg["iterations"])
        self.runs_per_config: int = int(self.cfg["runs_per_config"])
        self.num_processes: int = int(self.cfg["num_processes"])
        self.auto_resume: bool = bool(self.cfg["auto_resume"])
        self.skip_completed: bool = bool(self.cfg["skip_completed"])
        self.retry_failed_synthesis: bool = bool(self.cfg["retry_failed_synthesis"])
        self.only_incomplete: bool = bool(self.cfg["only_incomplete"])
        self.target_exp_ids: list[int] | None = self.cfg["target_exp_ids"]
        self.noise_model: NoiseModelEnum = NoiseModelEnum(
            self.cfg.get("noise_model", "heteroscedastic")
        )
        raw_mode = self.cfg.get("synthesis_mode")
        self.synthesis_mode: SynthesisMode | None = (
            SynthesisMode(raw_mode.lower()) if raw_mode else None
        )

        # 3. Search space dimensions and prompt strategies
        self.problems: list[int] = [
            int(p) for p in self.cfg.get("problem_ids", [1, 8, 11, 15, 21])
        ]
        self.dimensions: list[int] = [int(d) for d in self.cfg.get("dimensions", [2, 3, 5])]
        self.noise_stds: list[float] = [float(s) for s in self.cfg.get("noise_stds", [0.0, 0.05])]

        raw_strats = self.cfg.get("prompt_strategies", ["baseline"])
        if isinstance(raw_strats, str):
            raw_strats = [raw_strats]
        self.prompt_strategies: list[PromptStrategy] = [
            PromptStrategy(s.lower()) if isinstance(s, str) else s for s in raw_strats
        ]

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
        for dim in self.dimensions:
            for noise_std in self.noise_stds:
                noise_val = round(noise_std, 4)
                if self.synthesis_mode and noise_std > 0:
                    mode_enum = self.synthesis_mode
                    mode_label = (
                        f"Implicit ({noise_std})"
                        if mode_enum == SynthesisMode.IMPLICIT
                        else f"Noisy ({noise_std})"
                    )
                else:
                    mode_enum = SynthesisMode.CLEAN if noise_std == 0.0 else SynthesisMode.NOISY
                    mode_label = "Clean (0.0)" if noise_std == 0.0 else f"Noisy ({noise_std})"

                for strat in self.prompt_strategies:
                    for p_id in self.problems:
                        cfg_key = (p_id, dim, mode_enum, noise_val, strat)
                        n_comp = len(db_comp.get(cfg_key, []))
                        n_fail = len(db_fail.get(cfg_key, []))
                        n_run = len(db_run.get(cfg_key, []))

                        if n_comp >= self.runs_per_config:
                            status_label = "✅ Completed (Valid Champion)"
                        elif n_fail > 0 and self.retry_failed_synthesis:
                            status_label = f"⚠️ Failed Synthesis (To Retry, {n_fail} run)"
                        elif n_run > 0:
                            status_label = f"🔄 Incomplete/Running ({n_run})"
                        else:
                            status_label = "⏳ Pending"

                        matrix_rows.append({
                            "Problem": f"f{p_id} ({BBOBFunction.get_short_name(p_id)})",
                            "Dimension": f"{dim}D",
                            "Environment": mode_label,
                            "Strategy": strat.capitalize(),
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
            "problem_ids": self.problems,
            "dimensions": self.dimensions,
            "noise_stds": self.noise_stds,
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
        for dim in self.dimensions:
            for noise_std in self.noise_stds:
                noise_val = round(noise_std, 4)
                if self.synthesis_mode and noise_std > 0:
                    mode_enum = self.synthesis_mode
                    mode_label = (
                        f"implicit_std_{noise_std}"
                        if mode_enum == SynthesisMode.IMPLICIT
                        else f"noisy_std_{noise_std}"
                    )
                    task_mode = mode_enum
                else:
                    mode_enum = SynthesisMode.CLEAN if noise_std == 0.0 else SynthesisMode.NOISY
                    mode_label = "clean" if noise_std == 0.0 else f"noisy_std_{noise_std}"
                    task_mode = None

                for strat in self.prompt_strategies:
                    for p_id in self.problems:
                        cfg_key = (p_id, dim, mode_enum, noise_val, strat)
                        completed_list = db_comp.get(cfg_key, [])
                        running_list = db_run.get(cfg_key, [])

                        # Step A: Resume interrupted/running runs from DB if AUTO_RESUME enabled
                        if self.auto_resume:
                            for exp in running_list:
                                tasks.append(
                                    self._build_resume_task(
                                        exp=exp,
                                        p_id=p_id,
                                        dim=dim,
                                        noise_std=noise_std,
                                        mode_label=mode_label,
                                        strat=strat,
                                        synthesis_mode=task_mode,
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
                                        p_id=p_id,
                                        dim=dim,
                                        noise_std=noise_std,
                                        mode_label=mode_label,
                                        strat=strat,
                                        run_idx=run_idx,
                                        synthesis_mode=task_mode,
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
    ) -> tuple[dict[tuple, list], dict[tuple, list], dict[tuple, list]]:
        """Partitions database experiment records into completed, running, and failed groups."""
        db_completed: dict[tuple, list] = {}
        db_running: dict[tuple, list] = {}
        db_failed_synthesis: dict[tuple, list] = {}

        for exp in experiments:
            noise_val = round(exp.problem.noise_std, 4) if exp.problem.noise_std else 0.0
            key = (exp.problem.problem_id, exp.problem.dim, exp.mode, noise_val, exp.prompt_strategy)

            has_valid_champion = (
                exp.best_final_error is not None and np.isfinite(exp.best_final_error)
            )
            if exp.status == "completed":
                if has_valid_champion or not retry_failed_synthesis:
                    db_completed.setdefault(key, []).append(exp)
                else:
                    db_failed_synthesis.setdefault(key, []).append(exp)
            elif exp.status == "running":
                db_running.setdefault(key, []).append(exp)

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
        key_prefix: str = "",
        synthesis_mode: SynthesisMode | None = None,
    ) -> EvolutionTask:
        """Registers a new experiment record in the database and returns a fresh EvolutionTask."""
        noise_strat = NoiseStrategyFactory.create(
            noise_model=self.noise_model,
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
