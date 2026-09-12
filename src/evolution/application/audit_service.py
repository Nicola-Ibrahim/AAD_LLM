"""Synthesis Matrix Audit Application Service.

Reconciles configured evolutionary experiment conditions against SQLite database records,
reporting completion, partial, and pending status for LLM synthesis targets.
"""

from typing import Any

import numpy as np
import pandas as pd

from evolution.application.interfaces import BaseLogger
from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import BBOBFunction
from evolution.infra.storage.synthesis import SQLiteSynthesisRepository
from evolution.infra.storage.synthesis_config import (
    MatrixCondition,
    SynthesisConfig,
    SynthesisConfigRepository,
)


class SynthesisAuditService:
    """Application use case service for auditing algorithm synthesis matrix coverage."""

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisRepository,
        config_repo: SynthesisConfigRepository,
        logger: BaseLogger,
    ):
        self.sqlite_repo = sqlite_repo
        self.config_repo = config_repo
        self.logger = logger

        self.config: SynthesisConfig = self.config_repo.load_config()
        self.runs_per_config: int = self.config.runs_per_config
        self.retry_failed_synthesis: bool = self.config.retry_failed_synthesis
        self.auto_resume: bool = self.config.auto_resume
        self.skip_completed: bool = self.config.skip_completed

        self.problem_targets = self.config.problem_targets
        self.problems = self.config.problems
        self.dimensions = self.config.dimensions
        self.noise_stds = self.config.noise_stds
        self.synthesis_modes = self.config.mode_enums
        self.prompt_strategies = self.config.prompt_strategies
        self.target_exp_ids = self.config.target_exp_ids

    def group_experiments_by_condition(
        self,
        experiments: list[ExperimentSummary],
        retry_failed_synthesis: bool | None = None,
    ) -> tuple[
        dict[MatrixCondition, list[ExperimentSummary]],
        dict[MatrixCondition, list[ExperimentSummary]],
        dict[MatrixCondition, list[ExperimentSummary]],
    ]:
        """Partitions database experiment records into completed, running, and failed groups."""
        retry_flag = (
            retry_failed_synthesis
            if retry_failed_synthesis is not None
            else self.retry_failed_synthesis
        )

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
                if has_valid_champion or not retry_flag:
                    db_completed.setdefault(cond, []).append(exp)
                else:
                    db_failed_synthesis.setdefault(cond, []).append(exp)
            elif exp.status == "running":
                db_running.setdefault(cond, []).append(exp)

        return db_completed, db_running, db_failed_synthesis

    def audit_matrix(
        self,
        model_name: str,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Reconciles configured matrix against SQLite experiments for the specified LLM model."""
        all_db_exps = self.sqlite_repo.load(llm_name=model_name)
        db_comp, db_run, db_fail = self.group_experiments_by_condition(
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

        if matrix_rows:
            df_matrix = pd.DataFrame(matrix_rows).set_index(
                ["Problem", "Dimension", "Environment", "Strategy"]
            )
        else:
            df_matrix = pd.DataFrame(
                columns=["Problem", "Dimension", "Environment", "Strategy", "Target Runs", "Completed", "Status"]
            ).set_index(["Problem", "Dimension", "Environment", "Strategy"])

        total_cfg = len(df_matrix)
        total_done = sum(1 for r in matrix_rows if "✅" in r["Status"])
        total_retry = sum(1 for r in matrix_rows if "⚠️" in r["Status"])

        summary = {
            "model_name": model_name,
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
            model_name=model_name,
            total_conditions=total_cfg,
            completed=total_done,
            pending=total_cfg - total_done,
            retry=total_retry,
            progress_pct=summary["progress_pct"],
        )
        return df_matrix, summary
