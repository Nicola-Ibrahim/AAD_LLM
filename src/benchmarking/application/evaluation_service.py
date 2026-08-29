"""Benchmark Evaluation Orchestrator Service.

Coordinates unified workload planning, code validity verification, status auditing,
and pure empirical multi-trial execution ($N$ runs) for synthesized LLM champions
and classical baselines driven purely by configs/benchmark.toml.
"""

from datetime import datetime, timezone
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Callable

import ioh
import numpy as np
import pandas as pd

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.services.baselines import get_baseline_runner
from benchmarking.domain.services.resolvers import get_model_slug
from benchmarking.infra.io.hashing import compute_code_hash
from benchmarking.infra.io.trace_repository import EvaluationStateRepository, IOHTraceReader
from benchmarking.infra.logging import EvaluationLogger
from benchmarking.infra.storage.champions_repository import ChampionsReadRepository
from benchmarking.infra.storage.config_repository import EvaluationConfigRepository
from benchmarking.infra.storage.sqlite_repository import SQLiteSynthesisReadRepository
from evolution.domain.services.noise_strategy import (
    HeteroscedasticNoiseStrategy,
    NoNoiseStrategy,
)
from evolution.infra.problems.bbob import BBOBProblem
from shared.config import PROJECT_ROOT
from shared.execution import AlgorithmExecutor


