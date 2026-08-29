"""LLaMEA Algorithm Synthesis Application Service (Campaign & Execution Facade).

Coordinates synthesis configuration reading, database status reconciliation,
task construction, upfront synthesis session persistence, and parallel multi-process dispatching.
"""

from typing import Any

import numpy as np
import pandas as pd
from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import BBOBFunction, NoiseModelEnum, PromptStrategy
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

    # -------------------------------------------------------------------------
    # Public Use Cases
    # -------------------------------------------------------------------------

    def audit_matrix(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Reconciles configured matrix against SQLite experiments for the configured LLM model."""
        cfg = self.config_repo.load_config()
        llm_name = self.llm_client.model.name

        do_retry_failed = bool(cfg["retry_failed_synthesis"])
        runs_per_config = int(cfg["runs_per_config"])

        problems, dimensions, noise_stds, prompt_strats = self._resolve_search_space(cfg)

        all_db_exps = self.sqlite_repo.load(llm_name=llm_name)
        db_comp, db_run, db_fail = self._group_experiments_by_condition(
            experiments=all_db_exps,
            retry_failed_synthesis=do_retry_failed,
        )

        matrix_rows = []
        for dim in dimensions:
            for noise_std in noise_stds:
                mode_label = "Clean (0.0)" if noise_std == 0.0 else f"Noisy ({noise_std})"
                mode_str = "clean" if noise_std == 0.0 else "noisy"
                noise_val = round(noise_std, 4)

                for strat in prompt_strats:
                    for p_id in problems:
                        cfg_key = (p_id, dim, mode_str, noise_val, strat.value.lower())
                        n_comp = len(db_comp.get(cfg_key, []))
                        n_fail = len(db_fail.get(cfg_key, []))
                        n_run = len(db_run.get(cfg_key, []))

                        if n_comp >= runs_per_config:
                            status_label = "✅ Completed (Valid Champion)"
                        elif n_fail > 0 and do_retry_failed:
                            status_label = f"⚠️ Failed Synthesis (To Retry, {n_fail} run)"
                        elif n_run > 0:
                            status_label = f"🔄 Incomplete/Running ({n_run})"
                        else:
                            status_label = "⏳ Pending"

                        matrix_rows.append({
                            "Problem": f"f{p_id} ({BBOBFunction.get_short_name(p_id)})",
                            "Dimension": f"{dim}D",
                            "Environment": mode_label,
                            "Strategy": strat.value.capitalize(),
                            "Target Runs": runs_per_config,
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
            "retry_failed_synthesis": do_retry_failed,
            "auto_resume": cfg["auto_resume"],
            "skip_completed": cfg["skip_completed"],
            "problem_ids": cfg["problem_ids"],
            "dimensions": cfg["dimensions"],
            "noise_stds": cfg["noise_stds"],
            "prompt_strategies": [s.value for s in prompt_strats],
            "target_exp_ids": cfg["target_exp_ids"],
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
        cfg = self.config_repo.load_config()

        do_auto_resume = bool(cfg["auto_resume"])
        do_skip_comp = bool(cfg["skip_completed"])
        do_only_incomp = bool(cfg["only_incomplete"])
        do_retry_failed = bool(cfg["retry_failed_synthesis"])

        task_budget = int(cfg["budget"])
        task_iterations = int(cfg["iterations"])
        runs_per_config = int(cfg["runs_per_config"])
        noise_model = NoiseModelEnum(cfg.get("noise_model", "heteroscedastic"))
        f_target_ids = cfg["target_exp_ids"]

        # Fast path: targeted experiment IDs
        if f_target_ids:
            return self._build_targeted_tasks(
                target_ids=f_target_ids,
                task_budget=task_budget,
                fallback_iterations=task_iterations,
            )

        problems, dimensions, noise_stds, prompt_strats = self._resolve_search_space(cfg)

        all_db_exps = self.sqlite_repo.load(llm_name=self.llm_client.model.name)
        db_comp, db_run, _ = self._group_experiments_by_condition(
            experiments=all_db_exps,
            retry_failed_synthesis=do_retry_failed,
        )

        tasks: list[EvolutionTask] = []
        for dim in dimensions:
            for noise_std in noise_stds:
                mode_str = "clean" if noise_std == 0.0 else "noisy"
                mode_label = "clean" if noise_std == 0.0 else f"noisy_std_{noise_std}"
                noise_val = round(noise_std, 4)

                for strat in prompt_strats:
                    for p_id in problems:
                        cfg_key = (p_id, dim, mode_str, noise_val, strat.value.lower())
                        completed_list = db_comp.get(cfg_key, [])
                        running_list = db_run.get(cfg_key, [])

                        # Step A: Resume interrupted/running runs from DB if AUTO_RESUME enabled
                        if do_auto_resume:
                            for exp in running_list:
                                tasks.append(
                                    self._build_resume_task(
                                        exp=exp,
                                        p_id=p_id,
                                        dim=dim,
                                        noise_std=noise_std,
                                        mode_label=mode_label,
                                        strat=strat,
                                        task_budget=task_budget,
                                        task_iterations=task_iterations,
                                    )
                                )

                        # Step B: Calculate accounted count
                        accounted_runs = (len(completed_list) if do_skip_comp else 0) + (
                            len(running_list) if do_auto_resume else 0
                        )

                        # Step C: Schedule remaining fresh / retry runs
                        if not do_only_incomp:
                            remaining_needed = max(0, runs_per_config - accounted_runs)
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
                                        task_budget=task_budget,
                                        task_iterations=task_iterations,
                                        noise_model=noise_model,
                                    )
                                )
        return tasks

    def run_synthesis(
        self,
        max_workers: int | None = None,
        verbose: bool = True,
    ) -> dict[str, SessionResult]:
        """Builds tasks and executes the evolutionary synthesis in parallel using TaskOrchestrator."""
        self.logger.verbose = verbose
        cfg = self.config_repo.load_config()
        workers = max_workers if max_workers is not None else int(cfg.get("num_processes", 1))

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

    def _resolve_search_space(
        self,
        cfg: dict[str, Any],
    ) -> tuple[list[int], list[int], list[float], list[PromptStrategy]]:
        """Resolves active problems, dimensions, noise standard deviations, and strategies from config."""
        raw_strats = cfg.get("prompt_strategies", ["baseline"])
        if isinstance(raw_strats, str):
            raw_strats = [raw_strats]
        prompt_strats = [getattr(PromptStrategy, s.upper()) for s in raw_strats]

        problems = [int(p) for p in cfg.get("problem_ids", [1, 8, 11, 15, 21])]
        dimensions = [int(d) for d in cfg.get("dimensions", [2, 3, 5])]
        noise_stds = [float(s) for s in cfg.get("noise_stds", [0.0, 0.05])]

        return problems, dimensions, noise_stds, prompt_strats

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
            mode_str = exp.mode.lower()
            noise_val = round(exp.problem.noise_std, 4) if exp.problem.noise_std else 0.0
            strat_str = exp.prompt_strategy.lower()
            key = (exp.problem.problem_id, exp.problem.dim, mode_str, noise_val, strat_str)

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
        task_budget: int,
        fallback_iterations: int,
    ) -> list[EvolutionTask]:
        targeted_experiments = self.sqlite_repo.load_by_ids(target_ids)
        tasks: list[EvolutionTask] = []
        for exp in targeted_experiments:
            p_id = exp.problem.problem_id
            dim = exp.problem.dim
            noise_std = exp.problem.noise_std or 0.0
            strat_str = str(exp.prompt_strategy).lower()
            strat_enum = getattr(PromptStrategy, strat_str.upper())
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
                    key=f"f{p_id}_{dim}D_{'clean' if noise_std == 0.0 else f'noisy_std_{noise_std}'}_{strat_str}_target_exp{exp.id}",
                    problem=problem,
                    llm_client=self.llm_client,
                    experiment_id=exp.id,
                    initial_iteration=initial_iter,
                    budget=task_budget,
                    iterations=exp.max_iterations or fallback_iterations,
                    prompt_strategy=strat_enum,
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
        task_budget: int,
        task_iterations: int,
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
            key=f"f{p_id}_{dim}D_{mode_label}_{strat.value}_resume_exp{exp.id}",
            problem=resume_problem,
            llm_client=self.llm_client,
            experiment_id=exp.id,
            initial_iteration=initial_iter,
            budget=task_budget,
            iterations=exp.max_iterations or task_iterations,
            prompt_strategy=strat,
        )

    def _build_fresh_task(
        self,
        p_id: int,
        dim: int,
        noise_std: float,
        mode_label: str,
        strat: PromptStrategy,
        run_idx: int,
        task_budget: int,
        task_iterations: int,
        noise_model: NoiseModelEnum,
        key_prefix: str = "",
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
        exp_id = self.sqlite_repo.create_experiment(
            problem=problem_profile,
            mode=problem.mode,
            llm_name=self.llm_client.model.name,
            prompt_strategy=strat.value,
            budget=task_budget,
            iterations=task_iterations,
        )

        key = (
            f"{key_prefix}f{p_id}_{dim}D_{mode_label}_{strat.value}"
            if key_prefix
            else f"f{p_id}_{dim}D_{mode_label}_{strat.value}_run{run_idx}"
        )
        return EvolutionTask(
            key=key,
            problem=problem,
            llm_client=self.llm_client,
            experiment_id=exp_id,
            initial_iteration=0,
            budget=task_budget,
            iterations=task_iterations,
            prompt_strategy=strat,
        )
