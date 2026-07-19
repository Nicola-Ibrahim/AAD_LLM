from pathlib import Path

from infra.storage.sqlite.repository import SQLiteExperimentRepository
from infra.storage.sqlite.connection import build_engine, build_session_factory


def initialize_sqlite_storage(path: str | Path) -> SQLiteExperimentRepository:
    """Factory for building the SQLite experiment repository.

    Args:
        path: DB file path.
    """
    path_obj = Path(path)
    engine = build_engine(path_obj)
    session_factory = build_session_factory(engine)
    return SQLiteExperimentRepository(session_factory=session_factory)
