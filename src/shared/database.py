"""Shared database infrastructure and SQLite connection utilities.

Provides thread-safe connection pooling, WAL mode enforcement, and session factories
shared across bounded contexts without cross-domain dependencies.
"""

import sqlite3
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from shared.config import DATA_DIR


def ensure_db_dir(db_path: Path) -> None:
    """Ensure parent directory for database file exists."""
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)


def ensure_wal_mode(db_path: Path) -> None:
    """Ensures WAL journal mode is set on the DB file before engines are built.

    Idempotent and safe to call multiple times across concurrent processes.
    """
    ensure_db_dir(db_path)
    conn = sqlite3.connect(str(db_path), timeout=60.0)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode")
        row = cur.fetchone()
        if row is None or str(row[0]).lower() != "wal":
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
    finally:
        conn.close()


def build_engine(db_path: Path, echo: bool = False) -> Engine:
    """Creates and configures a SQLite SQLAlchemy engine with WAL mode and concurrency guards."""
    ensure_db_dir(db_path)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "check_same_thread": False,
            "timeout": 60.0,
        },
        echo=echo,
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=60000")
        cursor.close()

    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Creates a thread-safe SQLAlchemy sessionmaker bound to the engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def setup_storage_environment(db_paths: Iterable[Path]) -> None:
    """Pre-flight setup for SQLite databases before spawning concurrent processes."""
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
