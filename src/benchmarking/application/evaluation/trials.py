from datetime import datetime, timezone
from pathlib import Path
import hashlib
import random
import time
from collections.abc import Callable

import numpy as np

from benchmarking.application.evaluation.constants import (
    EVALUATION_SCHEMA_VERSION,
    ERROR_DEFINITION,
    executed_trial_count,
)
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.evaluation_state_store import EvaluationStateStore
from benchmarking.application.interfaces.logger import EvaluationLoggerInterface
from shared.application.interfaces.problem_factory import ProblemFactory
from benchmarking.application.champions import Champion
from benchmarking.application.evaluation.types import BaselineRunnerResolver, ExecutorBuilder
from benchmarking.domain.services.resolvers import ModelNames
from evolution.domain.interfaces import BaseProblem
from evolution.domain.enums import NoiseModelEnum
from evolution.domain.services.algorithm_scoring import AlgorithmScoringService


class EvaluationTrialRunner:
    """Resume and execute benchmark conditions across independent trials."""

    def __init__(
        self,
        state_repo: EvaluationStateStore,
        logger: EvaluationLoggerInterface,
        problem_factory: ProblemFactory,
        executor_factory: ExecutorBuilder,
        baseline_resolver: BaselineRunnerResolver,
        code_reader: CandidateCodeReader,
        model_names: ModelNames,
        config: EvaluationConfig,
    ) -> None:
        self.state_repo = state_repo
        self.logger = logger
        self.problem_factory = problem_factory
        self.executor_factory = executor_factory
        self.baseline_resolver = baseline_resolver
        self.code_reader = code_reader
        self.model_names = model_names
        self.n_runs = config.target_eval_runs
        self.budget_multiplier = config.budget_multiplier
        self.trial_timeout_seconds = config.eval_timeout_seconds
        self.force_rerun = config.force_rerun
        self.random_seed = config.random_seed

    def _execute_trial_runs(
        self,
        target_dir: Path,
        dim: int,
        noise_std: float,
        p_id: int,
        algo_name: str,
        runner_fn: Callable[[BaseProblem, int], tuple[float, float, int]],
        prov_metadata: dict[str, object],
        expected_code_hash: str | None = None,
        verbose: bool = True,
    ) -> dict[str, object]:
        """Generic empirical trial executor handling incremental resumption, IOH logging, and provenance."""
        self.logger.verbose = verbose
        existing_runs = 0
        clean_errors: list[float] = []
        best_objectives: list[float] = []
        true_optima: list[float] = []
        instance_ids: list[int] = []
        trial_seeds: list[int] = []
        runtimes: list[float] = []
        evals_list: list[int] = []
        can_resume = False

        if not self.force_rerun and self.state_repo.solver_directory_exists(target_dir):
            prov = self.state_repo.read_provenance(target_dir)
            provenance_is_current = (
                prov is not None
                and prov.get("evaluation_schema_version") == EVALUATION_SCHEMA_VERSION
                and prov.get("error_definition") == ERROR_DEFINITION
                and (not expected_code_hash or prov.get("code_hash") == expected_code_hash)
            )
            if provenance_is_current:
                clean_errors = prov.get("clean_errors", [])
                best_objectives = prov.get("best_objectives", [])
                true_optima = prov.get("true_optima", [])
                instance_ids = prov.get("instance_ids", [])
                trial_seeds = prov.get("trial_seeds", [])
                runtimes = prov.get("runtimes", [])
                evals_list = prov.get("evaluations_used", [])
                existing_runs = executed_trial_count(prov)
                clean_errors = clean_errors[:existing_runs]
                best_objectives = best_objectives[:existing_runs]
                true_optima = true_optima[:existing_runs]
                instance_ids = instance_ids[:existing_runs]
                trial_seeds = trial_seeds[:existing_runs]
                runtimes = runtimes[:existing_runs]
                evals_list = evals_list[:existing_runs]
                if existing_runs >= self.n_runs:
                    self.logger.cached(existing_runs, prov.get("median_error"))
                    return {
                        "status": "CACHED",
                        "median_clean_error": prov.get("median_error"),
                        "best_objectives": prov.get("best_objectives", []),
                        "true_optima": prov.get("true_optima", []),
                        "clean_errors": clean_errors,
                        "n_runs": existing_runs,
                    }
                elif existing_runs > 0:
                    can_resume = True
                    self.logger.resuming(existing_runs, self.n_runs)

        if not can_resume:
            if self.state_repo.solver_directory_exists(target_dir):
                # Stale traces cannot safely be resumed under the current
                # evaluation schema. Remove only this exact condition folder;
                # the notebook regenerates the champion export from the DB.
                self.state_repo.remove_solver_traces(target_dir)
            clean_errors, best_objectives, true_optima = [], [], []
            instance_ids, trial_seeds = [], []
            runtimes, evals_list = [], []
            start_run_idx = 1
            is_incremental = False
        else:
            start_run_idx = existing_runs + 1
            is_incremental = True

        budget = dim * self.budget_multiplier
        noise_model = NoiseModelEnum.NONE if noise_std == 0.0 else NoiseModelEnum.HETEROSCEDASTIC

        with self.state_repo.open_run_logger(target_dir, algo_name, is_incremental) as logger_ioh:
            for run_idx in range(start_run_idx, self.n_runs + 1):
                instance_id = run_idx
                trial_seed = self.random_seed + run_idx
                random.seed(trial_seed)
                np.random.seed(trial_seed)

                prob = self.problem_factory.create(
                    problem_id=p_id,
                    dim=dim,
                    noise_std=noise_std,
                    noise_model=noise_model,
                    instance_id=instance_id,
                    seed=trial_seed,
                )
                true_optimum = float(prob.true_optimum)
                true_optima.append(true_optimum)
                instance_ids.append(instance_id)
                trial_seeds.append(trial_seed)

                prob.attach_logger(logger_ioh)
                prob.set_budget(budget)
                trial_started = time.perf_counter()
                try:
                    best_objective, rt, _reported_evals = runner_fn(prob, budget)
                    best_objective = float(best_objective)
                    if not np.isfinite(best_objective):
                        best_objective = float("inf")
                        best_error = float("inf")
                    else:
                        best_error = AlgorithmScoringService.objective_gap(
                            best_objective, true_optimum
                        )
                except Exception:
                    best_objective, best_error = float("inf"), float("inf")
                    rt = time.perf_counter() - trial_started

                evals_used = int(prob.evaluations)
                clean_errors.append(best_error)
                best_objectives.append(best_objective)
                runtimes.append(rt)
                evals_list.append(evals_used)
                self.logger.trial(
                    trial_idx=run_idx,
                    total_trials=self.n_runs,
                    best_clean=best_error,
                    runtime=rt,
                    evals_used=evals_used,
                    best_objective=best_objective,
                    true_optimum=true_optimum,
                )
                prob.reset()

        median_err = float(np.median(clean_errors)) if clean_errors else float("inf")
        self.logger.condition_complete(len(clean_errors), median_err)
        prov_data = {
            **prov_metadata,
            "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
            "error_definition": ERROR_DEFINITION,
            "all_trials_executed": True,
            "problem_id": p_id,
            "dim": dim,
            "noise_std": noise_std,
            "budget": budget,
            "instance_ids": instance_ids,
            "trial_seeds": trial_seeds,
            "true_optima": true_optima,
            "best_objectives": best_objectives,
            "n_runs": len(clean_errors),
            "median_error": median_err,
            "median_clean_error": median_err,
            "errors": clean_errors,
            "clean_errors": clean_errors,
            "trial_records": [
                {
                    "trial": idx,
                    "instance_id": instance_ids[idx - 1],
                    "seed": trial_seeds[idx - 1],
                    "true_optimum": true_optima[idx - 1],
                    "best_objective": best_objectives[idx - 1],
                    "error": clean_errors[idx - 1],
                    "evaluations_used": evals_list[idx - 1],
                }
                for idx in range(1, len(clean_errors) + 1)
            ],
            "runtimes": runtimes,
            "evaluations_used": evals_list,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.state_repo.write_provenance(target_dir, prov_data)
        return {
            "status": "SUCCESS",
            "median_clean_error": median_err,
            "median_error": median_err,
            "best_objectives": best_objectives,
            "true_optima": true_optima,
            "clean_errors": clean_errors,
            "n_runs": len(clean_errors),
        }

    # ── Champion & Baseline Trial Callables ──────────────────────────────────────

    def run_champion_trials(
        self,
        champion_info: Champion,
        target_noise_std: float | None = None,
        solver_folder: str | None = None,
        verbose: bool = True,
        target_problem_id: int | None = None,
    ) -> dict[str, object]:
        """Execute empirical trials for a single LLM champion algorithm."""
        self.logger.verbose = verbose
        source_problem_id = champion_info["problem_id"]
        p_id = source_problem_id if target_problem_id is None else target_problem_id
        dim = champion_info["dim"]
        noise_std = (
            float(target_noise_std)
            if target_noise_std is not None
            else float(champion_info.get("noise_std", 0.0))
        )
        strat = champion_info.get("prompt_strategy", "baseline")
        llm_name = champion_info.get("llm_name", "llamea")
        algo_name = champion_info.get("algorithm_name", "ChampionAlgorithm")

        raw_code_path = Path(champion_info["code_path"])
        if not self.code_reader.exists(raw_code_path):
            self.logger.missing_code(str(raw_code_path))
            return {"status": "MISSING_CODE", "errors": []}

        code_str = self.code_reader.read(raw_code_path)
        code_hash = hashlib.sha256(code_str.strip().encode("utf-8")).hexdigest()
        model_slug = self.model_names.get_model_slug(llm_name)
        folder = solver_folder or f"{model_slug}_{strat}"
        target_dir = self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / folder
        if target_problem_id is not None and p_id != source_problem_id:
            target_dir = (
                self.state_repo.eval_dir.parent
                / "cross_function_traces"
                / f"source_f{source_problem_id}"
                / f"{dim}D"
                / f"std_{noise_std}"
                / f"f{p_id}"
                / f"{folder}_{code_hash[:12]}"
            )

        executor = self.executor_factory(self.trial_timeout_seconds)

        def champion_runner(prob: BaseProblem, budget: int) -> tuple[float, float, int]:
            t0 = time.perf_counter()
            best_x, _ = executor.execute_algorithm(
                code=code_str,
                name=algo_name,
                dim=dim,
                problem=prob,
                budget=budget,
            )
            t1 = time.perf_counter()
            best_objective = prob.eval_clean(best_x)
            return best_objective, (t1 - t0), prob.evaluations

        prov_metadata = {
            "model": llm_name,
            "model_slug": model_slug,
            "strategy": strat,
            "algorithm_name": algo_name,
            "code_path": champion_info.get("code_path", ""),
            "code_hash": code_hash,
            "source_problem_id": source_problem_id,
            "target_problem_id": p_id,
            "source_noise_std": float(champion_info.get("noise_std", 0.0)),
            "target_noise_std": noise_std,
            "experiment_id": champion_info.get("experiment_id"),
            "iteration_id": champion_info.get("iteration_id"),
            "evaluation_kind": (
                "cross_function"
                if target_problem_id is not None and p_id != source_problem_id
                else "noise_robustness"
                if noise_std != float(champion_info.get("noise_std", 0.0))
                else "native"
            ),
        }

        return self._execute_trial_runs(
            target_dir=target_dir,
            dim=dim,
            noise_std=noise_std,
            p_id=p_id,
            algo_name=algo_name,
            runner_fn=champion_runner,
            prov_metadata=prov_metadata,
            expected_code_hash=code_hash,
            verbose=verbose,
        )

    def run_baseline_trials(
        self,
        baseline_slug: str,
        dim: int,
        noise_std: float,
        p_id: int,
        verbose: bool = True,
    ) -> dict[str, object]:
        """Execute empirical trials for a classical baseline algorithm."""
        self.logger.verbose = verbose
        baseline_fn = self.baseline_resolver(baseline_slug)
        target_dir = (
            self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / baseline_slug
        )

        prov_metadata = {"baseline": baseline_slug}

        return self._execute_trial_runs(
            target_dir=target_dir,
            dim=dim,
            noise_std=noise_std,
            p_id=p_id,
            algo_name=baseline_slug,
            runner_fn=baseline_fn,
            prov_metadata=prov_metadata,
            expected_code_hash=None,
            verbose=verbose,
        )
