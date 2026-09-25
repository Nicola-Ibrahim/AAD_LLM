"""SQLite candidate reader and JSON export writer for benchmark champions."""

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from shared.config import RESULTS_DIR
from shared.database.tables import ExperimentORM, IterationORM


class ChampionsReadRepository:
    """Infrastructure adapter for reading candidate rows and writing champion exports."""

    def __init__(
        self,
        session_factory: sessionmaker,
        champions_path: Path = RESULTS_DIR / "benchmark" / "champions.json",
    ):
        self.SessionLocal = session_factory
        self.champions_path = Path(champions_path)

    def query_candidates(self) -> pd.DataFrame:
        """Return completed candidate iteration rows in deterministic ranking order."""
        stmt = (
            select(
                ExperimentORM.llm_name,
                ExperimentORM.problem_id,
                ExperimentORM.dim,
                ExperimentORM.mode,
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
                ExperimentORM.mode,
                ExperimentORM.noise_std,
                IterationORM.final_error.asc(),
                IterationORM.evaluations_used.asc(),
            )
        )
        with self.SessionLocal() as session:
            return pd.read_sql_query(stmt, session.connection())

    def write_champions_json(
        self, champions: dict[str, dict[str, Any]], output_path: Path | None = None
    ) -> Path:
        path = Path(output_path) if output_path else self.champions_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(champions, indent=2), encoding="utf-8")
        return path
