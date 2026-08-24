"""Champions read repository for extracting, formatting, and serializing champion algorithms."""

import json
from pathlib import Path
from typing import Any
import pandas as pd
from sqlalchemy import select

from shared.config import DATA_DIR
from shared.database import get_db_connection
from shared.tables import ExperimentORM, IterationORM


class ChampionsReadRepository:
    """Read-only infrastructure repository managing champion algorithm discovery and serialization."""

    def __init__(
        self,
        db_path: Path = DATA_DIR / "db.sqlite3",
        champions_path: Path = DATA_DIR / "champions.json",
    ):
        self.db_path = Path(db_path)
        self.champions_path = Path(champions_path)

    def extract_champions(self) -> dict[str, dict[str, Any]]:
        """Extract best Clean and Noisy champions per LLM model and experimental condition."""
        stmt = (
            select(
                ExperimentORM.llm_name,
                ExperimentORM.problem_id,
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.prompt_strategy,
                ExperimentORM.id.label("experiment_id"),
                IterationORM.id.label("iteration_id"),
                IterationORM.algorithm_name,
                IterationORM.final_error,
                IterationORM.evaluations_used,
                IterationORM.code_path,
            )
            .join(IterationORM, IterationORM.experiment_id == ExperimentORM.id)
            .where(
                ExperimentORM.status == "completed",
                IterationORM.final_error.isnot(None),
            )
            .order_by(
                ExperimentORM.llm_name,
                ExperimentORM.problem_id,
                ExperimentORM.dim,
                ExperimentORM.prompt_strategy,
                ExperimentORM.noise_std,
                IterationORM.final_error.asc(),
                IterationORM.evaluations_used.asc(),
            )
        )

        with get_db_connection(self.db_path) as conn:
            df = pd.read_sql_query(stmt, conn)

        champions: dict[str, dict[str, Any]] = {}
        if df.empty:
            return champions

        grouped = df.groupby(["llm_name", "problem_id", "dim", "prompt_strategy"])
        for (llm_name, p_id, dim, strat), group in grouped:
            if llm_name not in champions:
                champions[llm_name] = {}

            # 1. Clean Champion (noise_std == 0.0)
            clean_grp = group[group["noise_std"] == 0.0]
            if not clean_grp.empty:
                best_clean = clean_grp.iloc[0]
                k_clean = f"f{p_id}_{dim}D_clean_{strat}"
                champions[llm_name][k_clean] = {
                    "problem_id": int(p_id),
                    "dim": int(dim),
                    "mode": "clean",
                    "noise_std": 0.0,
                    "prompt_strategy": str(strat),
                    "experiment_id": int(best_clean["experiment_id"]),
                    "iteration_id": int(best_clean["iteration_id"]),
                    "algorithm_name": str(best_clean["algorithm_name"]),
                    "final_error": float(best_clean["final_error"]),
                    "evaluations_used": int(best_clean["evaluations_used"])
                    if pd.notnull(best_clean["evaluations_used"])
                    else None,
                    "code_path": str(best_clean["code_path"]),
                    "llm_name": str(llm_name),
                }

            # 2. Noisy Champion (noise_std > 0.0)
            noisy_grp = group[group["noise_std"] > 0.0]
            if not noisy_grp.empty:
                best_noisy = noisy_grp.iloc[0]
                k_noisy = f"f{p_id}_{dim}D_noisy_{strat}"
                champions[llm_name][k_noisy] = {
                    "problem_id": int(p_id),
                    "dim": int(dim),
                    "mode": "noisy",
                    "noise_std": float(best_noisy["noise_std"]),
                    "prompt_strategy": str(strat),
                    "experiment_id": int(best_noisy["experiment_id"]),
                    "iteration_id": int(best_noisy["iteration_id"]),
                    "algorithm_name": str(best_noisy["algorithm_name"]),
                    "final_error": float(best_noisy["final_error"]),
                    "evaluations_used": int(best_noisy["evaluations_used"])
                    if pd.notnull(best_noisy["evaluations_used"])
                    else None,
                    "code_path": str(best_noisy["code_path"]),
                    "llm_name": str(llm_name),
                }

        return champions

    def get_champions_flat(
        self,
        champions_dict: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Flatten model-nested champions dictionary into a single key-value mapping."""
        if champions_dict is None:
            if self.champions_path.exists():
                try:
                    champions_dict = json.loads(self.champions_path.read_text(encoding="utf-8"))
                except Exception:
                    champions_dict = self.extract_champions()
            else:
                champions_dict = self.extract_champions()

        champions_flat: dict[str, dict[str, Any]] = {}
        for k, v in champions_dict.items():
            if isinstance(v, dict) and "code_path" in v:
                champions_flat[k] = v
            elif isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    champions_flat[f"{k}/{sub_k}"] = sub_v
        return champions_flat

    def export_champions_json(
        self,
        output_path: Path | None = None,
    ) -> tuple[dict[str, dict[str, Any]], pd.DataFrame]:
        """Query DB for champions, save to JSON file, and return dictionary plus summary DataFrame."""
        out_path = Path(output_path) if output_path else self.champions_path
        out_path.parent.mkdir(parents=True, exist_ok=True)

        champions = self.extract_champions()
        if not champions:
            return {}, pd.DataFrame()

        out_path.write_text(json.dumps(champions, indent=2), encoding="utf-8")

        summary_rows = []
        for model_name, conds in champions.items():
            for key, c in conds.items():
                summary_rows.append({
                    "model": model_name,
                    "key": key,
                    "problem_id": c["problem_id"],
                    "dim": c["dim"],
                    "mode": c["mode"],
                    "noise_std": c["noise_std"],
                    "prompt_strategy": c["prompt_strategy"],
                    "algorithm_name": c["algorithm_name"],
                    "experiment_id": c["experiment_id"],
                    "iteration_id": c["iteration_id"],
                    "final_error": c["final_error"],
                    "evaluations_used": c["evaluations_used"],
                    "code_path": c["code_path"],
                })

        return champions, pd.DataFrame(summary_rows)
