"""Read-only synthesis coverage, independent of campaign dispatch."""

import pandas as pd
from pydantic import validate_call

from evolution.application.campaign.conditions import (
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisModeConfig,
    group_experiments_by_condition,
)
from evolution.application.campaign.settings import CampaignSettings
from evolution.application.interfaces.logger import BaseLogger
from evolution.domain.enums import BBOBFunction
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from shared.application.result import Result


class CampaignAudit:
    """Inspect experiment coverage without constructing or dispatching tasks."""

    def __init__(
        self,
        sqlite_repo: SynthesisRepository,
        logger: BaseLogger,
        model_name: str,
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.logger = logger
        self.model_name = model_name

    @validate_call(config={"strict": True})
    def inspect(
        self,
        *,
        problem_targets: list[ProblemTarget],
        noise_conditions: list[NoiseConditionConfig],
        synthesis_modes: list[SynthesisModeConfig],
        iterations: int,
        budget: int,
        timeout_seconds: float,
        runs_per_config: int,
        auto_resume: bool,
        skip_completed: bool,
        retry_failed_synthesis: bool,
    ) -> Result[tuple[pd.DataFrame, dict[str, object]]]:
        """Inspect the same explicit study parameters without dispatching work."""
        try:
            with self.logger.operation("synthesis coverage audit"):
                config = CampaignSettings(
                    problem_targets=problem_targets,
                    noise_conditions=noise_conditions,
                    synthesis_modes=synthesis_modes,
                    iterations=iterations,
                    budget=budget,
                    timeout_seconds=timeout_seconds,
                    runs_per_config=runs_per_config,
                    auto_resume=auto_resume,
                    skip_completed=skip_completed,
                    retry_failed_synthesis=retry_failed_synthesis,
                )
                llm_name = self.model_name
                all_db_exps = self.sqlite_repo.load(llm_name=llm_name)

                db_completed, db_running, db_failed = group_experiments_by_condition(
                    experiments=all_db_exps,
                )

                matrix_rows = []
                total_done = 0
                total_retry = 0

                for item in config.matrix_conditions:
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
                    elif n_running > 0 and config.auto_resume:
                        status_label = f"🔄 Incomplete ({n_running} to resume)"
                    elif n_fail > 0 and config.retry_failed_synthesis:
                        status_label = f"⚠️ Retry ({n_fail} failed)"
                        total_retry += 1
                    else:
                        status_label = "⏳ Pending"

                    matrix_rows.append(
                        {
                            "Problem": f"f{item.problem_id} ({BBOBFunction.get_short_name(item.problem_id)})",
                            "Dimension": f"{item.dim}D",
                            "Environment": f"{item.mode.value.title()} ({item.noise_std})",
                            "Strategy": item.strategy.capitalize(),
                            "Target Runs": config.runs_per_config,
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
                    "retry_failed_synthesis": config.retry_failed_synthesis,
                    "auto_resume": config.auto_resume,
                    "skip_completed": config.skip_completed,
                    "problem_targets": config.problem_targets,
                    "problem_ids": config.problem_ids,
                    "dimensions": config.dimensions,
                    "noise_stds": config.noise_stds,
                    "synthesis_modes": config.synthesis_mode_names,
                    "prompt_strategies": [s.value for s in config.prompt_strategies],
                }

                self.logger.audit_summary(
                    model_name=llm_name,
                    total_conditions=total_cfg,
                    completed=total_done,
                    pending=total_cfg - total_done,
                    retry=total_retry,
                    progress_pct=progress_pct,
                )
                return Result.success((df_matrix, summary))
        except Exception as error:
            return Result.failure("synthesis coverage audit", error)
