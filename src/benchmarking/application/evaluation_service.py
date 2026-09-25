"""Benchmark Evaluation Orchestrator Service.

Coordinates unified workload planning, code validity verification, status auditing,
and pure empirical multi-trial execution ($N$ runs) for synthesized LLM champions
and classical baselines driven purely by configs/benchmark.toml.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import random
import time
from typing import Any, Callable

import numpy as np
import pandas as pd

from benchmarking.domain.enums import BBOBFunction
from benchmarking.application.selection_service import ChampionSelectionService
from benchmarking.domain.services.resolvers import get_model_slug
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.ports import (
    BaselineResolver,
    CandidateCodeReader,
    CandidateExecutorFactory,
    ProblemFactory,
)

from evolution.domain.enums import SynthesisMode
from evolution.domain.enums import NoiseModelEnum
from evolution.domain.services.algorithm_scoring import AlgorithmScoringService

from shared.config import PROJECT_ROOT

EVALUATION_SCHEMA_VERSION = 2
ERROR_DEFINITION = "max(0, best_clean_objective - true_optimum)"


class EvaluationService:
    """Unified application service for workload auditing and empirical benchmark execution.

    Workflow Architecture:
    ┌────────────────────────────────────────────────────────┐
    │              EvaluationConfigRepository                │
    │         (benchmark.toml -> EvaluationConfig)           │
    └───────────────────────────┬────────────────────────────┘
                                │
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │                   EvaluationService                    │
    │                                                        │
    │  1. audit_workload()                                   │
    │     Inspect targets, completed runs, pending trials    │
    │                                                        │
    │  2. run_evaluation()                                   │
    │     ├── Synthesized LLM Champions                      │
    │     │   └── Execute on BBOBProblem across N runs       │
    │     ├── Classical Baselines (CMA-ES, DE, PSO)          │
    │     │   └── Execute on BBOBProblem across N runs       │
    │     └── IOHprofiler / Trace Persistence                │
    │         ├── Write IOH data (.dat, .json)               │
    │         └── Update EvaluationStateRepository           │
    └────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        sqlite_repo: Any,
        champions_repo: Any,
        trace_repo: Any,
        state_repo: Any,
        config_repo: Any,
        logger: Any,
        problem_factory: ProblemFactory,
        executor_factory: CandidateExecutorFactory,
        baseline_resolver: BaselineResolver,
        code_reader: CandidateCodeReader,
        project_root: Path = PROJECT_ROOT,
    ):
        self.sqlite_repo = sqlite_repo
        self.champions_repo = champions_repo
        self.champion_selection = ChampionSelectionService(champions_repo=champions_repo)
        self.trace_repo = trace_repo
        self.state_repo = state_repo
        self.config_repo = config_repo
        self.logger = logger
        self.project_root = Path(project_root)
        self.problem_factory = problem_factory
        self.executor_factory = executor_factory
        self.baseline_resolver = baseline_resolver
        self.code_reader = code_reader

        self.config: EvaluationConfig = self.config_repo.load_config()
        self.n_runs = self.config.target_eval_runs
        self.budget_multiplier = self.config.budget_multiplier
        self.trial_timeout_seconds = self.config.eval_timeout_seconds
        self.force_rerun = self.config.force_rerun
        self.classical_baselines = self.config.classical_baselines
        self.baseline_labels = self.config.baseline_labels
        self.cross_eval_clean_champions = self.config.cross_eval_clean_champions
        self.target_noise_stds = self.config.target_noise_stds
        self.random_seed = self.config.random_seed

    # ── Condition Discovery Helper ───────────────────────────────────────────────

    def _discover_target_conditions(self) -> list[tuple[int, float, int]]:
        """Discover unique (dim, noise_std, problem_id) conditions directly from SQLite or champions."""
        raw_conditions: list[tuple[int, float, int]] = []
        if self.sqlite_repo:
            try:
                raw_conditions = self.sqlite_repo.get_target_conditions()
            except Exception:
                raw_conditions = []

        if not raw_conditions:
            champions_flat = self.champion_selection.flatten_champions()
            raw_conditions = [
                (c["dim"], float(c.get("noise_std", 0.0)), c["problem_id"])
                for c in champions_flat.values()
                if "dim" in c and "problem_id" in c
            ]

        if not raw_conditions:
            return []

        # Extract all discovered dimensions, noise standard deviations, and problem IDs
        unique_dims = {c[0] for c in raw_conditions}
        unique_pids = {c[2] for c in raw_conditions}
        if self.target_noise_stds:
            target_noises = sorted(list(set(float(n) for n in self.target_noise_stds)))
        else:
            target_noises = sorted(list({float(c[1]) for c in raw_conditions} | {0.0}))

        expanded = {
            (d, float(n), p) for d in unique_dims for n in target_noises for p in unique_pids
        }
        return sorted(list(expanded))

    # ── Status Inspection Helper ─────────────────────────────────────────────────

    def _inspect_solver_status(
        self,
        target_dir: Path,
        expected_code_hash: str | None = None,
        code_valid: bool = True,
    ) -> tuple[str, int, float | None]:
        """Inspects target directory traces returning (status, runs_found, median_error)."""
        if not code_valid:
            return "MISSING_CODE", 0, None

        if not self.state_repo.solver_directory_exists(target_dir):
            return "PENDING", 0, None

        prov = self.state_repo.read_provenance(target_dir)
        if prov is None:
            return "PENDING", 0, None

        clean_errs = prov.get("errors", prov.get("clean_errors", []))
        runs_found = len(clean_errs)
        med_err = prov.get("median_error", prov.get("median_clean_error"))

        if (
            prov.get("evaluation_schema_version") != EVALUATION_SCHEMA_VERSION
            or prov.get("error_definition") != ERROR_DEFINITION
        ):
            return "NEEDS_RERUN", runs_found, None

        if expected_code_hash and prov.get("code_hash") != expected_code_hash:
            return "NEEDS_RERUN", runs_found, med_err

        if runs_found >= self.n_runs:
            return "COMPLETED", runs_found, med_err
        elif runs_found > 0:
            return "PENDING", runs_found, med_err
        return "PENDING", 0, None

    # ── Workload Auditing Helpers & Builders ────────────────────────────────────

    def _build_champion_audit_row(
        self,
        champ_key: str,
        champ: dict[str, Any],
        eval_noise: float,
        is_cross_eval: bool,
    ) -> dict[str, Any]:
        """Build standardized workload audit row for a champion or cross-evaluation trial."""
        p_id = champ["problem_id"]
        dim = champ["dim"]
        strat = champ.get("prompt_strategy", "baseline")
        llm_name = champ.get("llm_name", "llamea")
        model_slug = get_model_slug(llm_name)
        native_noise = float(champ.get("noise_std", 0.0))
        raw_mode = champ.get("mode")
        if raw_mode:
            mode_enum = SynthesisMode(raw_mode)
        elif "_implicit" in champ_key:
            mode_enum = SynthesisMode.IMPLICIT
        else:
            mode_enum = SynthesisMode.EXPLICIT

        code_path_raw = Path(champ["code_path"])
        code_valid = self._code_exists(code_path_raw)
        code_hash = (
            hashlib.sha256(self._read_code(code_path_raw).strip().encode("utf-8")).hexdigest()
            if code_valid
            else None
        )

        match mode_enum:
            case SynthesisMode.IMPLICIT:
                solver_folder = f"{model_slug}_{strat}_implicit"
            case SynthesisMode.EXPLICIT:
                if native_noise == 0.0:
                    solver_folder = f"{model_slug}_{strat}"
                else:
                    solver_folder = f"{model_slug}_{strat}_noisy"

        scaffold = (
            "baseline prompt (no added scaffold)"
            if strat == "baseline"
            else f"{strat} scaffold"
        )
        display_suffix = f" [{mode_enum.value} | {scaffold}]"
        if is_cross_eval:
            display_suffix += " (cross-eval)"

        target_dir = (
            self.state_repo.eval_dir / f"{dim}D" / f"std_{eval_noise}" / f"f{p_id}" / solver_folder
        )
        status, runs_found, med_err = self._inspect_solver_status(
            target_dir, expected_code_hash=code_hash, code_valid=code_valid
        )

        row_key = f"{champ_key}_eval_std{eval_noise}" if is_cross_eval else champ_key
        solver_type = "cross_eval" if is_cross_eval else "champion"

        return {
            "key": row_key,
            "raw_key": champ_key,
            "solver_type": solver_type,
            "solver": solver_folder,
            "display_name": f"{llm_name} ({strat}){display_suffix}",
            "model": llm_name,
            "strategy": strat,
            "problem_id": p_id,
            "dim": dim,
            "noise_std": eval_noise,
            "mode": mode_enum if not is_cross_eval else SynthesisMode.EXPLICIT,
            "target_runs": self.n_runs,
            "runs_found": runs_found,
            "status": status,
            "median_error": med_err,
            "is_filtered": False,
        }

    # ── Workload Auditing ────────────────────────────────────────────────────────

    def audit_champions_workload(self, include_cross_eval: bool = False) -> pd.DataFrame:
        """Audit LLM champion algorithms (evaluates native environments by default)."""
        champions_flat = self.champion_selection.flatten_champions()
        rows = [
            self._build_champion_audit_row(
                champ_key=k,
                champ=c,
                eval_noise=float(c.get("noise_std", 0.0)),
                is_cross_eval=False,
            )
            for k, c in champions_flat.items()
        ]
        df = pd.DataFrame(rows)
        if include_cross_eval:
            df_cross = self.audit_cross_eval_workload()
            if not df_cross.empty:
                df = pd.concat([df, df_cross], ignore_index=True)
        return df

    def audit_cross_eval_workload(self) -> pd.DataFrame:
        """Audit out-of-distribution cross-environment evaluations for clean champions."""
        champions_flat = self.champion_selection.flatten_champions()
        target_conditions = self._discover_target_conditions()
        noisy_levels = sorted(list({float(c[1]) for c in target_conditions if c[1] > 0.0}))
        if not noisy_levels:
            return pd.DataFrame()

        rows = []
        for k, c in champions_flat.items():
            native_noise = float(c.get("noise_std", 0.0))
            is_clean = native_noise == 0.0 and c.get("mode") == SynthesisMode.EXPLICIT
            if not is_clean:
                continue
            for n_std in noisy_levels:
                rows.append(
                    self._build_champion_audit_row(
                        champ_key=k,
                        champ=c,
                        eval_noise=n_std,
                        is_cross_eval=True,
                    )
                )
        return pd.DataFrame(rows)

    def audit_baselines_workload(self) -> pd.DataFrame:
        """Audit classical baseline algorithms across all target conditions."""
        target_conditions = self._discover_target_conditions()
        rows = []
        for baseline_slug in self.classical_baselines:
            b_name = self.baseline_labels.get(baseline_slug, baseline_slug.upper())
            for dim, noise_std, p_id in target_conditions:
                target_dir = (
                    self.state_repo.eval_dir
                    / f"{dim}D"
                    / f"std_{noise_std}"
                    / f"f{p_id}"
                    / baseline_slug
                )
                status, runs_found, med_err = self._inspect_solver_status(
                    target_dir, expected_code_hash=None, code_valid=True
                )
                rows.append(
                    {
                        "key": f"f{p_id}_{dim}D_std{noise_std}_{baseline_slug}",
                        "solver_type": "baseline",
                        "solver": baseline_slug,
                        "display_name": b_name,
                        "model": baseline_slug,
                        "strategy": "classical",
                        "problem_id": p_id,
                        "dim": dim,
                        "noise_std": noise_std,
                        "mode": SynthesisMode.EXPLICIT,
                        "target_runs": self.n_runs,
                        "runs_found": runs_found,
                        "status": status,
                        "median_error": med_err,
                        "is_filtered": False,
                    }
                )
        return pd.DataFrame(rows)

    def audit_workload(self, solver_type: str = "all") -> pd.DataFrame:
        """Comprehensive workload audit across configured solver types ('all', 'champions', 'cross_eval', 'baselines')."""
        dfs = []
        if solver_type in ("all", "champions"):
            dfs.append(self.audit_champions_workload())
        if solver_type in ("all", "cross_eval"):
            dfs.append(self.audit_cross_eval_workload())
        if solver_type in ("all", "baselines"):
            dfs.append(self.audit_baselines_workload())

        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)

    # ── Core Trial Execution Engine ──────────────────────────────────────────────

    def _execute_trial_runs(
        self,
        target_dir: Path,
        dim: int,
        noise_std: float,
        p_id: int,
        algo_name: str,
        runner_fn: Callable[[Any, int], tuple[float, float, int]],
        prov_metadata: dict[str, Any],
        expected_code_hash: str | None = None,
        verbose: bool = True,
    ) -> dict[str, Any]:
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
                existing_runs = len(clean_errors)
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
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            clean_errors, best_objectives, true_optima = [], [], []
            instance_ids, trial_seeds = [], []
            runtimes, evals_list = [], []
            start_run_idx = 1
            is_incremental = False
        else:
            start_run_idx = existing_runs + 1
            is_incremental = True

        budget = dim * self.budget_multiplier

        with self.state_repo.open_run_logger(
            target_dir, algo_name, is_incremental
        ) as logger_ioh:
            consecutive_failures = 0
            for run_idx in range(start_run_idx, self.n_runs + 1):
                instance_id = run_idx
                trial_seed = self.random_seed + run_idx
                random.seed(trial_seed)
                np.random.seed(trial_seed)

                prob = self._create_problem(
                    problem_id=p_id,
                    dim=dim,
                    noise_std=noise_std,
                    instance_id=instance_id,
                    seed=trial_seed,
                )
                true_optimum = float(prob.true_optimum)
                true_optima.append(true_optimum)
                instance_ids.append(instance_id)
                trial_seeds.append(trial_seed)

                if consecutive_failures >= 2:
                    clean_errors.append(float("inf"))
                    best_objectives.append(float("inf"))
                    runtimes.append(0.0)
                    evals_list.append(0)
                    self.logger.trial(
                        trial_idx=run_idx,
                        total_trials=self.n_runs,
                        best_clean=float("inf"),
                        runtime=0.0,
                        evals_used=0,
                        best_objective=float("inf"),
                        true_optimum=true_optimum,
                    )
                    prob.reset()
                    continue

                prob.attach_logger(logger_ioh)
                prob.set_budget(budget)
                trial_started = time.perf_counter()
                try:
                    best_objective, rt, _reported_evals = runner_fn(prob, budget)
                    best_objective = float(best_objective)
                    if not np.isfinite(best_objective):
                        best_objective = float("inf")
                        best_error = float("inf")
                        consecutive_failures += 1
                    else:
                        best_error = AlgorithmScoringService.objective_gap(
                            best_objective, true_optimum
                        )
                        consecutive_failures = 0
                except Exception:
                    best_objective, best_error = float("inf"), float("inf")
                    rt = time.perf_counter() - trial_started
                    consecutive_failures += 1

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

    def _create_problem(
        self, problem_id: int, dim: int, noise_std: float, instance_id: int, seed: int
    ):
        model = NoiseModelEnum.NONE if noise_std == 0.0 else NoiseModelEnum.HETEROSCEDASTIC
        return self.problem_factory.create(problem_id, dim, noise_std, model, instance_id, seed)

    def _code_exists(self, code_path: str | Path) -> bool:
        return self.code_reader.exists(code_path)

    def _read_code(self, code_path: str | Path) -> str:
        return self.code_reader.read(code_path)

    def _create_executor(self, timeout_seconds: float):
        return self.executor_factory(timeout_seconds)

    def _resolve_baseline(self, baseline_slug: str):
        return self.baseline_resolver(baseline_slug)

    def run_champion_trials(
        self,
        champion_info: dict[str, Any],
        target_noise_std: float | None = None,
        solver_folder: str | None = None,
        verbose: bool = True,
    ) -> dict[str, Any]:
        """Execute empirical trials for a single LLM champion algorithm."""
        self.logger.verbose = verbose
        p_id = champion_info["problem_id"]
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
        if not self._code_exists(raw_code_path):
            self.logger.missing_code(str(raw_code_path))
            return {"status": "MISSING_CODE", "errors": []}

        code_str = self._read_code(raw_code_path)
        code_hash = hashlib.sha256(code_str.strip().encode("utf-8")).hexdigest()
        model_slug = get_model_slug(llm_name)
        folder = solver_folder or f"{model_slug}_{strat}"
        target_dir = self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / folder

        executor = self._create_executor(self.trial_timeout_seconds)

        def champion_runner(prob: Any, budget: int) -> tuple[float, float, int]:
            t0 = time.perf_counter()
            best_x, returned_fitness = executor.execute_algorithm(
                code=code_str,
                name=algo_name,
                dim=dim,
                problem=prob,
                budget=budget,
            )
            t1 = time.perf_counter()
            if best_x is not None:
                best_objective = prob.eval_clean(best_x)
            elif prob.noise_std > 0.0:
                raise ValueError("Noisy champion must return best_x for clean objective scoring.")
            else:
                best_objective = float(returned_fitness)
            return best_objective, (t1 - t0), prob.evaluations

        prov_metadata = {
            "model": llm_name,
            "model_slug": model_slug,
            "strategy": strat,
            "algorithm_name": algo_name,
            "code_path": champion_info.get("code_path", ""),
            "code_hash": code_hash,
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
    ) -> dict[str, Any]:
        """Execute empirical trials for a classical baseline algorithm."""
        self.logger.verbose = verbose
        baseline_fn = self._resolve_baseline(baseline_slug)
        target_dir = (
            self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / baseline_slug
        )

        def baseline_runner(prob: Any, budget: int) -> tuple[float, float, int]:
            return baseline_fn(prob, budget)

        prov_metadata = {"baseline": baseline_slug}

        return self._execute_trial_runs(
            target_dir=target_dir,
            dim=dim,
            noise_std=noise_std,
            p_id=p_id,
            algo_name=baseline_slug,
            runner_fn=baseline_runner,
            prov_metadata=prov_metadata,
            expected_code_hash=None,
            verbose=verbose,
        )

    # ── Unified Batch Runner ─────────────────────────────────────────────────────

    def run_evaluations(
        self,
        solver_type: str = "all",
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial evaluations matching the configured workload."""
        self.logger.verbose = verbose

        df_audit = self.audit_workload(solver_type=solver_type)
        active = df_audit[~df_audit["is_filtered"] & (df_audit["status"] != "MISSING_CODE")]

        champions_flat = (
            self.champion_selection.flatten_champions()
            if solver_type in ("all", "champions", "cross_eval")
            else {}
        )
        results: list[dict[str, Any]] = []

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
                res = self.run_champion_trials(
                    matching[0],
                    target_noise_std=row["noise_std"],
                    solver_folder=row["solver"],
                    verbose=verbose,
                )
            else:
                res = self.run_baseline_trials(
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
                        if res.get("best_objectives") else None
                    ),
                    "median_true_optimum": (
                        float(np.median(res["true_optima"]))
                        if res.get("true_optima") else None
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
