"""Benchmark Evaluation Orchestrator Service.

Coordinates unified workload planning, code validity verification, status auditing,
and pure empirical multi-trial execution ($N$ runs) for synthesized LLM champions
and classical baselines driven purely by configs/benchmark.toml.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Callable

import ioh
import numpy as np
import pandas as pd

from benchmarking.domain.services.baselines import BASELINES
from benchmarking.domain.services.resolvers import get_model_slug
from benchmarking.infra.io.hashing import compute_code_hash
from benchmarking.infra.io.trace_repository import EvaluationStateRepository, IOHTraceReader
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
        project_root: Path = PROJECT_ROOT,
    ):
        self.sqlite_repo = sqlite_repo
        self.champions_repo = champions_repo
        self.trace_repo = trace_repo
        self.state_repo = state_repo
        self.config_repo = config_repo
        self.project_root = Path(project_root)

        cfg = self.config_repo.load_config()
        self.n_runs = int(cfg.get("target_eval_runs", 10))
        self.budget_multiplier = int(cfg.get("budget_multiplier", 10000))
        self.trial_timeout_seconds = float(cfg.get("eval_timeout_seconds", 300.0))
        self.classical_baselines = cfg.get("classical_baselines", ["cmaes", "de", "pso"])
        self.target_problems = cfg.get("target_problems", [1, 8, 11, 15, 21])
        self.target_dims = cfg.get("target_dims", [2, 3, 5])
        self.target_noise_levels = cfg.get("target_noise_levels", [0.0, 0.05])
        self.target_models = cfg.get("target_models", [])
        self.target_prompt_strategies = cfg.get("target_prompt_strategies", [])
        self.baseline_labels = cfg.get("baseline_labels", {})

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

        runs_found = self.state_repo.get_run_count(target_dir)
        prov = self.state_repo.read_provenance(target_dir)
        med_err = prov.get("median_clean_error") if prov else None

        if expected_code_hash and prov and prov.get("code_hash") != expected_code_hash:
            return "HASH_MISMATCH", runs_found, med_err

        if runs_found >= self.n_runs:
            return "COMPLETED", runs_found, med_err
        if runs_found > 0:
            return "PARTIAL", runs_found, med_err
        return "PENDING", 0, None

    # ── Unified Workload Auditing ────────────────────────────────────────────────

    def audit_workload(self, solver_type: str = "all") -> pd.DataFrame:
        """Audit complete benchmark workload across champions and classical baselines."""
        records: list[dict[str, Any]] = []

        # 1. Audit LLM Champions
        if solver_type.lower() in ("all", "champions", "champion", "llm"):
            champions_flat = self.champions_repo.get_champions_flat()
            for key, info in champions_flat.items():
                p_id = int(info["problem_id"])
                dim = int(info["dim"])
                mode = info.get("mode", "all").lower()
                strat = info.get("prompt_strategy", "baseline").lower()
                llm_name = info.get("llm_name", key.split("/")[0])
                noise_std = float(info.get("noise_std", 0.0))
                algo_name = info.get("algorithm_name", "")
                clean_key = key.split("/")[-1]

                # Match against TOML matrix config
                is_filtered = (
                    (bool(self.target_models) and not any(m.lower() in llm_name.lower() for m in self.target_models))
                    or (bool(self.target_problems) and p_id not in self.target_problems)
                    or (bool(self.target_prompt_strategies) and strat not in [s.lower() for s in self.target_prompt_strategies])
                    or (bool(self.target_dims) and dim not in self.target_dims)
                    or (bool(self.target_noise_levels) and noise_std not in self.target_noise_levels)
                )

                raw_code_path = Path(info["code_path"])
                code_file = self.project_root / raw_code_path if not raw_code_path.is_absolute() else raw_code_path
                code_valid = code_file.exists() and code_file.stat().st_size > 0
                code_hash = compute_code_hash(code_file.read_text(encoding="utf-8")) if code_valid else ""

                model_slug = get_model_slug(llm_name)
                folder_name = f"{model_slug}_{strat}"
                target_folder = self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / folder_name

                status, runs_found, med_err = self._inspect_solver_status(
                    target_dir=target_folder,
                    expected_code_hash=code_hash,
                    code_valid=code_valid,
                )

                records.append({
                    "solver_type": "champion",
                    "condition_key": clean_key,
                    "key": clean_key,
                    "model": model_slug,
                    "solver": model_slug,
                    "display_name": f"{model_slug} ({strat})",
                    "llm_name": llm_name,
                    "strategy": strat,
                    "mode": mode,
                    "dim": dim,
                    "noise_std": noise_std,
                    "problem_id": p_id,
                    "algorithm_name": algo_name,
                    "status": status,
                    "runs_found": runs_found,
                    "target_runs": self.n_runs,
                    "median_error": med_err,
                    "code_valid": code_valid,
                    "code_hash": code_hash,
                    "is_filtered": is_filtered,
                    "target_folder": target_folder,
                })

        # 2. Audit Classical Baselines
        if solver_type.lower() in ("all", "baselines", "baseline", "classical"):
            conditions = [
                (d, n, p)
                for d in self.target_dims
                for n in self.target_noise_levels
                for p in self.target_problems
            ]
            for dim, noise_std, p_id in conditions:
                for b_slug in self.classical_baselines:
                    b_name = self.baseline_labels.get(b_slug, b_slug.upper())
                    target_folder = self.state_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / b_slug

                    status, runs_found, med_err = self._inspect_solver_status(
                        target_dir=target_folder,
                        code_valid=True,
                    )

                    records.append({
                        "solver_type": "baseline",
                        "condition_key": f"{b_slug}_f{p_id}_{dim}D_std{noise_std}",
                        "key": f"{b_slug}_f{p_id}",
                        "model": b_slug,
                        "solver": b_slug,
                        "display_name": b_name,
                        "llm_name": b_name,
                        "baseline": b_slug,
                        "strategy": "classical",
                        "mode": "all",
                        "dim": dim,
                        "noise_std": noise_std,
                        "problem_id": p_id,
                        "algorithm_name": b_name,
                        "status": status,
                        "runs_found": runs_found,
                        "target_runs": self.n_runs,
                        "median_error": med_err,
                        "code_valid": True,
                        "code_hash": "builtin",
                        "is_filtered": False,
                        "target_folder": target_folder,
                    })

        return pd.DataFrame(records)

    def audit_champions_workload(self) -> pd.DataFrame:
        """Audit LLM champions workload against config matrix."""
        return self.audit_workload(solver_type="champions")

    def audit_baselines_workload(self) -> pd.DataFrame:
        """Audit classical baselines workload against config matrix."""
        return self.audit_workload(solver_type="baselines")

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
        force_rerun: bool = False,
    ) -> dict[str, Any]:
        """Generic empirical trial executor handling incremental resumption, IOH logging, and provenance."""
        existing_runs = 0
        clean_errors: list[float] = []
        runtimes: list[float] = []
        evals_list: list[int] = []
        can_resume = False

        if not force_rerun and target_dir.exists():
            prov = self.state_repo.read_provenance(target_dir)
            if prov is not None and (not expected_code_hash or prov.get("code_hash") == expected_code_hash):
                clean_errors = [float(e) for e in prov.get("clean_errors", [])]
                runtimes = [float(r) for r in prov.get("runtimes", [])]
                evals_list = [int(v) for v in prov.get("evaluations_used", [])]
                existing_runs = len(clean_errors)
                if existing_runs >= self.n_runs:
                    return {
                        "status": "CACHED",
                        "median_clean_error": prov.get("median_clean_error"),
                        "clean_errors": clean_errors,
                        "n_runs": existing_runs,
                    }
                elif existing_runs > 0:
                    can_resume = True

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

        budget = int(dim * self.budget_multiplier)
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

            for run_idx in range(start_run_idx, self.n_runs + 1):
                prob = BBOBProblem(
                    problem_id=p_id,
                    dim=dim,
                    noise_strategy=noise_strat,
                    instance_id=run_idx,
                )
                prob.attach_logger(logger_ioh)
                try:
                    best_clean, rt, evals_used = runner_fn(prob, budget)
                except Exception:
                    best_clean, rt, evals_used = float("inf"), 0.0, budget

                clean_errors.append(float(best_clean))
                runtimes.append(float(rt))
                evals_list.append(int(evals_used))
                prob.reset()

            logger_ioh.close()
            if is_incremental:
                self.state_repo.merge_run_logs(run_dir, target_dir)

        median_err = float(np.median(clean_errors)) if clean_errors else float("inf")
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
        force_rerun: bool = False,
    ) -> dict[str, Any]:
        """Execute empirical trials for a single LLM champion algorithm."""
        p_id = int(champion_info["problem_id"])
        dim = int(champion_info["dim"])
        noise_std = float(champion_info.get("noise_std", 0.0))
        strat = str(champion_info.get("prompt_strategy", "baseline"))
        llm_name = str(champion_info.get("llm_name", "llamea"))
        algo_name = str(champion_info.get("algorithm_name", "ChampionAlgorithm"))

        raw_code_path = Path(champion_info["code_path"])
        code_file = self.project_root / raw_code_path if not raw_code_path.is_absolute() else raw_code_path
        if not code_file.exists():
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
            "code_path": str(champion_info.get("code_path", "")),
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
            force_rerun=force_rerun,
        )

    def run_baseline_trials(
        self,
        baseline_slug: str,
        dim: int,
        noise_std: float,
        p_id: int,
        force_rerun: bool = False,
    ) -> dict[str, Any]:
        """Execute empirical trials for a classical baseline algorithm."""
        if baseline_slug not in BASELINES:
            raise ValueError(f"Unknown baseline: {baseline_slug}. Available: {list(BASELINES.keys())}")

        baseline_fn = BASELINES[baseline_slug]
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
            force_rerun=force_rerun,
        )

    # ── Unified Batch Runner ─────────────────────────────────────────────────────

    def run_evaluations(
        self,
        solver_type: str = "all",
        force_rerun: bool = False,
    ) -> pd.DataFrame:
        """Run all pending/partial evaluations matching the configured workload."""
        df_audit = self.audit_workload(solver_type=solver_type)
        active = df_audit[~df_audit["is_filtered"] & (df_audit["status"] != "MISSING_CODE")]

        champions_flat = self.champions_repo.get_champions_flat() if solver_type in ("all", "champions") else {}
        results: list[dict[str, Any]] = []

        for _, row in active.iterrows():
            stype = row["solver_type"]
            dim = int(row["dim"])
            noise_std = float(row["noise_std"])
            p_id = int(row["problem_id"])

            if stype == "champion":
                clean_k = row["key"]
                matching = [v for k, v in champions_flat.items() if k.endswith(clean_k) or k == clean_k]
                if not matching:
                    continue
                res = self.run_champion_trials(matching[0], force_rerun=force_rerun)
            else:
                res = self.run_baseline_trials(
                    baseline_slug=row["solver"],
                    dim=dim,
                    noise_std=noise_std,
                    p_id=p_id,
                    force_rerun=force_rerun,
                )

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

        return pd.DataFrame(results)

    def run_champions(self, force_rerun: bool = False) -> pd.DataFrame:
        """Run all pending/partial champion evaluations matching the config matrix."""
        return self.run_evaluations(solver_type="champions", force_rerun=force_rerun)

    def run_baselines(self, force_rerun: bool = False) -> pd.DataFrame:
        """Run all pending/partial baseline evaluations matching the config matrix."""
        return self.run_evaluations(solver_type="baselines", force_rerun=force_rerun)
