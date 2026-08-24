"""SQLite read repository for benchmarking experiments, balance queries, and matrix data."""

from pathlib import Path
import pandas as pd
from sqlalchemy import func, select

from shared.config import DATA_DIR
from shared.database import get_db_connection
from shared.tables import ExperimentORM, IterationORM


class SQLiteBenchmarkReadRepository:
    """Read-only infrastructure repository managing SQLite queries for benchmark experiments."""

    def __init__(self, db_path: Path = DATA_DIR / "db.sqlite3"):
        self.db_path = Path(db_path)

    def get_experiment_balance(self) -> tuple[pd.DataFrame, int]:
        """Query DB for completed experiments grouped by condition.

        Returns:
            Tuple of `(summary_dataframe, total_completed_count)`.
        """
        stmt = (
            select(
                ExperimentORM.problem_id,
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.prompt_strategy,
                func.count().label("count"),
            )
            .where(ExperimentORM.status == "completed")
            .group_by(
                ExperimentORM.problem_id,
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.prompt_strategy,
            )
            .order_by(
                ExperimentORM.problem_id,
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.prompt_strategy,
            )
        )

        with get_db_connection(self.db_path) as conn:
            df_summary = pd.read_sql_query(stmt, conn)
            total_completed = int(df_summary["count"].sum()) if not df_summary.empty else 0
            return df_summary, total_completed

    def get_target_conditions(self) -> list[tuple[int, float, int]]:
        """Discover unique (dim, noise_std, problem_id) experimental conditions from DB."""
        stmt = (
            select(
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.problem_id,
            )
            .distinct()
            .where(ExperimentORM.status == "completed")
            .order_by(
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.problem_id,
            )
        )

        with get_db_connection(self.db_path) as conn:
            df_db = pd.read_sql_query(stmt, conn)
            return [
                (int(r["dim"]), float(r["noise_std"]), int(r["problem_id"]))
                for _, r in df_db.iterrows()
            ]

    def get_synthesis_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load synthesis experiments and iterations tables into pandas DataFrames."""
        stmt_exp = select(ExperimentORM).where(ExperimentORM.status == "completed")
        stmt_iter = select(IterationORM)

        with get_db_connection(self.db_path) as conn:
            df_exp = pd.read_sql_query(stmt_exp, conn)
            df_iter = pd.read_sql_query(stmt_iter, conn)
            return df_exp, df_iter

    def get_completed_experiments_matrix(self) -> pd.DataFrame:
        """Query distinct conditions and models for global coverage matrix construction."""
        stmt = (
            select(
                ExperimentORM.llm_name,
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.problem_id,
                ExperimentORM.prompt_strategy,
            )
            .distinct()
            .where(ExperimentORM.status == "completed")
            .order_by(
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.problem_id,
            )
        )

        with get_db_connection(self.db_path) as conn:
            return pd.read_sql_query(stmt, conn)
