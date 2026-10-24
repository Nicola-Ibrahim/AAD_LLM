import hashlib
import random
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from benchmarking.application.benchmark.models import (
    BaselineRunner,
    BaselineRunnerResolver,
    ExecutorBuilder,
    RecordedTrial,
)
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.application.champions import Champion
from benchmarking.application.interfaces.benchmark_state_store import BenchmarkStateStore
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.logger import BenchmarkLoggerInterface
from benchmarking.domain.benchmark_results import (
    BENCHMARK_SCHEMA_VERSION,
    CHAMPION_RETURN_VALIDATION_VERSION,
    ERROR_DEFINITION,
)
from benchmarking.domain.services.condition_status import inspect_condition
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.domain.services.returned_point import validate_returned_point
from benchmarking.domain.trial_schedule import matching_trial_indices, select_scheduled_trials
from shared.application.interfaces.candidate_executor import (
    CANDIDATE_EXECUTION_VERSION,
    CandidateTimeout,
)
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.domain.noise_model import NoiseModelEnum
from shared.domain.problem import BaseProblem
from shared.domain.scoring import objective_gap


class BenchmarkTrialRunner:
    """Resume and execute benchmark conditions across independent trials."""

    def __init__(
        self,
        state_repo: BenchmarkStateStore,
        logger: BenchmarkLoggerInterface,
        problem_factory: ProblemFactory,
        executor_factory: ExecutorBuilder,
        baseline_resolver: BaselineRunnerResolver,
        code_reader: CandidateCodeReader,
        model_names: ModelNames,
    ) -> None:
        self.state_repo = state_repo
        self.logger = logger
        self.problem_factory = problem_factory
        self.executor_factory = executor_factory
        self.baseline_resolver = baseline_resolver
        self.code_reader = code_reader
        self.model_names = model_names

    def _execute_trial_runs(
        self,
        target_dir: Path,
        dim: int,
        noise_std: float,
        p_id: int,
        algo_name: str,
        runner_fn: BaselineRunner,
        prov_metadata: dict[str, object],
        expected_code_hash: str | None = None,
        verbose: bool = True,
        *,
        config: BenchmarkConfig,
    ) -> dict[str, object]:
        """Generic empirical trial executor handling incremental resumption, IOH logging, and provenance."""
        self.logger.verbose = verbose
        trials: list[RecordedTrial] = []
        can_resume = False
        schedule = config.trial_schedule
        completed_identities: set[tuple[int, int]] = set()

        if not config.force_rerun and self.state_repo.solver_directory_exists(target_dir):
            prov = self.state_repo.read_provenance(target_dir)
            inspection = inspect_condition(
                code_available=True,
                directory_exists=True,
                provenance=prov,
                expected_code_hash=expected_code_hash,
                expected_trials=config.trials_per_condition,
                expected_budget=config.budget,
                trial_schedule=schedule,
                expected_execution_version=prov_metadata.get("candidate_execution_contract"),
            )
            if inspection.reason == "incompatible_execution":
                raise ValueError(
                    "Cannot append champion trials from a different or unknown execution "
                    "contract. Preserve this study and explicitly rerun the condition if "
                    "needed; existing results were not removed."
                )
            if inspection.reason in {"complete", "partial", "not_started"}:
                existing_runs = inspection.reusable_trials
                if existing_runs >= config.trials_per_condition:
                    selected = select_scheduled_trials(prov, schedule)
                    self.logger.cached(existing_runs, selected["median_error"])
                    return {
                        "status": "CACHED",
                        "median_clean_error": selected["median_error"],
                        "best_objectives": selected.get("best_objectives", []),
                        "true_optima": selected.get("true_optima", []),
                        "clean_errors": selected["clean_errors"],
                        "n_runs": existing_runs,
                    }
                trials = RecordedTrial.from_provenance(prov)
                completed_identities = {
                    trials[i].identity for i in matching_trial_indices(prov, schedule)
                }
                can_resume = bool(trials)
                if existing_runs > 0:
                    self.logger.resuming(existing_runs, config.trials_per_condition)

        if not can_resume and self.state_repo.solver_directory_exists(target_dir):
            # Preserve the existing force/stale-result policy: replace only this
            # exact condition. Incompatible partial histories were rejected above.
            self.state_repo.remove_solver_traces(target_dir)

        noise_model = NoiseModelEnum.NONE if noise_std == 0.0 else NoiseModelEnum.HETEROSCEDASTIC
        next_trace_index = self.state_repo.get_trace_run_count(target_dir)

        with self.state_repo.open_run_logger(target_dir, algo_name, can_resume) as logger_ioh:
            for run_idx, (instance_id, trial_seed) in enumerate(schedule, start=1):
                if (instance_id, trial_seed) in completed_identities:
                    continue
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

                prob.attach_logger(logger_ioh)
                prob.set_budget(config.budget)
                if noise_std > 0.0:
                    prob.configure_observation_checkpoints(
                        config.budget, config.observation_trace_points
                    )
                trial_started = time.perf_counter()
                diagnostic: dict[str, str | None] = {
                    "error_type": None,
                    "error_message": None,
                    "error_traceback": None,
                }
                try:
                    best_objective, rt, _reported_evals = runner_fn(prob, config.budget)
                    best_objective = float(best_objective)
                    if not np.isfinite(best_objective):
                        best_objective = float("inf")
                        best_error = float("inf")
                        diagnostic.update(
                            error_type="NonFiniteObjective",
                            error_message="The solver returned a non-finite objective value.",
                        )
                    else:
                        best_error = objective_gap(best_objective, true_optimum)
                except Exception as error:
                    best_objective, best_error = float("inf"), float("inf")
                    rt = time.perf_counter() - trial_started
                    diagnostic.update(
                        error_type=type(error).__name__,
                        error_message=str(error),
                        error_traceback=None
                        if isinstance(error, CandidateTimeout)
                        else traceback.format_exc(),
                    )

                evals_used = int(prob.evaluations)
                trials.append(
                    RecordedTrial(
                        instance_id=instance_id,
                        seed=trial_seed,
                        true_optimum=true_optimum,
                        best_objective=best_objective,
                        error=best_error,
                        runtime=rt,
                        evaluations_used=evals_used,
                        trace_run_index=next_trace_index if evals_used > 0 else None,
                        error_type=diagnostic["error_type"],
                        error_message=diagnostic["error_message"],
                        error_traceback=diagnostic["error_traceback"],
                        observations=[
                            {
                                "evaluations": sample.evaluations,
                                "observed_y": sample.observed_y,
                            }
                            for sample in prob.observation_samples()
                        ],
                    )
                )
                next_trace_index += int(evals_used > 0)
                self.logger.trial(
                    trial_idx=run_idx,
                    total_trials=config.trials_per_condition,
                    best_clean=best_error,
                    runtime=rt,
                    evals_used=evals_used,
                    instance_id=instance_id,
                    trial_seed=trial_seed,
                    best_objective=best_objective,
                    true_optimum=true_optimum,
                )
                prob.reset()

        active_indices = matching_trial_indices(
            {
                "clean_errors": [trial.error for trial in trials],
                "instance_ids": [trial.instance_id for trial in trials],
                "trial_seeds": [trial.seed for trial in trials],
            },
            schedule,
        )
        median_err = float(np.median([trials[i].error for i in active_indices]))
        self.logger.condition_complete(len(active_indices), median_err)
        prov_data = {
            **prov_metadata,
            "evaluation_schema_version": BENCHMARK_SCHEMA_VERSION,
            "error_definition": ERROR_DEFINITION,
            "all_trials_executed": True,
            "problem_id": p_id,
            "dim": dim,
            "noise_std": noise_std,
            "budget": config.budget,
            "instance_ids": [trial.instance_id for trial in trials],
            "trial_seeds": [trial.seed for trial in trials],
            "true_optima": [trial.true_optimum for trial in trials],
            "best_objectives": [trial.best_objective for trial in trials],
            "n_runs": len(trials),
            "requested_instance_ids": [instance for instance, _ in schedule],
            "requested_trial_seeds": [seed for _, seed in schedule],
            "median_error": median_err,
            "median_clean_error": median_err,
            "errors": [trial.error for trial in trials],
            "clean_errors": [trial.error for trial in trials],
            "trial_records": [
                trial.provenance_row(index) for index, trial in enumerate(trials, start=1)
            ],
            "runtimes": [trial.runtime for trial in trials],
            "evaluations_used": [trial.evaluations_used for trial in trials],
            "observed_objectives": [trial.observations for trial in trials],
            "observation_trace_points": config.observation_trace_points,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.state_repo.write_provenance(target_dir, prov_data)
        selected = select_scheduled_trials(prov_data, schedule)
        return {
            "status": "SUCCESS",
            "median_clean_error": median_err,
            "median_error": median_err,
            "best_objectives": selected["best_objectives"],
            "true_optima": selected["true_optima"],
            "clean_errors": selected["clean_errors"],
            "n_runs": selected["n_runs"],
        }

    # ── Champion & Baseline Trial Callables ──────────────────────────────────────

    def run_champion_trials(
        self,
        champion_info: Champion,
        target_noise_std: float | None = None,
        solver_folder: str | None = None,
        verbose: bool = True,
        target_problem_id: int | None = None,
        *,
        config: BenchmarkConfig,
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
        target_dir = self.state_repo.condition_directory(dim, noise_std, p_id, folder)
        if target_problem_id is not None and p_id != source_problem_id:
            target_dir = self.state_repo.transfer_directory(
                source_problem_id, dim, noise_std, p_id, folder, code_hash
            )

        executor = self.executor_factory(config.trial_timeout_seconds)

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
            validate_returned_point(prob, best_x)
            best_objective = prob.eval_clean(best_x)
            return best_objective, (t1 - t0), prob.evaluations

        prov_metadata = {
            "model": llm_name,
            "candidate_execution_contract": CANDIDATE_EXECUTION_VERSION,
            "return_validation_version": CHAMPION_RETURN_VALIDATION_VERSION,
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
            config=config,
        )

    def run_baseline_trials(
        self,
        baseline_slug: str,
        dim: int,
        noise_std: float,
        p_id: int,
        verbose: bool = True,
        *,
        config: BenchmarkConfig,
    ) -> dict[str, object]:
        """Execute empirical trials for a classical baseline algorithm."""
        self.logger.verbose = verbose
        baseline_fn = self.baseline_resolver(baseline_slug)
        target_dir = self.state_repo.condition_directory(dim, noise_std, p_id, baseline_slug)

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
            config=config,
        )
