from collections import defaultdict

import numpy as np
import pandas as pd

from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_repository import SynthesisRepository
from evolution.application.synthesis_config import MatrixCondition, SynthesisConfig
from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import BBOBFunction


class CampaignAuditor:
    """Inspect synthesis records and report campaign coverage."""

    def __init__(
        self,
        sqlite_repo: SynthesisRepository,
        config: SynthesisConfig,
        logger: BaseLogger,
        model_name: str,
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.config = config
        self.logger = logger
        self.model_name = model_name

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
            has_valid_champion = exp.best_final_error is not None and np.isfinite(
                exp.best_final_error
            )
            if exp.status == "completed":
                if has_valid_champion:
                    completed[cond].append(exp)
                else:
                    failed[cond].append(exp)
            elif exp.status == "failed":
                failed[cond].append(exp)
            elif exp.status == "running":
                running[cond].append(exp)

        return dict(completed), dict(running), dict(failed)

    def audit_matrix(self, model_name: str | None = None) -> tuple[pd.DataFrame, dict[str, object]]:
        """Report champion coverage independently of candidate failures or replicate quotas.

        Historical running/failed record counts remain visible, but do not make
        a covered condition eligible for automatic recovery.
        """
        llm_name = self.model_name if model_name is None else model_name
        all_db_exps = self.sqlite_repo.load(llm_name=llm_name)

        db_completed, db_running, db_failed = self.group_experiments_by_condition(
            experiments=all_db_exps,
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

            # Coverage is champion availability, not candidate-iteration success
            # or a future independent-replicate quota.
            if n_comp > 0:
                status_label = "✅ Complete"
                total_done += 1
            elif n_running > 0 and self.config.auto_resume:
                status_label = f"🔄 Incomplete ({n_running} to resume)"
            elif n_fail > 0 and self.config.retry_failed_synthesis:
                status_label = f"⚠️ Retry ({n_fail} failed)"
                total_retry += 1
            else:
                status_label = "⏳ Pending"

            matrix_rows.append(
                {
                    "Problem": f"f{item.problem_id} ({BBOBFunction.get_short_name(item.problem_id)})",
                    "Dimension": f"{item.dim}D",
                    "Environment": item.env_label,
                    "Strategy": item.strategy.capitalize(),
                    "Target Runs": self.config.runs_per_config,
                    "Completed": n_comp,
                    "Running Records": n_running,
                    "Failed Records": n_fail,
                    "Status": status_label,
                }
            )

        if matrix_rows:
            df_matrix = pd.DataFrame(matrix_rows).set_index(
                ["Problem", "Dimension", "Environment", "Strategy"]
            )
        else:
            df_matrix = pd.DataFrame(
                columns=[
                    "Problem",
                    "Dimension",
                    "Environment",
                    "Strategy",
                    "Target Runs",
                    "Completed",
                    "Running Records",
                    "Failed Records",
                    "Status",
                ]
            ).set_index(["Problem", "Dimension", "Environment", "Strategy"])

        total_cfg = len(df_matrix)
        progress_pct = (total_done / max(1, total_cfg)) * 100

        summary: dict[str, object] = {
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
            "prompt_strategies": [s.value for s in self.config.prompt_strategies],
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
