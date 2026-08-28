"""SQLite read repository for benchmarking experiments, balance queries, and matrix data."""

from typing import Any
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from shared.tables import ExperimentORM, IterationORM


class SQLiteSynthesisReadRepository:
    """Read-only infrastructure repository managing SQLite queries for synthesis experiments and champion discovery."""

    def __init__(self, session_factory: sessionmaker):
        self.SessionLocal = session_factory

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
                ExperimentORM.mode,
                ExperimentORM.prompt_strategy,
                ExperimentORM.llm_name,
                func.count(ExperimentORM.id).label("completed_count"),
            )
            .where(ExperimentORM.status == "completed")
            .group_by(
                ExperimentORM.problem_id,
                ExperimentORM.dim,
                ExperimentORM.noise_std,
                ExperimentORM.mode,
                ExperimentORM.prompt_strategy,
                ExperimentORM.llm_name,
            )
        )

        with self.SessionLocal() as session:
            conn = session.connection()
            df = pd.read_sql_query(stmt, conn)

        total_completed = int(df["completed_count"].sum()) if not df.empty else 0
        return df, total_completed

    def get_target_conditions(self) -> list[tuple[int, float, int]]:
        """Extract unique `(dim, noise_std, problem_id)` tuples present in DB.

        Returns:
            List of sorted condition tuples.
        """
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

        with self.SessionLocal() as session:
            rows = session.execute(stmt).all()

        return [
            (
                int(r.dim),
                float(r.noise_std) if r.noise_std is not None else 0.0,
                int(r.problem_id),
            )
            for r in rows
        ]

    def get_completed_experiments_matrix(self) -> pd.DataFrame:
        """Fetch distinct completed combinations for auditing coverage."""
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

        with self.SessionLocal() as session:
            conn = session.connection()
            return pd.read_sql_query(stmt, conn)

    def get_synthesis_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load synthesis experiments and iterations tables into pandas DataFrames."""
        with self.SessionLocal() as session:
            conn = session.connection()
            df_exp = pd.read_sql_table(ExperimentORM.__tablename__, conn)
            df_iter = pd.read_sql_table(IterationORM.__tablename__, conn)
        return df_exp, df_iter

