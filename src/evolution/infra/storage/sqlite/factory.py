from collections.abc import Iterable
from pathlib import Path

from evolution.infra.storage.sqlite.repository import SQLiteExperimentRepository
from shared.config import DATA_DIR
from shared.database import (
    create_db_session_factory,
    ensure_wal_mode,
    get_db_connection,
    get_db_engine,
    setup_storage_environment,
)

__all__ = [
    "setup_storage_environment",
    "get_db_engine",
    "get_db_connection",
    "create_db_session_factory",
    "initialize_sqlite_storage",
]


def initialize_sqlite_storage(
    path: Path = DATA_DIR / "db.sqlite3",
) -> SQLiteExperimentRepository:
    """Factory for building the SQLite experiment repository.

    Args:
        path: DB file path. Defaults to DATA_DIR / "db.sqlite3".
    """
    session_factory = create_db_session_factory(path)
    return SQLiteExperimentRepository(session_factory=session_factory)