class EvaluationService:
    """Unified application service for workload auditing and empirical benchmark execution."""

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisReadRepository,
        champions_repo: ChampionsReadRepository,
        trace_repo: IOHTraceReader,
        state_repo: EvaluationStateRepository,
        config_repo: EvaluationConfigRepository,
        logger: EvaluationLogger,
        project_root: Path = PROJECT_ROOT,
    ):
        self.sqlite_repo = sqlite_repo
        self.champions_repo = champions_repo
        self.trace_repo = trace_repo
        self.state_repo = state_repo
        self.config_repo = config_repo
        self.logger = logger
        self.project_root = Path(project_root)

        cfg = self.config_repo.load_config()
        self.n_runs = cfg.get("target_eval_runs", 20)
        self.budget_multiplier = cfg.get("budget_multiplier", 10000)
        self.trial_timeout_seconds = cfg.get("eval_timeout_seconds", 30.0)
        self.force_rerun = cfg.get("force_rerun", False)
        self.classical_baselines = cfg.get("classical_baselines", ["cmaes", "de", "pso"])
        self.baseline_labels = cfg.get("baseline_labels", {})

    # ── Condition Discovery Helper ───────────────────────────────────────────────

    def _discover_target_conditions(self) -> list[tuple[int, float, int]]:
        """Discover unique (dim, noise_std, problem_id) conditions directly from SQLite or champions."""
        if self.sqlite_repo:
            try:
                conditions = self.sqlite_repo.get_target_conditions()
                if conditions:
                    return conditions
            except Exception:
                pass

        champions_flat = self.champions_repo.get_champions_flat()
        return sorted(
            list(
                {
                    (c["dim"], c.get("noise_std", 0.0), c["problem_id"])
                    for c in champions_flat.values()
                    if "dim" in c and "problem_id" in c
                }
            )
        )

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

        if not target_dir.exists():
            return "PENDING", 0, None

        prov = self.state_repo.read_provenance(target_dir)
        if prov is None:
            return "PENDING", 0, None

        if expected_code_hash and prov.get("code_hash") != expected_code_hash:
            return "NEEDS_RERUN", len(prov.get("clean_errors", [])), prov.get("median_clean_error")

        clean_errs = prov.get("clean_errors", [])
        runs_found = len(clean_errs)
        med_err = prov.get("median_clean_error")

        if runs_found >= self.n_runs:
            return "COMPLETED", runs_found, med_err
        elif runs_found > 0:
            return "PENDING", runs_found, med_err
        return "PENDING", 0, None

    # ── Workload Auditing Facades ────────────────────────────────────────────────

    def audit_champions_workload(self) -> pd.DataFrame:
        """Audit LLM-evolved champion algorithms workload against config matrix."""
        return self.audit_workload(solver_type="champions")

    def audit_baselines_workload(self) -> pd.DataFrame:
        """Audit classical baselines workload against config matrix."""
        return self.audit_workload(solver_type="baselines")

    def audit_workload(self, solver_type: str = "all") -> pd.DataFrame:
        """Comprehensive workload audit across configured solver types."""
        rows: list[dict[str, Any]] = []

        if solver_type in ("all", "champions"):
            champions_flat = self.champions_repo.get_champions_flat()
            for key, champ in champions_flat.items():
                p_id = champ["problem_id"]
                dim = champ["dim"]
                noise_std = champ.get("noise_std", 0.0)
                strat = champ.get("prompt_strategy", "baseline")
                llm_name = champ.get("llm_name", "llamea")
                model_slug = get_model_slug(llm_name)

                code_path_raw = Path(champ["code_path"])
                code_file = self.project_root / code_path_raw if not code_path_raw.is_absolute() else code_path_raw
                code_valid = code_file.exists()
                code_hash = compute_code_hash(code_file.read_text(encoding="utf-8")) if code_valid else None

                target_dir = self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / f"{model_slug}_{strat}"
                status, runs_found, med_err = self._inspect_solver_status(target_dir, expected_code_hash=code_hash, code_valid=code_valid)

                rows.append({
                    "key": key,
                    "solver_type": "champion",
                    "solver": f"{model_slug}_{strat}",
                    "display_name": f"{llm_name} ({strat})",
                    "model": llm_name,
                    "strategy": strat,
                    "problem_id": p_id,
                    "dim": dim,
                    "noise_std": noise_std,
                    "mode": "clean" if noise_std == 0.0 else "noisy",
                    "target_runs": self.n_runs,
                    "runs_found": runs_found,
                    "status": status,
                    "median_error": med_err,
                    "is_filtered": False,
                })

        if solver_type in ("all", "baselines"):
            target_conditions = self._discover_target_conditions()
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

                    rows.append({
                        "key": f"f{p_id}_{dim}D_std{noise_std}_{baseline_slug}",
                        "solver_type": "baseline",
                        "solver": baseline_slug,
                        "display_name": b_name,
                        "model": baseline_slug,
                        "strategy": "classical",
                        "problem_id": p_id,
                        "dim": dim,
                        "noise_std": noise_std,
                        "mode": "clean" if noise_std == 0.0 else "noisy",
                        "target_runs": self.n_runs,
                        "runs_found": runs_found,
                        "status": status,
                        "median_error": med_err,
                        "is_filtered": False,
                    })

        return pd.DataFrame(rows)

    # ── Core Trial Execution Engine ──────────────────────────────────────────────

    def _execute_trial_runs(
        self,
        target_dir: Path,
        dim: int,
        noise_std: float,
        p_id: int,
        algo_name: str,
        runner_fn: Callable[[BBOBProblem, int], tuple[float, float, int]],
        prov_metadata: dict[str, Any],
        expected_code_hash: str | None = None,
        verbose: bool = True,
    ) -> dict[str, Any]:
        """Generic empirical trial executor handling incremental resumption, IOH logging, and provenance."""
        self.logger.verbose = verbose
        existing_runs = 0
        clean_errors: list[float] = []
        runtimes: list[float] = []
        evals_list: list[int] = []
        can_resume = False

        if not self.force_rerun and target_dir.exists():
            prov = self.state_repo.read_provenance(target_dir)
            if prov is not None and (not expected_code_hash or prov.get("code_hash") == expected_code_hash):
                clean_errors = prov.get("clean_errors", [])
                runtimes = prov.get("runtimes", [])
                evals_list = prov.get("evaluations_used", [])
                existing_runs = len(clean_errors)
                if existing_runs >= self.n_runs:
                    self.logger.cached(existing_runs, prov.get("median_clean_error"))
                    return {
                        "status": "CACHED",
                        "median_clean_error": prov.get("median_clean_error"),
                        "clean_errors": clean_errors,
                        "n_runs": existing_runs,
                    }
                elif existing_runs > 0:
                    can_resume = True
                    self.logger.resuming(existing_runs, self.n_runs)

        if not can_resume:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            clean_errors, runtimes, evals_list = [], [], []
            start_run_idx = 1
            is_incremental = False
        else:
            start_run_idx = existing_runs + 1
            is_incremental = True

        budget = dim * self.budget_multiplier
        noise_strat = NoNoiseStrategy() if noise_std == 0.0 else HeteroscedasticNoiseStrategy(noise_std=noise_std)

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / target_dir.name if is_incremental else target_dir
            run_dir.parent.mkdir(parents=True, exist_ok=True)

            logger_ioh = ioh.logger.Analyzer(
                root=str(run_dir.parent),
                folder_name=run_dir.name,
                algorithm_name=algo_name,
                store_positions=False,
            )

            consecutive_failures = 0
            for run_idx in range(start_run_idx, self.n_runs + 1):
                if consecutive_failures >= 2:
                    clean_errors.append(float("inf"))
                    runtimes.append(0.0)
                    evals_list.append(budget)
                    self.logger.trial(
                        trial_idx=run_idx,
                        total_trials=self.n_runs,
                        best_clean=float("inf"),
                        runtime=0.0,
                        evals_used=budget,
                    )
                    continue

                prob = BBOBProblem(
                    problem_id=p_id,
                    dim=dim,
                    noise_strategy=noise_strat,
                    instance_id=run_idx,
                )
                prob.attach_logger(logger_ioh)
                try:
                    best_clean, rt, evals_used = runner_fn(prob, budget)
                    if np.isinf(best_clean):
                        consecutive_failures += 1
                    else:
                        consecutive_failures = 0
                except Exception:
                    best_clean, rt, evals_used = float("inf"), 0.0, budget
                    consecutive_failures += 1

                clean_errors.append(best_clean)
                runtimes.append(rt)
                evals_list.append(evals_used)
                self.logger.trial(
                    trial_idx=run_idx,
                    total_trials=self.n_runs,
                    best_clean=best_clean,
                    runtime=rt,
                    evals_used=evals_used,
                )
                prob.reset()

            logger_ioh.close()
            if is_incremental:
                self.state_repo.merge_run_logs(run_dir, target_dir)

        median_err = float(np.median(clean_errors)) if clean_errors else float("inf")
        self.logger.condition_complete(len(clean_errors), median_err)
        prov_data = {
            **prov_metadata,
            "problem_id": p_id,
            "dim": dim,
            "noise_std": noise_std,
            "budget": budget,
            "n_runs": len(clean_errors),
            "median_clean_error": median_err,
            "clean_errors": clean_errors,
            "runtimes": runtimes,
            "evaluations_used": evals_list,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.state_repo.write_provenance(target_dir, prov_data)
        return {
            "status": "SUCCESS",
            "median_clean_error": median_err,
            "clean_errors": clean_errors,
            "n_runs": len(clean_errors),
        }

    # ── Champion & Baseline Trial Callables ──────────────────────────────────────

    def run_champion_trials(
        self,
        champion_info: dict[str, Any],
        verbose: bool = True,
    ) -> dict[str, Any]:
        """Execute empirical trials for a single LLM champion algorithm."""
        self.logger.verbose = verbose
        p_id = champion_info["problem_id"]
        dim = champion_info["dim"]
        noise_std = champion_info.get("noise_std", 0.0)
        strat = champion_info.get("prompt_strategy", "baseline")
        llm_name = champion_info.get("llm_name", "llamea")
        algo_name = champion_info.get("algorithm_name", "ChampionAlgorithm")

        raw_code_path = Path(champion_info["code_path"])
        code_file = self.project_root / raw_code_path if not raw_code_path.is_absolute() else raw_code_path
        if not code_file.exists():
            self.logger.missing_code(str(raw_code_path))
            return {"status": "MISSING_CODE", "errors": []}

        code_str = code_file.read_text(encoding="utf-8")
        code_hash = compute_code_hash(code_str)
        model_slug = get_model_slug(llm_name)
        target_dir = self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / f"{model_slug}_{strat}"

        executor = AlgorithmExecutor(timeout_seconds=self.trial_timeout_seconds)

        def champion_runner(prob: BBOBProblem, budget: int) -> tuple[float, float, int]:
            t0 = time.perf_counter()
            best_x, returned_fitness = executor.execute_algorithm(
                code=code_str,
                name=algo_name,
                dim=dim,
                problem=prob,
                budget=budget,
            )
            t1 = time.perf_counter()
            best_clean = prob.eval_clean(best_x) if best_x is not None else float(returned_fitness)
            return best_clean, (t1 - t0), prob.evaluations

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
        baseline_fn = get_baseline_runner(baseline_slug)
        target_dir = self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / baseline_slug

        def baseline_runner(prob: BBOBProblem, budget: int) -> tuple[float, float, int]:
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

        champions_flat = self.champions_repo.get_champions_flat() if solver_type in ("all", "champions") else {}
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

            if stype == "champion":
                clean_k = row["key"]
                matching = [v for k, v in champions_flat.items() if k.endswith(clean_k) or k == clean_k]
                if not matching:
                    continue
                res = self.run_champion_trials(matching[0], verbose=verbose)
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

            results.append({
                "solver_type": stype,
                "solver": row["solver"],
                "display_name": row["display_name"],
                "problem_id": p_id,
                "dim": dim,
                "noise_std": noise_std,
                "status": res["status"],
                "median_error": res.get("median_clean_error"),
            })

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
        """Run all pending/partial champion evaluations matching the config matrix."""
        return self.run_evaluations(solver_type="champions", verbose=verbose)

    def run_baselines(
        self,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial baseline evaluations matching the config matrix."""
        return self.run_evaluations(solver_type="baselines", verbose=verbose)
