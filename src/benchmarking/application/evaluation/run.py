from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.champion_repository import ChampionRepository
from benchmarking.application.interfaces.evaluation_state_store import EvaluationStateStore
from benchmarking.application.interfaces.logger import EvaluationLoggerInterface
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from shared.application.interfaces.problem_factory import ProblemFactory
from benchmarking.application.evaluation.types import BaselineRunnerResolver, ExecutorBuilder

import numpy as np
import pandas as pd

from benchmarking.application.evaluation.trials import EvaluationTrialRunner
from benchmarking.application.evaluation.workload import EvaluationWorkload
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.services.resolvers import ModelNames


class EvaluationService:
    """Coordinate workload auditing and benchmark trial execution."""

    def __init__(
        self,
        sqlite_repo: SynthesisReadRepository,
        champions_repo: ChampionRepository,
        state_repo: EvaluationStateStore,
        config: EvaluationConfig,
        logger: EvaluationLoggerInterface,
        problem_factory: ProblemFactory,
        executor_factory: ExecutorBuilder,
        baseline_resolver: BaselineRunnerResolver,
        code_reader: CandidateCodeReader,
        model_names: ModelNames,
    ) -> None:
        self.champion_selection = ChampionSelectionService(champions_repo=champions_repo)
        self.logger = logger
        self.model_names = model_names
        self.config = config
        self.workload = EvaluationWorkload(
            sqlite_repo=sqlite_repo,
            champion_selection=self.champion_selection,
            state_repo=state_repo,
            code_reader=code_reader,
            model_names=model_names,
            config=self.config,
        )
        self.trials = EvaluationTrialRunner(
            state_repo=state_repo,
            logger=logger,
            problem_factory=problem_factory,
            executor_factory=executor_factory,
            baseline_resolver=baseline_resolver,
            code_reader=code_reader,
            model_names=model_names,
            config=self.config,
        )

    def run_evaluations(
        self,
        solver_type: str = "all",
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial evaluations matching the configured workload."""
        self.logger.verbose = verbose

        df_audit = self.workload.audit_workload(solver_type=solver_type)
        active = df_audit[~df_audit["is_filtered"] & (df_audit["status"] != "MISSING_CODE")]

        champions_flat = (
            self.champion_selection.flatten_champions()
            if solver_type in ("all", "champions", "cross_eval")
            else {}
        )
        results: list[dict[str, object]] = []

        total_active = len(active)
        self.logger.header(
            title=f"Starting Benchmark Evaluations for {solver_type.upper()}",
            subtitle=f"{total_active} target conditions to evaluate",
        )
        cached_count = 0
        executed_count = 0

        for idx, (_, row) in enumerate(active.iterrows(), start=1):
            stype = row["solver_type"]
            dim = row["dim"]
            noise_std = row["noise_std"]
            p_id = row["problem_id"]
            s_name = row["display_name"]

            self.logger.condition_start(
                index=idx,
                total=total_active,
                solver_type=stype,
                solver_name=s_name,
                dim=dim,
                noise_std=noise_std,
                problem_id=p_id,
                problem_name=BBOBFunction.get_name(p_id),
                mode=(row.get("mode") if stype in ("champion", "cross_eval") else None),
                strategy=(row.get("strategy") if stype in ("champion", "cross_eval") else None),
            )

            if stype in ("champion", "cross_eval"):
                raw_k = row.get("raw_key", row["key"])
                matching = [v for k, v in champions_flat.items() if k == raw_k or k.endswith(raw_k)]
                if not matching:
                    matching = [
                        v
                        for k, v in champions_flat.items()
                        if k == row["key"] or k.endswith(row["key"])
                    ]
                if not matching:
                    continue
                res = self.trials.run_champion_trials(
                    matching[0],
                    target_noise_std=row["noise_std"],
                    solver_folder=row["solver"],
                    verbose=verbose,
                )
            else:
                res = self.trials.run_baseline_trials(
                    baseline_slug=row["solver"],
                    dim=dim,
                    noise_std=noise_std,
                    p_id=p_id,
                    verbose=verbose,
                )

            if res.get("status") == "CACHED":
                cached_count += 1
            else:
                executed_count += 1

            results.append(
                {
                    "solver_type": stype,
                    "solver": row["solver"],
                    "display_name": row["display_name"],
                    "problem_id": p_id,
                    "dim": dim,
                    "noise_std": noise_std,
                    "status": res["status"],
                    "median_error": res.get("median_clean_error"),
                    "median_best_objective": (
                        float(np.median(res["best_objectives"]))
                        if res.get("best_objectives")
                        else None
                    ),
                    "median_true_optimum": (
                        float(np.median(res["true_optima"])) if res.get("true_optima") else None
                    ),
                }
            )

        self.logger.summary(
            title=f"Completed {solver_type.title()} Evaluations",
            stats={
                "Total": total_active,
                "Cached": cached_count,
                "Executed/Resumed": executed_count,
            },
        )
        return pd.DataFrame(results)

    def run_champions(
        self,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial native champion evaluations."""
        return self.run_evaluations(solver_type="champions", verbose=verbose)

    def run_cross_evaluations(
        self,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial cross-environment evaluations for clean champions."""
        return self.run_evaluations(solver_type="cross_eval", verbose=verbose)

    def run_baselines(
        self,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial baseline evaluations matching the config matrix."""
        return self.run_evaluations(solver_type="baselines", verbose=verbose)
