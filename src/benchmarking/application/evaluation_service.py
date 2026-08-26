"""Benchmark Evaluation Application Service (Notebooks 04 & 05 Use Cases).

Coordinates workload auditing and empirical multi-run execution ($N=10$)
for both synthesized LLM champions and classical baselines.
"""

import json
import logging
from pathlib import Path
import shutil
import time
from typing import Any

import ioh
import numpy as np
import pandas as pd

from benchmarking.domain.services.baselines import BASELINES
from benchmarking.domain.services.resolvers import get_model_slug
from benchmarking.infra.io.hashing import compute_code_hash
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage.champions_repository import ChampionsReadRepository
from benchmarking.infra.storage.sqlite_repository import SQLiteBenchmarkReadRepository
from evolution.domain.services.noise_strategy import (
    HeteroscedasticNoiseStrategy,
    NoNoiseStrategy,
)
from evolution.infra.problems.bbob import BBOBProblem
from shared.execution import AlgorithmExecutor
from shared.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


class BenchmarkEvaluationService:
    """Application use case for auditing and running multi-trial benchmark evaluations."""

    def __init__(
        self,
        sqlite_repo: SQLiteBenchmarkReadRepository,
        champions_repo: ChampionsReadRepository,
        trace_repo: IOHTraceReader,
        project_root: Path = PROJECT_ROOT,
        n_runs: int = 10,
        budget_multiplier: int = 10000,
        trial_timeout_seconds: int = 300,
    ):
        self.sqlite_repo = sqlite_repo
        self.champions_repo = champions_repo
        self.trace_repo = trace_repo
        self.project_root = Path(project_root)
        self.n_runs = n_runs
        self.budget_multiplier = budget_multiplier
        self.trial_timeout_seconds = trial_timeout_seconds

    # ── Workload Auditing ────────────────────────────────────────────────────────

    def audit_champions_workload(
        self,
        champions_flat: dict[str, dict[str, Any]] | None = None,
        filter_models: list[str] | None = None,
        filter_problems: list[int] | None = None,
        filter_strategies: list[str] | None = None,
        filter_modes: list[str] | None = None,
        filter_dims: list[int] | None = None,
        filter_noise: list[float] | None = None,
    ) -> pd.DataFrame:
        """Audit LLM champions completion, code validity, and hash integrity."""
        if champions_flat is None:
            champions_flat = self.champions_repo.get_champions_flat()

        audit_records: list[dict[str, Any]] = []

        for key, info in champions_flat.items():
            p_id = int(info["problem_id"])
            dim = int(info["dim"])
            mode = info.get("mode", "all").lower()
            strat = info.get("prompt_strategy", "baseline").lower()
            llm_name = info.get("llm_name", key.split("/")[0])
            noise_std = float(info.get("noise_std", 0.0))
            algo_name = info.get("algorithm_name", "")
            clean_key = key.split("/")[-1]

            # Filtering
            is_filtered = False
            if filter_models and not any(m.lower() in llm_name.lower() for m in filter_models):
                is_filtered = True
            if filter_problems and p_id not in filter_problems:
                is_filtered = True
            if filter_strategies and strat not in filter_strategies:
                is_filtered = True
            if filter_modes and mode not in filter_modes:
                is_filtered = True
            if filter_dims and dim not in filter_dims:
                is_filtered = True
            if filter_noise and noise_std not in filter_noise:
                is_filtered = True

            raw_code_path = Path(info["code_path"])
            code_file = (
                self.project_root / raw_code_path
                if not raw_code_path.is_absolute()
                else raw_code_path
            )
            has_code = code_file.exists()
            code_hash = compute_code_hash(code_file) if has_code else ""

            model_slug = get_model_slug(llm_name)
            folder_name = f"{model_slug}_{strat}"
            target_log_folder = (
                self.trace_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / folder_name
            )
            prov_path = target_log_folder / "provenance.json"

            status = "PENDING"
            runs_found = 0
            med_err = None

            if not has_code:
                status = "MISSING_CODE"
            elif target_log_folder.exists():
                runs_found = self.trace_repo.get_run_count(target_log_folder)
                if prov_path.exists():
                    try:
                        prov = json.loads(prov_path.read_text(encoding="utf-8"))
                        med_err = prov.get("median_clean_error")
                        if prov.get("code_hash") == code_hash and runs_found > 0:
                            status = "COMPLETED"
                        else:
                            status = "NEEDS_RERUN"
                    except Exception:
                        status = "NEEDS_RERUN"
                else:
                    status = "NEEDS_RERUN"

            audit_records.append({
                "model": model_slug,
                "llm_name": llm_name,
                "key": clean_key,
                "problem_id": p_id,
                "dim": dim,
                "noise_std": noise_std,
                "strategy": strat,
                "algorithm_name": algo_name,
                "status": status,
                "runs_found": runs_found,
                "median_error": med_err,
                "is_filtered": is_filtered,
            })

        return pd.DataFrame(audit_records)

    def audit_baselines_workload(
        self,
        conditions: list[tuple[int, float, int]] | None = None,
        baselines: list[str] | dict[str, Any] | None = None,
        filter_baselines: list[str] | None = None,
        filter_dims: list[int] | None = None,
        filter_noise: list[float] | None = None,
        filter_problems: list[int] | None = None,
    ) -> pd.DataFrame:
        """Scan evaluations directory across classical baseline conditions."""
        if conditions is None:
            conditions = self.sqlite_repo.get_target_conditions()
        if isinstance(baselines, dict):
            active_baselines = list(baselines.keys())
        elif isinstance(baselines, list):
            active_baselines = baselines
        else:
            active_baselines = list(BASELINES.keys())

        baseline_labels = {
            "cmaes": "CMA-ES",
            "de": "Differential Evolution",
            "pso": "Particle Swarm Optimization",
        }

        audit_records = []
        for dim, noise_std, p_id in conditions:
            for b_slug in active_baselines:
                b_name = baseline_labels.get(b_slug, b_slug.upper())

                is_filtered = False
                if filter_baselines and b_slug.lower() not in [f.lower() for f in filter_baselines]:
                    is_filtered = True
                if filter_dims and dim not in filter_dims:
                    is_filtered = True
                if filter_noise and noise_std not in filter_noise:
                    is_filtered = True
                if filter_problems and p_id not in filter_problems:
                    is_filtered = True

                target_folder = (
                    self.trace_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / b_slug
                )
                prov_path = target_folder / "provenance.json"
                status = "PENDING"
                runs_found = 0
                med_err = None

                if target_folder.exists():
                    dat_files = [f for f in target_folder.glob("**/*.dat") if f.stat().st_size > 0]
                    runs_found = len(dat_files)
                    if prov_path.exists() and runs_found > 0:
                        try:
                            prov = json.loads(prov_path.read_text(encoding="utf-8"))
                            med_err = prov.get("median_clean_error")
                            status = "COMPLETED"
                        except Exception:
                            status = "NEEDS_RERUN"
                    elif runs_found > 0:
                        status = "COMPLETED"

                audit_records.append({
                    "baseline": b_slug,
                    "display_name": b_name,
                    "dim": dim,
                    "noise_std": noise_std,
                    "problem_id": p_id,
                    "status": status,
                    "runs_found": runs_found,
                    "median_error": med_err,
                    "is_filtered": is_filtered,
                })

        return pd.DataFrame(audit_records)

    # ── Multi-Run Empirical Trial Execution ─────────────────────────────────────

    def _setup_problem_with_logger(
        self,
        p_id: int,
        dim: int,
        noise_std: float,
        solver_name: str,
        target_dir: Path,
    ) -> tuple[BBOBProblem, ioh.logger.Analyzer]:
        """Instantiate problem and attach IOHprofiler logger."""
        noise_strat = (
            NoNoiseStrategy()
            if noise_std == 0.0
            else HeteroscedasticNoiseStrategy(noise_std=noise_std)
        )
        problem = BBOBProblem(
            problem_id=p_id,
            dim=dim,
            noise_strategy=noise_strat,
            instance_id=1,
        )
        logger_ioh = ioh.logger.Analyzer(
            root=str(target_dir.parent),
            folder_name=target_dir.name,
            algorithm_name=solver_name,
            store_positions=False,
        )
        problem.attach_logger(logger_ioh)
        return problem, logger_ioh

    def run_champion_trials(
        self,
        champion_info: dict[str, Any],
        n_runs: int | None = None,
        force_rerun: bool = False,
    ) -> dict[str, Any]:
        """Execute N empirical trials for a single LLM champion algorithm."""
        effective_n_runs = n_runs if n_runs is not None else self.n_runs
        p_id = int(champion_info["problem_id"])
        dim = int(champion_info["dim"])
        noise_std = float(champion_info.get("noise_std", 0.0))
        strat = str(champion_info.get("prompt_strategy", "baseline"))
        llm_name = str(champion_info.get("llm_name", "llamea"))
        algo_name = str(champion_info.get("algorithm_name", "ChampionAlgorithm"))

        raw_code_path = Path(champion_info["code_path"])
        code_file = (
            self.project_root / raw_code_path
            if not raw_code_path.is_absolute()
            else raw_code_path
        )
        if not code_file.exists():
            return {"status": "MISSING_CODE", "errors": []}

        code_str = code_file.read_text(encoding="utf-8")
        code_hash = compute_code_hash(code_str)

        model_slug = get_model_slug(llm_name)
        folder_name = f"{model_slug}_{strat}"
        target_dir = self.trace_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / folder_name
        prov_path = target_dir / "provenance.json"

        if not force_rerun and target_dir.exists() and prov_path.exists():
            try:
                prov = json.loads(prov_path.read_text(encoding="utf-8"))
                if prov.get("code_hash") == code_hash and (
                    prov.get("n_runs", 0) >= effective_n_runs
                    or self.trace_repo.get_run_count(target_dir) >= effective_n_runs
                ):
                    return {"status": "CACHED", "median_clean_error": prov.get("median_clean_error")}
            except Exception:
                pass

        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        budget = int(dim * self.budget_multiplier)
        clean_errors, runtimes, evals_list = [], [], []

        executor = AlgorithmExecutor(timeout_seconds=self.trial_timeout_seconds)
        noise_strat = (
            NoNoiseStrategy()
            if noise_std == 0.0
            else HeteroscedasticNoiseStrategy(noise_std=noise_std)
        )
        logger_ioh = ioh.logger.Analyzer(
            root=str(target_dir.parent),
            folder_name=target_dir.name,
            algorithm_name=algo_name,
            store_positions=False,
        )

        for run_idx in range(1, effective_n_runs + 1):
            prob = BBOBProblem(
                problem_id=p_id,
                dim=dim,
                noise_strategy=noise_strat,
                instance_id=run_idx,
            )
            prob.attach_logger(logger_ioh)
            t0 = time.perf_counter()
            try:
                best_x, returned_fitness = executor.execute_algorithm(
                    code=code_str,
                    name=algo_name,
                    dim=dim,
                    problem=prob,
                    budget=budget,
                )
                t1 = time.perf_counter()
                if best_x is not None:
                    best_clean = prob.eval_clean(best_x)
                else:
                    best_clean = float(returned_fitness)
                evals_used = prob.evaluations
            except Exception as e:
                t1 = time.perf_counter()
                best_clean = float("inf")
                evals_used = budget
                logger.error(f"Error in champion run {run_idx}: {e}")

            clean_errors.append(float(best_clean))
            runtimes.append(float(t1 - t0))
            evals_list.append(int(evals_used))
            prob.reset()

        logger_ioh.close()

        median_err = float(np.median(clean_errors))
        prov_data = {
            "model": llm_name,
            "model_slug": model_slug,
            "strategy": strat,
            "algorithm_name": algo_name,
            "code_path": str(champion_info["code_path"]),
            "code_hash": code_hash,
            "problem_id": p_id,
            "dim": dim,
            "noise_std": noise_std,
            "budget": budget,
            "n_runs": self.n_runs,
            "median_clean_error": median_err,
            "clean_errors": clean_errors,
            "runtimes": runtimes,
            "evaluations_used": evals_list,
        }
        prov_path.write_text(json.dumps(prov_data, indent=2), encoding="utf-8")
        return {"status": "SUCCESS", "median_clean_error": median_err, "clean_errors": clean_errors}

    def run_baseline_trials(
        self,
        baseline_slug: str,
        dim: int,
        noise_std: float,
        p_id: int,
        n_runs: int | None = None,
        force_rerun: bool = False,
    ) -> dict[str, Any]:
        """Execute N empirical trials for a classical baseline algorithm."""
        effective_n_runs = n_runs if n_runs is not None else self.n_runs
        if baseline_slug not in BASELINES:
            raise ValueError(f"Unknown baseline: {baseline_slug}. Available: {list(BASELINES.keys())}")

        baseline_fn = BASELINES[baseline_slug]
        target_dir = self.trace_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / baseline_slug
        prov_path = target_dir / "provenance.json"

        if not force_rerun and target_dir.exists() and prov_path.exists():
            try:
                prov = json.loads(prov_path.read_text(encoding="utf-8"))
                if (
                    prov.get("n_runs", 0) >= effective_n_runs
                    or self.trace_repo.get_run_count(target_dir) >= effective_n_runs
                ):
                    return {"status": "CACHED", "median_clean_error": prov.get("median_clean_error")}
            except Exception:
                pass

        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        budget = int(dim * self.budget_multiplier)
        clean_errors, runtimes, evals_list = [], [], []

        noise_strat = (
            NoNoiseStrategy()
            if noise_std == 0.0
            else HeteroscedasticNoiseStrategy(noise_std=noise_std)
        )
        logger_ioh = ioh.logger.Analyzer(
            root=str(target_dir.parent),
            folder_name=target_dir.name,
            algorithm_name=baseline_slug,
            store_positions=False,
        )

        for run_idx in range(1, effective_n_runs + 1):
            prob = BBOBProblem(
                problem_id=p_id,
                dim=dim,
                noise_strategy=noise_strat,
                instance_id=run_idx,
            )
            prob.attach_logger(logger_ioh)
            try:
                best_clean, rt, evals_used = baseline_fn(prob, budget)
            except Exception as e:
                logger.error(f"Error in {baseline_slug} run {run_idx}: {e}")
                best_clean, rt, evals_used = float("inf"), 0.0, budget

            clean_errors.append(float(best_clean))
            runtimes.append(float(rt))
            evals_list.append(int(evals_used))
            prob.reset()

        logger_ioh.close()
        median_err = float(np.median(clean_errors))
        prov_data = {
            "baseline": baseline_slug,
            "problem_id": p_id,
            "dim": dim,
            "noise_std": noise_std,
            "budget": budget,
            "n_runs": effective_n_runs,
            "median_clean_error": median_err,
            "clean_errors": clean_errors,
            "runtimes": runtimes,
            "evaluations_used": evals_list,
        }
        prov_path.write_text(json.dumps(prov_data, indent=2), encoding="utf-8")
        return {"status": "SUCCESS", "median_clean_error": median_err, "clean_errors": clean_errors}

    def run_champions(
        self,
        champions_flat: dict[str, dict[str, Any]] | None = None,
        filter_models: list[str] | None = None,
        filter_problems: list[int] | None = None,
        filter_strategies: list[str] | None = None,
        filter_modes: list[str] | None = None,
        filter_dims: list[int] | None = None,
        filter_noise: list[float] | None = None,
        n_runs: int | None = None,
        force_rerun: bool = False,
    ) -> pd.DataFrame:
        """Run all pending/filtered LLM champion evaluations and return results summary."""
        df_audit = self.audit_champions_workload(
            champions_flat=champions_flat,
            filter_models=filter_models,
            filter_problems=filter_problems,
            filter_strategies=filter_strategies,
            filter_modes=filter_modes,
            filter_dims=filter_dims,
            filter_noise=filter_noise,
        )

        active = df_audit[~df_audit["is_filtered"] & (df_audit["status"] != "MISSING_CODE")]
        if champions_flat is None:
            champions_flat = self.champions_repo.get_champions_flat()

        results = []
        for _, row in active.iterrows():
            clean_k = row["key"]
            matching_items = [v for k, v in champions_flat.items() if k.endswith(clean_k) or k == clean_k]
            if not matching_items:
                continue
            champ = matching_items[0]

            res = self.run_champion_trials(champ, n_runs=n_runs, force_rerun=force_rerun)
            results.append({
                "model": row["model"],
                "key": row["key"],
                "problem_id": row["problem_id"],
                "dim": row["dim"],
                "noise_std": row["noise_std"],
                "status": res["status"],
                "median_error": res.get("median_clean_error"),
            })

        return pd.DataFrame(results)

    def run_baselines(
        self,
        conditions: list[tuple[int, float, int]] | None = None,
        baselines: list[str] | dict[str, Any] | None = None,
        filter_baselines: list[str] | None = None,
        filter_dims: list[int] | None = None,
        filter_noise: list[float] | None = None,
        filter_problems: list[int] | None = None,
        n_runs: int | None = None,
        force_rerun: bool = False,
    ) -> pd.DataFrame:
        """Run all pending/filtered baseline evaluations and return results summary."""
        df_audit = self.audit_baselines_workload(
            conditions=conditions,
            baselines=baselines,
            filter_baselines=filter_baselines,
            filter_dims=filter_dims,
            filter_noise=filter_noise,
            filter_problems=filter_problems,
        )

        active = df_audit[~df_audit["is_filtered"]]
        results = []
        for _, row in active.iterrows():
            b_slug = row["baseline"]
            dim = int(row["dim"])
            noise_std = float(row["noise_std"])
            p_id = int(row["problem_id"])

            res = self.run_baseline_trials(
                baseline_slug=b_slug,
                dim=dim,
                noise_std=noise_std,
                p_id=p_id,
                n_runs=n_runs,
                force_rerun=force_rerun,
            )
            results.append({
                "baseline": b_slug,
                "display_name": row["display_name"],
                "dim": dim,
                "noise_std": noise_std,
                "problem_id": p_id,
                "status": res["status"],
                "median_error": res.get("median_clean_error"),
            })

        return pd.DataFrame(results)

