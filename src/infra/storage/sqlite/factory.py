from pathlib import Path

from core.config import DATA_DIR
from infra.storage.sqlite.connection import build_engine, build_session_factory
from infra.storage.sqlite.repository import SQLiteExperimentRepository


def initialize_sqlite_storage(
    path: Path = DATA_DIR / "db.sqlite3",
) -> SQLiteExperimentRepository:
    """Factory for building the SQLite experiment repository.

    Args:
        path: DB file path. Defaults to DATA_DIR / "db.sqlite3".
    """

    engine = build_engine(path)
    session_factory = build_session_factory(engine)
    repo = SQLiteExperimentRepository(session_factory=session_factory)

    return repo
