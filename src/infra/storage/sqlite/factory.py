from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import DATA_DIR
from infra.storage.sqlite.connection import build_engine, build_session_factory, ensure_wal_mode
from infra.storage.sqlite.repository import SQLiteExperimentRepository


def setup_storage_environment(db_paths: Iterable[Path]) -> None:
    """Pre-flight setup for SQLite databases before spawning concurrent processes.

    Ensures WAL mode is enabled on all unique database paths in the parent process.
    """
    for db_path in set(db_paths):
        if db_path:
            ensure_wal_mode(db_path)


def get_db_engine(path: Path = DATA_DIR / "db.sqlite3") -> Engine:
    """Returns a configured SQLAlchemy database engine for SQL queries and dataframes."""
    ensure_wal_mode(path)
    return build_engine(path)


@contextmanager
def get_db_connection(
    path: Path = DATA_DIR / "db.sqlite3",
) -> Generator[Connection, None, None]:
    """Context manager yielding a live database connection for query execution."""
    engine = get_db_engine(path)
    with engine.connect() as conn:
        yield conn


def create_db_session_factory(
    path: Path = DATA_DIR / "db.sqlite3",
) -> sessionmaker[Session]:
    """Creates engine and returns a thread-safe session factory for the given SQLite database path."""
    engine = get_db_engine(path)
    return build_session_factory(engine)


def initialize_sqlite_storage(
    path: Path = DATA_DIR / "db.sqlite3",
) -> SQLiteExperimentRepository:
    """Factory for building the SQLite experiment repository.

    Args:
        path: DB file path. Defaults to DATA_DIR / "db.sqlite3".
    """
    session_factory = create_db_session_factory(path)
    return SQLiteExperimentRepository(session_factory=session_factory)
